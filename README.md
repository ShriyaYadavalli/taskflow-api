# TaskFlow API

A RESTful API for managing projects and tasks, built with **Python, FastAPI, SQLAlchemy, SQLite, and Docker**. This project demonstrates backend development fundamentals, database relationships, request validation, automated testing, and containerization.

## Project Links

- **Source Code:** [GitHub Repository](https://github.com/ShriyaYadavalli/taskflow-api)
- **Docker Image:** [Docker Hub](https://hub.docker.com/r/shriyayadavalli/taskflow-api)
- **Interactive API Documentation:** `http://localhost:8000/docs` after starting the application.

## Features

- Create, retrieve, update, and delete tasks (CRUD).
- Create projects and associate tasks with projects.
- Filter tasks by status and priority.
- Paginate task results using `limit` and `offset`.
- Validate request data using Pydantic.
- Handle missing resources with appropriate HTTP status codes.
- Persist data using SQLite.
- Run the application in Docker with Docker Compose.
- Store database data in a persistent Docker volume.
- Run automated API tests using pytest and FastAPI's TestClient.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application programming language |
| FastAPI | REST API framework |
| SQLAlchemy | ORM and database interactions |
| SQLite | Relational database |
| Pydantic | Request validation and data schemas |
| pytest | Automated testing |
| Docker | Application containerization |
| Docker Compose | Container configuration and execution |

## Getting Started

Choose one of the following options to run the application.

### Option 1: Run with Docker Hub

Use the prebuilt Docker image to run TaskFlow API without cloning the repository or building the image yourself.

**Prerequisites:** Docker installed and running.

#### 1. Pull the image

```bash
docker pull shriyayadavalli/taskflow-api:1.0
```

#### 2. Start the container

```bash
docker run -d \
  --name taskflow-api \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:////app/data/taskflow.db \
  -v taskflow_data:/app/data \
  shriyayadavalli/taskflow-api:1.0
```

#### 3. Access the API

Once the container is running, open:

- **Interactive API documentation:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

#### 4. Manage the container

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

- The Docker Hub repository must be public for users to pull the image without signing in.
- Each user gets a separate database in their own Docker volume. Your local database records are not included in the image.
- Database data persists when the container is stopped or removed, provided the named volume is not deleted.
- If port `8000` is already in use, replace `-p 8000:8000` with `-p 8001:8000` and access the API at `http://localhost:8001/docs`.

### Option 2: Run with Docker Compose

Use Docker Compose to build and run the application from the source code.

**Prerequisites:** Docker Desktop installed and running.

#### 1. Clone the repository

```bash
git clone https://github.com/ShriyaYadavalli/taskflow-api.git
cd taskflow-api
```

#### 2. Build and start the application

```bash
docker compose up --build
```

#### 3. Access the API

- **Interactive API documentation:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

#### 4. Stop the application

```bash
docker compose down
```

Docker Compose stores the database in a named volume, allowing data to persist when containers are stopped and recreated. The local database and Docker database are separate.

To remove the containers and the database volume, run:

```bash
docker compose down -v
```

**Warning:** The `-v` option deletes the Compose-managed database volume and its stored data.

### Option 3: Run Locally with Python

Run the application directly on your computer without Docker.

**Prerequisites:** Python installed.

#### 1. Clone the repository

```bash
git clone https://github.com/ShriyaYadavalli/taskflow-api.git
cd taskflow-api
```

#### 2. Create and activate a virtual environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

#### 4. Start the API

```bash
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

The local application uses `taskflow.db` in the working directory by default.

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

### Supported Task Values

| Field | Accepted values |
|---|---|
| `status` | `pending`, `in_progress`, `completed` |
| `priority` | `low`, `medium`, `high` |

### Example: Create a Task

Send a `POST` request to `/tasks` with this JSON body:

```json
{
  "title": "Build TaskFlow API",
  "description": "Complete the backend project",
  "status": "in_progress",
  "priority": "high"
}
```

### Example: Filter and Paginate Tasks

Retrieve pending, high-priority tasks, returning up to 10 results:

```http
GET /tasks?status=pending&priority=high&limit=10&offset=0
```

- `status` filters tasks by status.
- `priority` filters tasks by priority.
- `limit` controls the maximum number of results.
- `offset` specifies how many results to skip.

All filters and pagination parameters are optional.

### Example: Update a Task

Send a `PATCH` request to `/tasks/1` with only the fields you want to change:

```json
{
  "status": "completed"
}
```

### Example: Create a Project

Send a `POST` request to `/projects`:

```json
{
  "name": "Portfolio Projects",
  "description": "Projects built for my software engineering portfolio"
}
```

A task can optionally reference a project through its `project_id`.

## Run Tests

Activate your virtual environment if you're running locally, then execute:

```bash
python -m pytest -v
```

The test suite covers:

- Task creation and retrieval.
- Request validation.
- Filtering and pagination.
- Project creation and task relationships.
- Responses for missing tasks.

Tests use a separate temporary SQLite database to avoid modifying the application's normal database.

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

| File | Responsibility |
|---|---|
| `main.py` | API routes and request handling |
| `database.py` | Database engine, sessions, and dependencies |
| `models.py` | SQLAlchemy database models and relationships |
| `schemas.py` | Pydantic schemas and request validation |
| `test_tasks.py` | Automated API tests |
| `Dockerfile` | Instructions for building the Docker image |
| `compose.yaml` | Docker service, environment, and volume configuration |
| `requirements.txt` | Python dependencies |

## What I Learned

- Designing RESTful API endpoints with FastAPI.
- Modeling relational data and relationships with SQLAlchemy.
- Validating requests with Pydantic.
- Implementing filtering and pagination with SQLAlchemy queries.
- Handling errors and HTTP status codes.
- Writing automated tests with pytest and FastAPI's TestClient.
- Managing configuration through environment variables.
- Containerizing an application with Docker and Docker Compose.
- Persisting database data using Docker volumes.
- Managing source code with Git and GitHub.

## Future Improvements

- Add user authentication and authorization.
- Introduce database migrations with Alembic.
- Expand integration and edge-case testing.
- Deploy the API to a cloud platform.
- Add continuous integration to run tests automatically.

---

**Built as a backend development portfolio project to practice API design, relational databases, testing, and containerization.**
