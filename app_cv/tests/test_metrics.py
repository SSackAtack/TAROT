import unittest

from tarotvision.metrics import RollingMetric, RuntimeMetrics


class RollingMetricTest(unittest.TestCase):
    def test_keeps_last_values(self):
        metric = RollingMetric(maxlen=3)

        metric.add(10.0)
        metric.add(20.0)
        metric.add(30.0)
        metric.add(40.0)

        self.assertEqual(metric.values, [20.0, 30.0, 40.0])
        self.assertEqual(metric.average, 30.0)

    def test_empty_average_is_zero(self):
        metric = RollingMetric(maxlen=3)

        self.assertEqual(metric.average, 0.0)

    def test_runtime_metrics_snapshots_average_values(self):
        metrics = RuntimeMetrics(maxlen=2)

        metrics.add("frame_ms", 10.0)
        metrics.add("frame_ms", 20.0)
        metrics.add("frame_ms", 30.0)

        self.assertEqual(metrics.snapshot(), {"frame_ms": 25.0})


if __name__ == "__main__":
    unittest.main()
