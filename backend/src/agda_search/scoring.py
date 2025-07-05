from .util import split_with_ignored, normalize_arrows, normalize_brackets
from .constants import IGNORED_TOKENS


def _tokenise(s: str):
    return split_with_ignored(normalize_brackets(normalize_arrows(s)))


def heuristic_score(user_sig: str, cand_sig: str) -> float:
    u = _tokenise(user_sig)
    c = _tokenise(cand_sig)

    same_pos = sum(1 for x, y in zip(u, c) if x == y)
    same_pos_norm = same_pos / len(u)
    op_overlap = len(set(u) & set(c) - IGNORED_TOKENS)
    len_penalty = -0.6 * abs(len(c) - len(u))

    return 2 * same_pos_norm + op_overlap + len_penalty
