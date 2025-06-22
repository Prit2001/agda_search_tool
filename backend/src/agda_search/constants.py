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
