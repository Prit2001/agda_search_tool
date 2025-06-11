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

KNOWN_OPERATORS = {
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
}
VAR_LABEL = "var"
OPER_LABEL = "oper"


def classify_token(tok: str) -> str:
    """
    - Single‐letter a–z or '_' → wildcard variable (match ANY var <name>)
    - Digit sequences → exact num <value>
    - Known operator symbols → exact oper <symbol>
    - Everything else (multi‐char identifiers) → exact var <thatName>
    """
    core = tok.strip("(){}[],:")
    if not core:
        return ""

    if core == "→":
        return ARROW_RE

    if core.isdigit():

        return rf"{NON_WORD}num{SPACE}{core}{NON_WORD}"

    if core in KNOWN_OPERATORS:

        return rf"{NON_WORD}{OPER_LABEL}{SPACE}{re.escape(core)}{NON_WORD}"

    if len(core) == 1 and (core == "_" or core.islower()):
        return rf"{NON_WORD}{VAR_LABEL}{SPACE}[[:alnum:]_]+{NON_WORD}"

    return rf"{NON_WORD}{VAR_LABEL}{SPACE}{re.escape(core)}{NON_WORD}"


def user_input_to_regex(raw: str) -> str:
    txt = normalize_arrows(raw or "").strip()
    if not txt:
        return ".*"

    segments = [seg for seg in re.split(r"\s*→\s*", txt) if seg]
    seg_pats = []
    for seg in segments:
        toks = [t for t in re.split(r"\s+", seg) if t]
        seg_pats.append("".join(classify_token(t) for t in toks))

    body = ARROW_RE.join(seg_pats)
    return rf".*{body}.*"


@app.route("/search")
def search():
    raw_q = request.args.get("q", "")
    pattern = user_input_to_regex(raw_q)
    print(pattern)
    app.logger.debug("regex → %s", pattern)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT file_path, function_name, signature, annotated_signature
        FROM   agda_signatures
        WHERE  annotated_signature ~* %s
        LIMIT  200;
        """,
        (pattern,),
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
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
