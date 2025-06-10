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
    "¬",
}

KNOWN_TYPE_CONSTRUCTORS = {
    "Set",
    "Bool",
    "List",
    "Ordering",
    "Maybe",
    "Nat",
    "Char",
    "String",
    "IO",
    "Either",
    "Eq",
    "Show",
    "Ord",
    "succ"
}

BRACKET_PAIRS = {"{": "}", "⦃": "⦄", "(": ")"}


def extract_bracketed_tokens(s):
    tokens = []
    stack = []
    current = ""
    for c in s:
        if c in BRACKET_PAIRS:
            if current.strip():
                tokens.append(current.strip())
                current = ""
            stack.append((c, ""))
        elif stack and c == BRACKET_PAIRS[stack[-1][0]]:
            opener, content = stack.pop()
            content = content.strip()
            if content:
                tokens.append(f"{opener}{content}{c}")
        elif stack:
            stack[-1] = (stack[-1][0], stack[-1][1] + c)
        elif c in [" ", "→", ","]:
            if current.strip():
                tokens.append(current.strip())
                current = ""
            if c in ["→", ","]:
                tokens.append(c)
        else:
            current += c
    if current.strip():
        tokens.append(current.strip())
    return tokens


def classify_token(tok, declared_variables, type_constructors):
    if tok.isdigit():
        return "num"
    elif tok in declared_variables:
        return "var"
    elif tok in KNOWN_OPERATORS or tok in type_constructors:
        return "oper"
    elif re.fullmatch(r"[a-zA-Z_≤≥≠≡⊔⊓′₀₁₂₃₄₅₆₇₈₉][\w′₀₁₂₃₄₅₆₇₈₉≤≥≠≡⊔⊓']*", tok):
        return "var"
    else:
        return "unknown"


def classify_signature(segments, declared_variables, type_constructors):
    combined = " ".join(segments)
    tokens = re.split(r"[ \t\n\r\f\v:→(){}⦃⦄]+", combined)
    variables, operators, numbers = set(), set(), set()

    for tok in tokens:
        tok = tok.strip(",")
        if not tok:
            continue
        kind = classify_token(tok, declared_variables, type_constructors)
        if kind == "num":
            numbers.add(tok)
        elif kind == "var":
            variables.add(tok)
        elif kind == "oper":
            operators.add(tok)

    return list(variables), list(operators), list(numbers)


def annotate_piece(piece, declared_variables, type_constructors):
    piece = piece.strip()
    if ":" in piece:
        left, right = map(str.strip, piece.split(":", 1))
        right_annot = " ".join(
            annotate_signature(right, declared_variables, type_constructors)
        )
        return f"var {left} : {right_annot}"
    kind = classify_token(piece, declared_variables, type_constructors)
    if kind in {"var", "oper", "num"}:
        return f"{kind} {piece}"
    return piece


def annotate_signature(signature, declared_variables, type_constructors):
    tokens = extract_bracketed_tokens(signature)
    result = []
    for tok in tokens:
        clean = tok.strip()
        if clean in ["→", ","]:
            result.append(clean)
        elif any(
            clean.startswith(b) and clean.endswith(BRACKET_PAIRS[b])
            for b in BRACKET_PAIRS
        ):
            b = next(b for b in BRACKET_PAIRS if clean.startswith(b))
            inner = clean[1:-1].strip()
            annotated_inner = (
                annotate_piece(inner, declared_variables, type_constructors)
                if ":" in inner
                else " ".join(
                    annotate_signature(inner, declared_variables, type_constructors)
                )
            )
            result.append(f"{b}{annotated_inner}{BRACKET_PAIRS[b]}")
        else:
            result.append(annotate_piece(clean, declared_variables, type_constructors))
    return result


def shallow_trace_piece(piece, declared_variables, type_constructors):
    piece = piece.strip()
    if ":" in piece:
        left = piece.split(":", 1)[0].strip()
        return f"var {left}"
    kind = classify_token(piece, declared_variables, type_constructors)
    if kind in {"var", "oper", "num"}:
        return f"{kind} {piece}"
    return None


def generate_shallow_trace(signature, declared_variables, type_constructors):
    tokens = extract_bracketed_tokens(signature)
    result = []
    for tok in tokens:
        clean = tok.strip()
        if clean in ["→", ","]:
            continue
        elif any(
            clean.startswith(b) and clean.endswith(BRACKET_PAIRS[b])
            for b in BRACKET_PAIRS
        ):
            b = next(b for b in BRACKET_PAIRS if clean.startswith(b))
            inner = clean[1:-1].strip()
            st_inner = (
                shallow_trace_piece(inner, declared_variables, type_constructors)
                if ":" in inner
                else ", ".join(
                    x
                    for x in generate_shallow_trace(
                        inner, declared_variables, type_constructors
                    )
                    if x
                )
            )
            result.append(f"{b}{st_inner}{BRACKET_PAIRS[b]}")
        else:
            piece = shallow_trace_piece(clean, declared_variables, type_constructors)
            if piece:
                result.append(piece)
    return result


class AgdaExtractor:
    decl_re = re.compile(
        r"^\s*([\w⁅⁆′≡≠≤≥⊓⊔⊤⊥∧∨∃∀λΣΠ⟦⟧⟨⟩·•□◯∞≜≔⇔⇒←→↔⇐⇑⇓⇨⇦∈∉∋∌⊆⊇⊂⊃∪∩-]+)\s*:\s*(.+?)\s*$",
        re.MULTILINE,
    )

    variable_re = re.compile(r"^\s*(private\s+)?variable\s+(.+)", re.MULTILINE)
    data_re = re.compile(
        r"(?m)^data\s+([^\s:]+)(?:\s+.*)?\s*:\s*.*?Set\s*where\s*((?:.*\n)*?)(?=^(\S|\Z))",
        re.MULTILINE,
    )
    record_re = re.compile(
        r"^\s*record\s+(\w+)\s*(?:\((.*?)\))?\s*:\s*Set", re.MULTILINE
    )
    module_re = re.compile(r"^\s*module\s+(\w+)\s*(?:\((.*?)\))?\s*where", re.MULTILINE)

    def __init__(self, root_dir):
        self.root_dir = root_dir

    def scan_lagda_files(self):
        lagda_files = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".lagda"):
                    lagda_files.append(os.path.join(root, file))
        return lagda_files
    
    def split_top_level_arrows(self, sig: str) -> List[str]:
        parts: List[str] = []
        cur: str = ""
        depth: int = 0
        i = 0
        while i < len(sig):
            ch = sig[i]
            if ch in "({⦃":
                depth += 1
            elif ch in ")}⦄":
                depth = max(depth - 1, 0)
            if depth == 0:
                if ch == "→":
                    parts.append(cur)
                    cur = ""
                    i += 1
                    continue
                if sig.startswith("->", i):
                    parts.append(cur)
                    cur = ""
                    i += 2
                    continue
            cur += ch
            i += 1
        parts.append(cur)
        return parts

    def extract_from_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        declared_variables = set()
        type_constructors = set(KNOWN_TYPE_CONSTRUCTORS)

        for var_match in self.variable_re.finditer(content):
            decl = var_match.group(2)
            for line in decl.split("\n"):
                parts = re.split(r"\s*:\s*", line)
                if len(parts) == 2:
                    names = parts[0].strip().split()
                    declared_variables.update(names)
        for data_match in list(self.data_re.finditer(content)):
            type_name, params, body = data_match.groups()
            type_constructors.add(type_name)
            if params:
                declared_variables.update(
                    [p.split(":")[0].strip() for p in params.split() if ":" in p]
                )
            constructors = re.findall(r"^\s*(\w+)\s*:", body, re.MULTILINE)
            type_constructors.update(constructors)

        for rec_match in self.record_re.finditer(content):
            type_name = rec_match.group(1)
            param_block = rec_match.group(2)
            type_constructors.add(type_name)
            if param_block:
                declared_variables.update(
                    [p.split(":")[0].strip() for p in param_block.split() if ":" in p]
                )

        for mod_match in self.module_re.finditer(content):
            param_block = mod_match.group(2)
            if param_block:
                declared_variables.update(
                    [p.split(":")[0].strip() for p in param_block.split() if ":" in p]
                )

        blocks = re.findall(r"(?ms)\\begin{code}(.*?)\\end{code}", content)
        blocks += re.findall(r"(?ms)```agda\s*(.*?)```", content)

        functions = []
        for block in blocks:
            block = re.sub(r"(?ms)\{\-.*?\-\}", "", block)
            cleaned_lines = [
                re.sub(r"--.*", "", line).strip()
                for line in block.splitlines()
                if line.strip()
            ]
            cleaned = "\n".join(cleaned_lines)

            for m in self.decl_re.finditer(cleaned):
                name, sig = m.group(1), m.group(2).strip()
                type_constructors.add(name)
                raw_parts = self.split_top_level_arrows(sig)
                parts = [p.strip().strip("⦃⦄") for p in raw_parts if p.strip()]
                # parts = [p.strip() for p in re.split(r"\s*→\s*", sig) if p.strip()]
                if len(parts) < 2:
                    continue

                input_types = parts[:-1]
                output_type = parts[-1]

                vars_, ops_, nums_ = classify_signature(
                    input_types + [output_type], declared_variables, type_constructors
                )
                annotated = " ".join(
                    annotate_signature(sig, declared_variables, type_constructors)
                )
                shallow = ", ".join(
                    generate_shallow_trace(sig, declared_variables, type_constructors)
                )

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
                        "annotated_signature": annotated,
                        "shallow_trace": shallow,
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
                fn["annotated_signature"],
                fn["shallow_trace"],
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
                      variables, operators, numbers,
                      annotated_signature, shallow_trace
                    ) VALUES %s ON CONFLICT(file_path,function_name,signature) DO NOTHING
                """
                execute_values(cur, insert_sql, rows)
            conn.commit()
