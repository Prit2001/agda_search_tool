import os
import re
import logging
from typing import List, Tuple, Dict, Any

import psycopg2
from psycopg2.extras import execute_values

from config import DB_PARAMS, CREATE_TABLE_SQL


class AgdaScanner:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def scan_files(self) -> List[str]:
        matches: List[str] = []
        for root, _, filenames in os.walk(self.root_dir):
            for fn in filenames:
                if fn.endswith((".lagda")):
                    matches.append(os.path.join(root, fn))
        return matches


class AgdaParser:
    CODE_BLOCK_PATTERNS = [
        re.compile(r"(?ms)\\begin\{code\}(.*?)\\end\{code\}"),
        re.compile(r"(?ms)```agda\s*(.*?)```"),
    ]
    DECL_RE = re.compile(
        r"^\s*([\w⁅⁆′≡≠≤≥⊓⊔⊤⊥∧∨∃∀λΣΠ⟦⟧⟨⟩·•□◯∞≜≔⇔⇒←→↔⇐⇑⇓⇨⇦∈∉∋∌⊆⊇⊂⊃∪∩-]+)"
        r"\s*:\s*(.+?)\s*$",
        re.MULTILINE,
    )

    def extract(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks: List[str] = []
        for pat in self.CODE_BLOCK_PATTERNS:
            blocks.extend(pat.findall(content))

        results: List[Dict[str, Any]] = []
        for block in blocks:
            block = re.sub(r"(?ms)\{\-.*?\-\}", "", block)
            lines = [re.sub(r"--.*", "", L).rstrip() for L in block.splitlines()]
            text = "\n".join([L for L in lines if L.strip()])

            for m in self.DECL_RE.finditer(text):
                name, sig = m.group(1), m.group(2).strip()
                parts = [p.strip() for p in re.split(r"\s*→\s*", sig) if p.strip()]
                if len(parts) < 2:
                    continue

                results.append(
                    {
                        "name": name,
                        "signature": sig,
                        "input_types": parts[:-1],
                        "output_type": parts[-1],
                    }
                )
        return results


def build_signature_parts(parts: List[str]) -> List[str]:
    out: List[str] = []

    if parts and parts[0].startswith("∀"):
        m = re.search(r"\{([^}]*)\}", parts[0])
        if m:
            for v in m.group(1).split():
                out.append(f"[{v} var]")
        parts = parts[1:]

    op_pat = re.compile(
        r"^([A-Za-z_]\w*)\s*(≤|<|≥|>|≡|≠|::|\+\+|⊕|⊗|⊓|⊔|∧|∨)\s*([A-Za-z_]\w*)$"
    )
    for part in parts:
        for seg in re.split(r"[,;]\s*", part):
            seg = seg.strip()
            m = op_pat.match(seg)
            if m:
                lhs, op, rhs = m.groups()
                out.append(f"[{lhs} var -> {op} op -> {rhs} var]")
            else:
                if re.match(r"^[A-Za-z_]\w*$", seg):
                    out.append(f"[{seg} var]")
                else:
                    out.append(f"[{seg}]")
    return out


class DatabaseClient:
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def ensure_schema(self) -> None:
        with psycopg2.connect(**self.params) as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)

    def insert(self, rows: List[Tuple[Any, ...]]) -> int:
        insert_sql = """
            INSERT INTO agda_signatures (
              file_path,
              function_name,
              signature,
              input_types,
              output_type,
              signature_parts
            ) VALUES %s
            ON CONFLICT (file_path, function_name, signature) DO NOTHING
        """
        with psycopg2.connect(**self.params) as conn:
            with conn.cursor() as cur:
                execute_values(cur, insert_sql, rows)
                return cur.rowcount


def extract_and_persist(root_dir: str) -> int:
    logging.info(f"Scanning {root_dir} for lagda files")
    scanner = AgdaScanner(root_dir)
    parser_ = AgdaParser()
    db = DatabaseClient(DB_PARAMS)

    db.ensure_schema()

    all_rows: List[Tuple[Any, ...]] = []
    for fp in scanner.scan_files():
        rel = os.path.relpath(fp, start=root_dir)
        try:
            for sig in parser_.extract(fp):
                parts = sig["input_types"] + [sig["output_type"]]
                sig_parts = build_signature_parts(parts)
                all_rows.append(
                    (
                        rel,
                        sig["name"],
                        sig["signature"],
                        sig["input_types"],
                        sig["output_type"],
                        sig_parts,
                    )
                )
        except Exception as e:
            logging.error(f"Error parsing {rel}: {e}")

    if not all_rows:
        logging.info("No functions found.")
        return 0

    inserted = db.insert(all_rows)
    logging.info(f"Found {len(all_rows)} functions")
    return inserted
