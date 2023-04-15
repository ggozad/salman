import asyncio

import pytest

from salman.nats import NATSManager


def fibo(n):
    if n < 2:
        return n
    return fibo(n - 1) + fibo(n - 2)


@pytest.mark.asyncio
async def test_pubsub():
    mgr = await NATSManager.create()
    await mgr.add_stream("test_stream", ["fibo.even", "fibo.odd"])

    received = []
    received_odd = []
    received_even = []

    async def subscriber(msg):
        received.append(msg.data.decode())
        await msg.ack()

    async def subscriber_odd(msg):
        received_odd.append(msg.data.decode())
        await msg.ack()

    async def subscriber_even(msg):
        received_even.append(msg.data.decode())
        await msg.ack()

    await mgr.subscribe("test_stream", "fibo.*", subscriber)
    await mgr.subscribe("test_stream", "fibo.odd", subscriber_odd)
    await mgr.subscribe("test_stream", "fibo.even", subscriber_even)

    for i in range(0, 10):
        num = fibo(i)
        if num % 2 == 0:
            await mgr.publish("fibo.even", str(num).encode())
        else:
            await mgr.publish("fibo.odd", str(num).encode())

    assert received == ["0", "1", "1", "2", "3", "5", "8", "13", "21", "34"]
    assert received_odd == ["1", "1", "3", "5", "13", "21"]
    assert received_even == ["0", "2", "8", "34"]

    await mgr.stop()


@pytest.mark.asyncio
async def test_workers():
    mgr = await NATSManager.create()
    await mgr.add_stream("test_stream", ["tasks"])

    worker1_received = []
    worker2_received = []

    async def worker1(msg):
        worker1_received.append(msg.data.decode())
        await msg.ack()

    async def worker2(msg):
        worker2_received.append(msg.data.decode())
        await msg.ack()

    await mgr.subscribe("test_stream", "tasks", worker1, queue="workers")
    await mgr.subscribe("test_stream", "tasks", worker2, queue="workers")

    for i in range(0, 10):
        await mgr.publish("tasks", str(i).encode())

    await asyncio.sleep(0.1)
    assert set(worker1_received).intersection(worker2_received) == set()
    assert set(worker1_received + worker2_received) == set(
        ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    )
    await mgr.stop()


@pytest.mark.asyncio
async def test_receipt():
    mgr = await NATSManager.create()
    await mgr.add_stream("test_stream", ["tasks"])

    worker_received = []

    async def worker(msg):
        worker_received.append(msg.data.decode())
        await msg.ack()

    # First publish a few items without a worker
    for i in range(0, 5):
        await mgr.publish("tasks", str(i).encode())

    # When we start the worker, it should receive the 5 items
    await mgr.subscribe("test_stream", "tasks", worker, queue="workers", ack_wait=0.1)
    await asyncio.sleep(0.1)
    assert worker_received == ["0", "1", "2", "3", "4"]

    worker_received = []
    non_ack_worker_received = []

    async def non_ack_worker(msg):
        non_ack_worker_received.append(msg.data.decode())

    # Now subscribe a worker that doesn't ack
    await mgr.subscribe(
        "test_stream", "tasks", non_ack_worker, queue="workers", ack_wait=0.1
    )

    for i in range(0, 10):
        await mgr.publish("tasks", str(i).encode())

    # While we sleep, the worker should eventually receive all items that were
    # published, but the non-ack worker has not acknowledged.
    await asyncio.sleep(1.0)

    # Worker should have received all items. The non-ack worker should have also received
    # all items, but it didn't ack.
    assert len(set(worker_received).intersection(non_ack_worker_received)) > 0
    assert set(worker_received) == set(
        ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    )

    await mgr.stop()
