import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import paramiko
from concurrent.futures import ThreadPoolExecutor

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

print(f"Watching {WATCHED_DIR} for changes")

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
    # Ensure the remote directory exists
    remote_dir = os.path.dirname(remote_file)
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        # Create remote directory and all intermediate directories if they don't exist
        current_dir = ''
        for dir in remote_dir.split('/'):
            current_dir += dir + '/'
            try:
                sftp.stat(current_dir)
            except FileNotFoundError:
                sftp.mkdir(current_dir)
    sftp.put(local_file, remote_file)
    sftp.close()
    client.close()
    print(f"Synchronized {local_file} to {remote_file} on RPi")

# Event handler for directory monitoring
class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            remote_path = os.path.join(RPI_DEST_DIR, relative_path).replace("\\", "/")
            sync_file_to_rpi(local_path, remote_path)

    def on_created(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            remote_path = os.path.join(RPI_DEST_DIR, relative_path).replace("\\", "/")
            sync_file_to_rpi(local_path, remote_path)


def sync_all_files_to_rpi():
    def sync_file(file_info):
        local_file_path, remote_file_path = file_info
        sync_file_to_rpi(local_file_path, remote_file_path)

    # Collect all files that need to be synced
    files_to_sync = []
    for root, dirs, files in os.walk(WATCHED_DIR):
        for file in files:
            local_file_path = os.path.join(root, file)
            if not is_ignored(local_file_path):
                relative_path = os.path.relpath(local_file_path, WATCHED_DIR).replace("\\", "/")
                remote_file_path = os.path.join(RPI_DEST_DIR, relative_path).replace("\\", "/")
                files_to_sync.append((local_file_path, remote_file_path))

    # Use ThreadPoolExecutor to sync files in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(sync_file, files_to_sync)

# Modify the main function to call sync_all_files_to_rpi at the start
def main():
    sync_all_files_to_rpi()  # Sync all files at script start
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
