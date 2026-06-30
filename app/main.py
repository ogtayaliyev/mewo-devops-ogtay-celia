import time

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app import db, metrics
from app.games import GAMES, check_cooldown, validate_score
from app.middleware import PrometheusMiddleware

app = FastAPI(title="Retro Arcade Leaderboard")
app.add_middleware(PrometheusMiddleware)


class ScoreInput(BaseModel):
    player: str = Field(min_length=1, max_length=50)
    game: str
    score: int


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/")
def home() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
def get_metrics() -> Response:
    return Response(content=metrics.prometheus_metrics(), media_type="text/plain; version=0.0.4")


@app.get("/games")
def list_games() -> dict:
    return {"games": [{"name": name, "max_score": max_score} for name, max_score in GAMES.items()]}


@app.post(
    "/scores",
    status_code=201,
    responses={
        400: {"description": "Jeu inconnu ou score négatif"},
        422: {"description": "Score supérieur au maximum du jeu"},
        429: {"description": "Cooldown : soumission trop rapide (2 s minimum)"},
    },
)
def submit_score(body: ScoreInput) -> dict:
    ok, reason = validate_score(body.game, body.score)
    if not ok:
        metrics.record_rejection(body.game, reason)
        status = 422 if reason == "score_too_high" else 400
        raise HTTPException(status_code=status, detail=reason)

    last = db.get_last_submit(body.player, body.game)
    ok, reason = check_cooldown(last, time.time())
    if not ok:
        metrics.record_rejection(body.game, reason)
        raise HTTPException(status_code=429, detail=reason)

    rank = db.add_score(body.player, body.game, body.score)
    metrics.record_acceptance(body.game)
    return {"rank": rank}


@app.get(
    "/leaderboard/{game}",
    responses={
        404: {"description": "Jeu inconnu"},
    },
)
def leaderboard(game: str, limit: int = 10) -> dict:
    if game not in GAMES:
        raise HTTPException(status_code=404, detail="unknown_game")

    limit = min(max(limit, 1), 100)
    entries = db.get_leaderboard(game, limit)
    metrics.record_leaderboard_view(game)
    return {"game": game, "leaderboard": entries}


@app.get("/players/{player}")
def player_scores(player: str) -> dict:
    scores = db.get_player_best_scores(player)
    return {"player": player, "scores": scores}
