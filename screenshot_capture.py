"""
Screenshot Capture Module
Handles screenshot capturing functionality
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
import pyautogui
from PIL import Image, ImageDraw, ImageFont

class ScreenshotCapture:
    """Handles screenshot capturing and saving operations"""
    
    def __init__(self, save_directory: str, file_prefix: str = "screenshot", 
                 file_format: str = "png", timestamp_format: str = "%Y%m%d_%H%M%S"):
        """
        Initialize screenshot capture
        
        Args:
            save_directory: Directory to save screenshots
            file_prefix: Prefix for screenshot filenames
            file_format: Image format (png, jpg, etc.)
            timestamp_format: Format for timestamp in filename
        """
        self.save_directory = Path(save_directory)
        self.file_prefix = file_prefix
        self.file_format = file_format.lower()
        self.timestamp_format = timestamp_format
        
        # Ensure save directory exists
        self.save_directory.mkdir(parents=True, exist_ok=True)
    
    def capture_full_screen(self) -> Optional[Image.Image]:
        """
        Capture full screen screenshot
        
        Returns:
            PIL Image object or None if failed
        """
        try:
            screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            print(f"Error capturing full screen: {e}")
            return None
    
    def capture_region(self, x1: int, y1: int, x2: int, y2: int) -> Optional[Image.Image]:
        """
        Capture a specific region of the screen
        
        Args:
            x1, y1: Top-left coordinates
            x2, y2: Bottom-right coordinates
            
        Returns:
            PIL Image object or None if failed
        """
        try:
            # Ensure coordinates are in correct order
            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # Validate region is within screen bounds
            screen_width, screen_height = self.get_screen_size()
            if left < 0 or top < 0 or width <= 0 or height <= 0:
                return None
            if left + width > screen_width or top + height > screen_height:
                return None
            
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return screenshot
        except Exception as e:
            print(f"Error capturing region: {e}")
            return None
    
    def save_screenshot(self, image: Image.Image, custom_name: Optional[str] = None) -> Optional[str]:
        """
        Save screenshot to file
        
        Args:
            image: PIL Image object to save
            custom_name: Optional custom filename
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            if custom_name:
                filename = f"{custom_name}.{self.file_format}"
            else:
                timestamp = datetime.now().strftime(self.timestamp_format)
                filename = f"{self.file_prefix}_{timestamp}.{self.file_format}"
            
            filepath = self.save_directory / filename
            
            # Save with optimization
            if self.file_format == 'png':
                image.save(filepath, optimize=True)
            elif self.file_format == 'jpg':
                image.save(filepath, quality=95, optimize=True)
            else:
                image.save(filepath)
            
            return str(filepath)
        except Exception as e:
            print(f"Error saving screenshot: {e}")
            return None
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get current screen resolution
        
        Returns:
            Tuple of (width, height)
        """
        try:
            return pyautogui.size()
        except Exception as e:
            print(f"Error getting screen size: {e}")
            return (1920, 1080)  # Default fallback
    
    def add_timestamp(self, image: Image.Image, position: str = "bottom-right") -> Image.Image:
        """
        Add timestamp to screenshot
        
        Args:
            image: PIL Image object
            position: Position of timestamp ("top-left", "top-right", "bottom-left", "bottom-right")
            
        Returns:
            Image with timestamp added
        """
        try:
            # Create a copy to avoid modifying the original
            image = image.copy()
            draw = ImageDraw.Draw(image)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Get text size
            bbox = draw.textbbox((0, 0), timestamp, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position with margin
            margin = 10
            img_width, img_height = image.size
            
            if position == "top-left":
                x, y = margin, margin
            elif position == "top-right":
                x, y = img_width - text_width - margin, margin
            elif position == "bottom-left":
                x, y = margin, img_height - text_height - margin
            else:  # bottom-right
                x, y = img_width - text_width - margin, img_height - text_height - margin
            
            # Ensure text stays within image bounds
            x = max(margin, min(x, img_width - text_width - margin))
            y = max(margin, min(y, img_height - text_height - margin))
            
            # Draw text with shadow for better visibility
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), timestamp, 
                     font=font, fill="black")
            draw.text((x, y), timestamp, font=font, fill="white")
            
            return image
        except Exception as e:
            print(f"Error adding timestamp: {e}")
            return image