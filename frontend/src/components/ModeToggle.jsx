import { Radio } from "antd";

export default function ModeToggle({ mode, setMode, query, runSearch }) {
  const handleModeChange = (e) => {
    const newMode = e.target.value;
    setMode(newMode);
    if (query?.trim()) {
      runSearch(query.trim(), newMode);
    }
  };

  return (
    <Radio.Group
      value={mode}
      onChange={handleModeChange}
      optionType="button"
      buttonStyle="solid"
    >
      <Radio value="strict">Strict</Radio>
      <Radio value="loose">Loose</Radio>
    </Radio.Group>
  );
}
