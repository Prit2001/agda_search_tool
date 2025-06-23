import { Input, Button } from "antd";
import { SearchOutlined } from "@ant-design/icons";

export default function SearchBar({ value, onChange, onSearch, loading }) {
  return (
    <Input.Search
      placeholder="Type signature fragment…"
      value={value}
      onChange={onChange}
      onSearch={onSearch}
      loading={loading}
      enterButton={<Button icon={<SearchOutlined />}>Search</Button>}
      size="large"
      allowClear
    />
  );
}
