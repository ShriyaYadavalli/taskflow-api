# TaskFlow API

A REST API for managing projects and tasks, built with **Python, FastAPI, SQLAlchemy, SQLite, and Docker**.

## Features

- Create, retrieve, update, and delete tasks (CRUD).
- Create projects and associate tasks with projects.
- Filter tasks by status and priority.
- Paginate task results using `limit` and `offset`.
- Validate request data using Pydantic.
- Handle missing resources with appropriate HTTP status codes.
- Persist data using SQLite.
- Run the application in Docker with Docker Compose.
- Automated API tests using pytest and FastAPI's TestClient.

## Tech Stack

- **Language:** Python
- **API framework:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Testing:** pytest
- **Containerization:** Docker and Docker Compose

## Run with Docker Hub

You can run TaskFlow API using the prebuilt Docker image from Docker Hub without cloning the repository or building the image yourself.

### 1. Pull the image

```bash
docker pull shriyayadavalli/taskflow-api:1.0
```

### 2. Start the container

```bash
docker run -d \
  --name taskflow-api \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:////app/data/taskflow.db \
  -v taskflow_data:/app/data \
  shriyayadavalli/taskflow-api:1.0
```

### 3. Access the API

Once the container is running, open:

- **Interactive API documentation:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

### 4. Manage the container

Stop the container:

```bash
docker stop taskflow-api
```

Start it again:

```bash
docker start taskflow-api
```

Remove the container:

```bash
docker rm -f taskflow-api
```

**Notes:**
- Docker must be installed and running.
- The Docker Hub repository must be public for anyone to pull the image without signing in.
- Each user gets a separate SQLite database in their own Docker volume. Your local database records are not included in the image.
- The database persists when the container is stopped or removed, unless the named volume is deleted.


## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/ShriyaYadavalli/taskflow-api.git
cd taskflow-api
```

### 2. Create and activate a virtual environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the API

```bash
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

## Run with Docker

Make sure Docker Desktop is running, then execute:

```bash
docker compose up --build
```

The API will be available at:

http://localhost:8000/docs

To stop the containers:

```bash
docker compose down
```

The SQLite database used by Docker is stored in a named Docker volume so that data can persist when containers are stopped and recreated. The local database and Docker database are separate.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| POST | `/tasks` | Create a task |
| GET | `/tasks` | List tasks with optional filters and pagination |
| GET | `/tasks/{task_id}` | Retrieve a task |
| PATCH | `/tasks/{task_id}` | Partially update a task |
| DELETE | `/tasks/{task_id}` | Delete a task |
| POST | `/projects` | Create a project |
| GET | `/projects` | List projects |
| GET | `/projects/{project_id}/tasks` | List tasks associated with a project |

### Example: Create a task

Send a `POST` request to `/tasks` with this JSON body:

```json
{
  "title": "Build TaskFlow API",
  "description": "Complete the backend project",
  "status": "in_progress",
  "priority": "high"
}
```

### Example: Filter and paginate tasks

```text
GET /tasks?status=pending&priority=high&limit=10&offset=0
```

### Example: Update a task

Send a `PATCH` request to `/tasks/1`:

```json
{
  "status": "completed"
}
```

### Example: Create a project

Send a `POST` request to `/projects`:

```json
{
  "name": "Portfolio Projects",
  "description": "Projects built for my software engineering portfolio"
}
```

## Run Tests

With your virtual environment activated:

```bash
python -m pytest -v
```

The test suite covers task creation, validation, filtering, pagination, project relationships, and missing-task responses.

## Project Structure

```text
taskflow-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── schemas.py
├── tests/
│   └── test_tasks.py
├── .dockerignore
├── .gitignore
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

## What I Learned

- Designing RESTful API endpoints with FastAPI.
- Defining database models and relationships with SQLAlchemy.
- Validating API inputs and handling errors.
- Implementing filtering and pagination.
- Writing automated tests for API behavior.
- Containerizing an application with Docker.
- Persisting SQLite data with Docker volumes.

## Future Improvements

- Add user authentication and authorization.
- Add database migrations with Alembic.
- Add more integration tests.
- Deploy the API to a cloud platform.
