import os
import socket
import ssl
import subprocess
import yaml
from datetime import datetime
import requests

# Load secrets from encrypted YAML file
def load_secrets():
    output = subprocess.run(
        ["sops", "--decrypt", "secrets.enc.yaml"],
        capture_output=True, text=True, check=True
    )
    return yaml.safe_load(output.stdout)

secrets = load_secrets()

# SSL Configuration
SERVER_IP = 'your_server_ip'  # Replace with your server's IP
SERVER_PORT = 9000
CLIENT_CERT = 'client_cert.pem'
CLIENT_KEY = 'client_key.pem'
CA_CERT = 'server_cert.pem'

# Write certificates and keys from secrets
with open(CLIENT_CERT, 'w') as f:
    f.write(secrets['client_cert'])
with open(CLIENT_KEY, 'w') as f:
    f.write(secrets['client_key'])
with open(CA_CERT, 'w') as f:
    f.write(secrets['server_cert'])

# Prepare secure SSL context
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.load_cert_chain(certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
context.load_verify_locations(CA_CERT)

#heartbeat check to the client 
def send_heartbeat():
    while True:
        try:
            response = requests.post(
                f"https://{SERVER_IP}:{SERVER_PORT}/heartbeat",
                json={"device_id": "unique_device_id"},
                verify=CA_CERT
            )
            if response.status_code == 200:
                print("[INFO] Heartbeat sent successfully.")
            else:
                print("[ERROR] Failed to send heartbeat.")
        except requests.exceptions.RequestException as e:
            print("[ERROR] Heartbeat request failed:", e)
        time.sleep(600)  # Send heartbeat every 10 minutes

# BIOS Wipe Function for Dell Laptop
def perform_bios_wipe():
    print("[INFO] Attempting to lock BIOS and disable boot options.")
    try:
        subprocess.run(["cctk", "--setuppwd", "your_password"], check=True)  # Set a BIOS password
        subprocess.run(["cctk", "--usbboot=disable"], check=True)
        subprocess.run(["cctk", "--bootorder=none"], check=True)
        print("[SUCCESS] BIOS configured for wipe.")
    except subprocess.CalledProcessError as e:
        print("[ERROR] BIOS configuration failed:", e)

# Secure Disk Wipe
def secure_disk_wipe():
    print("[INFO] Starting disk wipe.")
    try:
        subprocess.run("cipher /w:C:\\", shell=True, check=True)
        print("[SUCCESS] Disk wiped successfully.")
    except subprocess.CalledProcessError as e:
        print("[ERROR] Disk wipe failed:", e)

# Send log to server
def log_operation(device_id, operation):
    url = f"https://{SERVER_IP}:{SERVER_PORT}/log_operation"
    data = {
        "device_id": device_id,
        "operation": operation,
        "user": "client"
    }
    try:
        response = requests.post(url, json=data, verify=CA_CERT)
        if response.status_code == 200:
            print("[INFO] Log sent to server successfully.")
        else:
            print("[ERROR] Failed to log operation to server.")
    except requests.exceptions.RequestException as e:
        print("[ERROR] Request to server failed:", e)

# Connect to Server and Await Commands
def connect_to_server():
    print("[INFO] Connecting to server...")
    with socket.create_connection((SERVER_IP, SERVER_PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=SERVER_IP) as ssock:
            print("[INFO] Connected to server, awaiting commands.")

            while True:
                command = ssock.recv(1024).decode('utf-8')
                print(f"[INFO] Received command: {command}")

                if command == "WIPE":
                    log_operation("device_id", "Wipe command received from server.")
                    perform_bios_wipe()
                    secure_disk_wipe()
                    log_operation("device_id", "Wipe completed.")
                    ssock.sendall("WIPE_SUCCESS".encode('utf-8'))
                    print("[INFO] Wipe command executed and response sent.")
                else:
                    print("[WARNING] Unknown command received.")

if __name__ == "__main__":
    try:
        connect_to_server()
    except Exception as e:
        print("[ERROR] Client failed to connect or execute commands:", e)
