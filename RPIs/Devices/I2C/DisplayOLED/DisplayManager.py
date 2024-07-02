import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
# from luma.oled.device import sh1106
from luma.emulator.device import pygame
from PIL import ImageFont, ImageDraw

# A class for writing to an OLED Display
class Display:
    def __init__(self):
        # serial = i2c(port=0, address=0x3C)
        # self.device = sh1106(serial)
        self.device = pygame(width=128, height=64)
        
        # Wake the screen by drawing an outline
        self.clear()

    # Clear the Display
    def clear(self):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")

    # Fill the background of a given image object
    def fill_background(self, draw, color="black"):
        draw.rectangle(self.device.bounding_box, outline="black", fill=color)

    def write_centered_text(self, text, clear_display=True, padding=3):
        with canvas(self.device) as draw:
            if clear_display:
                self.fill_background(draw)
            
            max_font_size = 40
            min_font_size = 10
            width, height = self.device.width, self.device.height
        
            # Determine the appropriate font size and break text into lines if necessary
            lines = []  # Will hold the final lines of text
            for font_size in range(max_font_size, min_font_size - 1, -1):
                font = ImageFont.truetype("arial.ttf", font_size)
                words = text.split()
                current_line = words.pop(0)
                lines = [current_line]
                
                for word in words:
                    # Check if adding the next word exceeds the line width
                    test_line = f"{current_line} {word}"
                    text_width, text_height = draw.textbbox((0, 0), test_line, font=font)[2:4]
                    if text_width <= width - (2 * padding):
                        # If it fits, update the current line
                        current_line = test_line
                        lines[-1] = current_line  # Update the last line
                    else:
                        # Start a new line
                        current_line = word
                        lines.append(current_line)
                
                # Check if the lines fit vertically
                total_text_height = len(lines) * text_height
                if total_text_height <= height - (2 * padding):
                    break  # The text fits with the current font size
            
            # Adjust text position for padding and centering
            padded_height = height - (2 * padding)
            text_y = (padded_height - total_text_height) // 2 + padding  # Start y position
            
            for line in lines:
                text_width, _ = draw.textbbox((0, 0), line, font=font)[2:4]
                text_x = (width - text_width) // 2
                draw.text((text_x, text_y), line, font=font, fill="white")
                text_y += text_height  # Move to the next line

    # Draw a progress bar with optional text
    def draw_progress_bar(self, value, max_value=100, text=None, clear_display=True):
        with canvas(self.device) as draw:
            if clear_display:
                self.fill_background(draw)

            width, height = self.device.width, self.device.height
            bar_width = width - 20
            bar_height = 20
            bar_x = 10
            bar_y = (height - bar_height) // 2
            progress_length = int((value / max_value) * bar_width)

            draw.rectangle((bar_x, bar_y, bar_x + bar_width, bar_y + bar_height), outline="white", fill="black")
            draw.rectangle((bar_x, bar_y, bar_x + progress_length, bar_y + bar_height), outline="white", fill="white")

            if text:
                font = ImageFont.truetype("arial.ttf", 14)
                text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
                text_x = (width - text_width) // 2
                text_y = bar_y + bar_height + 5
                draw.text((text_x, text_y), text, font=font, fill="white")


# Example usage
if __name__ == "__main__":
    display = Display()
    display.write_centered_text("Hello, World! a a a a a a a a a a")
    time.sleep(2)
    display.draw_progress_bar(value=50, max_value=100, text="Loading...")

    for i in range(101):
        display.draw_progress_bar(value=i, max_value=100, text=f"Loading... {i}%")
        time.sleep(0.1)
