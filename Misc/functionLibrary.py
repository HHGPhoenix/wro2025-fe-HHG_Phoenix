import usb

def find_usb_device(self, vendor_id, product_id):
    """
    Find a USB device by vendor and product id.
    
    Parameters:
    vendor_id (int): Vendor ID of the USB device.
    product_id (int): Product ID of the USB device.
    
    Returns:
    usb.core.Device: USB device if found, None otherwise.
    """

    for device in usb.core.find(find_all=True):
        if device.idVendor == vendor_id and device.idProduct == product_id:
            return device
    return None