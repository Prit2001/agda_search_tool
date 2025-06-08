from flask import Flask, request, jsonify
import psycopg2
import os
import re

from config import DB_PARAMS


app = Flask(__name__)

KNOWN_OPERATORS = {
    "≤",
    "≥",
    "<",
    ">",
    "≡",
    "≠",
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
    "even",
    "Parity",
}


def classify_token(tok: str) -> str:
    if tok.isdigit():
        return r"num\s+\d+"
    if tok in KNOWN_OPERATORS:
        return r"oper\s+" + re.escape(tok)

    return r"var\s+\w+"


def user_input_to_regex(raw: str) -> str:
    segments = [seg.strip() for seg in re.split(r"\s*→\s*", raw) if seg.strip()]
    segment_patterns: list[str] = []

    for seg in segments:
        tokens = re.split(r"\s+", seg)
        token_patterns: list[str] = []
        for tok in tokens:
            token_patterns.append(classify_token(tok))

        segment_patterns.append(r"\s+".join(token_patterns))

    full_pattern = r"\s*→\s*".join(segment_patterns)
    return f".*{full_pattern}.*"


@app.route("/search")
def search():
    raw_q = request.args.get("q", "").strip()
    if not raw_q:
        return jsonify([])

    pattern = user_input_to_regex(raw_q)
    print(pattern, "pattern")

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    sql = """
        SELECT
          file_path,
          function_name,
          signature,
          annotated_signature
        FROM agda_signatures
        WHERE annotated_signature ~* %s
        LIMIT 200;
    """
    cur.execute(sql, (pattern,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = [
        {
            "file_path": r[0],
            "function_name": r[1],
            "signature": r[2],
            "annotated_signature": r[3],
        }
        for r in rows
    ]
    return jsonify(results)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
