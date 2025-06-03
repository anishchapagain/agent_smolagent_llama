# config.py

# Ollama LLM Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate" # Default Ollama API endpoint
OLLAMA_MODEL_NAME = "llama3.2:latest"

# Your Mock API Endpoints (replace with your actual API Gateway/service URLs in a real scenario)
AUTH_API_BASE_URL = "http://127.0.0.1:5000" # banking_api_mock
BANKING_API_BASE_URL = "http://127.0.0.1:5001" # auth_api_mock
MCP_SERVER_URL = "http://127.0.0.1:5002/mcp/invoke" # mcp_server

# Prompt template for the LLM to guide it towards tool usage
# This is crucial for getting the LLM to output structured data for tool calls.
# We instruct the LLM to output a JSON object if a tool is needed.
LLM_TOOL_PROMPT_TEMPLATE = """
You are a helpful financial assistant. Your primary goal is to assist the user with banking queries.
You have access to the following tools:

1.  **get_account_balance**: Use this tool to retrieve the current balances of all accounts for the authenticated user.
    Parameters: None
    Example usage: {{"tool_name": "get_account_balance", "parameters": {{}}}}

2.  **get_recent_transactions**: Use this tool to retrieve recent transactions for the authenticated user.
    Parameters: None
    Example usage: {{"tool_name": "get_recent_transactions", "parameters": {{}}}}

If the user asks a question that requires one of these tools, respond ONLY with a JSON object containing the "tool_name" and "parameters" as shown in the examples above. DO NOT include any other text.
If the user's query does NOT require a tool, respond with a natural language answer.

User Query: {user_query}
"""