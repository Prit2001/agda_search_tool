import re
import os
import psycopg2
from psycopg2.extras import execute_values
import logging

from config import CREATE_TABLE_SQL, DB_PARAMS


def extract_functions_from_agda(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = []
    blocks += re.findall(r"(?ms)\\begin\{code\}(.*?)\\end\{code\}", content)
    blocks += re.findall(r"(?ms)```agda\s*(.*?)```", content)

    decl_re = re.compile(r"^\s*([\w-]+)\s*:\s*(.+?)\s*$", re.MULTILINE)
    functions = []

    for block in blocks:
        block = re.sub(r"(?ms)\{\-.*?\-\}", "", block)

        cleaned = []
        for line in block.splitlines():
            line = re.sub(r"--.*", "", line)
            if line.strip():
                cleaned.append(line)
        block = "\n".join(cleaned)

        for m in decl_re.finditer(block):
            name, sig = m.group(1), m.group(2).strip()

            sig = re.sub(r"^(∀|forall)[^→\-]*[→\-]\s*", "", sig)

            parts = re.split(r"\s*→\s*|\s*->\s*", sig)

            parts = [
                p.strip() for p in parts if p.strip() and not p.strip().startswith("{")
            ]

            if len(parts) < 2:
                continue

            input_types = parts[:-1]
            output_type = parts[-1]

            if not name[0].islower():
                continue

            functions.append(
                {"name": name, "input_types": input_types, "output_type": output_type}
            )

    return functions


def extract_from_project(directory):
    all_functions = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".lagda"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, start=directory)
                funcs = extract_functions_from_agda(file_path)
                for f in funcs:
                    all_functions.append(
                        (f["name"], f["input_types"], f["output_type"], rel_path)
                    )
    return all_functions


def ensure_table_exists() -> None:
    conn = psycopg2.connect(**DB_PARAMS)
    print(conn)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)
                logging.info("Ensured agda_functions table exists.")
                cur.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                      agda_functions_unique_idx
                    ON agda_functions(name, input_types, file_path);
                    """
                )
                logging.info("Ensured unique index on agda_functions.")
    finally:
        conn.close()


def save_functions_to_db(directory):
    records = extract_from_project(directory)
    if not records:
        logging.info("No functions found to insert.")
        return

    ensure_table_exists()

    insert_sql = (
        "INSERT INTO agda_functions"
        " (name, input_types, output_type, file_path)"
        " VALUES %s"
        " ON CONFLICT (name, input_types, file_path) DO NOTHING"
    )

    conn = psycopg2.connect(**DB_PARAMS)
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, insert_sql, records)
        logging.info("Inserted %d new records into the database", len(records))
    finally:
        conn.close()
