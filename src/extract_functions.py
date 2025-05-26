import os
import re
import logging
from typing import List, Tuple, Dict, Any

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

IGNORED_TYPES = {
    "Ordering",
    "List",
    "Set",
    "Tuple",
    "Bool",
    "String",
    "Char",
    "char",
    "λ",
    "⟦",
    "⟧",
    "∀",
}


def classify_signature(parts: List[str]) -> Tuple[List[str], List[str], List[str]]:
    text = " ".join(parts)
    tokens = re.split(r"[\s,:→(){}⦃⦄]+", text)
    vars_, ops_, nums_ = set(), set(), set()
    for tok in tokens:
        if not tok or tok == "_" or tok in IGNORED_TYPES:
            continue
        if tok.isdigit():
            nums_.add(tok)
        elif tok in KNOWN_OPERATORS:
            ops_.add(tok)
        else:
            vars_.add(tok)
    return list(vars_), list(ops_), list(nums_)


def build_signature_parts(parts: List[str]) -> List[str]:
    out: List[str] = []
    if parts and parts[0].startswith("∀"):
        m = re.search(r"\{([^}]*)\}", parts[0])
        if m:
            names = re.findall(r"([A-Za-z_][\w≡]*)\s*:", m.group(1))
            for v in names:
                if v not in IGNORED_TYPES:
                    out.append(f"[{v} var]")
        parts = parts[1:]
    op_pat = re.compile(
        r"^([A-Za-z_]\w*)\s*(≤|<|≥|>|≡|≠|::|\+\+|⊕|⊗|⊓|⊔|∧|∨)\s*([A-Za-z_]\w*)$"
    )
    for part in parts:
        for raw in re.split(r"[,;]\s*", part):
            seg = raw.strip().strip("(){}⦃⦄")
            if not seg or seg == "_":
                continue
            if ":" in seg:
                seg = seg.split(":", 1)[0].strip()
                if not seg:
                    continue
            tokens = seg.split()
            if not tokens:
                continue
            if tokens[0] in IGNORED_TYPES:
                tokens = tokens[1:]
                if not tokens:
                    continue
            if len(tokens) == 1:
                tok = tokens[0]
                if tok.isdigit():
                    out.append(f"[{tok} num]")
                elif tok in KNOWN_OPERATORS:
                    out.append(f"[{tok} op]")
                elif tok not in IGNORED_TYPES:
                    out.append(f"[{tok} var]")
                continue
            joined = " ".join(tokens)
            m = op_pat.match(joined)
            if m:
                lhs, op, rhs = m.groups()
                out.append(f"[{lhs} var -> {op} op -> {rhs} var]")
            else:
                for t in tokens:
                    if not t or t == "_" or t in IGNORED_TYPES:
                        continue
                    if t.isdigit():
                        out.append(f"[{t} num]")
                    elif t in KNOWN_OPERATORS:
                        out.append(f"[{t} op]")
                    else:
                        out.append(f"[{t} var]")
    return out


class AgdaScanner:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def scan_files(self) -> List[str]:
        files = []
        for root, _, fns in os.walk(self.root_dir):
            for fn in fns:
                if fn.endswith((".lagda")):
                    files.append(os.path.join(root, fn))
        return files


class AgdaParser:
    CODE_BLOCK_PATTERNS = [
        re.compile(r"(?ms)\\begin\{code\}(.*?)\\end\{code\}"),
        re.compile(r"(?ms)```agda\s*(.*?)```"),
    ]
    DECL_RE = re.compile(
        r"^\s*([\w⁅⁆′≡≠≤≥⊓⊔⊤⊥∧∨∃∀λΣΠ⟦⟧⟨⟩·•□◯∞≜≔⇔⇒←→↔⇐⇑⇓⇨⇦∈∉∋∌⊆⊇⊂⊃∪∩-]+)\s*:\s*(.+?)\s*$",
        re.MULTILINE,
    )

    def extract(self, fp: str) -> List[Dict[str, Any]]:
        text = open(fp, encoding="utf-8").read()
        blocks = []
        for p in self.CODE_BLOCK_PATTERNS:
            blocks += p.findall(text)
        res = []
        for b in blocks:
            b = re.sub(r"(?ms)\{\-.*?\-\}", "", b)
            lines = [re.sub(r"--.*", "", L).rstrip() for L in b.splitlines()]
            txt = "\n".join([L for L in lines if L.strip()])
            for m in self.DECL_RE.finditer(txt):
                name, sig = m.group(1), m.group(2).strip()
                parts = [p.strip() for p in re.split(r"\s*→\s*", sig) if p.strip()]
                if len(parts) < 2:
                    continue
                res.append(
                    {
                        "name": name,
                        "signature": sig,
                        "input_types": parts[:-1],
                        "output_type": parts[-1],
                    }
                )
        return res


class DatabaseClient:
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def ensure_schema(self):
        with psycopg2.connect(**self.params) as c:
            with c.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)

    def insert(self, rows: List[Tuple[Any, ...]]) -> int:
        sql = """
        INSERT INTO agda_signatures(
        file_path, function_name, signature,
        input_types, output_type, signature_parts,
        variables, operators, numbers
        ) VALUES %s ON CONFLICT(file_path,function_name,signature) DO NOTHING
        """
        with psycopg2.connect(**self.params) as c:
            with c.cursor() as cur:
                execute_values(cur, sql, rows)
                return cur.rowcount


def extract_and_persist(root_dir: str) -> int:
    logging.info(f"Scanning {root_dir}")
    s = AgdaScanner(root_dir)
    p = AgdaParser()
    db = DatabaseClient(DB_PARAMS)
    db.ensure_schema()
    rows = []
    for fp in s.scan_files():
        rel = os.path.relpath(fp, root_dir)
        for sig in p.extract(fp):
            parts = sig["input_types"] + [sig["output_type"]]
            sp = build_signature_parts(parts)
            vs, os_, ns = classify_signature(parts)
            rows.append(
                (
                    rel,
                    sig["name"],
                    sig["signature"],
                    sig["input_types"],
                    sig["output_type"],
                    sp,
                    vs,
                    os_,
                    ns,
                )
            )
    if not rows:
        return 0
    logging.info(f"Found {len(rows)} functions")
    return db.insert(rows)
