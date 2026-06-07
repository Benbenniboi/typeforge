from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional
from app.core.stats import calculate_wpm, calculate_consistency


@dataclass
class TestResult:
    mode: str
    duration: int
    wpm: float
    raw_wpm: float
    accuracy: float
    consistency: float
    char_count: int
    error_count: int
    test_text: str
    wpm_snapshots: list = field(default_factory=list)
    error_map: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    timestamp: str = ""
    id: Optional[int] = None

    @property
    def correct_chars(self):
        return self.char_count

    @property
    def total_chars(self):
        return len(self.test_text)


class TypingEngine:
    SNAPSHOT_INTERVAL = 0.5  # seconds

    def __init__(self, target: str, mode: str = "words", duration: int = 0):
        self.target = target
        self.mode = mode
        self.duration = duration

        self.current_position = 0
        self._typed_chars: list[tuple[str, bool]] = []
        self._keystroke_timestamps: list[float] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

        self.error_count = 0
        self.backspace_count = 0
        self.error_map: dict[str, int] = {}

        self.wpm_snapshots: list[float] = []
        self._last_snapshot_time: float = 0.0

        self._wrong_chars: list[tuple[int, str]] = []

    def process_key(self, char: str) -> bool:
        if self.is_complete:
            return False

        now = time.monotonic()

        if self._start_time is None:
            self._start_time = now
            self._last_snapshot_time = now

        if char == "\x08":  # backspace
            if self.current_position > 0:
                self.current_position -= 1
                if self._typed_chars:
                    self._typed_chars.pop()
            self.backspace_count += 1
            self._maybe_snapshot(now)
            return True

        expected = self.target[self.current_position] if self.current_position < len(self.target) else ""
        correct = (char == expected)

        self._typed_chars.append((char, correct))
        self._keystroke_timestamps.append(now)

        if correct:
            self.current_position += 1
        else:
            self.error_count += 1
            self._wrong_chars.append((self.current_position, char))
            key = expected.lower() if expected else char.lower()
            self.error_map[key] = self.error_map.get(key, 0) + 1
            self.current_position += 1

        self._maybe_snapshot(now)

        if self.current_position >= len(self.target):
            self._end_time = now

        return correct

    def _maybe_snapshot(self, now: float):
        if self._start_time is None:
            return
        elapsed = now - self._start_time
        if elapsed - (self._last_snapshot_time - self._start_time) >= self.SNAPSHOT_INTERVAL:
            self.wpm_snapshots.append(self.wpm)
            self._last_snapshot_time = now

    @property
    def elapsed_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        end = self._end_time or time.monotonic()
        return end - self._start_time

    @property
    def wpm(self) -> float:
        correct_count = sum(1 for _, ok in self._typed_chars if ok)
        return calculate_wpm(correct_count, self.elapsed_seconds)

    @property
    def raw_wpm(self) -> float:
        return calculate_wpm(len(self._typed_chars), self.elapsed_seconds)

    @property
    def accuracy(self) -> float:
        total = len(self._typed_chars)
        if total == 0:
            return 100.0
        correct = sum(1 for _, ok in self._typed_chars if ok)
        return (correct / total) * 100.0

    @property
    def consistency(self) -> float:
        return calculate_consistency(self.wpm_snapshots)

    @property
    def is_complete(self) -> bool:
        return self.current_position >= len(self.target)

    @property
    def typed_pairs(self) -> list[tuple[str, bool]]:
        return list(self._typed_chars)

    def get_result(self, mode: str = None, duration: int = None) -> TestResult:
        from datetime import datetime
        correct_chars = sum(1 for _, ok in self._typed_chars if ok)
        return TestResult(
            mode=mode or self.mode,
            duration=duration or self.duration,
            wpm=round(self.wpm, 1),
            raw_wpm=round(self.raw_wpm, 1),
            accuracy=round(self.accuracy, 1),
            consistency=round(self.consistency, 1),
            char_count=correct_chars,
            error_count=self.error_count,
            test_text=self.target,
            wpm_snapshots=list(self.wpm_snapshots),
            error_map=dict(self.error_map),
            elapsed_seconds=round(self.elapsed_seconds, 2),
            timestamp=datetime.now().isoformat(),
        )

    def reset(self, new_target: str = None):
        self.target = new_target if new_target is not None else self.target
        self.current_position = 0
        self._typed_chars = []
        self._keystroke_timestamps = []
        self._start_time = None
        self._end_time = None
        self.error_count = 0
        self.backspace_count = 0
        self.error_map = {}
        self.wpm_snapshots = []
        self._last_snapshot_time = 0.0
        self._wrong_chars = []
