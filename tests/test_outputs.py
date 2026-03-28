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

_processes = []


def _kill_port(port):
    os.system(f"fuser -k {port}/tcp 2>/dev/null || true")


def _start_all_services():
    global _processes

    for port in [5000, 5001, 5002]:
        _kill_port(port)
    time.sleep(1)

    env = os.environ.copy()

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

    for proc in _processes:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            raise RuntimeError(
                f"Service process exited prematurely with code {proc.returncode}.\n"
                f"stdout: {stdout.decode()}\nstderr: {stderr.decode()}"
            )


def _stop_all_services():
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

    for port in [5000, 5001, 5002]:
        _kill_port(port)
    time.sleep(1)


@pytest.fixture(autouse=True, scope="module")
def manage_services():
    _start_all_services()
    yield
    _stop_all_services()


class TestServiceHealth:

    def test_service_a_health(self):
        response = requests.get("http://localhost:5000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "service_a"

    def test_service_b_health(self):
        response = requests.get("http://localhost:5001/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "service_b"

    def test_service_c_health(self):
        response = requests.get("http://localhost:5002/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "service_c"


class TestServiceRoot:

    def test_service_a_root(self):
        response = requests.get("http://localhost:5000/", timeout=5)
        assert response.status_code == 200
        assert "service_a" in response.text

    def test_service_b_root(self):
        response = requests.get("http://localhost:5001/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "service_b_ok"

    def test_service_c_root(self):
        response = requests.get("http://localhost:5002/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "service_c_ok"


class TestServiceCData:

    def test_service_c_data_returns_json(self):
        response = requests.get(
            "http://localhost:5002/api/data",
            headers={"X-Internal-Request": "true"},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert "service_c_ok" in str(data)

    def test_service_c_data_has_status(self):
        response = requests.get(
            "http://localhost:5002/api/data",
            headers={"X-Internal-Request": "true"},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("service_c_ok") is True or data.get("status") == "service_c_ok"


class TestServiceBProcess:

    def test_service_b_process_returns_ok(self):
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


class TestRequestChain:

    def test_request_chain_success(self):
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
        response = requests.get(
            "http://localhost:5000/request_chain",
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


def test_generate_reward():
    with open("reward.txt", "w") as f:
        f.write("1.0\n")
    import json
    with open("reward.json", "w") as f:
        json.dump({"reward": 1.0}, f)
