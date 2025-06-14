from flask import Flask, request, jsonify
import psycopg2
import os
import re

from config import DB_PARAMS

app = Flask(__name__)


ASCII_TO_UNI = {"->": "→", "-->": "→"}
IGNORED_TOKENS = {"∀", "ℕ", "λ" "{", "}", "(", ")", ":", "⦃", "⦄", "⟦", "⟧"}


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
    split_user_inp = user_inp.split()
    split_fn_sign = fn_sign.split()
    matching = False

    if len(split_user_inp) > len(split_fn_sign):
        return False

    for op in operators:
        if op in split_user_inp:
            user_inp_ind_op = split_user_inp.index(op)
            cand_ind_op = split_fn_sign.index(op)
            for i in range(user_inp_ind_op):
                if (
                    split_fn_sign[cand_ind_op - user_inp_ind_op + i] not in vars
                    and split_user_inp[i]
                    != split_fn_sign[cand_ind_op - user_inp_ind_op + i]
                ):
                    matching = False
                else:
                    matching = True
            for i in range(user_inp_ind_op + 1, len(split_user_inp)):
                cand_ind_op += 1
                if (
                    split_fn_sign[cand_ind_op] not in vars
                    and split_user_inp[i] != split_fn_sign[cand_ind_op]
                ):
                    matching = False
                else:
                    matching = True

    return matching


def find_matching_operators(raw: str) -> list[tuple]:
    raw_q = raw or ""
    if not raw_q.strip():
        return []

    normalized_q = normalize_arrows(raw_q).strip()
    cleaned = strip_ignored(normalized_q)
    no_arrows = cleaned.replace("→", "")

    toks = no_arrows.split()
    if not toks:
        return []

    ops_query = [t for t in toks if not t.isdigit()]
    nums_query = [t for t in toks if t.isdigit()]

    conn = psycopg2.connect(**DB_PARAMS)
    try:
        cur = conn.cursor()
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
             WHERE (operators && %s)
                OR (numbers   && %s)
             ORDER BY length(signature), function_name
             LIMIT 200;
            """,
            (ops_query, nums_query),
        )
        candidates = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    ops_in_db = set()
    nums_in_db = set()
    for *_, op_arr, num_arr in candidates:
        ops_in_db.update(op_arr)
        nums_in_db.update(num_arr)

    results = []
    for fp, fn, sign, ann, vars, ops, nums, *_ in candidates:
        if match_annotated_signature(sign, vars, ops, nums, normalized_q):
            results.append((fp, fn, sign, ann))

    return candidates


@app.route("/search")
def search():
    raw_q = request.args.get("q", "")
    try:
        rows = find_matching_operators(raw_q)

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
    except:
        print("An exception occurred")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
