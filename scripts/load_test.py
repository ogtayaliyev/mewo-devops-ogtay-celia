#!/usr/bin/env python3
"""Test de charge simple pour générer trafic et tentatives de triche."""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
GAMES = ["pacman", "tetris", "snake", "breakout", "donkeykong"]


def submit_score(client: httpx.Client, player: str, game: str, score: int) -> int:
    response = client.post(
        f"{BASE_URL}/scores",
        json={"player": player, "game": game, "score": score},
    )
    return response.status_code


def view_leaderboard(client: httpx.Client, game: str) -> int:
    response = client.get(f"{BASE_URL}/leaderboard/{game}")
    return response.status_code


def pick_game(worker_id: int, round_index: int) -> str:
    return GAMES[(worker_id + round_index) % len(GAMES)]


def pick_score(worker_id: int, round_index: int) -> int:
    # ~30 % de scores invalides pour simuler la triche
    if round_index % 3 == 0:
        return 1_000_000 + ((worker_id * 17 + round_index * 12345) % 8_000_000)
    return 100 + ((worker_id * 7919 + round_index * 997) % 50_000)


def worker(worker_id: int, rounds: int) -> None:
    with httpx.Client(timeout=5.0) as client:
        for i in range(rounds):
            game = pick_game(worker_id, i)
            player = f"P{worker_id:02d}"
            score = pick_score(worker_id, i)
            submit_score(client, player, game, score)
            view_leaderboard(client, game)
            time.sleep(0.1)


def main() -> None:
    workers = 5
    rounds = 20
    print(f"Load test → {BASE_URL} ({workers} workers, {rounds} rounds each)")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, n, rounds) for n in range(workers)]
        for future in as_completed(futures):
            future.result()

    print("Done. Check Grafana (http://localhost:3000) and Prometheus alerts.")


if __name__ == "__main__":
    main()
