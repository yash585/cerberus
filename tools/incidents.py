import json
from pathlib import Path


DATA_FILE = Path(__file__).parent.parent / "data" / "incidents.json"


def search_incidents(query: str) -> list:
    """
    Search security incidents using an incident ID, title,
    severity, status, or affected asset.
    """

    with open(DATA_FILE, "r") as file:
        incidents = json.load(file)

    query = query.lower()

    results = []

    for incident in incidents:
        searchable_text = " ".join(
            str(value).lower() for value in incident.values()
        )

        if query in searchable_text:
            results.append(incident)

    return results


def get_incident(incident_id: str) -> dict:
    """
    Retrieve a specific incident using its incident ID.
    """

    with open(DATA_FILE, "r") as file:
        incidents = json.load(file)

    for incident in incidents:
        if incident["id"].lower() == incident_id.lower():
            return incident

    return {"error": f"Incident {incident_id} not found"}