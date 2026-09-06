import os
import json

from groq import Groq
from dotenv import load_dotenv

from tools.incidents import search_incidents, get_incident
from tools.assets import search_assets, get_asset
from tools.knowledge_base import search_knowledge_base


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are CERBERUS, an internal AI-powered Security Operations Center assistant.

Your purpose is to assist SOC analysts with:

- Security incident investigation
- Asset information retrieval
- Cybersecurity knowledge and guidance
- Incident summarization
- Basic threat analysis

You have access to internal tools for retrieving incident records,
asset information, and security knowledge base articles.

Use the available tools when the user asks for information that may
exist in the internal SOC data.

TOOL USAGE RULES:

1. Use search_incidents when the user asks about incidents using
   descriptions, severity, status, affected assets, or general incident
   information.

2. Use get_incident only when the user provides a specific incident ID.

3. Use search_assets when the user asks about assets using hostname,
   IP address, department, operating system, or criticality.

4. Use get_asset only when the user provides a specific hostname.

5. Use search_knowledge_base when the user asks about security procedures,
   monitoring guidance, detection techniques, or incident response guidance.

6. Never call a search tool with an empty query.

7. If the user asks for the most recent, latest, or last incident but
   does not provide an ID, use search_incidents with a meaningful query
   related to the user's request.

Always provide accurate and concise security-focused responses.

Do not claim to have performed actions that you have not actually performed.
"""


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "search_incidents",
            "description": (
                "Search security incidents using keywords, severity, "
                "status, asset name, or incident details. The query "
                "must not be empty."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A meaningful search query for finding "
                            "relevant security incidents."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_incident",
            "description": (
                "Retrieve complete details for a specific incident "
                "using its incident ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": (
                            "The incident ID, for example INC-2026-001."
                        )
                    }
                },
                "required": ["incident_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_assets",
            "description": (
                "Search assets using hostname, IP address, department, "
                "operating system, or criticality. The query must not "
                "be empty."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A meaningful search query for finding "
                            "relevant assets."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_asset",
            "description": (
                "Retrieve complete information for a specific asset "
                "using its hostname."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "Hostname of the asset."
                    }
                },
                "required": ["hostname"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the internal cybersecurity knowledge base for "
                "security procedures, detection techniques, and "
                "incident response guidance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A meaningful search query for the internal "
                            "security knowledge base."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    }

]


# ============================================================
# AVAILABLE PYTHON TOOL FUNCTIONS
# ============================================================

AVAILABLE_TOOLS = {

    "search_incidents": search_incidents,

    "get_incident": get_incident,

    "search_assets": search_assets,

    "get_asset": get_asset,

    "search_knowledge_base": search_knowledge_base

}


# ============================================================
# TOOL ARGUMENT VALIDATION
# ============================================================

def validate_tool_arguments(function_name: str, arguments: dict):

    if function_name in [
        "search_incidents",
        "search_assets",
        "search_knowledge_base"
    ]:

        query = arguments.get("query", "")

        if not isinstance(query, str) or not query.strip():

            return False, {
                "error": "Search query cannot be empty."
            }


    if function_name == "get_incident":

        incident_id = arguments.get("incident_id", "")

        if not isinstance(incident_id, str) or not incident_id.strip():

            return False, {
                "error": "Incident ID cannot be empty."
            }


    if function_name == "get_asset":

        hostname = arguments.get("hostname", "")

        if not isinstance(hostname, str) or not hostname.strip():

            return False, {
                "error": "Hostname cannot be empty."
            }


    return True, None


# ============================================================
# AGENT FUNCTION
# ============================================================

def run_agent(user_message: str) -> dict:


    # --------------------------------------------------------
    # INITIAL CONVERSATION
    # --------------------------------------------------------

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },

        {
            "role": "user",
            "content": user_message
        }

    ]


    tool_activity = []


    # --------------------------------------------------------
    # FIRST MODEL REQUEST
    # --------------------------------------------------------

    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=messages,

        tools=TOOLS,

        tool_choice="auto"

    )


    response_message = response.choices[0].message


    # --------------------------------------------------------
    # IF NO TOOL WAS CALLED
    # --------------------------------------------------------

    if not response_message.tool_calls:

        return {

            "response": (
                response_message.content
                or "I was unable to generate a response."
            ),

            "tool_calls": []

        }


    # --------------------------------------------------------
    # ADD MODEL TOOL CALL MESSAGE
    # --------------------------------------------------------

    messages.append(
        response_message
    )


    # --------------------------------------------------------
    # EXECUTE TOOL CALLS
    # --------------------------------------------------------

    for tool_call in response_message.tool_calls:


        function_name = tool_call.function.name


        # ----------------------------------------------------
        # RECORD TOOL START
        # ----------------------------------------------------

        tool_activity.append({

            "name": function_name,

            "status": "running",

            "detail": f"Executing {function_name}"

        })


        # ----------------------------------------------------
        # CHECK IF TOOL EXISTS
        # ----------------------------------------------------

        if function_name not in AVAILABLE_TOOLS:

            tool_result = {

                "error": (
                    f"Unknown tool requested: {function_name}"
                )

            }


        else:

            # ------------------------------------------------
            # PARSE TOOL ARGUMENTS
            # ------------------------------------------------

            try:

                function_args = json.loads(
                    tool_call.function.arguments
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                function_args = {}


            # ------------------------------------------------
            # VALIDATE TOOL ARGUMENTS
            # ------------------------------------------------

            is_valid, validation_error = (
                validate_tool_arguments(
                    function_name,
                    function_args
                )
            )


            if not is_valid:

                tool_result = validation_error


            else:

                # --------------------------------------------
                # EXECUTE PYTHON TOOL
                # --------------------------------------------

                function_to_call = AVAILABLE_TOOLS[
                    function_name
                ]


                try:

                    tool_result = function_to_call(
                        **function_args
                    )

                except Exception as error:

                    tool_result = {

                        "error": str(error)

                    }


        # ----------------------------------------------------
        # CALCULATE RESULT COUNT
        # ----------------------------------------------------

        if isinstance(tool_result, list):

            result_count = len(tool_result)

        else:

            result_count = 1


        # ----------------------------------------------------
        # RECORD TOOL COMPLETION
        # ----------------------------------------------------

        tool_activity.append({

            "name": function_name,

            "status": "done",

            "detail": (
                f"Completed successfully — "
                f"{result_count} result(s)"
            )

        })


        # ----------------------------------------------------
        # ADD TOOL RESULT TO CONVERSATION
        # ----------------------------------------------------

        messages.append(

            {

                "role": "tool",

                "tool_call_id": tool_call.id,

                "content": json.dumps(
                    tool_result
                )

            }

        )


    # --------------------------------------------------------
    # SECOND MODEL REQUEST
    #
    # IMPORTANT:
    # Tools MUST be supplied here as well because the
    # conversation now contains tool calls and tool responses.
    # --------------------------------------------------------

    second_response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=messages,

        tools=TOOLS,

        tool_choice="auto"

    )


    final_response = (
        second_response
        .choices[0]
        .message
        .content
    )


    # --------------------------------------------------------
    # RETURN FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "response": (
            final_response
            or "I was unable to generate a final response."
        ),

        "tool_calls": tool_activity

    }