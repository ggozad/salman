from salman.graph.triplets import (
    Object,
    Subject,
    create_knowledge_triplet,
    delete_subject,
)


def test_triplets():
    delete_subject(subject=Subject(name="Salman"))

    # Add a triplet, persist it.
    subject, predicate, object = create_knowledge_triplet(
        subject=Subject(name="Salman"),
        predicate="KNOWS",
        obj=Object(name="Neo4j"),
    )
    assert subject.name == "Salman"
    assert predicate == "KNOWS"
    assert object.name == "Neo4j"
    assert subject.id is not None
    assert object.id is not None

    # Retrieve the triplet.
    subject = Subject.from_subject("Salman")
    assert subject.name == "Salman"
    assert subject.id is not None

    # Add another relationship, persist it.
    subject.add_relationship("KNOWS", Object(name="Python"))
    triplets = subject.get_triplets()
    assert triplets == {("KNOWS", "Neo4j"), ("KNOWS", "Python")}

    # Add another triplet with new objects, persist it.
    subject, predicate, object = create_knowledge_triplet(
        subject=Subject(name="Salman"),
        predicate="WANTS_TO_LEARN",
        obj=Object(name="Rust"),
    )

    # Retrieve the triplets.
    triplets = subject.get_triplets()
    assert triplets == {
        ("KNOWS", "Neo4j"),
        ("KNOWS", "Python"),
        ("WANTS_TO_LEARN", "Rust"),
    }

    delete_subject(subject=Subject(name="Salman"))
