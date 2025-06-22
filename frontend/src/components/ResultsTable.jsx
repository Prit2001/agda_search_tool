import { Table, Typography } from "antd";

const { Text } = Typography;

export default function ResultsTable({ results, loading }) {
  const columns = [
    { title: "File Path", dataIndex: "file_path", key: "fp" },
    { title: "Function Name", dataIndex: "function_name", key: "fn" },
    {
      title: "Function Signature",
      dataIndex: "signature",
      key: "sig",
      render: (text) => <Text style={{ fontFamily: "monospace" }}>{text}</Text>,
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={results}
      rowKey={(row) => `${row.file_path}-${row.function_name}-${row.signature}`}
      loading={loading}
      pagination={{ pageSize: 20 }}
      size="middle"
      bordered
    />
  );
}
