import os
import logging

from extract_functions import AgdaExtractor, DatabaseClient

logging.basicConfig(level=logging.INFO)

def main():
    root_dir = os.getenv("AGDA_PROJECT_DIRECTORY")
    if not root_dir:
        logging.error("Environment variable AGDA_PROJECT_DIRECTORY is not set.")
        return

    extractor = AgdaExtractor(root_dir)
    functions = extractor.collect_functions()

    if functions:
        logging.info(f"Inserting {len(functions)} functions into the database.")
        db = DatabaseClient()
        db.insert_into_db(functions)
    else:
        logging.info("No functions to insert.")

if __name__ == "__main__":
    main()
