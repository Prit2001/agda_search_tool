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


ZERO_FORMS = {"0", "zero", "𝟎"}


SUCC_TOKENS   = r"(?:suc|succ)"
DIGIT_PAT     = r"\d+"
