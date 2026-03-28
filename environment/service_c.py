"""
Service C - Data Service
========================
Provides core data storage and retrieval functionality.
Called by Service B as part of the request processing chain.

Port: 5002
"""
import os
import sys
import logging
from flask import Flask, request, jsonify
import requests as http_requests

from config import LOG_LEVEL
from service_a import validate_request

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('service_c')

app = Flask(__name__)

DATA_STORE = {
    "records": [
        {"id": 1, "value": "alpha", "category": "primary", "active": True},
        {"id": 2, "value": "beta", "category": "secondary", "active": False},
        {"id": 3, "value": "gamma", "category": "primary", "active": True},
        {"id": 4, "value": "delta", "category": "tertiary", "active": True},
    ],
    "metadata": {
        "version": "2.0",
        "last_updated": "2024-01-15T10:30:00Z",
        "total_records": 4
    }
}


def format_response(data, service_name):
    return {
        "source": service_name,
        "data": data,
        "timestamp": "2024-01-15T10:30:00Z"
    }


@app.before_request
def log_and_validate():
    logger.debug(f"Received: {request.method} {request.path}")


@app.route('/')
def index():
    logger.info("Service C index endpoint called")
    return jsonify({
        "service": "service_c",
        "status": "service_c_ok",
        "version": "2.0.0"
    })


@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "service_c"}), 200


@app.route('/api/data')
def get_data():
    logger.info("Data endpoint called")

    if not validate_request(request):
        logger.warning("Unauthorized request to /api/data")
        return jsonify({"error": "unauthorized"}), 401

    active_count = sum(1 for r in DATA_STORE["records"] if r["active"])
    logger.info(f"Request validated, returning data ({active_count} active records)")

    return f"service_c_ok: {active_count} active records available", 200


@app.route('/api/records')
def get_records():
    return jsonify(format_response(DATA_STORE["records"], "service_c"))


@app.route('/api/metadata')
def get_metadata():
    return jsonify(format_response(DATA_STORE["metadata"], "service_c"))


if __name__ == '__main__':
    logger.info("Starting Service C (Data Service) on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)
