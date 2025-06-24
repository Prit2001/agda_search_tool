# AGDA Search Tool

- **main.py**: Application entry‑point—parses CLI arguments and starts the search loop.
- **requirements.txt**: Python dependencies locked to tested versions.
- **README.md**: Project documentation.
- **.env/sample.env**: Environment variables consumed by main.py.


A full-stack search interface over an Agda code database, with:

- **Backend**: Python + Flask + PostgreSQL  
- **Frontend**: React (Create React App)

---

## Table of Contents

1. [Prerequisites](#prerequisites)  
2. [Download & Install Dependencies](#download--install-dependencies)  
3. [Project Setup](#project-setup)  
4. [Database Initialization](#database-initialization)  
5. [Running the Backend](#running-the-backend)  
6. [Running the Frontend](#running-the-frontend)  
7. [Environment Variables](#environment-variables) 


### Prerequisites

You will need:

1. **PostgreSQL 14+**  
2. **Node.js 20+** (includes npm)  
3. **Python 3.9+**
4. **Git (to clone the repository)**



## Installing PostgreSQL

- **Windows / macOS**: Download the installer for PostgreSQL 14 or above from  
  https://www.postgresql.org/download/  
- **Ubuntu/Debian**:
```bash
$ sudo apt update
$ sudo apt install -y postgresql-14 postgresql-client-14
```
 
## Installing Node.js

Visit https://nodejs.org/ and download the LTS (v20+) installer for your OS.

Verify with:

$ node --version   # should be v20.x or higher
$ npm --version

## Installing Python 3.9+

Windows / macOS: https://www.python.org/downloads/

Linux (Ubuntu/Debian):
$ sudo apt update
$ sudo apt install -y python3 python3-venv python3-pip



### Download & Install Dependencies

# 1. Clone the repository
``` bash
$ git clone https://gitlab.rhrk.uni-kl.de/dek50dyx/agda_search_tool.git
$ cd agda_search_tool
```

# 2. Install Poetry

https://python-poetry.org/docs/#installation

- **macOS / Linux**  
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

- **Windows (PowerShell)**
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
# then add %USERPROFILE%\.poetry\bin to your PATH

# 3. Activate Poetry (Recommended)
From the project root, run:
``` bash
$ poetry install
$ poetry env activate
```



### Project Setup
# 1. Create your .env at the project root and copy-paste variables from sample.env to .env:
$ cp sample.env .env

# 2. Edit .env (in project root) to set your database details:
AGDA_PROJECT_DIRECTORY=/path/to/your/agda/project
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agda_search
DB_USER=your_db_user
DB_PASSWORD=your_db_password

PORT=5001

# 3. Frontend Environment
# Create frontend/.env

DANGEROUSLY_DISABLE_HOST_CHECK=true
# IMPORTANT: use the exact host:port where the Flask API runs.
# Example below assumes you started `python src/app.py --port 5001`
REACT_APP_API_URL=http://localhost:5001


### Database Initialization

# 1. Start the PostgreSQL server (if it isn’t already running):

# e.g. on Ubuntu/Debian:
$ sudo service postgresql start

# macOS with Homebrew:
brew services start postgresql@14

# 2. Create the database:
$ createdb agda_search

# 3. Initialize Database Schema
$ python backend/src/main.py

This will connect to your agda_search database and create the necessary table(s).



### Running the Backend
From the project root (with your environment active (via poetry shell)):

# Launch the Flask API server:
$ python backend/src/app.py

By default, the API listens on http://localhost:5001.



### Running the Frontend
1. Open a new terminal and navigate to the frontend folder:
$ cd frontend

2. Install React dependencies:
$ npm install

3. Create .env in frontend:
DANGEROUSLY_DISABLE_HOST_CHECK=true
# IMPORTANT: use the exact host:port where the Flask API runs.
# Example below assumes you started `python src/app.py --port 5001
REACT_APP_API_URL=http://localhost:5001

4. Start the React development server:
$ npm run start

The UI will open at http://localhost:3000 and communicate with your Flask backend.



### Environment Variables
.env at project root 

AGDA_PROJECT_DIRECTORY=/path/to/your/agda/project
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agda_search
DB_USER=your_db_user
DB_PASSWORD=your_db_password

PORT=5001

# Frontend (frontend/.env)
DANGEROUSLY_DISABLE_HOST_CHECK=true
# IMPORTANT: use the exact host:port where the Flask API runs.
# Example below assumes you started `python src/app.py --port 5001`
REACT_APP_API_URL=http://localhost:5001
