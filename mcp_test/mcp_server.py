# mcp_server.py
from flask import Flask, request, jsonify
import requests # Used to make HTTP requests to mock APIs

app = Flask(__name__)

# Configuration for mock APIs (replace with your actual API Gateway/service URLs)
AUTH_API_BASE_URL = "http://127.0.0.1:5000"
BANKING_API_BASE_URL = "http://127.00.0.1:5001"

@app.route('/mcp/invoke', methods=['POST'])
def invoke_mcp_tool():
    """
    MCP Server endpoint to receive requests from an LLM (MCP Client).
    It validates user context and calls the appropriate banking service.

    Expected MCP Request Structure (simplified for demonstration):
    {
        "user_context": {
            "token": "user_auth_token_from_client_app",
            "user_id": "user_id_if_available"
        },
        "tool_name": "get_account_balance" or "get_recent_transactions",
        "parameters": {
            "account_id": "ACC001" (optional, depending on tool)
        }
    }

    MCP Response Structure (simplified):
    {
        "status": "success" or "error",
        "data": { ... tool specific data ... },
        "message": "..."
    }
    """
    mcp_request = request.get_json()
    
    user_context = mcp_request.get('user_context', {})
    tool_name = mcp_request.get('tool_name')
    parameters = mcp_request.get('parameters', {})

    print(f"Received MCP request: {mcp_request} {user_context} {tool_name} {parameters}")
    # 1. Validate User Context using Existing Authentication API
    user_id = None
    if 'token' in user_context:
        try:
            auth_response = requests.post(
                f"{AUTH_API_BASE_URL}/auth/validate_token",
                json={"token": user_context['token']}
            )
            auth_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            auth_data = auth_response.json()
            user_id = auth_data.get('user_id')
        except requests.exceptions.RequestException as e:
            print(f"Authentication API error: {e}")
            return jsonify({
                "status": "error",
                "message": "Authentication failed or token invalid."
            }), 401
    elif 'user_id' in user_context:
        # If client directly provides user_id, you'd need another validation mechanism
        # or assume it's pre-validated by the client application's backend.
        # For this example, we'll use it directly if token is not present.
        user_id = user_context['user_id']
    
    if not user_id:
        return jsonify({
            "status": "error",
            "message": "User context (token or user_id) is missing or invalid."
        }), 400

    # 2. Invoke Banking Service based on tool_name and validated user_id
    if tool_name == "get_account_balance":
        try:
            banking_response = requests.get(
                f"{BANKING_API_BASE_URL}/banking/accounts/{user_id}/balance"
            )
            banking_response.raise_for_status()
            return jsonify({
                "status": "success",
                "data": banking_response.json()
            }), 200
        except requests.exceptions.RequestException as e:
            print(f"Banking API error for get_account_balance: {e}")
            return jsonify({
                "status": "error",
                "message": f"Failed to retrieve account balance: {e}"
            }), 500
    
    elif tool_name == "get_recent_transactions":
        try:
            banking_response = requests.get(
                f"{BANKING_API_BASE_URL}/banking/transactions/{user_id}/recent"
            )
            banking_response.raise_for_status()
            return jsonify({
                "status": "success",
                "data": banking_response.json()
            }), 200
        except requests.exceptions.RequestException as e:
            print(f"Banking API error for get_recent_transactions: {e}")
            return jsonify({
                "status": "error",
                "message": f"Failed to retrieve recent transactions: {e}"
            }), 500
    
    else:
        return jsonify({
            "status": "error",
            "message": f"Unknown tool: {tool_name}"
        }), 404

if __name__ == '__main__':
    print("Starting MCP Server on port 5002...mcp_server.py")
    app.run(port=5002, debug=True)