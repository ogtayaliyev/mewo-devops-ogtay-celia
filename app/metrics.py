from prometheus_client import Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Requêtes HTTP",
    ["route", "status"],
)

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latence des requêtes HTTP",
    ["route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

SCORES_SUBMITTED = Counter(
    "scores_submitted_total",
    "Scores acceptés",
    ["game"],
)

REJECTED_SCORES = Counter(
    "rejected_scores_total",
    "Scores rejetés",
    ["game", "reason"],
)

LEADERBOARD_VIEWS = Counter(
    "leaderboard_views_total",
    "Consultations de classement",
    ["game"],
)


def record_http_request(route: str, status: int, duration: float) -> None:
    HTTP_REQUESTS.labels(route=route, status=str(status)).inc()
    HTTP_LATENCY.labels(route=route).observe(duration)


def record_rejection(game: str, reason: str) -> None:
    REJECTED_SCORES.labels(game=game, reason=reason).inc()


def record_acceptance(game: str) -> None:
    SCORES_SUBMITTED.labels(game=game).inc()


def record_leaderboard_view(game: str) -> None:
    LEADERBOARD_VIEWS.labels(game=game).inc()


def prometheus_metrics() -> bytes:
    return generate_latest()
