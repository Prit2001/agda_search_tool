import os
import re
import logging
import psycopg2
from psycopg2.extras import execute_values

from config import DB_PARAMS, CREATE_TABLE_SQL

KNOWN_OPERATORS = {
    "→",
    "+",
    "-",
    "*",
    "/",
    "×",
    "÷",
    "≡",
    "≠",
    "<",
    ">",
    "≤",
    "≥",
    "::",
    "++",
    "⊕",
    "⊗",
    "⊓",
    "⊔",
    "∧",
    "∨",
}


def classify_signature(segments):
    combined = " ".join(segments)
    tokens = re.split(r"[ \t\n\r\f\v:→(){}⦃⦄]+", combined)
    variables, operators, numbers = set(), set(), set()

    for tok in tokens:
        tok = tok.strip(",")
        if not tok:
            continue
        if tok.isdigit():
            numbers.add(tok)
        elif tok in KNOWN_OPERATORS:
            operators.add(tok)
        elif re.match(r"^[a-z_][\w']*$", tok):
            variables.add(tok)

    return list(variables), list(operators), list(numbers)


class AgdaExtractor:
    decl_re = re.compile(
        r"^\s*([\w⁅⁆′≡≠≤≥⊓⊔⊤⊥∧∨∃∀λΣΠ⟦⟧⟨⟩·•□◯∞≜≔⇔⇒←→↔⇐⇑⇓⇨⇦∈∉∋∌⊆⊇⊂⊃∪∩-]+)"
        r"\s*:\s*(.+?)\s*$",
        re.MULTILINE,
    )

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def scan_lagda_files(self):
        lagda_files = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".lagda"):
                    lagda_files.append(os.path.join(root, file))
        return lagda_files

    def extract_from_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = re.findall(r"(?ms)\\begin{code}(.*?)\\end{code}", content)
        blocks += re.findall(r"(?ms)```agda\s*(.*?)```", content)

        functions = []
        for block in blocks:
            block = re.sub(r"(?ms)\{\-.*?\-\}", "", block)
            cleaned_lines = []
            for line in block.splitlines():
                line = re.sub(r"--.*", "", line).strip()
                if line:
                    cleaned_lines.append(line)
            cleaned = "\n".join(cleaned_lines)

            for m in self.decl_re.finditer(cleaned):
                name, sig = m.group(1), m.group(2).strip()
                parts = [p.strip() for p in re.split(r"\s*→\s*", sig) if p.strip()]
                if len(parts) < 2:
                    continue

                input_types, output_type = parts[:-1], parts[-1]
                vars_, ops_, nums_ = classify_signature(parts)

                functions.append(
                    {
                        "file_path": os.path.relpath(file_path, self.root_dir),
                        "name": name,
                        "signature": sig,
                        "input_types": input_types,
                        "output_type": output_type,
                        "variables": vars_,
                        "operators": ops_,
                        "numbers": nums_,
                    }
                )

        return functions

    def collect_functions(self):
        all_rows = []
        for path in self.scan_lagda_files():
            try:
                all_rows.extend(self.extract_from_file(path))
            except Exception as e:
                logging.error(f"Error in {path}: {e}")
        return all_rows


class DatabaseClient:
    def __init__(self):
        self.db_params = DB_PARAMS
        self.create_sql = CREATE_TABLE_SQL

    def insert_into_db(self, functions):
        rows = [
            (
                fn["file_path"],
                fn["name"],
                fn["signature"],
                fn["input_types"],
                fn["output_type"],
                fn["variables"],
                fn["operators"],
                fn["numbers"],
            )
            for fn in functions
        ]

        with psycopg2.connect(**self.db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(self.create_sql)
                insert_sql = """
                    INSERT INTO agda_signatures (
                      file_path, function_name, signature,
                      input_types, output_type,
                      variables, operators, numbers
                    ) VALUES %s
                """
                execute_values(cur, insert_sql, rows)
            conn.commit()
