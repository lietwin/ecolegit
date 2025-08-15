# 🚀 Deployment Guide

This service is designed for easy deployment on cloud platforms. All configurations are simplified and production-ready.

## Render Deployment (Recommended)

### Quick Deploy
1. **Connect GitHub Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select your forked `ecolegit` repository

2. **Configure Service**
   ```
   Name: ecolegits-webhook
   Branch: main
   Build Command: pip install -r requirements.txt
   Start Command: python main.py
   ```

3. **Set Environment Variables**
   ```
   ENVIRONMENT=production
   PORT=8000
   API_KEY=your-secure-api-key (optional)
   WEBHOOK_SECRET=your-webhook-secret (optional)
   ```

### Using render.yaml (Recommended)
The repository includes `render.yaml` for Infrastructure as Code deployment:

1. **Fork/Clone the repository**
2. **Push to your GitHub**
3. **Import to Render**
   - Dashboard → "New +" → "Blueprint"
   - Connect repository
   - Render will automatically use `render.yaml`

### Manual Configuration

#### Basic Setup
- **Environment**: Python 3.11
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`
- **Health Check Path**: `/health`

#### Environment Variables
| Variable | Value | Required |
|----------|-------|----------|
| `ENVIRONMENT` | `production` | Yes |
| `PORT` | `8000` | No (auto-set) |
| `API_KEY` | Your secure key | Optional |
| `WEBHOOK_SECRET` | Your webhook secret | Optional |

## Docker Deployment

### Build and Run Locally
```bash
# Build image
docker build -t ecolegits-webhook .

# Run container
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e API_KEY=your-api-key \
  ecolegits-webhook
```

### Deploy to Container Registry
```bash
# Tag for registry
docker tag ecolegits-webhook your-registry/ecolegits-webhook

# Push to registry
docker push your-registry/ecolegits-webhook
```

## Other Platforms

### Heroku
1. **Create Procfile**
   ```
   web: python main.py
   ```

2. **Deploy**
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku config:set ENVIRONMENT=production
   ```

### Railway
1. **Connect GitHub repository**
2. **Set environment variables**
3. **Deploy automatically**

### Fly.io
1. **Install flyctl**
2. **Initialize**
   ```bash
   fly launch
   fly deploy
   ```

## Configuration

### Production Security
```json
{
  "security": {
    "enable_auth": true,
    "enable_webhook_signature": true,
    "trusted_hosts": ["your-domain.com"]
  },
  "rate_limiting": {
    "requests_per_minute": 100,
    "enabled": true
  }
}
```

### Environment Variables
- `API_KEY`: Set for authentication
- `WEBHOOK_SECRET`: Set for signature verification
- `ENVIRONMENT`: Always set to `production`

## Monitoring

### Health Checks
- **Endpoint**: `GET /health`
- **Expected Response**: `{"status": "healthy"}`

### Logs
Monitor application logs for:
- Request patterns
- Error rates
- Performance metrics

### Metrics
Key metrics to monitor:
- Response time
- Error rate
- Request volume
- Memory usage

## Security Checklist

- [ ] API_KEY set and secure
- [ ] WEBHOOK_SECRET configured
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Trusted hosts restricted
- [ ] Logs don't expose secrets

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure all dependencies in `requirements.txt`
   - Check Python version compatibility

2. **Port Binding Issues**
   - Use `0.0.0.0` host binding
   - Respect `PORT` environment variable

3. **Configuration Errors**
   - Check `config.json` exists or is created
   - Verify environment variables

4. **Health Check Failures**
   - Ensure `/health` endpoint responds
   - Check startup time requirements

### Debug Mode
Set `ENVIRONMENT=development` for detailed logs:
```bash
# Local debugging
export ENVIRONMENT=development
python main.py
```

## Performance Optimization

### Production Settings
- Use production ASGI server (uvicorn)
- Enable logging level: WARNING
- Configure rate limiting
- Set appropriate worker count

### Scaling
- **Horizontal**: Multiple instances
- **Vertical**: Increase memory/CPU
- **Database**: External config storage
- **Caching**: Redis for rate limiting

## Support

- **Documentation**: [API Docs](https://your-app.render.com/docs)
- **Health Check**: [Health](https://your-app.render.com/health)
- **Repository**: [GitHub](https://github.com/lietwin/ecolegit)
- **Issues**: [GitHub Issues](https://github.com/lietwin/ecolegit/issues)