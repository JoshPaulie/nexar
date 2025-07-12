"""Ensure snippet and output from examples/basic/README_example is accurate and present in the README."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"
EXAMPLE = ROOT / "README_example.py"


def get_example_code() -> str:
    """Read in example code, preserving all formatting and line endings."""
    with EXAMPLE.open("r", encoding="utf-8") as f:
        content = f.read()
    # Ensure the content doesn't have trailing newlines that would mess up markdown
    return content.rstrip()


def get_example_output() -> str:
    """Run example code snippet, capture output."""
    env = os.environ.copy()
    env_script = str(ROOT / "riot-key.sh")
    # Source riot-key.sh and run the example
    command = f"source {env_script} && uv run python {EXAMPLE}"
    result = subprocess.run(
        ["/bin/bash", "-c", command],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
        check=False,
    )
    output = result.stdout.strip()
    # Remove any key set messages or blank lines at the top
    import re

    return re.sub(r"^.*?\n(?=Summoner:)", "", output, flags=re.DOTALL)


def update_readme(code: str, output: str) -> None:
    """Update the README with new code and output, replacing only the Usage example section."""
    # Read README and split into lines
    with README.open("r", encoding="utf-8") as f:
        readme_lines = f.readlines()

    # Split code and output into lines
    code_lines = code.split("\n")
    output_lines = output.split("\n")

    # Find the indices for code block replacement
    code_start_idx = None
    code_end_idx = None
    output_start_idx = None
    output_end_idx = None

    for i, line in enumerate(readme_lines):
        if "<!-- example-block-start -->" in line:
            code_start_idx = i
        elif "<!-- example-block-end -->" in line:
            code_end_idx = i
        elif "<!-- example-output-block-start -->" in line:
            output_start_idx = i
        elif "<!-- example-output-block-end -->" in line:
            output_end_idx = i

    if None in [code_start_idx, code_end_idx, output_start_idx, output_end_idx]:
        msg = "Could not find all required comment markers in README"
        raise ValueError(msg)

    # Build new README content
    new_readme_lines = []

    # Add everything up to code block
    new_readme_lines.extend(readme_lines[: code_start_idx + 1])

    # Add code block
    new_readme_lines.append("```python\n")
    new_readme_lines.extend([line + "\n" for line in code_lines])
    new_readme_lines.append("```\n")

    # Add everything between code block end and output block start
    new_readme_lines.extend(readme_lines[code_end_idx : output_start_idx + 1])

    # Add output block
    new_readme_lines.append("```\n")
    new_readme_lines.extend([line + "\n" for line in output_lines])
    new_readme_lines.append("```\n")

    # Add everything after output block
    new_readme_lines.extend(readme_lines[output_end_idx:])

    # Write the updated README
    with README.open("w", encoding="utf-8") as f:
        f.writelines(new_readme_lines)


if __name__ == "__main__":
    code = get_example_code()
    output = get_example_output()

    update_readme(code, output)
    print("README.md updated with latest example and output.")
