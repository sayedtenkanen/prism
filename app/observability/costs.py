from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

MODEL_COSTS_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}


class TokenCost(BaseModel):
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class CostTracker:
    def __init__(self, budget_limit: float | None = None) -> None:
        self.budget_limit = budget_limit
        self.records: list[TokenCost] = []
        self._total_cost: float = 0.0

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> TokenCost:
        costs = MODEL_COSTS_PER_1K_TOKENS.get(model, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total = round(input_cost + output_cost, 6)

        record = TokenCost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=round(input_cost, 6),
            output_cost=round(output_cost, 6),
            total_cost=total,
        )

        self.records.append(record)
        self._total_cost += total
        return record

    def get_total_cost(self) -> float:
        return round(self._total_cost, 6)

    def get_cost_by_model(self) -> dict[str, float]:
        by_model: dict[str, float] = {}
        for record in self.records:
            by_model[record.model] = by_model.get(record.model, 0.0) + record.total_cost
        return {k: round(v, 6) for k, v in by_model.items()}

    def get_total_tokens(self) -> dict[str, int]:
        input_total = sum(r.input_tokens for r in self.records)
        output_total = sum(r.output_tokens for r in self.records)
        return {"input": input_total, "output": output_total, "total": input_total + output_total}

    def is_over_budget(self) -> bool:
        if self.budget_limit is None:
            return False
        return self._total_cost > self.budget_limit

    def get_remaining_budget(self) -> float | None:
        if self.budget_limit is None:
            return None
        return round(self.budget_limit - self._total_cost, 6)

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_cost": self.get_total_cost(),
            "total_tokens": self.get_total_tokens(),
            "cost_by_model": self.get_cost_by_model(),
            "num_requests": len(self.records),
            "budget_limit": self.budget_limit,
            "over_budget": self.is_over_budget(),
            "remaining_budget": self.get_remaining_budget(),
        }

    def clear(self) -> None:
        self.records.clear()
        self._total_cost = 0.0
