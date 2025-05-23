import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont, ImageDraw, Image
import threading
import psutil

# A class for writing to an OLED Display
class Display:
    def __init__(self, port=0):
        self.i2c = i2c(port=port, address=0x3C)
        self.device = sh1106(self.i2c)
        self.cpu_usage = 0
        self.memory_usage = 0
        self.header_image = Image.new('1', (self.device.width, 20))  # Assuming header height is 12
        self.header_draw = ImageDraw.Draw(self.header_image)
        self.main_content_image = Image.new('1', (self.device.width, self.device.height - 20))
        self.main_content_draw = ImageDraw.Draw(self.main_content_image)
        self.lock = threading.Lock()  # Lock for thread-safe updates
        self.header_update_thread = threading.Thread(target=self.update_header_info)
        self.header_update_thread.daemon = True
        self.header_update_thread.start()
        self.draw_display_thread = threading.Thread(target=self.draw_display)
        self.draw_display_thread.daemon = True
        self.draw_display_thread.start()
        
    # Clear the Display
    def clear(self):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")

    # Fill the background of a given image object
    def fill_background(self, draw, color="black"):
        draw.rectangle(self.device.bounding_box, outline="black", fill=color)

    def update_header_info(self):
        while True:
            with self.lock:
                self.cpu_usage = psutil.cpu_percent()
                self.memory_usage = psutil.virtual_memory().percent
            time.sleep(0.5)

    def draw_display(self):
        while True:
            with canvas(self.device) as draw:
                # Clear header area
                draw.rectangle((0, 0, self.device.width, 12), fill="black")
                # Draw header
                font = ImageFont.truetype("arial.ttf", 10)
                header_text = f"CPU: {self.cpu_usage}% MEM: {self.memory_usage}%"
                text_width, text_height = draw.textbbox((0, 0), header_text, font=font)[2:4]
                text_x = (self.device.width - text_width) // 2
                draw.text((text_x, 0), header_text, font=font, fill="white")

                with self.lock:
                    # Draw main content
                    draw.bitmap((0, 12), self.main_content_image, fill="white")
            
            time.sleep(0.1)
                    
    def write_centered_text(self, text: str, clear_display=True, padding=3):
        width, height = self.device.width, self.device.height
        header_height = 12  # Height of the header
        height -= header_height + padding

        lines = []
        for font_size in range(40, 9, -1):
            font = ImageFont.truetype("arial.ttf", font_size)
            words = text.split()
            current_line = words.pop(0)# "Hello!".split -> ["Hello!"] -> "Hello!"
            lines = [current_line]

            if len(words) == 0:
                _, text_height = ImageDraw.Draw(self.main_content_image).textbbox((0, 0), current_line, font=font)[2:4]
                total_text_height = text_height
                break
                
            for word in words:
                test_line = f"{current_line} {word}"
                text_width, text_height = ImageDraw.Draw(self.main_content_image).textbbox((0, 0), test_line, font=font)[2:4]
                if text_width <= width - (2 * padding):
                    current_line = test_line
                    lines[-1] = current_line
                else:
                    current_line = word
                    lines.append(current_line)
                

            total_text_height = len(lines) * text_height
            if total_text_height <= height - (2 * padding):
                break

        padded_height = height - (2 * padding)
        text_y = (padded_height - total_text_height) // 2 + padding

        with self.lock:
            self.main_content_draw.rectangle((0, 0, self.device.width, self.device.height - 12), fill="black")
            for line in lines:
                text_width, _ = self.main_content_draw.textbbox((0, 0), line, font=font)[2:4]
                text_x = (width - text_width) // 2
                self.main_content_draw.text((text_x, text_y), line, font=font, fill="white")
                text_y += text_height

    def draw_progress_bar(self, value, max_value=100, text=None, clear_display=True):
        width, height = self.device.width, self.device.height - 12  # Excluding header height
        bar_width = width - 20
        bar_height = 20
        bar_x = 10
        bar_y = (height - bar_height) // 2 - 6  # Centered in the main content area

        progress_length = int((value / max_value) * bar_width)
        
        with self.lock:
            if max_value == value:
                self.main_content_draw.rectangle((0, 0, self.device.width, self.device.height - 12), fill="black", outline="white")
            else:
                self.main_content_draw.rectangle((0, 0, self.device.width, self.device.height - 12), fill="black", outline="black")
                
            self.main_content_draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), outline="white", fill="black")
            self.main_content_draw.rectangle((bar_x, bar_y, bar_x + progress_length, bar_y + bar_height), outline="white", fill="white")

            if text:
                font = ImageFont.truetype("arial.ttf", 14)
                text_width, text_height = self.main_content_draw.textbbox((0, 0), text, font=font)[2:4]
                text_x = (width - text_width) // 2
                text_y = bar_y + bar_height + 5
                self.main_content_draw.text((text_x, text_y), text, font=font, fill="white")


# Example usage
if __name__ == "__main__":
    display = Display()
    display.write_centered_text("Hello, World! a a a a a a a a a a")
    time.sleep(1)
    display.draw_progress_bar(value=50, max_value=100, text="Loading...")

    for i in range(101):
        display.draw_progress_bar(value=i, max_value=100, text=f"Loading... {i}%")
        time.sleep(0.1)
