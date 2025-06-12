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
    tokens = tokenize_query(normalized_q)

    var_map = {}
    pattern_parts = []

    for token in tokens:
        if token in IGNORED_TOKENS:
            continue
        elif token == "→":
            pattern_parts.append(ARROW_RE)
        elif token.isdigit():
            pattern_parts.append(rf"{NON_WORD}num{SPACE}{token}{NON_WORD}")
        elif token in KNOWN_LITERALS:
            pattern_parts.append(
                rf"{NON_WORD}{OPER_LABEL}{SPACE}{re.escape(token)}{NON_WORD}"
            )
        else:
            if token not in var_map:

                new_group_index = len(var_map) + 1
                var_map[token] = new_group_index
                pattern_parts.append(
                    rf"{NON_WORD}{VAR_LABEL}{SPACE}([^[:space:]]+){NON_WORD}"
                )
            else:

                group_index = var_map[token]
                pattern_parts.append(
                    rf"{NON_WORD}{VAR_LABEL}{SPACE}\{group_index}{NON_WORD}"
                )

    annotated_regex = f".*{''.join(pattern_parts)}.*"

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
