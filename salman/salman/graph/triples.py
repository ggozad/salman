from pydantic import BaseModel

from salman.neo4j import Neo4jSession, create_node, create_relationship


def predicate_to_label(predicate: str):
    """
    Return the predicate as a label, using only A-Z characters and underscores.
    """
    predicate = predicate.replace(" ", "_")
    return "".join(
        [char for char in predicate.upper() if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"]
    )


class Object(BaseModel):
    id: int | None = None
    name: str

    @property
    def labels(self):
        return ["Object"]


class Subject(BaseModel):
    id: int | None = None
    name: str

    def __init__(self, **data):
        super().__init__(**data)
        with Neo4jSession() as neo:
            records = neo.query(
                """
                MATCH (s:Subject)
                WHERE s.name = $name
                RETURN s, id(s)""",
                {"name": self.name},
            )
            if records:
                self.id = records[0]["id(s)"]

    @property
    def labels(self):
        return ["Subject", self.name]

    def save(self):
        with Neo4jSession() as neo:
            if not self.id:
                res = neo.query(
                    """
                    CREATE (s:Subject)
                    SET s.name = $name
                    RETURN s, id(s)""",
                    parameters={"name": self.name},
                )
                self.id = res[0]["id(s)"]

    def add_relationship(self, predicate: str, obj: Object):
        obj.id = create_node(obj)
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
                MATCH (s:Subject)-[p]-(o) WHERE s.name=$name
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
    subject: Subject,
    predicate: str,
    obj: Object,
) -> None:
    if subject.id is None:
        subject.save()

    obj.id = create_node(obj)
    create_relationship(
        start_node_id=subject.id,
        end_node_id=obj.id,
        relationship_type=predicate_to_label(predicate),
        params={"name": predicate},
    )
    return (subject, predicate, obj)


def delete_subject(subject: Subject):
    with Neo4jSession() as neo:
        neo.query(
            """
            MATCH (s:Subject)-[p]-(o)
            WHERE s.name = $name
            DELETE s,p,o""",
            {"name": subject.name},
        )


def get_subject(subject: Subject):
    with Neo4jSession() as neo:
        records = neo.query(
            """
            MATCH (s:Subject)-[p]-(o)
            WHERE s.name = $name
            RETURN s,p,o, id(s)""",
            {"name": subject.name},
        )
        return records
