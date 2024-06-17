import usb

def find_usb_device(self, vendor_id, product_id):
        # Find the device by vendor and product id
        for device in usb.core.find(find_all=True):
            if device.idVendor == vendor_id and device.idProduct == product_id:
                return device
        return None