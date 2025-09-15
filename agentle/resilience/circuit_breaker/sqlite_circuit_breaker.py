from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional, override

import aiosqlite

from agentle.resilience.circuit_breaker.circuit_breaker_protocol import (
    CircuitBreakerProtocol,
)


@dataclass
class SQLiteCircuitBreaker(CircuitBreakerProtocol):
    """
    SQLite-based circuit breaker for multi-process environments without external services.

    Uses a single SQLite database file for shared state across processes.
    Requires no containers or external servers.

    Notes:
    - SQLite provides file-level locking; use WAL mode for better concurrency.
    - Time calculations use time.monotonic() deltas where applicable; persisted timestamps use time.time().
    """

    db_path: str = "circuit_breaker.db"
    failure_threshold: int = 5
    recovery_timeout: float = 300.0
    half_open_max_calls: int = 3
    half_open_success_threshold: int = 2
    exponential_backoff_multiplier: float = 1.5
    max_recovery_timeout: float = 1800.0

    _conn: Optional[aiosqlite.Connection] = None
    _init_lock: asyncio.Lock = asyncio.Lock()

    async def _ensure_db(self) -> aiosqlite.Connection:
        if self._conn is not None:
            return self._conn
        async with self._init_lock:
            if self._conn is None:
                self._conn = await aiosqlite.connect(self.db_path)
                await self._conn.execute("PRAGMA journal_mode=WAL;")
                await self._conn.execute("PRAGMA synchronous=NORMAL;")
                await self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS circuits (
                        circuit_id TEXT PRIMARY KEY,
                        failure_count INTEGER NOT NULL DEFAULT 0,
                        last_failure_time REAL NOT NULL DEFAULT 0,
                        is_open INTEGER NOT NULL DEFAULT 0,
                        recovery_attempts INTEGER NOT NULL DEFAULT 0,
                        half_open_calls INTEGER NOT NULL DEFAULT 0,
                        half_open_successes INTEGER NOT NULL DEFAULT 0,
                        half_open_permits INTEGER NOT NULL DEFAULT 0,
                        updated_at REAL NOT NULL DEFAULT (strftime('%s','now'))
                    )
                    """
                )
                await self._conn.commit()
        return self._conn

    async def _get_row(self, conn: aiosqlite.Connection, circuit_id: str) -> None:
        # Ensure row exists; UPSERT on conflict keeps existing
        await conn.execute(
            """
            INSERT INTO circuits (circuit_id) VALUES (?)
            ON CONFLICT(circuit_id) DO NOTHING
            """,
            (circuit_id,),
        )

    def _calc_timeout(self, attempts: int) -> float:
        timeout = self.recovery_timeout * (
            self.exponential_backoff_multiplier**attempts
        )
        return min(timeout, self.max_recovery_timeout)

    @override
    async def is_open(self, circuit_id: str) -> bool:
        conn = await self._ensure_db()
        # Use SAVEPOINT to avoid nested BEGIN errors under concurrency
        await conn.execute("SAVEPOINT cb_tx;")
        try:
            await self._get_row(conn, circuit_id)
            cur = await conn.execute(
                "SELECT is_open, last_failure_time, recovery_attempts, half_open_calls, half_open_permits FROM circuits WHERE circuit_id=?",
                (circuit_id,),
            )
            row = await cur.fetchone()
            is_open_flag, last_failure_time, attempts, half_calls, permits = row

            now = time.time()
            if is_open_flag:
                # Check if recovery window expired => transition to half-open
                timeout = self._calc_timeout(attempts)
                if now - float(last_failure_time) > timeout:
                    await conn.execute(
                        """
                        UPDATE circuits
                        SET is_open=0,
                            half_open_calls=0,
                            half_open_successes=0,
                            half_open_permits=?
                        WHERE circuit_id=?
                        """,
                        (max(0, self.half_open_max_calls), circuit_id),
                    )
                    await conn.execute("RELEASE cb_tx;")
                    await conn.commit()
                    return False
                await conn.execute("RELEASE cb_tx;")
                return True

            # Enforce half-open admission if active using atomic decrement
            if half_calls > 0 or permits > 0:
                cur2 = await conn.execute(
                    "UPDATE circuits SET half_open_permits=half_open_permits-1 WHERE circuit_id=? AND half_open_permits > 0",
                    (circuit_id,),
                )
                granted = cur2.rowcount == 1
                await conn.execute("RELEASE cb_tx;")
                await conn.commit()
                if granted:
                    return False  # allowed
                # No permits left; block further calls while half-open cycle active
                return True

            await conn.execute("RELEASE cb_tx;")
            return False
        except Exception:
            await conn.execute("ROLLBACK TO cb_tx;")
            await conn.execute("RELEASE cb_tx;")
            await conn.rollback()
            raise

    @override
    async def record_success(self, circuit_id: str) -> None:
        conn = await self._ensure_db()
        await conn.execute("SAVEPOINT cb_tx;")
        try:
            await self._get_row(conn, circuit_id)
            cur = await conn.execute(
                "SELECT is_open, half_open_calls, half_open_successes, half_open_permits FROM circuits WHERE circuit_id=?",
                (circuit_id,),
            )
            is_open_flag, half_calls, half_success, permits = await cur.fetchone()
            if is_open_flag:
                # Unexpected success while open; ignore
                await conn.execute("RELEASE cb_tx;")
                return

            # Treat as half-open if permits > 0 or we have any half-open counters
            if permits > 0 or half_calls > 0 or half_success > 0:
                half_calls += 1
                half_success += 1
                # Decide outcome
                if (
                    half_success >= self.half_open_success_threshold
                    or half_calls >= self.half_open_max_calls
                ):
                    if half_success >= self.half_open_success_threshold:
                        # Close the circuit
                        await conn.execute(
                            """
                            UPDATE circuits
                            SET failure_count=0,
                                last_failure_time=0,
                                recovery_attempts=0,
                                half_open_calls=0,
                                half_open_successes=0,
                                half_open_permits=0,
                                is_open=0
                            WHERE circuit_id=?
                            """,
                            (circuit_id,),
                        )
                    else:
                        # Reopen due to insufficient successes
                        await conn.execute(
                            """
                            UPDATE circuits
                            SET is_open=1,
                                last_failure_time=?,
                                recovery_attempts=recovery_attempts+1,
                                half_open_calls=0,
                                half_open_successes=0,
                                half_open_permits=0
                            WHERE circuit_id=?
                            """,
                            (time.time(), circuit_id),
                        )
                else:
                    await conn.execute(
                        "UPDATE circuits SET half_open_calls=?, half_open_successes=? WHERE circuit_id=?",
                        (half_calls, half_success, circuit_id),
                    )
                await conn.execute("RELEASE cb_tx;")
                await conn.commit()
                return

            # Normal success: reset counters
            await conn.execute(
                "UPDATE circuits SET failure_count=0, last_failure_time=0, recovery_attempts=0 WHERE circuit_id=?",
                (circuit_id,),
            )
            await conn.execute("RELEASE cb_tx;")
            await conn.commit()
        except Exception:
            await conn.execute("ROLLBACK TO cb_tx;")
            await conn.execute("RELEASE cb_tx;")
            await conn.rollback()
            raise

    @override
    async def record_failure(self, circuit_id: str) -> None:
        conn = await self._ensure_db()
        await conn.execute("SAVEPOINT cb_tx;")
        try:
            await self._get_row(conn, circuit_id)
            cur = await conn.execute(
                "SELECT is_open, failure_count, half_open_calls, half_open_permits FROM circuits WHERE circuit_id=?",
                (circuit_id,),
            )
            is_open_flag, failure_count, half_calls, permits = await cur.fetchone()
            now = time.time()

            # Failure during half-open: either permits > 0 or we've recorded half-open calls
            if permits > 0 or half_calls > 0:
                # Failure in half-open: reopen, bump attempts, clear half-open
                await conn.execute(
                    """
                    UPDATE circuits
                    SET is_open=1,
                        failure_count=failure_count+1,
                        last_failure_time=?,
                        recovery_attempts=recovery_attempts+1,
                        half_open_calls=0,
                        half_open_successes=0,
                        half_open_permits=0
                    WHERE circuit_id=?
                    """,
                    (now, circuit_id),
                )
                await conn.execute("RELEASE cb_tx;")
                await conn.commit()
                return

            # Normal failure path
            failure_count += 1
            open_it = 1 if failure_count >= self.failure_threshold else 0
            await conn.execute(
                """
                UPDATE circuits
                SET failure_count=?,
                    last_failure_time=?,
                    is_open=CASE WHEN ?=1 THEN 1 ELSE is_open END
                WHERE circuit_id=?
                """,
                (failure_count, now, open_it, circuit_id),
            )
            await conn.execute("RELEASE cb_tx;")
            await conn.commit()
        except Exception:
            await conn.execute("ROLLBACK TO cb_tx;")
            await conn.execute("RELEASE cb_tx;")
            await conn.rollback()
            raise

    @override
    async def get_failure_count(self, circuit_id: str) -> int:
        conn = await self._ensure_db()
        await self._get_row(conn, circuit_id)
        cur = await conn.execute(
            "SELECT failure_count FROM circuits WHERE circuit_id=?",
            (circuit_id,),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0

    @override
    async def reset_circuit(self, circuit_id: str) -> None:
        conn = await self._ensure_db()
        await conn.execute(
            """
            UPDATE circuits
            SET failure_count=0,
                last_failure_time=0,
                is_open=0,
                recovery_attempts=0,
                half_open_calls=0,
                half_open_successes=0,
                half_open_permits=0
            WHERE circuit_id=?
            """,
            (circuit_id,),
        )
        await conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
