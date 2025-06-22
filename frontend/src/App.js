import React, { useState } from "react";
import { Radio, Button, Input } from "antd";
import { SearchOutlined, LoadingOutlined } from "@ant-design/icons";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("strict");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = () => {
    const trimmed = query.trim();
    if (!trimmed) return;

    setHasSearched(true);
    setLoading(true);

    fetch(
      `/search?q=${encodeURIComponent(trimmed)}&mode=${encodeURIComponent(
        mode
      )}`
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setResults)
      .catch((err) => {
        console.error("Search error:", err);
        setResults([]);
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="app-container">
      <h1>Agda Function Search</h1>

      <div className="search-box">
        <Input
          placeholder="Type to search..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onPressEnter={handleSearch}
          size="large"
        />

        <Button
          type="primary"
          icon={loading ? <LoadingOutlined /> : <SearchOutlined />}
          onClick={handleSearch}
          disabled={loading}
          size="large"
          style={{ marginLeft: "0.75rem" }}
        >
          Search
        </Button>
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <Radio.Group
          onChange={(e) => setMode(e.target.value)}
          value={mode}
          optionType="button"
          buttonStyle="solid"
        >
          <Radio value="strict">Strict</Radio>
          <Radio value="loose">Loose</Radio>
        </Radio.Group>
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
