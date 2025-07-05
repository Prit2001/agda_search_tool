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


DIGIT_FORMS = {
    "0": {"0", "zero",  "𝟎", "𝟘"},
    "1": {"1", "one",   "𝟏", "𝟙"},
    "2": {"2", "two",   "𝟐", "𝟚"},
    "3": {"3", "three", "𝟑", "𝟛"},
    "4": {"4", "four",  "𝟒", "𝟜"},
    "5": {"5", "five",  "𝟓", "𝟝"},
    "6": {"6", "six",   "𝟔", "𝟞"},
    "7": {"7", "seven", "𝟕", "𝟟"},
    "8": {"8", "eight", "𝟖", "𝟠"},
    "9": {"9", "nine",  "𝟗", "𝟡"},
}


ALIAS_TO_DIGIT = { alias: canon for canon, aliases in DIGIT_FORMS.items() for alias in aliases}


SUCC_TOKENS = r"(?:suc|succ)"
DIGIT_PAT = r"\d+"
