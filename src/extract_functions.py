import os
import re
import logging
import psycopg2
from psycopg2.extras import execute_values

from config import DB_PARAMS, CREATE_TABLE_SQL

KNOWN_OPERATORS = {
    "→", "+", "-", "*", "/", "×", "÷", "≡", "≠", "<", ">", "≤", "≥", "::", "++",
    "⊕", "⊗", "⊓", "⊔", "∧", "∨"
}

KNOWN_TYPE_CONSTRUCTORS = {
    "Set", "Bool", "List", "Ordering", "Maybe", "Nat", "Char", "String", "IO", "Either", "Eq", "Show", "Ord"
}

BRACKET_PAIRS = {
    '{': '}',
    '⦃': '⦄',
    '(': ')'
}

def extract_bracketed_tokens(s):
    tokens = []
    stack = []
    current = ''
    for c in s:
        if c in BRACKET_PAIRS:
            if current.strip():
                tokens.append(current.strip())
                current = ''
            stack.append((c, ''))
        elif stack and c == BRACKET_PAIRS[stack[-1][0]]:
            opener, content = stack.pop()
            content = content.strip()
            if content:
                tokens.append(f"{opener}{content}{c}")
        elif stack:
            stack[-1] = (stack[-1][0], stack[-1][1] + c)
        elif c in [' ', '→', ',']:
            if current.strip():
                tokens.append(current.strip())
                current = ''
            if c in ['→', ',']:
                tokens.append(c)
        else:
            current += c
    if current.strip():
        tokens.append(current.strip())
    return tokens

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
        elif tok in KNOWN_OPERATORS or tok in KNOWN_TYPE_CONSTRUCTORS:
            operators.add(tok)
        elif re.fullmatch(r"[A-Z]", tok):
            variables.add(tok)
        elif re.fullmatch(r"[a-zA-Z_≤≥≠≡⊔⊓][\w≤≥≠≡⊔⊓']*", tok):
            variables.add(tok)

    return list(variables), list(operators), list(numbers)


def annotate_piece(piece):
    piece = piece.strip()
    if ":" in piece:
        left, right = map(str.strip, piece.split(":", 1))
        return f"var {left} : {' '.join(annotate_signature(right))}"
    if piece.isdigit():
        return f"num {piece}"
    if piece in KNOWN_TYPE_CONSTRUCTORS or piece in KNOWN_OPERATORS:
        return f"oper {piece}"
    if re.fullmatch(r"[a-zA-Z_≤≥≠≡⊔⊓][\w≤≥≠≡⊔⊓']*", piece):
        return f"var {piece}"
    return piece


def annotate_signature(signature):
    tokens = extract_bracketed_tokens(signature)
    result = []
    for tok in tokens:
        clean = tok.strip()
        if clean in ['→', ',']:
            result.append(clean)
        elif any(clean.startswith(b) and clean.endswith(BRACKET_PAIRS[b]) for b in BRACKET_PAIRS):
            b = next(b for b in BRACKET_PAIRS if clean.startswith(b))
            inner = clean[1:-1].strip()
            annotated_inner = annotate_piece(inner) if ':' in inner else ' '.join(annotate_signature(inner))
            result.append(f"{b}{annotated_inner}{BRACKET_PAIRS[b]}")
        else:
            result.append(annotate_piece(clean))
    return result


def shallow_trace_piece(piece):
    piece = piece.strip()
    if ":" in piece:
        left = piece.split(":", 1)[0].strip()
        return f"var {left}"
    if piece.isdigit():
        return f"num {piece}"
    if piece in KNOWN_TYPE_CONSTRUCTORS:
        return None
    if piece in KNOWN_OPERATORS:
        return f"oper {piece}"
    if re.fullmatch(r"[a-zA-Z_≤≥≠≡⊔⊓][\w≤≥≠≡⊔⊓']*", piece):
        return f"var {piece}"
    return None


def generate_shallow_trace(signature):
    tokens = extract_bracketed_tokens(signature)
    result = []
    for tok in tokens:
        clean = tok.strip()
        if clean in ['→', ',']:
            result.append(clean)
        elif any(clean.startswith(b) and clean.endswith(BRACKET_PAIRS[b]) for b in BRACKET_PAIRS):
            b = next(b for b in BRACKET_PAIRS if clean.startswith(b))
            inner = clean[1:-1].strip()
            st_inner = shallow_trace_piece(inner) if ':' in inner else " ".join(
                x for x in generate_shallow_trace(inner) if x
            )
            result.append(f"{b}{st_inner}{BRACKET_PAIRS[b]}")
        else:
            piece = shallow_trace_piece(clean)
            if piece:
                result.append(piece)
    return result


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

                input_types_raw, output_type_raw = parts[:-1], parts[-1]

                input_types = [t for t in input_types_raw if t not in KNOWN_TYPE_CONSTRUCTORS]
                output_type = "" if output_type_raw in KNOWN_TYPE_CONSTRUCTORS else output_type_raw

                vars_, ops_, nums_ = classify_signature(input_types + ([output_type] if output_type else []))
                annotated = " ".join(annotate_signature(sig))
                shallow = " ".join(generate_shallow_trace(sig))

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
                    ) VALUES %s
                """
                execute_values(cur, insert_sql, rows)
            conn.commit()
