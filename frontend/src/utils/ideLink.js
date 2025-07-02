export const makeVsCodeLink = (absPath, line) => {
  return `vscode://file/${encodeURIComponent(absPath)}:${line}:1`;
};
