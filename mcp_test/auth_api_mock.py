# auth_api_mock.py
from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# In a real system, this would be a database of users and their hashed passwords
MOCK_USERS = {
    "john.doe": {"password": "password123", "user_id": "user_12345"},
    "jane.smith": {"password": "securepass", "user_id": "user_67890"}
}

# In a real system, tokens would be signed JWTs or similar
MOCK_TOKENS = {} # token: user_id mapping

@app.route('/auth/login', methods=['POST'])
def login():
    """
    Simulates user login and token issuance.
    OpenAPI Spec equivalent:
    paths:
      /auth/login:
        post:
          summary: Authenticate user and get a token
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    username: {type: string}
                    password: {type: string}
          responses:
            '200':
              description: Authentication successful
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      token: {type: string}
                      user_id: {type: string}
            '401':
              description: Invalid credentials
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in MOCK_USERS and MOCK_USERS[username]['password'] == password:
        token = str(uuid.uuid4()) # Generate a simple UUID token
        user_id = MOCK_USERS[username]['user_id']
        MOCK_TOKENS[token] = user_id
        return jsonify({"token": token, "user_id": user_id}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/auth/validate_token', methods=['POST'])
def validate_token():
    """
    Simulates token validation and returns user details.
    OpenAPI Spec equivalent:
    paths:
      /auth/validate_token:
        post:
          summary: Validate an authentication token
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    token: {type: string}
          responses:
            '200':
              description: Token is valid
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      user_id: {type: string}
            '401':
              description: Invalid or expired token
    """
    data = request.get_json()
    token = data.get('token')
    
    user_id = MOCK_TOKENS.get(token)
    if user_id:
        return jsonify({"user_id": user_id}), 200
    return jsonify({"message": "Invalid or expired token"}), 401

if __name__ == '__main__':
    print("Starting mock authentication API on port 5000..auth_api_mock.")
    app.run(port=5000, debug=True)