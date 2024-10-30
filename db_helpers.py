import sqlite3
from datetime import datetime

# Initialize the database with devices and audit logs tables
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
        id TEXT PRIMARY KEY,
        name TEXT,
        status TEXT,
        encryption_status BOOLEAN,
        last_accessed TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        operation TEXT,
        timestamp TEXT,
        user TEXT,
        FOREIGN KEY(device_id) REFERENCES devices(id)
    )''')
    conn.commit()
    conn.close()

# Insert a new device into the devices table
def insert_device(device_id, name, status, encryption_status, role):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO devices (id, name, status, encryption_status, last_accessed, role)
                VALUES (?, ?, ?, ?, ?, ?)''', (device_id, name, status, encryption_status, datetime.now().isoformat(), role))
    conn.commit()
    conn.close()

# Retrieve all devices from the devices table
def get_devices():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM devices')
    devices = c.fetchall()
    conn.close()
    return devices

# Retrieve a specific device by its ID
def get_device_by_id(device_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
    device = c.fetchone()
    conn.close()
    return device

# Log an operation in the audit log
def log_operation(device_id, operation, user):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO audit_log (device_id, operation, timestamp, user)
                VALUES (?, ?, ?, ?)''', (device_id, operation, datetime.now().isoformat(), user))
    conn.commit()
    conn.close()

# Update device status to "Wiped" after a wipe operation
def wipe_device(device_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE devices SET status = "Wiped" WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
