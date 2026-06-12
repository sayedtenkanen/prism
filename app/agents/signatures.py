import dspy


class SecurityReview(dspy.Signature):
    """Review code for security vulnerabilities following OWASP guidelines.

    Check for: injection risks, authentication/authorization flaws,
    secrets detection, dependency vulnerabilities, XSS, CSRF,
    SQL injection, path traversal, and insecure configurations.
    """

    files_changed: str = dspy.InputField(desc="List of changed files with their paths and languages")
    diff: str = dspy.InputField(desc="The unified diff of changes")
    findings: str = dspy.OutputField(
        desc="JSON array of findings, each with: finding, severity (critical/high/medium/low/info), "
        "confidence (0.0-1.0), evidence, recommendation, file, line, cwe_id, owasp_category"
    )


class PerformanceReview(dspy.Signature):
    """Review code for performance issues and optimization opportunities.

    Check for: N+1 query patterns, inefficient loops, memory leaks,
    unnecessary allocations, network inefficiencies, database concerns,
    caching opportunities, and algorithmic complexity.
    """

    files_changed: str = dspy.InputField(desc="List of changed files with their paths and languages")
    diff: str = dspy.InputField(desc="The unified diff of changes")
    findings: str = dspy.OutputField(
        desc="JSON array of findings, each with: finding, severity (critical/high/medium/low/info), "
        "confidence (0.0-1.0), evidence, recommendation, file, line, category"
    )


class MaintainabilityReview(dspy.Signature):
    """Review code for maintainability, readability, and design quality.

    Check for: code complexity, readability issues, design smells,
    SOLID principle violations, refactoring opportunities,
    code duplication, and naming conventions.
    """

    files_changed: str = dspy.InputField(desc="List of changed files with their paths and languages")
    diff: str = dspy.InputField(desc="The unified diff of changes")
    findings: str = dspy.OutputField(
        desc="JSON array of findings, each with: finding, severity (critical/high/medium/low/info), "
        "confidence (0.0-1.0), evidence, recommendation, file, line, complexity_score"
    )


class TestingReview(dspy.Signature):
    """Review code for test quality and coverage gaps.

    Check for: missing test coverage, weak assertions, untested branches,
    regression risks, test isolation issues, and test maintainability.
    """

    files_changed: str = dspy.InputField(desc="List of changed files with their paths and languages")
    diff: str = dspy.InputField(desc="The unified diff of changes")
    findings: str = dspy.OutputField(
        desc="JSON array of findings, each with: finding, severity (critical/high/medium/low/info), "
        "confidence (0.0-1.0), evidence, recommendation, file, line, coverage_gap"
    )


class ArchitectureReview(dspy.Signature):
    """Review code for architectural quality and design patterns.

    Check for: layer violations, boundary violations, service coupling,
    domain consistency, dependency direction, and separation of concerns.
    """

    files_changed: str = dspy.InputField(desc="List of changed files with their paths and languages")
    diff: str = dspy.InputField(desc="The unified diff of changes")
    findings: str = dspy.OutputField(
        desc="JSON array of findings, each with: finding, severity (critical/high/medium/low/info), "
        "confidence (0.0-1.0), evidence, recommendation, file, line, layer_violation"
    )


class DocumentationReview(dspy.Signature):
    """Review code for documentation quality and completeness.

    Check for: missing documentation, API documentation gaps,
    changelog requirements, inline comments, and README updates.
    """

    files_changed: str = dspy.InputField(desc="List of changed files with their paths and languages")
    diff: str = dspy.InputField(desc="The unified diff of changes")
    findings: str = dspy.OutputField(
        desc="JSON array of findings, each with: finding, severity (critical/high/medium/low/info), "
        "confidence (0.0-1.0), evidence, recommendation, file, line"
    )


class JudgeAggregation(dspy.Signature):
    """Aggregate and deduplicate review findings from multiple agents into a single coherent verdict.

    Remove duplicate findings, rank by severity, resolve contradictions,
    and produce a clear engineering summary.
    """

    all_findings: str = dspy.InputField(
        desc="JSON object with agent_name keys, each containing a JSON array of findings"
    )
    summary: str = dspy.OutputField(desc="Executive summary of the review")
    critical_findings: str = dspy.OutputField(desc="JSON array of critical severity findings")
    major_findings: str = dspy.OutputField(desc="JSON array of high/major severity findings")
    minor_findings: str = dspy.OutputField(desc="JSON array of medium/low/info severity findings")
    approved: bool = dspy.OutputField(desc="Whether the PR is approved (true) or needs changes (false)")


class DebateChallenge(dspy.Signature):
    """Challenge a finding from another agent with evidence-based reasoning.

    Evaluate whether the finding is valid, partially valid, or invalid.
    Provide counter-evidence or context that may reduce confidence.
    """

    finding: str = dspy.InputField(desc="The finding to challenge (JSON)")
    challenger_agent: str = dspy.InputField(desc="Name of the agent challenging the finding")
    code_context: str = dspy.InputField(desc="Relevant code context for evaluation")
    challenge: str = dspy.OutputField(desc="The challenge text explaining why the finding may be invalid")
    confidence_adjustment: float = dspy.OutputField(
        desc="Suggested confidence adjustment (-1.0 to 1.0, negative = reduce confidence)"
    )
