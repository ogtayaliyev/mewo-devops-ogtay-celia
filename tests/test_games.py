import time

from app.games import check_cooldown, sort_leaderboard, validate_score


def test_valid_score_accepted():
    ok, reason = validate_score("pacman", 123456)
    assert ok is True
    assert reason is None


def test_score_above_max_rejected():
    ok, reason = validate_score("pacman", 1_000_000)
    assert ok is False
    assert reason == "score_too_high"


def test_leaderboard_sorted_best_first():
    scores = [
        {"player": "A", "score": 100},
        {"player": "B", "score": 500},
        {"player": "C", "score": 300},
    ]
    sorted_scores = sort_leaderboard(scores)
    assert [s["score"] for s in sorted_scores] == [500, 300, 100]


def test_cooldown_rejects_fast_resubmit():
    now = time.time()
    ok, reason = check_cooldown(now - 1, now)
    assert ok is False
    assert reason == "cooldown"
