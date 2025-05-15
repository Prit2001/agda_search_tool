import os
from dotenv import load_dotenv
from extract_functions import save_functions_to_db


def main():
    load_dotenv()

    project_dir = os.getenv("AGDA_PROJECT_DIRECTORY")
    if not project_dir:
        raise RuntimeError("Please set AGDA_PROJECT_DIRECTORY in your .env file")

    save_functions_to_db(project_dir)


if __name__ == "__main__":
    main()
