import json
from pathlib import Path


# ============================================================
# DATA FILE
# ============================================================

DATA_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "incidents.json"
)


# ============================================================
# LOAD INCIDENTS
# ============================================================

def load_incidents() -> list:

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# SEARCH INCIDENTS
# ============================================================

def search_incidents(query: str) -> list:

    incidents = load_incidents()


    # --------------------------------------------------------
    # NORMALIZE QUERY
    # --------------------------------------------------------

    query = query.lower().strip()


    # --------------------------------------------------------
    # EMPTY QUERY
    # --------------------------------------------------------

    if not query:

        return incidents


    # --------------------------------------------------------
    # ALL INCIDENTS
    # --------------------------------------------------------

    all_keywords = [
        "all incidents",
        "show all",
        "list all",
        "every incident",
        "all"
    ]


    if any(
        keyword in query
        for keyword in all_keywords
    ):

        return incidents


    # --------------------------------------------------------
    # STATUS FILTERS
    # --------------------------------------------------------

    status_mapping = {

        "open": "open",

        "resolved": "resolved",

        "closed": "closed",

        "in progress": "in progress",

        "investigating": "investigating"

    }


    for keyword, status in status_mapping.items():

        if keyword in query:

            results = [

                incident
                for incident in incidents

                if incident.get(
                    "status",
                    ""
                ).lower() == status

            ]


            return results


    # --------------------------------------------------------
    # SEVERITY FILTERS
    # --------------------------------------------------------

    severity_mapping = {

        "critical": "critical",

        "high": "high",

        "medium": "medium",

        "low": "low"

    }


    for keyword, severity in severity_mapping.items():

        if (
            keyword in query
            and "severity" in query
        ):

            results = [

                incident
                for incident in incidents

                if incident.get(
                    "severity",
                    ""
                ).lower() == severity

            ]


            return results


    # --------------------------------------------------------
    # GENERAL KEYWORD SEARCH
    # --------------------------------------------------------

    results = []


    query_words = query.split()


    for incident in incidents:


        searchable_text = " ".join(

            str(value).lower()

            for value in incident.values()

        )


        # Exact full query match

        if query in searchable_text:

            results.append(incident)

            continue


        # Word-based matching

        matched_words = sum(

            1

            for word in query_words

            if word in searchable_text

        )


        # Require at least one meaningful match

        if matched_words > 0:

            results.append(incident)


    return results


# ============================================================
# GET SPECIFIC INCIDENT
# ============================================================

def get_incident(
    incident_id: str
) -> dict:


    incidents = load_incidents()


    incident_id = (
        incident_id
        .lower()
        .strip()
    )


    for incident in incidents:


        if (

            incident.get(
                "id",
                ""
            ).lower()

            == incident_id

        ):

            return incident


    return {

        "error":
            f"Incident {incident_id} not found"

    }