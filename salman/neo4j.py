from neo4j import AsyncGraphDatabase, GraphDatabase
from pydantic import BaseModel

from salman.config import Config


class Neo4jSession:
    def __init__(self):
        self._uri = Config.NEO4J_URI
        self._db_name = Config.NEO4J_DATABASE
        self._user = Config.NEO4J_USER
        self._pwd = Config.NEO4J_PASSWORD

    def __enter__(self):
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._pwd))
        return self

    def __exit__(self, *args):
        if self._driver is not None:
            self._driver.close()

    async def __aenter__(self):
        self._driver = AsyncGraphDatabase.driver(
            self._uri, auth=(self._user, self._pwd)
        )
        return self

    async def __aexit__(self, *args):
        if self._driver is not None:
            await self._driver.close()

    async def aquery(self, query, parameters=None):
        records, summary, keys = await self._driver.execute_query(query, parameters)
        return records

    def query(self, query, parameters=None):
        records, summary, keys = self._driver.execute_query(query, parameters)
        return records


async def create_node(model: BaseModel):
    async with Neo4jSession() as neo:
        params = model.dict()
        labels = ":".join(model.labels)

        return await neo.query(
            f"CREATE (n:{labels} $params) RETURN id(n) AS id",
            {"params": params},
        )[0].get("id")


def predicate_to_label(predicate: str):
    """
    Return the predicate as a label, using only A-Z characters and underscores.
    """
    predicate = predicate.replace(" ", "_")
    return "".join(
        [char for char in predicate.upper() if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_"]
    )


async def create_relationship(
    start_node_id: int,
    end_node_id: int,
    relationship_label: str,
    params: dict = {},
) -> None:
    relationship_label = predicate_to_label(relationship_label)

    async with Neo4jSession() as neo:
        return await neo.aquery(
            f"""
            MATCH (a), (b)
            WHERE id(a) = $start_node_id AND id(b) = $end_node_id
            WITH a, b
            CREATE (a)-[:{relationship_label} $params]->(b)
            """,
            {
                "start_node_id": start_node_id,
                "end_node_id": end_node_id,
                "params": params,
            },
        )
