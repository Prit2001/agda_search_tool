from typing import List

from ..db import get_cursor
from ..util import (
    normalize_arrows,
    normalize_brackets,
    strip_ignored,
    split_with_ignored,
    match_annotated_signature,
)
from ..constants import IGNORED_TOKENS
from ..scoring import heuristic_score
from .base import SearchStrategy


class StrictSearch(SearchStrategy):

    def _candidates(self, ops_query: List[str], nums_query: List[str]):
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT file_path,
                       function_name,
                       signature,
                       annotated_signature,
                       variables,
                       operators,
                       numbers,
                       line_no
                FROM   agda_signatures
                WHERE  (operators && %s) OR (numbers && %s)
                ORDER  BY length(signature), function_name
                """,
                (ops_query, nums_query),
            )
            return cur.fetchall()

    def find(self, user_query: str):

        cleaned = strip_ignored(
            normalize_brackets(normalize_arrows(user_query))
        ).replace("→", "")

        toks = split_with_ignored(cleaned)
        ops_query = [t for t in toks if (not t.isdigit()) and t not in IGNORED_TOKENS]
        nums_query = [t for t in toks if t.isdigit()]

        candidates = self._candidates(ops_query, nums_query)
        norm_q = normalize_brackets(normalize_arrows(user_query)).strip()

        results = []
        for fp, fn, sig, ann, vars_, ops, nums, line_no in candidates:
            if match_annotated_signature(sig, vars_, ops, nums, norm_q):
                score = heuristic_score(user_query, sig)
                results.append((fp, fn, sig, ann, score, line_no))

        results.sort(key=lambda r: r[-2], reverse=True)
        return results
