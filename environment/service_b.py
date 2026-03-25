"""
Service B - Processing Service
===============================
Receives requests from Service A and delegates data retrieval
to Service C. Applies processing logic and returns results.

Port: 5001
"""
import os
import sys
import logging
from flask import Flask, request, jsonify
import requests as http_requests

from config import SERVICE_C_URL, REQUEST_TIMEOUT, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('service_b')

app = Flask(__name__)


@app.before_request
def log_request():
    """Log incoming requests for debugging and tracing"""
    logger.debug(f"Received: {request.method} {request.path}")
    logger.debug(f"From: {request.headers.get('X-Request-Source', 'unknown')}")


@app.route('/')
def index():
    """Root endpoint - returns service status"""
    return jsonify({
        "service": "service_b",
        "status": "service_b_ok",
        "version": "1.1.0"
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "service_b"}), 200


@app.route('/api/process')
def process_request():
    """
    Process endpoint - receives requests from Service A
    and fetches data from Service C.

    Expects Service C to return a JSON response which is
    then wrapped with Service B's own status information.
    """
    logger.info("Processing request - fetching data from Service C")

    try:
        # Forward authentication headers to downstream service
        downstream_headers = {
            "X-Auth-Token": request.headers.get("X-Auth-Token", ""),
            "X-Internal-Request": "true",
            "X-Request-Source": "service_b"
        }

        # Call Service C data endpoint
        response = http_requests.get(
            f"{SERVICE_C_URL}/api/data",
            timeout=REQUEST_TIMEOUT,
            headers=downstream_headers
        )
        response.raise_for_status()

        # Parse JSON response from Service C
        service_c_data = response.json()

        result = {
            "status": "service_b_ok",
            "service_b_ok": True,
            "processed": True,
            "downstream": service_c_data
        }

        logger.info("Successfully processed request with Service C data")
        return jsonify(result)

    except http_requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to Service C at {SERVICE_C_URL}: {e}")
        return jsonify({
            "error": "service_c_unreachable",
            "service_c_url": SERVICE_C_URL,
            "details": str(e)
        }), 502

    except http_requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to Service C at {SERVICE_C_URL}")
        return jsonify({"error": "service_c_timeout"}), 504

    except ValueError as e:
        logger.error(f"Failed to parse Service C response as JSON: {e}")
        return jsonify({
            "error": "invalid_json_from_service_c",
            "details": str(e)
        }), 502

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info(f"Starting Service B (Processing) on port 5001")
    logger.info(f"Configured Service C URL: {SERVICE_C_URL}")
    app.run(host='0.0.0.0', port=5001, debug=False)
