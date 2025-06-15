def get_angles_edges(yaw, last_yaw, current_edge, running_check=False, edge_cooldown=0):
    """
    Get the angles and edges based on the current yaw.

    Args:
        yaw (float): The current yaw angle.
        last_yaw (float): The last recorded yaw angle.
        current_edge (int): The current edge count.
        running_check (bool, optional): Flag to check if the running condition should be evaluated. Defaults to False.
        edge_cooldown (int, optional): Countdown to prevent counting edges too frequently. Defaults to 0.
        
    Returns:
        tuple: A tuple containing the updated current_edge, relative_angle, last_yaw, running (if running_check is True),
               and edge_cooldown.
    """
    
    # Decrement the cooldown if it's active
    if edge_cooldown > 0:
        edge_cooldown -= 1
    
    angle_diff = abs(yaw - last_yaw)
    if angle_diff > 80 and edge_cooldown == 0:
        current_edge += 1
        last_yaw = yaw  # Store the actual yaw where we detected the edge
        edge_cooldown = 10  # Set cooldown to prevent counting multiple edges during obstacle avoidance
    
    if current_edge == 0:
        relative_angle = yaw
    elif yaw < 0:
        relative_angle = yaw + current_edge * 90
    else:
        relative_angle = yaw - current_edge * 90
    
    print(f"Current edge: {current_edge}, Relative angle: {relative_angle}")
    
    if running_check and current_edge >= 12:
        running = False
        
        return current_edge, relative_angle, last_yaw, running, edge_cooldown
    
    elif running_check:
        running = True
        
        return current_edge, relative_angle, last_yaw, running, edge_cooldown
        
    return current_edge, relative_angle, last_yaw, edge_cooldown