# LLM Utils

A utility package for working with various LLM providers (OpenAI, Anthropic, Google GenAI).

## Features

- Multi-provider LLM interaction functions
- Image processing utilities
- Token counting and management
- Structured response parsing with schema validation
- Type-safe data structures using Pydantic and dataclasses

## Installation

```bash
uv sync --dev
```

## Usage

```python
import llm

# Simple query
response = llm.responses.query("What is the capital of France?")

# Structured response with schema
@dataclass
class Capital:
    capital: str
    country: str

response, conversation = llm.responses.chat("What is the capital of France?", schema=Capital)
```
