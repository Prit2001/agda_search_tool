import { Drawer, List } from "antd";
import { useEffect, useState } from "react";

export default function HistoryDrawer({ open, onClose, onSelect }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (!open) return;
    fetch("/history?limit=50")
      .then((r) => r.json())
      .then(setHistory)
      .catch(console.error);
  }, [open]);

  return (
    <Drawer
      title="Recent searches"
      placement="right"
      width={350}
      onClose={onClose}
      open={open}
    >
      <List
        dataSource={history}
        renderItem={(item) => (
          <List.Item
            style={{ cursor: "pointer" }}
            onClick={() => onSelect(item)}
          >
            <code>{item}</code>
          </List.Item>
        )}
      />
    </Drawer>
  );
}
