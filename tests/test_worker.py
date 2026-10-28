import pytest

from app.worker import process_message


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
