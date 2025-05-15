# AGDA Search Tool

- **main.py**: Application entry‑point—parses CLI arguments and starts the search loop.
- **requirements.txt**: Python dependencies locked to tested versions.
- **README.md**: Project documentation.
- **.env/sample.env**: Environment variables consumed by main.py.


## Quick-start

# 1. Clone the repository
$ git clone https://gitlab.rhrk.uni-kl.de/dek50dyx/agda_search_tool.git
$ cd agda_search_tool

# 2. Install dependencies
$ pip install -r requirements.txt

# 3. Copy environment template and edit values
$ cp sample.env .env
$ nano .env  # set DB credentials, host, port, etc.

# 4. Initialise the database (one‑time)
$ createdb agda_search             # create database in PostgreSQL

# 5. Run the application
$ python main.py             