"""
Main Application Entry Point
Orchestrates the screenshot utility components
"""

import os
import sys
import keyboard
import threading
from pathlib import Path
from typing import Optional, Tuple

from config_manager import ConfigManager
from screenshot_capture import ScreenshotCapture
from ui_design import ScreenshotUI

class ScreenshotApp:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        """Initialize the screenshot application"""
        self.config = ConfigManager()
        self.capture = ScreenshotCapture(
            save_directory=self.config.get("save_directory"),
            file_prefix=self.config.get("file_prefix"),
            file_format=self.config.get("file_format"),
            timestamp_format=self.config.get("timestamp_format")
        )
        
        self.ui = None
        self.region_start = None
        self.region_overlay = None
        self.region_canvas = None
        self.running = True
        
        self._init_ui()
        self._setup_hotkeys()
    
    def _init_ui(self):
        """Initialize the user interface"""
        self.ui = ScreenshotUI(
            config_manager=self.config,
            capture_callback=self.capture_fullscreen,
            region_callback=self.start_region_selection,
            exit_callback=self.cleanup
        )
    
    def _setup_hotkeys(self):
        """Setup global hotkeys for screenshot capture"""
        try:
            keyboard.add_hotkey(
                self.config.get("hotkey_fullscreen"),
                self.capture_fullscreen,
                suppress=True
            )
            
            keyboard.add_hotkey(
                self.config.get("hotkey_region"),
                self.start_region_selection,
                suppress=True
            )
        except Exception as e:
            print(f"Error setting up hotkeys: {e}")
    
    def capture_fullscreen(self):
        """Capture full screen screenshot"""
        try:
            screenshot = self.capture.capture_full_screen()
            if screenshot:
                screenshot = self.capture.add_timestamp(screenshot)
                filepath = self.capture.save_screenshot(screenshot)
                if filepath:
                    if self.ui and self.ui.root:
                        self.ui.root.after(0, self.ui.update_preview, filepath)
        except Exception as e:
            if self.ui:
                self.ui.root.after(0, self.ui.show_error, "Capture Error", str(e))
    
    def start_region_selection(self):
        """Start region selection process"""
        try:
            import pyautogui
            import tkinter as tk
            
            screen_width, screen_height = self.capture.get_screen_size()
            
            self.region_overlay = tk.Toplevel()
            self.region_overlay.title("Select Region")
            self.region_overlay.geometry(f"{screen_width}x{screen_height}+0+0")
            self.region_overlay.attributes('-fullscreen', True)
            self.region_overlay.attributes('-alpha', 0.3)
            self.region_overlay.attributes('-topmost', True)
            self.region_overlay.configure(background='black')
            
            self.region_canvas = tk.Canvas(
                self.region_overlay,
                width=screen_width,
                height=screen_height,
                highlightthickness=0,
                background='black'
            )
            self.region_canvas.pack(fill=tk.BOTH, expand=True)
            
            self.region_canvas.bind('<Button-1>', self._on_region_start)
            self.region_canvas.bind('<B1-Motion>', self._on_region_drag)
            self.region_canvas.bind('<ButtonRelease-1>', self._on_region_end)
            self.region_overlay.bind('<Escape>', self._cancel_region_selection)
            
            self.region_start = None
            self.region_rect = None
            
            self.region_overlay.focus_set()
            
        except Exception as e:
            if self.ui:
                self.ui.root.after(0, self.ui.show_error, "Region Selection Error", str(e))
            if self.ui:
                self.ui.root.after(0, self.ui.enable_region_button)
    
    def _on_region_start(self, event):
        """Handle mouse down event for region selection"""
        self.region_start = (event.x, event.y)
        
        self.region_rect = self.region_canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline='red', width=2, fill='white', stipple='gray50'
        )
    
    def _on_region_drag(self, event):
        """Handle mouse drag event for region selection"""
        if self.region_start and self.region_rect:
            self.region_canvas.coords(
                self.region_rect,
                self.region_start[0], self.region_start[1],
                event.x, event.y
            )
    
    def _on_region_end(self, event):
        """Handle mouse up event for region selection"""
        if self.region_start:
            x1, y1 = self.region_start
            x2, y2 = event.x, event.y
            
            if self.region_overlay:
                self.region_overlay.destroy()
                self.region_overlay = None
                self.region_canvas = None
            
            if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                screenshot = self.capture.capture_region(x1, y1, x2, y2)
                if screenshot:
                    screenshot = self.capture.add_timestamp(screenshot)
                    filepath = self.capture.save_screenshot(screenshot)
                    if filepath and self.ui:
                        self.ui.root.after(0, self.ui.update_preview, filepath)
            else:
                if self.ui:
                    self.ui.root.after(0, self.ui._update_status, "Region too small - please select a larger area")
        
        self.region_start = None
        self.region_rect = None
        if self.ui:
            self.ui.root.after(0, self.ui.enable_region_button)
    
    def _cancel_region_selection(self, event=None):
        """Cancel region selection"""
        if self.region_overlay:
            self.region_overlay.destroy()
            self.region_overlay = None
            self.region_canvas = None
        
        self.region_start = None
        self.region_rect = None
        if self.ui:
            self.ui.root.after(0, self.ui.enable_region_button)
            self.ui.root.after(0, self.ui._update_status, "Region selection cancelled")
    
    def cleanup(self):
        """Clean up resources before exit"""
        self.running = False
        
        try:
            keyboard.remove_all_hotkeys()
        except:
            pass
        
        if self.region_overlay:
            try:
                self.region_overlay.destroy()
            except:
                pass
    
    def run(self):
        """Run the application"""
        try:
            if self.ui:
                self.ui.run()
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            print(f"Application error: {e}")
            self.cleanup()

def main():
    """Main entry point"""
    try:
        app = ScreenshotApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()