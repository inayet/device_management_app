import yaml
import subprocess
from fasthtml.common import *
import socket
import ssl
from db_helpers import get_devices, get_device_by_id, log_operation, insert_device, wipe_device
from datetime import datetime

# Load secrets from encrypted YAML file
def load_secrets():
    output = subprocess.run(
        ["sops", "--decrypt", "secrets.enc.yaml"],
        capture_output=True, text=True, check=True
    )
    return yaml.safe_load(output.stdout)

secrets = load_secrets()

# SSL/TLS Configurations
SERVER_CERT_CONTENT = secrets['server_cert']
SERVER_KEY_CONTENT = secrets['server_key']
CLIENT_CERT_CONTENT = secrets['client_cert']
CLIENT_KEY_CONTENT = secrets['client_key']

# Write secrets to temporary files for SSL
with open('server_cert.pem', 'w') as f:
    f.write(SERVER_CERT_CONTENT)
with open('server_key.pem', 'w') as f:
    f.write(SERVER_KEY_CONTENT)
with open('client_cert.pem', 'w') as f:
    f.write(CLIENT_CERT_CONTENT)
with open('client_key.pem', 'w') as f:
    f.write(CLIENT_KEY_CONTENT)

SERVER_CERT = "server_cert.pem"
SERVER_KEY = "server_key.pem"
CLIENT_CERT = "client_cert.pem"
HOST = "0.0.0.0"
PORT = 9000

app, rt = fast_app(
    hdrs=(
        Link(rel='stylesheet', href='https://unpkg.com/@picocss/pico@latest/css/pico.min.css'),
        Link(rel='stylesheet', href='/static/styles.css'),
    ),
    static_path='static'
)

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
context.load_verify_locations(CLIENT_CERT)
context.verify_mode = ssl.CERT_REQUIRED

# Secure logging endpoint to receive logs from client
@rt("/log_operation")
def post(req):
    data = req.json()
    device_id = data.get("device_id")
    operation = data.get("operation")
    user = data.get("user", "client")

    # Log the operation in the database
    log_operation(device_id, operation, user)
    return JSONResponse({"status": "Log recorded successfully"})

def send_wipe_command(device_id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with context.wrap_socket(sock, server_side=False) as secure_sock:
            secure_sock.connect((HOST, PORT))
            secure_sock.send(device_id.encode('utf-8'))
            secure_sock.send("WIPE".encode('utf-8'))
            response = secure_sock.recv(1024).decode('utf-8')
            return response == "WIPE_SUCCESS"

@dataclass
class Device:
    id: str
    name: str
    status: str
    encryption_status: bool
    last_accessed: str
    role: str

    def __ft__(self):
        return Article(
            H2(self.name),
            P(f"Status: {self.status}"),
            P(f"Encryption: {'Enabled' if self.encryption_status else 'Disabled'}"),
            P(f"Last Accessed: {self.last_accessed}"),
            A("View Details", href=f"/devices/{self.id}", cls="button"),
            cls="device-item"
        )

def layout(*args, title="Device Management", **kwargs):
    return Titled(
        title,
        Nav(
            A("Home", href="/"),
            A("Devices", href="/devices"),
            A("Add Device", href="/devices/new"),
            A("Audit Logs", href="/audit"),
            cls="navigation"
        ),
        Main(*args, **kwargs)
    )

@rt("/")
def get():
    return layout(P("Welcome to the Device Management Dashboard!"), title="Home")

@rt("/devices")
def get():
    devices_data = get_devices()
    devices = [Device(id=row[0], name=row[1], status=row[2], encryption_status=row[3], last_accessed=row[4], role=row[5]) for row in devices_data]
    return layout(
        Div(
            *[device.__ft__() for device in devices],
            cls="device-list"
        ),
        title="Devices"
    )

@rt("/devices/{device_id}")
def get(device_id: str):
    device_data = get_device_by_id(device_id)
    if not device_data:
        return layout(H1("Error"), P(f"Device with ID {device_id} not found."), title="Error")
    
    device = Device(id=device_data[0], name=device_data[1], status=device_data[2], encryption_status=device_data[3], last_accessed=device_data[4], role=device_data[5])
    return layout(
        H1(f"Device: {device.name}"),
        P(f"Status: {device.status}"),
        P(f"Encryption: {'Enabled' if device.encryption_status else 'Disabled'}"),
        Form(method="post", action=f"/devices/{device.id}/wipe")(
            Button("Wipe Device", type="submit", cls="button danger")
        ),
        title=f"Device {device.name}"
    )

@rt("/devices/{device_id}/wipe")
def post(device_id: str):
    if send_wipe_command(device_id):
        log_operation(device_id, "Wipe", "admin")
        wipe_device(device_id)
    return RedirectResponse(url="/devices")

serve()
