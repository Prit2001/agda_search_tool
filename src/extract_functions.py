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


def classify_signature(segments, known_vars=None, known_ops=None):
    known_vars = set(known_vars or [])
    known_ops = set(known_ops or [])
    combined = " ".join(segments)
    tokens = re.split(r"[ \t\n\r\f\v:→(){}⦃⦄]+", combined)
    variables, operators, numbers = set(), set(), set()

    for tok in tokens:
        tok = tok.strip(",")
        if not tok:
            continue
        if tok.isdigit():
            numbers.add(tok)
        elif tok in KNOWN_OPERATORS or tok in KNOWN_TYPE_CONSTRUCTORS or tok in known_ops:
            operators.add(tok)
        elif tok in known_vars:
            variables.add(tok)
        elif re.fullmatch(r"[a-zA-Z_≤≥≠≡⊔⊓][\w≤≥≠≡⊔⊓₀₁₂₃₄₅₆₇₈₉′']*", tok):
            variables.add(tok)
        else:
            operators.add(tok)

    return list(variables), list(operators), list(numbers)


def annotate_piece(piece, known_vars=None, known_ops=None):
    known_vars = set(known_vars or [])
    known_ops = set(known_ops or [])
    piece = piece.strip()
    if ":" in piece:
        left, right = map(str.strip, piece.split(":", 1))
        return f"var {left} : {' '.join(annotate_signature(right, known_vars, known_ops))}"
    if piece.isdigit():
        return f"num {piece}"
    if piece in KNOWN_TYPE_CONSTRUCTORS or piece in KNOWN_OPERATORS or piece in known_ops:
        return f"oper {piece}"
    if piece in known_vars or re.fullmatch(r"[a-zA-Z_≤≥≠≡⊔⊓][\w≤≥≠≡⊔⊓₀₁₂₃₄₅₆₇₈₉′']*", piece):
        return f"var {piece}"
    return f"oper {piece}"


def annotate_signature(signature, known_vars=None, known_ops=None):
    tokens = extract_bracketed_tokens(signature)
    result = []
    for tok in tokens:
        clean = tok.strip()
        if clean in ['→', ',']:
            result.append(clean)
        elif any(clean.startswith(b) and clean.endswith(BRACKET_PAIRS[b]) for b in BRACKET_PAIRS):
            b = next(b for b in BRACKET_PAIRS if clean.startswith(b))
            inner = clean[1:-1].strip()
            annotated_inner = annotate_piece(inner, known_vars, known_ops) if ':' in inner else ' '.join(annotate_signature(inner, known_vars, known_ops))
            result.append(f"{b}{annotated_inner}{BRACKET_PAIRS[b]}")
        else:
            result.append(annotate_piece(clean, known_vars, known_ops))
    return result


def shallow_trace_piece(piece, known_vars=None, known_ops=None):
    known_vars = set(known_vars or [])
    known_ops = set(known_ops or [])
    piece = piece.strip()
    if ":" in piece:
        left = piece.split(":", 1)[0].strip()
        return f"var {left}"
    if piece.isdigit():
        return f"num {piece}"
    if piece in KNOWN_TYPE_CONSTRUCTORS or piece in KNOWN_OPERATORS or piece in known_ops:
        return f"oper {piece}"
    if piece in known_vars or re.fullmatch(r"[a-zA-Z_≤≥≠≡⊔⊓][\w≤≥≠≡⊔⊓₀₁₂₃₄₅₆₇₈₉′']*", piece):
        return f"var {piece}"
    return f"oper {piece}"


def generate_shallow_trace(signature, known_vars=None, known_ops=None):
    tokens = extract_bracketed_tokens(signature)
    result = []
    for tok in tokens:
        clean = tok.strip()
        if clean in ['→', ',']:
            result.append(clean)
        elif any(clean.startswith(b) and clean.endswith(BRACKET_PAIRS[b]) for b in BRACKET_PAIRS):
            b = next(b for b in BRACKET_PAIRS if clean.startswith(b))
            inner = clean[1:-1].strip()
            st_inner = shallow_trace_piece(inner, known_vars, known_ops) if ':' in inner else " ".join(
                x for x in generate_shallow_trace(inner, known_vars, known_ops) if x
            )
            result.append(f"{b}{st_inner}{BRACKET_PAIRS[b]}")
        else:
            piece = shallow_trace_piece(clean, known_vars, known_ops)
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
        self.declared_variables = set()
        self.declared_operators = set()

    def scan_lagda_files(self):
        lagda_files = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".lagda"):
                    lagda_files.append(os.path.join(root, file))
        return lagda_files

    def scan_declarations(self):
        data_re = re.compile(r"^\s*(data|record|module)\s+(\S+)\s*(\((.*?)\))?", re.MULTILINE)
        constructor_re = re.compile(r"^\s*([\w_′⁺⁻∷≡≠≤≥⊓⊔⊤⊥∧∨∃∀]+)\s*:", re.MULTILINE)
        for path in self.scan_lagda_files():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                blocks = re.findall(r"(?ms)\\begin{code}(.*?)\\end{code}", text)
                blocks += re.findall(r"(?ms)```agda\s*(.*?)```", text)

                for block in blocks:
                    for m in data_re.finditer(block):
                        kind, name, _, raw_params = m.groups()
                        if name:
                            self.declared_operators.add(name)
                        if raw_params:
                            params = re.findall(r"([a-zA-Z_][\w']*)\s*:", raw_params)
                            self.declared_variables.update(params)

                        if kind == "data":
                            after = block[m.end():].split("where", 1)
                            if len(after) > 1:
                                body = after[1]
                                for con in constructor_re.finditer(body):
                                    self.declared_operators.add(con.group(1).strip())
            except Exception as e:
                logging.warning(f"Declaration scan error in {path}: {e}")

    def extract_from_file(self, file_path):
        def split_top_level_arrows(sig):
            result = []
            current = ''
            stack = []
            i = 0
            while i < len(sig):
                c = sig[i]
                if c in BRACKET_PAIRS:
                    stack.append(BRACKET_PAIRS[c])
                    current += c
                elif stack and c == stack[-1]:
                    stack.pop()
                    current += c
                elif sig[i:i+1] == '→' and not stack:
                    result.append(current.strip())
                    current = ''
                elif sig[i:i+1] == '→':
                    current += '→'
                else:
                    current += c
                i += 1
            if current.strip():
                result.append(current.strip())
            return result

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
                parts = split_top_level_arrows(sig)
                if len(parts) < 2:
                    continue

                input_types, output_type = parts[:-1], parts[-1]

                vars_, ops_, nums_ = classify_signature(
                    parts, known_vars=self.declared_variables, known_ops=self.declared_operators
                )
                annotated = " ".join(annotate_signature(sig, self.declared_variables, self.declared_operators))
                shallow = " ".join(generate_shallow_trace(sig, self.declared_variables, self.declared_operators))

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
        self.scan_declarations()
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
