import argparse
import asyncio
import os
import time

from agentle.resilience.circuit_breaker.duckdb_circuit_breaker import (
    DuckDBCircuitBreaker,
)


async def main():
    parser = argparse.ArgumentParser(description="DuckDB Circuit Breaker demo")
    parser.add_argument(
        "--db-path",
        default="duckdb_cb.duckdb",
        help="Path to the DuckDB database file (will be created if missing)",
    )
    parser.add_argument(
        "--circuit-id",
        default="demo-service",
        help="Circuit ID to use for the demo",
    )
    args = parser.parse_args()

    print(f"Using DuckDB file: {os.path.abspath(args.db_path)}")

    breaker = DuckDBCircuitBreaker(
        db_path=args.db_path,
        failure_threshold=2,
        recovery_timeout=0.5,
        half_open_max_calls=2,
        half_open_success_threshold=2,
        exponential_backoff_multiplier=2.0,
        max_recovery_timeout=4.0,
    )

    cid = args.circuit_id

    try:
        # Initial state
        print("Initial is_open:", await breaker.is_open(cid))

        # Cause it to open
        await breaker.record_failure(cid)
        print("After 1 failure, is_open:", await breaker.is_open(cid))
        await breaker.record_failure(cid)
        print(
            "After 2 failures, is_open (should be True/open):",
            await breaker.is_open(cid),
        )

        # Wait past recovery_timeout to allow half-open on next probe
        time.sleep(0.6)
        half_probe = await breaker.is_open(cid)
        print("Probe after timeout (False means admitted/half-open):", half_probe)

        # Simulate concurrent calls trying to pass through during half-open
        async def check():
            return await breaker.is_open(cid)

        results = await asyncio.gather(*[check() for _ in range(5)])
        allowed = results.count(False)
        blocked = results.count(True)
        print(
            f"Half-open admissions: allowed={allowed}, blocked={blocked} (max={breaker.half_open_max_calls})"
        )

        # Reset and demonstrate a clean close flow
        await breaker.reset_circuit(cid)
        print("\nResetting circuit and demonstrating close flow...")
        await breaker.record_failure(cid)
        await breaker.record_failure(cid)
        print("Opened. is_open:", await breaker.is_open(cid))
        time.sleep(0.6)
        print("Half-open probe (False means admitted):", await breaker.is_open(cid))
        # Close with two successes
        await breaker.record_success(cid)
        await breaker.record_success(cid)
        print("Closed. is_open (should be False):", await breaker.is_open(cid))

        # Show persisted failure count (should be 0 when closed)
        print("Failure count:", await breaker.get_failure_count(cid))
        print("Done. Inspect the DB file on disk to verify persistence.")
    finally:
        await breaker.close()


if __name__ == "__main__":
    asyncio.run(main())
