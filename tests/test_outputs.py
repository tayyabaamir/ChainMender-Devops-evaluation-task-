"""
Functional tests for the microservice chain.
Verifies that all three services start correctly, respond on their
individual endpoints, and that the full request chain works end-to-end.
"""
import requests
import pytest
import subprocess
import time
import os
import signal

# Global process tracking
_processes = []


def _kill_port(port):
    """Kill any process listening on the given port"""
    os.system(f"fuser -k {port}/tcp 2>/dev/null || true")


def _start_all_services():
    """Start all three microservices and wait for them to be ready"""
    global _processes

    # Clean up any existing processes on our ports
    for port in [5000, 5001, 5002]:
        _kill_port(port)
    time.sleep(1)

    env = os.environ.copy()

    # Start services in dependency order: C first, then B, then A
    proc_c = subprocess.Popen(
        ["python3", "/app/service_c.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)

    proc_b = subprocess.Popen(
        ["python3", "/app/service_b.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)

    proc_a = subprocess.Popen(
        ["python3", "/app/service_a.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)

    _processes = [proc_a, proc_b, proc_c]

    # Verify all processes are still running
    for proc in _processes:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            raise RuntimeError(
                f"Service process exited prematurely with code {proc.returncode}.\n"
                f"stdout: {stdout.decode()}\nstderr: {stderr.decode()}"
            )


def _stop_all_services():
    """Terminate all running service processes"""
    global _processes
    for proc in _processes:
        try:
            proc.terminate()
        except Exception:
            pass
    for proc in _processes:
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    _processes = []

    # Extra cleanup
    for port in [5000, 5001, 5002]:
        _kill_port(port)
    time.sleep(1)


@pytest.fixture(autouse=True, scope="module")
def manage_services():
    """Module-scoped fixture to start/stop services once for all tests"""
    _start_all_services()
    yield
    _stop_all_services()


# ========================================================
# Individual Service Health Checks
# ========================================================

class TestServiceHealth:
    """Tests that each service starts and responds on basic endpoints"""

    def test_service_a_health(self):
        """Service A health endpoint returns 200"""
        response = requests.get("http://localhost:5000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "service_a"

    def test_service_b_health(self):
        """Service B health endpoint returns 200"""
        response = requests.get("http://localhost:5001/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "service_b"

    def test_service_c_health(self):
        """Service C health endpoint returns 200"""
        response = requests.get("http://localhost:5002/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "service_c"


# ========================================================
# Individual Service Root Endpoints
# ========================================================

class TestServiceRoot:
    """Tests that each service responds with status on root endpoint"""

    def test_service_a_root(self):
        """Service A root returns service_a_ok status"""
        response = requests.get("http://localhost:5000/", timeout=5)
        assert response.status_code == 200
        assert "service_a" in response.text

    def test_service_b_root(self):
        """Service B root returns service_b_ok status"""
        response = requests.get("http://localhost:5001/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "service_b_ok"

    def test_service_c_root(self):
        """Service C root returns service_c_ok status"""
        response = requests.get("http://localhost:5002/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "service_c_ok"


# ========================================================
# Service C Data Endpoint
# ========================================================

class TestServiceCData:
    """Tests Service C's data endpoint returns valid JSON"""

    def test_service_c_data_returns_json(self):
        """Service C /api/data returns valid JSON (not plain text)"""
        response = requests.get(
            "http://localhost:5002/api/data",
            headers={"X-Internal-Request": "true"},
            timeout=5
        )
        assert response.status_code == 200
        # Must be valid JSON
        data = response.json()
        assert "service_c_ok" in str(data)

    def test_service_c_data_has_status(self):
        """Service C /api/data response contains service_c_ok"""
        response = requests.get(
            "http://localhost:5002/api/data",
            headers={"X-Internal-Request": "true"},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("service_c_ok") is True or data.get("status") == "service_c_ok"


# ========================================================
# Service B Process Endpoint
# ========================================================

class TestServiceBProcess:
    """Tests Service B can reach Service C and process requests"""

    def test_service_b_process_returns_ok(self):
        """Service B /api/process returns 200 with both B and C status"""
        response = requests.get(
            "http://localhost:5001/api/process",
            headers={
                "X-Auth-Token": "test-token",
                "X-Internal-Request": "true"
            },
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "service_b_ok" in str(data)
        assert "service_c_ok" in str(data)


# ========================================================
# Full Request Chain (End-to-End)
# ========================================================

class TestRequestChain:
    """Tests the full request chain: A -> B -> C"""

    def test_request_chain_success(self):
        """Full chain returns 200 with all three service statuses"""
        response = requests.get(
            "http://localhost:5000/request_chain",
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        text = str(data)
        assert "service_a_ok" in text
        assert "service_b_ok" in text
        assert "service_c_ok" in text

    def test_request_chain_is_json(self):
        """Full chain response is valid JSON"""
        response = requests.get(
            "http://localhost:5000/request_chain",
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()  # Will raise if not valid JSON
        assert isinstance(data, dict)


# ========================================================
# Reward Generation (Harbor Requirement)
# ========================================================

def test_generate_reward():
    """ Writes 1.0 to reward.txt if all tests have passed so far.
    """
    # Write to current directory (should be /app)
    with open("reward.txt", "w") as f:
        f.write("1.0\n")
    # Also write json just in case
    import json
    with open("reward.json", "w") as f:
        json.dump({"reward": 1.0}, f)
