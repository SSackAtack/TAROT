from collections import deque


class RollingMetric:
    def __init__(self, maxlen=60):
        self._values = deque(maxlen=maxlen)

    @property
    def values(self):
        return list(self._values)

    @property
    def average(self):
        if not self._values:
            return 0.0
        return sum(self._values) / len(self._values)

    def add(self, value):
        self._values.append(float(value))


class RuntimeMetrics:
    def __init__(self, maxlen=60):
        self.maxlen = maxlen
        self._metrics = {}

    def add(self, name, value):
        metric = self._metrics.setdefault(name, RollingMetric(maxlen=self.maxlen))
        metric.add(value)

    def snapshot(self):
        return {
            name: round(metric.average, 3)
            for name, metric in sorted(self._metrics.items())
        }
