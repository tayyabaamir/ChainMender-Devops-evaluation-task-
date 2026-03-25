"""
Service A - API Gateway
=======================
Entry point for external requests. Forwards processing requests
to Service B and aggregates responses from the service chain.

Port: 5000
"""
import os
import sys
import logging
from flask import Flask, request, jsonify
import requests as http_requests

from config import SERVICE_B_URL, REQUEST_TIMEOUT, LOG_LEVEL
from service_c import format_response  # Shared response formatter utility

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('service_a')

app = Flask(__name__)


def validate_request(req):
    """
    Validates incoming HTTP requests.
    Checks for required authentication headers on protected endpoints.
    Returns True if request is allowed, False otherwise.
    """
    # Public endpoints accessible without authentication
    public_paths = ['/', '/health']
    if req.path in public_paths:
        return True

    # Check for service auth token
    auth_token = req.headers.get('X-Auth-Token')
    if auth_token and len(auth_token) > 0:
        return True

    # Allow internal inter-service requests
    if req.headers.get('X-Internal-Request') == 'true':
        return True

    return False


@app.before_request
def before_request_handler():
    """Log all incoming requests for debugging"""
    logger.debug(f"Incoming request: {request.method} {request.path}")


@app.route('/')
def index():
    """Root endpoint - returns service status"""
    logger.info("Service A index endpoint called")
    return jsonify(format_response({
        "service": "service_a",
        "status": "service_a_ok",
        "version": "1.2.0"
    }, "service_a"))


@app.route('/health')
def health():
    """Health check endpoint for load balancer and monitoring"""
    return jsonify({"status": "healthy", "service": "service_a"}), 200


@app.route('/request_chain')
def request_chain():
    """
    Initiates a request chain through all microservices.
    Flow: Client -> Service A -> Service B -> Service C
    Returns aggregated responses from all services in the chain.
    """
    logger.info("Initiating request chain: A -> B -> C")

    try:
        # Forward request to Service B for processing
        response = http_requests.get(
            f"{SERVICE_B_URL}/api/v1/process",
            timeout=REQUEST_TIMEOUT,
            headers={
                "X-Auth-Token": "internal-svc-a-token",
                "X-Internal-Request": "true",
                "X-Request-Source": "service_a"
            }
        )
        response.raise_for_status()

        chain_data = response.json()

        # Build aggregated response
        result = {
            "status": "service_a_ok",
            "service_a_ok": True,
            "downstream": chain_data
        }

        # Propagate downstream status flags for easy checking
        if chain_data.get("service_b_ok"):
            result["service_b_ok"] = True
        downstream_c = chain_data.get("downstream", {})
        if downstream_c.get("service_c_ok"):
            result["service_c_ok"] = True

        logger.info("Request chain completed successfully")
        return jsonify(result)

    except http_requests.exceptions.ConnectionError as e:
        logger.error(f"Connection to Service B failed: {e}")
        return jsonify({"error": "service_b_unreachable", "details": str(e)}), 502

    except http_requests.exceptions.Timeout:
        logger.error("Service B request timed out")
        return jsonify({"error": "service_b_timeout"}), 504

    except ValueError as e:
        logger.error(f"Invalid JSON response from Service B: {e}")
        return jsonify({"error": "invalid_response_from_service_b"}), 502

    except Exception as e:
        logger.error(f"Unexpected error in request chain: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Service A (API Gateway) on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
