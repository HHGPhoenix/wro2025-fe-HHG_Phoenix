import os
import time
import paramiko
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import logging
import pathspec

# Load environment variables from .env file
load_dotenv()

# Environment variables
WATCHED_DIR = os.getenv('WATCHED_DIR')  # The folder to monitor

# RPi 1 details
RPI1_HOST = os.getenv('RPI1_HOST')
RPI1_PORT = int(os.getenv('RPI1_PORT', 22))
RPI1_USER = os.getenv('RPI1_USER')
RPI1_PASS = os.getenv('RPI1_PASS')
RPI1_DEST_DIR = os.getenv('RPI1_DEST_DIR')

# RPi 2 details
RPI2_HOST = os.getenv('RPI2_HOST')
RPI2_PORT = int(os.getenv('RPI2_PORT', 22))
RPI2_USER = os.getenv('RPI2_USER')
RPI2_PASS = os.getenv('RPI2_PASS')
RPI2_DEST_DIR = os.getenv('RPI2_DEST_DIR')

# Update to use GITIGNORE_PATH environment variable
GITIGNORE_FILE = os.getenv('GITIGNORE_PATH')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load .gitignore entries and compile into pathspec
def load_gitignore_entries():
    if os.path.exists(GITIGNORE_FILE):
        with open(GITIGNORE_FILE, 'r') as f:
            gitignore_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return pathspec.PathSpec.from_lines('gitwildmatch', gitignore_lines)
    return pathspec.PathSpec([])  # Return an empty PathSpec if no .gitignore file is found

# Check if the file should be ignored using pathspec
def is_ignored(file_path):
    # Convert to relative path from WATCHED_DIR and normalize
    relative_path = os.path.relpath(file_path, WATCHED_DIR).replace("\\", "/")
    gitignore_spec = load_gitignore_entries()
    return gitignore_spec.match_file(relative_path)

# SSH connection setup
def ssh_connect(host, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=user, password=password)
    return client

# Global SSH clients
ssh_clients = {}

# Function to establish and maintain SSH connections
def setup_ssh_connections():
    ssh_clients['rpi1'] = {'client': None, 'host': RPI1_HOST, 'port': RPI1_PORT, 'user': RPI1_USER, 'pass': RPI1_PASS}
    ssh_clients['rpi2'] = {'client': None, 'host': RPI2_HOST, 'port': RPI2_PORT, 'user': RPI2_USER, 'pass': RPI2_PASS}

    for key in ssh_clients:
        ssh_clients[key]['client'] = ssh_connect_with_retries(
            ssh_clients[key]['host'],
            ssh_clients[key]['port'],
            ssh_clients[key]['user'],
            ssh_clients[key]['pass']
        )

def ssh_connect_with_retries(host, port, user, password, retries=10, delay=5, long_delay=60):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    attempt = 0
    while attempt < retries:
        try:
            client.connect(host, port=port, username=user, password=password)
            logging.info(f"Successfully connected to {host} on attempt {attempt + 1}")
            return client
        except Exception as e:
            logging.warning(f"Failed to connect to {host} on attempt {attempt + 1}: {e}")
            attempt += 1
            time.sleep(delay)
    
    # After initial retries, switch to longer delay
    while True:
        try:
            client.connect(host, port=port, username=user, password=password)
            logging.info(f"Successfully reconnected to {host} after prolonged attempts")
            return client
        except Exception as e:
            logging.warning(f"Failed to reconnect to {host}: {e}")
            time.sleep(long_delay)

def is_ssh_client_connected(client):
    try:
        transport = client.get_transport()
        if transport and transport.is_active():
            return True
    except Exception as e:
        logging.error(f"Failed to check SSH client status: {e}")
    return False

def ensure_ssh_connection(name):
    if not is_ssh_client_connected(ssh_clients[name]['client']):
        logging.info(f"Reconnecting to {name}")
        ssh_clients[name]['client'] = ssh_connect_with_retries(
            ssh_clients[name]['host'],
            ssh_clients[name]['port'],
            ssh_clients[name]['user'],
            ssh_clients[name]['pass']
        )

# Synchronize file to RPi with error handling and persistent connection reuse
def sync_file_to_rpi(local_file, remote_file, name):
    if not os.path.exists(local_file):
        logging.error(f"File {local_file} does not exist and cannot be synced.")
        return

    if is_ignored(local_file):
        logging.info(f"Ignoring {local_file} based on .gitignore rules")
        return

    try:
        ensure_ssh_connection(name)
        client = ssh_clients[name]['client']
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
        logging.info(f"Synchronized {local_file} to {remote_file} on {ssh_clients[name]['host']}")
    except Exception as e:
        logging.error(f"Failed to sync {local_file} to {ssh_clients[name]['host']}: {e}")
        # Log the failure for later retry
        failed_syncs.add((local_file, remote_file, name))

# Retry failed syncs
def retry_failed_syncs():
    global failed_syncs
    remaining_syncs = set()
    for sync_info in list(failed_syncs):  # Use list to avoid modifying the set during iteration
        local_file, remote_file, name = sync_info
        try:
            sync_file_to_rpi(local_file, remote_file, name)
            failed_syncs.discard(sync_info)  # Remove the sync info if successful
        except Exception as e:
            logging.error(f"Retry failed for {local_file} to {ssh_clients[name]['host']}: {e}")
            remaining_syncs.add(sync_info)
    failed_syncs = remaining_syncs

# Synchronize file to both RPis
def sync_file_to_rpis(local_file, relative_path):
    rpi1_remote_file = os.path.join(RPI1_DEST_DIR, relative_path).replace("\\", "/")
    rpi2_remote_file = os.path.join(RPI2_DEST_DIR, relative_path).replace("\\", "/")

    sync_file_to_rpi(local_file, rpi1_remote_file, 'rpi1')
    sync_file_to_rpi(local_file, rpi2_remote_file, 'rpi2')

# Event handler for directory monitoring
class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            sync_file_to_rpis(local_path, relative_path)

    def on_created(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            sync_file_to_rpis(local_path, relative_path)

def sync_all_files_to_rpis():
    def sync_file(file_info):
        local_file_path, relative_path = file_info
        sync_file_to_rpis(local_file_path, relative_path)

    # Collect all files that need to be synced
    files_to_sync = []
    for root, dirs, files in os.walk(WATCHED_DIR):
        for file in files:
            local_file_path = os.path.join(root, file)
            if not is_ignored(local_file_path):
                relative_path = os.path.relpath(local_file_path, WATCHED_DIR).replace("\\", "/")
                files_to_sync.append((local_file_path, relative_path))

    # Use ThreadPoolExecutor to sync files in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(sync_file, files_to_sync)

def main():
    global failed_syncs
    failed_syncs = set()
    
    setup_ssh_connections()  # Establish SSH connections to both RPis
    sync_all_files_to_rpis()  # Sync all files at script start
    
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCHED_DIR, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            retry_failed_syncs()  # Retry any failed syncs periodically
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()
