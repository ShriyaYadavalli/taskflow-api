
# TaskFlow API

A task management REST API built with Python and FastAPI.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Uvicorn

## Current Features

- Welcome endpoint
- Health check endpoint
- Interactive API documentation

## Run Locally

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start the development server:

```bash
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to explore the API.
