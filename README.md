# BDI Aircraft API

Big Data Infrastructure Aircraft API project for processing and analyzing aircraft data.

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

## Project Structure

```
bdi-aircraft-api/
├── bdi_api/            # Main package directory
│   ├── __init__.py
│   ├── main.py        # FastAPI application
│   ├── settings.py    # Project settings
│   └── s1/           # S1 exercise module
│       ├── __init__.py
│       └── exercise.py
├── data/              # Data directory
│   ├── raw/          # Raw downloaded data
│   └── prepared/     # Processed data
└── tests/            # Test directory
    └── s1/          # Tests for S1 module
```
