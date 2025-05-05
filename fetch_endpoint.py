import os
import subprocess

def fetch_endpoint():
endpoint_url = os.getenv("ENDPOINT_URL", "http://globus_connect_container:7512/DataPath")
result = subprocess.run(["curl", "-s", endpoint_url], capture_output=True, text=True)
endpoint_id = result.stdout.strip()

if result.returncode != 0:
    print(f"Failed to fetch endpoint ID. Error: {result.stderr}")
    return

print(f"Fetched GLOBUS_ENDPOINT_ID: {endpoint_id}")
# You can use the endpoint_id here or set it as an environment variable
os.environ["GLOBUS_ENDPOINT_ID"] = endpoint_id

if __name__ == "__main__":
    fetch_endpoint()

endpoint_url = "http://globus_connect_container:7512/DataPath"
result = subprocess.run(["curl", "-s", endpoint_url], capture_output=True, text=True)
