## Files
auth_api_mock.py
banking_api_mock.py
mcp_server.py
ollama_mcp_client.py

### Install Flask and Requests
pip install Flask requests

### Run the Mock APIs and MCP Server (in separate terminal windows):
#### Terminal 1 (Auth API):
python auth_api_mock.py

You should see output indicating Flask is running on http://127.0.0.1:5000.

#### Terminal 2 (Banking API):
python banking_api_mock.py

You should see output indicating Flask is running on http://127.0.0.1:5001.

#### Terminal 3 (MCP Server):
python mcp_server.py

You should see output indicating Flask is running on http://127.0.0.1:5002.

#### Run the Ollama MCP Client Simulation (in a new terminal window) Terminal 4 (Ollama Client):

python ollama_mcp_client.py

**This script will simulate the LLM's interaction, including a mock login, and then make calls to your running MCP Server. Observe the output in all four terminals to see the full flow.**

## Explanation of the Code
### auth_api_mock.py:
- Simulates your existing authentication service. It has a hardcoded MOCK_USERS dictionary.
- The /auth/login endpoint takes a username and password, and if valid, issues a simple UUID-based "token" and returns a user_id.
- The /auth/validate_token endpoint takes a token and returns the associated user_id if valid.
- This represents the API your client applications currently use for authentication.

### banking_api_mock.py:
- Simulates your existing banking services. It has hardcoded MOCK_ACCOUNTS and mock_transactions.
- banking/accounts/<user_id>/balance and /banking/transactions/<user_id>/recent are examples of your core banking APIs. In a real system, these would be protected by your API Gateway and expect a valid authentication context (which the MCP Server will provide).

### mcp_server.py:
- This is your central MCP implementation. It runs on port 5002.
- The /mcp/invoke endpoint is where your LLM (as an MCP client) sends its requests.
- User Context Validation: It first extracts the token or user_id from the user_context in the incoming MCP request. It then makes an internal HTTP call to your auth_api_mock.py's /auth/validate_token endpoint. This is how it leverages your existing authentication infrastructure.
- Tool Invocation: Based on the tool_name provided by the LLM, it then makes another internal HTTP call to the appropriate endpoint on your banking_api_mock.py.
- Response Formatting: It takes the response from the banking API and wraps it in a simplified MCP response format (status, data, message) before sending it back to the LLM.

### ollama_mcp_client.py:
- This script acts as a simplified representation of how an Ollama LLM would interact.
- It first simulates a user logging in to get a user_auth_token and user_id (just like a real client app would).
- The simulate_ollama_query function mimics the LLM's decision-making process: it analyzes the user_query to determine if a banking tool is needed.
- If a tool is needed, it constructs the mcp_request_payload and sends it to your mcp_server.py.
- It then "interprets" the mcp_response and generates a natural language response for the user. This "interpretation" part is where the LLM's generative capabilities would truly shine in a real scenario.

**Above  setup demonstrates how your MCP Server becomes the crucial intermediary, allowing your LLMs to securely and contextually interact with your established banking APIs without needing to directly integrate with each one or manage complex authentication flows themselves. The existing authentication API remains the authority for user identity, and the MCP Server acts as the trusted bridge.**


## Understanding the flow of communication in our MCP integration.

### 1. `OLLAMA_API_URL = "http://localhost:11434/api/generate"`

* **Who is calling it?**
    * The `ollama_mcp_client_simulation.py` script. Specifically, the `call_ollama_llm` function within this script.
* **What is its purpose?**
    * This URL points to the **local Ollama LLM server**. The `ollama_mcp_client_simulation.py` script acts as the client to this LLM. It sends the user's query (along with the tool-use prompt) to Ollama to get a response. This response is then analyzed to determine if a banking tool needs to be invoked or if a direct natural language answer can be provided.

### 2. `AUTH_API_BASE_URL = "http://127.0.0.1:5000"`

* **Who is calling it?**
    * **Caller 1 (Simulated Client Application):** The `ollama_mcp_client_simulation.py` script, specifically in its `if __name__ == '__main__':` block.
        * **Purpose:** This call simulates a **traditional client application** (e.g., your mobile banking app or web portal) performing an initial user login. It calls `http://127.0.0.1:5000/auth/login` to obtain an authentication token and the user's ID. This is a one-time setup step in our simulation to get a valid user context.
    * **Caller 2 (Your MCP Server):** The `mcp_server.py` script.
        * **Purpose:** This is a critical internal call. When the `mcp_server.py` receives a request from the LLM (which includes user context like a token or user ID), it calls `http://127.0.0.1:5000/auth/validate_token` on your existing authentication API. The purpose is to **validate the user's authentication token or user ID** and ensure that the AI is acting on behalf of a legitimate and currently authenticated user. This leverages your existing security infrastructure.

### 3. `BANKING_API_BASE_URL = "http://127.00.0.1:5001"`

* **Who is calling it?**
    * **Your MCP Server:** The `mcp_server.py` script.
* **What is its purpose?**
    * This URL points to your **existing core banking functionalities** (e.g., endpoints for getting account balances, recent transactions, initiating payments, etc.). After the `mcp_server.py` has successfully validated the user's context (by calling the `AUTH_API_BASE_URL`), it then calls the appropriate endpoint on `http://127.0.0.1:5001` (e.g., `/banking/accounts/{user_id}/balance`) to retrieve the specific financial data or perform the requested banking action.

### 4. `MCP_SERVER_URL = "http://127.0.0.1:5002/mcp/invoke"`

* **Who is calling it?**
    * **The Ollama LLM Client Simulation:** The `ollama_mcp_client.py` script, specifically the `process_user_query_with_ollama` function.
* **What is its purpose?**
    * This is the endpoint of **your newly implemented Model Context Provider (MCP) server**. When the `ollama_mcp_client_simulation.py` (acting as the LLM's orchestration layer) determines that the LLM needs to use an external banking tool to fulfill a user's request, it sends a structured MCP request (a JSON payload specifying the `tool_name` and `parameters`) to this URL. This is the entry point for AI-driven, contextual interactions with your banking services.

In summary, the `ollama_mcp_client_simulation.py` (representing your LLM integration) is the primary caller of the `OLLAMA_API_URL` and `MCP_SERVER_URL`. The `mcp_server.py` then acts as the central orchestrator, calling your `AUTH_API_BASE_URL` for user validation and your `BANKING_API_BASE_URL` for core banking operations.
