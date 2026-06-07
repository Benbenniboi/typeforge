from __future__ import annotations
import statistics


def calculate_wpm(char_count: int, elapsed_seconds: float) -> float:
    if elapsed_seconds <= 0:
        return 0.0
    elapsed_minutes = elapsed_seconds / 60.0
    return (char_count / 5.0) / elapsed_minutes


def calculate_consistency(wpm_snapshots: list) -> float:
    if len(wpm_snapshots) < 2:
        return 100.0
    values = [v for v in wpm_snapshots if v > 0]
    if len(values) < 2:
        return 100.0
    mean = statistics.mean(values)
    if mean == 0:
        return 100.0
    stdev = statistics.stdev(values)
    cv = (stdev / mean) * 100.0
    return max(0.0, min(100.0, 100.0 - cv))


def get_percentile(wpm: float, all_scores: list) -> float:
    if not all_scores:
        return 0.0
    below = sum(1 for s in all_scores if s < wpm)
    return (below / len(all_scores)) * 100.0
