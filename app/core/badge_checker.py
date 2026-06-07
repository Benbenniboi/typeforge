from __future__ import annotations
from datetime import datetime
from app.core.engine import TestResult
from app.database import Database

BADGE_DEFS = {
    "first_test": {
        "title": "First Test",
        "description": "Complete your very first test",
    },
    "breaking_50": {
        "title": "Breaking 50",
        "description": "Reach 50 WPM in a single test",
    },
    "breaking_75": {
        "title": "Breaking 75",
        "description": "Reach 75 WPM in a single test",
    },
    "breaking_100": {
        "title": "Breaking 100",
        "description": "Reach 100 WPM in a single test",
    },
    "accuracy_king": {
        "title": "Accuracy King",
        "description": "100% accuracy on a test over 25 words",
    },
    "consistent": {
        "title": "Consistent",
        "description": "Consistency score above 90% on any test",
    },
    "week_streak": {
        "title": "Week Streak",
        "description": "Practice 7 days in a row",
    },
    "month_streak": {
        "title": "Month Streak",
        "description": "Practice 30 days in a row",
    },
    "lesson_graduate": {
        "title": "Lesson Graduate",
        "description": "Complete all 30 lessons",
    },
    "speed_demon": {
        "title": "Speed Demon",
        "description": "Complete a 60-second test over 80 WPM",
    },
    "night_owl": {
        "title": "Night Owl",
        "description": "Complete a test after midnight",
    },
    "early_bird": {
        "title": "Early Bird",
        "description": "Complete a test before 6 AM",
    },
    "code_monkey": {
        "title": "Code Monkey",
        "description": "Complete 10 code mode tests",
    },
}


def check_badges(new_result: TestResult, history: list[TestResult], db: Database) -> list[str]:
    earned = []

    def earn(badge_id: str):
        if not db.has_badge(badge_id):
            db.save_badge(badge_id)
            earned.append(badge_id)

    # First test
    earn("first_test")

    # WPM milestones
    if new_result.wpm >= 50:
        earn("breaking_50")
    if new_result.wpm >= 75:
        earn("breaking_75")
    if new_result.wpm >= 100:
        earn("breaking_100")

    # Accuracy
    if new_result.accuracy >= 100.0 and new_result.char_count >= 25:
        earn("accuracy_king")

    # Consistency
    if new_result.consistency >= 90.0:
        earn("consistent")

    # Speed demon: time_60 mode, 80+ WPM
    if "time_60" in new_result.mode and new_result.wpm >= 80:
        earn("speed_demon")

    # Night owl / early bird
    ts = datetime.fromisoformat(new_result.timestamp)
    hour = ts.hour
    if hour >= 0 and hour < 6:
        if hour < 6 and hour >= 0:
            earn("night_owl") if hour >= 0 else None
            if hour < 6:
                earn("early_bird")

    # Actually: midnight is 0:00, early bird is before 6am
    if hour == 0 or hour == 1 or hour == 2 or hour == 3:
        if hour == 0:
            earn("night_owl")

    # Code monkey: 10 code tests
    code_tests = sum(1 for r in history if "code" in r.mode)
    if code_tests >= 10:
        earn("code_monkey")

    # Streaks
    dates = sorted({datetime.fromisoformat(r.timestamp).date() for r in history}, reverse=True)
    from datetime import date
    today = date.today()
    streak = 0
    from datetime import timedelta
    for i, d in enumerate(dates):
        if d == today - timedelta(days=i):
            streak += 1
        else:
            break

    if streak >= 7:
        earn("week_streak")
    if streak >= 30:
        earn("month_streak")

    # Lesson graduate
    completed = db.get_completed_lesson_count()
    if completed >= 30:
        earn("lesson_graduate")

    return earned
