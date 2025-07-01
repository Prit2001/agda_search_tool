import { Table, Typography } from "antd";
import { useState } from "react";
import { makeVsCodeLink } from "../utils/ideLink";

const { Text } = Typography;

export default function ResultsTable({ results, loading }) {
  const columns = [
    {
      title: "File Path",
      dataIndex: "file_path",
      key: "fp",
      render: (_, row) => (
        <a
          href={makeVsCodeLink(row.abs_path ?? row.file_path, row.line_no ?? 1)}
          title="Open in VS Code"
        >
          {row.file_path}
        </a>
      ),
    },
    { title: "Function Name", dataIndex: "function_name", key: "fn" },
    {
      title: "Function Signature",
      dataIndex: "signature",
      key: "sig",
      render: (text) => <Text style={{ fontFamily: "monospace" }}>{text}</Text>,
    },
  ];

  const [pageCfg, setPageCfg] = useState({
    current: 1,
    pageSize: 20,
    showSizeChanger: true,
    pageSizeOptions: ["20", "50", "100"],
  });

  return (
    <Table
      columns={columns}
      dataSource={results}
      rowKey={(row) => `${row.file_path}-${row.function_name}-${row.signature}`}
      loading={loading}
      pagination={{
        ...pageCfg,
        onChange: (page, pageSize) =>
          setPageCfg((p) => ({ ...p, current: page, pageSize })),
      }}
      size="middle"
      bordered
    />
  );
}
