import os
import logging
import psycopg2
from psycopg2.extras import execute_values

from extract_functions import extract_functions_from_agda
from config import DB_PARAMS, CREATE_TABLE_SQL

logging.basicConfig(level=logging.INFO)

def scan_lagda_files(root_dir):
    lagda_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".lagda"):
                lagda_files.append(os.path.join(root, file))
    return lagda_files

def insert_into_db(rows):
    with psycopg2.connect(**DB_PARAMS) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            insert_sql = """
            INSERT INTO agda_signatures (
                file_path, function_name, signature, input_types, output_type,
                variables, operators, numbers
            ) VALUES %s
            """
            execute_values(cur, insert_sql, rows)
        conn.commit()

def main():
    root_dir = os.getenv("AGDA_PROJECT_DIRECTORY")
    all_rows = []

    for file_path in scan_lagda_files(root_dir):
        try:
            functions = extract_functions_from_agda(file_path)
            rel_path = os.path.relpath(file_path, start=root_dir)
            if functions:
                for fn in functions:
                    row = (
                        rel_path,
                        fn["name"],
                        fn["signature"],
                        fn["input_types"],
                        fn["output_type"],
                        fn["variables"],
                        fn["operators"],
                        fn["numbers"]
                    )
                    all_rows.append(row)
        except Exception as e:
            logging.error(f"Error in {file_path}: {e}")

    if all_rows:
        logging.info(f"Inserting {len(all_rows)} functions into the database.")
        insert_into_db(all_rows)
    else:
        logging.info("No functions to insert.")

if __name__ == "__main__":
    main()
