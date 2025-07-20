# EcoLogits Webhook Service

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-brightgreen.svg)](https://github.com/psf/black)

A production-ready FastAPI service for calculating environmental impact of AI model usage, designed with clean architecture principles and SOLID design patterns.

## 🌱 **Features**

- **Environmental Impact Calculation**: Calculate energy consumption and carbon footprint for AI models
- **Webhook Integration**: Seamless integration with Make.com and other webhook services
- **Security**: API key authentication and HMAC webhook signature verification
- **Rate Limiting**: Configurable request rate limiting
- **Clean Architecture**: SOLID principles with dependency injection
- **Comprehensive Testing**: 99% test coverage
- **Production Ready**: Structured logging, error handling, and monitoring

## 🏗️ **Architecture**

```
src/
├── config/          # Configuration management
├── domain/          # Business logic and models
├── infrastructure/  # External services and security
├── api/            # FastAPI routes and middleware
└── application.py   # Application factory
```

## 🚀 **Quick Start**

### Prerequisites

- Python 3.11+
- pip or poetry

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ecolegit
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt  # For development
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Supported Models: http://localhost:8000/models

## ⚙️ **Configuration**

The service uses a `config.json` file that's automatically created with defaults:

```json
{
  "model_mappings": {
    "gpt-4o": "gpt-4o-2024-05-13",
    "claude-3-opus": "claude-3-opus-20240229"
  },
  "security": {
    "enable_auth": false,
    "enable_webhook_signature": false,
    "max_tokens_per_request": 1000000,
    "trusted_hosts": ["*"]
  },
  "rate_limiting": {
    "requests_per_minute": 60,
    "enabled": true
  }
}
```

### Environment Variables

- `API_KEY`: API key for authentication (when enabled)
- `WEBHOOK_SECRET`: Secret for webhook signature verification
- `ENVIRONMENT`: `development`, `testing`, or `production`
- `PORT`: Server port (default: 8000)

## 📡 **API Endpoints**

### Calculate Environmental Impact

**POST** `/calculate`

Calculate the environmental impact of AI model usage.

```json
{
  "model": "gpt-4o",
  "input_tokens": 1000,
  "output_tokens": 500,
  "metadata": {
    "user_id": "user123",
    "session": "abc"
  }
}
```

**Response:**
```json
{
  "model": "gpt-4o",
  "input_tokens": 1000,
  "output_tokens": 500,
  "total_tokens": 1500,
  "energy_kwh": 0.001234,
  "gwp_kgco2eq": 0.000567,
  "calculation_id": "calc-abc123",
  "timestamp": "2024-01-01T12:00:00Z",
  "success": true,
  "error": null
}
```

### Health Check

**GET** `/health`

Check service health status.

### Supported Models

**GET** `/models`

Get list of supported AI models.

## 🔐 **Security**

### API Key Authentication

Enable in config:
```json
{
  "security": {
    "enable_auth": true
  }
}
```

Set environment variable:
```bash
export API_KEY="your-secret-api-key"
```

### Webhook Signature Verification

Enable HMAC-SHA256 signature verification:
```json
{
  "security": {
    "enable_webhook_signature": true
  }
}
```

Set webhook secret:
```bash
export WEBHOOK_SECRET="your-webhook-secret"
```

## 🧪 **Testing**

Run the complete test suite:

```bash
# Run all tests with coverage
pytest tests/ --cov=main --cov-report=html

# Run specific test categories
pytest tests/test_domain/ -v
pytest tests/test_api/ -v

# Check test coverage
open htmlcov/index.html
```

**Current Test Coverage: 99%**

## 🚀 **Deployment**

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY main.py .

EXPOSE 8000
CMD ["python", "main.py"]
```

### Environment-specific Deployment

**Production:**
```bash
export ENVIRONMENT=production
export API_KEY="prod-api-key"
export WEBHOOK_SECRET="prod-webhook-secret"
python main.py
```

## 📈 **Monitoring**

The service includes structured logging and health endpoints for monitoring:

- **Health Check**: `/health` - Service status
- **Metrics**: Built-in request logging and error tracking
- **Configuration**: Runtime configuration validation

## 🤝 **Contributing**

We follow conventional commits and clean code practices:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feat/new-feature`
3. **Make changes following SOLID principles**
4. **Add tests** (maintain 99% coverage)
5. **Commit using conventional commits**: `feat: add new calculation method`
6. **Push and create a pull request**

### Conventional Commits Format

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/modifications
- `chore:` Maintenance tasks

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- [EcoLogits](https://github.com/genai-impact/ecologits) - Environmental impact calculation library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Make.com](https://make.com/) - Webhook integration platform

## 📞 **Support**

- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)
- **Documentation**: [API Docs](http://localhost:8000/docs)

---

**Built with ❤️ and Clean Architecture principles**