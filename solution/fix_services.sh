#!/bin/bash
# Fix all microservice dependency and configuration issues
# Fixes applied:
#   1. Resolve circular import between service_a and service_c
#   2. Correct SERVICE_C_PORT in config.py (5003 -> 5002)
#   3. Fix endpoint path in service_a (/api/v1/process -> /api/process)
#   4. Fix response format in service_c /api/data (plain text -> JSON)
set -e

cd /app

# ==============================================================
# Fix 1: Resolve circular import by extracting shared utilities
# ==============================================================
# service_a imports format_response from service_c
# service_c imports validate_request from service_a
# This creates a circular import that crashes both services.
# Solution: extract both functions into a new utils.py module.

cat > /app/utils.py << 'UTILS_EOF'
"""
Shared utilities for microservices.
Extracted to resolve circular import between service_a and service_c.
"""


def validate_request(req):
    """
    Validates incoming HTTP requests.
    Checks for required authentication headers on protected endpoints.
    Returns True if request is allowed, False otherwise.
    """
    public_paths = ['/', '/health']
    if req.path in public_paths:
        return True

    auth_token = req.headers.get('X-Auth-Token')
    if auth_token and len(auth_token) > 0:
        return True

    if req.headers.get('X-Internal-Request') == 'true':
        return True

    return False


def format_response(data, service_name):
    """
    Standardized response formatter for all services.
    Ensures consistent response structure across the microservice chain.
    """
    return {
        "source": service_name,
        "data": data,
        "timestamp": "2024-01-15T10:30:00Z"
    }
UTILS_EOF

# Update service_a.py: import from utils instead of service_c
sed -i 's/from service_c import format_response/from utils import format_response/' /app/service_a.py

# Update service_c.py: import from utils instead of service_a
sed -i 's/from service_a import validate_request/from utils import validate_request/' /app/service_c.py

# ==============================================================
# Fix 2: Correct SERVICE_C_PORT in config.py
# ==============================================================
# config.py has SERVICE_C_PORT defaulting to 5003, but Service C
# actually listens on port 5002.
sed -i "s/SERVICE_C_PORT', 5003/SERVICE_C_PORT', 5002/" /app/config.py

# ==============================================================
# Fix 3: Fix endpoint path in service_a.py
# ==============================================================
# service_a calls /api/v1/process on service_b, but service_b
# only exposes /api/process (no /v1/ prefix).
sed -i 's|/api/v1/process|/api/process|' /app/service_a.py

# ==============================================================
# Fix 4: Fix response format in service_c /api/data endpoint
# ==============================================================
# service_c returns plain text from /api/data, but service_b
# expects a JSON response and calls .json() on it.
# Replace the plain text return with a proper JSON response.
python3 << 'PYFIX_EOF'
import re

with open('/app/service_c.py', 'r') as f:
    content = f.read()

# Replace the plain text return statement with JSON response
old_line = '    return f"service_c_ok: {active_count} active records available", 200'
new_line = '    return jsonify({"status": "service_c_ok", "service_c_ok": True, "active_records": active_count}), 200'

content = content.replace(old_line, new_line)

with open('/app/service_c.py', 'w') as f:
    f.write(content)
PYFIX_EOF

echo "All fixes applied successfully."
