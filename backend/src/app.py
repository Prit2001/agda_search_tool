from flask import Flask, request, jsonify
import psycopg2
import os
import re

from config import DB_PARAMS

app = Flask(__name__)


ASCII_TO_UNI_ARROW = {"->": "→", "-->": "→"}


def normalise_arrows(txt: str) -> str:
    for ascii_arrow, uni_arrow in ASCII_TO_UNI_ARROW.items():
        txt = txt.replace(ascii_arrow, uni_arrow)
    return txt


NON_WORD = r"[^\w]*"
ARROW_RE = r"[^\w]*→[^\w]*"

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


VO_GROUP = r"(var|oper)"


def classify_token(tok: str) -> str:
    core = tok.strip("(){}[],:")
    if not core:
        return ""

    if core == "→":
        return ARROW_RE

    if core.isdigit():
        return rf"{NON_WORD}num\s+{core}{NON_WORD}"

    if core in KNOWN_OPERATORS:
        return rf"{NON_WORD}oper\s+{re.escape(core)}{NON_WORD}"

    return rf"{NON_WORD}{VO_GROUP}\s+{re.escape(core)}{NON_WORD}"


def user_input_to_regex(raw: str) -> str:
    raw = normalise_arrows(raw).strip()
    if not raw:
        return ".*"

    segments = [seg for seg in re.split(r"\s*→\s*", raw) if seg]
    seg_pats = []

    for seg in segments:
        tokens = [t for t in re.split(r"\s+", seg) if t]
        seg_pats.append("".join(classify_token(t) for t in tokens))

    body = ARROW_RE.join(seg_pats)
    return rf".*{body}.*"


@app.route("/search")
def search():
    raw_q = request.args.get("q", "")
    pattern = user_input_to_regex(raw_q)

    app.logger.debug("regex = %s", pattern)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT file_path,
               function_name,
               signature,
               annotated_signature
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
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
