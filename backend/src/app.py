from __future__ import annotations

import logging
import os
from flask import Flask, request, jsonify
import psycopg2
from config import DB_PARAMS, CREATE_HISTORY_TABLE_SQL

from agda_search.strategies import get_strategy

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
    cur.execute(CREATE_HISTORY_TABLE_SQL)
conn.commit()


@app.route("/search")
def search() -> tuple:
    query: str = request.args.get("q", "") or ""
    mode: str = request.args.get("mode", "strict")

    try:
        strategy = get_strategy(mode)
    except Exception:
        logging.warning("unknown mode '%s' - defaulting to strict search", mode)
        strategy = get_strategy("strict")

    try:
        with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO search_history (query) VALUES (%s) "
                "ON CONFLICT (query) DO UPDATE SET ts = now();",
                (query,),
            )
        conn.commit()
        rows = strategy.find(query)
    except Exception:
        logging.exception("error while running search")
        return jsonify({"error": "internal"}), 500

    return jsonify(
        [
            {
                "file_path": fp,
                "function_name": fn,
                "signature": sig,
                "annotated_signature": ann,
                "relevance": score,
            }
            for fp, fn, sig, ann, score in rows
        ]
    )


@app.route("/history")
def history():
    limit = int(request.args.get("limit", 30))
    with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT query FROM search_history ORDER BY ts DESC LIMIT %s;",
            (limit,),
        )
        return jsonify([row[0] for row in cur.fetchall()])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
