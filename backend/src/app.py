from flask import Flask, request, jsonify
import psycopg2, os, re
from config import DB_PARAMS

app = Flask(__name__)

ASCII_TO_UNI = {"->": "→", "-->": "→"}
IGNORED_TOKENS = {"∀", "ℕ", "λ", "{", "}", "(", ")", ":", "⦃", "⦄", "⟦", "⟧"}


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


def match_annotated_signature(
    fn_sign: str, vars: list, operators: list, nums: list, user_inp: str
) -> bool:
    fn_sign = normalize_arrows(fn_sign)
    split_user = user_inp.split()
    split_sig = fn_sign.split()

    if len(split_user) > len(split_sig):
        return False

    if not operators:
        for utok, stok in zip(split_user, split_sig):
            if stok in vars or (stok.isdigit() and stok in nums):
                continue
            if utok != stok:
                return False
        return True

    for op in operators:
        if op not in split_user:
            continue

        if op not in split_sig:
            continue

        u_idx = split_user.index(op)
        s_idx = split_sig.index(op)

        start_idx = s_idx - u_idx
        end_idx = start_idx + len(split_user)
        if start_idx < 0 or end_idx > len(split_sig):
            continue

        for i in range(u_idx):
            cand = split_sig[start_idx + i]
            if cand not in vars and split_user[i] != cand:
                break

        else:
            ok = True
            for i in range(u_idx + 1, len(split_user)):
                cand = split_sig[start_idx + i]
                if cand not in vars and split_user[i] != cand:
                    ok = False
                    break

            if ok:
                return True

    return False


def find_matching_operators(raw: str) -> list[tuple]:
    raw_q = raw or ""
    if not raw_q.strip():
        return []

    norm_q = normalize_arrows(raw_q).strip()
    cleaned = strip_ignored(norm_q).replace("→", "")
    toks = cleaned.split()
    if not toks:
        return []

    ops_query = [t for t in toks if (not t.isdigit()) and t not in IGNORED_TOKENS]
    nums_query = [t for t in toks if t.isdigit()]

    with psycopg2.connect(**DB_PARAMS) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT file_path,
                   function_name,
                   signature,
                   annotated_signature,
                   variables,
                   operators,
                   numbers
            FROM agda_signatures
            WHERE (operators && %s) OR (numbers && %s)
            ORDER BY length(signature), function_name
            LIMIT 400;
            """,
            (ops_query, nums_query),
        )
        candidates = cur.fetchall()

    ops_in_db = set()
    nums_in_db = set()
    for *_, op_arr, num_arr in candidates:
        ops_in_db.update(op for op in op_arr if op not in IGNORED_TOKENS)
        nums_in_db.update(num_arr)

    results = []

    for fp, fn, sig, ann, vars, ops, nums in candidates:
        if match_annotated_signature(sig, vars, ops, nums, norm_q):
            results.append((fp, fn, sig, ann))

    return results


@app.route("/search")
def search():
    q = request.args.get("q", "")
    try:
        rows = find_matching_operators(q)
        return jsonify(
            [
                {
                    "file_path": fp,
                    "function_name": fn,
                    "signature": sig,
                    "annotated_signature": ann,
                }
                for fp, fn, sig, ann, *_ in rows
            ]
        )
    except Exception as exc:
        return jsonify({"error": "internal"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
