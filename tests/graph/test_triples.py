import pytest

from salman.graph.triples import Node, create_semantic_triple


@pytest.mark.asyncio
async def test_node():
    node = Node(name="test_node")
    assert node.id is None
    await node.save()
    assert node.id is not None

    node = Node(name="test_node")
    assert node.id is not None
    assert node.name == "test_node"
    assert node.labels == set(["Node"])

    node.labels.add("label")
    await node.save()

    node = Node(name="test_node")
    assert node.id is not None
    assert node.name == "test_node"
    assert "label" in node.labels


@pytest.mark.asyncio
async def test_triples():
    # Add a triple, persist it.
    subject, predicate, object = await create_semantic_triple(
        subject=Node(name="Test Subject"),
        predicate="knows",
        obj=Node(name="Test Object #1"),
    )
    assert subject.name == "Test Subject"
    assert predicate == "knows"
    assert object.name == "Test Object #1"
    assert subject.id is not None
    assert object.id is not None
    # Retrieve the triple.
    subject = Node(name="Test Subject")
    assert subject.name == "Test Subject"
    assert subject.id is not None

    # Add another relationship, persist it.
    await subject.add_relationship("knows well", Node(name="Test Object #2"))
    triples = await subject.get_triples()
    assert triples == {
        ("Test Subject", "knows", "Test Object #1"),
        ("Test Subject", "knows well", "Test Object #2"),
    }

    # Add another triple with new objects, persist it.
    subject, predicate, object = await create_semantic_triple(
        subject=Node(name="Test Subject"),
        predicate="wants to learn",
        obj=Node(name="Test Object #3"),
    )

    # Retrieve the triples.
    triples = await subject.get_triples()
    assert triples == {
        ("Test Subject", "knows", "Test Object #1"),
        ("Test Subject", "knows well", "Test Object #2"),
        ("Test Subject", "wants to learn", "Test Object #3"),
    }
