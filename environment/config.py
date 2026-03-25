"""
Shared configuration for microservices.
Centralizes port assignments, service URLs, and runtime settings.
"""
import os

# Service port assignments
SERVICE_A_PORT = int(os.environ.get('SERVICE_A_PORT', 5000))
SERVICE_B_PORT = int(os.environ.get('SERVICE_B_PORT', 5001))
SERVICE_C_PORT = int(os.environ.get('SERVICE_C_PORT', 5003))  # Default port for Service C

# Construct service URLs from ports
SERVICE_A_URL = f"http://localhost:{SERVICE_A_PORT}"
SERVICE_B_URL = f"http://localhost:{SERVICE_B_PORT}"
SERVICE_C_URL = f"http://localhost:{SERVICE_C_PORT}"

# Request settings
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 10))

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
