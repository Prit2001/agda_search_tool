import { useState } from "react";
import { Layout, Space, Button } from "antd";
import { HistoryOutlined } from "@ant-design/icons";
import SearchBar from "../components/SearchBar";
import ModeToggle from "../components/ModeToggle";
import ResultsTable from "../components/ResultsTable";
import HistoryDrawer from "../components/HistoryDrawer";
import { search } from "../api/search";
import { addQueryToHistory } from "../utils/localHistory";
import { DEFAULT_MODE } from "../constants";

const { Header, Content } = Layout;

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState(DEFAULT_MODE);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const runSearch = async (forcedQuery) => {
    const q = (forcedQuery ?? query).trim();
    if (!q) return;
    setLoading(true);
    try {
      const data = await search(q, mode);
      setResults(data);
      addQueryToHistory(q);
    } catch (e) {
      console.error(e);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ background: "#fff" }}>
        <h1 style={{ textAlign: "center" }}>Agda Function Search</h1>
      </Header>

      <Content style={{ padding: "2rem 3rem" }}>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <SearchBar
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={runSearch}
            loading={loading}
          />

          <Space align="center">
            <ModeToggle mode={mode} setMode={setMode} />
            <Button
              icon={<HistoryOutlined />}
              onClick={() => setDrawerOpen(true)}
            >
              History
            </Button>
          </Space>

          <ResultsTable results={results} loading={loading} />
        </Space>

        <HistoryDrawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          onSelect={(q) => {
            setDrawerOpen(false);
            setQuery(q);
            runSearch(q);
          }}
        />
      </Content>
    </Layout>
  );
}
