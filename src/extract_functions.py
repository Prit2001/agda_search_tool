import re
import os


def extract_functions_from_agda(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = []
    blocks += re.findall(r"(?ms)\\begin\{code\}(.*?)\\end\{code\}", content)
    blocks += re.findall(r"(?ms)```agda\s*(.*?)```", content)

    decl_re = re.compile(r"^\s*([\w-]+)\s*:\s*(.+?)\s*$", re.MULTILINE)
    functions = []

    for block in blocks:
        block = re.sub(r"(?ms)\{\-.*?\-\}", "", block)

        cleaned_lines = []
        for line in block.splitlines():
            line = re.sub(r"--.*", "", line)
            if not line.strip():
                continue
            cleaned_lines.append(line)

        cleaned_block = "\n".join(cleaned_lines)

        for match in decl_re.finditer(cleaned_block):
            name = match.group(1)
            sig = match.group(2).strip()
            parts = re.split(r"\s*→\s*|\s*->\s*", sig)
            input_types = parts[:-1]
            output_type = parts[-1]
            functions.append(
                {"name": name, "input_types": input_types, "output_type": output_type}
            )

    return functions


def extract_from_project(directory):
    all_functions = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".lagda"):
                file_path = os.path.join(root, file)
                funcs = extract_functions_from_agda(file_path)
                all_functions.extend(funcs)
    return all_functions
