from salman.graph.triples import (
    Node,
    create_semantic_triple,
    delete_node,
)


def test_node():
    delete_node("test_node")
    node = Node(name="test_node")
    assert node.id is None
    node.save()
    assert node.id is not None

    node = Node(name="test_node")
    assert node.id is not None
    assert node.name == "test_node"
    assert node.labels == set()

    node.labels.add("label")
    node.save()

    node = Node(name="test_node")
    assert node.id is not None
    assert node.name == "test_node"
    assert "label" in node.labels

    delete_node("test_node")


def test_triples():
    delete_node("Test Subject")
    delete_node("Test Object #1")
    delete_node("Test Object #2")
    delete_node("Test Object #3")

    # Add a triple, persist it.
    subject, predicate, object = create_semantic_triple(
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
    subject.add_relationship("knows well", Node(name="Test Object #2"))
    triples = subject.get_triples()
    assert triples == {("knows", "Test Object #1"), ("knows well", "Test Object #2")}

    # Add another triple with new objects, persist it.
    subject, predicate, object = create_semantic_triple(
        subject=Node(name="Test Subject"),
        predicate="wants to learn",
        obj=Node(name="Test Object #3"),
    )

    # Retrieve the triples.
    triples = subject.get_triples()
    assert triples == {
        ("knows", "Test Object #1"),
        ("knows well", "Test Object #2"),
        ("wants to learn", "Test Object #3"),
    }

    delete_node("Test Subject")
    delete_node("Test Object #1")
    delete_node("Test Object #2")
    delete_node("Test Object #3")
