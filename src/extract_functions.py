import re
import os
import psycopg2
from psycopg2.extras import execute_values
import logging

from config import CREATE_TABLE_SQL, DB_PARAMS

# Basic operator list (→ included, "->" removed as per request)
KNOWN_OPERATORS = {
    "→", "+", "-", "*", "/", "×", "÷", "≡", "≠", "<", ">", "≤", "≥", "::", "++", "⊕", "⊗", "⊓", "⊔", "∧", "∨"
}

def extract_functions_from_agda(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = []
    blocks += re.findall(r"(?ms)\\begin{code}(.*?)\\end{code}", content)
    blocks += re.findall(r"(?ms)```agda\s*(.*?)```", content)

    decl_re = re.compile(
        r"^\s*([\w⁅⁆′≡≠≤≥⊓⊔⊤⊥∧∨∃∀λΣΠ⟦⟧⟨⟩·•□◯∞≜≔⇔⇒←→↔⇐⇑⇓⇨⇦∈∉∋∌⊆⊇⊂⊃∪∩-]+)\s*:\s*(.+?)\s*$",
        re.MULTILINE,
    )

    functions = []

    for block in blocks:
        block = re.sub(r"(?ms)\{\-.*?\-\}", "", block)
        cleaned = []
        for line in block.splitlines():
            line = re.sub(r"--.*", "", line)
            if line.strip():
                cleaned.append(line)
        block = "\n".join(cleaned)

        for m in decl_re.finditer(block):
            name, sig = m.group(1), m.group(2).strip()

            original_sig = sig
            parts = [p.strip() for p in re.split(r"\s*→\s*", sig) if p.strip()]
            if len(parts) < 2:
                continue

            input_types = parts[:-1]
            output_type = parts[-1]

            variables, operators, numbers = classify_signature(input_types + [output_type])

            functions.append({
                "name": name,
                "signature": original_sig,
                "input_types": input_types,
                "output_type": output_type,
                "variables": variables,
                "operators": operators,
                "numbers": numbers
            })

    return functions

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
