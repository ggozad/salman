from salman.graph.triples import get_facts_for_subject


def search_kb(subjects: list[str]):
    memories = set([])
    for subject in subjects:
        memories.update(get_facts_for_subject(subject))
    # Convert to list to make it JSON serializable
    memories = list(memories)
    return memories
