import asyncio

import spacy
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from salman.logging import salman as logger
from salman.neo4j import Neo4jSession, create_relationship

_embedding_model: SentenceTransformer | None = None
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_nlp = spacy.load("en_core_web_sm")


async def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.debug(f"Loading {EMBEDDING_MODEL}")
        try:
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            logger.debug(f"Loaded {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load {EMBEDDING_MODEL}: {e}")
            raise e
    return _embedding_model


loop = asyncio.get_event_loop()
loop.create_task(get_embedding_model())


async def get_embeddings(text: str):
    model = await get_embedding_model()
    return model.encode(text)


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

    async def save(self):
        async with Neo4jSession() as neo:
            labels = ":".join(self.labels)
            if labels:
                labels = ":" + labels
            if self.id:
                res = await neo.aquery(
                    f"""
                    MATCH (n)
                    WHERE id(n) = $id
                    {f"SET n{labels}" if labels else ""}
                    RETURN n, id(n)""",
                    parameters={"id": self.id},
                )
            else:
                res = await neo.aquery(
                    f"""
                    CREATE (n{labels})
                    SET n.name = $name
                    RETURN n, id(n)""",
                    parameters={"name": self.name},
                )
            self.id = res[0]["id(n)"]

    async def add_relationship(self, predicate: str, obj: "Node"):
        if obj.id is None:
            await obj.save()

        fact = f"{self.name} {predicate} {obj.name}"
        fact_embeddings = await get_embeddings(fact)

        await create_relationship(
            start_node_id=self.id,
            end_node_id=obj.id,
            relationship_type=predicate_to_label(predicate),
            params={
                "predicate": predicate,
                "fact": fact,
                "fact_embeddings": fact_embeddings.tolist(),
            },
        )

    async def get_triples(self):
        result = set([])
        async with Neo4jSession() as neo:
            records = await neo.aquery(
                """
                    MATCH (s)-[p]->(o) WHERE id(s) = $id OR id(o) = $id
                    RETURN s,p,o""",
                {"id": self.id},
            )

            result.update(
                [
                    (
                        record["s"]["name"],
                        record["p"]["predicate"],
                        record["o"]["name"],
                    )
                    for record in records
                ]
            )
        return result


async def create_semantic_triple(
    subject: Node,
    predicate: str,
    obj: Node,
) -> tuple[Node, str, Node]:
    if subject.id is None:
        await subject.save()

    if obj.id is None:
        await obj.save()

    fact = f"{subject.name} {predicate} {obj.name}"
    fact_embeddings = await get_embeddings(fact)

    await create_relationship(
        start_node_id=subject.id,
        end_node_id=obj.id,
        relationship_type=predicate_to_label(predicate),
        params={
            "predicate": predicate,
            "fact": fact,
            "fact_embeddings": fact_embeddings.tolist(),
        },
    )

    return (subject, predicate, obj)


async def delete_node(name: str):
    async with Neo4jSession() as neo:
        await neo.aquery(
            """
            MATCH (n)
            WHERE n.name = $name
            DETACH DELETE n""",
            {"name": name},
        )


async def get_facts_for_subject(subject: str) -> set[str]:
    doc = _nlp(subject)
    tokens = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "ADJ"]]
    results = set([])
    facts = set([])
    async with Neo4jSession() as neo:
        for token in tokens:
            records = await neo.aquery(
                """
                    MATCH (s)-[p]-(o)
                    WHERE s.name CONTAINS $name
                    RETURN s,p,o, id(s)""",
                {"name": token},
            )
            results.update(records)
    for record in results:
        node = Node(name=record["s"]["name"])
        for triple in await node.get_triples():
            facts.add(" ".join(triple))
    return facts
