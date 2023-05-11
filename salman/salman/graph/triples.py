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
        return ["Object", self.name]


class Subject(BaseModel):
    id: int | None = None
    name: str

    @property
    def labels(self):
        return ["Subject", self.name]

    def save(self):
        with Neo4jSession() as neo:
            res = neo.query(
                f"""
                MERGE (s:Subject:{self.name})
                SET s.name = $name
                RETURN s, id(s)""",
                parameters={"name": self.name},
            )
            self.id = res[0]["id(s)"]

    def add_relationship(self, predicate: str, obj: Object):
        if not self.id:
            self.save()
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
                f"""
                MATCH (s:Subject:{self.name})-[p]-(o)
                RETURN s,p,o"""
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

    @classmethod
    def from_subject(cls, subject: str):
        with Neo4jSession() as neo:
            records = neo.query(
                f"""
                MATCH (s:Subject:{subject})
                RETURN s, id(s)"""
            )
            if not records:
                return cls(name=subject)
            return cls(
                id=records[0]["id(s)"],
                name=records[0]["s"]["name"],
            )


def create_semantic_triple(
    subject: Subject,
    predicate: str,
    obj: Object,
) -> None:
    saved = Subject.from_subject(subject.name)
    if saved:
        subject.id = saved.id
    else:
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
            f"""
            MATCH (s:Subject:{subject.name})-[p]-(o)
            DELETE s,p,o"""
        )


def get_subject(subject: Subject):
    with Neo4jSession() as neo:
        records = neo.query(
            f"""
            MATCH (s:Subject:{subject.name})-[p]-(o)
            RETURN s,p,o, id(s)"""
        )
        return records
