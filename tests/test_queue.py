from unittest.mock import Mock

from app.queue import (
    DEAD_LETTER_EXCHANGE,
    DEAD_LETTER_QUEUE,
    QUEUE_NAME,
    declare_queues,
)


def test_declares_dead_letter_exchange():
    channel = Mock()

    declare_queues(channel)

    channel.exchange_declare.assert_called_once_with(
        exchange=DEAD_LETTER_EXCHANGE,
        exchange_type="direct",
        durable=True,
    )


def test_declares_and_binds_dead_letter_queue():
    channel = Mock()

    declare_queues(channel)

    channel.queue_declare.assert_any_call(
        queue=DEAD_LETTER_QUEUE,
        durable=True,
    )

    channel.queue_bind.assert_called_once_with(
        queue=DEAD_LETTER_QUEUE,
        exchange=DEAD_LETTER_EXCHANGE,
        routing_key=DEAD_LETTER_QUEUE,
    )


def test_main_queue_uses_dead_letter_routing():
    channel = Mock()

    declare_queues(channel)

    channel.queue_declare.assert_any_call(
        queue=QUEUE_NAME,
        durable=True,
        arguments={
            "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
            "x-dead-letter-routing-key": DEAD_LETTER_QUEUE,
        },
    )
