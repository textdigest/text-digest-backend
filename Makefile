.PHONY: help
help:
	@echo "Commands:"
	@echo "  dev    - Build and run API in Docker container (use this every time)"

.PHONY: dev
dev:
	@echo "Building and starting server at http://localhost:8000..."
	@test -d venv || python3 -m venv venv
	./venv/bin/pip install -e .
	docker build -t text-digest-backend .
	docker run --rm -p 8000:8000 -v $(PWD)/src:/var/task/src -v ~/.aws:/root/.aws:ro --env-file .env -e PYTHONPATH=/var/task/src --entrypoint python text-digest-backend -m uvicorn main:app --reload --host 0.0.0.0 --port 8000