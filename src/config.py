import os
from dotenv import load_dotenv


load_dotenv()

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "db"),
    "user": os.getenv("DB_USER", "user"),
    "password": os.getenv("DB_PASSWORD", "password"),
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agda_functions (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  input_types TEXT[] NOT NULL,
  output_type TEXT NOT NULL,
  file_path TEXT NOT NULL
);
"""
