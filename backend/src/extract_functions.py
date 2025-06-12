import os
import re
from typing import List, Tuple, Dict

SEPARATOR_TOKENS = {"∀", "->", "→", "λ", ":"}
SPECIAL_BRACKETS = ["{", "⦃", "("]

class AgdaExtractor:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def collect_functions(self):
        all_functions = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".lagda"):
                    full_path = os.path.join(root, file)
                    with open(full_path, encoding='utf-8') as f:
                        content = f.read()
                    code_blocks = self.extract_code_blocks(content)
                    declared_vars = self.extract_global_declarations(code_blocks)
                    functions = self.extract_signatures(code_blocks, full_path, declared_vars)
                    all_functions.extend(functions)
        return all_functions

    def extract_code_blocks(self, text: str) -> str:
        blocks = re.findall(r"\\begin{code}(.*?)\\end{code}", text, re.DOTALL)
        return "\n".join(blocks)

    def extract_global_declarations(self, code: str) -> Dict[str, str]:
        declared = {}
        for match in re.findall(r"variable\s+(.*?)\s*(?=\n\S|\Z)", code, re.DOTALL):
            for line in match.strip().splitlines():
                if ':' not in line:
                    continue
                parts = [x.strip() for x in line.split(":", 1)]
                if len(parts) == 2:
                    names, _ = parts
                    for name in names.split():
                        declared[name] = "variable"
        for match in re.finditer(r"(data|record|module)\s+\S+\s+\((.*?)\)", code):
            for param in match.group(2).split(","):
                name_type = param.strip().split(":")
                if len(name_type) == 2:
                    for name in name_type[0].split():
                        declared[name.strip()] = "variable"
        return declared

    def extract_signatures(self, code: str, file_path: str, declared: Dict[str, str]):
        signatures = []
        seen_signatures = set()
        cleaned_code = re.sub(r"\{\-.*?\-\}", "", code, flags=re.DOTALL)
        lines = [
            re.sub(r"--.*", "", line).strip()
            for line in cleaned_code.splitlines()
            if line.strip()
        ]
        code = "\n".join(lines)

        decl_re = re.compile(
            r"^\s*([\w⁅⁆′≡≠≤≥⊓⊔⊤⊥∧∨∃∀λΣΠ⟦⟧⟨⟩·•□◯∞≜≔⇔⇒←→↔⇐⇑⇓⇨⇦∈∉∋∌⊆⊇⊂⊃∪∩-]+)\s*:\s*(.+?)\s*$",
            re.MULTILINE,
        )
        signature_matches = decl_re.findall(code)

        for name, sig in signature_matches:
            sig = sig.strip()
            if not sig or "→" not in sig and "->" not in sig:
                continue
            if (file_path, name, sig) in seen_signatures:
                continue
            seen_signatures.add((file_path, name, sig))

            sig_cleaned = sig.replace("->", "→")
            synthetic_vars = self.extract_synthetic_variables(sig_cleaned)
            tokens = self.tokenize_signature(sig_cleaned)
            vars_, ops, nums = self.classify_tokens(tokens, declared, synthetic_vars)
            annotated = self.annotate_inline(sig_cleaned, vars_, ops, nums)
            shallow_trace = self.shallow_trace(sig_cleaned, vars_, ops, nums)
            inputs, output = self.split_signature(sig_cleaned)
            signatures.append({
                "file_path": file_path,
                "function_name": name,
                "signature": sig,  # Only type part
                "input_types": inputs,
                "output_type": output,
                "variables": list(vars_),
                "operators": list(ops),
                "numbers": list(nums),
                "annotated_signature": annotated,
                "shallow_trace": shallow_trace
            })
        return signatures

    def extract_synthetic_variables(self, sig: str) -> set:
        synthetic_vars = set()
        bracketed = re.findall(r"[{⦃(](.*?)[}⦄)]", sig)
        for block in bracketed:
            parts = block.split(":")
            if len(parts) == 2:
                lhs = parts[0].strip()
                for name in lhs.split():
                    synthetic_vars.add(name)
        return synthetic_vars

    def split_signature(self, sig: str) -> Tuple[List[str], str]:
        parts = []
        bracket_stack = []
        current = ""

        for char in sig:
            if char in "({⦃":
                bracket_stack.append(char)
            elif char in ")}⦄":
                if bracket_stack:
                    bracket_stack.pop()
            if char == "→" and not bracket_stack:
                parts.append(current.strip())
                current = ""
            else:
                current += char
        parts.append(current.strip())
        return parts[:-1], parts[-1]

    def tokenize_signature(self, sig: str) -> List[str]:
        return re.findall(r"[a-zA-Z₀-₉\d′_≤≥≡≠⊕⊗⊓⊔∧∨+\-*/×÷<>\.]+", sig)

    def classify_tokens(self, tokens: List[str], declared: Dict[str, str], synthetic_vars: set) -> Tuple[set, set, set]:
        variables, operators, numbers = set(), set(), set()
        for tok in tokens:
            if tok in SEPARATOR_TOKENS:
                continue
            elif re.fullmatch(r"\d+", tok):
                numbers.add(tok)
            elif tok in declared or tok in synthetic_vars:
                variables.add(tok)
            elif re.fullmatch(r"[A-Z]\w*", tok) and tok not in declared:
                operators.add(tok)
            elif re.search(r"[^\w]", tok):
                operators.add(tok)
            else:
                variables.add(tok)
        return variables, operators, numbers

    def annotate_inline(self, sig: str, vars_: set, ops: set, nums: set) -> str:
        def annotate_token(token: str) -> str:
            if token in vars_:
                return f"var {token}"
            elif token in ops:
                return f"oper {token}"
            elif token in nums:
                return f"num {token}"
            return token

        pattern = r"[a-zA-Z₀-₉\d′_≤≥≡≠⊕⊗⊓⊔∧∨+\-*/×÷<>\.]+"
        return re.sub(pattern, lambda m: annotate_token(m.group()), sig)

    def shallow_trace(self, sig: str, vars_: set, ops: set, nums: set) -> str:
        sig_clean = sig.replace("->", "→")
        parts = []
        bracket_stack = []
        current = ""

        for char in sig_clean:
            if char in "({⦃":
                bracket_stack.append(char)
            elif char in ")}⦄":
                if bracket_stack:
                    bracket_stack.pop()
            if char == "→" and not bracket_stack:
                parts.append(current.strip())
                current = ""
            else:
                current += char
        parts.append(current.strip())

        def annotate_segment(segment: str) -> str:
            pattern = r"[a-zA-Z₀-₉\d′_≤≥≡≠⊕⊗⊓⊔∧∨+\-*/×÷<>\.]+"
            return re.sub(pattern, lambda m: self.annotate_token_for_trace(m.group(), vars_, ops, nums), segment)

        return ", ".join(annotate_segment(part) for part in parts)

    def annotate_token_for_trace(self, token: str, vars_: set, ops: set, nums: set) -> str:
        if token in vars_:
            return f"var {token}"
        elif token in ops:
            return f"oper {token}"
        elif token in nums:
            return f"num {token}"
        return token

# --- Database logic ---

import psycopg2
from psycopg2.extras import execute_values
from config import DB_PARAMS, CREATE_TABLE_SQL

class DatabaseClient:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_PARAMS)
        self.ensure_table()

    def ensure_table(self):
        with self.conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        self.conn.commit()

    def insert_into_db(self, rows):
        insert_sql = """
        INSERT INTO agda_signatures (
            file_path, function_name, signature,
            input_types, output_type,
            variables, operators, numbers,
            annotated_signature, shallow_trace
        )
        VALUES %s
        ON CONFLICT (file_path, function_name, signature) DO NOTHING;
        """
        values = [
            (
                row["file_path"],
                row["function_name"],
                row["signature"],
                row["input_types"],
                row["output_type"],
                row["variables"],
                row["operators"],
                row["numbers"],
                row["annotated_signature"],
                row["shallow_trace"]
            )
            for row in rows
        ]
        with self.conn.cursor() as cur:
            execute_values(cur, insert_sql, values)
        self.conn.commit()
