"""Ensure snippet and output from examples/basic/README_example is accurate and present in the README."""

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"
EXAMPLE = ROOT / "examples/basic/README_example.py"

CODE_BLOCK_PATTERN = re.compile(r"(## Usage example\n)(.*?)(##|$)", re.DOTALL)
OUTPUT_BLOCK_PATTERN = re.compile(r"(### Sample Output\n)(.*?)(##|$)", re.DOTALL)


def get_example_code() -> str:
    """Read in example code."""
    with EXAMPLE.open("r", encoding="utf-8") as f:
        return f.read().strip()


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
    )
    output = result.stdout.strip()
    # Remove any key set messages or blank lines at the top
    return re.sub(r"^.*?\n(?=Summoner:)", "", output, flags=re.DOTALL)


def update_readme(code: str, output: str) -> None:
    with README.open("r", encoding="utf-8") as f:
        content = f.read()

    # Replace code block
    new_code_block = (
        "## Usage example\n\n"
        "Below is a real, working example from `examples/basic/README_example.py`:\n\n"
        f"```python\n{code}\n```\n\n"
        "### Sample Output\n\n"
        f"```\n{output}\n```\n\n"
    )
    # Replace from ## Usage example to next ##
    content = CODE_BLOCK_PATTERN.sub(new_code_block + r"\3", content, count=1)

    with README.open("w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    code = get_example_code()
    output = get_example_output()
    update_readme(code, output)
    print("README.md updated with latest example and output.")
