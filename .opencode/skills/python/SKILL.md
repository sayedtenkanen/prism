---
name: python
description: Python 3.12 conventions and patterns for Prism. Use when writing Python code, mentions "python", "type hints", "async", "pydantic", "dataclass". Triggers on Python-specific questions.
---

# Python Conventions

## Runtime

- Python 3.12+ (required by DSPy)
- Use native types: `list`, `dict`, `set`, `tuple` (NOT `typing.List`)
- Use `Optional[X]` from typing (since `X | None` requires 3.10+)

## Type Hints

```python
# GOOD
def process(items: list[str]) -> dict[str, int]:
    ...

def fetch(url: str, timeout: float | None = None) -> bytes:
    ...

# BAD
from typing import List, Dict
def process(items: List[str]) -> Dict[str, int]:
    ...
```

## Async Patterns

```python
# All graph nodes are async
async def review_node(state: PRReviewState) -> dict[str, Any]:
    ...

# Use asyncio.to_thread for sync code
async def run_sync_function():
    result = await asyncio.to_thread(sync_function, arg1, arg2)

# Never block in async context
async def bad_example():
    time.sleep(1)  # WRONG
    await asyncio.sleep(1)  # RIGHT
```

## Pydantic v2

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    field: str = "default"
    optional_field: str | None = None
    list_field: list[str] = Field(default_factory=list)

# Use model_dump() not .dict()
data = model.model_dump()

# Use model_validate() not .parse_obj()
model = MyModel.model_validate(data)
```

## String Formatting

```python
# GOOD - f-strings
name = f"hello {world}"

# GOOD - format()
name = "hello {}".format(world)

# BAD - % formatting
name = "hello %s" % world
```

## Error Handling

```python
# Be specific about exceptions
try:
    result = risky_operation()
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    raise

# Don't catch bare Exception
except Exception:  # BAD
    pass

# Use custom exceptions for domain errors
class ReviewError(Exception):
    pass
```

## File Handling

```python
# Always specify encoding
with open(path, encoding="utf-8") as f:
    data = json.load(f)

# Use Path for file operations
from pathlib import Path
path = Path("data/file.json")
path.parent.mkdir(parents=True, exist_ok=True)
```

## Imports

```python
# Standard library first, then third-party, then local
import json
import time
from pathlib import Path

import dspy
from pydantic import BaseModel

from app.core.config import settings
from app.sia.memory import MemoryStore
```

## Prism Checklist

Before writing Python code:

```bash
ruff check . && ruff format --check . && mypy app/
```
