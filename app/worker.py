import json

import pika
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import Task
from app.queue import (
    RABBITMQ_HOST,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    QUEUE_NAME,
    RETRY_QUEUE,
    MAX_RETRIES,
    declare_queues,
)


class PermanentJobError(ValueError):
    """An error that retrying will not fix."""


def process_message(message: dict) -> None:
    """Process a queued TaskFlow job."""
    job_type = message.get("job_type")
    payload = message.get("payload", {})

    if job_type == "process_task":
        task_id = payload.get("task_id")

        if not isinstance(task_id, int) or isinstance(task_id, bool):
            raise PermanentJobError("A valid task_id is required")

        db = SessionLocal()

        try:
            task = db.get(Task, task_id)

            if task is None:
                raise PermanentJobError(
                    f"Task {task_id} does not exist"
                )

            if task.status == "completed":
                print(
                    f"Task {task_id} is already completed.",
                    flush=True,
                )
                return

            task.status = "in_progress"
            db.commit()

            print(
                f"Task {task_id} is now in progress.",
                flush=True,
            )

            # Demonstration processing step.
            # Replace this with the actual task operation later.
            task.status = "completed"
            db.commit()

            print(
                f"Task {task_id} completed successfully.",
                flush=True,
            )

        except SQLAlchemyError:
            db.rollback()
            raise

        finally:
            db.close()

    elif job_type == "send_notification":
        recipient = payload.get("recipient")
        subject = payload.get(
            "subject",
            "TaskFlow notification",
        )
        body = payload.get(
            "message",
            "You have a new notification from TaskFlow.",
        )

        if not recipient:
            raise PermanentJobError(
                "Notification recipient is required"
            )

        print("----- SIMULATED EMAIL -----", flush=True)
        print(f"To: {recipient}", flush=True)
        print(f"Subject: {subject}", flush=True)
        print(f"Body: {body}", flush=True)
        print("----- EMAIL NOT SENT -----", flush=True)

    else:
        print(f"Processing message: {message}", flush=True)


def handle_message(ch, method, properties, body) -> None:
    """Process one RabbitMQ delivery and decide whether to ack, retry, or reject."""
    try:
        message = json.loads(body.decode("utf-8"))
        process_message(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except PermanentJobError as error:
        print(f"Permanent job failure: {error}", flush=True)
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )

    except Exception as error:
        headers = (properties.headers or {}) if properties else {}
        retry_count = headers.get("x-retry-count", 0)

        if retry_count < MAX_RETRIES:
            next_retry_count = retry_count + 1

            try:
                ch.basic_publish(
                    exchange="",
                    routing_key=RETRY_QUEUE,
                    body=body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type="application/json",
                        headers={
                            **headers,
                            "x-retry-count": next_retry_count,
                        },
                    ),
                )

                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(
                    f"Temporary failure: {error}. "
                    f"Retry {next_retry_count}/{MAX_RETRIES} scheduled.",
                    flush=True,
                )

            except Exception as publish_error:
                print(
                    f"Could not schedule retry: {publish_error}",
                    flush=True,
                )
                ch.basic_nack(
                    delivery_tag=method.delivery_tag,
                    requeue=True,
                )

        else:
            print(
                f"Retry limit reached: {error}. "
                "Sending job to dead-letter queue.",
                flush=True,
            )
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )


def main() -> None:
    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD,
    )

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials,
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    declare_queues(channel)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=handle_message,
        auto_ack=False,
    )

    print("TaskFlow worker is waiting for messages...", flush=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
