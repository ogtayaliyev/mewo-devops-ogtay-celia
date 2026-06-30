import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const GAMES = ["pacman", "tetris", "snake", "breakout", "donkeykong"];

function isScoreAcceptedOrRejected(response) {
  return (
    response.status === 201 ||
    response.status === 400 ||
    response.status === 422 ||
    response.status === 429
  );
}

function isLeaderboardOk(response) {
  return response.status === 200;
}

// Montée progressive de la concurrence (ramp-up)
export const options = {
  stages: [
    { duration: "30s", target: 5 },
    { duration: "1m", target: 25 },
    { duration: "1m", target: 50 },
    { duration: "30s", target: 0 },
  ],
};

export default function runLoadTest() {
  const game = GAMES[__VU % GAMES.length];
  const player = `K6_${__VU}_${__ITER}`;

  // ~40 % de scores invalides → déclenche l'alerte CheatSpike dans Prometheus
  const cheat = __ITER % 5 < 2;
  const score = cheat ? 9_999_999 : 500 + (__ITER % 40_000);

  const submit = http.post(
    `${BASE_URL}/scores`,
    JSON.stringify({ player, game, score }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(submit, {
    "score accepté ou rejeté (anti-triche)": isScoreAcceptedOrRejected,
  });

  const board = http.get(`${BASE_URL}/leaderboard/${game}?limit=10`);
  check(board, { "classement ok": isLeaderboardOk });

  sleep(0.05);
}

export function handleSummary() {
  return {
    stdout:
      "\nTest de charge terminé.\n" +
      "→ Grafana : http://localhost:3000\n" +
      "→ Prometheus alerts : http://localhost:9090/alerts\n",
  };
}
