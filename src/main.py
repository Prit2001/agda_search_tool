import os
from dotenv import load_dotenv
from extract_functions import extract_from_project


def main():
    load_dotenv()

    project_dir = os.getenv("AGDA_PROJECT_DIRECTORY")
    if not project_dir:
        raise RuntimeError("Please set AGDA_PROJECT_DIRECTORY in your .env file")

    functions = extract_from_project(project_dir)
    print(functions)


if __name__ == "__main__":
    main()
