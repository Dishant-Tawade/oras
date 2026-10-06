# ORAS: Resource Allocation Simulator

A multiplayer web simulation. Teams act as a company, split a yearly budget across departments (R&D, marketing, sales, operations and so on), and compete against each other over several years. Each year ends only when every team has locked in its decisions. An admin dashboard controls the session.

- **Backend:** Python, FastAPI, WebSockets, NumPy
- **Frontend:** React, Vite, Three.js
- **Storage:** plain JSON files by default (no database needed). Google Firestore is optional.
- **Scenarios:** 12 built in (US, Canada, India, UK × electric vehicles, pharma, hydration)

## What you need

- Python 3.11 or newer
- Node.js 20 or newer (includes npm)

## Run it

Open two terminals, both starting in the project folder.

### Terminal 1: backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export ADMIN_USERNAME=admin        # Windows (PowerShell): $env:ADMIN_USERNAME="admin"
export ADMIN_PASSWORD=choose-a-password
python main.py
```

The backend runs at http://localhost:8080. The first start creates a `backend/data/` folder that holds all saved state.

Admin login stays switched off unless both `ADMIN_USERNAME` and `ADMIN_PASSWORD` are set.

### Terminal 2: frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Single-server alternative

To serve everything from the backend on port 8080, build the frontend once:

```bash
cd frontend
npm install
npm run build
```

Then start the backend as above and open http://localhost:8080.

## Logging in

Click **Enter Platform**, then sign in.

| Who | Username | Password | Team key |
|---|---|---|---|
| Admin | the `ADMIN_USERNAME` you set | the `ADMIN_PASSWORD` you set | leave empty |
| Team controller | `user_team_1` … `user_team_6` | `password` | `team_1` … `team_6` |
| Team viewer | `viewer_1_team_1` … `viewer_3_team_6` | `password` | `team_1` … `team_6` |

These 24 demo accounts come from `backend/seed_users.json` and are copied to `backend/data/users.json` on first start. Each team's first login becomes its controller. The controller makes the decisions; viewers watch.

To try a full game on your own, use two browser windows (one normal, one private) so you can be the admin and a team at the same time. For a real multi-team game, add users from the admin dashboard (one at a time, or from an Excel file with the columns Username, Password, Team Key) and share the team keys.

## How a game runs

1. The admin picks a scenario in the dashboard (default: US electric vehicles).
2. Each team's controller reads the briefing and starts the simulation.
3. Teams set their allocations and lock the year. Year 1 has a 30-minute timer, later years 20 minutes. If the timer runs out, the server locks the team's saved draft automatically.
4. When every team has locked, results and the leaderboard are released and the next year begins.
5. After the final year, teams see their final score.

The admin can pause the game, kick players, and reset everything.

## Settings

Set these as environment variables before starting the backend.

| Variable | Default | Purpose |
|---|---|---|
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | not set | Admin login (required for the dashboard) |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:8080,http://localhost:3000` | Comma-separated browser origins allowed to call the API. `*` is rejected. |
| `ORAS_DATA_DIR` | `backend/data` | Where saved state is kept |
| `STORAGE_BACKEND` | `local` | `local` or `firestore` |
| `LOG_LEVEL` | `INFO` | Log detail |

Frontend (set before `npm run dev`): `ORAS_BACKEND` is the backend address the dev server forwards to (default `localhost:8080`). `VITE_WS_HOST` sets the WebSocket host at build time when the frontend and backend are on different hosts.

To start a fresh game, use **Reset** in the admin dashboard. To wipe everything including users, stop the backend and delete `backend/data/`.

## Limits of local storage

- Run exactly **one** backend process. Timers and live connections are held in memory.
- Use `python main.py` (or the Docker image), not multiple workers.

## Docker

```bash
docker build -t oras .
docker run -p 8080:8080 -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=choose-a-password \
  -v oras-data:/app/data oras
```

Open http://localhost:8080. The volume keeps state across restarts.

## Optional: Firestore

For deployments that need shared storage:

```bash
pip install -r backend/requirements-firestore.txt
export STORAGE_BACKEND=firestore
export GCP_PROJECT=your-project-id
export FIRESTORE_DATABASE="(default)"
```

Google credentials must be available (for example `gcloud auth application-default login`). On first start the users collection is filled from `seed_users.json`; set `FORCE_SEED_USERS=true` to overwrite it. For Docker, build with `--build-arg REQUIREMENTS=requirements-firestore.txt` and set `STORAGE_BACKEND=firestore`.

## Load testing

`tools/load_test/` has a browser-based test that plays full games with many simulated users, and a script that checks the log for synchronization errors. See the notes at the top of `browser_load_test.py`.

## Project layout

```
backend/
  main.py            app entry point
  auth.py            passwords, sessions, admin tokens
  storage.py         JSON-file and Firestore storage
  simulator.py       simulation engine
  scenarios/         one file per country and industry, plus news
  routers/           REST and WebSocket endpoints
  services/          game logic, timers, narrative text, insights
  seed_users.json    demo accounts
frontend/
  src/pages/         login, storyboard, game, admin
  src/components/    game tabs and shared pieces
tools/load_test/     load testing
```

## Adding a scenario

Copy `backend/scenarios/us_ev.py` and its `_news.py` file, edit the content, call `register_scenario()` with a new country and industry pair, and add the module name to `_SCENARIO_MODULES` in `backend/scenarios/__init__.py`.
