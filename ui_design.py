"""
UI Design Module
Handles the graphical user interface using Tkinter
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Callable, Tuple
import threading
from PIL import Image, ImageTk
class ScreenshotUI:
    """Main UI class for the screenshot application"""
    
    def __init__(self, config_manager, capture_callback: Callable, 
                 region_callback: Callable, exit_callback: Callable):
        """
        Initialize the UI
        
        Args:
            config_manager: Configuration manager instance
            capture_callback: Callback for full screen capture
            region_callback: Callback for region capture
            exit_callback: Callback for application exit
        """
        self.config = config_manager
        self.capture_callback = capture_callback
        self.region_callback = region_callback
        self.exit_callback = exit_callback
        
        self.root = tk.Tk()
        self.root.title("pxsnap")
        self.root.resizable(True, True)
        self.root.minsize(500, 400)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._apply_custom_styles()
        
        self.preview_image = None
        self.last_screenshot_path = None
        self.region_selection_active = False
        self.user_resized = False
        
        self._build_scrollable_ui()
        self._load_window_geometry()
        
        self._bind_mousewheel()
        
        self.root.bind('<Configure>', self._on_window_resize)
    
    def _apply_custom_styles(self):
        """Apply custom styling to widgets"""
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Info.TLabel', font=('Arial', 10))
        self.style.configure('Action.TButton', font=('Arial', 11, 'bold'))
        self.style.configure('Settings.TFrame', relief='ridge', borderwidth=2)
        
        self.style.map('Action.TButton',
                      foreground=[('pressed', 'white'), ('active', 'white')],
                      background=[('pressed', '#004080'), ('active', '#0066cc')])
    
    def _build_scrollable_ui(self):
        """Build the main UI layout with scrollable frame"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self._build_ui_content()
    
    def _build_ui_content(self):
        """Build the UI content inside the scrollable frame"""
        main_container = ttk.Frame(self.scrollable_frame, padding="20")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.scrollable_frame.columnconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(4, weight=1)
        
        title_label = ttk.Label(main_container, text="📸 pxsnap", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        action_frame = ttk.LabelFrame(main_container, text="Quick Actions", padding="15")
        action_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.fullscreen_btn = ttk.Button(action_frame, text="📷 Full Screen (Print Screen)",
                                        command=self._on_fullscreen_capture,
                                        style='Action.TButton')
        self.fullscreen_btn.grid(row=0, column=0, padx=5, pady=8, sticky=(tk.W, tk.E))
        
        self.region_btn = ttk.Button(action_frame, text="🖼️ Select Region (Ctrl+Print Screen)",
                                    command=self._on_region_capture,
                                    style='Action.TButton')
        self.region_btn.grid(row=1, column=0, padx=5, pady=8, sticky=(tk.W, tk.E))
        
        action_frame.columnconfigure(0, weight=1)
        
        preview_frame = ttk.LabelFrame(main_container, text="Preview", padding="15")
        preview_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.preview_container = ttk.Frame(preview_frame)
        self.preview_container.pack(expand=True, fill=tk.BOTH)
        
        self.preview_label = ttk.Label(self.preview_container, text="No screenshot taken yet",
                                      style='Info.TLabel')
        self.preview_label.pack(expand=True)
        
        settings_frame = ttk.LabelFrame(main_container, text="Settings", padding="15",
                                       style='Settings.TFrame')
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(settings_frame, text="Save Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.dir_var = tk.StringVar(value=self.config.get("save_directory"))
        dir_entry = ttk.Entry(settings_frame, textvariable=self.dir_var, width=50)
        dir_entry.grid(row=0, column=1, padx=10, pady=5, sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(settings_frame, text="Browse...", 
                               command=self._browse_directory)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="File Prefix:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.prefix_var = tk.StringVar(value=self.config.get("file_prefix"))
        prefix_entry = ttk.Entry(settings_frame, textvariable=self.prefix_var, width=30)
        prefix_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Format:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value=self.config.get("file_format"))
        format_combo = ttk.Combobox(settings_frame, textvariable=self.format_var,
                                   values=["png", "jpg"], width=15, state="readonly")
        format_combo.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        self.preview_var = tk.BooleanVar(value=self.config.get("show_preview"))
        preview_check = ttk.Checkbutton(settings_frame, text="Show preview after capture",
                                       variable=self.preview_var)
        preview_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=8)
        
        self.open_folder_var = tk.BooleanVar(value=self.config.get("auto_open_folder"))
        open_check = ttk.Checkbutton(settings_frame, text="Open folder after capture",
                                    variable=self.open_folder_var)
        open_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=8)
        
        apply_btn = ttk.Button(settings_frame, text="✓ Apply Settings",
                              command=self._apply_settings, style='Action.TButton')
        apply_btn.grid(row=5, column=0, columnspan=3, pady=15)
        
        settings_frame.columnconfigure(1, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_container, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        main_container.columnconfigure(0, weight=1)
    
    def _bind_mousewheel(self):
        """Bind mousewheel to scroll the canvas"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _load_window_geometry(self):
        """Load and apply window geometry from config"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        width = max(500, min(int(screen_width * 0.7), 1200))
        height = max(400, min(int(screen_height * 0.7), 900))
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        saved_geometry = self.config.get("window_geometry")
        if saved_geometry:
            try:
                self.root.geometry(saved_geometry)
                return
            except:
                pass
        
        geometry = f"{width}x{height}+{x}+{y}"
        self.root.geometry(geometry)
    
    def _save_window_geometry(self):
        """Save current window geometry to config"""
        if self.user_resized:
            self.config.set("window_geometry", self.root.geometry())
    
    def _on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget == self.root and self.root.winfo_width() > 1 and self.root.winfo_height() > 1:
            self.user_resized = True
    
    def _browse_directory(self):
        """Open directory browser dialog"""
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)
    
    def _apply_settings(self):
        """Apply current settings"""
        try:
            updates = {
                "save_directory": self.dir_var.get(),
                "file_prefix": self.prefix_var.get(),
                "file_format": self.format_var.get(),
                "show_preview": self.preview_var.get(),
                "auto_open_folder": self.open_folder_var.get()
            }
            self.config.update(updates)
            self._update_status("✓ Settings applied successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def _on_fullscreen_capture(self):
        """Handle full screen capture button click"""
        self._update_status("Capturing full screen...")
        threading.Thread(target=self.capture_callback, daemon=True).start()
    
    def _on_region_capture(self):
        """Handle region capture button click"""
        if not self.region_selection_active:
            self._update_status("Click and drag to select region...")
            self.region_selection_active = True
            self.region_btn.config(state="disabled")
            threading.Thread(target=self.region_callback, daemon=True).start()
    
    def update_preview(self, image_path: str):
        """Update the preview with a new screenshot"""
        try:
            if self.preview_var.get():
                image = Image.open(image_path)
                max_size = (500, 400)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                
                self.preview_label.config(image=photo, text="")
                self.preview_label.image = photo
                
                self.last_screenshot_path = image_path
                self._update_status(f"✓ Screenshot saved: {os.path.basename(image_path)}")
                
                if self.open_folder_var.get():
                    os.startfile(os.path.dirname(image_path))
                
                self.root.after(100, self._update_scroll_region)
                
                if not self.user_resized:
                    self.root.after(200, self._auto_adjust_window_size)
        except Exception as e:
            print(f"Error updating preview: {e}")
    
    def _auto_adjust_window_size(self):
        """Automatically adjust window size to fit content if not manually resized"""
        if not self.user_resized:
            self.scrollable_frame.update_idletasks()
            content_height = self.scrollable_frame.winfo_height()
            
            current_width = self.root.winfo_width()
            current_height = self.root.winfo_height()
            
            screen_height = self.root.winfo_screenheight()
            
            new_height = min(content_height + 100, int(screen_height * 0.9))
            
            if new_height > current_height + 50:
                self.root.geometry(f"{current_width}x{new_height}")
    
    def _update_scroll_region(self):
        """Update the scroll region of the canvas"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _update_status(self, message: str):
        """Update status bar message"""
        self.status_var.set(message)
    
    def enable_region_button(self):
        """Re-enable region selection button"""
        self.region_selection_active = False
        self.region_btn.config(state="normal")
    
    def show_error(self, title: str, message: str):
        """Show error message dialog"""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """Show info message dialog"""
        messagebox.showinfo(title, message)
    
    def run(self):
        """Start the UI main loop"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()
    
    def _on_closing(self):
        """Handle window closing"""
        self._save_window_geometry()
        self.exit_callback()
        self.root.destroy()