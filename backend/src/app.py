from flask import Flask, request, jsonify
import psycopg2
import os
import re

from config import DB_PARAMS

app = Flask(__name__)


ASCII_TO_UNI = {"->": "→", "-->": "→"}
IGNORED_TOKENS = {"∀", "{", "}", "(", ")", ":", "⦃", "⦄"}


def normalize_arrows(txt: str) -> str:
    for a, u in ASCII_TO_UNI.items():
        txt = txt.replace(a, u)
    return txt


def tokenize_query(q: str) -> list[str]:
    return re.findall(r"[\w\-]+|->|-->|→|[^\s\w]", q)


def strip_ignored(txt: str) -> str:
    for tok in IGNORED_TOKENS:
        txt = txt.replace(tok, "")
    return txt


def find_matching_operators(raw: str) -> list[tuple]:
    raw_q = raw or ""
    if not raw_q.strip():

        return []

    normalized_q = normalize_arrows(raw_q).strip()
    print(normalized_q)

    cleaned = strip_ignored(normalized_q)

    no_arrows = cleaned.replace("→", "")

    ops = no_arrows.split()
    if not ops:
        return []

    conn = psycopg2.connect(**DB_PARAMS)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT file_path, function_name, signature, annotated_signature
              FROM agda_signatures
             WHERE operators && %s
             ORDER BY length(signature), function_name
             LIMIT 200;
            """,
            (ops,),
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@app.route("/search")
def search():
    raw_q = request.args.get("q", "")
    rows = find_matching_operators(raw_q)
    print(len(rows), "len rows")

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
