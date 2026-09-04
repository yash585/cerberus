import os
import json
from groq import Groq
from dotenv import load_dotenv

from tools.incidents import search_incidents, get_incident
from tools.assets import search_assets, get_asset
from tools.knowledge_base import search_knowledge_base


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


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

Use tools when the user asks for information that may exist in the
internal SOC data.

Always provide accurate and concise security-focused responses.

Do not claim to have performed actions that you have not actually performed.
"""


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_incidents",
            "description": "Search security incidents using keywords, severity, status, asset name, or incident details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding relevant security incidents."
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
            "description": "Retrieve complete details for a specific incident using its incident ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "The incident ID, for example INC-2026-001."
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
            "description": "Search assets using hostname, IP address, department, operating system, or criticality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding relevant assets."
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
            "description": "Retrieve complete information for a specific asset using its hostname.",
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
            "description": "Search the internal cybersecurity knowledge base for security procedures, detection techniques, and incident response guidance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for the security knowledge base."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


AVAILABLE_TOOLS = {
    "search_incidents": search_incidents,
    "get_incident": get_incident,
    "search_assets": search_assets,
    "get_asset": get_asset,
    "search_knowledge_base": search_knowledge_base
}


def run_agent(user_message: str) -> str:

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

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:

        messages.append(response_message)

        for tool_call in response_message.tool_calls:

            function_name = tool_call.function.name

            function_args = json.loads(
                tool_call.function.arguments
            )

            function_to_call = AVAILABLE_TOOLS[function_name]

            tool_result = function_to_call(
                **function_args
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                }
            )

        second_response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages
        )

        return second_response.choices[0].message.content

    return response_message.content