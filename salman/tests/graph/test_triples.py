from salman.graph.triples import (
    Object,
    Subject,
    create_semantic_triple,
    delete_subject,
)


def test_triples():
    delete_subject(subject=Subject(name="Salman AI"))

    # Add a triple, persist it.
    subject, predicate, object = create_semantic_triple(
        subject=Subject(name="Salman AI"),
        predicate="knows",
        obj=Object(name="Neo4j"),
    )
    assert subject.name == "Salman AI"
    assert predicate == "knows"
    assert object.name == "Neo4j"
    assert subject.id is not None
    assert object.id is not None

    # Retrieve the triple.
    subject = Subject(name="Salman AI")
    assert subject.name == "Salman AI"
    assert subject.id is not None

    # Add another relationship, persist it.
    subject.add_relationship("knows well", Object(name="Python"))
    triples = subject.get_triples()
    assert triples == {("knows", "Neo4j"), ("knows well", "Python")}

    # Add another triple with new objects, persist it.
    subject, predicate, object = create_semantic_triple(
        subject=Subject(name="Salman AI"),
        predicate="wants to learn",
        obj=Object(name="the Rust language"),
    )

    # Retrieve the triples.
    triples = subject.get_triples()
    assert triples == {
        ("knows", "Neo4j"),
        ("knows well", "Python"),
        ("wants to learn", "the Rust language"),
    }

    delete_subject(subject=Subject(name="Salman AI"))
    subject = Subject(name="Salman AI")
    assert subject.id is None
