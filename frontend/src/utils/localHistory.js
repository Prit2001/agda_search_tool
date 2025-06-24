import { HISTORY_KEY } from "../constants";

export function addQueryToHistory(q) {
  if (!q) return;
  const hist = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  // if (hist.includes(q)) return;
  hist.unshift(q);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(hist.slice(0, 50)));
}

export function getHistory() {
  return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
}
