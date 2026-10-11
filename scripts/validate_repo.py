#!/usr/bin/env python3
"""Validate required Proofline project files and basic repository invariants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/ARCHITECTURE.md",
    "docs/REVIEW_PROTOCOL.md",
    "docs/OPERATING_MODEL.md",
    "docs/ROADMAP.md",
    "docs/RISK_REGISTER.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/ADR/0001-local-first-vertical-slice.md",
    ".github/workflows/ci.yml",
    ".github/dependabot.yml",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/ISSUE_TEMPLATE/review.yml",
    "tests/test_repo_contract.py",
]


def main() -> int:
    errors = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        if "Demonstrate, don't advertise." not in text:
            errors.append("README must preserve the evidence-first principle")

    workflow = ROOT / ".github/workflows/ci.yml"
    if workflow.exists():
        text = workflow.read_text(encoding="utf-8")
        if "permissions:" not in text or "contents: read" not in text:
            errors.append("CI workflow must declare minimal read-only contents permission")
        if "pull_request:" not in text:
            errors.append("CI workflow must run for pull requests")
        if "persist-credentials: false" not in text:
            errors.append("checkout must not persist GitHub credentials")
        if "actions/checkout@" not in text or "actions/setup-python@" not in text:
            errors.append("CI must declare explicit checkout and Python setup actions")

    if errors:
        print("REPOSITORY VALIDATION: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"REPOSITORY VALIDATION: PASS ({len(REQUIRED)} required files; core CI invariants checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
