class ParkingUtils:
    def __init__(self, parking_spot_distance, left_lidar_points, right_lidar_points, front_lidar_points):
        self.parking_spot_distance = parking_spot_distance
        self.left_lidar_points = left_lidar_points
        self.right_lidar_points = right_lidar_points
        self.front_lidar_points = front_lidar_points


    def determine_if_parked_and_direction(self):
        left_average = self.get_average_for_lidar_points(self.left_lidar_points)
        right_average = self.get_average_for_lidar_points(self.right_lidar_points)

        # Simple logic to determine if parked
        if left_average + right_average < self.parking_spot_distance:
            # Determine direction when parked
            if left_average < right_average:
                return True, "counterclockwise"
            else:
                return True, "clockwise"

        return False, None


    def get_average_for_lidar_points(self, lidar_points):
        if not lidar_points:
            return 0
        
        total = sum(lidar_points)
        average = total / len(lidar_points)
        return average