import pika

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@patch("app.main.publish_task_message")
def test_create_job_queues_message(mock_publish):
    payload = {
        "job_type": "generate_report",
        "payload": {
            "report_name": "weekly_task_report",
            "requested_by": "taskflow-user",
        },
    }

    response = client.post("/jobs", json=payload)

    assert response.status_code == 202
    assert response.json() == {
        "status": "queued",
        "job": payload,
    }

    mock_publish.assert_called_once_with(payload)


@patch("app.main.publish_task_message")
def test_create_job_defaults_payload_to_empty_dict(mock_publish):
    payload = {"job_type": "cleanup"}

    response = client.post("/jobs", json=payload)

    assert response.status_code == 202
    assert response.json()["job"] == {
        "job_type": "cleanup",
        "payload": {},
    }

    mock_publish.assert_called_once_with({
        "job_type": "cleanup",
        "payload": {},
    })


@patch("app.main.publish_task_message")
def test_create_job_rejects_missing_job_type(mock_publish):
    response = client.post(
        "/jobs",
        json={"payload": {"example": "value"}},
    )

    assert response.status_code == 422
    mock_publish.assert_not_called()


@patch(
    "app.main.publish_task_message",
    side_effect = pika.exceptions.AMQPConnectionError("RabbitMQ unavailable"),
)
def test_create_job_returns_503_when_queue_is_unavailable(mock_publish):
    response = client.post(
        "/jobs",
        json={"job_type": "generate_report"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Job queue is currently unavailable"
    }

    mock_publish.assert_called_once()
