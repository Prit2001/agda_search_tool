from __future__ import annotations

import logging
import os
from flask import Flask, request, jsonify

from agda_search.strategies import get_strategy

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)


@app.route("/search")
def search() -> tuple:
    query: str = request.args.get("q", "") or ""
    mode: str = request.args.get("mode", "strict")

    try:
        strategy = get_strategy(mode)
    except Exception:
        logging.warning("unknown mode '%s' – defaulting to strict search", mode)
        strategy = get_strategy("strict")

    try:
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
            }
            for fp, fn, sig, ann in rows
        ]
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
