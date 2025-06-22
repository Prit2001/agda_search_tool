import { Radio } from "antd";
import { DEFAULT_MODE } from "../constants";

export default function ModeToggle({ mode, setMode }) {
  return (
    <Radio.Group
      value={mode}
      onChange={(e) => setMode(e.target.value)}
      optionType="button"
      buttonStyle="solid"
      defaultValue={DEFAULT_MODE}
    >
      <Radio value="strict">Strict</Radio>
      <Radio value="loose">Loose</Radio>
    </Radio.Group>
  );
}
