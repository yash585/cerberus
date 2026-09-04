import json
from pathlib import Path


DATA_FILE = Path(__file__).parent.parent / "data" / "assets.json"


def search_assets(query: str) -> list:
    """
    Search assets using hostname, IP address, department,
    operating system, or criticality.
    """

    with open(DATA_FILE, "r") as file:
        assets = json.load(file)

    query = query.lower()

    results = []

    for asset in assets:
        searchable_text = " ".join(
            str(value).lower() for value in asset.values()
        )

        if query in searchable_text:
            results.append(asset)

    return results


def get_asset(hostname: str) -> dict:
    """
    Retrieve a specific asset using its hostname.
    """

    with open(DATA_FILE, "r") as file:
        assets = json.load(file)

    for asset in assets:
        if asset["hostname"].lower() == hostname.lower():
            return asset

    return {"error": f"Asset {hostname} not found"}