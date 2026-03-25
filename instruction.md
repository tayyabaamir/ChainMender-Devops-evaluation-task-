# Microservice Dependency Fix

You have three Python Flask microservices running locally that form a request chain:

- **Service A** (port 5000) — API Gateway that receives external requests and forwards them to Service B
- **Service B** (port 5001) — Processing Service that receives from Service A and delegates to Service C  
- **Service C** (port 5002) — Data Service that provides core data and responds back up the chain

The expected request flow is:
```
Client → Service A (5000) → Service B (5001) → Service C (5002)
```

## Current Problem

When you attempt to start the services and test the request chain, **multiple failures occur**. The services do not function correctly — some fail to start entirely, and the end-to-end request chain (`/request_chain` on Service A) does not return a successful aggregated response.

## Your Goal

1. Attempt to start all three services and observe the failures.
2. Analyze error logs and tracebacks to identify the root causes.
3. Examine the service source code and configuration files in `/app/` to understand inter-service communication.
4. Apply targeted fixes to the Python source files and/or configuration to resolve all issues.
5. Verify that:
   - All three services start without errors
   - Each service responds on its root endpoint (`/`) with a 200 status
   - Each service's `/health` endpoint returns 200
   - Service C's `/api/data` endpoint returns valid JSON containing `"service_c_ok"`
   - Service B's `/api/process` endpoint successfully calls Service C and returns JSON containing both `"service_b_ok"` and `"service_c_ok"`
   - Service A's `/request_chain` endpoint successfully chains through all services and returns JSON containing `"service_a_ok"`, `"service_b_ok"`, and `"service_c_ok"`

## Files

The following files are located in `/app/`:
- `config.py` — Shared configuration (ports, URLs, timeouts)
- `service_a.py` — API Gateway service
- `service_b.py` — Processing service
- `service_c.py` — Data service
- `requirements.txt` — Python dependencies (already installed)

## Constraints

- Do not modify the port that each service listens on (Service A=5000, B=5001, C=5002)
- Do not install additional packages
- All fixes must be applied to files in `/app/`
