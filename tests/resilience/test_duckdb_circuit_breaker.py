import asyncio
import os
import tempfile
import time

import pytest

from agentle.resilience.circuit_breaker.duckdb_circuit_breaker import (
    DuckDBCircuitBreaker,
)


def run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def breaker():
    with tempfile.TemporaryDirectory(prefix="cb-") as tmpdir:
        path = os.path.join(tmpdir, "circuit_breaker.duckdb")
        b = DuckDBCircuitBreaker(
            db_path=path,
            failure_threshold=2,
            recovery_timeout=0.05,
            half_open_max_calls=2,
            half_open_success_threshold=2,
            exponential_backoff_multiplier=2.0,
            max_recovery_timeout=1.0,
        )
        try:
            yield b
        finally:
            run(b.close())


def test_open_close_flow(breaker: DuckDBCircuitBreaker):
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


def test_half_open_failure_reopens(breaker: DuckDBCircuitBreaker):
    cid = "svc2"
    for _ in range(breaker.failure_threshold):
        run(breaker.record_failure(cid))
    assert run(breaker.is_open(cid)) is True
    time.sleep(0.06)
    assert run(breaker.is_open(cid)) is False
    run(breaker.record_failure(cid))
    assert run(breaker.is_open(cid)) is True


def test_admission_limits_in_half_open(breaker: DuckDBCircuitBreaker):
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
    assert results.count(False) == 2  # allowed
    assert results.count(True) >= 3  # blocked


def test_reset_and_get_failure_count(breaker: DuckDBCircuitBreaker):
    cid = "svc4"
    run(breaker.record_failure(cid))
    assert run(breaker.get_failure_count(cid)) == 1
    run(breaker.reset_circuit(cid))
    assert run(breaker.get_failure_count(cid)) == 0
