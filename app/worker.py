import json
import pika

from app.queue import (
    RABBITMQ_HOST,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    QUEUE_NAME,
    declare_queues,
)


def process_message(message: dict) -> None:
    """Process a queued TaskFlow job."""
    job_type = message.get("job_type")
    payload = message.get("payload", {})

    if job_type == "send_notification":
        recipient = payload.get("recipient")
        subject = payload.get("subject", "TaskFlow notification")
        body = payload.get(
            "message",
            "You have a new notification from TaskFlow.",
        )

        if not recipient:
            raise ValueError("Notification recipient is required")

        print("----- SIMULATED EMAIL -----", flush=True)
        print(f"To: {recipient}", flush=True)
        print(f"Subject: {subject}", flush=True)
        print(f"Body: {body}", flush=True)
        print("----- EMAIL NOT SENT -----", flush=True)

    else:
        print(f"Processing message: {message}", flush=True)


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

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body.decode("utf-8"))
            process_message(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as error:
            print(f"Message processing failed: {error}", flush=True)
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
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
