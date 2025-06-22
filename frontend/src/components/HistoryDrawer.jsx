import { Drawer, List } from "antd";
import { getHistory } from "../utils/localHistory";

export default function HistoryDrawer({ open, onClose, onSelect }) {
  const history = getHistory();

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
