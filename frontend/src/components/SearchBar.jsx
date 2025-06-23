import { Input, Button } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { useState, useRef } from "react";
import "../App.css";

const SYMBOL_MAP = {
  "\\->": "→",
  "\\=>": "⇒",
  "\\forall": "∀",
  "\\==": "≡",
  "\\leq": "≤",
  "\\geq": "≥",
  "\\times": "×",
  "\\lambda": "λ",
  "\\bot": "⊥",
  "\\top": "⊤",
  "\\neg": "¬",
  "\\in": "∈",
  "\\and": "∧",
  "\\or": "∨",
  "\\union": "∪",
  "\\approx": "≈",
  "\\identical": "≣",
  "\\subset": "⊂",
  "\\supset": "⊃",
  "\\subseteq": "⊆",
  "\\uplus": "⊎",
  "\\turnstile": "⊢",
  "\\Gamma": "Γ",
  "\\N": "ℕ",
  "\\bullet": "●",
  "\\prime": "′",
  "\\sub0": "₀",
  "\\sub1": "₁",
  "\\sub2": "₂",
  "\\sub3": "₃",
  "\\phi": "ϕ",
  "\\psi": "ψ",
  "\\sigma": "σ",
  "\\iota": "ι",
  "\\epsilon": "ε",
  "\\dot": "·",
  "\\triangleright": "▷",
  "\\triangleleft": "◁",
  "\\langle": "⟨",
  "\\rangle": "⟩",
  "\\llbracket": "⟦",
  "\\rrbracket": "⟧",
  "\\lcustom": "⟅",
  "\\rcustom": "⟆",
  "\\downarrow": "↓",
  "\\join": "⧺",
  "\\relcomp": "⨾",
  "\\leqq": "⩽",
  "\\dbl1": "𝟙",
  "\\dbl2": "𝟚"
};


const SYMBOL_LIST = Object.values(SYMBOL_MAP);

export default function SearchBar({ value, onChange, onSearch, loading }) {
  const inputRef = useRef(null);
  const [showSymbols, setShowSymbols] = useState(false);

  const handleChange = (e) => {
    const newVal = e.target.value;

    setShowSymbols(newVal.endsWith("\\"));

    const replaced = newVal.replace(/\\[a-z=>-]+/g, (match) => SYMBOL_MAP[match] || match);

    onChange({ target: { value: replaced } });
  };

  const insertSymbol = (symbol) => {
  const el = inputRef.current?.input;
  if (!el) return;

  const start = el.selectionStart;
  const end = el.selectionEnd;

  const before = value.slice(0, start);
  const after = value.slice(end);
  const lastBackslashIndex = before.lastIndexOf("\\");

  const newVal =
    lastBackslashIndex !== -1
      ? before.slice(0, lastBackslashIndex) + symbol + after
      : before + symbol + after;

  onChange({ target: { value: newVal } });
  setShowSymbols(false);

  const newPos =
    lastBackslashIndex !== -1
      ? lastBackslashIndex + symbol.length
      : start + symbol.length;

  setTimeout(() => {
    el.focus();
    el.setSelectionRange(newPos, newPos);
  }, 0);
};


  return (
    <div className="search-wrapper">
      <Input.Search
        ref={inputRef}
        placeholder="Type signature fragment…"
        value={value}
        onChange={handleChange}
        onSearch={(val) => {
          onSearch(val);
          setShowSymbols(false);
        }}
        loading={loading}
        enterButton={<Button icon={<SearchOutlined />}>Search</Button>}
        size="large"
        allowClear
      />

      {showSymbols && (
        <div className="symbol-panel">
          {SYMBOL_LIST.map((sym, i) => (
            <button
              key={i}
              className="symbol-btn"
              onClick={() => insertSymbol(sym)}
            >
              {sym}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
