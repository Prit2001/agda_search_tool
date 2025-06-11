from flask import Flask, request, jsonify
import psycopg2
import os
import re

from config import DB_PARAMS

app = Flask(__name__)


ASCII_TO_UNI = {"->": "→", "-->": "→"}


def normalize_arrows(txt: str) -> str:
    for a, u in ASCII_TO_UNI.items():
        txt = txt.replace(a, u)
    return txt


NON_WORD = r"[^[:alnum:]_]*"
SPACE = r"[[:space:]]+"
ARROW_RE = rf"{NON_WORD}→{NON_WORD}"


KNOWN_OPERATORS_BASE = {
    "+",
    "-",
    "*",
    "/",
    "×",
    "÷",
    "::",
    "++",
    "⊕",
    "⊗",
    "⊓",
    "⊔",
    "∧",
    "∨",
    "¬",
    "<",
    ">",
    "≤",
    "≥",
    "≡",
    "≠",
    "even",
    "Parity",
    "succ",
    "length",
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
}

KNOWN_LITERALS = KNOWN_OPERATORS_BASE | KNOWN_TYPE_CONSTRUCTORS

IGNORED_TOKENS = {"∀", "{", "}", "(", ")", ":"}

VAR_LABEL = "var"
OPER_LABEL = "oper"


def classify_token(tok: str) -> str:
    core = tok
    if not core:
        return ""
    if core in IGNORED_TOKENS:
        return ""
    if core == "→":
        return ARROW_RE
    if core.isdigit():
        return rf"{NON_WORD}num{SPACE}{core}{NON_WORD}"
    if core in KNOWN_LITERALS:
        return rf"{NON_WORD}{OPER_LABEL}{SPACE}{re.escape(core)}{NON_WORD}"

    if len(core) == 1 and (core == "_" or core.islower()):
        return rf"{NON_WORD}{VAR_LABEL}{SPACE}[^[:space:]]+{NON_WORD}"

    return rf"{NON_WORD}{VAR_LABEL}{SPACE}{re.escape(core)}{NON_WORD}"


def tokenize_query(q: str) -> list[str]:
    return re.findall(r"[\w\-]+|->|-->|→|[^\s\w]", q)


def user_input_to_patterns(raw: str):
    raw_q = raw or ""
    if not raw_q.strip():
        return r"\z", r"\z"

    tokens_for_raw = tokenize_query(raw_q)
    escaped_tokens_for_raw = [re.escape(t) for t in tokens_for_raw if t]
    raw_signature_regex = f".*{'.*'.join(escaped_tokens_for_raw)}.*"

    normalized_q = normalize_arrows(raw_q).strip()
    tokens_for_annotated = tokenize_query(normalized_q)
    pattern_parts = [classify_token(t) for t in tokens_for_annotated]
    annotated_regex = f".*{''.join(pattern_parts)}.*"

    annotated_regex = re.sub(r"(?:" + NON_WORD + r"){2,}", NON_WORD, annotated_regex)
    annotated_regex = re.sub(r"(\.\*)+", ".*", annotated_regex)

    return annotated_regex, raw_signature_regex


@app.route("/search")
def search():
    raw_q = request.args.get("q", "")

    annotated_regex, raw_signature_regex = user_input_to_patterns(raw_q)
    app.logger.debug(
        "User query '%s' → annotated_regex: '%s' | raw_regex: '%s'",
        raw_q,
        annotated_regex,
        raw_signature_regex,
    )

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT file_path, function_name, signature, annotated_signature
        FROM   agda_signatures
        WHERE  annotated_signature ~* %s
           OR  signature ~* %s
        ORDER BY length(signature), function_name
        LIMIT  200;
        """,
        (annotated_regex, raw_signature_regex),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(
        [
            {
                "file_path": fp,
                "function_name": fn,
                "signature": sig,
                "annotated_signature": ann,
            }
            for fp, fn, sig, ann in rows
        ]
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
