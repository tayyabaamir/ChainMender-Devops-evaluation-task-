"""
Shared configuration for microservices.
Centralizes port assignments, service URLs, and runtime settings.
"""
import os

SERVICE_A_PORT = int(os.environ.get('SERVICE_A_PORT', 5000))
SERVICE_B_PORT = int(os.environ.get('SERVICE_B_PORT', 5001))
SERVICE_C_PORT = int(os.environ.get('SERVICE_C_PORT', 5003))

SERVICE_A_URL = f"http://localhost:{SERVICE_A_PORT}"
SERVICE_B_URL = f"http://localhost:{SERVICE_B_PORT}"
SERVICE_C_URL = f"http://localhost:{SERVICE_C_PORT}"

REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 10))

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
