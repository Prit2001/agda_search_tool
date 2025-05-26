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
    id                SERIAL    PRIMARY KEY,
    file_path         TEXT      NOT NULL,
    function_name     TEXT      NOT NULL,
    signature         TEXT      NOT NULL,
    input_types       TEXT[]    NOT NULL,
    output_type       TEXT      NOT NULL,
    signature_parts   TEXT[]    NOT NULL,
    UNIQUE (file_path, function_name, signature)
);
"""
