import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import os
import sys
import subprocess
import threading
from pathlib import Path
import re

class TikTokDownloader:
    @staticmethod
    def get_system_font(size=9, weight='normal'):
        """Get appropriate font for current OS"""
        if sys.platform == 'win32':
            return ('Segoe UI', size, weight)
        elif sys.platform == 'darwin':
            return ('SF Pro Display', size, weight) if weight != 'normal' else ('SF Pro Text', size, weight)
        else:  # Linux and other Unix-like
            return ('Ubuntu', size, weight) if weight != 'normal' else ('DejaVu Sans', size, weight)
    
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Universal Video Downloader")
        self.root.geometry("780x650")
        self.root.resizable(True, True)
        
        # Dark mode colors - Modern dark theme
        self.colors = {
            'bg_primary': '#1a1a1a',       # Main dark background
            'bg_secondary': '#2d2d2d',     # Card backgrounds
            'bg_tertiary': '#3a3a3a',      # Input backgrounds
            'accent_blue': '#0078d4',      # Primary blue accent
            'accent_blue_hover': '#106ebe', # Blue hover state
            'accent_success': '#00bcf2',   # Success blue
            'text_primary': '#ffffff',     # Primary white text
            'text_secondary': '#cccccc',   # Secondary light text
            'text_muted': '#999999',       # Muted gray text
            'border': '#404040',           # Border color
            'error': '#ff6b6b',           # Red error (kept)
            'warning': '#ffd700',         # Gold warning
            'shadow': '#000000'           # Shadow color
        }
        
        # Variables
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.remove_metadata = tk.BooleanVar()
        self.mirror_video = tk.BooleanVar()
        self.speed_change = tk.BooleanVar()
        self.brightness_change = tk.BooleanVar()
        self.crop_video = tk.BooleanVar()
        self.add_watermark = tk.BooleanVar()
        self.batch_download = tk.BooleanVar()
        self.max_videos = tk.StringVar(value="10")
        self.url_var = tk.StringVar()
        
        # Track if current URL is TikTok profile
        self.is_tiktok_profile = False
        
        # Track downloaded videos count for manual limiting
        self.downloaded_count = 0
        self.max_download_limit = 0
        
        self.setup_modern_style()
        self.setup_ui()
        
    def setup_modern_style(self):
        """Setup modern dark theme styling for the application"""
        # Configure root window with dark background
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Create and configure dark theme style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure modern dark button styles
        self.style.configure(
            'Modern.TButton',
            background=self.colors['accent_blue'],
            foreground=self.colors['text_primary'],
            borderwidth=1,
            relief='flat',
            focuscolor='none',
            padding=(20, 10),
            font=self.get_system_font(10, 'normal')
        )
        
        self.style.map(
            'Modern.TButton',
            background=[('active', self.colors['accent_blue_hover']),
                       ('pressed', self.colors['accent_success'])]
        )
        
        # Configure accent button (download button)
        self.style.configure(
            'Accent.TButton',
            background=self.colors['accent_blue'],
            foreground=self.colors['text_primary'],
            borderwidth=1,
            relief='flat',
            focuscolor='none',
            padding=(25, 14),
            font=self.get_system_font(11, 'bold')
        )
        
        self.style.map(
            'Accent.TButton',
            background=[('active', self.colors['accent_blue_hover']),
                       ('pressed', self.colors['accent_success'])]
        )
        
        # Configure modern dark entry style
        self.style.configure(
            'Modern.TEntry',
            fieldbackground=self.colors['bg_tertiary'],
            foreground=self.colors['text_primary'],
            borderwidth=1,
            relief='solid',
            bordercolor=self.colors['border'],
            padding=12,
            font=self.get_system_font(10, 'normal')
        )
        
        self.style.map(
            'Modern.TEntry',
            bordercolor=[('focus', self.colors['accent_blue'])]
        )
        
        # Configure modern dark label styles
        self.style.configure(
            'Title.TLabel',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_primary'],
            font=self.get_system_font(22, 'bold')
        )
        
        self.style.configure(
            'Subtitle.TLabel',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_muted'],
            font=self.get_system_font(10, 'normal')
        )
        
        self.style.configure(
            'Heading.TLabel',
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_primary'],
            font=self.get_system_font(11, 'bold')
        )
        
        self.style.configure(
            'Modern.TLabel',
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_secondary'],
            font=self.get_system_font(9, 'normal')
        )
        
        self.style.configure(
            'Status.TLabel',
            background=self.colors['bg_primary'],
            foreground=self.colors['text_muted'],
            font=self.get_system_font(9, 'italic')
        )
        
        # Configure modern dark frame styles
        self.style.configure(
            'Modern.TFrame',
            background=self.colors['bg_primary'],
            relief='flat'
        )
        
        self.style.configure(
            'Card.TFrame',
            background=self.colors['bg_secondary'],
            relief='solid',
            borderwidth=1,
            bordercolor=self.colors['border']
        )
        
        # Add container frame style
        self.style.configure(
            'Container.TFrame',
            background=self.colors['bg_primary'],
            relief='flat'
        )
        
        # Configure modern dark labelframe style
        self.style.configure(
            'Modern.TLabelframe',
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_primary'],
            borderwidth=1,
            relief='solid',
            bordercolor=self.colors['border'],
            font=self.get_system_font(10, 'bold')
        )
        
        self.style.configure(
            'Modern.TLabelframe.Label',
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_primary']
        )
        
        # Configure modern dark checkbutton style
        self.style.configure(
            'Modern.TCheckbutton',
            background=self.colors['bg_secondary'],
            foreground=self.colors['text_secondary'],
            font=self.get_system_font(9, 'normal'),
            focuscolor='none'
        )
        
        self.style.map(
            'Modern.TCheckbutton',
            background=[('active', self.colors['bg_secondary'])],
            foreground=[('active', self.colors['text_primary'])]
        )
        
        # Configure modern dark progressbar style
        self.style.configure(
            'Modern.Horizontal.TProgressbar',
            background=self.colors['accent_success'],
            troughcolor=self.colors['bg_tertiary'],
            borderwidth=0,
            lightcolor=self.colors['accent_success'],
            darkcolor=self.colors['accent_success']
        )
        
    def setup_ui(self):
        # Create main canvas and scrollbar for scrollable content with dark theme
        canvas = tk.Canvas(self.root, bg=self.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        # Main container with modern styling
        main_container = ttk.Frame(canvas, style='Modern.TFrame')
        
        # Configure scrolling and canvas width binding
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Auto-hide scrollbar when not needed
            bbox = canvas.bbox("all")
            if bbox and bbox[3] > canvas.winfo_height():
                scrollbar.pack(side="right", fill="y")
            else:
                scrollbar.pack_forget()
        
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        main_container.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_width)
        
        canvas_window = canvas.create_window((0, 0), window=main_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas - scrollbar will be packed conditionally
        canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store canvas reference for later use
        self.canvas = canvas
        self.main_container = main_container
        
        # Add overall padding to content with optimized spacing
        content_frame = ttk.Frame(self.main_container, style='Container.TFrame')
        content_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Update main container reference for content
        self.main_container = content_frame
        
        # Header section with modern spacing
        header_frame = ttk.Frame(self.main_container, style='Container.TFrame')
        header_frame.pack(fill='x', pady=(0, 30))
        
        # App title with better typography
        title_label = ttk.Label(header_frame, text="🎯 Universal Video Downloader", 
                               style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Download video dari TikTok, YouTube, Facebook & 1000+ platform", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(pady=(8, 0))
        
        # Main input section container
        input_section = ttk.Frame(self.main_container, style='Container.TFrame')
        input_section.pack(fill='x', pady=(0, 25))
        
        # URL Input Card with modern styling
        url_card = ttk.Frame(input_section, style='Card.TFrame')
        url_card.pack(fill='x', pady=(0, 12), padx=2, ipady=18)
        
        url_content = ttk.Frame(url_card, style='Card.TFrame')
        url_content.pack(fill='x', padx=18, pady=12)
        
        ttk.Label(url_content, text="🔗 Video URL", style='Heading.TLabel').pack(anchor='w', pady=(0, 8))
        
        url_input_frame = ttk.Frame(url_content, style='Card.TFrame')
        url_input_frame.pack(fill='x')
        
        self.url_entry = ttk.Entry(url_input_frame, textvariable=self.url_var, 
                                  style='Modern.TEntry', width=45)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 12))
        
        # Bind URL change event to check for TikTok profile
        self.url_var.trace('w', self.on_url_change)
        
        paste_btn = ttk.Button(url_input_frame, text="📋 Paste", 
                              command=self.paste_url, style='Modern.TButton')
        paste_btn.pack(side='right')
        
        # Download Path Card
        path_card = ttk.Frame(input_section, style='Card.TFrame')
        path_card.pack(fill='x', padx=2, ipady=18)
        
        path_content = ttk.Frame(path_card, style='Card.TFrame')
        path_content.pack(fill='x', padx=18, pady=12)
        
        ttk.Label(path_content, text="📁 Folder Penyimpanan", style='Heading.TLabel').pack(anchor='w', pady=(0, 8))
        
        path_input_frame = ttk.Frame(path_content, style='Card.TFrame')
        path_input_frame.pack(fill='x')
        
        self.path_entry = ttk.Entry(path_input_frame, textvariable=self.download_path, 
                                   style='Modern.TEntry', state="readonly")
        self.path_entry.pack(side='left', fill='x', expand=True, padx=(0, 12))
        
        browse_btn = ttk.Button(path_input_frame, text="🗂️ Browse", 
                               command=self.browse_folder, style='Modern.TButton')
        browse_btn.pack(side='right')
        
        # Options section container
        options_section = ttk.Frame(self.main_container, style='Container.TFrame')
        options_section.pack(fill='x', pady=(0, 25))
        
        # Basic Options Card with improved layout
        basic_options_card = ttk.LabelFrame(options_section, text="⚙️ Opsi Dasar", 
                                           style='Modern.TLabelframe')
        basic_options_card.pack(fill='x', pady=(0, 12), padx=2, ipady=12)
        
        basic_content = ttk.Frame(basic_options_card, style='Modern.TLabelframe')
        basic_content.pack(fill='x', padx=18, pady=10)
        
        metadata_check = ttk.Checkbutton(basic_content, 
                                        text="🛡️ Hapus metadata video (memerlukan FFmpeg)", 
                                        variable=self.remove_metadata,
                                        style='Modern.TCheckbutton')
        metadata_check.pack(anchor='w')
        
        # Anti-Copyright Options Card with better spacing
        anticopy_card = ttk.LabelFrame(options_section, text="🚫 Anti-Copyright Features", 
                                      style='Modern.TLabelframe')
        anticopy_card.pack(fill='x', padx=2, ipady=12)
        
        anticopy_content = ttk.Frame(anticopy_card, style='Modern.TLabelframe')
        anticopy_content.pack(fill='x', padx=18, pady=10)
        
        # Create a grid-like layout for checkboxes
        checkbox_container = ttk.Frame(anticopy_content, style='Modern.TLabelframe')
        checkbox_container.pack(fill='x')
        
        # Left column checkboxes
        left_column = ttk.Frame(checkbox_container, style='Modern.TLabelframe')
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        mirror_check = ttk.Checkbutton(left_column, 
                                      text="🪞 Mirror video (flip horizontal)", 
                                      variable=self.mirror_video,
                                      style='Modern.TCheckbutton')
        mirror_check.pack(anchor='w', pady=3)
        
        speed_check = ttk.Checkbutton(left_column, 
                                     text="⚡ Ubah kecepatan (0.95x - anti algoritma)", 
                                     variable=self.speed_change,
                                     style='Modern.TCheckbutton')
        speed_check.pack(anchor='w', pady=3)
        
        brightness_check = ttk.Checkbutton(left_column, 
                                          text="🌟 Adjust brightness & contrast", 
                                          variable=self.brightness_change,
                                          style='Modern.TCheckbutton')
        brightness_check.pack(anchor='w', pady=3)
        
        # Right column checkboxes  
        right_column = ttk.Frame(checkbox_container, style='Modern.TLabelframe')
        right_column.pack(side='right', fill='both', expand=True)
        
        crop_check = ttk.Checkbutton(right_column, 
                                    text="✂️ Crop video (remove 2% edges)", 
                                    variable=self.crop_video,
                                    style='Modern.TCheckbutton')
        crop_check.pack(anchor='w', pady=3)
        
        watermark_check = ttk.Checkbutton(right_column, 
                                         text="💧 Add subtle watermark", 
                                         variable=self.add_watermark,
                                         style='Modern.TCheckbutton')
        watermark_check.pack(anchor='w', pady=3)
        
        # TikTok Batch Download Options (initially hidden)
        self.batch_card = ttk.LabelFrame(options_section, text="📦 TikTok Batch Download", 
                                        style='Modern.TLabelframe')
        # Don't pack initially - will be shown when TikTok profile detected
        
        batch_content = ttk.Frame(self.batch_card, style='Modern.TLabelframe')
        batch_content.pack(fill='x', padx=18, pady=10)
        
        batch_check = ttk.Checkbutton(batch_content, 
                                     text="📥 Download semua video dari profile ini", 
                                     variable=self.batch_download,
                                     style='Modern.TCheckbutton')
        batch_check.pack(anchor='w', pady=(0, 8))
        
        # Max videos setting
        max_videos_frame = ttk.Frame(batch_content, style='Modern.TLabelframe')
        max_videos_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(max_videos_frame, text="🔢 Maksimal video:", 
                 style='Modern.TLabel').pack(side='left')
        
        max_videos_entry = ttk.Entry(max_videos_frame, textvariable=self.max_videos, 
                                    style='Modern.TEntry', width=5)
        max_videos_entry.pack(side='left', padx=(10, 0))
        
        ttk.Label(max_videos_frame, text="(kosongkan untuk semua | ⚠️ fitur beta)", 
                 style='Modern.TLabel').pack(side='left', padx=(10, 0))
        
        # Action section container
        action_section = ttk.Frame(self.main_container, style='Container.TFrame')
        action_section.pack(fill='x', pady=(0, 0))
        
        # Download Button with better styling
        button_frame = ttk.Frame(action_section, style='Container.TFrame')
        button_frame.pack(fill='x', pady=(15, 20))
        
        # Buttons container for centering multiple buttons
        buttons_container = ttk.Frame(button_frame, style='Container.TFrame')
        buttons_container.pack()
        
        self.download_btn = ttk.Button(buttons_container, text="🚀 Unduh Video", 
                                      command=self.start_download, style='Accent.TButton')
        self.download_btn.pack(side='left', padx=(0, 15))
        
        # AI Auto Clipper button
        self.ai_clipper_btn = ttk.Button(buttons_container, text="🤖 AI Auto Clipper", 
                                        command=self.open_ai_clipper, style='Modern.TButton')
        self.ai_clipper_btn.pack(side='left')
        
        # Progress Section with modern layout
        progress_frame = ttk.Frame(action_section, style='Container.TFrame')
        progress_frame.pack(fill='x', pady=(0, 25))
        
        # Progress bar container for centering
        progress_container = ttk.Frame(progress_frame, style='Container.TFrame')
        progress_container.pack()
        
        self.progress = ttk.Progressbar(progress_container, mode='indeterminate',
                                       style='Modern.Horizontal.TProgressbar',
                                       length=400)
        self.progress.pack()
        
        # Status label with better positioning
        self.status_label = ttk.Label(progress_frame, text="✨ Siap untuk mengunduh", 
                                     style='Status.TLabel')
        self.status_label.pack(pady=(12, 0))
        
        # Supported platforms info
        platforms_frame = ttk.Frame(action_section, style='Container.TFrame')
        platforms_frame.pack(fill='x', pady=(10, 0))
        
        platforms_label = ttk.Label(platforms_frame, 
                                   text="📡 Supported: TikTok • YouTube • Facebook • Instagram • Twitter • 1000+ more", 
                                   style='Status.TLabel')
        platforms_label.pack()
        
    def on_url_change(self, *args):
        """Handle URL change to detect TikTok profile and show/hide batch options"""
        url = self.url_var.get().strip()
        
        if url and self.validate_url(url):
            platform = self.detect_platform(url)
            
            if platform == 'TikTok' and self.is_tiktok_profile:
                # Show batch download options
                self.batch_card.pack(fill='x', padx=2, ipady=12, pady=(12, 0))
            else:
                # Hide batch download options
                self.batch_card.pack_forget()
                self.batch_download.set(False)
        else:
            # Hide batch download options for invalid URLs
            self.batch_card.pack_forget()
            self.batch_download.set(False)
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_var.set(clipboard_content)
        except tk.TclError:
            pass
            
    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
            
    def open_ai_clipper(self):
        """Open AI Auto Clipper window"""
        try:
            # Import and run AI clipper
            import subprocess
            import sys
            
            # Check if ai_clipper.py exists
            ai_clipper_path = os.path.join(os.path.dirname(__file__), 'ai_clipper.py')
            if not os.path.exists(ai_clipper_path):
                messagebox.showerror("❌ Error", "AI Auto Clipper tidak ditemukan!\nPastikan file ai_clipper.py ada di folder yang sama.")
                return
            
            # Run AI clipper in new process
            subprocess.Popen([sys.executable, ai_clipper_path])
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Gagal membuka AI Auto Clipper: {str(e)}")
            
    def validate_url(self, url):
        """Validate video URL from supported platforms"""
        # Comprehensive patterns for major video platforms
        video_patterns = [
            # TikTok patterns (videos and profiles)
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:vm|vt)\.tiktok\.com/\w+',
            r'https?://(?:www\.)?tiktok\.com/t/\w+',
            r'https?://m\.tiktok\.com/v/\d+\.html',
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/?$',  # Profile URLs
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/?(?:\?.*)?$',  # Profile with params
            
            # YouTube patterns
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
            
            # Facebook patterns
            r'https?://(?:www\.)?facebook\.com/.*/videos/\d+',
            r'https?://(?:www\.)?facebook\.com/watch/?\?v=\d+',
            r'https?://fb\.watch/[\w-]+',
            
            # Instagram patterns
            r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/reel/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/tv/[\w-]+',
            
            # Twitter patterns
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+',
            
            # Generic video patterns (for other platforms)
            r'https?://.*\.(mp4|avi|mov|mkv|webm|flv|m4v)',
            r'https?://.*/(video|watch|v)[\?/].*'
        ]
        
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in video_patterns)
    
    def detect_platform(self, url):
        """Detect video platform from URL"""
        url_lower = url.lower()
        
        if 'tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower or 'vt.tiktok.com' in url_lower:
            # Check if it's a TikTok profile URL
            self.is_tiktok_profile = self.is_tiktok_profile_url(url)
            return 'TikTok'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'YouTube'
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return 'Facebook'
        elif 'instagram.com' in url_lower:
            return 'Instagram'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'Twitter'
        else:
            return 'Generic'
    
    def is_tiktok_profile_url(self, url):
        """Check if URL is a TikTok profile (not individual video)"""
        profile_patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/?$',  # Profile main page
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/?(?:\?.*)?$',  # Profile with query params
        ]
        
        return any(re.match(pattern, url) for pattern in profile_patterns)
    
    def get_platform_options(self, download_path, platform):
        """Get platform-specific yt-dlp options"""
        # Base options for all platforms
        base_opts = {
            'outtmpl': os.path.join(download_path, '%(uploader)s_%(title)s_%(id)s.%(ext)s'),
            'ignoreerrors': False,
            'no_warnings': True,
            'extractflat': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'quiet': True,
            'no_color': True,
            'extract_flat': False,
            'cookiefile': None,
            'progress_hooks': [self.progress_hook],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        # Platform-specific optimizations
        if platform == 'TikTok':
            base_opts.update({
                'format': 'best[ext=mp4]/best',  # TikTok biasanya mp4
            })
            
            # Handle batch download for TikTok profiles
            if self.is_tiktok_profile and self.batch_download.get():
                max_videos = self.max_videos.get().strip()
                if max_videos and max_videos.isdigit():
                    # Multiple approaches to ensure limiting works
                    limit = int(max_videos)
                    
                    # Method 1: Standard playlist limiting
                    base_opts['playliststart'] = 1
                    base_opts['playlistend'] = limit
                    
                    # Method 2: Max downloads
                    base_opts['max_downloads'] = limit
                    
                    # Method 3: Use playlist-items format (1-N)
                    base_opts['playlist_items'] = f"1-{limit}"
                
                # Update output template for batch download
                base_opts['outtmpl'] = os.path.join(download_path, '%(uploader)s', '%(title)s_%(id)s.%(ext)s')
                
                # Ensure we treat this as a playlist
                base_opts['extract_flat'] = False
                base_opts['ignoreerrors'] = True  # Continue if some videos fail
                
                # Add debug verbose to see what's happening
                base_opts['verbose'] = False  # Keep false to avoid spam, but we have our own debug
        elif platform == 'YouTube':
            base_opts.update({
                'format': 'best[height<=1080][ext=mp4]/best[ext=mp4]/best',  # YouTube optimal
                # TIDAK DOWNLOAD SUBTITLE - Tidak diperlukan untuk video downloader biasa
                # Jika perlu transkrip, pakai Whisper di AI Auto Clipper
                'retries': 3,              # Add retry mechanism
                'sleep_interval': 1,       # Add delay between requests
            })
        elif platform == 'Facebook':
            base_opts.update({
                'format': 'best[ext=mp4]/best',  # Facebook video format
            })
        elif platform == 'Instagram':
            base_opts.update({
                'format': 'best[ext=mp4]/best',  # Instagram optimal
            })
        elif platform == 'Twitter':
            base_opts.update({
                'format': 'best[ext=mp4]/best',  # Twitter video format
            })
        else:
            # Generic platform
            base_opts.update({
                'format': 'best[ext=mp4]/best[ext=webm]/best',  # Try mp4 first, fallback
            })
        
        return base_opts
        
    def update_status(self, message):
        """Update status label with modern styling"""
        # Add appropriate emoji based on message content
        if "error" in message.lower() or "gagal" in message.lower():
            icon = "❌"
        elif "berhasil" in message.lower() or "selesai" in message.lower():
            icon = "✅"
        elif "mengunduh" in message.lower() or "download" in message.lower():
            icon = "⬇️"
        elif "mencoba" in message.lower():
            icon = "🔄"
        elif "metadata" in message.lower():
            icon = "🛡️"
        elif "mirror" in message.lower():
            icon = "🪞"
        else:
            icon = "💫"
            
        self.status_label.config(text=f"{icon} {message}")
        self.root.update_idletasks()
        
    def start_download(self):
        """Start download in separate thread"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showerror("❌ Error", "Masukkan URL video terlebih dahulu!")
            return
            
        if not self.validate_url(url):
            messagebox.showerror("❌ URL Invalid", "URL video tidak valid!\n\nContoh URL yang didukung:\n• TikTok Video: https://www.tiktok.com/@user/video/123\n• TikTok Profile: https://www.tiktok.com/@username\n• YouTube: https://www.youtube.com/watch?v=abc123\n• Facebook: https://www.facebook.com/watch/?v=123\n• Instagram: https://www.instagram.com/p/abc123")
            return
            
        if not os.path.exists(self.download_path.get()):
            messagebox.showerror("❌ Folder Error", "Folder penyimpanan tidak ditemukan!\nSilakan pilih folder yang valid.")
            return
        
        # Disable button and start progress
        self.download_btn.config(state="disabled")
        self.progress.start(10)
        
        # Start download in thread
        threading.Thread(target=self.download_video, daemon=True).start()
        
    def progress_hook(self, d):
        """Progress hook for yt-dlp with modern styling"""
        if d['status'] == 'downloading':
            # Handle batch download progress
            if self.is_tiktok_profile and self.batch_download.get():
                if 'playlist_index' in d and 'playlist_count' in d:
                    current = d['playlist_index']
                    total = d['playlist_count']
                    
                    # Manual limit check - show warning if approaching limit
                    if self.max_download_limit > 0 and current > self.max_download_limit:
                        self.update_status(f"⚠️ Batas {self.max_download_limit} video terlewat - yt-dlp tidak menghormati limit")
                        # Don't raise error here as it can cause issues
                    
                    filename = d.get('filename', '').split('/')[-1] if 'filename' in d else 'video'
                    limit_text = f"/{self.max_download_limit}" if self.max_download_limit > 0 else f"/{total}"
                    self.update_status(f"Mengunduh video {current}{limit_text}: {filename[:30]}...")
                else:
                    self.update_status("Mengunduh video dari profile...")
            else:
                # Single video download progress
                if 'total_bytes' in d and d['total_bytes'] is not None:
                    percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                    # Convert bytes to MB for display
                    downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                    total_mb = d['total_bytes'] / (1024 * 1024)
                    self.update_status(f"Mengunduh... {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)")
                elif 'downloaded_bytes' in d:
                    downloaded_mb = d['downloaded_bytes'] / (1024 * 1024)
                    self.update_status(f"Mengunduh... {downloaded_mb:.1f} MB")
                else:
                    self.update_status("Mengunduh video...")
        elif d['status'] == 'finished':
            if self.is_tiktok_profile and self.batch_download.get():
                self.downloaded_count += 1
                
                # Check if we've reached our manual limit
                if self.max_download_limit > 0 and self.downloaded_count >= self.max_download_limit:
                    self.update_status(f"✅ Limit tercapai: {self.downloaded_count} video selesai didownload")
                    # We don't raise error here as this video is already finished
                else:
                    self.update_status("Video selesai, melanjutkan ke video berikutnya...")
            else:
                self.update_status("Download selesai, memproses...")
            
    def download_video(self):
        """Download video using yt-dlp"""
        try:
            url = self.url_var.get().strip()
            download_path = self.download_path.get()
            
            self.update_status("Memulai unduhan...")
            
            # Detect platform for optimal settings
            platform = self.detect_platform(url)
            
            if platform == 'TikTok' and self.is_tiktok_profile and self.batch_download.get():
                max_videos = self.max_videos.get().strip()
                if max_videos:
                    self.update_status(f"Terdeteksi: TikTok Profile (maksimal {max_videos} video)")
                else:
                    self.update_status(f"Terdeteksi: TikTok Profile (semua video)")
            else:
                self.update_status(f"Terdeteksi platform: {platform}")
            
            # Platform-specific yt-dlp options
            ydl_opts = self.get_platform_options(download_path, platform)
            
            # Debug logging untuk batch download
            if self.is_tiktok_profile and self.batch_download.get():
                max_videos = self.max_videos.get().strip()
                if max_videos and max_videos.isdigit():
                    # Set manual limit for fallback
                    self.max_download_limit = int(max_videos)
                    self.downloaded_count = 0
                    self.update_status(f"🔧 Debug: Limit diset ke {max_videos} video (playlistend={max_videos}, max_downloads={max_videos})")
                else:
                    self.max_download_limit = 0
                    self.downloaded_count = 0
                self.update_status("Menganalisis profile dan daftar video...")
            else:
                self.max_download_limit = 0
                self.downloaded_count = 0
                self.update_status("Mendapatkan informasi video...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # Extract info first to get filename
                    info = ydl.extract_info(url, download=False)
                    
                    # Debug: Check if it's recognized as playlist
                    if self.is_tiktok_profile and self.batch_download.get():
                        if 'entries' in info:
                            total_entries = len(list(info['entries']))
                            self.update_status(f"🔍 Debug: Playlist terdeteksi dengan {total_entries} video")
                            if self.max_download_limit > 0:
                                actual_limit = min(self.max_download_limit, total_entries)
                                self.update_status(f"🎯 Akan download {actual_limit} dari {total_entries} video")
                        else:
                            self.update_status("⚠️ Debug: URL tidak dikenali sebagai playlist oleh yt-dlp")
                    
                    filename = ydl.prepare_filename(info)
                    
                    # Check if file already exists
                    if os.path.exists(filename):
                        self.update_status("File sudah ada, menimpa...")
                    
                    # Download the video
                    ydl.download([url])
                    
                    # Verify file was downloaded
                    if not os.path.exists(filename):
                        raise Exception("File tidak ditemukan setelah download")
                        
                except yt_dlp.DownloadError as e:
                    # Try with different format if first attempt fails
                    self.update_status("Mencoba format alternatif...")
                    ydl_opts['format'] = 'best/worst'
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(url, download=False)
                        filename = ydl2.prepare_filename(info)
                        ydl2.download([url])
                
            self.update_status("Video berhasil diunduh!")
            
            # Apply anti-copyright features if requested
            if self.is_tiktok_profile and self.batch_download.get():
                # For batch download, process all downloaded videos
                self.apply_batch_anticopyright_features(filename)
            else:
                # For single video download
                if os.path.exists(filename):
                    self.apply_anticopyright_features(filename)
            
            self.root.after(0, self.download_complete, filename)
            
        except yt_dlp.DownloadError as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                error_msg = f"Rate limit exceeded (429 error)!\n\n💡 Solusi:\n• Tunggu 5-10 menit sebelum mencoba lagi\n• Gunakan VPN jika perlu\n• Coba platform lain sementara\n\nDetail: {error_str}"
            elif "403" in error_str or "Forbidden" in error_str:
                error_msg = f"Video tidak bisa diakses (403 error)!\n\n💡 Solusi:\n• Video mungkin private atau dibatasi region\n• Coba dengan VPN\n• Pastikan video masih ada\n\nDetail: {error_str}"
            elif "404" in error_str or "Not Found" in error_str:
                error_msg = f"Video tidak ditemukan (404 error)!\n\n💡 Solusi:\n• Periksa URL sekali lagi\n• Video mungkin sudah dihapus\n• Coba copy URL langsung dari browser\n\nDetail: {error_str}"
            else:
                error_msg = f"Error download: Video mungkin tidak tersedia atau dibatasi.\n\n💡 Tips troubleshooting:\n• Periksa koneksi internet\n• Coba video lain\n• Update yt-dlp: pip install --upgrade yt-dlp\n\nDetail: {error_str}"
            self.root.after(0, self.download_failed, error_msg)
        except Exception as e:
            error_msg = f"Error tidak terduga: {str(e)}\n\n💡 Tips:\n• Restart aplikasi\n• Periksa koneksi internet\n• Coba dengan URL yang lebih sederhana"
            self.root.after(0, self.download_failed, error_msg)
            
    def remove_video_metadata(self, video_path):
        """Remove metadata using ffmpeg"""
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            
            # Create temporary file
            temp_path = video_path + '_temp.mp4'
            
            # FFmpeg command to remove metadata
            cmd = [
                'ffmpeg', '-i', video_path,
                '-map_metadata', '-1',
                '-c', 'copy',
                '-y',  # Overwrite output file
                temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Replace original file with cleaned version
                os.replace(temp_path, video_path)
                self.update_status("Metadata berhasil dihapus!")
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                self.update_status("Gagal menghapus metadata, namun video berhasil diunduh")
                
        except subprocess.CalledProcessError:
            self.update_status("FFmpeg tidak ditemukan, metadata tidak dihapus")
        except Exception as e:
            self.update_status(f"Error menghapus metadata: {str(e)}")
            
    def mirror_video_file(self, video_path):
        """Mirror video horizontally using ffmpeg"""
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            
            # Create temporary file for mirrored video
            path_obj = Path(video_path)
            temp_path = str(path_obj.parent / f"{path_obj.stem}_mirrored{path_obj.suffix}")
            
            # FFmpeg command to mirror video horizontally
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', 'hflip',  # Horizontal flip filter
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-y',  # Overwrite output file
                temp_path
            ]
            
            self.update_status("Melakukan mirror video...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Replace original file with mirrored version
                os.replace(temp_path, video_path)
                self.update_status("Video berhasil di-mirror!")
                return True
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                self.update_status("Gagal mirror video, namun video berhasil diunduh")
                return False
                
        except subprocess.CalledProcessError:
            self.update_status("FFmpeg tidak ditemukan, video tidak di-mirror")
            return False
        except Exception as e:
            self.update_status(f"Error mirror video: {str(e)}")
            return False
    
    def apply_anticopyright_features(self, filename):
        """Apply all selected anti-copyright features"""
        try:
            # Check if FFmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            if any([self.remove_metadata.get(), self.mirror_video.get(), 
                   self.speed_change.get(), self.brightness_change.get(), 
                   self.crop_video.get(), self.add_watermark.get()]):
                self.update_status("FFmpeg tidak ditemukan, fitur anti-copyright dilewati")
            return
        
        # Build FFmpeg filter chain
        filters = []
        needs_processing = False
        
        # 1. Remove metadata (basic operation)
        if self.remove_metadata.get():
            self.update_status("Menghapus metadata...")
            needs_processing = True
        
        # 2. Mirror video
        if self.mirror_video.get():
            filters.append("hflip")
            needs_processing = True
        
        # 3. Speed change (0.95x for anti-detection)
        if self.speed_change.get():
            filters.append("setpts=PTS/0.95")  # Speed up slightly
            needs_processing = True
        
        # 4. Brightness & contrast adjustment
        if self.brightness_change.get():
            filters.append("eq=brightness=0.05:contrast=1.1")  # Subtle changes
            needs_processing = True
        
        # 5. Crop edges (remove 2% from each side)
        if self.crop_video.get():
            filters.append("crop=iw*0.96:ih*0.96:(iw-iw*0.96)/2:(ih-ih*0.96)/2")
            needs_processing = True
        
        # 6. Add subtle watermark
        if self.add_watermark.get():
            # Add semi-transparent text overlay
            watermark_text = "📱"  # Subtle emoji watermark
            filters.append(f"drawtext=text='{watermark_text}':fontsize=20:fontcolor=white@0.3:x=w-tw-10:y=10")
            needs_processing = True
        
        if not needs_processing:
            return
        
        # Apply all filters at once for efficiency
        self.update_status("Mengaplikasikan fitur anti-copyright...")
        self.apply_video_filters(filename, filters)
    
    def apply_batch_anticopyright_features(self, sample_filename):
        """Apply anti-copyright features to all videos in batch download"""
        try:
            # Check if any anti-copyright feature is enabled
            needs_processing = any([
                self.remove_metadata.get(), self.mirror_video.get(), 
                self.speed_change.get(), self.brightness_change.get(), 
                self.crop_video.get(), self.add_watermark.get()
            ])
            
            if not needs_processing:
                return
            
            # Check if FFmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except subprocess.CalledProcessError:
                self.update_status("FFmpeg tidak ditemukan, fitur anti-copyright dilewati")
                return
            
            # Get folder path from sample filename
            folder_path = os.path.dirname(sample_filename)
            
            # Find all video files in the batch download folder
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
            video_files = []
            
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        full_path = os.path.join(folder_path, file)
                        video_files.append(full_path)
            
            if not video_files:
                self.update_status("Tidak ada video ditemukan untuk diproses")
                return
            
            # Process each video with anti-copyright features
            total_videos = len(video_files)
            self.update_status(f"🔄 Memproses {total_videos} video dengan fitur anti-copyright...")
            
            for i, video_path in enumerate(video_files, 1):
                filename = os.path.basename(video_path)
                self.update_status(f"🎨 Memproses video {i}/{total_videos}: {filename[:30]}...")
                self.apply_anticopyright_features(video_path)
            
            self.update_status(f"✅ Selesai memproses {total_videos} video dengan fitur anti-copyright!")
            
        except Exception as e:
            self.update_status(f"Error batch anti-copyright: {str(e)}")
    
    def apply_video_filters(self, video_path, filters):
        """Apply multiple video filters using FFmpeg"""
        try:
            path_obj = Path(video_path)
            temp_path = str(path_obj.parent / f"{path_obj.stem}_processed{path_obj.suffix}")
            
            # Build FFmpeg command
            cmd = ['ffmpeg', '-i', video_path]
            
            # Add video filters if any
            if filters:
                filter_chain = ",".join(filters)
                cmd.extend(['-vf', filter_chain])
            
            # Audio processing for speed change
            if self.speed_change.get():
                cmd.extend(['-af', 'atempo=0.95'])  # Adjust audio tempo
            else:
                cmd.extend(['-c:a', 'copy'])  # Copy audio without re-encoding
            
            # Metadata removal
            if self.remove_metadata.get():
                cmd.extend(['-map_metadata', '-1'])
            
            # Output options
            cmd.extend(['-y', temp_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Replace original file with processed version
                os.replace(temp_path, video_path)
                
                # Count applied features
                feature_count = sum([
                    self.remove_metadata.get(),
                    self.mirror_video.get(),
                    self.speed_change.get(),
                    self.brightness_change.get(),
                    self.crop_video.get(),
                    self.add_watermark.get()
                ])
                
                self.update_status(f"✅ {feature_count} fitur anti-copyright berhasil diterapkan!")
                return True
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                self.update_status("⚠️ Sebagian fitur anti-copyright gagal, video tetap tersimpan")
                return False
                
        except Exception as e:
            self.update_status(f"Error applying filters: {str(e)}")
            return False
            
    def download_complete(self, filename):
        """Handle successful download"""
        self.progress.stop()
        self.download_btn.config(state="normal")
        
        if self.is_tiktok_profile and self.batch_download.get():
            # Handle batch download completion
            folder_path = os.path.dirname(filename)
            
            # Count downloaded files
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
            video_files = []
            
            # Check if folder exists and count videos
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        video_files.append(file)
            
            total_size = sum(os.path.getsize(os.path.join(folder_path, f)) for f in video_files) / (1024 * 1024)
            
            # Check if anti-copyright features were applied
            features_applied = []
            if self.remove_metadata.get(): features_applied.append("📝 Metadata dihapus")
            if self.mirror_video.get(): features_applied.append("🪞 Mirror")
            if self.speed_change.get(): features_applied.append("⚡ Speed 0.95x")
            if self.brightness_change.get(): features_applied.append("🌟 Brightness")
            if self.crop_video.get(): features_applied.append("✂️ Crop")
            if self.add_watermark.get(): features_applied.append("💧 Watermark")
            
            features_text = ""
            if features_applied:
                features_text = f"\n🎨 Fitur diterapkan: {', '.join(features_applied)}"
            
            message = f"🎉 Batch download selesai!\n\n📦 Total video: {len(video_files)}\n📏 Total ukuran: {total_size:.1f} MB\n📂 Lokasi: {folder_path}{features_text}"
            
        else:
            # Handle single video download
            file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
            
            # Check if anti-copyright features were applied
            features_applied = []
            if self.remove_metadata.get(): features_applied.append("📝 Metadata dihapus")
            if self.mirror_video.get(): features_applied.append("🪞 Mirror")
            if self.speed_change.get(): features_applied.append("⚡ Speed 0.95x")
            if self.brightness_change.get(): features_applied.append("🌟 Brightness")
            if self.crop_video.get(): features_applied.append("✂️ Crop")
            if self.add_watermark.get(): features_applied.append("💧 Watermark")
            
            features_text = ""
            if features_applied:
                features_text = f"\n🎨 Fitur diterapkan: {', '.join(features_applied)}"
            
            message = f"🎉 Video berhasil diunduh!\n\n📁 File: {os.path.basename(filename)}\n📏 Ukuran: {file_size:.1f} MB\n📂 Lokasi: {os.path.dirname(filename)}{features_text}"
            folder_path = os.path.dirname(filename)
        
        result = messagebox.askquestion("✅ Download Selesai", 
                                       message + "\n\n🗂️ Buka folder penyimpanan?",
                                       icon="question")
        
        if result == 'yes':
            # Open folder in file explorer
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', folder_path], check=True)
            else:  # Linux and other Unix-like systems
                subprocess.run(['xdg-open', folder_path], check=True)
                
        self.update_status("Siap untuk mengunduh")
        
    def download_failed(self, error_msg):
        """Handle failed download"""
        self.progress.stop()
        self.download_btn.config(state="normal")
        self.update_status("Unduhan gagal")
        
        messagebox.showerror("❌ Download Gagal", f"💥 {error_msg}\n\n🔧 Tips:\n• Cek koneksi internet\n• Pastikan video TikTok bisa diakses\n• Coba dengan URL lain\n• Update yt-dlp: pip install --upgrade yt-dlp")

def main():
    root = tk.Tk()
    
    # Set app icon (optional, create a simple icon)
    try:
        # You can add an icon file here if needed
        # root.iconbitmap('icon.ico')
        pass
    except:
        pass
    
    # Configure window properties for dark theme
    root.configure(bg='#1a1a1a')
    
    # Create application instance
    app = TikTokDownloader(root)
    
    # Center window on screen with modern positioning
    root.update_idletasks()
    width = 780
    height = 650
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2) - 30
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Set minimum and maximum size for optimal display
    root.minsize(750, 600)
    root.maxsize(900, 800)
    
    # Focus on URL entry for better UX
    root.after(100, lambda: app.url_entry.focus())
    
    root.mainloop()

if __name__ == "__main__":
    main() 