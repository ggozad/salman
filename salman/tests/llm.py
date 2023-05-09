from langchain.graphs.networkx_graph import KnowledgeTriple

from salman.llm.graph import memory


def test_graph_triples_extraction():
    entities = memory.get_current_entities("Python and Rust are programming languages.")
    assert entities == ["Python", "Rust"]

    triples = memory.get_knowledge_triplets(
        "Python and Rust are programming languages."
    )
    assert triples == [
        KnowledgeTriple(
            subject="Python",
            predicate="is a",
            object_="programming language",
        ),
        KnowledgeTriple(
            subject="Rust",
            predicate="is a",
            object_="programming language",
        ),
    ]
