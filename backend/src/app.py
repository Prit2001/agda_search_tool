from flask import Flask, request, jsonify
import psycopg2, os, re
from config import DB_PARAMS

app = Flask(__name__)

ASCII_TO_UNI = {"->": "→", "-->": "→"}
IGNORED_TOKENS = {
    "∀",
    "ℕ",
    "ℤ",
    "𝔹",
    "𝕋",
    "λ",
    "{",
    "}",
    "(",
    ")",
    ":",
    "⦃",
    "⦄",
    "⟦",
    "⟧",
}
OPEN_BRACKETS = {"{", "(", "⦃"}
CLOSE_BRACKETS = {"}", ")", "⦄"}
BRACKET_MAP = {
    **{ch: "(" for ch in OPEN_BRACKETS},
    **{ch: ")" for ch in CLOSE_BRACKETS},
}


def normalize_arrows(txt: str) -> str:
    for a, u in ASCII_TO_UNI.items():
        txt = txt.replace(a, u)
    return txt


def normalize_brackets(txt: str) -> str:
    return "".join(BRACKET_MAP.get(ch, ch) for ch in txt)


def _unify_var(user_tok: str, cand_tok: str, subst: dict[str, str]) -> bool:
    if user_tok in subst:
        return subst[user_tok] == cand_tok

    if cand_tok in subst.values():
        return False
    subst[user_tok] = cand_tok
    return True


def split_with_ignored(txt: str) -> list[str]:
    tokens, buf = [], []
    for ch in txt:
        if ch.isspace():
            if buf:
                tokens.append("".join(buf))
                buf.clear()
        elif ch in IGNORED_TOKENS:
            if buf:
                tokens.append("".join(buf))
                buf.clear()
            tokens.append(ch)
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf))
    return tokens


def tokenize_query(q: str) -> list[str]:
    return split_with_ignored(q)


def strip_ignored(txt: str) -> str:
    for tok in IGNORED_TOKENS:
        txt = txt.replace(tok, "")
    return txt


def br_equal(a: str, b: str) -> bool:
    return (
        a == b
        or (a in OPEN_BRACKETS and b in OPEN_BRACKETS)
        or (a in CLOSE_BRACKETS and b in CLOSE_BRACKETS)
    )


def _drop_colon_sections(tok_list: list[str]) -> list[str]:
    out: list[str] = []
    i, n = 0, len(tok_list)

    while i < n:
        t = tok_list[i]

        if t in OPEN_BRACKETS:
            out.append(t)
            depth = 1
            j = i + 1
            colon_at_lvl1 = -1

            while j < n and depth:
                tt = tok_list[j]
                if tt in OPEN_BRACKETS:
                    depth += 1
                elif tt in CLOSE_BRACKETS:
                    depth -= 1

                if depth == 1 and tt == ":" and colon_at_lvl1 == -1:
                    colon_at_lvl1 = j
                j += 1

            close_idx = j - 1

            if colon_at_lvl1 == -1:
                out.extend(tok_list[i + 1 : close_idx])
            else:
                out.extend(tok_list[i + 1 : colon_at_lvl1])

            out.append(tok_list[close_idx])
            i = close_idx + 1
            continue

        out.append(t)
        i += 1

    return out


def match_annotated_signature(
    fn_sign: str,
    vars: list[str],
    user_inp: str,
) -> bool:

    sig_tokens = split_with_ignored(normalize_brackets(normalize_arrows(fn_sign)))
    user_tokens = split_with_ignored(normalize_brackets(normalize_arrows(user_inp)))

    if ":" not in user_tokens:
        sig_tokens = _drop_colon_sections(sig_tokens)

    m, n = len(user_tokens), len(sig_tokens)
    if m > n:
        return False

    for start in range(n - m + 1):
        subst: dict[str, str] = {}
        ok = True

        for utok, stok in zip(user_tokens, sig_tokens[start : start + m]):
            if stok in vars:
                if utok in subst:
                    if subst[utok] != stok:
                        ok = False
                        break
                elif stok in subst.values():
                    ok = False
                    break
                subst[utok] = stok
            elif utok in IGNORED_TOKENS:
                if not br_equal(utok, stok):
                    ok = False
                    break
            elif utok != stok:
                ok = False
                break

        if ok:
            return True

    return False


def find_matching_operators(raw: str) -> list[tuple]:
    raw_q = raw or ""
    if not raw_q.strip():
        return []

    norm_q = normalize_brackets(normalize_arrows(raw_q)).strip()

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
            FROM agda_signatures;
            """
        )
        candidates = cur.fetchall()

    results = []

    for fp, fn, sig, ann, vars, ops, nums in candidates:
        if match_annotated_signature(sig, vars, norm_q):
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
    except Exception:
        return jsonify({"error": "internal"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
