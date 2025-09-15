import asyncio
import time
from typing import List

import pytest

from agentle.resilience.circuit_breaker.in_memory_circuit_breaker import (
    InMemoryCircuitBreaker,
)


def make_breaker(**kwargs) -> InMemoryCircuitBreaker:
    # Use tiny timeouts for fast tests
    return InMemoryCircuitBreaker(
        failure_threshold=kwargs.get("failure_threshold", 2),
        recovery_timeout=kwargs.get("recovery_timeout", 0.05),
        half_open_max_calls=kwargs.get("half_open_max_calls", 2),
        half_open_success_threshold=kwargs.get("half_open_success_threshold", 2),
        exponential_backoff_multiplier=kwargs.get(
            "exponential_backoff_multiplier", 2.0
        ),
        max_recovery_timeout=kwargs.get("max_recovery_timeout", 1.0),
        circuit_cleanup_interval=kwargs.get(
            "circuit_cleanup_interval", 0x7FFFFFFF
        ),  # disable background cleanup in tests
        enable_metrics=True,
    )


def run(coro):
    return asyncio.run(coro)


def test_initial_state_is_closed():
    cb = make_breaker()
    assert run(cb.is_open("svc")) is False
    assert run(cb.get_failure_count("svc")) == 0


def test_opens_after_failure_threshold():
    cb = make_breaker(failure_threshold=3)
    run(cb.record_failure("svc"))
    run(cb.record_failure("svc"))
    assert run(cb.is_open("svc")) is False
    run(cb.record_failure("svc"))
    assert run(cb.is_open("svc")) is True


def test_half_open_after_timeout_then_success_closes():
    cb = make_breaker(
        recovery_timeout=0.03, half_open_success_threshold=2, half_open_max_calls=3
    )
    cid = "svc"
    # Open the circuit
    for _ in range(cb.failure_threshold):
        run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True
    # Wait for half-open transition
    time.sleep(0.04)
    assert run(cb.is_open(cid)) is False  # transition to half-open
    # 2 successes should close
    run(cb.record_success(cid))
    run(cb.record_success(cid))
    state = run(cb.get_circuit_state(cid))
    assert state["is_open"] is False
    assert state["failure_count"] == 0
    assert state["is_half_open"] is False


def test_half_open_failure_reopens_immediately():
    cb = make_breaker(recovery_timeout=0.02)
    cid = "svc"
    for _ in range(cb.failure_threshold):
        run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True
    time.sleep(0.03)
    assert run(cb.is_open(cid)) is False  # half-open
    # A single failure in half-open should reopen immediately
    run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True


def test_reset_circuit_clears_state():
    cb = make_breaker()
    cid = "svc"
    for _ in range(cb.failure_threshold):
        run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True
    run(cb.reset_circuit(cid))
    assert run(cb.is_open(cid)) is False
    assert run(cb.get_failure_count(cid)) == 0


def test_bulk_reset_multiple_circuits():
    cb = make_breaker()
    ids = ["a", "b", "c"]
    for cid in ids:
        for _ in range(cb.failure_threshold):
            run(cb.record_failure(cid))
        assert run(cb.is_open(cid)) is True
    results = run(cb.bulk_reset_circuits(ids))
    assert all(results[cid] for cid in ids)
    assert all(run(cb.is_open(cid)) is False for cid in ids)


def test_metrics_are_populated():
    cb = make_breaker()
    cid = "svc"
    run(cb.is_open(cid))
    run(cb.record_failure(cid))
    run(cb.record_success(cid))
    metrics = run(cb.get_metrics())
    # Spot-check a few counters exist and have sane types
    for key in [
        "successes_recorded",
        "failures_recorded",
        "total_circuits",
        "open_circuits",
        "closed_circuits",
        "last_cleanup_seconds_ago",
    ]:
        assert key in metrics
        assert isinstance(metrics[key], int)


def test_exponential_backoff_increases_timeout():
    cb = make_breaker(
        recovery_timeout=0.01,
        exponential_backoff_multiplier=3.0,
        max_recovery_timeout=0.2,
    )
    cid = "svc"
    # Open circuit
    for _ in range(cb.failure_threshold):
        run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True
    # First recovery attempt window
    time.sleep(0.02)
    assert run(cb.is_open(cid)) is False  # half-open
    run(cb.record_failure(cid))  # fail in half-open -> reopen and attempts = 1
    t1 = cb._calculate_recovery_timeout(cid)

    # Second recovery attempt window
    time.sleep(t1 + 0.01)
    assert run(cb.is_open(cid)) is False  # half-open again
    run(cb.record_failure(cid))  # fail again -> attempts = 2
    t2 = cb._calculate_recovery_timeout(cid)

    assert t2 > t1
    assert t2 <= cb.max_recovery_timeout


def test_record_success_on_open_does_not_crash_or_close():
    cb = make_breaker()
    cid = "svc"
    for _ in range(cb.failure_threshold):
        run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True
    # This shouldn't raise and shouldn't close immediately
    run(cb.record_success(cid))
    assert run(cb.is_open(cid)) is True


def test_calls_blocked_metric_increments_when_open():
    cb = make_breaker()
    cid = "svc"
    # Open
    for _ in range(cb.failure_threshold):
        run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True
    before = run(cb.get_metrics()).get("calls_blocked", 0)
    # Query multiple times while open
    run(cb.is_open(cid))
    run(cb.is_open(cid))
    after = run(cb.get_metrics()).get("calls_blocked", 0)
    assert after >= before + 2


def test_close_clears_all_resources():
    cb = make_breaker()
    cids: List[str] = ["x", "y"]
    for cid in cids:
        run(cb.record_failure(cid))
    run(cb.close())
    # After close, state should be empty; asking again should recreate state lazily
    assert run(cb.get_failure_count("x")) == 0
    assert run(cb.is_open("y")) is False


def test_concurrent_failures_are_serialized_and_counted():
    cb = make_breaker()
    cid = "svc"

    async def many_failures(n: int):
        await asyncio.gather(*[cb.record_failure(cid) for _ in range(n)])

    run(many_failures(20))
    count = run(cb.get_failure_count(cid))
    assert count == 20
    assert run(cb.is_open(cid)) is True  # surpasses threshold


def test_manual_cleanup_removes_stale_closed_circuits():
    cb = make_breaker(circuit_cleanup_interval=0.02)
    # Touch a few circuits so they exist
    for cid in ["a", "b", "c"]:
        _ = run(cb.get_failure_count(cid))
    # Sleep beyond 2x interval so 0.0 last_failure_time becomes stale
    time.sleep(0.05)
    # Manually invoke cleanup
    run(cb._cleanup_stale_circuits())
    metrics = run(cb.get_metrics())
    # total_circuits should be 0 after cleanup
    assert metrics["total_circuits"] == 0


def test_get_all_circuits_returns_states_without_deadlock():
    cb = make_breaker()
    run(cb.record_failure("svc1"))
    run(cb.record_failure("svc2"))

    async def call_with_timeout():
        return await asyncio.wait_for(cb.get_all_circuits(), timeout=0.5)

    circuits = run(call_with_timeout())
    ids = {c["circuit_id"] for c in circuits}
    assert {"svc1", "svc2"}.issubset(ids)


@pytest.mark.xfail(
    reason="Half-open call limiting not enforced in is_open; allows unlimited concurrent calls"
)
def test_half_open_call_limit_enforced_expected_behavior():
    cb = make_breaker(
        recovery_timeout=0.02, half_open_max_calls=1, half_open_success_threshold=2
    )
    cid = "svc"
    for _ in range(cb.failure_threshold):
        run(cb.record_failure(cid))
    assert run(cb.is_open(cid)) is True
    time.sleep(0.03)
    # Enter half-open
    assert run(cb.is_open(cid)) is False

    # Simulate multiple concurrent admission checks while half-open; expected desired behavior is to allow only 1
    async def check():
        return await cb.is_open(cid)

    async def go():
        return await asyncio.gather(*[check() for _ in range(5)])

    results = run(go())
    # Desired: only first allowed (False), rest blocked (True). Current: all False.
    assert results.count(True) >= 4  # expecting most blocked if limit enforced
