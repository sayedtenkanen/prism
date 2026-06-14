---
name: least-privilege
description: Permission manifest enforcement, scoped credentials, and identity file protection. Use when user mentions "least privilege", "permissions", "access control", "manifest", "scoped credentials". Triggers on AST03 security questions.
---

# Least Privilege (AST03)

## Overview

Skills should only have access to resources required for their stated function. Over-privileged skills create excessive blast radius — a legitimate skill with overly permissive access can be weaponized by prompt injection attacks.

**Key Finding**: 280+ skills on ClawHub were found exposing API keys and PII beyond their declared function (Snyk, Feb 2026).

## Permission Manifest

### YAML Frontmatter Schema

```yaml
# SKILL.md frontmatter
---
name: example-skill
version: "1.0.0"

permissions:
  files:
    read:
      - ~/.config/app.json
      - ./data/
    write:
      - ./output/
    deny_write:
      - SOUL.md
      - MEMORY.md
      - AGENTS.md
      - ~/.ssh/
      - ~/.env
  network:
    allow:
      - api.example.com
      - github.com
    deny: "*"
  shell: false
  tools:
    - web_fetch
    - read_file
---
```

### Manifest Validation

```python
from pydantic import BaseModel, field_validator
from pathlib import Path


class FilePermissions(BaseModel):
    read: list[str] = []
    write: list[str] = []
    deny_write: list[str] = [
        "SOUL.md",
        "MEMORY.md",
        "AGENTS.md",
        "~/.ssh/",
        "~/.env",
    ]


class NetworkPermissions(BaseModel):
    allow: list[str] = []
    deny: str = "*"

    @field_validator("deny")
    @classmethod
    def validate_deny(cls, v: str) -> str:
        if v != "*":
            raise ValueError("Network deny must be '*' (default deny all)")
        return v


class SkillPermissions(BaseModel):
    files: FilePermissions = FilePermissions()
    network: NetworkPermissions = NetworkPermissions()
    shell: bool = False
    tools: list[str] = []


class SkillManifest(BaseModel):
    name: str
    version: str
    permissions: SkillPermissions = SkillPermissions()

    def validate_least_privilege(self, stated_function: str) -> list[str]:
        """Validate permissions match stated function."""
        issues = []

        if self.permissions.shell and "shell" not in stated_function.lower():
            issues.append("Shell access granted but not required for stated function")

        if "*" in self.permissions.network.allow:
            issues.append("Wildcard network access violates least privilege")

        if not self.permissions.files.deny_write:
            issues.append("No identity file protection configured")

        return issues
```

### Permission Scope Enforcement

```python
from pathlib import Path
import fnmatch


class PermissionEnforcer:
    """Enforce skill permissions at runtime."""

    def __init__(self, permissions: SkillPermissions):
        self.permissions = permissions

    def check_file_access(self, path: Path, mode: str) -> bool:
        """Check if file access is permitted."""
        path_str = str(path)

        # Check deny_write first
        for denied in self.permissions.files.deny_write:
            if fnmatch.fnmatch(path_str, denied):
                return False

        if mode == "read":
            return any(
                fnmatch.fnmatch(path_str, allowed)
                for allowed in self.permissions.files.read
            )
        elif mode == "write":
            return any(
                fnmatch.fnmatch(path_str, allowed)
                for allowed in self.permissions.files.write
            )

        return False

    def check_network_access(self, domain: str) -> bool:
        """Check if network access is permitted."""
        if "*" in self.permissions.network.allow:
            return True

        return any(
            fnmatch.fnmatch(domain, allowed)
            for allowed in self.permissions.network.allow
        )

    def check_shell_access(self) -> bool:
        """Check if shell access is permitted."""
        return self.permissions.shell

    def check_tool_access(self, tool: str) -> bool:
        """Check if tool access is permitted."""
        return tool in self.permissions.tools
```

## Identity File Protection

### Protected Files

```python
IDENTITY_FILES = {
    "agent_identity": [
        "SOUL.md",
        "MEMORY.md",
        "AGENTS.md",
    ],
    "ssh_keys": [
        "~/.ssh/id_rsa",
        "~/.ssh/id_ed25519",
        "~/.ssh/authorized_keys",
    ],
    "credentials": [
        "~/.env",
        "~/.aws/credentials",
        "~/.config/gcloud/credentials.db",
    ],
}


def check_identity_protection(path: Path) -> dict:
    """Check if path is a protected identity file."""
    path_str = str(path)

    for category, files in IDENTITY_FILES.items():
        for protected in files:
            if fnmatch.fnmatch(path_str, protected):
                return {
                    "protected": True,
                    "category": category,
                    "severity": "critical",
                    "message": f"Attempt to access protected {category} file",
                }

    return {"protected": False}
```

### Audit Logging

```python
import logging
from datetime import datetime, timezone
from pathlib import Path


logger = logging.getLogger("skill.audit")


def log_permission_check(
    skill_name: str,
    resource: str,
    mode: str,
    allowed: bool,
) -> None:
    """Log permission check for audit trail."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": skill_name,
        "resource": resource,
        "mode": mode,
        "allowed": allowed,
    }

    if allowed:
        logger.info("Permission granted", extra=event)
    else:
        logger.warning("Permission denied", extra=event)
```

## Scoped Credentials

### Per-Skill Credentials

```python
from pydantic import BaseModel, SecretStr


class ScopedCredential(BaseModel):
    skill_name: str
    service: str
    credential: SecretStr
    scopes: list[str]
    expires_at: str | None = None


class CredentialManager:
    """Manage scoped credentials per skill."""

    def __init__(self) -> None:
        self._credentials: dict[str, dict[str, ScopedCredential]] = {}

    def register_credential(self, credential: ScopedCredential) -> None:
        """Register a scoped credential for a skill."""
        if credential.skill_name not in self._credentials:
            self._credentials[credential.skill_name] = {}

        self._credentials[credential.skill_name][credential.service] = credential

    def get_credential(self, skill_name: str, service: str) -> ScopedCredential | None:
        """Get credential for specific skill and service."""
        return self._credentials.get(skill_name, {}).get(service)

    def list_credentials(self, skill_name: str) -> list[ScopedCredential]:
        """List all credentials for a skill."""
        return list(self._credentials.get(skill_name, {}).values())
```

## Checklist

Before granting permissions:

```bash
# Validate manifest
python -c "
from app.security.least_privilege import SkillManifest
import yaml
from pathlib import Path

manifest_data = yaml.safe_load(Path('SKILL.md').read_text().split('---')[1])
manifest = SkillManifest(**manifest_data)
issues = manifest.validate_least_privilege('review code for security')
print(issues)
"

# Audit existing permissions
grep -A 20 "permissions:" .opencode/skills/*/SKILL.md
```

## Common Violations

| Violation | Risk | Fix |
|-----------|------|-----|
| Wildcard network access | High | Use domain allowlists |
| No deny_write for identity files | Critical | Add SOUL.md, MEMORY.md to deny_write |
| Shell access on non-shell skills | Medium | Set shell: false |
| Overly broad file read/write | Medium | Scope to specific paths |
| Shared agent-level credentials | High | Use per-skill scoped credentials |

## References

- [OWASP AST03 — Over-Privileged Skills](https://owasp.github.io/www-project-agentic-skills-top-10/ast03.html)
- [Snyk: 280+ Leaky Skills](https://snyk.io/blog/280-leaky-skills-openclaw-clawhub-exposing-api-keys-pii/)
- [ASVS V4 — Access Control](https://owasp.org/www-project-application-security-verification-standard/)
- [CWE-250 — Execution with Unnecessary Privileges](https://cwe.mitre.org/data/definitions/250.html)
