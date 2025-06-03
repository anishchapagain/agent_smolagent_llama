# banking_api_mock.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock user account data
MOCK_ACCOUNTS = {
    "user_12345": {
        "accounts": [
            {"account_id": "ACC001", "type": "Savings", "balance": 15000.50, "currency": "USD"},
            {"account_id": "ACC002", "type": "Checking", "balance": 5000.00, "currency": "USD"}
        ]
    },
    "user_67890": {
        "accounts": [
            {"account_id": "ACC003", "type": "Savings", "balance": 2500.75, "currency": "USD"}
        ]
    }
}

@app.route('/banking/accounts/<user_id>/balance', methods=['GET'])
def get_account_balance(user_id):
    """
    Simulates getting account balance for a user.
    OpenAPI Spec equivalent:
    paths:
      /banking/accounts/{user_id}/balance:
        get:
          summary: Get account balance for a specific user
          parameters:
            - in: path
              name: user_id
              schema: {type: string}
              required: true
          responses:
            '200':
              description: Account balances retrieved successfully
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      accounts:
                        type: array
                        items:
                          type: object
                          properties:
                            account_id: {type: string}
                            type: {type: string}
                            balance: {type: number}
                            currency: {type: string}
            '404':
              description: User or accounts not found
    """
    # In a real scenario, this would involve token validation from API Gateway
    # For this mock, we assume the user_id is already validated by MCP Server
    accounts_data = MOCK_ACCOUNTS.get(user_id)
    if accounts_data:
        return jsonify(accounts_data), 200
    return jsonify({"message": "User or accounts not found"}), 404

@app.route('/banking/transactions/<user_id>/recent', methods=['GET'])
def get_recent_transactions(user_id):
    """
    Simulates getting recent transactions for a user.
    OpenAPI Spec equivalent:
    paths:
      /banking/transactions/{user_id}/recent:
        get:
          summary: Get recent transactions for a specific user
          parameters:
            - in: path
              name: user_id
              schema: {type: string}
              required: true
          responses:
            '200':
              description: Recent transactions retrieved successfully
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      transactions:
                        type: array
                        items:
                          type: object
                          properties:
                            transaction_id: {type: string}
                            date: {type: string}
                            amount: {type: number}
                            description: {type: string}
            '404':
              description: User or transactions not found
    """
    # Mock transaction data (simplified)
    mock_transactions = {
        "user_12345": [
            {"transaction_id": "TRN001", "date": "2025-05-30", "amount": -100.00, "description": "Grocery Store"},
            {"transaction_id": "TRN002", "date": "2025-05-29", "amount": 500.00, "description": "Salary Deposit"}
        ],
        "user_67890": [
            {"transaction_id": "TRN003", "date": "2025-05-28", "amount": -25.50, "description": "Coffee Shop"}
        ]
    }
    transactions_data = mock_transactions.get(user_id)
    if transactions_data:
        return jsonify({"transactions": transactions_data}), 200
    return jsonify({"message": "User or transactions not found"}), 404

if __name__ == '__main__':
    print("Starting mock banking API on port 5001..banking_api_mock.py.")
    app.run(port=5001, debug=True)