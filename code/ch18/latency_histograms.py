"""Log-bucket latency histograms: percentiles that survive the long tail.

A stdlib-only re-implementation of the HdrHistogram layout (power-of-two
buckets with linear sub-buckets), because "compute p99" is a sentence every
API engineer says and few can defend. Properties:

  * O(1) memory per recording, fixed-size counts array
  * bounded relative error: 2 significant figures => every recorded value
    lands in a bucket whose width is at most ~0.8% of the value
  * percentiles are read from cumulative bucket counts, never from a
    sample list, so cost is O(buckets), not O(samples)

The demo generates a seeded long-tail distribution (typical API latency:
fast median, brutal tail) and prints the comparison that motivates this
whole chapter: the naive average sits comfortably below p99 --- the average
is lying to you about your users' pain.

Run:  python latency_histograms.py        (demo)
      pytest latency_histograms.py -q     (embedded test suite)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class LogHistogram:
    """HdrHistogram-style integer histogram (values in milliseconds)."""

    lowest: int = 1
    highest: int = 3_600_000  # one hour in ms
    significant_figures: int = 2
    total: int = 0
    sum_ms: float = 0.0
    counts: list[int] = field(init=False)

    def __post_init__(self) -> None:
        if not 1 <= self.significant_figures <= 5:
            raise ValueError("significant_figures must be in 1..5")
        if self.lowest < 1 or self.highest < 2 * self.lowest:
            raise ValueError("need 1 <= lowest <= highest/2")
        # sub_bucket_count: smallest power of two >= 2 * 10^sig
        self._sub_mag = math.ceil(math.log2(2 * 10 ** self.significant_figures))
        self._sub_count = 1 << self._sub_mag
        self._half = self._sub_count // 2
        self._unit_mag = (self.lowest).bit_length() - 1
        # bucket_count: enough doublings to reach `highest`
        self._bucket_count = 1
        trackable = self._sub_count << self._unit_mag
        while trackable < self.highest:
            trackable <<= 1
            self._bucket_count += 1
        self.counts = [0] * ((self._bucket_count + 1) * self._half)

    # -- recording ---------------------------------------------------------
    def _counts_index(self, value: int) -> int:
        if value < 0 or value > self.highest:
            raise ValueError(f"value {value} outside [0, {self.highest}]")
        v = max(value >> self._unit_mag, 1)
        bucket = max(0, v.bit_length() - self._sub_mag)
        sub_bucket = v >> bucket
        return (bucket + 1) * self._half + (sub_bucket - self._half)

    def record(self, value: int) -> None:
        self.counts[self._counts_index(value)] += 1
        self.total += 1
        self.sum_ms += value

    # -- reading -----------------------------------------------------------
    def _value_at(self, counts_index: int) -> int:
        bucket = (counts_index >> (self._sub_mag - 1)) - 1
        sub_bucket = (counts_index & (self._half - 1)) + self._half
        if bucket < 0:
            bucket = 0
            sub_bucket -= self._half
        return sub_bucket << (bucket + self._unit_mag)

    def percentile(self, q: float) -> int:
        """Smallest recorded-bucket value at which q% of samples fall."""
        if not 0 < q <= 100:
            raise ValueError("q must be in (0, 100]")
        if self.total == 0:
            raise ValueError("no samples recorded")
        rank = max(1, math.ceil(q / 100.0 * self.total))
        cumulative = 0
        for idx, count in enumerate(self.counts):
            cumulative += count
            if cumulative >= rank:
                return self._value_at(idx)
        raise AssertionError("unreachable: rank <= total")

    def mean(self) -> float:
        if self.total == 0:
            raise ValueError("no samples recorded")
        return self.sum_ms / self.total


def exact_quantile(data: list[int], q: float) -> int:
    """Ground truth on small data: the rank-based quantile of a sorted list."""
    if not data:
        raise ValueError("empty data")
    ordered = sorted(data)
    rank = max(1, math.ceil(q / 100.0 * len(ordered)))
    return ordered[rank - 1]


def synthetic_latencies(seed: int = 18, n: int = 10_000) -> list[int]:
    """Seeded long-tail: 95% of requests are healthy, 5% hit the tail."""
    rng = random.Random(seed)
    out: list[int] = []
    for _ in range(n):
        if rng.random() < 0.95:  # healthy path: tight lognormal around ~25 ms
            out.append(max(1, int(rng.lognormvariate(math.log(25), 0.35))))
        else:                    # tail path: GC pauses, retries, cold caches
            out.append(rng.randint(800, 30_000))
    return out


def _demo() -> None:
    data = synthetic_latencies()
    hist = LogHistogram()
    for ms in data:
        hist.record(ms)
    print(f"samples={hist.total}  (seeded, long-tail)")
    print(f"  naive average : {hist.mean():9.1f} ms   <-- the lie")
    for q in (50, 95, 99, 99.9):
        print(f"  p{q:<5}        : {hist.percentile(q):9} ms")
    ratio = hist.percentile(99) / hist.mean()
    print(f"  p99 / average : {ratio:9.1f}x  <-- what the average was hiding")


# ---------------------------------------------------------------------------
# Embedded test suite: pytest latency_histograms.py -q
# ---------------------------------------------------------------------------
def test_percentiles_match_exact_quantiles_on_small_data() -> None:
    # values below sub_bucket_count (256) each get their own bucket,
    # so histogram percentiles must equal exact rank-based quantiles
    data = list(range(1, 256))
    hist = LogHistogram()
    for v in data:
        hist.record(v)
    for q in (1, 25, 50, 75, 90, 95, 99, 99.9, 100):
        assert hist.percentile(q) == exact_quantile(data, q)


def test_larger_values_stay_within_resolution_bound() -> None:
    data = list(range(1, 5001))
    hist = LogHistogram()
    for v in data:
        hist.record(v)
    for q in (25, 50, 75, 90, 99):
        approx, exact = hist.percentile(q), exact_quantile(data, q)
        assert abs(approx - exact) / exact < 0.01  # 2 significant figures


def test_mean_is_exact() -> None:
    hist = LogHistogram()
    for v in [10, 20, 30]:
        hist.record(v)
    assert hist.mean() == 20.0


def test_rank_rounding_uses_ceiling() -> None:
    data = [5] * 9 + [900]  # p90 rank = ceil(9.0) = 9 -> 5; p95 -> 900
    hist = LogHistogram()
    for v in data:
        hist.record(v)
    assert hist.percentile(90) == 5
    assert hist.percentile(95) == 900


def test_relative_error_is_bounded_by_resolution() -> None:
    hist = LogHistogram(significant_figures=2)
    hist.record(12_345)  # bucket width at this magnitude is 128 ms
    approx = hist.percentile(50)
    assert abs(approx - 12_345) / 12_345 < 0.01


def test_out_of_range_and_empty_rejected() -> None:
    hist = LogHistogram()
    import pytest

    with pytest.raises(ValueError):
        hist.record(hist.highest + 1)
    with pytest.raises(ValueError):
        hist.percentile(99)
    with pytest.raises(ValueError):
        hist.percentile(0)


def test_long_tail_demo_is_deterministic() -> None:
    assert synthetic_latencies() == synthetic_latencies()
    hist = LogHistogram()
    for ms in synthetic_latencies():
        hist.record(ms)
    assert hist.percentile(99) > 10 * hist.mean()  # the tail really is long


if __name__ == "__main__":
    _demo()
