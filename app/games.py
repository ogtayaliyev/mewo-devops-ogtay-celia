# Scores max "humainement atteignables" par jeu
GAMES = {
    "pacman": 999_999,
    "tetris": 9_999_999,
    "snake": 99_999,
    "breakout": 896_980,
    "donkeykong": 1_247_700,
}

COOLDOWN_SECONDS = 2


def validate_score(game: str, score: int) -> tuple[bool, str | None]:
    """Vérifie un score. Retourne (ok, motif_rejet)."""
    if game not in GAMES:
        return False, "unknown_game"
    if score < 0:
        return False, "negative_score"
    if score > GAMES[game]:
        return False, "score_too_high"
    return True, None


def check_cooldown(last_submit_ts: float | None, now: float) -> tuple[bool, str | None]:
    """Vérifie le délai entre deux soumissions."""
    if last_submit_ts is None:
        return True, None
    if now - last_submit_ts < COOLDOWN_SECONDS:
        return False, "cooldown"
    return True, None


def sort_leaderboard(scores: list[dict]) -> list[dict]:
    """Trie du meilleur au moins bon."""
    return sorted(scores, key=lambda s: s["score"], reverse=True)
