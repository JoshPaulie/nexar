"""Ensure snippet and output from README_example.py is accurate and present in the README."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"
EXAMPLE = ROOT / "README_example.py"

OUTPUT_MARKER = "Summoner:"


class ExampleRunError(RuntimeError):
    """Raised when the example fails or produces output that cannot be trusted."""


def get_example_code() -> str:
    """Read in example code, preserving all formatting and line endings."""
    with EXAMPLE.open("r", encoding="utf-8") as f:
        content = f.read()
    # Ensure the content doesn't have trailing newlines that would mess up markdown
    return content.rstrip()


def run_example(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run the example, sourcing riot-key.sh only when no key is already in the environment."""
    example = str(EXAMPLE)
    if env.get("RIOT_API_KEY"):
        command = f"uv run python {example}"
    else:
        command = f"source {ROOT / 'riot-key.sh'} && uv run python {example}"
    return subprocess.run(  # noqa: S603
        ["/bin/bash", "-c", command],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
        check=False,
    )


def get_example_output() -> str:
    """
    Run the example and return its output.

    A failed run, an empty run, or output without the expected ``Summoner:`` line raises
    :class:`ExampleRunError` so the README is never blanked by a broken example.
    """
    result = run_example(os.environ.copy())

    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        msg = f"README_example.py exited with status {result.returncode}; README was not modified.\n{details}"
        raise ExampleRunError(msg)

    output = result.stdout.strip()
    if not output:
        msg = "README_example.py produced no output; README was not modified."
        raise ExampleRunError(msg)

    if OUTPUT_MARKER not in output:
        msg = f"README_example.py output has no {OUTPUT_MARKER!r} line; README was not modified.\n{output}"
        raise ExampleRunError(msg)

    # Drop any chatter printed before the report (e.g. progress lines from the example)
    return output[output.index(OUTPUT_MARKER) :]


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


def main() -> int:
    """Regenerate the README example blocks, exiting non-zero when the example fails."""
    try:
        code = get_example_code()
        output = get_example_output()
        update_readme(code, output)
    except (ExampleRunError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print("README.md updated with latest example and output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
