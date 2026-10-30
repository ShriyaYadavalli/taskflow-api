# TaskFlow API

A RESTful API for managing projects and tasks, built with **Python, FastAPI, SQLAlchemy, SQLite, RabbitMQ, and Docker**.

TaskFlow demonstrates backend development fundamentals, relational database design, request validation, automated testing, containerization, asynchronous background job processing, and cloud deployment using **AWS EC2**.

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
- Process background jobs asynchronously using RabbitMQ.
- Separate API request handling from background job execution using a dedicated worker.
- Implement message acknowledgment, retry handling, and dead-letter routing.
- Deploy containerized services to an AWS EC2 instance using Docker Compose.
- Share persistent SQLite database storage between the API and worker services.

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
| RabbitMQ | Message broker for asynchronous job processing |
| Pika | Python client for communicating with RabbitMQ |
| AWS EC2 | Cloud virtual machine hosting the application |
| Amazon Linux 2023 | Operating system running on the EC2 instance |

## AWS Deployment Architecture

TaskFlow API is deployed on an **AWS EC2 instance** running Amazon Linux 2023. Docker Compose manages three separate services: the FastAPI application, RabbitMQ message broker, and background worker.

### Architecture Overview

```text
                  Developer
                      |
                      | SSH
                      v
              AWS EC2 Instance
              Amazon Linux 2023
                      |
                Docker Compose
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
        API       RabbitMQ      Worker
      FastAPI      Broker      Python
          |           ^           |
          |           |           |
          |       Job Queue       |
          +-----------------------+
                      |
                      v
               SQLite Database
                Shared Volume
```

### Docker Services

| Service | Responsibility |
|---|---|
| api | Runs the FastAPI application and handles HTTP requests |
| rabbitmq | Receives and manages messages published by the API |
| worker | Consumes queued messages and processes background jobs |

The API and worker share a persistent Docker volume containing the SQLite database. This allows both services to access the same task records.

### RabbitMQ Queues

TaskFlow uses three queues to manage background job processing:

| Queue | Purpose |
|---|---|
| `taskflow-jobs` | Main queue containing jobs waiting to be processed |
| `taskflow-jobs-retry` | Temporarily holds jobs scheduled for another processing attempt |
| `taskflow-jobs-dead` | Stores jobs that cannot be processed successfully |

### Background Job Processing

When a client submits a job through `POST /jobs`:

1. The API validates the request and creates a JSON message.
2. The API publishes the message to the `taskflow-jobs` queue.
3. RabbitMQ stores the message until a worker is available.
4. The worker consumes the message and processes the requested task.
5. The worker updates the task status in the shared SQLite database.
6. After successful processing, the worker acknowledges the message.

Task statuses follow this workflow:

```text
pending
   |
   v
in_progress
   |
   v
completed
```

### Error Handling and Message Retries

TaskFlow implements different handling strategies for permanent and temporary failures.

- **Successful processing:** The worker acknowledges the message.
- **Permanent failure:** The message is rejected without requeueing and routed to the dead-letter queue.
- **Temporary failure:** The message is published to the retry queue with an incremented retry counter.
- **Retry delay:** The retry queue uses a 5-second message expiration before routing the message back to the main queue.
- **Maximum retries:** The worker allows up to three retry attempts before routing an unsuccessful job to the dead-letter queue.

### Deployment Security

The EC2 deployment uses restricted network access:

- SSH access is restricted to the authorized IP address configured in the AWS security group.
- The API is bound to the EC2 instance's localhost interface.
- API documentation can be accessed through an SSH tunnel.
- RabbitMQ ports are not exposed publicly.
- Environment variables and RabbitMQ credentials are stored in an EC2 `.env` file rather than committed to GitHub.

### Accessing the Deployed API

The API is accessed through an SSH tunnel rather than a publicly exposed HTTP port.

After establishing the SSH tunnel, open:

- **Interactive API documentation:** `http://127.0.0.1:8000/docs`
- **Health check:** `http://127.0.0.1:8000/health`

The SSH tunnel forwards local port `8000` to the API running on the EC2 instance.

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

- **Interactive API documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)

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

**Note:** This standalone Docker Hub option runs the API container only. It does not start the RabbitMQ broker or background worker. Use Docker Compose for the complete background-processing architecture.

### Option 2: Run with Docker Compose

Use Docker Compose to build and run the application from the source code.

**Prerequisites:** Docker Desktop installed and running.

#### 1. Clone the repository

```bash
git clone https://github.com/ShriyaYadavalli/taskflow-api.git
cd taskflow-api
```

#### 2. Configure environment variables

Create a `.env` file in the project root containing your RabbitMQ credentials:

```env
RABBITMQ_USER=your_username
RABBITMQ_PASSWORD=your_password
```

Use your own credentials. Do not commit the `.env` file to GitHub.

#### 3. Build and start the application

```bash
docker compose up --build
```

#### 4. Access the API

- **Interactive API documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)

#### 5. Stop the application

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

[http://127.0.0.1:8000/docs](http://127.0.0