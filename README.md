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

### 1. Run locally

-   Ensure make is installed on your machine.
-   Use the following command:

```bash
make dev
```

-   The API will be available at `http://localhost:8000`

### 2. Select Interpreter

-   `Cmd+Shift+P` > "Python: Select Interpreter" > `./venv/bin/python`.

### 3. Ping Health to Verify

-   Ping the health check route to verify everything is working:

```bash
curl http://localhost:8000/api/v1/health/
```

## Adding Dependecies

-   Any external python dependencies must be added to pyproject.toml

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
│
└── terraform/                      # IaC
    ├── main.tf                     # Entry point - orchestrates everything
    ├── provider.tf                 # AWS provider configuration
    ├── variables.tf                # Input variables (customizable settings)
    ├── outputs.tf                  # Output values (URLs, IDs, etc.)
    └── resources/
        └── [aws_service_name].tf   # Individual service configurations
```

## AWS Services in Use

-   **API Gateway** - API Hosting
-   **Lambda** - Compute
-   **S3** - BLOB Store
-   **DynamoDB** - Database
-   **Cognito** - User Authentication
-   **ECR** - Container registry
