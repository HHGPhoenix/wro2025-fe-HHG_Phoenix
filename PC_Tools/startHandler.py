import subprocess
import threading

print("Which module do you want to start?")
print("1. DataManager")
print("2. AIController")
print("3. BOTH")

choice = input("Enter your choice: ")

def start_data_manager():
    print("Starting DataManager")
    subprocess.run(["python", "-m", "RPIs.DataManager.main"])

def start_ai_controller():
    print("Starting AIController")
    subprocess.run(["python", "-m", "RPIs.AIController.main"])

if choice == '1':
    start_data_manager()

elif choice == '2':
    start_ai_controller()

elif choice == '3':
    print("Starting DataManager and AIController")
    dm_thread = threading.Thread(target=start_data_manager)
    ai_thread = threading.Thread(target=start_ai_controller)
    dm_thread.start()
    ai_thread.start()
    dm_thread.join()
    ai_thread.join()