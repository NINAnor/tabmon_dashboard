# TABMON Dashboard - Portainer Deployment Guide

## Environment Variables Required

When deploying this dashboard in Portainer, you need to upload the following `.env` file as a secret:

### .env File Contents
```bash
BASE_DATA_DIR=http://rclone:8081/data/

# Authentication credentials for dashboard
# These must match your htpasswd file credentials
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_password
```

## Portainer Deployment Steps

1. **Upload .env as Secret**:
   - Go to Portainer → Secrets
   - Create new secret named `dashboard-env`
   - Upload your `.env` file with correct credentials

2. **Update docker-compose.yml**:
   ```yaml
   services:
     dashboard:
       build:
         context: .
       env_file:
         - .env  # This will be the secret in Portainer
       secrets:
         - htpasswd
   ```

3. **Deploy Stack**:
   - Use the docker-compose.yml file
   - Ensure secrets are properly mapped

## Security Notes

- **Never commit `.env` file to repository** (it's in .gitignore)
- **Use Portainer secrets** for production deployment
- **Credentials are never hardcoded** in source code
- **Environment variables** are the only source of credentials

## Local Development

For local development, create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
# Edit .env with your local credentials
```

## Troubleshooting

If images fail to load:
1. Check environment variables: `docker exec container_name env | grep AUTH`
2. Verify credentials match htpasswd file
3. Test API access: curl with credentials
