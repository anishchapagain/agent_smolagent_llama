# ollama_mcp_client_simulation.py
import requests
import json
import re # For regex to extract JSON from LLM response
from config import OLLAMA_API_URL, OLLAMA_MODEL_NAME, AUTH_API_BASE_URL, MCP_SERVER_URL, LLM_TOOL_PROMPT_TEMPLATE

def call_ollama_llm(prompt):
    """
    Sends a prompt to the Ollama LLM and returns its raw response.
    """
    headers = {'Content-Type': 'application/json'}
    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False, # We want the full response at once
        "options": {
            "temperature": 0.0, # Make LLM deterministic for tool calling
            "num_predict": 200 # Increased prediction length slightly for more robust JSON output
        }
    }
    try:
        response = requests.post(OLLAMA_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama LLM: {e}")
        return None

def parse_llm_response_for_tool_call(llm_response):
    """
    Attempts to parse the LLM's response for a JSON tool call.
    Returns the parsed dictionary if valid, otherwise None.
    """
    # Try to find any JSON-like structure
    # Use re.DOTALL to match across multiple lines if LLM output is formatted
    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
    
    if json_match:
        json_string = json_match.group(0)
        print(f"DEBUG: Found potential JSON string: '{json_string}'")
        try:
            # Attempt to load the matched string as JSON
            tool_call = json.loads(json_string)
            
            # Ensure it's a dictionary and contains the expected keys
            if isinstance(tool_call, dict) and "tool_name" in tool_call and "parameters" in tool_call:
                print(f"DEBUG: Successfully parsed valid tool call JSON: {tool_call}")
                return tool_call
            else:
                # If it's JSON but not the expected tool call format (missing keys or wrong type)
                print(f"DEBUG: JSON found but not valid tool call format (missing 'tool_name' or 'parameters' or not a dict): {tool_call}")
                return None
        except json.JSONDecodeError as e:
            # If it's not valid JSON
            print(f"DEBUG: Regex matched, but not valid JSON: '{json_string}' Error: {e}")
            return None
    else:
        print("DEBUG: No JSON-like structure found in LLM response.")
    # No JSON-like structure found
    return None

def process_user_query_with_ollama(user_query, user_auth_token=None, user_id=None):
    """
    Orchestrates the interaction: LLM -> MCP Server -> Banking API.
    """
    print(f"\n--- Processing User Query: '{user_query}' ---")
    
    # 1. Prepare prompt for LLM to guide tool usage
    llm_prompt = LLM_TOOL_PROMPT_TEMPLATE.format(user_query=user_query)
    print(f"DEBUG: Sending prompt to Ollama LLM...{llm_prompt.strip()}")
    
    # 2. Call Ollama LLM
    llm_raw_response = call_ollama_llm(llm_prompt)
    if llm_raw_response is None:
        return "I'm sorry, I couldn't connect to the AI assistant. Please check Ollama server."

    print(f"DEBUG: Ollama LLM Raw Response: '{llm_raw_response.strip()}'")

    # 3. Parse LLM response for tool call
    tool_call_payload = parse_llm_response_for_tool_call(llm_raw_response)
    print(f"DEBUG: Parsed tool_call_payload: {tool_call_payload} (Type: {type(tool_call_payload)})")

    if tool_call_payload:
        # LLM wants to use a tool, prepare MCP request
        # Using .get() ensures no KeyError even if keys are unexpectedly missing,
        # but parse_llm_response_for_tool_call should prevent this now.
        tool_name = tool_call_payload.get("tool_name")
        parameters = tool_call_payload.get("parameters", {})

        if tool_name is None:
            # This case should ideally be caught by parse_llm_response_for_tool_call,
            # but as a fallback, if tool_name is still missing, treat as natural language.
            print("DEBUG: tool_name is None after parsing, falling back to natural language.")
            return llm_raw_response # Fallback to natural language if tool_name is truly missing

        mcp_request_payload = {
            "user_context": {
                "token": user_auth_token,
                "user_id": user_id
            },
            "tool_name": tool_name,
            "parameters": parameters
        }
        
        print(f"DEBUG: LLM decided to call tool: '{tool_name}'")
        print(f"DEBUG: Sending MCP request to server: {json.dumps(mcp_request_payload, indent=2)}")

        try:
            # 4. Call MCP Server
            print("DEBUG: Sending request to MCP Server...")
            mcp_response_raw = requests.post(MCP_SERVER_URL, json=mcp_request_payload)
            mcp_response_raw.raise_for_status()
            mcp_response = mcp_response_raw.json()

            print(f"DEBUG: Received MCP response: {json.dumps(mcp_response, indent=2)}")

            # 5. Interpret MCP response and generate final user-facing response
            if mcp_response.get("status") == "success":
                data = mcp_response.get("data")
                if tool_name == "get_account_balance":
                    accounts = data.get("accounts", [])
                    if accounts:
                        balance_summary = ", ".join([
                            f"{acc['type']} ({acc['account_id']}): {acc['balance']} {acc['currency']}"
                            for acc in accounts
                        ])
                        return f"Here are your current balances: {balance_summary}."
                    else:
                        return "I couldn't find any account balances for you."
                elif tool_name == "get_recent_transactions":
                    transactions = data.get("transactions", [])
                    if transactions:
                        transaction_summary = "\n".join([
                            f"  - {t['date']}: {t['description']} ({t['amount']} {t['currency'] if 'currency' in t else 'USD'})"
                            for t in transactions[:3] # Show top 3 for brevity
                        ])
                        return f"Here are your most recent transactions:\n{transaction_summary}\nFor more, please check your banking app."
                    else:
                        return "I couldn't find any recent transactions for you."
                else:
                    return f"Successfully executed tool '{tool_name}', but I'm not sure how to summarize the response: {data}"
            else:
                return f"I encountered an error while trying to get that information: {mcp_response.get('message', 'Unknown error')}"

        except requests.exceptions.ConnectionError:
            return "I'm sorry, I cannot connect to the banking services at the moment. Please ensure the MCP server is running."
        except requests.exceptions.RequestException as e:
            return f"An unexpected error occurred while processing your request through MCP: {e}"
    else:
        # LLM did not output a tool call, treat as natural language response
        print("DEBUG: LLM did not output a tool call, returning raw LLM response.")
        return llm_raw_response # The LLM's direct response to the user query

if __name__ == '__main__':
    # --- First, simulate a login to get a token ---
    print("--- Simulating User Login ---")
    login_payload = {"username": "john.doe", "password": "password123"}
    try:
        login_response = requests.post(f"{AUTH_API_BASE_URL}/auth/login", json=login_payload)
        login_response.raise_for_status()
        login_data = login_response.json()
        user_token = login_data.get("token")
        logged_in_user_id = login_data.get("user_id")
        print(f"Login successful. User ID: {logged_in_user_id}, Token: {user_token[:8]}...")
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        user_token = None
        logged_in_user_id = None

    if user_token and logged_in_user_id:
        # --- Now, simulate LLM queries with the obtained context ---
        print("\n--- Simulating LLM Queries with Authenticated Context ---")
        
        # Query 1: Get balance (should trigger tool)
        response_llm_1 = process_user_query_with_ollama("What's my current account balance?", user_auth_token=user_token, user_id=logged_in_user_id)
        print(f"\nLLM Final Response: {response_llm_1}")

        # # Query 2: Get recent transactions (should trigger tool)
        # response_llm_2 = process_user_query_with_ollama("Can you show me my latest transactions?", user_auth_token=user_token, user_id=logged_in_user_id)
        # print(f"\nLLM Final Response: {response_llm_2}")
        
        # # Query 3: Something the LLM can answer directly (should NOT trigger tool)
        # response_llm_3 = process_user_query_with_ollama("What is the capital of France?", user_auth_token=user_token, user_id=logged_in_user_id)
        # print(f"\nLLM Final Response: {response_llm_3}")

        # # Query 4: Simulate invalid token (should trigger tool, but MCP will reject)
        # response_llm_4 = process_user_query_with_ollama("What's my balance?", user_auth_token="invalid_token_123", user_id=logged_in_user_id)
        # print(f"\nLLM Final Response: {response_llm_4}")

        # # Query 5: A more complex query that might test LLM's understanding (should trigger tool)
        # response_llm_5 = process_user_query_with_ollama("Could you give me an overview of my financial standing?", user_auth_token=user_token, user_id=logged_in_user_id)
        # print(f"\nLLM Final Response: {response_llm_5}")

    else:
        print("\nSkipping LLM simulation as login failed.")