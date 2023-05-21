import spacy
from pydantic import BaseModel

from salman.neo4j import Neo4jSession, create_relationship

_nlp = spacy.load("en_core_web_sm")


def predicate_to_label(predicate: str):
    """
    Return the predicate as a label, using only A-Z characters and underscores.
    """
    predicate = predicate.replace(" ", "_")
    return "".join(
        [char for char in predicate.upper() if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"]
    )


class Node(BaseModel):
    id: int | None = None
    name: str
    labels: set[str] = set(["Node"])

    def __init__(self, **data):
        super().__init__(**data)
        with Neo4jSession() as neo:
            records = neo.query(
                """
                MATCH (o)
                WHERE o.name = $name
                RETURN o, id(o)""",
                {"name": self.name},
            )
            if records:
                self.labels = set(records[0]["o"].labels)
                self.id = records[0]["id(o)"]

    def save(self):
        with Neo4jSession() as neo:
            labels = ":".join(self.labels)
            if labels:
                labels = ":" + labels
            if self.id:
                res = neo.query(
                    f"""
                    MATCH (n)
                    WHERE id(n) = $id
                    {f"SET n{labels}" if labels else ""}
                    RETURN n, id(n)""",
                    parameters={"id": self.id},
                )
            else:
                res = neo.query(
                    f"""
                    CREATE (n{labels})
                    SET n.name = $name
                    RETURN n, id(n)""",
                    parameters={"name": self.name},
                )
            self.id = res[0]["id(n)"]

    def add_relationship(self, predicate: str, obj: "Node"):
        if obj.id is None:
            obj.save()

        create_relationship(
            start_node_id=self.id,
            end_node_id=obj.id,
            relationship_type=predicate_to_label(predicate),
            params={"name": predicate},
        )

    def get_triples(self):
        doc = _nlp(self.name)
        tokens = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "ADJ"]]
        result = set([])
        with Neo4jSession() as neo:
            for token in tokens:
                records = neo.query(
                    """
                    MATCH (s)-[p]->(o) WHERE s.name CONTAINS $name
                    RETURN s,p,o""",
                    {"name": token},
                )
                result.update(
                    [
                        (
                            record["s"]["name"],
                            record["p"]["name"],
                            record["o"]["name"],
                        )
                        for record in records
                    ]
                )
        return result


def create_semantic_triple(
    subject: Node,
    predicate: str,
    obj: Node,
) -> None:
    if subject.id is None:
        subject.save()

    if obj.id is None:
        obj.save()

    create_relationship(
        start_node_id=subject.id,
        end_node_id=obj.id,
        relationship_type=predicate_to_label(predicate),
        params={"name": predicate},
    )
    return (subject, predicate, obj)


def delete_node(name: str):
    with Neo4jSession() as neo:
        neo.query(
            """
            MATCH (n)
            WHERE n.name = $name
            DETACH DELETE n""",
            {"name": name},
        )


def get_facts_for_subject(subject: str) -> set[str]:
    doc = _nlp(subject)
    tokens = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "ADJ"]]
    results = set([])
    facts = set([])
    with Neo4jSession() as neo:
        for token in tokens:
            records = neo.query(
                """
                    MATCH (s)-[p]-(o)
                    WHERE s.name CONTAINS $name
                    RETURN s,p,o, id(s)""",
                {"name": token},
            )
            results.update(records)
    for record in results:
        node = Node(name=record["s"]["name"])
        for triple in node.get_triples():
            facts.add(" ".join(triple))
    return facts
