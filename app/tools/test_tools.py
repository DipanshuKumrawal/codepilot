import subprocess
from pathlib import Path


def run_tests(repo_path):

    try:

        result = subprocess.run(
            ["pytest"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:

        return {
            "return_code": -1,
            "stdout": "",
            "stderr": "Tests timed out."
        }


def run_test_file(repo_path, test_file):

    try:

        result = subprocess.run(
            ["pytest", test_file],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:

        return {
            "return_code": -1,
            "stdout": "",
            "stderr": "Test execution timed out."
        }