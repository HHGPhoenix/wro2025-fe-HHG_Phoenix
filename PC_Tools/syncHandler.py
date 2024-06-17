import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import paramiko

# Load environment variables from .env file
load_dotenv()

# Environment variables
WATCHED_DIR = os.getenv('WATCHED_DIR')  # The folder to monitor
RPI_HOST = os.getenv('RPI_HOST')  # RPi hostname or IP
RPI_PORT = int(os.getenv('RPI_PORT', 22))  # RPi SSH port (default 22)
RPI_USER = os.getenv('RPI_USER')  # RPi SSH username
RPI_PASS = os.getenv('RPI_PASS')  # RPi SSH password
RPI_DEST_DIR = os.getenv('RPI_DEST_DIR')  # Destination directory on RPi
GITIGNORE_FILE = os.path.join(WATCHED_DIR, '.gitignore')

# Load .gitignore entries
def load_gitignore_entries():
    if os.path.exists(GITIGNORE_FILE):
        with open(GITIGNORE_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Check if the file should be ignored
def is_ignored(file_path):
    gitignore_entries = load_gitignore_entries()
    for entry in gitignore_entries:
        if entry in file_path:
            return True
    return False

# SSH connection setup
def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(RPI_HOST, port=RPI_PORT, username=RPI_USER, password=RPI_PASS)
    return client

# Synchronize file to RPi
def sync_file_to_rpi(local_file, remote_file):
    if is_ignored(local_file):
        print(f"Ignoring {local_file} based on .gitignore rules")
        return
    client = ssh_connect()
    sftp = client.open_sftp()
    sftp.put(local_file, remote_file)
    sftp.close()
    client.close()
    print(f"Synchronized {local_file} to {remote_file} on RPi")

# Event handler for directory monitoring
class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR)
            remote_path = os.path.join(RPI_DEST_DIR, relative_path)
            sync_file_to_rpi(local_path, remote_path)

    def on_created(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR)
            remote_path = os.path.join(RPI_DEST_DIR, relative_path)
            sync_file_to_rpi(local_path, remote_path)

# Main function
def main():
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCHED_DIR, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
