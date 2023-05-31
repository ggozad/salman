import pytest

from salman.graph.triples import Node, create_semantic_triple, search_facts


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
        subject=Node(name="Test Subject #1"),
        predicate="knows",
        obj=Node(name="Test Object #1"),
    )
    assert subject.name == "Test Subject #1"
    assert predicate == "knows"
    assert object.name == "Test Object #1"
    assert subject.id is not None
    assert object.id is not None
    # Retrieve the triple.
    subject = Node(name="Test Subject #1")
    assert subject.name == "Test Subject #1"
    assert subject.id is not None

    # Add another relationship, persist it.
    await subject.add_relationship("knows well", Node(name="Test Object #2"))
    triples = await subject.get_triples()
    assert triples == {
        ("Test Subject #1", "knows", "Test Object #1"),
        ("Test Subject #1", "knows well", "Test Object #2"),
    }

    # Add another triple with new objects, persist it.
    subject, predicate, object = await create_semantic_triple(
        subject=Node(name="Test Subject #1"),
        predicate="wants to learn",
        obj=Node(name="Test Object #3"),
    )

    # Retrieve the triples.
    triples = await subject.get_triples()
    assert triples == {
        ("Test Subject #1", "knows", "Test Object #1"),
        ("Test Subject #1", "knows well", "Test Object #2"),
        ("Test Subject #1", "wants to learn", "Test Object #3"),
    }


@pytest.mark.asyncio
async def test_search():
    facts = [
        ("Test Subject #1", "wants to learn", "Test Object #2"),
        ("Test Subject #1", "is", "the daughter of Test Object #1"),
        ("Test Subject #1", "knows well", "Test Object #3"),
        ("Test Subject #2", "is the son of", "Test Object #1"),
    ]

    for s, p, o in facts:
        await create_semantic_triple(
            subject=Node(name=s), predicate=p, obj=Node(name=o)
        )

    search_result = await search_facts("Who is the family of Test Subject #1?")
    top_2_facts = [fact for fact, similarity in search_result][:2]
    assert "Test Subject #1 is the daughter of Test Object #1" in top_2_facts
    assert "Test Subject #2 is the son of Test Object #1" in top_2_facts
