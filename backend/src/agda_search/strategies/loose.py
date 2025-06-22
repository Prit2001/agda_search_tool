from ..db import get_cursor
from ..util import (
    split_with_ignored,
    normalize_arrows,
    normalize_brackets,
    _drop_colon_sections,
    br_equal,
    IGNORED_TOKENS,
)
from .base import SearchStrategy


class LooseSearch(SearchStrategy):
    def find(self, user_query: str):
        norm_q = normalize_brackets(normalize_arrows(user_query)).strip()

        with get_cursor() as cur:
            cur.execute(
                """
                    SELECT file_path,function_name,signature,annotated_signature,
                        variables
                    FROM agda_signatures
                """
            )
            rows = cur.fetchall()

        res = []
        for fp, fn, sig, ann, vars_ in rows:
            if self._matches(sig, vars_, norm_q):
                res.append((fp, fn, sig, ann))
        return res

    def _matches(self, fn_sign: str, vars_, user_inp: str) -> bool:
        sig_toks = split_with_ignored(normalize_brackets(normalize_arrows(fn_sign)))
        user_toks = split_with_ignored(normalize_brackets(normalize_arrows(user_inp)))

        if ":" not in user_toks:
            sig_toks = _drop_colon_sections(sig_toks)

        m, n = len(user_toks), len(sig_toks)
        if m > n:
            return False

        for start in range(n - m + 1):
            subst, ok = {}, True
            for ut, st in zip(user_toks, sig_toks[start : start + m]):
                if st in vars_:
                    if (
                        ut in subst
                        and subst[ut] != st
                        or st in subst.values()
                        and subst.get(ut) != st
                    ):
                        ok = False
                        break
                    subst[ut] = st
                elif ut in IGNORED_TOKENS and not br_equal(ut, st):
                    ok = False
                    break
                elif ut not in IGNORED_TOKENS and ut != st:
                    ok = False
                    break
            if ok:
                return True
        return False
