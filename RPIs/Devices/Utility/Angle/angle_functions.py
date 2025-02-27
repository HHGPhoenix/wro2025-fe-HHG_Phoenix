def get_angles_edges(yaw, last_yaw, current_edge, running_check=False):
    """
    Get the angles and edges based on the current yaw.

    Args:
        yaw (float): The current yaw angle.
        last_yaw (float): The last recorded yaw angle.
        current_edge (int): The current edge count.
        running_check (bool, optional): Flag to check if the running condition should be evaluated. Defaults to False.

    Returns:
        tuple: A tuple containing the updated current_edge, relative_angle, last_yaw, and running (if running_check is True).
    """
    
    if abs(yaw) > last_yaw + 75:
        current_edge += 1
        last_yaw = last_yaw + 90
    
    if current_edge == 0:
        relative_angle = yaw
    elif yaw < 0:
        relative_angle = yaw + current_edge * 90
    else:
        relative_angle = yaw - current_edge * 90
    
    print(f"Current edge: {current_edge}, Relative angle: {relative_angle}")
    
    if running_check and current_edge >= 11:
        running = False
        
        return current_edge, relative_angle, last_yaw, running
    
    elif running_check:
        running = True
        
        return current_edge, relative_angle, last_yaw, running
        
    return current_edge, relative_angle, last_yaw