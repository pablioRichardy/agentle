.PHONY: release ngrok docs clear-cache evolution evolution-down

release:
	uv run release.py

ngrok:
	ngrok http --url=wrongly-delicate-trout.ngrok-free.app 8000

docs:
	@echo "Gerando documentação..."
	cd docs && make html

evolution:
	cd docker && docker compose up -d

evolution-down:
	cd docker && docker compose down

clear-cache:
	@echo "Removing Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "Removing mypy cache..."
	rm -rf .mypy_cache
