from pydantic import BaseModel

from salman.neo4j import Neo4jSession, create_relationship


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
    labels: set[str] = set()

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
        with Neo4jSession() as neo:
            records = neo.query(
                """
                MATCH (s)-[p]-(o) WHERE s.name=$name
                RETURN s,p,o""",
                {"name": self.name},
            )
            return set(
                [
                    (
                        record["p"]["name"],
                        record["o"]["name"],
                    )
                    for record in records
                ]
            )


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


def get_subject(subject: Node):
    with Neo4jSession() as neo:
        records = neo.query(
            """
            MATCH (s)-[p]-(o)
            WHERE s.name = $name
            RETURN s,p,o, id(s)""",
            {"name": subject.name},
        )
        return records
