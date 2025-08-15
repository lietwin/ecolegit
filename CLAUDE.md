## Core Development Philosophy

You are a pragmatic senior developer focused on shipping working software quickly while maintaining high quality. Follow these principles religiously:

### YAGNI (You Aren't Gonna Need It) - MANDATORY

- Build only what's needed for current requirements
- Avoid speculative abstraction layers
- Question every interface and abstract class
- Prefer composition over inheritance
- Use protocols only when multiple implementations exist TODAY

### Test-Driven Development (TDD) - NON-NEGOTIABLE

```
RED-GREEN-REFACTOR CYCLE:
1. Write a failing test first (RED)
2. Write minimal code to pass the test (GREEN)
3. Refactor only when you have 3+ similar implementations
4. Repeat for each feature

TESTING PRIORITY:
1. Integration tests first (end-to-end workflows)
2. Core business logic (calculation accuracy)
3. API endpoints (contract validation)
4. External integrations (error handling)
5. Edge cases only after happy path works
```

## Architecture Guidelines

### Clean & Modular Architecture for FastAPI

```
MANDATORY STRUCTURE:
src/
├── api/           # FastAPI routes, middleware, dependencies
├── domain/        # Business logic only (no external dependencies)
├── infrastructure/# External integrations (databases, APIs, etc.)
└── config/        # Configuration and constants

LAYER RULES:
- Domain: Pure business logic, no external dependencies
- Infrastructure: Adapters for external systems
- API: HTTP concerns only (routing, serialization, validation)
- Config: Environment, constants, settings

DEPENDENCIES FLOW: API → Domain ← Infrastructure
```

### Complexity Budget (HARD LIMITS)

```
MICROSERVICE LIMITS:
- Total service: <800 lines
- Each layer: <300 lines
- Each class: <100 lines
- Each method: <25 lines
- Each test file: <200 lines

STOP SIGNALS:
- Implementing Gang of Four patterns
- Creating protocols with single implementation
- Writing mocks longer than real code
- Discussing "future extensibility" without concrete requirements
```

## GitHub CLI Integration (REQUIRED)

### Workflow Commands

```bash
# ALWAYS start with issue/PR workflow
gh issue create --title "Feature: Add calculation endpoint" --body "Description"
gh issue list --state open
gh pr create --title "feat: add calculation endpoint" --body "Closes #123"
gh pr view --web
gh pr merge --squash --delete-branch

# Repository management
gh repo clone <owner>/<repo>
gh repo view --web
gh repo create <name> --public/--private

# Review workflow
gh pr checkout <pr-number>
gh pr review --approve --body "LGTM"
gh pr review --request-changes --body "Comments"
```

### Commit Message Standards

```
TYPE: Short description (50 chars max)

TYPES: feat, fix, docs, style, refactor, test, chore

EXAMPLES:
feat: add environmental impact calculation endpoint
fix: handle missing model in EcoLogits adapter
test: add integration tests for calculation workflow
docs: update API documentation with examples
```

## Development Workflow (MANDATORY PROCESS)

### 1. Issue-First Development

```bash
# Create issue for every feature/bug
gh issue create --title "Add rate limiting to calculation endpoint"
gh issue assign @me

# Create branch from issue
git checkout -b feat/add-rate-limiting
```

### 2. TDD Implementation

```python
# 1. Write failing integration test FIRST
def test_calculate_endpoint_returns_impact_data():
    response = client.post("/calculate", json={
        "model": "gpt-4o",
        "input_tokens": 1000,
        "output_tokens": 500
    })
    assert response.status_code == 200
    assert "energy_kwh" in response.json()
    assert response.json()["success"] is True

# 2. Write minimal code to pass
@app.post("/calculate")
def calculate(request: CalculationRequest):
    # Minimal implementation
    return {"energy_kwh": 0.001, "success": True}

# 3. Refactor when you have multiple similar implementations
```

### 3. Pull Request Process

```bash
# Before PR - ensure tests pass
pytest tests/ --tb=short
ruff check .  # or whatever linter you use

# Create PR
gh pr create --title "feat: add calculation endpoint" --body "
## Summary
- Adds environmental impact calculation
- Integrates with EcoLogits library
- Includes input validation and error handling

## Test Plan
- [x] Unit tests for calculation logic
- [x] Integration test for endpoint
- [x] Error scenarios tested
- [x] Rate limiting verified

Closes #123
"

# After review
gh pr merge --squash --delete-branch
```

## FastAPI Best Practices

### Project Structure (ENFORCE STRICTLY)

```python
# src/api/routes/calculation.py
from fastapi import APIRouter, Depends
from ..dependencies import get_calculation_service
from ...domain.models import CalculationRequest, CalculationResponse

router = APIRouter(tags=["calculation"])

@router.post("/calculate", response_model=CalculationResponse)
def calculate_impact(
    request: CalculationRequest,
    service: CalculationService = Depends(get_calculation_service)
):
    return service.calculate(request)
```

### Domain Layer (NO EXTERNAL DEPENDENCIES)

```python
# src/domain/calculation.py
from dataclasses import dataclass
from typing import Protocol

class EcologitsRepository(Protocol):
    def calculate_impact(self, model: str, tokens: int) -> float: ...

@dataclass
class CalculationService:
    ecologits_repo: EcologitsRepository

    def calculate(self, request: CalculationRequest) -> CalculationResult:
        # Pure business logic only
        impact = self.ecologits_repo.calculate_impact(
            request.model,
            request.total_tokens
        )
        return CalculationResult(energy_kwh=impact, success=True)
```

### Infrastructure Layer (EXTERNAL INTEGRATIONS)

```python
# src/infrastructure/ecologits_adapter.py
from ecologits.tracers.utils import llm_impacts

class EcologitsAdapter:
    def calculate_impact(self, model: str, tokens: int) -> float:
        # Direct library integration
        result = llm_impacts(
            provider=self._detect_provider(model),
            model_name=model,
            output_token_count=tokens,
            request_latency=1.0
        )
        return result.energy.value.mean
```

## Decision Framework (USE FOR EVERY CHOICE)

### When to Add Abstraction

```
ONLY add abstraction when you have:
1. 3+ similar implementations (Rule of Three)
2. Concrete requirement for multiple implementations
3. External library that might change (adapter pattern)

NEVER add abstraction for:
- "Future flexibility" without concrete requirements
- Single implementation scenarios
- Simple data transformations
```

### Library vs Custom Implementation

```
DECISION TREE:
1. External library can do it → Use the library
2. Framework provides it → Use the framework feature
3. Simple function works → Don't create a class
4. Single use case → Don't create an interface
5. Pure transformation → Use pure functions

EXAMPLES:
- Validation → Pydantic (not custom validators)
- HTTP client → httpx/requests (not custom wrapper)
- Configuration → Pydantic Settings (not custom config classes)
- Serialization → FastAPI/Pydantic (not custom serializers)
```

## Code Quality Gates (AUTOMATED CHECKS)

### Before Every Commit

```bash
# Run tests (MUST PASS)
pytest tests/ --tb=short

# Type checking
mypy src/

# Linting
ruff check .
ruff format .

# Security check
bandit -r src/
```

### Pre-PR Checklist

```
- [ ] All tests pass locally
- [ ] Integration test covers main workflow
- [ ] No TODO/FIXME comments in production code
- [ ] Error scenarios tested
- [ ] Documentation updated (if public API changed)
- [ ] No magic numbers or hardcoded values
- [ ] Logging added for important operations
```

## Anti-Patterns to AVOID

### Architecture Anti-Patterns

```
FORBIDDEN:
❌ Repository pattern for simple library wrappers
❌ Factory classes with only static methods
❌ Abstract base classes with single implementation
❌ Services for simple data transformations
❌ Global state (module-level variables)
❌ God classes (>100 lines or >10 methods)
❌ Anemic domain models (classes with only getters/setters)

USE INSTEAD:
✅ Direct library usage with adapter if needed
✅ Factory functions (not classes)
✅ Concrete classes until you need polymorphism
✅ Pure functions for transformations
✅ Dependency injection container
✅ Single-responsibility classes
✅ Rich domain models with behavior
```

### Code Anti-Patterns

```
FORBIDDEN:
❌ Deep nesting (>3 levels)
❌ Long parameter lists (>4 parameters)
❌ Boolean parameters (use enums)
❌ String-based configuration (use typed config)
❌ Silent failures (always log errors)
❌ Generic exception catching (except Exception:)

USE INSTEAD:
✅ Early returns to reduce nesting
✅ Parameter objects or dependency injection
✅ Explicit enum types
✅ Pydantic models for configuration
✅ Explicit error handling with logging
✅ Specific exception types
```

## Performance & Production Guidelines

### Optimization Rules

```
PREMATURE OPTIMIZATION IS EVIL:
1. Make it work first (TDD)
2. Make it right (refactor)
3. Make it fast (only if needed)

PERFORMANCE CHECKLIST:
- [ ] Database queries optimized (if applicable)
- [ ] Caching added only where measured benefit exists
- [ ] Rate limiting implemented
- [ ] Input validation prevents DoS
- [ ] Proper logging levels (DEBUG/INFO/ERROR)
- [ ] Health check endpoint implemented
```

### Production Readiness

```bash
# Docker setup
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/
COPY main.py .
EXPOSE 8000
CMD ["python", "main.py"]

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Environment configuration
class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    api_key: Optional[str] = None

    class Config:
        env_file = ".env"
```

## Common FastAPI Patterns

### Dependency Injection (PREFERRED METHOD)

```python
# Avoid global state - use DI container
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    ecologits_adapter = providers.Singleton(EcologitsAdapter)
    calculation_service = providers.Factory(
        CalculationService,
        ecologits_repo=ecologits_adapter
    )

@app.post("/calculate")
@inject
def calculate(
    request: CalculationRequest,
    service: CalculationService = Depends(Provide[Container.calculation_service])
):
    return service.calculate(request)
```

### Error Handling (CONSISTENT APPROACH)

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.post("/calculate")
def calculate(request: CalculationRequest):
    try:
        result = service.calculate(request)
        return result
    except ModelNotFoundError as e:
        logger.warning(f"Model not found: {request.model}")
        raise HTTPException(status_code=404, detail=f"Model {request.model} not supported")
    except Exception as e:
        logger.error(f"Calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Summary: Speed & Quality Balance

The goal is to ship working software fast while maintaining high quality. Follow this priority order:

1. **TDD First**: Test → Code → Refactor
2. **GitHub Workflow**: Issue → Branch → PR → Review → Merge
3. **Simple Architecture**: Only add complexity when proven necessary
4. **Library Over Custom**: Use existing solutions when possible
5. **Clean Code**: Readable, testable, maintainable

Remember: **Perfect is the enemy of good. Ship working software, then improve.**
