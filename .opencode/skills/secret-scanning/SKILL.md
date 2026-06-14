---
name: secret-scanning
description: Detecting credential leaks, API keys, and PII in skills and code. Use when user mentions "secret scanning", "credential detection", "API key", "leaked secrets", "gitleaks". Triggers on AST01/AST03 security questions.
---

# Secret Scanning (AST01, AST03)

## Overview

Skills often have access to sensitive data. Malicious or poorly written skills can leak API keys, SSH credentials, wallet files, and PII. The OWASP Agentic Skills Top 10 found 280+ skills exposing credentials beyond their declared function.

## Detection Patterns

### API Key Patterns

```python
import re
from pathlib import Path


SECRET_PATTERNS = {
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "aws_secret_key": r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})",
    "github_token": r"ghp_[A-Za-z0-9]{36}",
    "github_fine_grained": r"github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}",
    "slack_token": r"xox[baprs]-[0-9]{10,13}-[0-9a-zA-Z-]+",
    "slack_webhook": r"https://hooks\.slack\.com/services/T[A-Z0-9]{8}/B[A-Z0-9]{8}/[a-zA-Z0-9]{24}",
    "stripe_key": r"sk_live_[0-9a-zA-Z]{24,}",
    "openai_key": r"sk-[A-Za-z0-9]{48}",
    "anthropic_key": r"sk-ant-[A-Za-z0-9]{48}",
    "google_api_key": r"AIza[0-9A-Za-z_-]{35}",
    "private_key_header": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
}


def scan_for_secrets(content: str) -> list[dict]:
    """Scan content for leaked secrets."""
    findings = []

    for name, pattern in SECRET_PATTERNS.items():
        matches = re.finditer(pattern, content)
        for match in matches:
            findings.append({
                "type": name,
                "line": content[:match.start()].count("\n") + 1,
                "match": match.group()[:20] + "...",
                "severity": "critical",
            })

    return findings
```

### PII Patterns

```python
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone_us": r"(?:\+1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}",
    "ssn": r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",
    "credit_card": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "aws_arn": r"arn:aws:[a-zA-Z0-9-]+:[a-z0-9-]*:[0-9]{12}:[a-zA-Z0-9/_-]+",
}


def scan_for_pii(content: str) -> list[dict]:
    """Scan content for PII exposure."""
    findings = []

    for name, pattern in PII_PATTERNS.items():
        matches = re.finditer(pattern, content)
        for match in matches:
            findings.append({
                "type": name,
                "line": content[:match.start()].count("\n") + 1,
                "match": match.group()[:20] + "..." if len(match.group()) > 20 else match.group(),
                "severity": "high",
            })

    return findings
```

## Skill File Scanning

### SKILL.md Analysis

```python
from pathlib import Path


def scan_skill_file(skill_path: Path) -> dict:
    """Scan a skill file for secrets and PII."""
    content = skill_path.read_text(encoding="utf-8")

    secrets = scan_for_secrets(content)
    pii = scan_for_pii(content)

    return {
        "path": str(skill_path),
        "secrets": secrets,
        "pii": pii,
        "total_findings": len(secrets) + len(pii),
        "risk_level": _calculate_risk(secrets, pii),
    }


def _calculate_risk(secrets: list[dict], pii: list[dict]) -> str:
    """Calculate overall risk level."""
    critical_count = sum(1 for s in secrets if s["severity"] == "critical")
    high_count = sum(1 for p in pii if p["severity"] == "high")

    if critical_count > 0:
        return "critical"
    elif high_count > 2:
        return "high"
    elif high_count > 0:
        return "medium"
    return "low"
```

### Environment File Scanning

```python
def scan_env_file(env_path: Path) -> dict:
    """Scan .env files for exposed secrets."""
    if not env_path.exists():
        return {"status": "not_found"}

    content = env_path.read_text(encoding="utf-8")
    findings = []

    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key, value = line.split("=", 1)
            value = value.strip("'\"")

            if value and len(value) > 8:
                findings.append({
                    "line": line_num,
                    "key": key.strip(),
                    "severity": "critical",
                    "message": f"Exposed credential: {key.strip()}",
                })

    return {
        "path": str(env_path),
        "findings": findings,
        "total": len(findings),
    }
```

## Integration with Gitleaks

```python
import subprocess
from pathlib import Path


def run_gitleaks(scan_path: Path) -> dict:
    """Run gitleaks scan on skill directory."""
    try:
        result = subprocess.run(
            ["gitleaks", "detect", "--source", str(scan_path), "--report-format", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        return {
            "exit_code": result.returncode,
            "findings": result.stdout,
            "errors": result.stderr,
        }
    except FileNotFoundError:
        return {"error": "gitleaks not installed"}
    except subprocess.TimeoutExpired:
        return {"error": "scan timed out"}
```

## Checklist

Before committing skills:

```bash
# Scan skill files
gitleaks detect --source .opencode/skills/ --verbose

# Scan for hardcoded secrets
grep -rn "API_KEY\|SECRET\|TOKEN\|PASSWORD" .opencode/skills/

# Check for private keys
find .opencode/skills/ -name "*.pem" -o -name "*.key" -o -name "*.p12"
```

## Common Findings

| Pattern | Severity | Action |
|---------|----------|--------|
| AWS keys | Critical | Rotate immediately |
| GitHub tokens | Critical | Revoke and rotate |
| Private keys | Critical | Rotate certificates |
| API keys | High | Rotate and audit |
| Email addresses | Medium | Redact or mask |
| IP addresses | Low | Document if intentional |

## References

- [OWASP AST01 — Malicious Skills](https://owasp.github.io/www-project-agentic-skills-top-10/ast01.html)
- [OWASP AST03 — Over-Privileged Skills](https://owasp.github.io/www-project-agentic-skills-top-10/ast03.html)
- [Snyk: 280+ Leaky Skills](https://snyk.io/blog/280-leaky-skills-openclaw-clawhub-exposing-api-keys-pii/)
- [Gitleaks Documentation](https://github.com/gitleaks/gitleaks)
