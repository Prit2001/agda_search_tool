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
CREATE TABLE IF NOT EXISTS agda_signatures (
    id SERIAL PRIMARY KEY,
    file_path TEXT,
    function_name TEXT,
    signature TEXT,
    input_types TEXT[],
    output_type TEXT,
    variables TEXT[],
    operators TEXT[],
    numbers TEXT[],
    line_no INT,
    annotated_signature TEXT,
    shallow_trace TEXT,
    UNIQUE (file_path, function_name, signature)
);
"""


CREATE_HISTORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS search_history (
    id      SERIAL PRIMARY KEY,
    query   TEXT UNIQUE,
    ts      TIMESTAMPTZ DEFAULT now()
);
"""
