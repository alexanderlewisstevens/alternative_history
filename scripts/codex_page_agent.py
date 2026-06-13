#!/usr/bin/env python3
"""Run one extraction agent for one PDF page record."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

from lib.extraction_common import load_config, resolve_source_paths
from validate_records import validate_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENV = (
    "PAGE_PROMPT_FILE",
    "PAGE_RECORD_OUTPUT",
    "PAGE_NUMBER",
    "PAGE_FILE",
    "SOURCE_ID",
)


def require_env() -> dict[str, str]:
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise RuntimeError("missing required environment variable(s): " + ", ".join(missing))
    return {name: os.environ[name] for name in REQUIRED_ENV}


def resolve_page_path(source_id: str, page_file: str, config_path: str) -> Path:
    env_path = os.environ.get("PAGE_PATH")
    if env_path:
        page_path = Path(env_path)
        return page_path if page_path.is_absolute() else PROJECT_ROOT / page_path

    source = load_config(config_path, source_id)
    paths = resolve_source_paths(source)
    page_path = Path(page_file)
    return page_path if page_path.is_absolute() else paths["sliced_pages_dir"] / page_path


def codex_command(codex_bin: str, last_message_path: Path) -> list[str]:
    command = [
        codex_bin,
        "exec",
        "--cd",
        str(PROJECT_ROOT),
        "--sandbox",
        "workspace-write",
        "--ask-for-approval",
        "never",
        "--output-last-message",
        str(last_message_path),
    ]
    model = os.environ.get("CODEX_MODEL")
    if model:
        command.extend(["--model", model])
    command.append("-")
    return command


def build_prompt(
    *,
    base_prompt: str,
    page_path: Path,
    output_file: Path,
    env: dict[str, str],
    attempt: int,
    backend: str,
    page_text: str | None = None,
    validation_errors: list[str] | None = None,
    current_output: str | None = None,
) -> str:
    repair_text = ""
    if validation_errors:
        repair_text = "\n".join(f"- {error}" for error in validation_errors)
        repair_text = f"""

## Repair Required

The previous output failed local validation with these errors:

{repair_text}

Rewrite `{output_file}` with a corrected schema-v2 page record. Do not preserve invalid sections, old field names, Markdown footnote syntax, or long source quotations.
"""
    if current_output:
        repair_text += f"""

## Previous Invalid Output

```markdown
{current_output.strip()}
```
"""

    if backend == "codex":
        output_rule = f"Make exactly one content output: write the page record to `{output_file}`."
        inspection_rule = (
            f"You may use local shell inspection commands such as "
            f"`pdftotext -layout \"{page_path}\" -` and "
            f"`pdftotext -bbox-layout \"{page_path}\" -`."
        )
        final_rule = (
            "Your final response should contain only the Markdown record or a one-line "
            f"confirmation that `{output_file}` was written."
        )
    else:
        output_rule = (
            "Return exactly one Markdown page record. The wrapper will write and validate "
            f"it at `{output_file}`."
        )
        inspection_rule = (
            "Use only the page text snapshot and layout signals included in this prompt; "
            "you cannot inspect local files directly."
        )
        final_rule = "Your final response must contain only the Markdown record."

    page_text_section = ""
    if page_text:
        page_text_section = f"""

## Local Page Text Snapshot

This text was extracted from only the requested sliced PDF page with `pdftotext -layout`.
Use it to identify structure, boundaries, notes, bibliography, and editorial apparatus.
Do not reproduce extended Norton prose in the Markdown output.

```text
{page_text.strip()}
```
"""

    return f"""You are a per-page extraction subagent for the Alternative History project.

Read the task prompt below, inspect only this one sliced PDF page, and write exactly one Markdown page record.

- PDF page path: `{page_path}`
- Output path: `{output_file}`
- Page number: `{env["PAGE_NUMBER"]}`
- Page file: `{env["PAGE_FILE"]}`
- Source ID: `{env["SOURCE_ID"]}`
- Output mode: `{os.environ.get("OUTPUT_MODE", "summary_only")}`
- Access level: `{os.environ.get("ACCESS_LEVEL", "restricted")}`

Operational rules:

- {output_rule}
- Do not edit repo-tracked files or any other generated page record.
- {inspection_rule}
- Follow `docs/templates/extraction/page-record.md` and the local validator contract.
- Preserve required sections in this exact order: Page Overview, Layout And Reading Order, Excerpt, Source Notes, Bibliography Items, Source Editorial Apparatus, Assembly Hints, Keywords, Quality Checks, Project Notes.
- Because this Norton source is copyrighted/restricted, summarize in original language and do not transcribe extended prose.
- Keep source notes, bibliography, and source editorial apparatus separate from excerpt cards.
- If you are uncertain, produce a valid low-confidence record with explicit uncertainty rather than failing to write the file.
- {final_rule}

Attempt: {attempt}
{repair_text}
{page_text_section}

## Page Task Prompt

{base_prompt}
"""


def extract_markdown_record(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None

    fence_match = re.search(r"```(?:markdown|md)?\s*(---\n.*?\n---\n.*?)(?:\n```|$)", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip() + "\n"

    start = stripped.find("---\n")
    if start >= 0:
        return stripped[start:].strip() + "\n"

    return None


def materialize_last_message(last_message_path: Path, output_file: Path) -> bool:
    if not last_message_path.exists():
        return False
    candidate = extract_markdown_record(last_message_path.read_text(encoding="utf-8"))
    if not candidate:
        return False
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(candidate, encoding="utf-8")
    return True


def validate_output(output_file: Path) -> tuple[bool, list[str]]:
    if not output_file.exists():
        return False, ["agent did not create PAGE_RECORD_OUTPUT"]
    result = validate_file(output_file, expected_type="page_record")
    return not result.errors, result.errors


def run_codex(command: list[str], prompt: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        input=prompt,
        text=True,
        capture_output=True,
    )


def extract_page_text(page_path: Path) -> str:
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(page_path), "-"],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return f"[pdftotext failed: {exc}]"
    if result.returncode != 0:
        error = result.stderr.strip() or f"pdftotext exited with {result.returncode}"
        return f"[pdftotext failed: {error}]"
    return result.stdout


def openai_text_from_response(data: dict[str, object]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    parts: list[str] = []
    output = data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
    if parts:
        return "\n".join(parts)

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content

    raise RuntimeError("API response did not contain model text")


def call_openai_api(
    *,
    prompt: str,
    model: str,
    api_key: str,
    base_url: str,
    api_mode: str,
    timeout: float,
) -> str:
    base_url = base_url.rstrip("/")
    if api_mode == "responses":
        url = f"{base_url}/responses"
        payload: dict[str, object] = {
            "model": model,
            "input": prompt,
        }
    elif api_mode == "chat_completions":
        url = f"{base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You produce only valid Markdown records that match the user's "
                        "schema and rights constraints."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
    else:
        raise RuntimeError("api_mode must be responses or chat_completions")

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API request failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"API request failed: {exc}") from exc

    if not isinstance(response_data, dict):
        raise RuntimeError("API response was not a JSON object")
    return openai_text_from_response(response_data)


def write_model_text(model_text: str, output_file: Path) -> None:
    markdown = extract_markdown_record(model_text) or model_text.strip() + "\n"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=os.environ.get("SOURCE_CONFIG", "data/extraction-sources.yml"))
    parser.add_argument("--codex-bin", default=os.environ.get("CODEX_BIN", "codex"))
    parser.add_argument(
        "--backend",
        choices=["codex", "openai"],
        default=os.environ.get("PAGE_AGENT_BACKEND", "codex"),
        help="Execution backend. Use openai for API-driven extraction.",
    )
    parser.add_argument(
        "--openai-base-url",
        default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    parser.add_argument(
        "--openai-model",
        default=os.environ.get("OPENAI_MODEL") or os.environ.get("CODEX_MODEL"),
    )
    parser.add_argument(
        "--openai-api-mode",
        choices=["responses", "chat_completions"],
        default=os.environ.get("OPENAI_API_MODE", "responses"),
    )
    parser.add_argument(
        "--openai-timeout",
        type=float,
        default=float(os.environ.get("OPENAI_TIMEOUT", "180")),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        env = require_env()
        prompt_file = Path(env["PAGE_PROMPT_FILE"])
        output_file = Path(env["PAGE_RECORD_OUTPUT"])
        page_path = resolve_page_path(env["SOURCE_ID"], env["PAGE_FILE"], args.config)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not prompt_file.exists():
        print(f"error: PAGE_PROMPT_FILE does not exist: {prompt_file}", file=sys.stderr)
        return 1
    if not page_path.exists():
        print(f"error: resolved page path does not exist: {page_path}", file=sys.stderr)
        return 1

    base_prompt = prompt_file.read_text(encoding="utf-8")
    page_text = extract_page_text(page_path) if args.backend == "openai" else None

    with tempfile.TemporaryDirectory(prefix="codex-page-agent-") as temp_dir:
        last_message_path = Path(temp_dir) / "last-message.md"
        codex_bin = shutil.which(args.codex_bin) or args.codex_bin
        command = codex_command(codex_bin, last_message_path)

        if args.dry_run:
            print(f"prompt_file: {prompt_file}")
            print(f"output_file: {output_file}")
            print(f"page_path: {page_path}")
            print(f"backend: {args.backend}")
            if args.backend == "codex":
                print("command: " + " ".join(command))
            else:
                print(f"openai_base_url: {args.openai_base_url}")
                print(f"openai_model: {args.openai_model or '[required for actual run]'}")
                print(f"openai_api_mode: {args.openai_api_mode}")
                print(f"page_text_chars: {len(page_text or '')}")
            return 0

        if args.backend == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                print("error: OPENAI_API_KEY is required for --backend openai", file=sys.stderr)
                return 1
            if not args.openai_model:
                print(
                    "error: OPENAI_MODEL or CODEX_MODEL is required for --backend openai",
                    file=sys.stderr,
                )
                return 1

        validation_errors: list[str] | None = None
        current_output: str | None = None
        last_result: subprocess.CompletedProcess[str] | None = None

        for attempt in (1, 2):
            prompt = build_prompt(
                base_prompt=base_prompt,
                page_path=page_path,
                output_file=output_file,
                env=env,
                attempt=attempt,
                backend=args.backend,
                page_text=page_text,
                validation_errors=validation_errors,
                current_output=current_output,
            )
            if args.backend == "codex":
                last_message_path.unlink(missing_ok=True)
                last_result = run_codex(command, prompt)
            else:
                try:
                    model_text = call_openai_api(
                        prompt=prompt,
                        model=args.openai_model,
                        api_key=api_key,
                        base_url=args.openai_base_url,
                        api_mode=args.openai_api_mode,
                        timeout=args.openai_timeout,
                    )
                except Exception as exc:
                    validation_errors = [str(exc)]
                    break
                write_model_text(model_text, output_file)

            ok, errors = validate_output(output_file)
            if not ok and args.backend == "codex":
                materialize_last_message(last_message_path, output_file)
                ok, errors = validate_output(output_file)
            if ok:
                return 0

            validation_errors = errors
            current_output = output_file.read_text(encoding="utf-8") if output_file.exists() else ""
            if attempt == 1:
                continue

        if last_result is not None and last_result.returncode != 0:
            print(last_result.stderr.strip() or last_result.stdout.strip(), file=sys.stderr)
        for error in validation_errors or ["page agent failed"]:
            print(f"validation error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
