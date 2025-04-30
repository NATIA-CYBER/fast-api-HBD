# BDI Aircraft API

Big Data Infrastructure Aircraft API project.

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Run the application:
```bash
poetry run uvicorn bdi_api.main:app --reload
```

## Development

- Run tests:
```bash
poetry run pytest
```

- Check code style:
```bash
poetry run ruff check .
```
