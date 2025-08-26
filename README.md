# Text Digest Backend

FastAPI backend for Text Digest API, deployed on AWS Lambda using containerized deployment.

## Core Dependencies

-   **FastAPI** - API framework
-   **Uvicorn** - Run Fast API locally
-   **Mangum** - Converts Fast API endpoints into lambda functions for hosting

## Prerequisites

Install the following:

-   **Python 3.13**
-   **Docker**
-   **AWS CLI**
-   **Terraform**

## Local Development

### 1. Create virtual environment

```bash
py -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r src/requirements.txt
```

### 3. Run locally

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

### 4. Test endpoints

Ping the health check route to verify everything is working:

```bash
curl http://localhost:8000/api/v1/health/
```

## Project Structure

```
root/
├── tests/
├── src/
│   ├── main.py              # API entry point (Do not modify)
│   ├── requirements.txt     # Dependencies
│   │
│   ├── services/              # Biz Logic goes here, which feeds the API
│   │   └── users/             # User service biz logic
│   │   └── reader/            # eReader service biz logic
│   │       ...ect.
│   │
│   └── api/
│       └── v1/
│           ├── api.py         # API router config
│           └── endpoints/
│               └── health.py  # Here is where we define endpoints...
│               └── users.py   # Users service endpoints
│               └── reader.py  # eReader service endpoints
│               ... ect
│
├── Dockerfile                  # AWS Deployment container
├── .github/                   # CI/CD workflows
└── terraform/                 # IaC
```

## Deployment

All deployment is automated by GitHub Actions + Terraform

## AWS Services in Use

-   **API Gateway** - API Hosting
-   **Lambda** - Compute
-   **DynamoDB** - Database
-   **Cognito** - User Authentication
-   **ECR** - Container registry

## Environment Variables

TBD
