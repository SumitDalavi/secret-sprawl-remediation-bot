from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Simulated state of valid tokens in the Identity Provider
VALID_TOKENS = {
    "AKIAIOSFODNN7EXAMPLE": {"type": "AWS", "user": "dev-team-ci", "status": "active"},
    "ghp_16C7e42J09L908C3X43M9R64O29T96EXAMPLE": {"type": "GitHub", "user": "ci-bot", "status": "active"}
}

@app.route('/api/v1/revoke', methods=['POST'])
def revoke_token():
    data = request.json
    secret = data.get('secret')
    rule_id = data.get('rule_id')

    if not secret:
        return jsonify({"error": "Missing 'secret' in payload"}), 400

    app.logger.info(f"Received revocation request for secret (Rule: {rule_id})")

    if secret in VALID_TOKENS:
        if VALID_TOKENS[secret]['status'] == 'revoked':
            return jsonify({"status": "already_revoked", "message": "Token was already revoked."}), 200
        
        # Simulate revocation
        VALID_TOKENS[secret]['status'] = 'revoked'
        app.logger.info(f"SUCCESS: Revoked {VALID_TOKENS[secret]['type']} token for user {VALID_TOKENS[secret]['user']}.")
        return jsonify({
            "status": "success", 
            "message": "Token successfully revoked.",
            "details": VALID_TOKENS[secret]
        }), 200
    else:
        app.logger.warning("FAILED: Token not found in Identity Provider or is a mock/test key.")
        return jsonify({"status": "not_found", "message": "Token not found."}), 404

if __name__ == '__main__':
    # Run on port 5000
    app.run(port=5000)
