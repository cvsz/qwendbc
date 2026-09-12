from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_ENV_FILES = (
    ROOT / ".env.example",
    ROOT / ".env.webui.example",
    ROOT / "configs" / ".env.example",
)
SENSITIVE_NAME = re.compile(r"(?:API_KEY|ACCESS_TOKEN|SECRET_KEY|PASSWORD|JUPYTER_TOKEN)$")
EXTRA_SENSITIVE_NAMES = {
    "OPENWEBUI_GOOGLE_PSE_CX",
    # This variable is JSON and may contain OAuth client_secret values.
    "OPENWEBUI_OAUTH_PROVIDERS",
}


def test_example_environment_files_do_not_embed_credentials() -> None:
    findings: list[str] = []
    for path in EXAMPLE_ENV_FILES:
        for line_number, raw_line in enumerate(
            path.read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if SENSITIVE_NAME.search(name) or name in EXTRA_SENSITIVE_NAMES:
                if value.strip():
                    findings.append(f"{path.relative_to(ROOT)}:{line_number}:{name}")

    assert (
        findings == []
    ), "Example environment files must contain blank credential values: " + ", ".join(findings)
