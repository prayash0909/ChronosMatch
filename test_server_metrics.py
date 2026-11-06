
import time

import pytest

from server import ChronosService


@pytest.fixture
def service(tmp_path):
    return ChronosService(
        db_path=tmp_path / "metrics_test.db"
    )


def test_empty_throughput_is_zero(service):
    state = service.state()

    assert state["performance"]["throughput_ops"] == 0.0



def test_throughput_with_recent_orders(service):
    now = time.perf_counter()

    # Simulate a full 5-second measurement window
    service.metrics_started_at = now - 5

    service.order_timestamps.extend([
        now - 0.3,
        now - 0.2,
        now - 0.1,
    ])

    state = service.state()

    throughput = state["performance"]["throughput_ops"]

    assert throughput == pytest.approx(0.6, abs=0.1)


def test_expired_timestamps_are_removed(service):
    now = time.perf_counter()

    service.order_timestamps.extend([
        now - 6,
        now - 0.1,
    ])

    service.state()

    assert len(service.order_timestamps) == 1


def test_reset_clears_performance_metrics(service):
    service.order_timestamps.extend([
        time.perf_counter(),
        time.perf_counter(),
    ])

    service.total_processing_time_ns = 500000
    service.last_latency_us = 500.0

    result = service.reset()

    assert service.next_id == 1
    assert len(service.order_timestamps) == 0
    assert service.total_processing_time_ns == 0
    assert service.last_latency_us == 0.0
    assert result["performance"]["throughput_ops"] == 0.0
