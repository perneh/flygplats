# Tournaments vs rounds and player statistics

## Concepts

| Concept | Tables | What it stores |
|--------|--------|----------------|
| **Tournament** | `tournaments`, `tournament_participants`, `tournament_flights` | Event metadata, who plays, handicap for grouping, flights (≤4 by handicap). |
| **Tournament score** | `scorecards`, `hole_scores` | **Gross strokes per hole (1–18)** for that event only — one scorecard per player after `POST …/start`. After `POST …/stop`, status is **finished** and gross lines are read-only via the API. |
| **Practice / tracked play** | `rounds`, `shots`, `holes` | A **round** is a player on a **course** over time; **shots** are GPS-tracked strokes (position, club, optional `distance` in metres). |
| **Player statistics** (`GET /players/{id}/performance`) | `rounds` + `shots` | Aggregates **tracked rounds only**. Updating tournament **HoleScore** rows does **not** change this endpoint. |

So: **tournament scorecards** and **round/shots** are separate unless you deliberately play a tracked round on the **same course** and **same calendar day** as the tournament — then **`POST /api/v1/tournaments/shot-detail`** can attach shot-level data (see below).

## Data flow

```
Tournament ──< Scorecard ──< HoleScore     ← gross per hole (POST /scorecards/hole)
     │
     └── course_id ──> Course ──< Hole      ← par per hole (leaderboard vs par)

Player ──< Round ──< Shot ──> Hole         ← performance API & shot-detail
```

- **Leaderboard** (`POST /api/v1/tournaments/leaderboard` with `{"tournament_id": …}`): joins scorecards + course holes → **rank**, **strokes per hole**, **to par** per hole and overall (only holes with a recorded stroke count toward gross / par sum).
- **Shot detail** (`POST /api/v1/tournaments/shot-detail` with `tournament_id` and `player_id`): finds a **Round** with the same `player_id`, `course_id` as the tournament, and `started_at` date (UTC) equal to `tournament.play_date`. If found, returns each shot’s **distance** (`Shot.distance`), **club**, order — plus per-hole **stroke_count** and **to_par**. If no round matches, the response has `matched_round_id: null` and `holes: []` (tournament-only scoring still works via the leaderboard).

## When does “statistics” update?

- **Tournament gross**: update with `POST /api/v1/scorecards/hole` (body includes `scorecard_id`, `hole_number`, `strokes`, `player_id`).
- **Performance / shot analytics**: update by recording **shots** on a **round** (`POST /shots`, etc.), not via tournament endpoints.
