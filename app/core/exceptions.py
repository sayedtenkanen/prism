"""Custom exception classes for Prism."""


class PrismException(Exception):
    """Base exception for all Prism errors."""

    pass


class ParseFindingsError(PrismException):
    """Raised when findings JSON parsing fails."""

    def __init__(self, raw_value: str, original_error: Exception) -> None:
        self.raw_value = raw_value
        self.original_error = original_error
        super().__init__(
            f"Failed to parse findings from: {raw_value[:100]}... Error: {str(original_error)}"
        )


class InvalidConfidenceAdjustment(PrismException):
    """Raised when confidence adjustment value is invalid."""

    def __init__(self, value: str, agent_name: str) -> None:
        self.value = value
        self.agent_name = agent_name
        super().__init__(
            f"Invalid confidence adjustment '{value}' from agent '{agent_name}'. "
            f"Expected numeric value between -1.0 and 1.0"
        )


class GraphExecutionError(PrismException):
    """Raised when graph pipeline execution fails."""

    def __init__(self, step: str, original_error: Exception) -> None:
        self.step = step
        self.original_error = original_error
        super().__init__(f"Graph execution failed at step '{step}': {str(original_error)}")


class InvalidTriggerConfig(PrismException):
    """Raised when job trigger configuration is invalid."""

    def __init__(self, trigger: str, message: str) -> None:
        self.trigger = trigger
        super().__init__(f"Invalid trigger configuration for '{trigger}': {message}")


class InvalidCronExpression(InvalidTriggerConfig):
    """Raised when cron expression is malformed."""

    def __init__(self, expression: str, expected_fields: int = 5) -> None:
        self.expression = expression
        self.expected_fields = expected_fields
        parts = len(expression.split())
        super().__init__(
            "cron",
            f"Expected {expected_fields} fields, got {parts}. "
            f"Format: 'minute hour day month day_of_week'",
        )
