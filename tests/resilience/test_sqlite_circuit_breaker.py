import asyncio
import os
import tempfile
import time

import pytest

from agentle.resilience.circuit_breaker.sqlite_circuit_breaker import (
    SQLiteCircuitBreaker,
)


def run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def breaker():
    fd, path = tempfile.mkstemp(prefix="cb-", suffix=".db")
    os.close(fd)
    try:
        b = SQLiteCircuitBreaker(
            db_path=path,
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max_calls=2,
            half_open_success_threshold=2,
            exponential_backoff_multiplier=2.0,
            max_recovery_timeout=1.0,
        )
        yield b
    finally:
        run(b.close())
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def test_open_close_flow(breaker: SQLiteCircuitBreaker):
    cid = "svc"
    run(breaker.record_failure(cid))
    assert run(breaker.is_open(cid)) is False
    run(breaker.record_failure(cid))
    assert run(breaker.is_open(cid)) is True
    time.sleep(0.06)
    assert run(breaker.is_open(cid)) is False  # half-open
    run(breaker.record_success(cid))
    run(breaker.record_success(cid))
    assert run(breaker.is_open(cid)) is False


def test_half_open_failure_reopens(breaker: SQLiteCircuitBreaker):
    cid = "svc2"
    for _ in range(breaker.failure_threshold):
        run(breaker.record_failure(cid))
    assert run(breaker.is_open(cid)) is True
    time.sleep(0.06)
    assert run(breaker.is_open(cid)) is False
    run(breaker.record_failure(cid))
    assert run(breaker.is_open(cid)) is True


def test_admission_limits_in_half_open(breaker: SQLiteCircuitBreaker):
    cid = "svc3"
    for _ in range(breaker.failure_threshold):
        run(breaker.record_failure(cid))
    time.sleep(0.06)
    assert run(breaker.is_open(cid)) is False

    async def check():
        return await breaker.is_open(cid)

    async def go():
        return await asyncio.gather(*[check() for _ in range(5)])

    results = run(go())
    # With 2 permits, expect exactly 2 False (allowed) and remaining True (blocked)
    assert results.count(False) == 2
    assert results.count(True) >= 3


def test_reset_and_get_failure_count(breaker: SQLiteCircuitBreaker):
    cid = "svc4"
    run(breaker.record_failure(cid))
    assert run(breaker.get_failure_count(cid)) == 1
    run(breaker.reset_circuit(cid))
    assert run(breaker.get_failure_count(cid)) == 0
