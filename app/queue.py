import json
import os

import pika


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "taskflow")
RABBITMQ_PASSWORD = os.getenv(
    "RABBITMQ_PASSWORD",
    "localdevpassword",
)

QUEUE_NAME = "taskflow-jobs"
RETRY_QUEUE = "taskflow-jobs-retry"
DEAD_LETTER_QUEUE = "taskflow-jobs-dead"
DEAD_LETTER_EXCHANGE = "taskflow-dead-letter"

RETRY_DELAY_MS = 5000
MAX_RETRIES = 3


def declare_queues(channel) -> None:
    """Create the main, retry, and dead-letter queues."""

    channel.exchange_declare(
        exchange=DEAD_LETTER_EXCHANGE,
        exchange_type="direct",
        durable=True,
    )

    channel.queue_declare(
        queue=DEAD_LETTER_QUEUE,
        durable=True,
    )

    channel.queue_bind(
        queue=DEAD_LETTER_QUEUE,
        exchange=DEAD_LETTER_EXCHANGE,
        routing_key=DEAD_LETTER_QUEUE,
    )

    channel.queue_declare(
        queue=RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": RETRY_DELAY_MS,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": QUEUE_NAME,
        },
    )

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={
            "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
            "x-dead-letter-routing-key": DEAD_LETTER_QUEUE,
        },
    )


def publish_task_message(message: dict) -> None:
    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD,
    )

    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials,
        connection_attempts=3,
        retry_delay=1,
        socket_timeout=3,
    )

    connection = pika.BlockingConnection(parameters)

    try:
        channel = connection.channel()
        declare_queues(channel)

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
    finally:
        connection.close()
