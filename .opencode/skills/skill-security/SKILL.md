---
name: skill-security
description: Skill integrity validation, signature verification, and supply chain security. Use when user mentions "skill security", "signature verification", "supply chain", "skill integrity", "hash pinning". Triggers on AST01/AST02 security questions.
---

# Skill Security (AST01, AST02)

## Overview

Skills define the behavior layer of AI agents. A malicious or compromised skill gains immediate access to API keys, SSH credentials, wallet files, and shell. The OWASP Agentic Skills Top 10 identifies this as Critical severity.

**Key Statistics (2026):**
- 36.82% of skills contain security flaws (Snyk ToxicSkills)
- 13.4% have critical vulnerabilities
- 76+ confirmed malicious payloads
- 1,184 malicious skills in ClawHavoc campaign

## Signature Verification

### Ed25519 Signatures

```python
import hashlib
from pathlib import Path

def verify_skill_signature(
    skill_content: str,
    signature: str,
    public_key: str,
) -> bool:
    """Verify ed25519 signature of skill content."""
    try:
        import ed25519
        pk = ed25519.VerifyingKey(public_key.encode(), encoding="hex")
        pk.verify(signature.encode(), skill_content.encode(), encoding="hex")
        return True
    except Exception:
        return False


def hash_pin_skill(skill_path: Path, expected_hash: str) -> bool:
    """Verify skill content hash matches expected value."""
    content = skill_path.read_text(encoding="utf-8")
    actual_hash = hashlib.sha256(content.encode()).hexdigest()
    return actual_hash == expected_hash
```

### SKILL.md Frontmatter Validation

```python
import yaml
from pathlib import Path
from pydantic import BaseModel


class SkillManifest(BaseModel):
    name: str
    version: str
    signature: str
    content_hash: str
    permissions: dict[str, list[str]] | None = None


def validate_skill_manifest(skill_path: Path) -> SkillManifest:
    """Parse and validate SKILL.md frontmatter."""
    content = skill_path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        raise ValueError("Missing YAML frontmatter")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter format")

    manifest = yaml.safe_load(parts[1])
    return SkillManifest(**manifest)
```

## Supply Chain Security

### Hash Pinning

```python
import hashlib
import json
from pathlib import Path

SKILL_LOCK_FILE = "skills.lock.json"


def pin_skill(skill_path: Path, lock_file: Path | None = None) -> dict:
    """Create hash pin for installed skill."""
    content = skill_path.read_text(encoding="utf-8")
    skill_hash = hashlib.sha256(content.encode()).hexdigest()

    pin = {
        "path": str(skill_path),
        "hash": f"sha256:{skill_hash}",
        "size": len(content),
    }

    if lock_file and lock_file.exists():
        pins = json.loads(lock_file.read_text(encoding="utf-8"))
    else:
        pins = {}

    pins[skill_path.name] = pin
    if lock_file:
        lock_file.write_text(json.dumps(pins, indent=2), encoding="utf-8")

    return pin


def verify_pins(lock_file: Path) -> list[str]:
    """Verify all skills match their pinned hashes."""
    violations = []
    pins = json.loads(lock_file.read_text(encoding="utf-8"))

    for name, pin in pins.items():
        skill_path = Path(pin["path"])
        if not skill_path.exists():
            violations.append(f"{name}: file missing")
            continue

        content = skill_path.read_text(encoding="utf-8")
        actual_hash = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

        if actual_hash != pin["hash"]:
            violations.append(f"{name}: hash mismatch (expected {pin['hash']}, got {actual_hash})")

    return violations
```

### Registry Scanning

```python
import subprocess
from pathlib import Path


def scan_skill(skill_path: Path) -> dict:
    """Scan skill for security issues."""
    results = {
        "path": str(skill_path),
        "issues": [],
        "risk_level": "low",
    }

    content = skill_path.read_text(encoding="utf-8")

    # Check for suspicious patterns
    suspicious_patterns = [
        "curl ",
        "wget ",
        "eval(",
        "exec(",
        "subprocess",
        "os.system",
        "base64",
        "decode",
        "exfiltrate",
        "~/.ssh",
        "~/.env",
        "SOUL.md",
        "MEMORY.md",
    ]

    for pattern in suspicious_patterns:
        if pattern.lower() in content.lower():
            results["issues"].append(f"Suspicious pattern: {pattern}")

    if len(results["issues"]) > 3:
        results["risk_level"] = "critical"
    elif len(results["issues"]) > 1:
        results["risk_level"] = "high"
    elif results["issues"]:
        results["risk_level"] = "medium"

    return results
```

## Behavioral Indicators

### Red Flags in Skills

```python
RED_FLAGS = {
    "credential_access": [
        "~/.ssh",
        "~/.env",
        "API_KEY",
        "SECRET",
        "TOKEN",
        "CREDENTIAL",
    ],
    "identity_file_write": [
        "SOUL.md",
        "MEMORY.md",
        "AGENTS.md",
    ],
    "network_exfiltration": [
        "curl",
        "wget",
        "requests.post",
        "httpx",
        "webhook",
    ],
    "shell_execution": [
        "subprocess.run",
        "os.system",
        "eval(",
        "exec(",
    ],
}


def analyze_skill_behavior(skill_path: Path) -> dict:
    """Analyze skill for behavioral red flags."""
    content = skill_path.read_text(encoding="utf-8").lower()
    findings = {}

    for category, patterns in RED_FLAGS.items():
        matches = [p for p in patterns if p.lower() in content]
        if matches:
            findings[category] = matches

    return findings
```

## Checklist

Before accepting or modifying skills:

```bash
# Verify signature
python -c "from app.security.skill_verifier import verify_skill; verify_skill('path/to/skill')"

# Scan for issues
python -c "from app.security.skill_verifier import scan_skill; print(scan_skill('path/to/skill'))"

# Verify hash pins
python -c "from app.security.skill_verifier import verify_pins; print(verify_pins('skills.lock.json'))"
```

## Incident Response

For confirmed malicious skills:

1. **Isolate** - Remove skill from active environment
2. **Revoke** - Rotate any credentials the skill accessed
3. **Scan** - Check for lateral movement or persistence
4. **Report** - Notify registry maintainers
5. **Document** - Record indicators of compromise

## References

- [OWASP AST01 — Malicious Skills](https://owasp.github.io/www-project-agentic-skills-top-10/ast01.html)
- [OWASP AST02 — Supply Chain Compromise](https://owasp.github.io/www-project-agentic-skills-top-10/ast02.html)
- [Snyk ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)
- [Antiy CERT: ClawHavoc Campaign](https://www.antiy.com/)
