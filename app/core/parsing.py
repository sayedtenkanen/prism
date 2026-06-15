"""Enhanced parse_findings with proper error handling."""
import json
import logging
from typing import Any

from app.core.exceptions import ParseFindingsError

logger = logging.getLogger(__name__)


def parse_findings(raw: Any, agent_name: str = "unknown") -> list[Any]:
    """Parse findings from raw LLM output with comprehensive error handling.

    Args:
        raw: Raw value to parse (list, JSON string, or other)
        agent_name: Name of the agent producing findings (for logging)

    Returns:
        List of findings parsed from raw value, or empty list on error

    Raises:
        ParseFindingsError: If raw value is a string but cannot be parsed as JSON
    """
    if isinstance(raw, list):
        return raw

    if isinstance(raw, str):
        if not raw.strip():
            logger.warning(f"Empty findings string from agent {agent_name}")
            return []

        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                logger.warning(
                    f"Findings from {agent_name} parsed to {type(parsed).__name__}, expected list"
                )
                return [parsed] if parsed else []
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from agent {agent_name}: {e}")
            raise ParseFindingsError(raw, e) from e
        except (TypeError, ValueError) as e:
            logger.error(f"Type error parsing findings from {agent_name}: {e}")
            raise ParseFindingsError(raw, e) from e

    logger.warning(f"Unexpected findings type {type(raw).__name__} from agent {agent_name}")
    return []
