import os
import logging

from extract_functions import extract_and_persist

logging.basicConfig(level=logging.INFO)


def main():
    root_dir = os.getenv("AGDA_PROJECT_DIRECTORY")
    if not root_dir:
        logging.error("Environment variable AGDA_PROJECT_DIRECTORY is not set.")
        return

    inserted = extract_and_persist(root_dir)
    logging.info(f"Inserted {inserted} new functions into the database.")


if __name__ == "__main__":
    main()
