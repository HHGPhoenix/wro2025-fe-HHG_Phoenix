import subprocess
import re
import os
import signal

class Lidar:
    def __init__(self, shared_lidar_list):
        self.shared_lidar_list = shared_lidar_list
        self.process = None
    
    def read_data(self):
        try:
            # Path to the C++ executable
            self.cpp_executable = "/home/pi/rplidar_sdk-master/output/Linux/Release/ultra_simple"
    
            # Initialize lists to hold the data
            self.current_360_data = []
    
            # Regex pattern to match the output lines
            self.pattern = re.compile(r'(S  )?theta: (\d+\.\d+) Dist: (\d+\.\d+) Q: (\d+)')
            
            # Ensure the file has execute permissions
            subprocess.run(["chmod", "+x", self.cpp_executable])
    
            # Run the C++ executable with the specified arguments and capture the output
            self.process = subprocess.Popen(
                [self.cpp_executable, "--channel", "--serial", "/dev/ttyUSB0", "460800"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    continue
                if output:
                    match = self.pattern.search(output)
                    if match:
                        if match.group(1) == 'S  ':
                            if len(self.current_360_data) > 10:  # Ensure the array has more than one value
                                self.shared_lidar_list.append(self.current_360_data)
                                if len(self.shared_lidar_list) > 10:
                                    self.shared_lidar_list.pop(0)
                            self.current_360_data = []
                        theta = float(match.group(2))
                        dist = float(match.group(3))
                        quality = int(match.group(4))
                        self.current_360_data.append((theta, dist, quality))
        except KeyboardInterrupt:
            print("KeyboardInterrupt caught, exiting...")
        finally:
            if self.process:
                # send keyboard interrupt to the process
                print("Sending SIGINT to the process")
                os.kill(self.process.pid, signal.SIGINT)
                self.process.wait()  # Wait for the process to terminate