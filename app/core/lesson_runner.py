from __future__ import annotations
import json
from app.config import CURRICULUM_FILE
from app.core.engine import TypingEngine, TestResult


class LessonRunner:
    def __init__(self, lesson: dict):
        self.lesson = lesson
        self.engine = TypingEngine(
            target=lesson["content"],
            mode="lesson",
            duration=0,
        )

    def process_key(self, char: str) -> bool:
        return self.engine.process_key(char)

    @property
    def is_complete(self) -> bool:
        return self.engine.is_complete

    @property
    def current_position(self) -> int:
        return self.engine.current_position

    @property
    def target(self) -> str:
        return self.engine.target

    @property
    def wpm(self) -> float:
        return self.engine.wpm

    @property
    def accuracy(self) -> float:
        return self.engine.accuracy

    @property
    def typed_pairs(self):
        return self.engine.typed_pairs

    def next_expected_char(self) -> str:
        pos = self.engine.current_position
        if pos < len(self.engine.target):
            return self.engine.target[pos]
        return ""

    def check_pass(self) -> tuple[bool, int, float, float]:
        wpm = self.engine.wpm
        accuracy = self.engine.accuracy
        min_wpm = self.lesson.get("min_wpm_to_pass", 15)
        min_acc = self.lesson.get("min_accuracy_to_pass", 85)
        passed = wpm >= min_wpm and accuracy >= min_acc
        stars = self._calc_stars(wpm)
        return passed, stars, wpm, accuracy

    def _calc_stars(self, wpm: float) -> int:
        thresholds = self.lesson.get("stars_thresholds", [15, 25, 35])
        if wpm >= thresholds[2]:
            return 3
        if wpm >= thresholds[1]:
            return 2
        if wpm >= thresholds[0]:
            return 1
        return 0

    def get_result(self) -> TestResult:
        return self.engine.get_result(mode="lesson")

    def reset(self):
        self.engine.reset()


def load_curriculum() -> list[dict]:
    if CURRICULUM_FILE.exists():
        with open(CURRICULUM_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def get_lesson_by_id(lesson_id: str) -> dict | None:
    for lesson in load_curriculum():
        if lesson["id"] == lesson_id:
            return lesson
    return None


def is_lesson_unlocked(lesson_id: str, progress: dict) -> bool:
    curriculum = load_curriculum()
    if not curriculum:
        return False
    first_lesson = curriculum[0]["id"]
    if lesson_id == first_lesson:
        return True

    for i, lesson in enumerate(curriculum):
        if lesson["id"] == lesson_id and i > 0:
            prev_lesson = curriculum[i - 1]
            prev_id = prev_lesson["id"]
            prev_progress = progress.get(prev_id, {})
            return bool(prev_progress.get("completed", False))

    return False
