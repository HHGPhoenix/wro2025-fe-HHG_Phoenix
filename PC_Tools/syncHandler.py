import os
import json
import sys
import time
import subprocess
from threading import Event, Thread
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paramiko  # Ensure paramiko is installed

# Get the current working directory
exec_dir = os.getcwd()

# Configuration variables, paths are now relative to exec_dir
CONFIG_FILE = os.path.join(exec_dir, 'PC_Tools', 'sync_handler_data.json')
GITIGNORE_FILE = os.path.join(exec_dir, '.gitignore')
WATCHED_DIR = os.path.join(exec_dir, 'RPIs')  # Specify your watched directory here
RPI_CONFIGS = {}

# Ensure necessary directories exist
try:
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    os.makedirs(WATCHED_DIR, exist_ok=True)
except Exception as e:
    print(f"Error creating directories: {e}")
    sys.exit(1)

# # Create the config file if it doesn't exist
# if not os.path.exists(CONFIG_FILE):
#     try:
#         with open(CONFIG_FILE, 'w') as f:
#             f.write('{}')  # Write an empty JSON object to the file
#     except Exception as e:
#         print(f"Error creating configuration file: {e}")
#         sys.exit(1)

# Load or create configuration file
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            f.write('{}')  # Write an empty JSON object to the file
        return {'RPIs': {}}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Load initial configuration
def load_initial_config():
    global GITIGNORE_FILE, RPI_CONFIGS
    config = load_config()
    
    GITIGNORE_FILE = os.path.join(WATCHED_DIR, '.gitignore')
    
    RPI_CONFIGS = config.get('RPIs', {})
    return config

# Update or add new RPI configuration dynamically
def configure_rpi(config):
    updated = False
    for rpi_host, rpi_details in config.get('RPIs', {}).items():
        if not all(k in rpi_details for k in ('host', 'user', 'pass', 'port', 'dest_dir')):
            print(f"RPI {rpi_host} is missing configuration details. Please update the configuration file.")
            sys.exit(0)
        if rpi_details.get('status') == 'unconfigured':
            print(f"RPI {rpi_host} is unconfigured. Please configure it and rerun the script.")
            sys.exit(0)
    
    if updated:
        save_config(config)
        sys.exit(0)
    
    print("All RPIs are configured.")
    return config
# Load initial configuration and ensure all RPIs are configured
config = load_initial_config()
config = configure_rpi(config)

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
def ssh_connect(rpi_host, rpi_user, rpi_pass, rpi_port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(rpi_host, port=rpi_port, username=rpi_user, password=rpi_pass)
    return client

# Synchronize file to RPi
def sync_file_to_rpi(local_file, remote_file, rpi_details):
    if is_ignored(local_file):
        print(f"Ignoring {local_file} based on .gitignore rules")
        return
    
    client = ssh_connect(rpi_details['host'], rpi_details['user'], rpi_details['pass'], rpi_details['port'])
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
    print(f"Synchronized {local_file} to {remote_file} on RPi {rpi_details['host']}")

# Event handler for directory monitoring
class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            for rpi, details in RPI_CONFIGS.items():
                remote_path = os.path.join(details['dest_dir'], relative_path).replace("\\", "/")
                sync_file_to_rpi(local_path, remote_path, details)

    def on_created(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            for rpi, details in RPI_CONFIGS.items():
                remote_path = os.path.join(details['dest_dir'], relative_path).replace("\\", "/")
                sync_file_to_rpi(local_path, remote_path, details)

# Synchronize all files to RPIs
def sync_all_files_to_rpis():
    def sync_file(file_info):
        local_file_path, remote_file_path, rpi_details = file_info
        sync_file_to_rpi(local_file_path, remote_file_path, rpi_details)

    files_to_sync = []
    for root, dirs, files in os.walk(WATCHED_DIR):
        for file in files:
            local_file_path = os.path.join(root, file)
            if not is_ignored(local_file_path):
                relative_path = os.path.relpath(local_file_path, WATCHED_DIR).replace("\\", "/")
                for rpi, details in RPI_CONFIGS.items():
                    remote_file_path = os.path.join(details['dest_dir'], relative_path).replace("\\", "/")
                    files_to_sync.append((local_file_path, remote_file_path, details))

    # Use ThreadPoolExecutor to sync files in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(sync_file, files_to_sync)

# Monitor for new or updated RPI configurations
def monitor_rpi_configs(stop_event):
    while not stop_event.is_set():
        config = load_config()
        config_changed = False

        for rpi, details in config['RPIs'].items():
            if not all(k in details for k in ('host', 'user', 'pass', 'port', 'dest_dir')):
                print(f"RPI {rpi} is missing configuration details. Please update the configuration file.")
                continue
            
            if details.get('status') == 'unconfigured':
                print(f"RPI {rpi} is unconfigured. Attempting to configure...")

                try:
                    client = ssh_connect(details['host'], details['user'], details['pass'], details['port'])
                    client.close()
                    details['status'] = 'configured'
                    config_changed = True
                    print(f"RPI {rpi} configured successfully.")
                except Exception as e:
                    print(f"Failed to connect to RPI {rpi}: {e}")

        if config_changed:
            save_config(config)
        
        time.sleep(5)
# Modify the main function to call sync_all_files_to_rpis at the start and monitor RPIs
def main():
    if "--run-in-cmd" not in sys.argv:
        # Construct the command to run this script in a new cmd window
        cmd_command = f'cmd /c "{sys.executable}" "{sys.argv[0]}" --run-in-cmd'
        # Open a new cmd window and run this script with the special argument
        subprocess.Popen(cmd_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        # Original main functionality
        config = load_initial_config()  # Load initial configuration
        
        stop_event = Event()
        
        # Start the configuration monitoring thread
        config_monitor_thread = Thread(target=monitor_rpi_configs, args=(stop_event,))
        config_monitor_thread.start()

        event_handler = ChangeHandler()
        observer = Observer()
        observer.schedule(event_handler, path=WATCHED_DIR, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            stop_event.set()
        observer.join()
        config_monitor_thread.join()

if __name__ == "__main__":
    main()
