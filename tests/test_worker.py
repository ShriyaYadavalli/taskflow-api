import json
from types import SimpleNamespace
from unittest.mock import Mock

import pika
import pytest

from app.queue import MAX_RETRIES, QUEUE_NAME, RETRY_QUEUE
from app.worker import (
    PermanentJobError,
    handle_message,
    process_message,
)


def test_send_notification_prints_email_preview(capsys):
    message = {
        "job_type": "send_notification",
        "payload": {
            "recipient": "user@example.com",
            "subject": "Report ready",
            "message": "Your report is ready.",
        },
    }

    process_message(message)

    output = capsys.readouterr().out

    assert "To: user@example.com" in output
    assert "Subject: Report ready" in output
    assert "Body: Your report is ready." in output
    assert "EMAIL NOT SENT" in output


def test_send_notification_without_recipient_raises_error():
    message = {
        "job_type": "send_notification",
        "payload": {
            "subject": "Report ready",
            "message": "Your report is ready.",
        },
    }

    with pytest.raises(
        ValueError,
        match="Notification recipient is required",
    ):
        process_message(message)


def test_unknown_job_type_keeps_existing_behavior(capsys):
    message = {
        "job_type": "generate_report",
        "payload": {"report_name": "weekly_report"},
    }

    process_message(message)

    output = capsys.readouterr().out

    assert "Processing message:" in output
    assert "generate_report" in output


def test_missing_recipient_is_a_permanent_error():
    message = {
        "job_type": "send_notification",
        "payload": {},
    }

    with pytest.raises(PermanentJobError):
        process_message(message)


def test_retry_configuration_has_a_positive_limit():
    assert MAX_RETRIES > 0
    assert RETRY_QUEUE == "taskflow-jobs-retry"
    assert QUEUE_NAME == "taskflow-jobs"



def test_successful_message_is_acknowledged():
    channel = Mock()
    method = SimpleNamespace(delivery_tag=1)
    properties = SimpleNamespace(headers={})
    body = json.dumps({
        "job_type": "generate_report",
        "payload": {},
    }).encode("utf-8")

    handle_message(channel, method, properties, body)

    channel.basic_ack.assert_called_once_with(delivery_tag=1)
    channel.basic_nack.assert_not_called()
    channel.basic_publish.assert_not_called()


def test_temporary_failure_schedules_retry(monkeypatch):
    channel = Mock()
    method = SimpleNamespace(delivery_tag=2)
    properties = SimpleNamespace(headers={})
    body = b'{"job_type": "send_notification", "payload": {}}'

    def fail_processing(message):
        raise RuntimeError("Temporary error")

    monkeypatch.setattr(
        "app.worker.process_message",
        fail_processing,
    )

    handle_message(channel, method, properties, body)

    channel.basic_publish.assert_called_once()
    publish_args = channel.basic_publish.call_args.kwargs

    assert publish_args["routing_key"] == RETRY_QUEUE
    assert publish_args["body"] == body
    assert publish_args["properties"].headers["x-retry-count"] == 1
    channel.basic_ack.assert_called_once_with(delivery_tag=2)


def test_retry_limit_sends_message_to_dead_letter_queue(monkeypatch):
    channel = Mock()
    method = SimpleNamespace(delivery_tag=3)
    properties = SimpleNamespace(
        headers={"x-retry-count": MAX_RETRIES},
    )
    body = b'{"job_type": "generate_report", "payload": {}}'

    def fail_processing(message):
        raise RuntimeError("Still failing")

    monkeypatch.setattr(
        "app.worker.process_message",
        fail_processing,
    )

    handle_message(channel, method, properties, body)

    channel.basic_nack.assert_called_once_with(
        delivery_tag=3,
        requeue=False,
    )
    channel.basic_publish.assert_not_called()
    channel.basic_ack.assert_not_called()


def test_permanent_failure_goes_to_dead_letter_queue():
    channel = Mock()
    method = SimpleNamespace(delivery_tag=4)
    properties = SimpleNamespace(headers={})
    body = json.dumps({
        "job_type": "send_notification",
        "payload": {},
    }).encode("utf-8")

    handle_message(channel, method, properties, body)

    channel.basic_nack.assert_called_once_with(
        delivery_tag=4,
        requeue=False,
    )
    channel.basic_publish.assert_not_called()
