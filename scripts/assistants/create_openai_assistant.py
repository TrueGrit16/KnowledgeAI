import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# Assistant tool definition for webhook-style call
tool_def = {
    "type": "function",
    "function": {
        "name": "run_agent_task",
        "description": "Call the RCA, SOP, or Ticket agent",
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["rca", "sop", "ticket"]
                },
                "payload": {
                    "type": "object",
                    "description": "The actual query (e.g. topic string)"
                }
            },
            "required": ["mode", "payload"]
        }
    }
}

assistant = openai.beta.assistants.create(
    name="KnowledgeOps Assistant",
    instructions="""You help users by calling `run_agent_task` to route queries to internal RCA, SOP, and Ticket agents.""",
    tools=[tool_def],
    model="gpt-4-1106-preview"
)

print("✅ Assistant created successfully!")
print("🆔 Assistant ID:", assistant.id)