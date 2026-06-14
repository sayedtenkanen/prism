---
name: pydantic
description: Pydantic v2 model design, validation, and settings patterns. Use when user mentions "pydantic", "model", "schema", "validation", "settings". Triggers on Pydantic questions.
---

# Pydantic v2 Conventions

## Model Design

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    field: str = "default"
    optional_field: str | None = None
    list_field: list[str] = Field(default_factory=list)
```

## Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str = ""
    model_config = {"env_prefix": "MY_APP_"}
```

## Serialization

```python
# GOOD
data = model.model_dump()
model = MyModel.model_validate(data)

# BAD (Pydantic v1)
data = model.dict()
model = MyModel.parse_obj(data)
```

## Field Types

```python
# Required
name: str

# Optional with default
timeout: float | None = None

# List with factory
items: list[str] = Field(default_factory=list)

# Nested model
config: AppConfig = Field(default_factory=AppConfig)

# Literal for enums
provider: Literal["github", "bitbucket"] = "github"
```

## Validation

```python
from pydantic import field_validator

class MyModel(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Name must be at least 3 characters")
        return v
```

## Checklist

Before writing Pydantic models:

```bash
mypy app/
```
