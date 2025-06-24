import { API_SEARCH } from "../constants";

export async function search(query, mode) {
  const url = `${API_SEARCH}?q=${encodeURIComponent(
    query
  )}&mode=${encodeURIComponent(mode)}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
