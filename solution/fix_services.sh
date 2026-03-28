#!/bin/bash
set -e

cd /app

cat > /app/utils.py << 'UTILS_EOF'
"""
Shared utilities for microservices.
Extracted to resolve circular import between service_a and service_c.
"""


def validate_request(req):
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
    return {
        "source": service_name,
        "data": data,
        "timestamp": "2024-01-15T10:30:00Z"
    }
UTILS_EOF

sed -i 's/from service_c import format_response/from utils import format_response/' /app/service_a.py

sed -i 's/from service_a import validate_request/from utils import validate_request/' /app/service_c.py

sed -i "s/SERVICE_C_PORT', 5003/SERVICE_C_PORT', 5002/" /app/config.py

sed -i 's|/api/v1/process|/api/process|' /app/service_a.py

python3 << 'PYFIX_EOF'
import re

with open('/app/service_c.py', 'r') as f:
    content = f.read()

old_line = '    return f"service_c_ok: {active_count} active records available", 200'
new_line = '    return jsonify({"status": "service_c_ok", "service_c_ok": True, "active_records": active_count}), 200'

content = content.replace(old_line, new_line)

with open('/app/service_c.py', 'w') as f:
    f.write(content)
PYFIX_EOF

echo "All fixes applied successfully."
