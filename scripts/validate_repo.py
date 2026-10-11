#!/usr/bin/env python3
"""Validate required Proofline files and key CI invariants."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=["README.md","CONTRIBUTING.md","SECURITY.md","index.html","verify_csv.py","requirements-dev.txt","run_checks.sh","examples/demo_sales.csv","docs/ARCHITECTURE.md","docs/OPERATING_MODEL.md","docs/REVIEW_PROTOCOL.md","docs/ROADMAP.md","docs/RISK_REGISTER.md","docs/RELEASE_CHECKLIST.md","docs/CI_CD.md","docs/QUALITY_GATES.md","docs/ARTIFACT_CATALOG.md","docs/context/AGENT_START_HERE.md","docs/context/PROJECT_CONTEXT.md","docs/context/EXTERNAL_CONTEXT.md","docs/architecture/OVERVIEW.md","docs/review/REVIEW_PROTOCOL.md","docs/review/templates/EXTERNAL_CRITIQUE_BRIEF.md","docs/product/PILOT_OFFER.md","docs/LICENSING_BEFORE_PUBLIC_RELEASE.md","docs/architecture/decisions/ADR-0001-local-first-mvp.md",".github/workflows/ci.yml",".github/dependabot.yml",".github/CODEOWNERS",".github/pull_request_template.md",".github/ISSUE_TEMPLATE/feature.yml",".github/ISSUE_TEMPLATE/review.yml","tests/test_verify_csv.py","tests/test_package.py","tests/test_repo_contract.py","tests/browser_test.py"]
def main():
    errors=[]
    errors.extend("missing required file: "+p for p in REQUIRED if not (ROOT/p).is_file())
    readme=ROOT/"README.md"
    if readme.exists() and "Demonstrate, don't advertise." not in readme.read_text(encoding="utf-8"): errors.append("README lost evidence-first principle")
    ci=ROOT/".github/workflows/ci.yml"
    if ci.exists():
        text=ci.read_text(encoding="utf-8")
        for item in ("permissions:","contents: read","pull_request:","persist-credentials: false","chromium-interactions:"):
            if item not in text: errors.append("CI missing invariant: "+item)
    if errors:
        print("REPOSITORY VALIDATION: FAIL"); print("\n".join("- "+e for e in errors)); return 1
    print("REPOSITORY VALIDATION: PASS ("+str(len(REQUIRED))+" required files and CI invariants)"); return 0
if __name__=="__main__": raise SystemExit(main())
