#!/bin/bash
# Golden solution - runs fix_services.sh to resolve all microservice issues
set -e

cd /app
bash /solution/fix_services.sh
