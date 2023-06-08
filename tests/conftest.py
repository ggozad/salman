import pytest_asyncio

from salman.graph.triples import delete_node


@pytest_asyncio.fixture(autouse=True)
async def cleanup_neo4j():
    # Clean up the database

    await delete_node("Test Subject #1")
    await delete_node("Test Subject #2")
    await delete_node("Test Object #1")
    await delete_node("Test Object #2")
    await delete_node("Test Object #3")
    await delete_node("test_node")
    yield
    await delete_node("Test Subject #1")
    await delete_node("Test Subject #2")
    await delete_node("Test Object #1")
    await delete_node("Test Object #2")
    await delete_node("Test Object #3")
    await delete_node("test_node")
