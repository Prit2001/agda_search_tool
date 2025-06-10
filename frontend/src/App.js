import React, { useState } from "react";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = () => {
    const trimmed = query.trim();
    if (!trimmed) {
      return;
    }

    setHasSearched(true);
    setLoading(true);

    fetch(`/search?q=${encodeURIComponent(trimmed)}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setResults(data);
      })
      .catch((err) => {
        console.error("Search error:", err);
        setResults([]);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div className="app-container">
      <h1>Agda Function Search</h1>

      <div className="search-box">
        <input
          type="text"
          placeholder="Type to search..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSearch();
            }
          }}
        />
        <button onClick={handleSearch} disabled={loading}>
          Search
        </button>
      </div>

      <div className="results-container">
        {loading ? (
          <div className="skeleton-table">
            <div className="skeleton-row header-row">
              <div className="skeleton-cell skeleton-header"></div>
              <div className="skeleton-cell skeleton-header"></div>
              <div className="skeleton-cell skeleton-header"></div>
            </div>
            {[...Array(5)].map((_, idx) => (
              <div className="skeleton-row" key={idx}>
                <div className="skeleton-cell"></div>
                <div className="skeleton-cell"></div>
                <div className="skeleton-cell"></div>
                <div className="skeleton-cell"></div>
              </div>
            ))}
          </div>
        ) : hasSearched && results.length === 0 ? (
          <p className="no-results">No results found.</p>
        ) : results.length > 0 ? (
          <table className="results-table">
            <thead>
              <tr>
                <th>File Path</th>
                <th>Function Name</th>
                <th>Function Signature</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row, idx) => (
                <tr key={idx}>
                  <td>{row.file_path}</td>
                  <td>{row.function_name}</td>
                  <td>{row.signature}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </div>
    </div>
  );
}

export default App;
