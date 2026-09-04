import json
from pathlib import Path


DATA_FILE = Path(__file__).parent.parent / "data" / "knowledge_base.json"


def search_knowledge_base(query: str) -> list:
    """
    Search the internal security knowledge base.
    """

    with open(DATA_FILE, "r") as file:
        articles = json.load(file)

    query_words = query.lower().split()

    results = []

    for article in articles:

        searchable_text = (
            article["title"] + " " + article["content"]
        ).lower()

        if any(word in searchable_text for word in query_words):
            results.append(article)

    return results