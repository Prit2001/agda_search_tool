# AGDA Search Tool

A full-stack search interface for exploring [Agda](https://agda.readthedocs.io/) codebases by type signature. Point it at any Agda project and instantly search for functions by name, signature, or structural pattern — with support for both **strict** and **loose** matching strategies.

---

## Features

- **Type-signature search** — query Agda functions by their type signatures
- **Strict & loose matching** — toggle between exact substring matching and a structural, token-aware search
- **Annotated results** — each result includes an annotated signature highlighting variables, operators, and numeric literals
- **Search history** — recent queries are persisted in PostgreSQL and accessible via a sidebar drawer
- **One-command indexing** — scan an entire Agda project and populate the database with a single CLI invocation

---

## Architecture

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19 · React Router · Ant Design |
| **Backend** | Python 3.9+ · Flask · psycopg2 |
| **Database** | PostgreSQL 14+ |
| **Package Manager** | Poetry (Python) · npm (JavaScript) |

---

## Getting Started

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| PostgreSQL | 14+ | [postgresql.org/download](https://www.postgresql.org/download/) |
| Node.js | 20+ (LTS) | [nodejs.org](https://nodejs.org/) |
| Python | 3.9+ | [python.org/downloads](https://www.python.org/downloads/) |
| Poetry | latest | [python-poetry.org](https://python-poetry.org/docs/#installation) |
| Git | any | [git-scm.com](https://git-scm.com/) |

### 1 — Clone the Repository

```bash
git clone https://gitlab.rhrk.uni-kl.de/dek50dyx/agda_search_tool.git
cd agda_search_tool
```

### 2 — Install Poetry

<details>
<summary><strong>macOS / Linux</strong></summary>

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```
</details>

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
# Then add %USERPROFILE%\.poetry\bin to your PATH
```
</details>

### 3 — Install Python Dependencies

```bash
poetry install
poetry env activate   # activates the project virtualenv
```

### 4 — Configure Environment Variables

```bash
cp sample.env .env
```

Edit `.env` at the project root:

```env
# Path to the Agda project you want to index
AGDA_PROJECT_DIRECTORY=/path/to/your/agda/project

# PostgreSQL connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agda_search
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Flask API port
PORT=5001
```

Create `frontend/.env`:

```env
DANGEROUSLY_DISABLE_HOST_CHECK=true
REACT_APP_API_URL=http://localhost:5001
```

> **Note:** `REACT_APP_API_URL` must match the host and port where the Flask API runs.

---

## Database Setup

**1. Start PostgreSQL** (if not already running):

```bash
# macOS (Homebrew)
brew services start postgresql@14

# Ubuntu / Debian
sudo service postgresql start
```

**2. Create the database:**

```bash
createdb agda_search
```

**3. Index your Agda project** (creates tables and inserts signatures):

```bash
python backend/src/main.py
```

This parses every `.lagda` file under `AGDA_PROJECT_DIRECTORY`, extracts type signatures, and stores them in the `agda_signatures` table.

---

## Running the Application

### Backend

From the project root (with your Poetry environment active):

```bash
python backend/src/app.py
```

The Flask API will start on **http://localhost:5001** by default.

### Frontend

In a **separate terminal**:

```bash
cd frontend
npm install
npm run start
```

The React UI will open at **http://localhost:3000** and proxy API requests to the Flask backend.

---


## Search Modes

| Mode | Description |
|------|-------------|
| **Strict** | Performs direct substring matching against stored signatures. Fast and precise — ideal when you know the exact type fragment. |
| **Loose** | Tokenises the query and matches structurally, accounting for variable names, operators, and type constructors. More forgiving for exploratory searches. |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `AGDA_PROJECT_DIRECTORY is not set` | Ensure your `.env` file exists at the project root and contains this variable. |
| `psycopg2` connection errors | Verify PostgreSQL is running and the credentials in `.env` are correct. |
| Frontend can't reach the API | Confirm `REACT_APP_API_URL` in `frontend/.env` matches the backend's host and port. Restart the React dev server after changing `.env`. |
| No search results | Run `python backend/src/main.py` to index your Agda project first. Ensure the project contains `.lagda` files. |

---
