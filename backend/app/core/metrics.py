from __future__ import annotations

import threading
from collections import defaultdict


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def incr(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            bucket = self._histograms[key]
            bucket.append(value)
            if len(bucket) > 500:
                del bucket[:250]

    def render_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            for key, value in sorted(self._counters.items()):
                lines.append(f"{key} {value}")
            for key, values in sorted(self._histograms.items()):
                if not values:
                    continue
                avg = sum(values) / len(values)
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_avg {round(avg, 3)}")
                lines.append(f"{key}_max {round(max(values), 3)}")
        return "\n".join(lines) + ("\n" if lines else "")

    @staticmethod
    def _key(name: str, labels: dict[str, str]) -> str:
        if not labels:
            return name
        joined = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{joined}}}"


metrics = MetricsRegistry()
