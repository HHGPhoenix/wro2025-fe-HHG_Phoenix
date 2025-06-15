class ParkingUtils:
    def __init__(self, parking_spot_distance, left_lidar_points, right_lidar_points, front_lidar_points):
        self.parking_spot_distance = parking_spot_distance
        self.left_lidar_points = left_lidar_points
        self.right_lidar_points = right_lidar_points
        self.front_lidar_points = front_lidar_points


    def determine_if_parked_and_direction(self, lidar_data):
        left_lidar_point_list = []
        right_lidar_point_list = []
        for lidar_point in lidar_data:
            if lidar_point[0] in range(self.left_lidar_points[0], self.left_lidar_points[1]):
                left_lidar_point_list.append(lidar_point)
            elif lidar_point[0] in range(self.right_lidar_points[0], self.right_lidar_points[1]):
                right_lidar_point_list.append(lidar_point)
                
        left_average = self.get_average_for_lidar_points(left_lidar_point_list)
        print(left_lidar_point_list)
        right_average = self.get_average_for_lidar_points(right_lidar_point_list)
        print(right_lidar_point_list)
        
        print(f"Left Average: {left_average}, Right Average: {right_average}")

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
        
        total = 0
        for point in lidar_points:
            total += point[1]

        average = total / len(lidar_points)
        return average