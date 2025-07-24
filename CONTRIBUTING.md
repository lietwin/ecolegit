# Contributing to EcoLogits Webhook Service

Thank you for your interest in contributing to the EcoLogits Webhook Service! This document outlines our development practices and guidelines.

## Development Philosophy

We follow pragmatic development principles focused on **shipping working software quickly while maintaining high quality**:

- **YAGNI (You Aren't Gonna Need It)**: Build only what's needed for current requirements
- **TDD First**: Write tests before implementation 
- **Simple Architecture**: Avoid premature abstraction
- **Clean Code**: Readable, testable, maintainable

## Getting Started

### Prerequisites

- Python 3.11+
- pip or poetry
- Git
- GitHub CLI (recommended)

### Setup

1. **Fork and Clone**
   ```bash
   gh repo fork lietwin/ecolegit --clone
   cd ecolegit
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **Run Tests**
   ```bash
   pytest tests/test_simple.py -v
   ```

4. **Start Development Server**
   ```bash
   python main.py
   ```

## Project Structure

```
src/
├── api/           # FastAPI routes, middleware, dependencies
├── domain/        # Business logic (no external dependencies)
├── infrastructure/# External integrations (EcoLogits, security)
└── config/        # Configuration and constants
```

### Architecture Rules

- **Domain**: Pure business logic, no external dependencies
- **Infrastructure**: Adapters for external systems
- **API**: HTTP concerns only (routing, serialization, validation)
- **Dependencies Flow**: API → Domain ← Infrastructure

## Development Workflow

### 1. Issue-First Development

```bash
# Create issue for every feature/bug
gh issue create --title "Add rate limiting validation" 
gh issue assign @me

# Create branch from issue
git checkout -b feat/add-rate-limiting
```

### 2. Test-Driven Development (MANDATORY)

```python
# 1. Write failing test FIRST (RED)
def test_calculate_endpoint_validates_tokens():
    response = client.post("/calculate", json={
        "model": "gpt-4o",
        "input_tokens": -1,  # Invalid
        "output_tokens": 500
    })
    assert response.status_code == 422

# 2. Write minimal code to pass (GREEN)
@app.post("/calculate")
def calculate(request: CalculationRequest):
    if request.input_tokens < 0:
        raise HTTPException(status_code=422, detail="Invalid tokens")
    # ... rest of implementation

# 3. Refactor only when you have 3+ similar implementations
```

### 3. Pull Request Process

```bash
# Before PR - ensure quality
pytest tests/ --tb=short
python -c "from src.application import create_app; create_app()"

# Create PR
gh pr create --title "feat: add token validation" --body "
## Summary
- Adds validation for negative token counts
- Returns 422 for invalid requests
- Includes comprehensive test coverage

## Test Plan  
- [x] Unit tests for validation logic
- [x] Integration test for endpoint
- [x] Error scenarios tested

Closes #123
"

# After review
gh pr merge --squash --delete-branch
```

## Code Quality Standards

### Complexity Limits (HARD LIMITS)

- Total service: <800 lines
- Each layer: <300 lines  
- Each class: <100 lines
- Each method: <25 lines

### Testing Requirements

- Write integration tests first (end-to-end workflows)
- Maintain >80% test coverage for new code
- All tests must pass before PR approval
- Test error scenarios, not just happy paths

### Code Style

```python
# ✅ Good: Simple, direct
def calculate_impact(model: str, tokens: int) -> float:
    provider = detect_provider(model)
    return llm_impacts(provider, model, tokens, 1.0).energy.value.mean

# ❌ Avoid: Over-abstraction
class ModelImpactCalculationStrategy(ABC):
    @abstractmethod
    def calculate(self, context: CalculationContext) -> ImpactResult: ...
```

## Decision Framework

### When to Add Abstraction

**ONLY** add abstraction when you have:
1. 3+ similar implementations (Rule of Three)
2. Concrete requirement for multiple implementations
3. External library that might change (adapter pattern)

### Library vs Custom Implementation

```
DECISION TREE:
1. External library can do it → Use the library
2. Framework provides it → Use the framework feature  
3. Simple function works → Don't create a class
4. Single use case → Don't create an interface
```

## Anti-Patterns to Avoid

### Forbidden Patterns

- ❌ Repository pattern for simple library wrappers
- ❌ Factory classes with only static methods
- ❌ Abstract base classes with single implementation
- ❌ Global state (module-level variables)
- ❌ God classes (>100 lines)
- ❌ Boolean parameters (use enums)

### Use Instead

- ✅ Direct library usage with adapter if needed
- ✅ Factory functions (not classes)
- ✅ Concrete classes until you need polymorphism
- ✅ Dependency injection container
- ✅ Single-responsibility classes
- ✅ Explicit enum types

## Commit Message Standards

```
TYPE: Short description (50 chars max)

TYPES: feat, fix, docs, style, refactor, test, chore

EXAMPLES:
feat: add environmental impact calculation endpoint
fix: handle missing model in EcoLogits adapter  
test: add integration tests for calculation workflow
```

## Pre-Commit Checklist

- [ ] All tests pass locally
- [ ] Integration test covers main workflow  
- [ ] No TODO/FIXME comments in production code
- [ ] Error scenarios tested
- [ ] No magic numbers or hardcoded values
- [ ] Logging added for important operations
- [ ] Code follows complexity limits

## Issue and PR Templates

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Send request to '/calculate'
2. With payload '...'
3. See error

**Expected behavior**
What you expected to happen.

**Environment**
- Python version:
- EcoLogits version:
- OS:
```

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature.

**Use Case**
Why is this feature needed?

**Proposed Implementation**
How should this be implemented?

**Testing Plan**
How will this be tested?
```

## Development Tips

### Debugging

```bash
# Local development with detailed logs
export ENVIRONMENT=development
python main.py

# Test specific endpoint
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "input_tokens": 1000, "output_tokens": 500}'
```

### Performance Testing

```bash
# Basic load test (install ab first)
ab -n 100 -c 10 http://localhost:8000/health
```

## Security Guidelines

- Never commit API keys or secrets
- Validate all user inputs
- Use HTTPS in production
- Enable rate limiting
- Log security events (but not sensitive data)

## Getting Help

- **Documentation**: Check README.md and API docs at `/docs`
- **Issues**: Search existing issues first
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Ask for review early and often

## Recognition

Contributors will be recognized in our README.md and release notes. Thank you for helping improve the EcoLogits Webhook Service!

---

**Remember**: Perfect is the enemy of good. Ship working software, then improve.