from flask import Flask, request, jsonify
import psycopg2
import os

from config import DB_PARAMS


app = Flask(__name__)


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    like_pattern = f"%{q}%"

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    sql = """
        SELECT
          file_path,
          function_name,
          signature,
          annotated_signature
        FROM agda_signatures
        WHERE function_name ILIKE %s
        LIMIT 100;
    """
    cur.execute(sql, (like_pattern,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = [
        {
            "file_path": r[0],
            "function_name": r[1],
            "signature": r[2],
            "signature_parts": r[3],
        }
        for r in rows
    ]
    return jsonify(results)


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
