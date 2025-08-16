#!/usr/bin/env python3
"""
AI Auto Clipper - Intelligent Video Clipping with Gemini AI
Memotong bagian penting dan emosional dari video YouTube menggunakan AI

FIXES APPLIED:
1. GLOBAL FONT SIZE: All caption styles now use consistent font size instead of individual overrides
2. SUBTITLE TEXT CLEANING: Removes ">>" and other unwanted characters from subtitle text
3. IMPROVED TEXT FORMATTING: Better subtitle text processing and formatting
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
import json
import re
from pathlib import Path
import yt_dlp
import whisper
import google.generativeai as genai
from datetime import timedelta, datetime
import tempfile

class AIAutoClipper:
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
        self.root.title("🤖 AI Auto Clipper - Multi-Platform Video Intelligence")
        self.root.geometry("1000x650")  # Wider for 2-column layout, shorter height
        self.root.resizable(True, True)
        self.root.minsize(950, 600)  # Minimum size for compact layout
        
        # Variables
        self.video_url = tk.StringVar()  # Changed from youtube_url to support multiple platforms
        self.detected_platform = tk.StringVar(value="Unknown")
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads" / "AI_Clips"))
        self.gemini_api_key = tk.StringVar()
        self.clip_duration = tk.StringVar(value="60")  # Default 60 seconds per clip
        self.max_clips = tk.StringVar(value="5")  # Max 5 clips
        self.emotion_focus = tk.StringVar(value="excitement")
        self.model_choice = tk.StringVar(value="auto")  # AI model selection
        
        # NEW FEATURE: Smart Duration Mode
        self.smart_duration = tk.BooleanVar(value=False)  # Enable smart content-based clipping
        self.min_clip_duration = tk.StringVar(value="20")  # Minimum clip duration for smart mode
        self.max_clip_duration = tk.StringVar(value="180")  # Maximum clip duration for smart mode
        
        # Anti-copyright & metadata options
        self.remove_metadata = tk.BooleanVar()
        self.mirror_video = tk.BooleanVar()
        self.speed_change = tk.BooleanVar()
        self.brightness_change = tk.BooleanVar()
        self.crop_video = tk.BooleanVar()
        
        # Enhanced watermark settings
        self.add_watermark = tk.BooleanVar()
        self.watermark_file = tk.StringVar()  # Path to PNG logo file
        self.watermark_position = tk.StringVar(value="top-right")  # Position setting
        self.watermark_size = tk.StringVar(value="medium")  # Size: small, medium, large
        self.watermark_opacity = tk.StringVar(value="0.7")  # Transparency: 0.1-1.0
        
        # Transcript source options (NEW FEATURE)
        self.transcript_mode = tk.StringVar(value="🔄 Auto Fallback (Coba YouTube → Whisper)")  # Default to auto fallback
        
        # NEW FEATURE: Custom Metadata Author (when remove_metadata is enabled)
        self.add_custom_author = tk.BooleanVar(value=False)  # Enable custom author metadata
        self.custom_author_name = tk.StringVar(value="AI Auto Clipper")  # Default author name
        
        # Social media format options
        self.convert_to_portrait = tk.BooleanVar()
        self.aspect_ratio = tk.StringVar(value="9:16")  # Default YouTube Shorts/Reels
        self.aspect_crop_mode = tk.StringVar(value="fit (+ black bars)")  # fit (padding) or crop (cut video)
        
        # Auto caption/subtitle options
        self.auto_caption = tk.BooleanVar()
        self.caption_style = tk.StringVar(value="bottom")  # bottom, top, center
        self.caption_font_size = tk.StringVar(value="24")
        self.caption_language = tk.StringVar(value="auto")  # auto, en, id
        
        # NEW: Caption Style Presets and Preview
        self.caption_style_preset = tk.StringVar(value="classic")  # classic, modern, neon, elegant, bold, minimal
        self.caption_animation = tk.StringVar(value="none")  # none, fade, slide, bounce, typewriter
        self.caption_color = tk.StringVar(value="white")  # white, yellow, cyan, green, orange, pink
        self.caption_outline = tk.StringVar(value="black")  # black, white, none
        self.caption_shadow = tk.BooleanVar(value=True)
        self.caption_background = tk.BooleanVar(value=False)
        self.caption_background_color = tk.StringVar(value="rgba(0,0,0,0.7)")
        self.caption_preview_text = tk.StringVar(value="Sample Caption Text")
        
        # Video quality options - IMPROVED DEFAULTS for better quality
        self.video_quality = tk.StringVar(value="ultra")  # ultra, high, medium, fast  
        self.video_crf = tk.StringVar(value="12")  # Constant Rate Factor (lower = better quality) - IMPROVED from 16 to 12
        self.target_resolution = tk.StringVar(value="1080p")  # 4K, 1080p, 720p, original
        self.social_optimized = tk.BooleanVar(value=True)  # Social media optimization
        
        # Processing variables
        self.video_path = None
        self.audio_path = None
        self.transcript = None
        self.ai_analysis = None
        self.clips_data = []
        self.show_advanced = tk.BooleanVar()  # For collapsible advanced options
        self.output_folder = tk.StringVar(value=str(Path.home() / "Downloads" / "AI_Clips"))
        
        # Colors for modern UI - Consistent with main.py
        self.colors = {
            'bg_primary': '#1a1a1a',       # Main dark background
            'bg_secondary': '#2d2d2d',     # Card backgrounds
            'bg_tertiary': '#3a3a3a',      # Input backgrounds
            'accent_blue': '#0078d4',      # Primary blue accent
            'accent_blue_hover': '#106ebe', # Blue hover state
            'accent_success': '#00bcf2',   # Success blue
            'accent_ai': '#00d4aa',        # AI-specific accent (teal)
            'text_primary': '#ffffff',     # Primary white text
            'text_secondary': '#cccccc',   # Secondary light text
            'text_muted': '#999999',       # Muted gray text
            'border': '#404040',           # Border color
            'error': '#ff6b6b',           # Red error
            'warning': '#ffd700',         # Gold warning
            'shadow': '#000000'           # Shadow color
        }
        
        self.setup_modern_style()
        self.setup_ui()
        
        # Initialize caption preview after UI is set up
        self.root.after(500, self.initialize_caption_preview)
        
        # Load saved settings
        self.load_settings()
        
        # Save settings when application closes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def initialize_caption_preview(self):
        """Initialize caption preview after UI is fully loaded"""
        if self.auto_caption.get():
            self.update_caption_preview_settings()
            self.update_style_description()
            self.update_animation_description()
    
    def on_tab_changed(self, tab_name):
        """Handle tab change events"""
        if tab_name == 'start':  # Start Clipping tab
            self.update_status("📋 Tab: Start Clipping - Siap untuk memulai proses AI clipping dengan pengaturan AI Analysis")
        elif tab_name == 'settings':  # Settings tab
            self.update_status("⚙️ Tab: Settings - Kustomisasi pengaturan output, caption, dan anti-copyright")
            
            # Update caption preview when switching to settings tab
            if self.auto_caption.get():
                self.root.after(100, self.update_caption_preview_settings)
                # Force another update after canvas is fully loaded
                self.root.after(500, self.update_caption_preview_settings)
    
    def setup_modern_style(self):
        """Setup modern dark theme styling"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure modern styles - consistent with main.py
        self.style.configure('AI.TLabel', 
                           background=self.colors['bg_secondary'],
                           foreground=self.colors['text_primary'],
                           font=self.get_system_font(11, 'normal'))
        
        self.style.configure('AITitle.TLabel',
                           background=self.colors['bg_secondary'], 
                           foreground=self.colors['accent_ai'],
                           font=self.get_system_font(14, 'bold'))
        
        self.style.configure('AICard.TFrame',
                           background=self.colors['bg_primary'],   # Match main background
                           relief='flat',
                           borderwidth=0)                          # Remove border
        
        # Configure LabelFrame for seamless modern cards
        self.style.configure('AICard.TLabelframe',
                           background=self.colors['bg_primary'],  # Same as main background
                           foreground=self.colors['accent_ai'],
                           borderwidth=0,                         # Remove border
                           relief='flat')
        
        self.style.configure('AICard.TLabelframe.Label',
                           background=self.colors['bg_primary'],   # Match main background
                           foreground=self.colors['accent_ai'],
                           font=self.get_system_font(11, 'bold'))
        
        self.style.configure('AIButton.TButton',
                           background=self.colors['accent_ai'],
                           foreground=self.colors['bg_primary'],
                           font=self.get_system_font(11, 'bold'),
                           borderwidth=0,
                           focuscolor='none')
        
        # Configure proper checkbox styles
        self.style.configure('AICheckbutton.TCheckbutton',
                           background=self.colors['bg_secondary'],
                           foreground=self.colors['text_primary'],
                           font=self.get_system_font(10, 'normal'),
                           focuscolor='none')
        
        self.style.map('AICheckbutton.TCheckbutton',
                      background=[('active', self.colors['bg_tertiary']),
                                 ('pressed', self.colors['bg_tertiary'])])
        
        self.style.configure('AIEntry.TEntry',
                           fieldbackground=self.colors['bg_tertiary'],
                           foreground=self.colors['text_primary'],
                           borderwidth=1,
                           font=self.get_system_font(10, 'normal'))
        
        # Configure Combobox styling
        self.style.configure('AIEntry.TCombobox',
                           fieldbackground=self.colors['bg_tertiary'],
                           foreground=self.colors['text_primary'],
                           borderwidth=1,
                           font=self.get_system_font(10, 'normal'),
                           arrowcolor=self.colors['text_primary'])
        
        self.style.map('AIEntry.TCombobox',
                      fieldbackground=[('readonly', self.colors['bg_tertiary'])],
                      foreground=[('readonly', self.colors['text_primary'])],
                      arrowcolor=[('readonly', self.colors['text_primary'])])
        
        self.style.configure('AIProgress.Horizontal.TProgressbar',
                           background=self.colors['accent_blue'],
                           troughcolor=self.colors['bg_tertiary'],
                           borderwidth=0)
        
        # Modern Notebook (Tab) styling with enhanced design
        self.style.configure('TNotebook', 
                           background=self.colors['bg_primary'],
                           borderwidth=0,
                           tabmargins=[2, 5, 2, 0])
        
        # Modern tab styling with rounded corners and better spacing
        self.style.configure('TNotebook.Tab',
                           background=self.colors['bg_secondary'],
                           foreground=self.colors['text_secondary'],
                           padding=[20, 12],
                           font=self.get_system_font(11, 'bold'),
                           borderwidth=0,
                           focuscolor='none')
        
        # Enhanced tab hover and selection effects
        self.style.map('TNotebook.Tab',
                      background=[('selected', self.colors['accent_ai']),
                                 ('active', self.colors['bg_tertiary']),
                                 ('!active', self.colors['bg_secondary'])],
                      foreground=[('selected', self.colors['text_primary']),
                                 ('active', self.colors['text_primary']),
                                 ('!active', self.colors['text_secondary'])],
                      relief=[('selected', 'flat'),
                             ('active', 'flat'),
                             ('!active', 'flat')])
        
        # Modern frame styling
        self.style.configure('TFrame',
                           background=self.colors['bg_primary'])
        

        

        
        # Modern button styling for tab-like elements
        self.style.configure('ModernTab.TButton',
                           background=self.colors['bg_secondary'],
                           foreground=self.colors['text_secondary'],
                           padding=[25, 15],
                           font=self.get_system_font(12, 'bold'),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat')
        
        self.style.map('ModernTab.TButton',
                      background=[('pressed', self.colors['accent_ai']),
                                 ('active', self.colors['bg_tertiary'])],
                      foreground=[('pressed', self.colors['text_primary']),
                                 ('active', self.colors['text_primary'])])
        
        # Active tab button styling
        self.style.configure('AITabActive.TButton',
                           background=self.colors['accent_ai'],
                           foreground=self.colors['text_primary'],
                           padding=[25, 15],
                           font=self.get_system_font(12, 'bold'),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat')
        
        self.style.map('AITabActive.TButton',
                      background=[('pressed', self.colors['accent_ai']),
                                 ('active', self.colors['accent_ai'])],
                      foreground=[('pressed', self.colors['text_primary']),
                                 ('active', self.colors['text_primary'])])
        
        # Root background
        self.root.configure(bg=self.colors['bg_primary'])
        
    def setup_ui(self):
        """Setup modern UI with tabbed interface"""
        # Main container
        main_frame = ttk.Frame(self.root, style='AICard.TFrame')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='AICard.TFrame')
        header_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(header_frame, text="🤖 AI Auto Clipper", 
                 style='AITitle.TLabel', font=self.get_system_font(18, 'bold')).pack(pady=(5, 2))
        ttk.Label(header_frame, text="Buat Ngeklip Video Pake AI Bang",
                 style='AI.TLabel', foreground=self.colors['text_secondary']).pack(pady=(0, 5))
        
        # Create Modern Custom Tab Interface
        self.create_modern_tab_interface(main_frame)
        
        # Setup Start Clipping Tab
        self.setup_start_clipping_tab()
        
        # Setup Settings Tab
        self.setup_settings_tab()
        
        # Bottom Status Section (Full Width) - Always visible
        self.setup_status_section(main_frame)
        
        # Add tab navigation hints
        self.add_tab_navigation_hints()
    
    def create_modern_tab_interface(self, parent):
        """Create modern custom tab interface with enhanced styling"""
        # Main container for tabs and content
        self.tab_container = ttk.Frame(parent, style='AICard.TFrame')
        self.tab_container.pack(fill='both', expand=True)
        
        # Modern tab header with enhanced styling
        self.tab_header = tk.Frame(self.tab_container, bg=self.colors['bg_tertiary'])
        self.tab_header.pack(fill='x', pady=(0, 15))
        
        # Add subtle separator line
        separator_frame = tk.Frame(self.tab_header, height=2, bg=self.colors['accent_ai'])
        separator_frame.pack(fill='x', pady=(0, 10))
        
        # Tab buttons container with better spacing
        tab_buttons_frame = tk.Frame(self.tab_header, bg=self.colors['bg_tertiary'])
        tab_buttons_frame.pack(expand=True, pady=(20, 15))
        
        # Create modern tab buttons with better spacing
        self.start_tab_button = ttk.Button(tab_buttons_frame, 
                                          text="🚀 Start Clipping",
                                          style='ModernTab.TButton',
                                          command=lambda: self.switch_tab('start'))
        self.start_tab_button.pack(side='left', padx=(0, 8))
        
        # Add small spacer between buttons
        spacer_frame = ttk.Frame(tab_buttons_frame, width=10)
        spacer_frame.pack(side='left')
        
        self.settings_tab_button = ttk.Button(tab_buttons_frame,
                                             text="⚙️ Settings",
                                             style='ModernTab.TButton',
                                             command=lambda: self.switch_tab('settings'))
        self.settings_tab_button.pack(side='left', padx=(8, 0))
        
        # Content container with modern styling
        self.content_container = ttk.Frame(self.tab_container, style='AICard.TFrame')
        self.content_container.pack(fill='both', expand=True, padx=5)
        
        # Create tab content frames with modern card styling
        self.start_tab = tk.Frame(self.content_container, bg=self.colors['bg_secondary'])
        self.settings_tab = tk.Frame(self.content_container, bg=self.colors['bg_secondary'])
        
        # Initialize with start tab active
        self.current_tab = 'start'
        self.update_tab_buttons()
        self.show_tab('start')
    
    def switch_tab(self, tab_name):
        """Switch between tabs with smooth transition"""
        if tab_name != self.current_tab:
            self.current_tab = tab_name
            self.update_tab_buttons()
            self.show_tab(tab_name)
            self.on_tab_changed(tab_name)
    
    def update_tab_buttons(self):
        """Update tab button styling based on active tab"""
        if self.current_tab == 'start':
            self.start_tab_button.configure(style='AITabActive.TButton')
            self.settings_tab_button.configure(style='ModernTab.TButton')
        else:
            self.start_tab_button.configure(style='ModernTab.TButton')
            self.settings_tab_button.configure(style='AITabActive.TButton')
    
    def show_tab(self, tab_name):
        """Show the selected tab content"""
        # Hide all tabs
        self.start_tab.pack_forget()
        self.settings_tab.pack_forget()
        
        # Show selected tab with modern padding
        if tab_name == 'start':
            self.start_tab.pack(fill='both', expand=True, padx=10, pady=10)
        elif tab_name == 'settings':
            self.settings_tab.pack(fill='both', expand=True, padx=10, pady=10)
    
    def add_tab_navigation_hints(self):
        """Add helpful hints for tab navigation"""
        # Add hint text below tab container
        hint_frame = ttk.Frame(self.tab_container, style='AICard.TFrame')
        hint_frame.pack(fill='x', pady=(5, 0))
        
        hint_text = "💡 Tips: Tab 'Start Clipping' untuk URL, AI Analysis, dan mulai proses. Tab 'Settings' untuk output, caption, dan anti-copyright"
        ttk.Label(hint_frame, text=hint_text,
                 style='AI.TLabel', foreground=self.colors['text_muted'],
                 font=self.get_system_font(9, 'normal')).pack(anchor='center')
    
    def setup_caption_settings_section(self, parent):
        """Setup dedicated caption settings section"""
        # Create modern card
        caption_card = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        caption_card.pack(fill='x', pady=(0, 8), padx=4, ipady=10)
        
        # Header
        header_frame = tk.Frame(caption_card, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(5, 8))
        
        tk.Label(header_frame, text="📝 Caption & Subtitle Settings", 
                font=self.get_system_font(11, 'bold'), 
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_ai']).pack(anchor='w')
        
        # Caption enable checkbox
        caption_enable_frame = tk.Frame(caption_card, bg=self.colors['bg_secondary'])
        caption_enable_frame.pack(fill='x', pady=(0, 10))
        
        caption_check = ttk.Checkbutton(caption_enable_frame, text="🎬 Enable Auto Caption/Subtitle", 
                                       variable=self.auto_caption, command=self.on_caption_toggle,
                                       style='AICheckbutton.TCheckbutton')
        caption_check.pack(anchor='w')
        
        # Caption options frame
        self.caption_options_settings = tk.Frame(caption_card, bg=self.colors['bg_secondary'])
        
        # Style preset row
        style_row = tk.Frame(self.caption_options_settings, bg=self.colors['bg_secondary'])
        style_row.pack(fill='x', pady=(5, 0))
        
        tk.Label(style_row, text="🎨 Style Preset:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=12).pack(side='left')
        
        style_preset_combo = ttk.Combobox(style_row, textvariable=self.caption_style_preset,
                                        values=["classic", "modern", "neon", "elegant", "bold", "minimal", "gradient", "retro", "glow", "thin", "soft"], 
                                        width=12, style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'), state="readonly")
        style_preset_combo.pack(side='left', padx=(5, 10))
        style_preset_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(100, self.on_caption_style_change))
        
        # Animation
        tk.Label(style_row, text="🎬 Animation:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        
        animation_combo = ttk.Combobox(style_row, textvariable=self.caption_animation,
                                     values=["none", "fade", "slide", "bounce", "typewriter", "zoom", "shake"], 
                                     width=10, style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'), state="readonly")
        animation_combo.pack(side='left', padx=(5, 0))
        animation_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(100, self.on_caption_animation_change))
        
        # Position and size row
        pos_row = tk.Frame(self.caption_options_settings, bg=self.colors['bg_secondary'])
        pos_row.pack(fill='x', pady=(5, 0))
        
        tk.Label(pos_row, text="📍 Position:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=12).pack(side='left')
        
        position_combo = ttk.Combobox(pos_row, textvariable=self.caption_style,
                                    values=["bottom", "top", "center"], 
                                    width=8, style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'), state="readonly")
        position_combo.pack(side='left', padx=(5, 10))
        position_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(200, self.update_caption_preview_settings))
        
        tk.Label(pos_row, text="📏 Font Size:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        
        size_combo = ttk.Combobox(pos_row, textvariable=self.caption_font_size,
                                values=["16", "20", "24", "28", "32"], 
                                width=6, style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'), state="readonly")
        size_combo.pack(side='left', padx=(5, 10))
        size_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(100, self.update_caption_preview_settings))
        size_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(300, self.update_caption_preview_settings))
        size_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(600, self.update_caption_preview_settings))
        
        # Outline width control
        tk.Label(pos_row, text="✏️ Outline:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        
        self.caption_outline_width = tk.StringVar(value="1.0")
        outline_combo = ttk.Combobox(pos_row, textvariable=self.caption_outline_width,
                                   values=["0", "0.5", "0.8", "1.0", "1.5", "2.0", "3.0"], 
                                   width=6, style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'), state="readonly")
        outline_combo.pack(side='left', padx=(5, 10))
        outline_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(100, self.update_caption_preview_settings))
        
        # Font size is now global - no override needed
        tk.Label(pos_row, text="🎯 Font Size:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        
        # Show current global font size (read-only)
        font_size_display = tk.Label(pos_row, text=f"Global: {self.caption_font_size.get()}px", 
                                   font=self.get_system_font(9, 'normal'), 
                                   bg=self.colors['bg_secondary'], fg=self.colors['accent_ai'])
        font_size_display.pack(side='left', padx=(5, 10))
        
        tk.Label(pos_row, text="🌐 Language:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        
        language_combo = ttk.Combobox(pos_row, textvariable=self.caption_language,
                                    values=["auto (Auto-detect)", "en (English)", "id (Indonesia)"], 
                                    width=15, style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'), state="readonly")
        language_combo.pack(side='left', padx=(5, 0))
        language_combo.bind('<<ComboboxSelected>>', self.on_caption_language_change)
        
        # Style and animation descriptions
        desc_row = tk.Frame(self.caption_options_settings, bg=self.colors['bg_secondary'])
        desc_row.pack(fill='x', pady=(5, 0))
        
        # Style description
        self.style_description_settings = tk.Label(desc_row, text="Classic: White text with black outline", 
                                                 font=self.get_system_font(8, 'normal'), 
                                                 bg=self.colors['bg_secondary'], fg=self.colors['text_muted'])
        self.style_description_settings.pack(anchor='w')
        
        # Animation description
        self.animation_description_settings = tk.Label(desc_row, text="Animation: No animation", 
                                                     font=self.get_system_font(8, 'normal'), 
                                                     bg=self.colors['bg_secondary'], fg=self.colors['text_muted'])
        self.animation_description_settings.pack(anchor='w')
        
        # Preview section
        preview_frame = tk.Frame(self.caption_options_settings, bg=self.colors['bg_secondary'])
        preview_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(preview_frame, text="👁️ Style Preview:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w', pady=(0, 5))
        
        # Preview canvas
        self.caption_preview_canvas_settings = tk.Canvas(preview_frame, bg=self.colors['bg_primary'], 
                                                       height=80, relief='flat', bd=0)
        self.caption_preview_canvas_settings.pack(fill='x', pady=(0, 5))
        self.caption_preview_canvas_settings.bind('<Configure>', lambda e: self.root.after(200, self.update_caption_preview_settings))
        self.caption_preview_canvas_settings.bind('<Configure>', lambda e: self.root.after(400, self.update_caption_preview_settings))
        self.caption_preview_canvas_settings.bind('<Configure>', lambda e: self.root.after(800, self.update_caption_preview_settings))
        
        # Preview text input
        preview_text_frame = tk.Frame(preview_frame, bg=self.colors['bg_secondary'])
        preview_text_frame.pack(fill='x')
        
        tk.Label(preview_text_frame, text="📝 Preview Text:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        
        preview_text_entry = ttk.Entry(preview_text_frame, textvariable=self.caption_preview_text,
                                     style='AIEntry.TEntry', font=self.get_system_font(9, 'normal'), width=30)
        preview_text_entry.pack(side='left', padx=(5, 0), fill='x', expand=True)
        preview_text_entry.bind('<KeyRelease>', lambda e: self.root.after(100, self.update_caption_preview_settings))
        preview_text_entry.bind('<KeyRelease>', lambda e: self.root.after(300, self.update_caption_preview_settings))
        preview_text_entry.bind('<KeyRelease>', lambda e: self.root.after(600, self.update_caption_preview_settings))
        
        # Caption info
        info_frame = tk.Frame(self.caption_options_settings, bg=self.colors['bg_secondary'])
        info_frame.pack(fill='x', pady=(10, 0))
        
        info_text = "💡 Fitur Caption: 9 Style Preset + 7 Animasi + Preview Real-time + Auto-detect bahasa"
        info_label = tk.Label(info_frame, text=info_text, 
                             font=self.get_system_font(8, 'normal'), 
                             bg=self.colors['bg_secondary'], fg=self.colors['text_muted'])
        info_label.pack(anchor='w')
        
        # Initially hide caption options
        self.caption_options_settings.pack_forget()
    
    def setup_start_clipping_tab(self):
        """Setup the Start Clipping tab with URL input and processing"""
        # Create simple frame for start tab (no scrollable canvas)
        start_content_frame = ttk.Frame(self.start_tab, style='AICard.TFrame')
        start_content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # URL Section
        self.setup_compact_url_section(start_content_frame)
        
        # AI Analysis Section (moved from Settings tab)
        self.setup_compact_ai_settings(start_content_frame)
        
        # Processing Section
        self.setup_compact_processing_section(start_content_frame)
    
    def setup_settings_tab(self):
        """Setup the Settings tab with all configuration options"""
        # Create scrollable frame for settings tab
        settings_canvas = tk.Canvas(self.settings_tab, bg=self.colors['bg_primary'], highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(self.settings_tab, orient="vertical", command=settings_canvas.yview)
        settings_scrollable_frame = ttk.Frame(settings_canvas, style='AICard.TFrame')
        
        settings_scrollable_frame.bind(
            "<Configure>",
            lambda e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        )
        
        settings_canvas_window = settings_canvas.create_window((0, 0), window=settings_scrollable_frame, anchor="nw")
        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        
        # Configure canvas width
        def configure_settings_canvas_width(event):
            settings_canvas.itemconfig(settings_canvas_window, width=settings_canvas.winfo_width())
        settings_canvas.bind("<Configure>", configure_settings_canvas_width)
        
        settings_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        settings_scrollbar.pack(side="right", fill="y")
        
        # Settings Instructions
        settings_instructions_frame = ttk.Frame(settings_scrollable_frame, style='AICard.TFrame')
        settings_instructions_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(settings_instructions_frame, text="⚙️ Advanced Settings:", 
                 style='AITitle.TLabel', font=self.get_system_font(12, 'bold')).pack(anchor='w', pady=(0, 5))
        
        settings_text = """🎯 Kustomisasi pengaturan output format, caption style, dan anti-copyright.
🔑 Gemini API Key diperlukan untuk fungsi AI - atur di bagian API Configuration.
🧠 AI Analysis settings sekarang tersedia di tab 'Start Clipping' untuk kemudahan akses.
💡 Pengaturan ini akan disimpan dan digunakan untuk semua proses clipping."""
        
        ttk.Label(settings_instructions_frame, text=settings_text,
                 style='AI.TLabel', foreground=self.colors['text_secondary'],
                 justify='left').pack(anchor='w', pady=(0, 10))
        
        # API Section (Required for AI functionality)
        self.setup_compact_api_section(settings_scrollable_frame)
        
        # Output Settings Section
        self.setup_compact_output_section(settings_scrollable_frame)
        
        # Caption Settings Section (Separate from anti-copyright)
        self.setup_caption_settings_section(settings_scrollable_frame)
        
        # Anti-Copyright Section
        self.setup_compact_anticopyright_section(settings_scrollable_frame)
        
        # Settings Tips Section
        settings_tips_frame = ttk.Frame(settings_scrollable_frame, style='AICard.TFrame')
        settings_tips_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Label(settings_tips_frame, text="💡 Settings Tips:", 
                 style='AITitle.TLabel', font=self.get_system_font(12, 'bold')).pack(anchor='w', pady=(0, 5))
        
        settings_tips_text = """• 📁 Output Settings: Format, resolusi, dan folder output
• 📝 Caption Style: 9 preset style + 7 animasi + preview real-time
• 🛡️ Anti-Copyright: Kombinasikan 2-3 fitur untuk hasil optimal
• 🧠 AI Analysis: Sekarang tersedia di tab 'Start Clipping'
• 💾 Settings akan disimpan otomatis untuk penggunaan selanjutnya"""
        
        ttk.Label(settings_tips_frame, text=settings_tips_text,
                 style='AI.TLabel', foreground=self.colors['text_secondary'],
                 justify='left').pack(anchor='w')
        
        # Settings Save Button
        save_settings_frame = ttk.Frame(settings_tips_frame, style='AICard.TFrame')
        save_settings_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Button(save_settings_frame, text="💾 Save Settings Now", 
                  command=self.save_settings, style='AIButton.TButton').pack(side='left')
        
        ttk.Label(save_settings_frame, text="💡 Settings akan otomatis disimpan saat aplikasi ditutup",
                 style='AI.TLabel', foreground=self.colors['text_muted'],
                 font=self.get_system_font(9, 'normal')).pack(side='left', padx=(10, 0))
        
    def setup_api_section(self, parent):
        """Setup API key configuration section"""
        api_frame = ttk.LabelFrame(parent, text="🔑 Gemini AI Configuration", style='AICard.TLabelframe')
        api_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=15)
        
        content = ttk.Frame(api_frame, style='AICard.TFrame')
        content.pack(fill='x', padx=15, pady=10)
        
        ttk.Label(content, text="Gemini API Key:", style='AI.TLabel').pack(anchor='w')
        
        api_input_frame = ttk.Frame(content, style='AICard.TFrame')
        api_input_frame.pack(fill='x', pady=(5, 10))
        
        self.api_entry = ttk.Entry(api_input_frame, textvariable=self.gemini_api_key, 
                                  style='AIEntry.TEntry', show="*", width=60)
        self.api_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(api_input_frame, text="💾 Save", 
                  command=self.save_api_key, style='AIButton.TButton').pack(side='right')
        
        ttk.Label(content, text="💡 Dapatkan API key gratis di: https://makersuite.google.com/app/apikey",
                 style='AI.TLabel', foreground=self.colors['text_secondary']).pack(anchor='w')
        
        # Test API button
        ttk.Button(content, text="🧪 Test API Connection", 
                  command=self.test_api_connection, style='AIButton.TButton').pack(anchor='w', pady=(5, 0))
        
        # Model selection frame
        model_frame = ttk.Frame(content)
        model_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(model_frame, text="🤖 AI Model:", style='AI.TLabel').pack(anchor='w')
        
        self.model_choice = tk.StringVar(value="auto")
        model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_choice, 
                                     values=["auto", "💎 gemini-2.5-pro (Premium)", "⭐ gemini-2.5-flash (Premium)", "🚀 gemini-2.0-flash", "🎯 gemini-1.5-pro", "⚡ gemini-1.5-flash"],
                                     state="readonly", style='AIEntry.TCombobox')
        model_dropdown.pack(anchor='w', pady=(2, 0), fill='x')
        
        # Model info label
        self.model_info_label = ttk.Label(model_frame, text="🔄 Auto-detect: Optimal model berdasarkan API tier", 
                                         style='AI.TLabel', foreground=self.colors['text_secondary'])
        self.model_info_label.pack(anchor='w', pady=(2, 0))
        
        # Bind model selection change
        self.model_choice.trace('w', self.on_model_change)
        
        # Load saved API key
        self.load_api_key()
        
    def setup_url_section(self, parent):
        """Setup Multi-Platform Video URL input section"""
        url_frame = ttk.LabelFrame(parent, text="🌐 Multi-Platform Video Input", style='AICard.TLabelframe')
        url_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=15)
        
        content = ttk.Frame(url_frame, style='AICard.TFrame')
        content.pack(fill='x', padx=15, pady=10)
        
        # URL input with platform detection
        url_label_frame = ttk.Frame(content, style='AICard.TFrame')
        url_label_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(url_label_frame, text="Video URL:", style='AI.TLabel').pack(side='left')
        self.platform_label = ttk.Label(url_label_frame, text="", style='AI.TLabel', 
                                       foreground=self.colors['accent_ai'])
        self.platform_label.pack(side='right')
        
        url_input_frame = ttk.Frame(content, style='AICard.TFrame')
        url_input_frame.pack(fill='x', pady=(5, 10))
        
        self.url_entry = ttk.Entry(url_input_frame, textvariable=self.video_url, 
                                  style='AIEntry.TEntry', width=60)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Add URL change detection
        self.video_url.trace('w', self.on_url_change)
        
        ttk.Button(url_input_frame, text="📋 Paste", 
                  command=self.paste_url, style='AIButton.TButton').pack(side='right')
        
        # Supported platforms info
        platforms_text = "✅ Supported: YouTube, TikTok, Instagram, Twitter, Facebook, Bilibili, dan 1000+ platform lainnya"
        ttk.Label(content, text=platforms_text,
                 style='AI.TLabel', foreground=self.colors['text_secondary']).pack(anchor='w', pady=(0, 5))
                 
        # Examples
        examples_text = "Contoh:\n• YouTube: https://www.youtube.com/watch?v=dQw4w9WgXcQ\n• TikTok: https://www.tiktok.com/@username/video/1234567890\n• Instagram: https://www.instagram.com/p/ABC123/"
        ttk.Label(content, text=examples_text,
                 style='AI.TLabel', foreground=self.colors['text_muted']).pack(anchor='w')
        
    def setup_ai_settings(self, parent):
        """Setup AI analysis settings"""
        ai_frame = ttk.LabelFrame(parent, text="🧠 AI Analysis Settings", style='AICard.TLabelframe')
        ai_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=15)
        
        content = ttk.Frame(ai_frame, style='AICard.TFrame')
        content.pack(fill='x', padx=15, pady=10)
        
        # Emotion focus
        emotion_frame = ttk.Frame(content, style='AICard.TFrame')
        emotion_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(emotion_frame, text="🎭 Fokus Emosi:", style='AI.TLabel').pack(side='left')
        
        emotions = ["excitement", "funny", "dramatic", "inspiring", "shocking", "emotional", "sad", "melancholic", "touching"]
        emotion_combo = ttk.Combobox(emotion_frame, textvariable=self.emotion_focus, 
                                   values=emotions, style='AIEntry.TEntry', state="readonly")
        emotion_combo.pack(side='left', padx=(10, 0))
        
        # Emotion descriptions
        emotion_desc_frame = ttk.Frame(content, style='AICard.TFrame')
        emotion_desc_frame.pack(fill='x', pady=(5, 0))
        
        emotion_descriptions = {
            "excitement": "🎯 Semangat & Energi Tinggi",
            "funny": "😄 Humor & Lucu",
            "dramatic": "🎭 Ketegangan & Konflik",
            "inspiring": "💪 Motivasi & Inspirasi",
            "shocking": "😱 Kejutan & Tidak Terduga",
            "emotional": "💝 Menyentuh Hati",
            "sad": "😢 Kesedihan & Melankolis",
            "melancholic": "🌙 Nostalgia & Perasaan Dalam",
            "touching": "💕 Mengharukan & Emosional"
        }
        
        # Create emotion description label
        self.emotion_desc_label = ttk.Label(emotion_desc_frame, text="🎯 Semangat & Energi Tinggi", style='AI.TLabel', foreground='gray')
        self.emotion_desc_label.pack(anchor='w')
        
        # Add detailed emotion info
        emotion_info_frame = ttk.Frame(content, style='AICard.TFrame')
        emotion_info_frame.pack(fill='x', pady=(5, 0))
        
        info_text = "💡 Tips: Pilih 'sad', 'melancholic', atau 'touching' untuk momen sedih dan mengharukan"
        ttk.Label(emotion_info_frame, text=info_text, style='AI.TLabel', foreground='blue').pack(anchor='w')
        
        # Additional info for sad emotions
        sad_info_frame = ttk.Frame(content, style='AICard.TFrame')
        sad_info_frame.pack(fill='x', pady=(3, 0))
        
        sad_info_text = "🎭 Emosi Sedih: Ideal untuk konten yang mengharukan, nostalgia, atau kata-kata yang menyentuh hati"
        ttk.Label(sad_info_frame, text=sad_info_text, style='AI.TLabel', foreground='purple').pack(anchor='w')
        
        # Bind emotion change event
        emotion_combo.bind('<<ComboboxSelected>>', self.on_emotion_change)
        
        # Clip settings
        settings_frame = ttk.Frame(content, style='AICard.TFrame')
        settings_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(settings_frame, text="⏱️ Durasi Clip (detik):", style='AI.TLabel').pack(side='left')
        ttk.Entry(settings_frame, textvariable=self.clip_duration, 
                 style='AIEntry.TEntry', width=10).pack(side='left', padx=(10, 20))
        
        ttk.Label(settings_frame, text="🔢 Max Clips:", style='AI.TLabel').pack(side='left')
        ttk.Entry(settings_frame, textvariable=self.max_clips, 
                 style='AIEntry.TEntry', width=10).pack(side='left', padx=(10, 0))
        
    def setup_anticopyright_section(self, parent):
        """Setup anti-copyright and metadata removal options"""
        anticopy_frame = ttk.LabelFrame(parent, text="🛡️ Anti-Copyright & Metadata", style='AICard.TLabelframe')
        anticopy_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=15)
        
        content = ttk.Frame(anticopy_frame, style='AICard.TFrame')
        content.pack(fill='x', padx=15, pady=10)
        
        ttk.Label(content, text="🎨 Transform clips untuk avoid copyright detection:",
                 style='AI.TLabel').pack(anchor='w', pady=(0, 10))
        
        # Basic options
        basic_frame = ttk.Frame(content, style='AICard.TFrame')
        basic_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Checkbutton(basic_frame, text="📝 Remove metadata dari semua clips", 
                       variable=self.remove_metadata, style='AICheckbutton.TCheckbutton').pack(anchor='w', pady=2)
        
        # Anti-copyright features
        features_frame = ttk.Frame(content, style='AICard.TFrame')
        features_frame.pack(fill='x')
        
        # Left column
        left_col = ttk.Frame(features_frame, style='AICard.TFrame')
        left_col.pack(side='left', fill='x', expand=True)
        
        ttk.Checkbutton(left_col, text="🪞 Mirror horizontal", 
                       variable=self.mirror_video, style='AICheckbutton.TCheckbutton').pack(anchor='w', pady=2)
        ttk.Checkbutton(left_col, text="⚡ Speed change (0.95x)", 
                       variable=self.speed_change, style='AICheckbutton.TCheckbutton').pack(anchor='w', pady=2)
        ttk.Checkbutton(left_col, text="🌟 Brightness & contrast", 
                       variable=self.brightness_change, style='AICheckbutton.TCheckbutton').pack(anchor='w', pady=2)
        
        # Right column  
        right_col = ttk.Frame(features_frame, style='AICard.TFrame')
        right_col.pack(side='left', fill='x', expand=True, padx=(20, 0))
        
        ttk.Checkbutton(right_col, text="✂️ Auto crop edges (2%)", 
                       variable=self.crop_video, style='AICheckbutton.TCheckbutton').pack(anchor='w', pady=2)
        ttk.Checkbutton(right_col, text="💧 Subtle watermark", 
                       variable=self.add_watermark, style='AICheckbutton.TCheckbutton').pack(anchor='w', pady=2)
        
        # Social media format section
        social_frame = ttk.Frame(content, style='AICard.TFrame')
        social_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Label(social_frame, text="📱 Social Media Format:",
                 style='AI.TLabel').pack(anchor='w', pady=(0, 8))
        
        # Portrait conversion checkbox
        portrait_frame = ttk.Frame(social_frame, style='AICard.TFrame')
        portrait_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Checkbutton(portrait_frame, text="📐 Convert to portrait format", 
                       variable=self.convert_to_portrait, style='AICheckbutton.TCheckbutton',
                       command=self.on_portrait_toggle).pack(side='left')
        
        # Aspect ratio selection
        ratio_frame = ttk.Frame(social_frame, style='AICard.TFrame')
        ratio_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(ratio_frame, text="📏 Aspect Ratio:", style='AI.TLabel').pack(side='left')
        
        ratios = ["9:16 (YT Shorts/Reels)", "4:5 (Instagram)", "1:1 (Square)", "16:9 (Landscape)"]
        self.ratio_combo = ttk.Combobox(ratio_frame, textvariable=self.aspect_ratio, 
                                       values=ratios, style='AIEntry.TEntry', 
                                       state="readonly", width=20)
        self.ratio_combo.pack(side='left', padx=(10, 0))
        
        # Initially disable ratio selection
        self.ratio_combo.configure(state="disabled")
        
        # Crop mode selection
        crop_mode_frame = ttk.Frame(social_frame, style='AICard.TFrame')
        crop_mode_frame.pack(fill='x', pady=(8, 0))
        
        ttk.Label(crop_mode_frame, text="✂️ Conversion Mode:", style='AI.TLabel').pack(side='left')
        
        crop_modes = ["fit (+ black bars)", "crop (potong video)"]
        self.crop_mode_combo = ttk.Combobox(crop_mode_frame, textvariable=self.aspect_crop_mode, 
                                           values=crop_modes, style='AIEntry.TEntry', 
                                           state="readonly", width=18)
        self.crop_mode_combo.pack(side='left', padx=(10, 0))
        
        # Initially disable crop mode selection
        self.crop_mode_combo.configure(state="disabled")
        
        # Auto Caption/Subtitle section
        caption_frame = ttk.Frame(content, style='AICard.TFrame')
        caption_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Label(caption_frame, text="📝 Auto Caption/Subtitle:",
                 style='AI.TLabel').pack(anchor='w', pady=(0, 8))
        
        # Caption checkbox
        ttk.Checkbutton(caption_frame, text="🎬 Enable auto caption/subtitle", 
                       variable=self.auto_caption, command=self.on_caption_toggle,
                       style='AICheckbutton.TCheckbutton').pack(anchor='w')
        
        # Caption options frame
        self.caption_options_main = ttk.Frame(caption_frame, style='AICard.TFrame')
        
        # Style preset row
        style_row = ttk.Frame(self.caption_options_main, style='AICard.TFrame')
        style_row.pack(fill='x', pady=(5, 0))
        
        ttk.Label(style_row, text="🎨 Style Preset:", style='AI.TLabel').pack(side='left')
        style_preset_combo = ttk.Combobox(style_row, textvariable=self.caption_style_preset,
                                        values=["classic", "modern", "neon", "elegant", "bold", "minimal", "gradient", "retro", "glow"], 
                                        width=12, style='AIEntry.TEntry', state="readonly")
        style_preset_combo.pack(side='left', padx=(10, 20))
        style_preset_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(100, self.on_caption_style_change))
        
        # Style description for main UI
        style_desc_main = ttk.Label(style_row, text="Classic: White text with black outline", 
                                  style='AI.TLabel', foreground=self.colors['text_muted'])
        style_desc_main.pack(side='left', padx=(10, 0))
        self.style_description_main = style_desc_main
        
        ttk.Label(style_row, text="🎬 Animation:", style='AI.TLabel').pack(side='left')
        animation_combo = ttk.Combobox(style_row, textvariable=self.caption_animation,
                                     values=["none", "fade", "slide", "bounce", "typewriter", "zoom", "shake"], 
                                     width=10, style='AIEntry.TEntry', state="readonly")
        animation_combo.pack(side='left', padx=(10, 0))
        animation_combo.bind('<<ComboboxSelected>>', self.on_caption_animation_change)
        
        # Animation description for main UI
        anim_desc_main = ttk.Label(style_row, text="Animation: No animation", 
                                 style='AI.TLabel', foreground=self.colors['text_muted'])
        anim_desc_main.pack(side='left', padx=(10, 0))
        self.animation_description_main = anim_desc_main
        
        # Position and size row
        pos_row = ttk.Frame(self.caption_options_main, style='AICard.TFrame')
        pos_row.pack(fill='x', pady=(5, 0))
        
        ttk.Label(pos_row, text="📍 Position:", style='AI.TLabel').pack(side='left')
        position_combo = ttk.Combobox(pos_row, textvariable=self.caption_style,
                                    values=["bottom", "top", "center"], 
                                    width=8, style='AIEntry.TEntry', state="readonly")
        position_combo.pack(side='left', padx=(10, 20))
        
        ttk.Label(pos_row, text="📏 Font Size:", style='AI.TLabel').pack(side='left')
        size_combo = ttk.Combobox(pos_row, textvariable=self.caption_font_size,
                                values=["16", "20", "24", "28", "32"], 
                                width=6, style='AIEntry.TEntry', state="readonly")
        size_combo.pack(side='left', padx=(10, 20))
        size_combo.bind('<<ComboboxSelected>>', lambda e: self.root.after(100, self.update_caption_preview_main))
        
        ttk.Label(pos_row, text="🌐 Language:", style='AI.TLabel').pack(side='left')
        language_combo = ttk.Combobox(pos_row, textvariable=self.caption_language,
                                    values=["auto (Auto-detect)", "en (English)", "id (Indonesia)"], 
                                    width=15, style='AIEntry.TEntry', state="readonly")
        language_combo.pack(side='left', padx=(10, 0))
        language_combo.bind('<<ComboboxSelected>>', self.on_caption_language_change)
        
        # Preview section
        preview_frame = ttk.Frame(self.caption_options_main, style='AICard.TFrame')
        preview_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(preview_frame, text="👁️ Style Preview:", style='AI.TLabel').pack(anchor='w', pady=(0, 5))
        
        # Preview canvas
        self.caption_preview_canvas_main = tk.Canvas(preview_frame, bg=self.colors['bg_primary'], 
                                                   height=80, relief='flat', bd=0)
        self.caption_preview_canvas_main.pack(fill='x', pady=(0, 5))
        self.caption_preview_canvas_main.bind('<Configure>', lambda e: self.root.after(100, self.update_caption_preview_main))
        
        # Preview text input
        preview_text_frame = ttk.Frame(preview_frame, style='AICard.TFrame')
        preview_text_frame.pack(fill='x')
        
        ttk.Label(preview_text_frame, text="📝 Preview Text:", style='AI.TLabel').pack(side='left')
        preview_text_entry = ttk.Entry(preview_text_frame, textvariable=self.caption_preview_text,
                                     style='AIEntry.TEntry', width=30)
        preview_text_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        preview_text_entry.bind('<KeyRelease>', lambda e: self.root.after(100, self.update_caption_preview_main))
        
        # Initially hide caption options
        self.caption_options_main.pack_forget()
        
        # Caption info for main UI
        caption_info_main = ttk.Frame(caption_frame, style='AICard.TFrame')
        caption_info_main.pack(fill='x', pady=(5, 0))
        
        info_text_main = "💡 Fitur Caption Baru: 9 Style Preset + 7 Animasi + Preview Real-time + Auto-detect bahasa"
        info_label_main = ttk.Label(caption_info_main, text=info_text_main, 
                                  style='AI.TLabel', foreground=self.colors['text_muted'])
        info_label_main.pack(anchor='w')
        
        # Tips
        ttk.Label(content, text="💡 Tips: Kombinasikan 2-3 fitur untuk hasil anti-copyright optimal",
                 style='AI.TLabel', foreground=self.colors['text_secondary']).pack(anchor='w', pady=(10, 0))
        ttk.Label(content, text="📝 Fit = tambah black bars, Crop = potong bagian video",
                 style='AI.TLabel', foreground=self.colors['text_secondary']).pack(anchor='w', pady=(3, 0))
        
    def setup_output_section(self, parent):
        """Setup output directory selection"""
        output_frame = ttk.LabelFrame(parent, text="📁 Output Settings", style='AICard.TLabelframe')
        output_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=15)
        
        content = ttk.Frame(output_frame, style='AICard.TFrame')
        content.pack(fill='x', padx=15, pady=10)
        
        ttk.Label(content, text="Output Folder:", style='AI.TLabel').pack(anchor='w')
        
        path_frame = ttk.Frame(content, style='AICard.TFrame')
        path_frame.pack(fill='x', pady=(5, 0))
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.download_path, 
                                   style='AIEntry.TEntry', state="readonly")
        self.path_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        ttk.Button(path_frame, text="🗂️ Browse", 
                  command=self.browse_folder, style='AIButton.TButton').pack(side='right')
        
    def setup_processing_section(self, parent):
        """Setup processing controls"""
        process_frame = ttk.LabelFrame(parent, text="🚀 AI Processing", style='AICard.TLabelframe')
        process_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=15)
        
        content = ttk.Frame(process_frame, style='AICard.TFrame')
        content.pack(fill='x', padx=15, pady=10)
        
        # Start button
        self.start_btn = ttk.Button(content, text="🤖 Start AI Auto Clipping", 
                                   command=self.start_ai_clipping, style='AIButton.TButton')
        self.start_btn.pack(pady=10)
        
        # Steps info
        steps_text = """
🔄 Proses AI Auto Clipping:
1. 📥 Download video YouTube
2. 🎵 Extract audio dan transcript
3. 🧠 Analisis AI dengan Gemini
4. ✂️ Generate clips berdasarkan emosi
5. 🛡️ Apply anti-copyright features
6. 🎬 Export clips final
        """
        ttk.Label(content, text=steps_text.strip(), style='AI.TLabel',
                 foreground=self.colors['text_secondary']).pack(pady=(10, 0))
        
    def setup_status_section(self, parent):
        """Setup status and progress indicators"""
        status_frame = ttk.LabelFrame(parent, text="📊 Status & Progress", style='AICard.TLabelframe')
        status_frame.pack(fill='x', pady=(0, 15), padx=10, ipady=15)
        
        content = ttk.Frame(status_frame, style='AICard.TFrame')
        content.pack(fill='x', padx=15, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(content, style='AIProgress.Horizontal.TProgressbar', 
                                       mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(content, text="Siap untuk memulai AI clipping", 
                                     style='AI.TLabel')
        self.status_label.pack(anchor='w')
        
        # Results area (will be populated after processing)
        self.results_frame = ttk.Frame(content, style='AICard.TFrame')
        self.results_frame.pack(fill='x', pady=(15, 0))
        
    def setup_compact_api_section(self, parent):
        """Compact API configuration section"""
        # Create modern card with subtle background
        api_card = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        api_card.pack(fill='x', pady=(0, 8), padx=4, ipady=10)
        
        # Header with icon
        header_frame = tk.Frame(api_card, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(5, 8))
        
        tk.Label(header_frame, text="🔑 API & Model", 
                font=self.get_system_font(11, 'bold'), 
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_ai']).pack(anchor='w')
        
        # API Key row
        key_row = tk.Frame(api_card, bg=self.colors['bg_secondary'])
        key_row.pack(fill='x', pady=(0, 8))
        
        tk.Label(key_row, text="API Key:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w')
        key_entry_frame = tk.Frame(key_row, bg=self.colors['bg_secondary'])
        key_entry_frame.pack(fill='x', pady=(2, 0))
        
        self.api_key_entry = ttk.Entry(key_entry_frame, textvariable=self.gemini_api_key, 
                                      show="*", style='AIEntry.TEntry', font=self.get_system_font(9, 'normal'))
        self.api_key_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(key_entry_frame, text="💾", command=self.save_api_key, 
                  style='AIButton.TButton', width=3).pack(side='right', padx=(5, 0))
        
        # Buttons row
        btn_row = tk.Frame(api_card, bg=self.colors['bg_secondary'])
        btn_row.pack(fill='x', pady=(0, 5))
        
        ttk.Button(btn_row, text="🧪 Test", command=self.test_api_connection, 
                  style='AIButton.TButton', width=8).pack(side='left')
        
        tk.Label(btn_row, text="💡 makersuite.google.com", 
                font=self.get_system_font(8, 'normal'), bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary']).pack(side='right', anchor='e')
        
        # Model selection - compact
        model_row = tk.Frame(api_card, bg=self.colors['bg_secondary'])
        model_row.pack(fill='x', pady=(5, 0))
        
        tk.Label(model_row, text="🤖 Model:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w')
        
        # Model choice already defined in __init__, no need to redefine
        model_dropdown = ttk.Combobox(model_row, textvariable=self.model_choice, 
                                     values=["auto", "💎 gemini-2.5-pro (Premium)", "⭐ gemini-2.5-flash (Premium)", 
                                            "🚀 gemini-2.0-flash", "🎯 gemini-1.5-pro", "⚡ gemini-1.5-flash"],
                                     state="readonly", style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'))
        model_dropdown.pack(fill='x', pady=(2, 0))
        
        # Model info
        self.model_info_label = tk.Label(model_row, text="🔄 Auto-detect optimal", 
                                        font=self.get_system_font(8, 'normal'), bg=self.colors['bg_secondary'], 
                                        fg=self.colors['text_secondary'])
        self.model_info_label.pack(anchor='w', pady=(2, 0))
        
        # Bind model selection change
        self.model_choice.trace('w', self.on_model_change)
        
        # Load saved API key
        self.load_api_key()
        
    def setup_compact_url_section(self, parent):
        """Compact Multi-Platform URL input section"""
        # Create modern card
        url_card = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        url_card.pack(fill='x', pady=(8, 0), padx=4, ipady=10)
        
        # Header with platform detection
        header_frame = tk.Frame(url_card, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(5, 8))
        
        tk.Label(header_frame, text="🌐 Video URL", 
                font=self.get_system_font(11, 'bold'), 
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_ai']).pack(side='left')
        
        self.compact_platform_label = tk.Label(header_frame, text="", 
                                              font=self.get_system_font(9, 'bold'), 
                                              bg=self.colors['bg_secondary'],
                                              fg=self.colors['accent_success'])
        self.compact_platform_label.pack(side='right')
        
        # URL input
        url_row = tk.Frame(url_card, bg=self.colors['bg_secondary'])
        url_row.pack(fill='x', pady=(0, 5))
        
        url_entry = ttk.Entry(url_row, textvariable=self.video_url, 
                             style='AIEntry.TEntry', font=self.get_system_font(9, 'normal'))
        url_entry.pack(side='left', fill='x', expand=True)
        
        # Add URL change detection
        self.video_url.trace('w', self.on_url_change)
        
        ttk.Button(url_row, text="📋", command=self.paste_url, 
                  style='AIButton.TButton', width=3).pack(side='right', padx=(5, 0))
        
        # Supported platforms info (smaller text)
        tk.Label(url_card, text="✅ YouTube, TikTok, Instagram, Twitter, Facebook + 1000+ platforms",
                font=self.get_system_font(8, 'normal'), bg=self.colors['bg_secondary'], 
                fg=self.colors['text_secondary']).pack(anchor='w', pady=(2, 0))
        
    def setup_compact_ai_settings(self, parent):
        """Compact AI analysis settings"""
        # Create modern card
        ai_card = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        ai_card.pack(fill='x', pady=(0, 8), padx=4, ipady=10)
        
        # Header
        header_frame = tk.Frame(ai_card, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(5, 8))
        
        tk.Label(header_frame, text="🧠 AI Analysis", 
                font=self.get_system_font(11, 'bold'), 
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_ai']).pack(anchor='w')
        
        # Settings in grid layout for compact design
        settings_grid = tk.Frame(ai_card, bg=self.colors['bg_secondary'])
        settings_grid.pack(fill='x', pady=(0, 5))
        
        # Row 1: Emotion Focus
        emotion_row = tk.Frame(settings_grid, bg=self.colors['bg_secondary'])
        emotion_row.pack(fill='x', pady=(0, 5))
        
        tk.Label(emotion_row, text="🎭 Fokus:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=10).pack(side='left')
        self.emotion_focus = tk.StringVar(value="excitement")
        emotion_combo = ttk.Combobox(emotion_row, textvariable=self.emotion_focus,
                                   values=["excitement", "funny", "dramatic", "inspiring", "shocking", "emotional", "sad", "melancholic", "touching"],
                                   state="readonly", style='AIEntry.TCombobox', width=12, font=self.get_system_font(9, 'normal'))
        emotion_combo.pack(side='left', fill='x', expand=True)
        
        # Emotion description for compact mode
        emotion_desc_row = tk.Frame(settings_grid, bg=self.colors['bg_secondary'])
        emotion_desc_row.pack(fill='x', pady=(2, 0))
        
        self.compact_emotion_desc = tk.Label(emotion_desc_row, text="🎯 Semangat & Energi Tinggi", 
                                            font=self.get_system_font(8, 'normal'), 
                                            bg=self.colors['bg_secondary'], 
                                            fg=self.colors['text_secondary'])
        self.compact_emotion_desc.pack(anchor='w', padx=(10, 0))
        
        # Emotion tips for compact mode
        emotion_tips_row = tk.Frame(settings_grid, bg=self.colors['bg_secondary'])
        emotion_tips_row.pack(fill='x', pady=(1, 0))
        
        tips_text = "💡 Tips: Pilih 'sad', 'melancholic', atau 'touching' untuk momen sedih"
        compact_tips = tk.Label(emotion_tips_row, text=tips_text, 
                               font=self.get_system_font(7, 'normal'), 
                               bg=self.colors['bg_secondary'], 
                               fg=self.colors['accent_ai'])
        compact_tips.pack(anchor='w', padx=(10, 0))
        
        # Additional sad emotion info for compact mode
        sad_tips_row = tk.Frame(settings_grid, bg=self.colors['bg_secondary'])
        sad_tips_row.pack(fill='x', pady=(1, 0))
        
        sad_tips_text = "🎭 Emosi Sedih: Ideal untuk konten mengharukan & nostalgia"
        sad_tips = tk.Label(sad_tips_row, text=sad_tips_text, 
                           font=self.get_system_font(7, 'normal'), 
                           bg=self.colors['bg_secondary'], 
                           fg=self.colors['text_secondary'])
        sad_tips.pack(anchor='w', padx=(10, 0))
        
        # Bind emotion change event for compact mode
        emotion_combo.bind('<<ComboboxSelected>>', self.on_compact_emotion_change)
        
        # Row 2: Smart Duration Mode (NEW FEATURE)
        smart_row = tk.Frame(settings_grid, bg=self.colors['bg_secondary'])
        smart_row.pack(fill='x', pady=(5, 0))
        
        self.smart_duration = tk.BooleanVar(value=False)
        smart_check = ttk.Checkbutton(smart_row, text="🧠 Smart Duration (potong berdasarkan inti topik)", 
                                     variable=self.smart_duration, command=self.on_smart_duration_toggle,
                                     style='AICheckbutton.TCheckbutton')
        smart_check.pack(anchor='w')
        
        # Row 3: Duration Settings (Dynamic based on Smart Mode)
        self.duration_settings = tk.Frame(settings_grid, bg=self.colors['bg_secondary'])
        self.duration_settings.pack(fill='x', pady=(5, 0))
        
        # Fixed Duration Settings (shown when Smart Duration is OFF)
        self.fixed_duration_frame = tk.Frame(self.duration_settings, bg=self.colors['bg_secondary'])
        self.fixed_duration_frame.pack(fill='x')
        
        tk.Label(self.fixed_duration_frame, text="⏱️ Durasi:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=10).pack(side='left')
        self.clip_duration = tk.StringVar(value="60")
        duration_entry = ttk.Entry(self.fixed_duration_frame, textvariable=self.clip_duration, 
                                  style='AIEntry.TEntry', width=6, font=self.get_system_font(9, 'normal'))
        duration_entry.pack(side='left', padx=(0, 10))
        
        tk.Label(self.fixed_duration_frame, text="🔢 Max:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        self.max_clips = tk.StringVar(value="5")
        max_entry = ttk.Entry(self.fixed_duration_frame, textvariable=self.max_clips, 
                             style='AIEntry.TEntry', width=4, font=self.get_system_font(9, 'normal'))
        max_entry.pack(side='left', padx=(5, 0))
        
        # Smart Duration Settings (shown when Smart Duration is ON)
        self.smart_duration_frame = tk.Frame(self.duration_settings, bg=self.colors['bg_secondary'])
        
        smart_params = tk.Frame(self.smart_duration_frame, bg=self.colors['bg_secondary'])
        smart_params.pack(fill='x')
        
        tk.Label(smart_params, text="⏱️ Min:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=10).pack(side='left')
        self.min_clip_duration = tk.StringVar(value="20")
        min_entry = ttk.Entry(smart_params, textvariable=self.min_clip_duration, 
                             style='AIEntry.TEntry', width=4, font=self.get_system_font(9, 'normal'))
        min_entry.pack(side='left', padx=(0, 5))
        
        tk.Label(smart_params, text="Max:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        self.max_clip_duration = tk.StringVar(value="180")
        max_duration_entry = ttk.Entry(smart_params, textvariable=self.max_clip_duration, 
                                      style='AIEntry.TEntry', width=4, font=self.get_system_font(9, 'normal'))
        max_duration_entry.pack(side='left', padx=(5, 10))
        
        tk.Label(smart_params, text="🔢 Max Clips:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side='left')
        max_clips_smart = ttk.Entry(smart_params, textvariable=self.max_clips, 
                                   style='AIEntry.TEntry', width=4, font=self.get_system_font(9, 'normal'))
        max_clips_smart.pack(side='left', padx=(5, 0))
        
        # Initially hide smart duration settings
        self.smart_duration_frame.pack_forget()
        
        # Row 3: Transcript Mode (NEW FEATURE)
        transcript_row = tk.Frame(settings_grid, bg=self.colors['bg_secondary'])
        transcript_row.pack(fill='x', pady=(8, 0))
        
        tk.Label(transcript_row, text="📝 Transkrip:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=10).pack(side='left')
        
        transcript_combo = ttk.Combobox(transcript_row, textvariable=self.transcript_mode,
                                       values=["🔄 Auto Fallback (Coba YouTube → Whisper)", 
                                              "📜 YouTube Subtitle (Cepat)", 
                                              "🤖 Whisper AI (Akurat)"],
                                       state="readonly", style='AIEntry.TCombobox', 
                                       width=28, font=self.get_system_font(8, 'normal'))
        transcript_combo.pack(side='left', fill='x', expand=True)
        
        # Bind transcript mode change to show info
        self.transcript_mode.trace('w', self.on_transcript_mode_change)
        
    def setup_compact_anticopyright_section(self, parent):
        """Compact anti-copyright settings with tabs"""
        # Create modern card
        anti_card = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        anti_card.pack(fill='x', pady=(8, 0), padx=4, ipady=10)
        
        # Header
        header_frame = tk.Frame(anti_card, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(5, 8))
        
        tk.Label(header_frame, text="🛡️ Anti-Copyright & Format", 
                font=self.get_system_font(11, 'bold'), 
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_ai']).pack(anchor='w')
        
        # Metadata removal (prominent)
        meta_frame = tk.Frame(anti_card, bg=self.colors['bg_secondary'])
        meta_frame.pack(fill='x', pady=(0, 8))
        
        self.remove_metadata = tk.BooleanVar(value=True)
        meta_check = ttk.Checkbutton(meta_frame, text="📝 Remove metadata", variable=self.remove_metadata,
                                    command=self.on_metadata_toggle, style='AICheckbutton.TCheckbutton')
        meta_check.pack(anchor='w')
        
        # Custom Author Metadata Options (shown when remove_metadata is enabled)
        self.custom_author_frame = tk.Frame(meta_frame, bg=self.colors['bg_secondary'])
        
        # Custom author checkbox
        author_check_frame = tk.Frame(self.custom_author_frame, bg=self.colors['bg_secondary'])
        author_check_frame.pack(fill='x', pady=(5, 2))
        
        self.add_custom_author = tk.BooleanVar(value=False)
        author_check = ttk.Checkbutton(author_check_frame, text="👤 Add custom author metadata", 
                                      variable=self.add_custom_author, command=self.on_custom_author_toggle,
                                      style='AICheckbutton.TCheckbutton')
        author_check.pack(anchor='w')
        
        # Author name input (shown when add_custom_author is enabled)
        self.author_input_frame = tk.Frame(self.custom_author_frame, bg=self.colors['bg_secondary'])
        
        author_label_frame = tk.Frame(self.author_input_frame, bg=self.colors['bg_secondary'])
        author_label_frame.pack(fill='x', pady=(2, 0))
        
        tk.Label(author_label_frame, text="Author:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        self.custom_author_name = tk.StringVar(value="AI Auto Clipper")
        author_entry = ttk.Entry(author_label_frame, textvariable=self.custom_author_name, 
                                style='AIEntry.TEntry', width=25, font=self.get_system_font(9, 'normal'))
        author_entry.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        # Initially hide both custom author frames
        self.custom_author_frame.pack_forget()
        self.author_input_frame.pack_forget()
        
        # Call toggle to show custom author options if remove_metadata is enabled by default
        self.on_metadata_toggle()
        
        # Advanced features in collapsible section
        advanced_frame = tk.Frame(anti_card, bg=self.colors['bg_secondary'])
        advanced_frame.pack(fill='x')
        
        # Show/Hide advanced button
        self.show_advanced = tk.BooleanVar()
        advanced_btn = ttk.Checkbutton(advanced_frame, text="⚙️ Advanced Features", 
                                      variable=self.show_advanced, command=self.toggle_advanced,
                                      style='AICheckbutton.TCheckbutton')
        advanced_btn.pack(anchor='w', pady=(0, 5))
        
        # Advanced options (initially hidden)
        self.advanced_options = tk.Frame(advanced_frame, bg=self.colors['bg_secondary'])
        
        # Advanced features in grid
        features_grid = tk.Frame(self.advanced_options, bg=self.colors['bg_secondary'])
        features_grid.pack(fill='x', pady=5)
        
        # Anti-copyright features (using existing variables from __init__)
        # Note: Variables already defined in __init__, no need to redefine
        
        ttk.Checkbutton(features_grid, text="🪞 Mirror", variable=self.mirror_video,
                       style='AICheckbutton.TCheckbutton').grid(row=0, column=0, sticky='w', padx=(0, 10))
        ttk.Checkbutton(features_grid, text="⚡ Speed", variable=self.speed_change,
                       style='AICheckbutton.TCheckbutton').grid(row=0, column=1, sticky='w', padx=(0, 10))
        ttk.Checkbutton(features_grid, text="🌟 Brightness", variable=self.brightness_change,
                       style='AICheckbutton.TCheckbutton').grid(row=1, column=0, sticky='w', padx=(0, 10))
        ttk.Checkbutton(features_grid, text="✂️ Crop", variable=self.crop_video,
                       style='AICheckbutton.TCheckbutton').grid(row=1, column=1, sticky='w', padx=(0, 10))
        # Enhanced watermark section (replacing simple checkbox)
        watermark_frame = tk.Frame(features_grid, bg=self.colors['bg_secondary'])
        watermark_frame.grid(row=2, column=0, sticky='ew', columnspan=2, pady=(5, 0))
        
        # Watermark enable checkbox
        ttk.Checkbutton(watermark_frame, text="💧 Custom Watermark", variable=self.add_watermark,
                       style='AICheckbutton.TCheckbutton', command=self.on_watermark_toggle).pack(anchor='w')
        
        # Watermark settings (initially hidden)
        self.watermark_settings = tk.Frame(watermark_frame, bg=self.colors['bg_secondary'])
        
        # File selection
        file_row = tk.Frame(self.watermark_settings, bg=self.colors['bg_secondary'])
        file_row.pack(fill='x', pady=(5, 2))
        
        tk.Label(file_row, text="📁 Logo:", font=self.get_system_font(9, 'normal'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        file_entry = ttk.Entry(file_row, textvariable=self.watermark_file, 
                              style='AIEntry.TEntry', font=self.get_system_font(8, 'normal'), width=20)
        file_entry.pack(side='left', padx=(5, 3), expand=True, fill='x')
        
        ttk.Button(file_row, text="📂", command=self.browse_watermark_file,
                  style='AIButton.TButton', width=3).pack(side='right')
        
        # Position and settings row
        settings_row = tk.Frame(self.watermark_settings, bg=self.colors['bg_secondary'])
        settings_row.pack(fill='x', pady=(2, 0))
        
        # Position dropdown
        tk.Label(settings_row, text="📍", font=self.get_system_font(9, 'normal'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        position_combo = ttk.Combobox(settings_row, textvariable=self.watermark_position,
                                     values=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
                                     width=10, style='AIEntry.TCombobox', 
                                     font=self.get_system_font(8, 'normal'), state="readonly")
        position_combo.pack(side='left', padx=(2, 5))
        
        # Size dropdown
        tk.Label(settings_row, text="📏", font=self.get_system_font(9, 'normal'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        size_combo = ttk.Combobox(settings_row, textvariable=self.watermark_size,
                                 values=["small", "medium", "large"], width=7,
                                 style='AIEntry.TCombobox', font=self.get_system_font(8, 'normal'), 
                                 state="readonly")
        size_combo.pack(side='left', padx=(2, 5))
        
        # Opacity dropdown
        tk.Label(settings_row, text="🌓", font=self.get_system_font(9, 'normal'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        opacity_combo = ttk.Combobox(settings_row, textvariable=self.watermark_opacity,
                                    values=["0.3", "0.5", "0.7", "0.9"], width=5,
                                    style='AIEntry.TCombobox', font=self.get_system_font(8, 'normal'), 
                                    state="readonly")
        opacity_combo.pack(side='left', padx=(2, 0))
        
        # Initially hide settings
        if not self.add_watermark.get():
            self.watermark_settings.pack_forget()
        
        # Social media format
        format_frame = tk.Frame(self.advanced_options, bg=self.colors['bg_secondary'])
        format_frame.pack(fill='x', pady=(8, 0))
        
        format_check = ttk.Checkbutton(format_frame, text="📱 Social Media Format", 
                                      variable=self.convert_to_portrait, command=self.on_portrait_toggle,
                                      style='AICheckbutton.TCheckbutton')
        format_check.pack(anchor='w')
        
        # Use existing aspect_ratio and aspect_crop_mode variables (defined in __init__)
        self.aspect_combo = ttk.Combobox(format_frame, textvariable=self.aspect_ratio,
                                        values=["9:16 (YT Shorts/Reels)", "4:5 (Instagram)", 
                                               "1:1 (Square)", "16:9 (Landscape)"],
                                        state="readonly", style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'))
        self.aspect_combo.pack(fill='x', pady=(3, 0))
        self.aspect_combo.configure(state='disabled')
        
        # Crop mode selection for compact mode
        self.crop_mode_combo_compact = ttk.Combobox(format_frame, textvariable=self.aspect_crop_mode,
                                                   values=["fit (+ black bars)", "crop (potong video)"],
                                                   state="readonly", style='AIEntry.TCombobox', font=self.get_system_font(9, 'normal'))
        self.crop_mode_combo_compact.pack(fill='x', pady=(3, 0))
        self.crop_mode_combo_compact.configure(state='disabled')
        

        
        # Video Quality section
        quality_frame = tk.Frame(self.advanced_options, bg=self.colors['bg_secondary'])
        quality_frame.pack(fill='x', pady=(8, 0))
        
        tk.Label(quality_frame, text="🎥 Video Quality & Resolution:", font=self.get_system_font(9, 'bold'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor='w')
        
        # Target Resolution section
        resolution_frame = tk.Frame(quality_frame, bg=self.colors['bg_secondary'])
        resolution_frame.pack(fill='x', pady=(5, 8))
        
        tk.Label(resolution_frame, text="📏 Target Resolution:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        resolution_combo = ttk.Combobox(resolution_frame, textvariable=self.target_resolution,
                                       values=["4K (2160p)", "1080p (Full HD)", "720p (HD)", "original"],
                                       width=15, style='AIEntry.TCombobox', font=self.get_system_font(8, 'normal'), state="readonly")
        resolution_combo.pack(side='left', padx=(5, 10))
        
        # Social Media Optimization
        social_check = ttk.Checkbutton(resolution_frame, text="📱 Social Media Optimized", 
                                      variable=self.social_optimized,
                                      style='AICheckbutton.TCheckbutton')
        social_check.pack(side='left', padx=(10, 0))
        
        # Quality options frame
        quality_opts_frame = tk.Frame(quality_frame, bg=self.colors['bg_secondary'])
        quality_opts_frame.pack(fill='x', pady=(3, 2))
        
        tk.Label(quality_opts_frame, text="Preset:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        quality_combo = ttk.Combobox(quality_opts_frame, textvariable=self.video_quality,
                                   values=["ultra", "high", "medium", "fast"], width=8,
                                   style='AIEntry.TCombobox', font=self.get_system_font(8, 'normal'), state="readonly")
        quality_combo.pack(side='left', padx=(5, 10))
        
        # CRF setting
        tk.Label(quality_opts_frame, text="Quality:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(side='left')
        
        crf_combo = ttk.Combobox(quality_opts_frame, textvariable=self.video_crf,
                               values=["12", "15", "16", "18", "20", "23"], width=4,
                               style='AIEntry.TCombobox', font=self.get_system_font(8, 'normal'), state="readonly")
        crf_combo.pack(side='left', padx=(5, 0))
        
        # Quality info with resolution details
        quality_info = tk.Label(quality_frame, 
                               text="💡 CRF: 12=Cinema, 15=Excellent, 16=High, 18=Good, 20=Medium, 23=Low\n📐 Resolution: 4K=3840x2160, 1080p=1920x1080, 720p=1280x720",
                               font=self.get_system_font(8, 'normal'), bg=self.colors['bg_secondary'], 
                               fg=self.colors['text_muted'], justify='left')
        quality_info.pack(anchor='w', pady=(2, 0))
        
    def setup_compact_output_section(self, parent):
        """Compact output settings"""
        # Create modern card
        output_card = tk.Frame(parent, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        output_card.pack(fill='x', pady=(0, 8), padx=4, ipady=10)
        
        # Header
        header_frame = tk.Frame(output_card, bg=self.colors['bg_secondary'])
        header_frame.pack(fill='x', pady=(5, 8))
        
        tk.Label(header_frame, text="📁 Output", 
                font=self.get_system_font(11, 'bold'), 
                bg=self.colors['bg_secondary'],
                fg=self.colors['accent_ai']).pack(anchor='w')
        
        # Output folder selection
        folder_row = tk.Frame(output_card, bg=self.colors['bg_secondary'])
        folder_row.pack(fill='x', pady=(0, 5))
        
        tk.Label(folder_row, text="Folder:", font=self.get_system_font(9, 'normal'), 
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], width=8).pack(side='left')
        
        folder_entry = ttk.Entry(folder_row, textvariable=self.output_folder, 
                                style='AIEntry.TEntry', font=self.get_system_font(9, 'normal'))
        folder_entry.pack(side='left', fill='x', expand=True)
        
        ttk.Button(folder_row, text="📂", command=self.browse_output_folder, 
                  style='AIButton.TButton', width=3).pack(side='right', padx=(5, 0))
        
    def setup_compact_processing_section(self, parent):
        """Compact processing controls"""
        process_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        process_frame.pack(fill='x', pady=(8, 8))
        
        # Main process button (prominent)
        self.process_btn = ttk.Button(process_frame, text="🚀 Start AI Auto Clipping", 
                                     command=self.start_clipping, style='AIButton.TButton',
                                     width=25)
        self.process_btn.pack(side='left', padx=(0, 5))
        
        # Clear log button (compact)
        self.clear_log_btn = ttk.Button(process_frame, text="🗑️", 
                                       command=self.clear_log_manual, style='AIButton.TButton',
                                       width=3)
        self.clear_log_btn.pack(side='left', padx=(0, 10))
        
        # Status indicator
        self.status_label = tk.Label(process_frame, text="Ready", 
                                    font=self.get_system_font(9, 'normal'), bg=self.colors['bg_primary'], 
                                    fg=self.colors['text_secondary'])
        self.status_label.pack(side='left', anchor='center')
        
    def setup_compact_status_section(self, parent):
        """Enhanced status and results with larger log area"""
        status_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        status_frame.pack(fill='x', pady=(0, 8))
        
        # Progress bar
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', 
                                       style='AIProgress.Horizontal.TProgressbar')
        self.progress.pack(fill='x', pady=(0, 5))
        
        # Results container with proper scrollbar layout
        results_container = tk.Frame(status_frame, bg=self.colors['bg_primary'])
        results_container.pack(fill='both', expand=True)
        
        # Results area (enlarged for better visibility)
        self.results_text = tk.Text(results_container, height=10, bg=self.colors['bg_tertiary'],
                                   fg=self.colors['text_primary'], font=self.get_system_font(11, 'normal'),
                                   borderwidth=1, relief='solid', bd=1, wrap='word',
                                   selectbackground=self.colors['accent_ai'], selectforeground='white')
        
        # Results scrollbar (properly positioned)
        results_scroll = ttk.Scrollbar(results_container, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        
        # Pack text and scrollbar properly
        self.results_text.pack(side='left', fill='both', expand=True)
        results_scroll.pack(side='right', fill='y')
        
        # Add initial message
        self.results_text.insert('1.0', "🤖 AI Auto Clipper Ready\n\n💡 Tips:\n• Paste your video URL\n• Configure AI settings\n• Click 'Start AI Auto Clipping'\n• Logs will appear here during processing\n\n")
        self.results_text.configure(state='disabled')  # Make read-only initially
        
    def toggle_advanced(self):
        """Toggle advanced anti-copyright options"""
        if self.show_advanced.get():
            self.advanced_options.pack(fill='x', pady=(5, 0))
        else:
            self.advanced_options.pack_forget()
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            url = self.root.clipboard_get()
            self.video_url.set(url)
        except:
            pass
            
    def detect_platform(self, url):
        """Detect video platform from URL"""
        url_lower = url.lower()
        
        # Platform detection patterns
        platforms = {
            'YouTube': ['youtube.com', 'youtu.be', 'm.youtube.com'],
            'TikTok': ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'],
            'Instagram': ['instagram.com', 'instagr.am'],
            'Twitter': ['twitter.com', 'x.com', 't.co'],
            'Facebook': ['facebook.com', 'fb.watch', 'm.facebook.com'],
            'Bilibili': ['bilibili.com', 'b23.tv'],
            'Twitch': ['twitch.tv', 'clips.twitch.tv'],
            'Dailymotion': ['dailymotion.com', 'dai.ly'],
            'Vimeo': ['vimeo.com'],
            'LinkedIn': ['linkedin.com'],
            'Reddit': ['reddit.com', 'v.redd.it'],
            'Streamable': ['streamable.com'],
            'YouTube Music': ['music.youtube.com'],
            'Rumble': ['rumble.com'],
            'Odysee': ['odysee.com'],
            'Pinterest': ['pinterest.com'],
            'Snapchat': ['snapchat.com']
        }
        
        for platform, domains in platforms.items():
            if any(domain in url_lower for domain in domains):
                return platform
                
        return "Unknown Platform" if url.strip() else ""
        
    def on_url_change(self, *args):
        """Handle URL change to detect platform"""
        url = self.video_url.get()
        platform = self.detect_platform(url)
        
        # Update platform labels
        if hasattr(self, 'platform_label'):
            if platform and platform != "Unknown Platform":
                self.platform_label.config(text=f"📍 {platform}")
            else:
                self.platform_label.config(text="")
                
        if hasattr(self, 'compact_platform_label'):
            if platform and platform != "Unknown Platform":
                self.compact_platform_label.config(text=f"📍 {platform}")
            else:
                self.compact_platform_label.config(text="")
                
        self.detected_platform.set(platform)
            
    def save_api_key(self):
        """Save API key to config file"""
        try:
            config_dir = Path.home() / ".ai_clipper"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.json"
            
            config = {"gemini_api_key": self.gemini_api_key.get()}
            
            with open(config_file, 'w') as f:
                json.dump(config, f)
                
            messagebox.showinfo("✅ Success", "API key berhasil disimpan!")
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Gagal menyimpan API key: {str(e)}")
            
    def load_api_key(self):
        """Load saved API key"""
        try:
            config_file = Path.home() / ".ai_clipper" / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.gemini_api_key.set(config.get("gemini_api_key", ""))
        except Exception:
            pass
            
    def extract_model_name(self, display_name):
        """Extract actual model name from display name"""
        if display_name == "auto":
            return "auto"
        elif "gemini-2.5-pro" in display_name:
            return "gemini-2.5-pro"
        elif "gemini-2.5-flash" in display_name:
            return "gemini-2.5-flash"
        elif "gemini-2.0-flash" in display_name:
            return "gemini-2.0-flash"
        elif "gemini-1.5-pro" in display_name:
            return "gemini-1.5-pro"
        elif "gemini-1.5-flash" in display_name:
            return "gemini-1.5-flash"
        else:
            return "gemini-1.5-flash"  # fallback

    def on_model_change(self, *args):
        """Handle model selection change"""
        display_name = self.model_choice.get()
        model = self.extract_model_name(display_name)
        
        if hasattr(self, 'model_info_label'):
            if model == "auto":
                self.model_info_label.config(text="🔄 Auto-detect: Optimal model berdasarkan API tier")
            elif model == "gemini-1.5-flash":
                self.model_info_label.config(text="⚡ Fast & efficient (Free tier)")
            elif model == "gemini-1.5-pro":
                self.model_info_label.config(text="🎯 High quality (Free tier)")
            elif model == "gemini-2.0-flash":
                self.model_info_label.config(text="🚀 Latest flash (Free tier)")
            elif model == "gemini-2.5-flash":
                self.model_info_label.config(text="⭐ Premium flash (Pro API required)")
            elif model == "gemini-2.5-pro":
                self.model_info_label.config(text="💎 Premium pro (Pro API required)")
    
    def on_transcript_mode_change(self, *args):
        """Handle transcript mode selection change"""
        mode = self.transcript_mode.get()
        
        if "Auto Fallback" in mode:
            info_text = "🔄 Coba YouTube subtitle dulu, jika gagal pakai Whisper"
        elif "YouTube Subtitle" in mode:
            info_text = "📜 Gunakan subtitle YouTube (Cepat, tapi tergantung ketersediaan)"
        elif "Whisper AI" in mode:
            info_text = "🤖 Generate dengan Whisper AI (Selalu tersedia, lebih akurat)"
        else:
            info_text = ""
            
        # Show info in status if available
        if hasattr(self, 'status_label') and info_text:
            self.status_label.config(text=info_text)
    
    def on_caption_language_change(self, *args):
        """Handle caption language selection change"""
        language = self.caption_language.get()
        
        if "auto" in language.lower():
            info_text = "🌐 Auto-detect language dari transcript"
        elif "english" in language.lower():
            info_text = "🇺🇸 Force English caption/subtitle"
        elif "indonesia" in language.lower():
            info_text = "🇮🇩 Force Indonesia caption/subtitle"
        else:
            info_text = ""
            
        # Show info in status if available
        if hasattr(self, 'status_label') and info_text:
            self.status_label.config(text=info_text)
        
        # Update caption preview to reflect language change
        self.root.after(200, self.update_caption_preview_settings)
            
    def on_caption_toggle(self):
        """Toggle caption options visibility"""
        if self.auto_caption.get():
            # Show caption options in Settings Tab only
            if hasattr(self, 'caption_options_settings'):
                self.caption_options_settings.pack(fill='x', pady=(5, 0))
                # Initialize preview after a short delay to ensure canvas is ready
                self.root.after(100, self.update_caption_preview_settings)
                # Force another update after canvas is fully loaded
                self.root.after(500, self.update_caption_preview_settings)
        else:
            # Hide caption options in Settings Tab only
            if hasattr(self, 'caption_options_settings'):
                self.caption_options_settings.pack_forget()
        
        # Auto-save settings after change
        self.root.after(1000, self.save_settings)
            
    def on_smart_duration_toggle(self):
        """Toggle between Fixed Duration and Smart Duration modes"""
        if self.smart_duration.get():
            # Show Smart Duration settings
            self.fixed_duration_frame.pack_forget()
            self.smart_duration_frame.pack(fill='x')
            
            # Update status to show Smart Duration mode
            if hasattr(self, 'status_label'):
                self.status_label.config(text="🧠 Smart Duration: AI akan potong berdasarkan inti topik")
        else:
            # Show Fixed Duration settings
            self.smart_duration_frame.pack_forget()
            self.fixed_duration_frame.pack(fill='x')
            
            # Update status to show Fixed Duration mode
            if hasattr(self, 'status_label'):
                self.status_label.config(text="⏱️ Fixed Duration: Potong dengan durasi tetap")
        
        # Auto-save settings after change
        self.root.after(1000, self.save_settings)
                
    def on_metadata_toggle(self):
        """Toggle custom author metadata options when remove metadata is enabled"""
        if self.remove_metadata.get():
            # Show custom author options
            self.custom_author_frame.pack(fill='x', pady=(5, 0))
            
            # If custom author is already enabled, show input field
            if self.add_custom_author.get():
                self.author_input_frame.pack(fill='x', pady=(2, 0))
                
            # Update status
            if hasattr(self, 'status_label'):
                self.status_label.config(text="📝 Remove metadata enabled - option untuk custom author tersedia")
        else:
            # Hide custom author options
            self.custom_author_frame.pack_forget()
            self.author_input_frame.pack_forget()
            
            # Update status
            if hasattr(self, 'status_label'):
                self.status_label.config(text="📝 Metadata akan dipertahankan dari video original")
                
    def on_custom_author_toggle(self):
        """Toggle author input field when custom author is enabled"""
        if self.add_custom_author.get():
            # Show author input field
            self.author_input_frame.pack(fill='x', pady=(2, 0))
            
            # Update status
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"👤 Custom author: '{self.custom_author_name.get()}' akan ditambahkan ke metadata")
        else:
            # Hide author input field
            self.author_input_frame.pack_forget()
            
            # Update status
            if hasattr(self, 'status_label'):
                self.status_label.config(text="📝 Hanya remove metadata, tidak add author custom")
            
    def get_selected_language(self):
        """Extract language code from UI selection"""
        language_setting = self.caption_language.get()
        
        if "auto" in language_setting.lower():
            return "auto"
        elif "english" in language_setting.lower() or "en" in language_setting:
            return "en"
        elif "indonesia" in language_setting.lower() or "id" in language_setting:
            return "id"
        else:
            return "auto"  # fallback
            
    def get_subtitle_language_priority(self):
        """Get language priority list for subtitle download based on user selection"""
        selected_lang = self.get_selected_language()
        
        if selected_lang == "en":
            return ['en', 'en-US', 'en-GB']  # English first
        elif selected_lang == "id":
            return ['id', 'id-ID']  # Indonesian first
        else:  # auto
            return ['en', 'id', 'en-US', 'en-GB', 'id-ID']  # Mixed priority
    
    def get_optimal_model(self):
        """Get optimal model based on API tier and user selection"""
        display_name = self.model_choice.get()
        selected_model = self.extract_model_name(display_name)
        
        if selected_model != "auto":
            return selected_model
        
        # Auto-detect optimal model based on API key capabilities
        api_key = self.gemini_api_key.get().strip()
        if not api_key:
            return "gemini-1.5-flash"  # Default fallback
            
        try:
            # Configure Gemini to test available models
            genai.configure(api_key=api_key)
            
            # Check available models and prioritize based on capabilities
            available_models = []
            premium_models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
                    if 'gemini-2.5' in model.name:
                        premium_models.append(model.name)
            
            # For Pro API users (have access to 2.5 models), prioritize premium models
            if premium_models:
                priority_models = [
                    "models/gemini-2.5-pro",      # Premium pro (highest quality) - BEST FOR PRO USERS
                    "models/gemini-2.5-flash",    # Premium flash (latest & fast) - EXCELLENT FOR PRO USERS
                    "models/gemini-2.0-flash",    # Latest stable
                    "models/gemini-1.5-pro",      # High quality
                    "models/gemini-1.5-flash"     # Fast & reliable
                ]
            else:
                # For Free API users, prioritize free tier models  
                priority_models = [
                    "models/gemini-1.5-pro",      # High quality (free tier)
                    "models/gemini-1.5-flash",    # Fast & reliable (free tier)
                    "models/gemini-2.0-flash",    # Latest stable (if available)
                ]
            
            # Select the best available model
            for preferred_model in priority_models:
                if preferred_model in available_models:
                    # Remove 'models/' prefix for display
                    return preferred_model.replace('models/', '')
                    
            # Fallback if no preferred models found
            return "gemini-1.5-flash"
            
        except Exception:
            # If error checking models, use safe default
            return "gemini-1.5-flash"
    
    def get_fallback_model(self, primary_model):
        """Get appropriate fallback model based on primary model failure"""
        fallback_options = {
            "gemini-2.5-pro": "gemini-2.5-flash",
            "gemini-2.5-flash": "gemini-2.0-flash", 
            "gemini-2.0-flash": "gemini-1.5-pro",
            "gemini-1.5-pro": "gemini-1.5-flash",
            "gemini-1.5-flash": "gemini-1.5-pro"
        }
        return fallback_options.get(primary_model, "gemini-1.5-flash")

    def test_api_connection(self):
        """Test Gemini API connection and show available models"""
        api_key = self.gemini_api_key.get().strip()
        if not api_key:
            messagebox.showerror("❌ Error", "Masukkan API key terlebih dahulu!")
            return
            
        try:
            # Configure Gemini with the API key
            genai.configure(api_key=api_key)
            
            # List available models
            models = []
            premium_models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model.name)
                    if 'gemini-2.5' in model.name or 'gemini-2.0' in model.name:
                        premium_models.append(model.name)
            
            if models:
                # Detect API tier
                api_tier = "🥇 Pro API" if premium_models else "🥉 Free API"
                
                models_text = "\n".join([f"✅ {model}" for model in models[:10]])  # Show first 10
                message = f"🎉 API Connection Successful!\n\n"
                message += f"API Tier: {api_tier}\n"
                message += f"Available Models: {len(models)}\n\n"
                message += f"Top Models:\n{models_text}"
                
                if len(models) > 10:
                    message += f"\n... dan {len(models)-10} model lainnya"
                
                if premium_models:
                    message += f"\n\n💎 Pro API Tier Detected!"
                    message += f"\n🚀 Premium Models Available: {len(premium_models)}"
                    message += f"\n✨ Rekomendasi: gemini-2.5-pro untuk highest quality"
                    message += f"\n⚡ Rekomendasi: gemini-2.5-flash untuk speed + quality balance"
                else:
                    message += f"\n\n🥉 Free API Tier"
                    message += f"\n✨ Rekomendasi: gemini-1.5-pro untuk best free quality"
                    message += f"\n⚡ Rekomendasi: gemini-1.5-flash untuk fastest processing"
                    
                messagebox.showinfo("✅ API Test Success", message)
                
                # Update auto-detect info
                if hasattr(self, 'model_info_label') and self.extract_model_name(self.model_choice.get()) == "auto":
                    optimal_model = self.get_optimal_model()
                    tier_text = "Pro API" if premium_models else "Free API"
                    self.model_info_label.config(text=f"🔄 Auto-detect: {optimal_model} ({tier_text})")
                    
            else:
                messagebox.showwarning("⚠️ Warning", "API connected but no models found with generateContent support")
                
        except Exception as e:
            error_msg = f"❌ API Test Failed!\n\nError: {str(e)}\n\n"
            error_msg += "Solusi:\n"
            error_msg += "1. Periksa API key di makersuite.google.com\n"
            error_msg += "2. Pastikan API key aktif dan valid\n"
            error_msg += "3. Cek koneksi internet\n"
            error_msg += "4. Pastikan Gemini API enabled"
            
            messagebox.showerror("❌ API Test Failed", error_msg)
            
    def validate_inputs(self):
        """Validate all inputs before processing"""
        if not self.gemini_api_key.get().strip():
            messagebox.showerror("❌ Error", "Gemini API key diperlukan!\n\nSilakan buka tab 'Settings' untuk mengatur API key.")
            return False
            
        if not self.video_url.get().strip():
            messagebox.showerror("❌ Error", "Video URL diperlukan!")
            return False
            
        # Check if URL is valid format
        url = self.video_url.get().strip()
        if not re.match(r'https?://', url):
            messagebox.showerror("❌ Error", "URL harus dimulai dengan http:// atau https://!")
            return False
            
        # Check if platform is supported
        platform = self.detect_platform(url)
        if platform == "Unknown Platform":
            # Still allow unknown platforms as yt-dlp might support them
            result = messagebox.askyesno("⚠️ Platform Tidak Dikenal", 
                                       f"Platform tidak dikenal dari URL ini.\n\nMasih ingin mencoba? yt-dlp mendukung 1000+ platform.")
            if not result:
                return False
            
        try:
            int(self.clip_duration.get())
            int(self.max_clips.get())
        except ValueError:
            messagebox.showerror("❌ Error", "Durasi clip dan max clips harus berupa angka!")
            return False
            
        return True
        
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        self.root.update()
        
    def start_ai_clipping(self):
        """Start the AI clipping process"""
        if not self.validate_inputs():
            return
            
        self.start_btn.config(state="disabled")
        self.progress.start(10)
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=self.ai_clipping_workflow, daemon=True).start()
        
    def ai_clipping_workflow(self):
        """Main AI clipping workflow"""
        try:
            # Step 1: Download video from detected platform
            platform = self.detected_platform.get() or "platform yang dipilih"
            self.update_status(f"📥 Mengunduh video dari {platform}...")
            self.download_video()
            
            # Step 2: Extract audio and transcript
            self.update_status("🎵 Mengextract audio dan membuat transcript...")
            self.extract_audio_and_transcript()
            
            # Step 3: AI Analysis with Gemini
            self.update_status("🧠 Menganalisis video dengan Gemini AI...")
            self.analyze_with_gemini()
            
            # Step 4: Generate clips
            self.update_status("✂️ Membuat clips berdasarkan analisis AI...")
            self.generate_clips()
            
            # Step 5: Show results
            self.update_status("✅ AI Auto Clipping selesai!")
            self.show_results()
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Error dalam proses AI clipping: {str(e)}")
        finally:
            self.root.after(0, self.reset_ui)
            
    def download_video(self):
        """Download video from multiple platforms using yt-dlp"""
        # Create temp directory for processing with better error handling
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="ai_clipper_")
            # Test write permission
            test_file = os.path.join(self.temp_dir, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except (OSError, IOError, PermissionError) as e:
            # Fallback to Downloads folder if temp fails
            try:
                fallback_dir = str(Path.home() / "Downloads" / "AI_Clipper_Temp")
                os.makedirs(fallback_dir, exist_ok=True)
                self.temp_dir = fallback_dir
                self.update_status(f"⚠️ Using fallback directory: {fallback_dir}")
            except Exception:
                raise Exception(f"Cannot create temporary directory: {str(e)}")
        except Exception as e:
            raise Exception(f"Temporary directory creation failed: {str(e)}")
        
        # Get platform info for optimization
        platform = self.detected_platform.get()
        url = self.video_url.get()
        
        # Base yt-dlp options - CONDITIONAL SUBTITLE DOWNLOAD BASED ON USER CHOICE
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(self.temp_dir, 'video.%(ext)s'),
            'ignoreerrors': True,       # Continue if some operations fail
            'no_warnings': True,        # Reduce output noise
            'retries': 3,              # Add retry mechanism
            'sleep_interval': 1,       # Add delay between requests
        }
        
        # Conditional subtitle download based on user preference with LANGUAGE SELECTION
        mode = self.transcript_mode.get()
        if "YouTube Subtitle" in mode or "Auto Fallback" in mode:
            # User wants to try YouTube subtitles - prioritize selected language
            language_priority = self.get_subtitle_language_priority()
            selected_lang = self.get_selected_language()
            
            ydl_opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': language_priority,  # Use user-selected language priority
                'subtitlesformat': 'srt',  # Prefer SRT format
            })
            
            if selected_lang == "en":
                self.update_status("📜 Mode: YouTube Subtitle (🇺🇸 English priority)")
            elif selected_lang == "id":
                self.update_status("📜 Mode: YouTube Subtitle (🇮🇩 Indonesia priority)")
            else:
                self.update_status("📜 Mode: YouTube Subtitle (🌐 Auto-detect language)")
        else:
            # User only wants Whisper AI
            ydl_opts.update({
                'writesubtitles': False,
                'writeautomaticsub': False,
            })
            selected_lang = self.get_selected_language()
            if selected_lang == "en":
                self.update_status("🤖 Mode: Whisper AI (🇺🇸 English)")
            elif selected_lang == "id":
                self.update_status("🤖 Mode: Whisper AI (🇮🇩 Indonesia)")
            else:
                self.update_status("🤖 Mode: Whisper AI (🌐 Auto-detect language)")
        
        # Platform-specific optimizations - FOKUS HANYA VIDEO QUALITY
        if platform == 'TikTok':
            # TikTok specific settings
            ydl_opts.update({
                'format': 'best',  # TikTok videos are usually single format
            })
        elif platform == 'Instagram':
            # Instagram specific settings
            ydl_opts.update({
                'format': 'best[ext=mp4]/best',
            })
        elif platform == 'Twitter':
            # Twitter/X specific settings
            ydl_opts.update({
                'format': 'best[ext=mp4]/best',
            })
        elif platform == 'Facebook':
            # Facebook specific settings
            ydl_opts.update({
                'format': 'best[ext=mp4]/best',
            })
        
        self.update_status(f"📥 Downloading video from {platform}...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to check if video is available
                self.update_status("🔍 Checking video availability...")
                info = ydl.extract_info(url, download=False)
                self.video_title = info.get('title', 'Unknown')
                self.video_platform = platform
                
                # Download the video
                self.update_status(f"⬇️ Downloading: {self.video_title[:50]}...")
                ydl.download([url])
                
        except yt_dlp.DownloadError as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                raise Exception(f"Rate limit exceeded. Please wait 5-10 minutes before trying again.\nDetails: {error_str}")
            elif "403" in error_str or "Forbidden" in error_str:
                raise Exception(f"Video access denied. Video might be private or region-blocked.\nDetails: {error_str}")
            elif "404" in error_str or "Not Found" in error_str:
                raise Exception(f"Video not found. Please check the URL.\nDetails: {error_str}")
            else:
                raise Exception(f"Download failed: {error_str}")
        except Exception as e:
            raise Exception(f"Unexpected error during download: {str(e)}")
            
        # Find downloaded video file
        for file in os.listdir(self.temp_dir):
            if file.startswith('video.') and file.endswith(('.mp4', '.webm', '.mkv', '.mov')):
                self.video_path = os.path.join(self.temp_dir, file)
                break
                
        if not self.video_path:
            raise Exception(f"Video download failed from {platform}")
            
    def extract_audio_and_transcript(self):
        """Extract audio and create transcript using YouTube subtitle OR Whisper AI based on user choice"""
        mode = self.transcript_mode.get()
        
        # Try YouTube subtitle first if user selected it
        if "YouTube Subtitle" in mode or "Auto Fallback" in mode:
            subtitle_success = self.try_youtube_subtitle()
            
            if subtitle_success:
                self.update_status("✅ Menggunakan subtitle YouTube")
                return
            elif "YouTube Subtitle" in mode:
                # User specifically wanted YouTube subtitle but it failed
                raise Exception("YouTube subtitle tidak tersedia untuk video ini.\n\n💡 Solusi:\n• Pilih mode 'Auto Fallback' atau 'Whisper AI'\n• Tidak semua video YouTube memiliki subtitle")
            else:
                # Auto fallback mode - continue to Whisper
                self.update_status("⚠️ YouTube subtitle tidak tersedia, fallback ke Whisper AI...")
        
        # Use Whisper AI (either by choice or fallback)
        self.update_status("🤖 Generating transcript dengan Whisper AI...")
        self.use_whisper_ai()
        
    def try_youtube_subtitle(self):
        """Try to use YouTube subtitle if available"""
        try:
            # Look for downloaded subtitle files
            subtitle_files = []
            for file in os.listdir(self.temp_dir):
                if file.endswith(('.srt', '.vtt')) and 'video.' in file:
                    subtitle_files.append(os.path.join(self.temp_dir, file))
            
            if not subtitle_files:
                return False
                
            # Use the first available subtitle file
            subtitle_path = subtitle_files[0]
            self.update_status(f"📜 Found subtitle: {os.path.basename(subtitle_path)}")
            
            # Parse subtitle file to create transcript format compatible with Whisper
            self.transcript = self.parse_subtitle_file(subtitle_path)
            return True
            
        except Exception as e:
            self.update_status(f"⚠️ YouTube subtitle parsing failed: {str(e)}")
            return False
            
    def parse_subtitle_file(self, subtitle_path):
        """Parse SRT/VTT subtitle file to Whisper-compatible format"""
        try:
            segments = []
            
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple SRT parsing
            if subtitle_path.endswith('.srt'):
                import re
                
                # SRT format pattern
                pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\n*$)'
                matches = re.findall(pattern, content, re.DOTALL)
                
                for match in matches:
                    start_time = self.srt_time_to_seconds(match[1])
                    end_time = self.srt_time_to_seconds(match[2])
                    text = match[3].strip().replace('\n', ' ')
                    
                    # Clean subtitle text before adding to segments
                    text = self.clean_subtitle_text(text)
                    
                    segments.append({
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    })
                    
            # Create Whisper-compatible transcript format with DYNAMIC LANGUAGE
            selected_lang = self.get_selected_language()
            detected_language = selected_lang if selected_lang != "auto" else "en"  # Fallback to English if auto
            
            transcript = {
                'text': ' '.join([seg['text'] for seg in segments]),
                'segments': segments,
                'language': detected_language  # Use selected or detected language
            }
            
            return transcript
            
        except Exception as e:
            raise Exception(f"Failed to parse subtitle file: {str(e)}")
            
    def srt_time_to_seconds(self, time_str):
        """Convert SRT time format (HH:MM:SS,mmm) to seconds"""
        time_str = time_str.replace(',', '.')  # Replace comma with dot for milliseconds
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
        
    def use_whisper_ai(self):
        """Generate transcript using Whisper AI with LANGUAGE SELECTION"""
        # Extract audio from video
        self.audio_path = os.path.join(self.temp_dir, 'audio.wav')
        
        cmd = [
            'ffmpeg', '-i', self.video_path,
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            '-y', self.audio_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Get selected language for Whisper
        selected_lang = self.get_selected_language()
        
        # Load Whisper model and transcribe with language setting
        self.update_status("🧠 Loading Whisper model...")
        model = whisper.load_model("base")
        
        # Prepare transcribe options based on language selection
        transcribe_options = {'word_timestamps': True}
        
        if selected_lang == "en":
            transcribe_options['language'] = 'en'
            self.update_status("🎤 Transcribing audio dengan Whisper (🇺🇸 English)...")
        elif selected_lang == "id":
            transcribe_options['language'] = 'id'
            self.update_status("🎤 Transcribing audio dengan Whisper (🇮🇩 Indonesia)...")
        else:  # auto
            # Let Whisper auto-detect language
            self.update_status("🎤 Transcribing audio dengan Whisper (🌐 Auto-detect)...")
        
        result = model.transcribe(self.audio_path, **transcribe_options)
        
        # Add detected language info to transcript
        detected_lang = result.get('language', 'unknown')
        self.update_status(f"✅ Whisper detected language: {detected_lang}")
        
        self.transcript = result
        
    def analyze_with_gemini(self):
        """Analyze transcript with Gemini AI to find important/emotional segments"""
        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key.get())
        
        # Get selected or optimal model
        selected_model = self.get_optimal_model()
        
        # Update status based on clipping mode
        if self.smart_duration.get():
            self.update_status(f"🧠 Smart Duration Analysis: Using {selected_model} untuk cari inti topik")
        else:
            self.update_status(f"⏱️ Fixed Duration Analysis: Using {selected_model} untuk potong durasi tetap")
        
        model = genai.GenerativeModel(selected_model)
        
        # Prepare transcript text with timestamps and ENHANCED CONTEXT
        transcript_text = ""
        total_segments = len(self.transcript['segments'])
        
        # Add context window for better boundary detection
        context_window = 2  # Look at 2 segments before and after
        
        for i, segment in enumerate(self.transcript['segments']):
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text']
            
            # Add context markers for better boundary detection
            context_info = ""
            if i == 0:
                context_info = "[START_OF_VIDEO] "
            elif i == total_segments - 1:
                context_info = "[END_OF_VIDEO] "
            
            # Add pause detection for natural boundaries
            pause_detection = ""
            if i < total_segments - 1:
                next_segment = self.transcript['segments'][i + 1]
                gap = next_segment['start'] - end_time
                if gap > 1.0:  # Gap lebih dari 1 detik
                    pause_detection = f" [PAUSE_{gap:.1f}s]"
                elif gap > 0.5:  # Gap lebih dari 0.5 detik
                    pause_detection = f" [SMALL_PAUSE_{gap:.1f}s]"
            
            transcript_text += f"[{start_time:.1f}s - {end_time:.1f}s]{context_info}{text}{pause_detection}\n"
        
        # AI prompt for analysis - ENHANCED SMART DURATION with context awareness
        if self.smart_duration.get():
            # ENHANCED SMART DURATION MODE: Context-aware content-based clipping
            prompt = f"""
Analisis transcript video berikut dengan CONTEXT AWARENESS dan identifikasi maksimal {self.max_clips.get()} bagian paling menarik berdasarkan INTI TOPIK dan NATURAL CONTENT BOUNDARIES.

🧠 ENHANCED SMART DURATION MODE: 
- Potong berdasarkan topik/konten dengan context awareness
- Gunakan pause detection dan natural boundaries
- Validasi complete thoughts dan sentences
- Context window analysis untuk boundary yang tepat

Fokus pada momen yang: {self.emotion_focus.get()}

EMOTION CONTEXT:
- excitement: Momen yang membangkitkan semangat, energi tinggi, antusiasme
- funny: Humor, lelucon, momen lucu dan menghibur
- dramatic: Ketegangan, konflik, momen yang menegangkan
- inspiring: Motivasi, kata-kata bijak, momen yang menginspirasi
- shocking: Kejutan, momen yang mengejutkan dan tidak terduga
- emotional: Momen yang menyentuh hati, berbagai emosi
- sad: Momen sedih, melankolis, kesedihan mendalam, kata-kata yang mengharukan
- melancholic: Momen yang melankolis, nostalgia, perasaan yang dalam, kenangan masa lalu
- touching: Momen yang menyentuh hati, mengharukan, emosional, kata-kata yang menyentuh jiwa

KHUSUS UNTUK EMOSI SEDIH/MELANKOLIS:
- sad: Fokus pada momen yang mengekspresikan kesedihan mendalam, kehilangan, atau perasaan yang mengharukan
- melancholic: Cari momen nostalgia, kenangan masa lalu, atau perasaan melankolis yang dalam
- touching: Pilih bagian yang menyentuh hati, mengharukan, atau memiliki emotional impact yang kuat

Transcript dengan Context Markers:
{transcript_text}

🎯 ENHANCED INSTRUKSI SMART DURATION:
1. **CONTEXT AWARENESS**: Lihat 2 segment sebelum dan sesudah untuk boundary yang tepat
2. **PAUSE DETECTION**: Gunakan [PAUSE_X.Xs] dan [SMALL_PAUSE_X.Xs] untuk natural breaks
3. **COMPLETE THOUGHTS**: Jangan potong di tengah kalimat atau topic
4. **NATURAL BOUNDARIES**: Cari pause, topic change, emotional shift, atau complete thoughts
5. **QUALITY OVER DURATION**: Prioritas konten yang meaningful dan complete
6. **Durasi minimum**: {self.min_clip_duration.get()} detik
7. **Durasi maksimum**: {self.max_clip_duration.get()} detik
8. **BOUNDARY VALIDATION**: Pastikan start dan end di tempat yang natural

🔍 BOUNDARY DETECTION STRATEGY:
- [START_OF_VIDEO]: Mulai dari awal jika konten menarik
- [END_OF_VIDEO]: Akhiri di akhir jika konten complete
- [PAUSE_X.Xs]: Gunakan pause panjang sebagai natural boundary
- [SMALL_PAUSE_X.Xs]: Gunakan pause pendek jika tidak ada alternatif
- Topic change: Cari pergeseran topik yang jelas
- Emotional shift: Cari perubahan emosi yang signifikan
- Complete sentences: Pastikan tidak memotong di tengah kalimat

KHUSUS UNTUK EMOSI SEDIH/MELANKOLIS:
- Cari momen yang mengekspresikan kesedihan, nostalgia, atau melankolis
- Fokus pada kata-kata yang menyentuh hati dan emosional
- Pilih bagian yang memiliki emotional depth dan meaning
- Hindari potong di tengah ekspresi emosi
- Prioritas pada momen yang mengekspresikan perasaan dalam dan autentik
- Cari bagian yang bisa membuat penonton terharu dan tersentuh
- Perhatikan intonasi suara yang sedih, melankolis, atau mengharukan
- Cari momen yang mengekspresikan kerinduan, kehilangan, atau perasaan mendalam
- Pilih bagian yang memiliki emotional storytelling yang kuat

Untuk setiap clip yang direkomendasikan, berikan:
1. Start time (dalam detik) - di awal complete topic dengan context validation
2. End time (dalam detik) - di akhir complete topic/natural pause dengan context validation
3. Alasan mengapa bagian ini menarik dan complete dengan boundary justification
4. Tingkat emosi (1-10)
5. Judul singkat untuk clip
6. Content summary - ringkasan inti topik
7. Boundary confidence (high/medium/low) - seberapa yakin boundary ini natural

Format response sebagai JSON array:
[
  {{
    "start_time": 45.2,
    "end_time": 127.8,
    "reason": "Complete explanation about economic system - natural topic boundary dengan pause 2.3s",
    "emotion_score": 8,
    "title": "Sistem Ekonomi Kapitalistik",
    "content_summary": "Penjelasan lengkap tentang sistem ekonomi kapitalistik dan dampaknya",
    "boundary_confidence": "high"
  }}
]

PENTING: 
- Durasi boleh bervariasi (20-180 detik) asalkan konten COMPLETE dan MEANINGFUL
- Gunakan context markers untuk boundary yang tepat
- Validasi setiap boundary dengan context window
- Prioritas pada natural breaks dan complete thoughts
"""
        else:
            # FIXED DURATION MODE: Traditional fixed-duration clipping
            prompt = f"""
Analisis transcript video berikut dan identifikasi {self.max_clips.get()} bagian paling menarik dan emosional.

FIXED DURATION MODE: Potong dengan durasi tetap.

Fokus pada momen yang: {self.emotion_focus.get()}

EMOTION CONTEXT:
- excitement: Momen yang membangkitkan semangat, energi tinggi, antusiasme
- funny: Humor, lelucon, momen lucu dan menghibur
- dramatic: Ketegangan, konflik, momen yang menegangkan
- inspiring: Motivasi, kata-kata bijak, momen yang menginspirasi
- shocking: Kejutan, momen yang mengejutkan dan tidak terduga
- emotional: Momen yang menyentuh hati, berbagai emosi
- sad: Momen sedih, melankolis, kesedihan mendalam, kata-kata yang mengharukan
- melancholic: Momen yang melankolis, nostalgia, perasaan yang dalam, kenangan masa lalu
- touching: Momen yang menyentuh hati, mengharukan, emosional, kata-kata yang menyentuh jiwa

KHUSUS UNTUK EMOSI SEDIH/MELANKOLIS:
- sad: Fokus pada momen yang mengekspresikan kesedihan mendalam, kehilangan, atau perasaan yang mengharukan
- melancholic: Cari momen nostalgia, kenangan masa lalu, atau perasaan melankolis yang dalam
- touching: Pilih bagian yang menyentuh hati, mengharukan, atau memiliki emotional impact yang kuat

Transcript:
{transcript_text}

Untuk setiap clip yang direkomendasikan, berikan:
1. Start time (dalam detik)
2. End time (dalam detik) 
3. Alasan mengapa bagian ini menarik
4. Tingkat emosi (1-10)
5. Judul singkat untuk clip

Format response sebagai JSON array dengan struktur:
[
  {{
    "start_time": 45.2,
    "end_time": 78.5, 
    "reason": "Momen klimaks yang sangat emosional",
    "emotion_score": 9,
    "title": "Klimaks Emosional"
  }}
]

Pastikan setiap clip berdurasi sekitar {self.clip_duration.get()} detik.

KHUSUS UNTUK EMOSI SEDIH/MELANKOLIS:
- Cari momen yang mengekspresikan kesedihan, nostalgia, atau melankolis
- Fokus pada kata-kata yang menyentuh hati dan emosional
- Pilih bagian yang memiliki emotional depth dan meaning
- Hindari potong di tengah ekspresi emosi
- Prioritas pada momen yang mengekspresikan perasaan dalam dan autentik
- Cari bagian yang bisa membuat penonton terharu dan tersentuh
- Perhatikan intonasi suara yang sedih, melankolis, atau mengharukan
- Cari momen yang mengekspresikan kerinduan, kehilangan, atau perasaan mendalam
- Pilih bagian yang memiliki emotional storytelling yang kuat
"""

        try:
            response = model.generate_content(prompt)
            # Extract JSON from response
            response_text = response.text
            
            # Find JSON in response (handle potential formatting issues)
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                self.ai_analysis = json.loads(json_match.group())
                
                # ENHANCED: Validate and improve boundaries if smart duration is enabled
                if self.smart_duration.get():
                    self.ai_analysis = self.validate_and_improve_boundaries(self.ai_analysis)
                    
            else:
                raise Exception("AI tidak mengembalikan format JSON yang valid")
                
        except Exception as e:
            # Try fallback model if primary fails
            try:
                # Get secondary model based on what failed
                fallback_model_name = self.get_fallback_model(selected_model)
                self.update_status(f"🔄 Mencoba model alternatif: {fallback_model_name}")
                fallback_model = genai.GenerativeModel(fallback_model_name)
                response = fallback_model.generate_content(prompt)
                response_text = response.text
                
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    self.ai_analysis = json.loads(json_match.group())
                    
                    # ENHANCED: Validate and improve boundaries if smart duration is enabled
                    if self.smart_duration.get():
                        self.ai_analysis = self.validate_and_improve_boundaries(self.ai_analysis)
                        
                else:
                    raise Exception("AI tidak mengembalikan format JSON yang valid")
                    
            except Exception as fallback_error:
                # ENHANCED: If both models fail, use fallback clipping strategy
                self.update_status("🔄 AI analysis gagal, menggunakan fallback clipping strategy...")
                self.ai_analysis = self.generate_fallback_clips()
                
                if not self.ai_analysis:
                    # If fallback also fails, provide helpful error message
                    error_msg = f"Gemini analysis gagal:\n\n"
                    error_msg += f"Primary model ({selected_model}): {str(e)}\n"
                    error_msg += f"Fallback model ({fallback_model_name}): {str(fallback_error)}\n"
                    error_msg += f"Fallback clipping strategy: Gagal\n\n"
                    error_msg += "Solusi:\n"
                    error_msg += "1. Periksa API key Gemini di makersuite.google.com\n"
                    error_msg += "2. Pastikan API key aktif dan memiliki quota\n"
                    error_msg += "3. Coba video dengan transcript yang lebih jelas\n"
                    error_msg += "4. Periksa koneksi internet\n"
                    error_msg += "5. Coba model yang berbeda di dropdown AI Model\n"
                    error_msg += "6. Gunakan Fixed Duration mode sebagai alternatif"
                    raise Exception(error_msg)
            
    def generate_clips(self):
        """Generate video clips based on AI analysis"""
        if not self.ai_analysis:
            raise Exception("Tidak ada data analisis AI")
            
        # Create output directory
        output_dir = Path(self.download_path.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean video title for filename
        safe_title = re.sub(r'[^\w\s\-]', '', self.video_title)
        safe_title = re.sub(r'[\-\s]+', '-', safe_title)
        
        self.clips_data = []
        
        for i, clip_info in enumerate(self.ai_analysis, 1):
            start_time = clip_info['start_time']
            end_time = clip_info['end_time']
            clip_title = clip_info.get('title', f'Clip {i}')
            
            # Generate filename
            filename = f"{safe_title}_clip_{i:02d}_{clip_title}.mp4"
            filename = re.sub(r'[^\w\s\-\.]', '', filename)
            output_path = output_dir / filename
            
            # Get optimal encoding settings based on user choice
            encoding_settings = self.get_video_encoding_settings()
            target_res = self.target_resolution.get()
            
            # Use FFmpeg to create clip with HD-optimized settings
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),  # Seek before input for accuracy
                '-i', self.video_path,
                '-t', str(end_time - start_time),
                '-c:v', 'libx264',       # H.264 encoder
                '-preset', encoding_settings['preset'],  # Quality preset
                '-crf', encoding_settings['crf'],       # Constant Rate Factor
                '-pix_fmt', encoding_settings['pix_fmt'], # Pixel format
            ]
            
            # Add profile and level for high quality
            if 'profile' in encoding_settings:
                cmd.extend(['-profile:v', encoding_settings['profile']])
            if 'level' in encoding_settings:
                cmd.extend(['-level', encoding_settings['level']])
            
            # Add tune for social media optimization
            if 'tune' in encoding_settings and encoding_settings['tune']:
                cmd.extend(['-tune', encoding_settings['tune']])
                
            # Add rate control for social media optimization
            if 'maxrate' in encoding_settings:
                cmd.extend(['-maxrate', encoding_settings['maxrate']])
            if 'bufsize' in encoding_settings:
                cmd.extend(['-bufsize', encoding_settings['bufsize']])
                
            # Add GOP settings for social media compatibility
            if 'g' in encoding_settings:
                cmd.extend(['-g', encoding_settings['g']])
            if 'keyint_min' in encoding_settings:
                cmd.extend(['-keyint_min', encoding_settings['keyint_min']])
            if 'sc_threshold' in encoding_settings:
                cmd.extend(['-sc_threshold', encoding_settings['sc_threshold']])
                
            # Audio settings - optimize based on target resolution
            audio_bitrate = '192k' if "4K" in target_res or "1080p" in target_res else '128k'
            cmd.extend([
                '-c:a', 'aac',           # Re-encode audio for compatibility
                '-b:a', audio_bitrate,   # Audio bitrate based on target quality
                '-ar', '48000',          # Standard sample rate for social media
                '-ac', '2',              # Stereo audio
                '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
                '-fflags', '+genpts',    # Generate presentation timestamps
                '-reset_timestamps', '1', # Reset timestamps to start from 0
            ])
            
            # Add movflags (includes faststart for web optimization)
            if 'movflags' in encoding_settings:
                cmd.extend(['-movflags', encoding_settings['movflags']])
            else:
                cmd.extend(['-movflags', '+faststart'])
                
            cmd.extend(['-y', str(output_path)])
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # ENHANCED: Calculate quality score and boundary info
            quality_score = self.get_clip_quality_score(clip_info)
            boundary_suggestions = self.suggest_boundary_improvements(clip_info)
            
            # Store clip data with enhanced information
            self.clips_data.append({
                'filename': filename,
                'path': str(output_path),
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'title': clip_title,
                'reason': clip_info.get('reason', ''),
                'emotion_score': clip_info.get('emotion_score', 0),
                'quality_score': quality_score,
                'boundary_confidence': clip_info.get('boundary_confidence', 'unknown'),
                'boundary_suggestions': boundary_suggestions,
                'fallback_generated': clip_info.get('fallback_generated', False),
                'boundary_improved': clip_info.get('boundary_improved', False)
            })
            
            # Enhanced quality info with resolution and boundary quality
            quality_info = f"{encoding_settings['preset']} preset, CRF {encoding_settings['crf']}"
            if target_res != "original":
                quality_info += f", {target_res}"
            if self.social_optimized.get():
                quality_info += ", Social Optimized"
            
            # Add boundary quality info
            boundary_info = ""
            if clip_info.get('boundary_improved'):
                boundary_info = " (Boundary improved)"
            if clip_info.get('fallback_generated'):
                boundary_info = " (Fallback generated)"
            if clip_info.get('boundary_confidence'):
                boundary_info += f" [{clip_info['boundary_confidence']} confidence]"
            
            self.update_status(f"✂️ Membuat clip {i}/{len(self.ai_analysis)}: {clip_title} ({quality_info}){boundary_info}")
            
        # SINGLE-PASS PROCESSING: Combine anti-copyright + captions to avoid multiple re-encoding
        needs_anticopyright = any([self.remove_metadata.get(), self.mirror_video.get(), 
                                  self.speed_change.get(), self.brightness_change.get(), 
                                  self.crop_video.get(), self.add_watermark.get(), 
                                  self.convert_to_portrait.get()])
        needs_captions = self.auto_caption.get()
        
        if needs_anticopyright or needs_captions:
            self.update_status("🎬 Applying single-pass processing (anti-copyright + captions)...")
            self.apply_single_pass_processing()
        else:
            self.update_status("✅ No post-processing needed - preserving original quality")
    
    def apply_single_pass_processing(self):
        """Apply all post-processing (anti-copyright + captions) in SINGLE PASS to preserve quality"""
        try:
            # Check if FFmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            self.update_status("⚠️ FFmpeg tidak ditemukan, post-processing dilewati")
            return
        
        total_clips = len(self.clips_data)
        
        for i, clip_info in enumerate(self.clips_data, 1):
            clip_path = clip_info['path']
            clip_name = clip_info['filename']
            start_time = clip_info['start_time']
            end_time = clip_info['end_time']
            
            self.update_status(f"🎬 Single-pass processing clip {i}/{total_clips}: {clip_name[:30]}...")
            
            # Apply all processing in one FFmpeg command
            self.apply_single_pass_to_clip(clip_path, start_time, end_time)
            
        self.update_status(f"✅ Single-pass processing completed for {total_clips} clips!")
    
    def apply_single_pass_to_clip(self, clip_path, start_time, end_time):
        """Apply all processing to a single clip in ONE PASS to preserve maximum quality"""
        try:
            # Create temporary output file
            temp_path = clip_path.replace('.mp4', '_processed.mp4')
            
            # Build comprehensive filter chain
            video_filters = []
            audio_filters = []
            
            # === VIDEO FILTERS ===
            
            # 1. Mirror video (horizontal flip)
            if self.mirror_video.get():
                video_filters.append("hflip")
                self.update_status(f"🪞 Applying mirror effect to {os.path.basename(clip_path)}")
            
            # 2. Speed change (affects both video and audio)
            if self.speed_change.get():
                video_filters.append("setpts=PTS/0.95")
                audio_filters.append("atempo=0.95")
                self.update_status(f"⚡ Applying speed change (0.95x) to {os.path.basename(clip_path)}")
            
            # 3. Brightness & contrast adjustment
            if self.brightness_change.get():
                video_filters.append("eq=brightness=0.05:contrast=1.1")
                self.update_status(f"🌟 Applying brightness/contrast adjustment to {os.path.basename(clip_path)}")
            
            # 4. Crop edges (remove 2% from each side)
            if self.crop_video.get():
                video_filters.append("crop=iw*0.96:ih*0.96:(iw-iw*0.96)/2:(ih-ih*0.96)/2")
                self.update_status(f"✂️ Applying edge crop (2%) to {os.path.basename(clip_path)}")
            
            # 5. Convert to portrait/social media format
            if self.convert_to_portrait.get():
                aspect_filter = self.get_aspect_ratio_filter()
                if aspect_filter:
                    video_filters.append(aspect_filter)
                    ratio_text = self.aspect_ratio.get()
                    crop_mode = self.aspect_crop_mode.get()
                    mode_text = "CROP (potong)" if "crop" in crop_mode.lower() else "FIT (+black bars)"
                    self.update_status(f"📱 Converting to {ratio_text} format ({mode_text}): {os.path.basename(clip_path)}")
            
            # 6. Add custom PNG watermark (complex overlay)
            watermark_added = False
            if self.add_watermark.get():
                watermark_file = self.watermark_file.get().strip()
                
                if watermark_file and os.path.exists(watermark_file):
                    # Complex overlay for PNG watermark - handle separately
                    watermark_added = True
                else:
                    # Simple text watermark
                    watermark_text = "📱"
                    video_filters.append(f"drawtext=text='{watermark_text}':fontsize=20:fontcolor=white@0.3:x=w-tw-10:y=10")
            
            # 7. Add subtitle overlay
            subtitle_filter = None
            if self.auto_caption.get():
                # Generate SRT for this clip
                srt_path = self.generate_srt_for_clip(start_time, end_time, clip_path)
                if srt_path:
                    # Get caption position and style configuration
                    position = self.caption_style.get()
                    style_config = self.get_caption_style_preset()
                    
                    # Validate style config
                    if not style_config:
                        print("⚠️ Style config is empty, using default")
                        style_config = {
                            "font_size": int(self.caption_font_size.get()),
                            "color": "&H00FFFFFF",
                            "outline_color": "&H00000000",
                            "outline_width": "2",
                            "background": False,
                            "background_color": "&H80000000",
                            "font_weight": "normal",
                            "font_style": "normal"
                        }
                    
                    print(f"🎬 Applying subtitle with style: {self.caption_style_preset.get()}")
                    print(f"🎬 Style config: {style_config}")
                    
                    # Apply GLOBAL FONT SIZE - Fixed global font size for all styles
                    style_config = self.apply_global_font_size(style_config)
                    base_font_size = style_config["font_size"]
                    font_size = self.get_adjusted_font_size(base_font_size)
                    
                    print(f"🎬 Font size - Base: {base_font_size}, Adjusted: {font_size}")
                    
                    # Get margins based on aspect ratio
                    margin_v, margin_h = self.get_subtitle_margins()
                    
                    # Build style string from configuration using the style preset consistently
                    style_parts = [
                        f"Fontsize={font_size}",
                        f"PrimaryColour={style_config.get('color', '&H00FFFFFF')}",
                        f"OutlineColour={style_config.get('outline_color', '&H00000000')}",
                        f"Outline={style_config.get('outline_width', '2')}"
                    ]
                    
                    # Add background if enabled in the style preset
                    if style_config.get('background', False):
                        style_parts.append(f"BackColour={style_config.get('background_color', '&H80000000')}")
                    
                    # Add font weight from style preset
                    if style_config.get('font_weight') == 'bold':
                        style_parts.append("Bold=1")
                    
                    # Add font style from style preset
                    if style_config.get('font_style') == 'italic':
                        style_parts.append("Italic=1")
                    
                    # Add alignment based on position
                    if position == "bottom":
                        alignment = "2"
                    elif position == "top":
                        alignment = "8"
                    else:  # center
                        alignment = "5"
                    style_parts.append(f"Alignment={alignment}")
                    
                    # Add margins
                    style_parts.append(f"MarginV={margin_v}")
                    if self.convert_to_portrait.get() and "9:16" in self.aspect_ratio.get():
                        style_parts.extend(["MarginL=10", "MarginR=10"])
                    
                    # Combine style parts
                    style_string = ",".join(style_parts)
                    
                    print(f"🎬 Style parts: {style_parts}")
                    print(f"🎬 Final style string: {style_string}")
                    
                    # Escape SRT path for Windows compatibility
                    srt_path_escaped = srt_path.replace('\\', '\\\\\\\\').replace(':', '\\\\:')
                    
                    # For typewriter animation, we'll handle it differently to avoid black screen
                    # The typewriter effect is already implemented in the SRT generation
                    # So we don't need additional FFmpeg animation filters
                    if self.caption_animation.get() == "typewriter":
                        # Typewriter effect is handled in SRT generation, no additional filter needed
                        subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='{style_string}'"
                        print(f"🎬 Subtitle filter with typewriter (SRT-based): {subtitle_filter}")
                        self.update_status(f"🔍 Using style: {self.caption_style_preset.get()}, font size: {font_size}px, position: {position}, typewriter effect (SRT-based)")
                    else:
                        # Get animation filter for other animations
                        animation_filter = self.get_caption_animation_filter()
                        
                        # Build subtitle filter with custom style and animation
                        if animation_filter and animation_filter != "":
                            # Apply animation to subtitle
                            subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='{style_string}',{animation_filter}"
                            print(f"🎬 Subtitle filter with animation: {subtitle_filter}")
                            self.update_status(f"🔍 Using style: {self.caption_style_preset.get()}, font size: {font_size}px, position: {position}, animation: {self.caption_animation.get()}")
                        else:
                            # No animation
                            subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='{style_string}'"
                            print(f"🎬 Subtitle filter: {subtitle_filter}")
                            self.update_status(f"🔍 Using style: {self.caption_style_preset.get()}, font size: {font_size}px, position: {position}")
            
            # === BUILD FFMPEG COMMAND ===
            
            cmd = ['ffmpeg', '-i', clip_path]
            
            # Handle PNG watermark overlay (requires separate input)
            if watermark_added:
                watermark_file = self.watermark_file.get().strip()
                cmd.extend(['-i', watermark_file])
                
                # Build complex filter with watermark
                size_filter = self.get_watermark_size_filter()
                position_filter = self.get_watermark_position_filter()
                opacity = self.watermark_opacity.get()
                
                # Start complex filter
                complex_filter = f"[1:v]scale={size_filter},format=rgba,colorchannelmixer=aa={opacity}[watermark];"
                complex_filter += f"[0:v][watermark]overlay={position_filter}"
                
                # Add other video filters to complex filter
                if video_filters:
                    complex_filter += "," + ",".join(video_filters)
                
                # Add subtitle to complex filter if needed
                if subtitle_filter:
                    complex_filter += "," + subtitle_filter
                
                cmd.extend(['-filter_complex', complex_filter])
                
            else:
                # Simple video filter chain
                all_video_filters = video_filters.copy()
                if subtitle_filter:
                    all_video_filters.append(subtitle_filter)
                
                if all_video_filters:
                    cmd.extend(['-vf', ",".join(all_video_filters)])
            
            # Audio filter
            if audio_filters:
                cmd.extend(['-af', ",".join(audio_filters)])
            elif not self.speed_change.get():
                cmd.extend(['-c:a', 'copy'])  # Copy audio without re-encoding if no speed change
            
            # Remove metadata if requested
            if self.remove_metadata.get():
                cmd.extend(['-map_metadata', '-1'])
                self.update_status(f"📝 Removing metadata from {os.path.basename(clip_path)}")
                
                # Add custom author metadata if enabled
                if self.add_custom_author.get():
                    author_name = self.custom_author_name.get().strip()
                    if author_name:
                        # Add custom metadata for author
                        cmd.extend(['-metadata', f'artist={author_name}'])
                        cmd.extend(['-metadata', f'author={author_name}'])
                        cmd.extend(['-metadata', f'creator={author_name}'])
                        cmd.extend(['-metadata', f'title=Created by {author_name}'])
                        self.update_status(f"👤 Adding custom author metadata: {author_name}")
                    else:
                        self.update_status("⚠️ Custom author name is empty, skipping custom metadata")
            
            # Get optimal encoding settings for MAXIMUM QUALITY preservation
            encoding_settings = self.get_video_encoding_settings()
            
            # ULTRA-HIGH QUALITY encoding for single pass
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', encoding_settings['preset'],
                '-crf', encoding_settings['crf'],
                '-pix_fmt', encoding_settings['pix_fmt']
            ])
            
            # Add profile and level for high quality
            if 'profile' in encoding_settings:
                cmd.extend(['-profile:v', encoding_settings['profile']])
            if 'level' in encoding_settings:
                cmd.extend(['-level', encoding_settings['level']])
                
            # Add movflags for optimal output
            if 'movflags' in encoding_settings:
                cmd.extend(['-movflags', encoding_settings['movflags']])
            else:
                cmd.extend(['-movflags', '+faststart'])
            
            cmd.extend(['-y', temp_path])
            
            # Execute single FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Replace original with processed version
                os.replace(temp_path, clip_path)
                
                # Clean up temporary SRT file if created
                if subtitle_filter and 'srt_path' in locals():
                    try:
                        os.remove(srt_path)
                    except:
                        pass
            else:
                # Clean up temp file if processing failed
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                self.update_status(f"⚠️ Warning: Single-pass processing failed for {os.path.basename(clip_path)}")
                
        except Exception as e:
            self.update_status(f"⚠️ Warning: Single-pass processing failed: {str(e)}")
            
    # DEPRECATED: This function is replaced by apply_single_pass_processing() for better quality
    # def apply_anticopyright_to_clips(self): - REMOVED (handled in single-pass processing)
        
    def apply_captions_to_clips(self):
        """Apply auto captions to all generated clips"""
        if not self.transcript or not self.clips_data:
            self.update_status("⚠️ No transcript or clips data available for captions")
            return
            
        # Debug: Check current style settings
        print(f"🎬 Starting caption application with style: {self.caption_style_preset.get()}")
        print(f"🎬 Auto caption enabled: {self.auto_caption.get()}")
        print(f"🎬 Caption position: {self.caption_style.get()}")
        print(f"🎬 Font size: {self.caption_font_size.get()}")
        
        total_clips = len(self.clips_data)
        
        for i, clip_info in enumerate(self.clips_data, 1):
            clip_path = clip_info['path']
            clip_name = clip_info['filename']
            start_time = clip_info['start_time']
            end_time = clip_info['end_time']
            
            self.update_status(f"📝 Adding captions to clip {i}/{total_clips}: {clip_name[:30]}...")
            
            # Generate SRT file for this clip
            srt_path = self.generate_srt_for_clip(start_time, end_time, clip_path)
            
            if srt_path:
                # Apply subtitle to video using FFmpeg
                self.apply_subtitle_to_video(clip_path, srt_path)
                
                # Clean up temporary SRT file
                try:
                    os.remove(srt_path)
                except:
                    pass
                    
        self.update_status(f"✅ Captions applied to {total_clips} clips!")
        
    def generate_srt_for_clip(self, clip_start, clip_end, clip_path):
        """Generate SRT subtitle file with NO OVERLAPPING and MAX 2 LINES"""
        try:
            self.update_status(f"📝 Generating clean subtitles for clip {clip_start:.1f}s - {clip_end:.1f}s")
            
            # Collect and process segments within clip timeframe
            valid_segments = []
            
            for segment in self.transcript['segments']:
                seg_start = segment['start']
                seg_end = segment['end']
                
                # Check if segment overlaps with clip timeframe
                if seg_start < clip_end and seg_end > clip_start:
                    # Adjust times relative to clip start (clip starts at 0)
                    adjusted_start = max(0, seg_start - clip_start)
                    adjusted_end = min(clip_end - clip_start, seg_end - clip_start)
                    
                    # Skip if adjusted time is invalid or too short
                    if adjusted_start >= adjusted_end or adjusted_end <= 0 or (adjusted_end - adjusted_start) < 0.3:
                        continue
                    
                    # Format and clean text
                    text = segment['text'].strip()
                    text = text.strip('.,!?;:')
                    
                    # Clean subtitle text to remove unwanted characters
                    text = self.clean_subtitle_text(text)
                    
                    # Skip empty or meaningless text
                    if not text or len(text) < 2 or text in ['...', '..', '.', ',', '!', '?']:
                        continue
                    
                    valid_segments.append({
                        'start': adjusted_start,
                        'end': adjusted_end,
                        'text': text
                    })
            
            if not valid_segments:
                self.update_status("⚠️ No valid segments found, trying fallback...")
                return self.generate_srt_fallback(clip_start, clip_end, clip_path)
            
            # PROCESS SEGMENTS: Remove overlaps and ensure proper timing
            processed_segments = self.process_subtitle_segments(valid_segments)
            
            # GENERATE SRT with max 2 lines per subtitle
            srt_content = ""
            subtitle_index = 1
            
            # Check if typewriter animation is enabled
            use_typewriter = self.caption_animation.get() == "typewriter"
            
            for segment in processed_segments:
                if use_typewriter:
                    # Generate typewriter effect segments
                    typewriter_segments = self.generate_typewriter_subtitle(
                        segment['text'], 
                        segment['start'], 
                        segment['end'] - segment['start']
                    )
                    
                    if typewriter_segments:
                        for tw_segment in typewriter_segments:
                            formatted_text = self.format_subtitle_text(tw_segment['text'])
                            start_srt = self.seconds_to_srt_time(tw_segment['start'])
                            end_srt = self.seconds_to_srt_time(tw_segment['end'])
                            
                            srt_content += f"{subtitle_index}\n"
                            srt_content += f"{start_srt} --> {end_srt}\n"
                            srt_content += f"{formatted_text}\n\n"
                            subtitle_index += 1
                    else:
                        # Fallback to normal subtitle if typewriter generation fails
                        formatted_text = self.format_subtitle_text(segment['text'])
                        start_srt = self.seconds_to_srt_time(segment['start'])
                        end_srt = self.seconds_to_srt_time(segment['end'])
                        
                        srt_content += f"{subtitle_index}\n"
                        srt_content += f"{start_srt} --> {end_srt}\n"
                        srt_content += f"{formatted_text}\n\n"
                        subtitle_index += 1
                else:
                    # Normal subtitle generation
                    formatted_text = self.format_subtitle_text(segment['text'])
                    start_srt = self.seconds_to_srt_time(segment['start'])
                    end_srt = self.seconds_to_srt_time(segment['end'])
                    
                    srt_content += f"{subtitle_index}\n"
                    srt_content += f"{start_srt} --> {end_srt}\n"
                    srt_content += f"{formatted_text}\n\n"
                    subtitle_index += 1
            
            self.update_status(f"✅ Generated {subtitle_index-1} clean subtitles (max 2 lines, no overlap)")
            
            # Save SRT file
            srt_path = clip_path.replace('.mp4', '.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
                
            return srt_path
            
        except Exception as e:
            self.update_status(f"⚠️ Warning: Failed to generate SRT for {os.path.basename(clip_path)}: {str(e)}")
            return None
    
    def process_subtitle_segments(self, segments):
        """Process segments to remove overlaps and ensure proper timing with gaps"""
        if not segments:
            return []
        
        # Sort segments by start time
        segments = sorted(segments, key=lambda x: x['start'])
        
        processed = []
        min_gap = 0.2  # Minimum 200ms gap between subtitles
        min_duration = 0.8  # Minimum 800ms duration per subtitle
        
        for i, segment in enumerate(segments):
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text']
            
            # Ensure minimum duration
            if (end_time - start_time) < min_duration:
                end_time = start_time + min_duration
            
            # Check overlap with previous subtitle
            if processed:
                prev_end = processed[-1]['end']
                
                # If there's overlap or insufficient gap
                if start_time < (prev_end + min_gap):
                    # Option 1: Adjust start time to create gap
                    new_start = prev_end + min_gap
                    
                    # Check if adjusted start is reasonable
                    if new_start < end_time:
                        start_time = new_start
                    else:
                        # Option 2: Skip this segment if adjustment makes it invalid
                        continue
            
            # Check overlap with next subtitle
            if i < len(segments) - 1:
                next_start = segments[i + 1]['start']
                
                # If current end overlaps with next start
                if end_time > (next_start - min_gap):
                    # Adjust end time to create gap
                    new_end = next_start - min_gap
                    
                    # Ensure minimum duration is maintained
                    if new_end > (start_time + min_duration):
                        end_time = new_end
                    else:
                        # Maintain minimum duration
                        end_time = start_time + min_duration
            
            processed.append({
                'start': start_time,
                'end': end_time,
                'text': text
            })
        
        return processed
            
    def format_subtitle_text(self, text):
        """Format text for subtitle display with MAX 2 LINES and optimal readability"""
        if not text:
            return ""
        
        # Clean up text - REMOVE ">>" and other unwanted characters
        text = text.strip()
        
        # Remove common unwanted characters and patterns
        text = re.sub(r'^>>\s*', '', text)  # Remove leading ">> "
        text = re.sub(r'\s*>>\s*', ' ', text)  # Remove any ">>" in middle
        text = re.sub(r'^\s*[>]{2,}\s*', '', text)  # Remove multiple ">" at start
        text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces
        
        # Remove other common subtitle artifacts
        text = re.sub(r'^[-_]\s*', '', text)  # Remove leading dashes/underscores
        text = re.sub(r'\s*[-_]\s*$', '', text)  # Remove trailing dashes/underscores
        text = re.sub(r'^\[.*?\]\s*', '', text)  # Remove [bracketed] content at start
        text = re.sub(r'\s*\[.*?\]\s*$', '', text)  # Remove [bracketed] content at end
        
        # Clean up any remaining artifacts
        text = re.sub(r'^\s*[>]\s*', '', text)  # Remove single ">" at start
        text = re.sub(r'\s*[>]\s*$', '', text)  # Remove single ">" at end
        text = re.sub(r'^\s*[>]{3,}\s*', '', text)  # Remove multiple ">" (3 or more)
        
        # Final cleanup
        text = text.strip()
        
        # Maximum characters per line for readability
        max_chars_per_line = 42
        max_lines = 2
        
        words = text.split()
        
        # If text is short enough for one line
        if len(text) <= max_chars_per_line:
            return text
        
        # Try to break into 2 lines optimally
        lines = []
        current_line = ""
        
        for word in words:
            # Check if adding word would exceed line limit
            test_line = current_line + (" " + word if current_line else word)
            
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                # Current line is full, start new line
                if current_line:
                    lines.append(current_line)
                    current_line = word
                    
                    # If we already have max lines, stop here
                    if len(lines) >= max_lines:
                        break
                else:
                    # Single word is too long, force it
                    current_line = word
        
        # Add remaining text to last line
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
        
        # Limit to max 2 lines
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            # If we cut off text, add ellipsis to last line
            if len(lines[max_lines-1]) > (max_chars_per_line - 3):
                lines[max_lines-1] = lines[max_lines-1][:(max_chars_per_line-3)] + "..."
        
        return "\n".join(lines)
    
    def clean_subtitle_text(self, text):
        """Clean subtitle text by removing unwanted characters and patterns"""
        if not text:
            return ""
        
        # Remove common unwanted characters and patterns
        text = re.sub(r'^>>\s*', '', text)  # Remove leading ">> "
        text = re.sub(r'\s*>>\s*', ' ', text)  # Remove any ">>" in middle
        text = re.sub(r'^\s*[>]{2,}\s*', '', text)  # Remove multiple ">" at start
        text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces
        
        # Remove other common subtitle artifacts
        text = re.sub(r'^[-_]\s*', '', text)  # Remove leading dashes/underscores
        text = re.sub(r'\s*[-_]\s*$', '', text)  # Remove trailing dashes/underscores
        text = re.sub(r'^\[.*?\]\s*', '', text)  # Remove [bracketed] content at start
        text = re.sub(r'\s*\[.*?\]\s*$', '', text)  # Remove [bracketed] content at end
        
        # Clean up any remaining artifacts
        text = re.sub(r'^\s*[>]\s*', '', text)  # Remove single ">" at start
        text = re.sub(r'\s*[>]\s*$', '', text)  # Remove single ">" at end
        text = re.sub(r'^\s*[>]{3,}\s*', '', text)  # Remove multiple ">" (3 or more)
        
        # Remove other common subtitle artifacts
        text = re.sub(r'^\(.*?\)\s*', '', text)  # Remove (parenthesized) content at start
        text = re.sub(r'\s*\(.*?\)\s*$', '', text)  # Remove (parenthesized) content at end
        text = re.sub(r'^\{.*?\}\s*', '', text)  # Remove {braced} content at start
        text = re.sub(r'\s*\{.*?\}\s*$', '', text)  # Remove {braced} content at end
        
        # Remove speaker indicators and timestamps
        text = re.sub(r'^[A-Z][a-z]*:\s*', '', text)  # Remove "Speaker:" at start
        text = re.sub(r'^\d+:\d+\s*', '', text)  # Remove "1:23" at start
        text = re.sub(r'^\d+\.\d+\s*', '', text)  # Remove "1.23" at start
        
        # Final cleanup
        text = text.strip()
        
        return text
    
    def get_global_font_size(self):
        """Get global font size for all subtitle styles - SIMPLIFIED GLOBAL FONT SIZE"""
        return int(self.caption_font_size.get())
    
    def apply_global_font_size(self, style_config):
        """Apply global font size to style configuration - FIXED GLOBAL FONT SIZE"""
        global_size = self.get_global_font_size()
        
        # Override all font sizes with global size
        if 'font_size' in style_config:
            style_config['font_size'] = global_size
        
        return style_config
    
    def test_subtitle_text_cleaning(self):
        """Test function to verify subtitle text cleaning works correctly"""
        test_cases = [
            ">> Oh, pendeta timbul",
            ">> >> Multiple arrows",
            ">>> Triple arrows",
            "- Leading dash",
            "_ Leading underscore",
            "[Music] Background music",
            "(Applause) Audience reaction",
            "{Sound effect}",
            "Speaker: Hello world",
            "1:23 Timestamp",
            "1.45 Another timestamp",
            ">> >> >> Multiple arrows with spaces",
            "Normal text without artifacts",
            "Text with >> in the middle >> here",
            ">> Text with trailing >>",
            ">> >> >> >> Multiple arrows at start",
        ]
        
        print("🧪 Testing Subtitle Text Cleaning:")
        print("=" * 50)
        
        for test_text in test_cases:
            cleaned = self.clean_subtitle_text(test_text)
            print(f"Original: '{test_text}'")
            print(f"Cleaned:  '{cleaned}'")
            print("-" * 30)
        
        print("✅ Subtitle text cleaning test completed!")
    
    def generate_srt_fallback(self, clip_start, clip_end, clip_path):
        """Fallback SRT generation with MAX 2 LINES and NO OVERLAP"""
        try:
            # Get the full transcript text for the time range
            full_text = self.transcript.get('text', '')
            
            if not full_text:
                return None
            
            clip_duration = clip_end - clip_start
            
            # Split text into smaller, manageable chunks for better subtitle flow
            words = full_text.split()
            
            # Calculate optimal chunk size for subtitle timing (aim for 2-3 second subtitles)
            target_subtitle_duration = 2.5  # seconds
            total_subtitles = max(1, int(clip_duration / target_subtitle_duration))
            words_per_subtitle = max(3, len(words) // total_subtitles)
            
            segments = []
            
            for i in range(0, len(words), words_per_subtitle):
                chunk_words = words[i:i + words_per_subtitle]
                text = " ".join(chunk_words)
                
                # Clean subtitle text to remove unwanted characters
                text = self.clean_subtitle_text(text)
                
                # Calculate timing for this chunk with proper gaps
                start_time = (i / len(words)) * clip_duration
                end_time = min(((i + words_per_subtitle) / len(words)) * clip_duration, clip_duration)
                
                # Ensure minimum duration and gap
                min_duration = 0.8
                if (end_time - start_time) < min_duration:
                    end_time = min(start_time + min_duration, clip_duration)
                
                if end_time > start_time:
                    segments.append({
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    })
            
            # Process segments to remove overlaps (use same logic as main function)
            processed_segments = self.process_subtitle_segments(segments)
            
            if not processed_segments:
                return None
            
            # Generate SRT with max 2 lines formatting
            srt_content = ""
            subtitle_index = 1
            
            for segment in processed_segments:
                # Format text for MAX 2 LINES
                formatted_text = self.format_subtitle_text(segment['text'])
                
                start_srt = self.seconds_to_srt_time(segment['start'])
                end_srt = self.seconds_to_srt_time(segment['end'])
                
                srt_content += f"{subtitle_index}\n"
                srt_content += f"{start_srt} --> {end_srt}\n"
                srt_content += f"{formatted_text}\n\n"
                subtitle_index += 1
            
            if srt_content:
                srt_path = clip_path.replace('.mp4', '.srt')
                with open(srt_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                
                self.update_status(f"✅ Fallback: Generated {subtitle_index-1} clean subtitles (max 2 lines)")
                return srt_path
                
            return None
            
        except Exception as e:
            self.update_status(f"⚠️ Fallback SRT generation failed: {str(e)}")
            return None
            
    def seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
        
    def apply_subtitle_to_video(self, video_path, srt_path):
        """Apply subtitle overlay to video using FFmpeg"""
        try:
            # Debug: Check if SRT file exists and has content
            if not os.path.exists(srt_path):
                self.update_status(f"⚠️ SRT file not found: {srt_path}")
                return
                
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
                self.update_status(f"🔍 SRT file size: {len(srt_content)} chars")
                print(f"SRT Content:\n{srt_content[:300]}...")
            
            # Create temporary output file
            temp_path = video_path.replace('.mp4', '_with_subs.mp4')
            
            # Get caption position and style configuration
            position = self.caption_style.get()
            style_config = self.get_caption_style_preset()
            
            # Validate style config
            if not style_config:
                print("⚠️ Style config is empty, using default")
                style_config = {
                    "font_size": int(self.caption_font_size.get()),
                    "color": "&H00FFFFFF",  # Correct ASS format: AABBGGRR
                    "outline_color": "&H00000000",  # Correct ASS format: AABBGGRR
                    "outline_width": "2",
                    "background": False,
                    "background_color": "&H80000000",  # Correct ASS format: AABBGGRR
                    "font_weight": "normal",
                    "font_style": "normal"
                }
            
            print(f"🎬 Applying subtitle with style: {self.caption_style_preset.get()}")
            print(f"🎬 Style config: {style_config}")
            
            # Apply GLOBAL FONT SIZE - Fixed global font size for all styles
            style_config = self.apply_global_font_size(style_config)
            base_font_size = style_config["font_size"]
            font_size = self.get_adjusted_font_size(base_font_size)
            
            print(f"🎬 Font size - Base: {base_font_size}, Adjusted: {font_size}")
            
            # Get margins based on aspect ratio
            margin_v, margin_h = self.get_subtitle_margins()
            
            # Build style string from configuration
            style_parts = [
                f"Fontsize={font_size}",
                f"PrimaryColour={style_config.get('color', '&Hffffff')}",
                f"OutlineColour={style_config.get('outline_color', '&H000000')}",
                f"Outline={style_config.get('outline_width', '2')}"
            ]
            
            # Apply style consistently from the style preset configuration
            # Add background if enabled in the style preset
            if style_config.get('background', False):
                style_parts.append(f"BackColour={style_config.get('background_color', '&H80000000')}")
            
            # Add font weight from style preset
            if style_config.get('font_weight') == 'bold':
                style_parts.append("Bold=1")
            
            # Add font style from style preset
            if style_config.get('font_style') == 'italic':
                style_parts.append("Italic=1")
            
            # Note: All style properties are now consistently applied from the style preset
            
            print(f"🎬 Style parts: {style_parts}")
            
            # Add alignment based on position
            if position == "bottom":
                alignment = "2"
            elif position == "top":
                alignment = "8"
            else:  # center
                alignment = "5"
            style_parts.append(f"Alignment={alignment}")
            
            print(f"🎬 Position: {position}, Alignment: {alignment}")
            
            # Add margins
            style_parts.append(f"MarginV={margin_v}")
            if self.convert_to_portrait.get() and "9:16" in self.aspect_ratio.get():
                style_parts.extend(["MarginL=10", "MarginR=10"])
            
            # Combine style parts
            style_string = ",".join(style_parts)
            
            # Debug: Log the final style configuration
            print(f"🎬 Final style configuration:")
            print(f"   - Preset: {self.caption_style_preset.get()}")
            print(f"   - Font size: {font_size}px (base: {base_font_size}px)")
            print(f"   - Position: {position} (alignment: {alignment})")
            print(f"   - Margins: V={margin_v}, H={margin_h}")
            print(f"   - Style string: {style_string}")
            
            print(f"🎬 Final style string: {style_string}")
            self.update_status(f"🔍 Using style: {self.caption_style_preset.get()}, font size: {font_size}px, position: {position}")
            
            # Escape the SRT path for Windows compatibility
            srt_path_escaped = srt_path.replace('\\', '\\\\\\\\').replace(':', '\\\\:')
            
            # Build subtitle filter with custom style
            subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='{style_string}'"
            
            print(f"🎬 Subtitle filter: {subtitle_filter}")
            
            # Get optimal encoding settings for subtitle overlay
            encoding_settings = self.get_video_encoding_settings()
            
            # FFmpeg command to add subtitles with quality preservation
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', subtitle_filter,
                '-c:v', 'libx264',
                '-preset', encoding_settings['preset'],
                '-crf', encoding_settings['crf'],
                '-pix_fmt', encoding_settings['pix_fmt'],
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-y', temp_path
            ]
            
            # Add profile and level for high quality
            if 'profile' in encoding_settings:
                cmd.extend(['-profile:v', encoding_settings['profile']])
            if 'level' in encoding_settings:
                cmd.extend(['-level', encoding_settings['level']])
            
            # Debug: Print FFmpeg command
            self.update_status(f"🔍 Running FFmpeg subtitle command...")
            print(f"FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Debug: Print FFmpeg output
            if result.stderr:
                print(f"FFmpeg stderr: {result.stderr}")
            if result.stdout:
                print(f"FFmpeg stdout: {result.stdout}")
            
            if result.returncode == 0:
                # Replace original with subtitled version
                os.replace(temp_path, video_path)
                self.update_status(f"✅ Subtitles successfully added to {os.path.basename(video_path)}")
            else:
                # Clean up temp file if processing failed
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                self.update_status(f"⚠️ Warning: Subtitle overlay failed for {os.path.basename(video_path)}")
                self.update_status(f"⚠️ FFmpeg error: {result.stderr[:200]}...")
                
        except Exception as e:
            self.update_status(f"⚠️ Warning: Subtitle processing failed for {os.path.basename(video_path)}: {str(e)}")
            
    def get_adjusted_font_size(self, base_font_size):
        """Adjust font size based on aspect ratio and caption style for social media formats"""
        if not self.convert_to_portrait.get():
            return base_font_size
            
        # Get aspect ratio
        ratio_text = self.aspect_ratio.get()
        
        # Get caption style preset for font size adjustment
        preset = self.caption_style_preset.get()
        
        # Base scaling based on aspect ratio
        if "9:16" in ratio_text:
            # Portrait format - reduce font size more aggressively (40% reduction)
            scale_factor = 0.6
        elif "4:5" in ratio_text:
            # Instagram format - reduce font size by 30%
            scale_factor = 0.7
        elif "1:1" in ratio_text:
            # Square format - reduce font size by 20%
            scale_factor = 0.8
        else:
            # Landscape or unknown - keep original size
            scale_factor = 1.0
        
        # Additional adjustment based on caption style preset
        if preset == "bold":
            # Bold style can be slightly smaller due to weight
            scale_factor *= 0.95
        elif preset == "neon":
            # Neon style with glow effect should be slightly larger
            scale_factor *= 1.05
        elif preset == "glow":
            # Glow style with thick outline should be slightly larger
            scale_factor *= 1.08
        elif preset == "minimal":
            # Minimal style can be slightly larger due to clean appearance
            scale_factor *= 1.02
        elif preset == "elegant":
            # Elegant style with italic can be slightly smaller
            scale_factor *= 0.98
        
        # Apply scaling and ensure minimum size
        adjusted_size = int(base_font_size * scale_factor)
        
        # Set minimum sizes based on style preset
        if preset == "bold":
            min_size = 14
        elif preset == "neon" or preset == "glow":
            min_size = 16
        elif preset == "minimal":
            min_size = 12
        else:
            min_size = 12
        
        return max(min_size, adjusted_size)
            
    def get_subtitle_margins(self):
        """Get subtitle margins based on aspect ratio and caption style"""
        if not self.convert_to_portrait.get():
            return 30, 20  # Default margins for landscape
            
        # Get aspect ratio
        ratio_text = self.aspect_ratio.get()
        
        # Get caption style preset for margin adjustment
        preset = self.caption_style_preset.get()
        
        # Base margins based on aspect ratio
        if "9:16" in ratio_text:
            # Portrait format - larger margins to avoid clipping
            base_margin_v, base_margin_h = 50, 30
        elif "4:5" in ratio_text:
            # Instagram format - medium margins
            base_margin_v, base_margin_h = 40, 25
        elif "1:1" in ratio_text:
            # Square format - standard margins
            base_margin_v, base_margin_h = 35, 20
        else:
            # Landscape format - standard margins
            base_margin_v, base_margin_h = 30, 20
        
        # Adjust margins based on caption style preset
        if preset == "bold":
            # Bold style needs more space
            base_margin_v += 10
            base_margin_h += 5
        elif preset == "neon":
            # Neon style with glow effect needs more space
            base_margin_v += 15
            base_margin_h += 8
        elif preset == "glow":
            # Glow style needs more space for outline
            base_margin_v += 12
            base_margin_h += 6
        elif preset == "minimal":
            # Minimal style can use tighter margins
            base_margin_v = max(20, base_margin_v - 5)
            base_margin_h = max(15, base_margin_h - 3)
        
        return base_margin_v, base_margin_h
    
    def get_aspect_ratio_filter(self):
        """Get FFmpeg filter for aspect ratio conversion to social media formats with CROP or FIT mode"""
        if not self.convert_to_portrait.get():
            return None
            
        ratio_text = self.aspect_ratio.get()
        target_res = self.target_resolution.get()
        crop_mode = self.aspect_crop_mode.get()
        
        # Get optimal dimensions based on target resolution
        if "4K" in target_res:
            base_width, base_height = 2160, 3840  # 4K Portrait
        elif "1080p" in target_res:
            base_width, base_height = 1080, 1920  # 1080p Portrait
        else:
            base_width, base_height = 720, 1280   # 720p Portrait
        
        # Determine if using crop mode or fit mode
        is_crop_mode = "crop" in crop_mode.lower()
        
        if "9:16" in ratio_text:
            # YouTube Shorts/Reels - Portrait 9:16
            width, height = base_width, int(base_width * 16 / 9)
            if is_crop_mode:
                # CROP MODE: Cut video to exact ratio
                return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}:(iw-ow)/2:(ih-oh)/2"
            else:
                # FIT MODE: Add black bars (original behavior)
                return f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
            
        elif "4:5" in ratio_text:
            # Instagram format - 4:5
            width, height = base_width, int(base_width * 5 / 4)
            if is_crop_mode:
                return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}:(iw-ow)/2:(ih-oh)/2"
            else:
                return f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
            
        elif "1:1" in ratio_text:
            # Square format - 1:1
            size = base_width
            if is_crop_mode:
                return f"scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size}:(iw-ow)/2:(ih-oh)/2"
            else:
                return f"scale={size}:{size}:force_original_aspect_ratio=decrease,pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:black"
            
        elif "16:9" in ratio_text:
            # Landscape format - 16:9
            width, height = int(base_height * 16 / 9), base_height
            if is_crop_mode:
                return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}:(iw-ow)/2:(ih-oh)/2"
            else:
                return f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
        else:
            # Default to 9:16 if no match
            width, height = base_width, int(base_width * 16 / 9)
            if is_crop_mode:
                return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}:(iw-ow)/2:(ih-oh)/2"
            else:
                return f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    
    def on_portrait_toggle(self):
        """Toggle portrait format options"""
        if self.convert_to_portrait.get():
            if hasattr(self, 'aspect_combo'):
                self.aspect_combo.configure(state='readonly')
            if hasattr(self, 'ratio_combo'):
                self.ratio_combo.configure(state='readonly')
            if hasattr(self, 'crop_mode_combo'):
                self.crop_mode_combo.configure(state='readonly')
            if hasattr(self, 'crop_mode_combo_compact'):
                self.crop_mode_combo_compact.configure(state='readonly')
        else:
            if hasattr(self, 'aspect_combo'):
                self.aspect_combo.configure(state='disabled')
            if hasattr(self, 'ratio_combo'):
                self.ratio_combo.configure(state='disabled')
            if hasattr(self, 'crop_mode_combo'):
                self.crop_mode_combo.configure(state='disabled')
            if hasattr(self, 'crop_mode_combo_compact'):
                self.crop_mode_combo_compact.configure(state='disabled')
        
        # Update caption preview to reflect aspect ratio changes
        self.root.after(300, self.update_caption_preview_settings)
                
    def on_watermark_toggle(self):
        """Toggle watermark settings visibility"""
        if self.add_watermark.get():
            if hasattr(self, 'watermark_settings'):
                self.watermark_settings.pack(fill='x', pady=(5, 0))
        else:
            if hasattr(self, 'watermark_settings'):
                self.watermark_settings.pack_forget()
                
    def browse_watermark_file(self):
        """Browse for watermark PNG file"""
        file_path = filedialog.askopenfilename(
            title="Select PNG Logo for Watermark",
            filetypes=[
                ("PNG files", "*.png"),
                ("All image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.watermark_file.set(file_path)
            
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(initialdir=self.output_folder.get())
        if folder:
            self.output_folder.set(folder)
        
    # DEPRECATED: This function is replaced by apply_single_pass_to_clip() for better quality and efficiency
    # def apply_clip_anticopyright_features(self, clip_path): - REMOVED (handled in single-pass processing)
    

            
    def show_results(self):
        """Show clipping results in the UI"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        if not self.clips_data:
            return
            
        # Results header
        ttk.Label(self.results_frame, text="🎬 AI Clipping Results", 
                 style='AITitle.TLabel').pack(anchor='w', pady=(0, 10))
        
        # Anti-copyright features summary
        features_applied = []
        if self.remove_metadata.get(): features_applied.append("📝 Metadata removed")
        if self.mirror_video.get(): features_applied.append("🪞 Mirror")
        if self.speed_change.get(): features_applied.append("⚡ Speed 0.95x")
        if self.brightness_change.get(): features_applied.append("🌟 Brightness")
        if self.crop_video.get(): features_applied.append("✂️ Crop")
        if self.add_watermark.get(): 
            watermark_file = self.watermark_file.get().strip()
            if watermark_file and os.path.exists(watermark_file):
                watermark_name = os.path.basename(watermark_file)
                features_applied.append(f"💧 Watermark ({watermark_name} • {self.watermark_position.get()} • {self.watermark_size.get()})")
            else:
                features_applied.append("💧 Watermark (text fallback)")
        if self.auto_caption.get(): features_applied.append(f"📝 Auto Caption ({self.caption_style.get()})")
        
        # Add enhanced video quality info
        quality_parts = [f"{self.video_quality.get().title()}"]
        quality_parts.append(f"CRF {self.video_crf.get()}")
        
        target_res = self.target_resolution.get()
        if target_res != "original":
            quality_parts.append(target_res)
            
        if self.social_optimized.get():
            quality_parts.append("Social Optimized")
            
        quality_info = f"🎥 Quality: {' • '.join(quality_parts)}"
        features_applied.append(quality_info)
        
        # Add platform info
        if hasattr(self, 'video_platform') and self.video_platform:
            platform_info = f"🌐 Source: {self.video_platform}"
            features_applied.append(platform_info)
            
        if self.convert_to_portrait.get(): 
            ratio_text = self.aspect_ratio.get().split(" ")[0]  # Get just the ratio part
            # Add resolution info for social media format
            if target_res != "original" and self.social_optimized.get():
                width, height = self.get_target_dimensions(self.aspect_ratio.get(), target_res)
                format_info = f"📐 {ratio_text} • {width}x{height}px"
            else:
                format_info = f"📐 {ratio_text} format"
            features_applied.append(format_info)
        
        if features_applied:
            features_text = f"🛡️ Anti-copyright applied: {', '.join(features_applied)}"
            ttk.Label(self.results_frame, text=features_text, style='AI.TLabel',
                     foreground=self.colors['accent_ai']).pack(anchor='w', pady=(0, 10))
        
        # ENHANCED: Show quality overview
        if self.clips_data:
            avg_quality = sum(clip.get('quality_score', 0) for clip in self.clips_data) / len(self.clips_data)
            clips_improved = sum(1 for clip in self.clips_data if clip.get('boundary_improved'))
            clips_fallback = sum(1 for clip in self.clips_data if clip.get('fallback_generated'))
            
            quality_text = f"🎯 Quality Overview: Rata-rata {avg_quality:.1f}/10"
            if clips_improved > 0:
                quality_text += f" • {clips_improved} boundary improved"
            if clips_fallback > 0:
                quality_text += f" • {clips_fallback} fallback generated"
                
            ttk.Label(self.results_frame, text=quality_text, style='AI.TLabel',
                     foreground=self.colors['accent_ai']).pack(anchor='w', pady=(0, 10))
        
        # Clips list
        for i, clip in enumerate(self.clips_data, 1):
            clip_frame = ttk.Frame(self.results_frame, style='AICard.TFrame')
            clip_frame.pack(fill='x', pady=5, padx=10)
            
            # Enhanced clip info with quality score
            title = f"🎬 {clip['title']}"
            duration = f"⏱️ {clip['duration']:.1f}s"
            emotion = f"❤️ {clip['emotion_score']}/10"
            quality = f"🌟 {clip.get('quality_score', 0):.1f}/10"
            confidence = f"🎯 {clip.get('boundary_confidence', 'unknown')}"
            
            info_text = f"{title} | {duration} | {emotion} | {quality} | {confidence}"
            ttk.Label(clip_frame, text=info_text, style='AI.TLabel').pack(anchor='w')
            
            reason_text = f"💡 {clip['reason']}"
            ttk.Label(clip_frame, text=reason_text, style='AI.TLabel',
                     foreground=self.colors['text_secondary']).pack(anchor='w', padx=(20, 0))
            
            # Show boundary improvement info
            if clip.get('boundary_improved'):
                improved_text = "✨ Boundary improved oleh AI untuk content completeness"
                ttk.Label(clip_frame, text=improved_text, style='AI.TLabel',
                         foreground=self.colors['accent_ai']).pack(anchor='w', padx=(20, 0))
                         
            if clip.get('fallback_generated'):
                fallback_text = "🔄 Clip dibuat dengan fallback strategy (AI analysis gagal)"
                ttk.Label(clip_frame, text=fallback_text, style='AI.TLabel',
                         foreground=self.colors['warning']).pack(anchor='w', padx=(20, 0))
                         
            # Show boundary suggestions if available
            if clip.get('boundary_suggestions'):
                suggestions = clip['boundary_suggestions']
                if suggestions != "✅ Boundary sudah optimal!":
                    suggestions_text = f"💡 Saran: {suggestions[:100]}..."
                    ttk.Label(clip_frame, text=suggestions_text, style='AI.TLabel',
                             foreground=self.colors['text_secondary']).pack(anchor='w', padx=(20, 0))
            
            # Add boundary preview button
            preview_button = ttk.Button(clip_frame, text="🔍 Preview Boundary", 
                                      command=lambda c=clip: self.show_boundary_preview(c),
                                      style='AIButton.TButton')
            preview_button.pack(anchor='w', padx=(20, 0), pady=(5, 0))
        
                # Open folder button
        ttk.Button(self.results_frame, text="🗂️ Buka Folder Clips", 
                  command=self.open_clips_folder, style='AIButton.TButton').pack(pady=10)
    
    def show_boundary_preview(self, clip_info):
        """Show detailed boundary preview in a new window"""
        # Create new window for boundary preview
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"🔍 Boundary Preview: {clip_info['title']}")
        preview_window.geometry("800x600")
        preview_window.resizable(True, True)
        
        # Make window modal
        preview_window.transient(self.root)
        preview_window.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(preview_window)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_text = f"🎬 {clip_info['title']} - Boundary Analysis"
        ttk.Label(main_frame, text=header_text, style='AITitle.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Basic info
        info_frame = ttk.LabelFrame(main_frame, text="📊 Clip Information", padding=10)
        info_frame.pack(fill='x', pady=(0, 20))
        
        info_text = f"""
⏱️ Durasi: {clip_info['duration']:.1f} detik
🎯 Emotion Score: {clip_info['emotion_score']}/10
🌟 Quality Score: {clip_info.get('quality_score', 0):.1f}/10
🎯 Confidence: {clip_info.get('boundary_confidence', 'unknown')}
📍 Start Time: {clip_info['start_time']:.1f}s
📍 End Time: {clip_info['end_time']:.1f}s
💡 Reason: {clip_info['reason']}
        """
        ttk.Label(info_frame, text=info_text, style='AI.TLabel').pack(anchor='w')
        
        # Boundary quality analysis
        quality_frame = ttk.LabelFrame(main_frame, text="🔍 Boundary Quality Analysis", padding=10)
        quality_frame.pack(fill='x', pady=(0, 20))
        
        # Get boundary preview
        boundary_preview = self.preview_clip_boundaries(clip_info)
        preview_text = tk.Text(quality_frame, height=15, wrap='word', font=self.get_system_font(9))
        preview_text.pack(fill='both', expand=True)
        preview_text.insert('1.0', boundary_preview)
        preview_text.config(state='disabled')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(quality_frame, orient='vertical', command=preview_text.yview)
        scrollbar.pack(side='right', fill='y')
        preview_text.config(yscrollcommand=scrollbar.set)
        
        # Boundary improvement suggestions
        if clip_info.get('boundary_suggestions'):
            suggestions_frame = ttk.LabelFrame(main_frame, text="💡 Improvement Suggestions", padding=10)
            suggestions_frame.pack(fill='x', pady=(0, 20))
            
            suggestions_text = tk.Text(suggestions_frame, height=6, wrap='word', font=self.get_system_font(9))
            suggestions_text.pack(fill='both', expand=True)
            suggestions_text.insert('1.0', clip_info['boundary_suggestions'])
            suggestions_text.config(state='disabled')
            
            # Add scrollbar
            suggestions_scrollbar = ttk.Scrollbar(suggestions_frame, orient='vertical', command=suggestions_text.yview)
            suggestions_scrollbar.pack(side='right', fill='y')
            suggestions_text.config(yscrollcommand=suggestions_scrollbar.set)
        
        # Close button
        ttk.Button(main_frame, text="✅ Tutup", 
                  command=preview_window.destroy, style='AIButton.TButton').pack(pady=10)
        
        # Center window on screen
        preview_window.update_idletasks()
        x = (preview_window.winfo_screenwidth() // 2) - (preview_window.winfo_width() // 2)
        y = (preview_window.winfo_screenheight() // 2) - (preview_window.winfo_height() // 2)
        preview_window.geometry(f"+{x}+{y}")
    
    def open_clips_folder(self):
        """Open the clips output folder (cross-platform)"""
        folder_path = self.download_path.get()
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', folder_path], check=True)
            else:  # Linux and other Unix-like systems
                subprocess.run(['xdg-open', folder_path], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            # Fallback: just show a message with the path
            messagebox.showinfo("📁 Folder Location", 
                              f"Clips saved to:\n{folder_path}\n\nPlease open this folder manually.")
            
    def show_error(self, error_msg):
        """Show error message"""
        messagebox.showerror("❌ Error", error_msg)
        
    def reset_ui(self):
        """Reset UI after processing"""
        self.progress.stop()
        self.start_btn.config(state="normal")
        
        # Cleanup temp files
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
            
            
    def start_clipping(self):
        """Start the AI auto clipping process"""
        if not self.validate_inputs():
            return
            
        # Clear log for new clipping session
        self.clear_log()
        
        # Add starting message
        self.add_log_message("🚀 Starting new AI Auto Clipping session...\n", color='accent_ai')
        self.add_log_message(f"📹 Source: {self.video_url.get()}\n")
        self.add_log_message(f"🎯 Model: {self.model_choice.get()}\n")
        self.add_log_message("=" * 50 + "\n\n")
            
        # Disable button during processing
        self.process_btn.configure(state='disabled')
        self.progress.configure(mode='indeterminate')
        self.progress.start()
        
        # Run in separate thread
        threading.Thread(target=self.process_video, daemon=True).start()
        

        
    def process_video(self):
        """Main video processing pipeline"""
        try:
            self.update_status("🎬 Starting AI video analysis...")
            
            # Create temp directory
            self.temp_dir = tempfile.mkdtemp(prefix="ai_clipper_")
            
            # Download video
            platform = self.detected_platform.get() or "platform yang dipilih"
            self.update_status(f"📥 Downloading video from {platform}...")
            self.download_video()
            
            # Extract audio and transcript
            self.update_status("🎵 Extracting audio and generating transcript...")
            self.extract_audio_and_transcript()
            
            # AI analysis
            self.update_status("🤖 Analyzing with Gemini AI...")
            self.analyze_with_gemini()
            
            # Generate clips
            self.update_status("✂️ Generating clips...")
            self.generate_clips()
            
            # NOTE: Anti-copyright features are now handled in single-pass processing during generate_clips()
            # No additional post-processing needed - everything is done in one efficient pass
            
            # Complete
            self.clip_generation_complete()
            
        except Exception as e:
            self.clip_generation_failed(str(e))
        finally:
            # Cleanup
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                import shutil
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
                    

            
    def clear_log(self):
        """Clear the log area"""
        if hasattr(self, 'results_text'):
            self.results_text.configure(state='normal')
            self.results_text.delete('1.0', 'end')
            self.results_text.configure(state='disabled')
            
    def clear_log_manual(self):
        """Clear log manually with confirmation and helpful message"""
        self.clear_log()
        self.add_log_message("🗑️ Log cleared manually\n\n", color='text_secondary')
        self.add_log_message("🤖 AI Auto Clipper Ready\n\n", color='accent_ai')
        self.add_log_message("💡 Ready for new clipping session:\n", color='text_primary')
        self.add_log_message("• Paste your video URL\n", color='text_secondary')
        self.add_log_message("• Configure AI settings\n", color='text_secondary')
        self.add_log_message("• Click 'Start AI Auto Clipping'\n\n", color='text_secondary')
            
    def add_log_message(self, message, color='text_primary'):
        """Add a message to the log with optional color"""
        if not hasattr(self, 'results_text'):
            return
            
        self.results_text.configure(state='normal')
        
        # Configure color tags if not already done
        if not hasattr(self, '_log_tags_configured'):
            self.results_text.tag_configure('accent_ai', foreground=self.colors['accent_ai'], font=self.get_system_font(11, 'bold'))
            self.results_text.tag_configure('accent_success', foreground=self.colors['accent_success'], font=self.get_system_font(11, 'bold'))
            self.results_text.tag_configure('accent_warning', foreground='#ff9900', font=self.get_system_font(11, 'bold'))
            self.results_text.tag_configure('accent_error', foreground='#ff4444', font=self.get_system_font(11, 'bold'))
            self.results_text.tag_configure('text_primary', foreground=self.colors['text_primary'])
            self.results_text.tag_configure('text_secondary', foreground=self.colors['text_secondary'])
            self._log_tags_configured = True
        
        # Insert message with color
        if color in ['accent_ai', 'accent_success', 'accent_warning', 'accent_error', 'text_primary', 'text_secondary']:
            self.results_text.insert('end', message, color)
        else:
            self.results_text.insert('end', message)
            
        # Auto-scroll to bottom
        self.results_text.see('end')
        self.results_text.configure(state='disabled')
        self.root.update_idletasks()
            
    def clip_generation_complete(self):
        """Handle successful completion"""
        self.progress.stop()
        self.progress.configure(mode='determinate', value=100)
        self.process_btn.configure(state='normal')
        
        # Add completion messages to log
        self.add_log_message("\n" + "=" * 50 + "\n", color='accent_success')
        self.add_log_message("✅ AI Auto Clipping Complete!\n", color='accent_success')
        self.add_log_message("=" * 50 + "\n\n", color='accent_success')
        
        self.add_log_message(f"📊 Generated {len(self.clips_data)} clips\n", color='text_primary')
        self.add_log_message(f"📁 Output folder: {self.output_folder.get()}\n\n", color='text_secondary')
        
        # Anti-copyright features summary
        features_applied = []
        if self.remove_metadata.get(): features_applied.append("📝 Metadata removed")
        if self.mirror_video.get(): features_applied.append("🪞 Mirror")
        if self.speed_change.get(): features_applied.append("⚡ Speed 0.95x")
        if self.brightness_change.get(): features_applied.append("🌟 Brightness")
        if self.crop_video.get(): features_applied.append("✂️ Crop")
        if self.add_watermark.get(): 
            watermark_file = self.watermark_file.get().strip()
            if watermark_file and os.path.exists(watermark_file):
                watermark_name = os.path.basename(watermark_file)
                features_applied.append(f"💧 Watermark ({watermark_name} • {self.watermark_position.get()} • {self.watermark_size.get()})")
            else:
                features_applied.append("💧 Watermark (text fallback)")
        if self.auto_caption.get(): features_applied.append(f"📝 Auto Caption ({self.caption_style.get()})")
        
        if features_applied:
            self.add_log_message(f"✅ Anti-copyright features applied to {len(self.clips_data)} clips!\n", color='accent_success')
            for feature in features_applied:
                self.add_log_message(f"   • {feature}\n", color='text_secondary')
            self.add_log_message("\n")
        
        # Clips details
        self.add_log_message("🎬 Generated Clips:\n", color='accent_ai')
        for i, clip in enumerate(self.clips_data, 1):
            title = clip.get('title', 'Untitled')
            duration = clip.get('duration', 0)
            score = clip.get('emotion_score', 0)
            
            self.add_log_message(f"{i}. {title}\n", color='text_primary')
            self.add_log_message(f"   ⏱️ Duration: {duration:.1f}s | 🎯 Score: {score}/10\n", color='text_secondary')
            
            # Add reason if available
            if 'reason' in clip:
                self.add_log_message(f"   💡 {clip['reason']}\n", color='text_secondary')
            self.add_log_message("\n")
        
        # Open output folder
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.output_folder.get())
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', self.output_folder.get()], check=True)
            else:  # Linux and other Unix-like systems
                subprocess.run(['xdg-open', self.output_folder.get()], check=True)
                
            self.add_log_message("📂 Output folder opened successfully!\n", color='accent_success')
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            # Fallback: show folder path in message
            self.add_log_message("⚠️ Could not open folder automatically\n", color='accent_warning')
            messagebox.showinfo("📁 Output Folder", 
                              f"Clips saved to:\n{self.output_folder.get()}")
            
        messagebox.showinfo("✅ Complete", f"AI Auto Clipping complete!\n{len(self.clips_data)} clips generated.")
        
    def clip_generation_failed(self, error_message):
        """Handle processing failure"""
        self.progress.stop()
        self.progress.configure(mode='determinate', value=0)
        self.process_btn.configure(state='normal')
        
        # Add error messages to log (without clearing previous logs for debugging)
        self.add_log_message("\n" + "=" * 50 + "\n", color='accent_error')
        self.add_log_message("❌ AI Auto Clipping Failed!\n", color='accent_error')
        self.add_log_message("=" * 50 + "\n\n", color='accent_error')
        
        self.add_log_message(f"🔴 Error Details:\n", color='accent_error')
        self.add_log_message(f"{error_message}\n\n", color='text_primary')
        
        self.add_log_message("🔧 Troubleshooting Tips:\n", color='accent_warning')
        tips = [
            "• Check your internet connection",
            "• Verify Gemini API key is valid",
            "• Ensure the video URL is accessible",
            "• Try a different video or shorter duration",
            "• Check if FFmpeg is properly installed",
            "• Check video is publicly accessible"
        ]
        
        for tip in tips:
            self.add_log_message(f"{tip}\n", color='text_secondary')
        
        self.add_log_message("\n💡 If the problem persists:\n", color='accent_ai')
        self.add_log_message("• Test API Connection button\n", color='text_secondary')
        self.add_log_message("• Use shorter video clips\n", color='text_secondary')
        self.add_log_message("• Check the console for detailed errors\n", color='text_secondary')
        
        self.update_status("❌ Processing failed")
        messagebox.showerror("❌ Error", f"AI Auto Clipping failed:\n\n{error_message}")
        
        # Clean up temp directory if exists
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.add_log_message("\n🗑️ Temporary files cleaned up\n", color='text_secondary')
            except:
                self.add_log_message("\n⚠️ Could not clean up temporary files\n", color='accent_warning')
                

                               
    def get_watermark_size_filter(self):
        """Get watermark size based on setting"""
        size_setting = self.watermark_size.get()
        size_mapping = {
            "small": "64:64",    # 64x64 pixels
            "medium": "96:96",   # 96x96 pixels  
            "large": "128:128"   # 128x128 pixels
        }
        return size_mapping.get(size_setting, "96:96")
        
    def get_watermark_position_filter(self):
        """Get watermark position coordinates"""
        position = self.watermark_position.get()
        margin = 10  # Margin from edges
        
        position_mapping = {
            "top-left": f"{margin}:{margin}",
            "top-right": f"W-w-{margin}:{margin}",
            "bottom-left": f"{margin}:H-h-{margin}",
            "bottom-right": f"W-w-{margin}:H-h-{margin}",
            "center": "(W-w)/2:(H-h)/2"
        }
        return position_mapping.get(position, f"W-w-{margin}:{margin}")
            
    def get_video_encoding_settings(self):
        """Get optimal video encoding settings based on user choice and social media optimization"""
        quality = self.video_quality.get()
        crf = self.video_crf.get()
        is_social_optimized = self.social_optimized.get()
        target_res = self.target_resolution.get()
        
        # Base encoding settings
        if quality == "ultra":
            settings = {
                'preset': 'veryslow',
                'crf': crf,
                'profile': 'high',
                'level': '5.1' if "4K" in target_res else '4.2',
                'pix_fmt': 'yuv420p',
                'tune': 'film' if is_social_optimized else None
            }
        elif quality == "high":
            settings = {
                'preset': 'slow',
                'crf': crf,
                'profile': 'high',
                'level': '4.2' if "1080p" in target_res or "4K" in target_res else '4.1',
                'pix_fmt': 'yuv420p',
                'tune': 'film' if is_social_optimized else None
            }
        elif quality == "medium":
            settings = {
                'preset': 'medium', 
                'crf': crf,
                'profile': 'main',
                'level': '4.1',
                'pix_fmt': 'yuv420p'
            }
        else:  # fast
            settings = {
                'preset': 'fast',
                'crf': crf,
                'pix_fmt': 'yuv420p'
            }
        
        # Social media optimizations
        if is_social_optimized:
            # Add specific optimizations for social media platforms
            settings.update({
                'maxrate': self.get_optimal_bitrate(target_res),
                'bufsize': self.get_buffer_size(target_res),
                'g': '48',  # GOP size for social media compatibility
                'keyint_min': '24',  # Minimum keyframe interval
                'sc_threshold': '0',  # Disable scene change detection for consistent GOP
            })
            
            # Add movflags for better social media compatibility
            settings['movflags'] = '+faststart+use_metadata_tags'
            
        return settings
        
    def get_optimal_bitrate(self, target_res):
        """Get optimal maximum bitrate for social media platforms"""
        if "4K" in target_res:
            return "35000k"  # 35 Mbps for 4K
        elif "1080p" in target_res:
            return "8000k"   # 8 Mbps for 1080p
        elif "720p" in target_res:
            return "5000k"   # 5 Mbps for 720p
        else:
            return "3000k"   # Default fallback
            
    def get_buffer_size(self, target_res):
        """Get optimal buffer size for rate control"""
        if "4K" in target_res:
            return "70000k"  # 2x maxrate
        elif "1080p" in target_res:
            return "16000k"  
        elif "720p" in target_res:
            return "10000k"  
        else:
            return "6000k"
            

    
    def get_caption_style_preset(self):
        """Get caption style configuration based on selected preset"""
        preset = self.caption_style_preset.get()
        print(f"🎨 Getting style preset for: {preset}")
        
        # Validate preset value
        if not preset or preset not in ["classic", "modern", "neon", "elegant", "bold", "minimal", "gradient", "retro", "glow", "thin", "soft"]:
            print(f"⚠️ Invalid preset '{preset}', using classic as fallback")
            preset = "classic"
            self.caption_style_preset.set("classic")
        
        # Define style presets with GLOBAL FONT SIZE - All styles use same base font size
        # ASS format: &HAABBGGRR (Alpha, Blue, Green, Red)
        global_font_size = self.get_global_font_size()
        
        presets = {
            "classic": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FFFFFF",  # White (AABBGGRR format)
                "outline_color": "&H00000000",  # Black outline
                "outline_width": "1",  # Reduced from 2 to 1 for thinner stroke
                "shadow": True,
                "background": False,
                "background_color": "&H80000000",  # Semi-transparent black
                "font_weight": "normal",
                "font_style": "normal"
            },
            "modern": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FFFFFF",  # Bright white
                "outline_color": "&H00000000",  # No outline
                "outline_width": "0",
                "shadow": True,
                "background": True,
                "background_color": "&HCC000000",  # More opaque background
                "font_weight": "bold",
                "font_style": "normal"
            },
            "neon": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FFFF00",  # Cyan (AABBGGRR format)
                "outline_color": "&H00FFFFFF",  # White glow
                "outline_width": "1.5",  # Reduced from 3 to 1.5 for thinner glow effect
                "shadow": True,
                "background": False,
                "background_color": "&H00000000",
                "font_weight": "bold",
                "font_style": "normal"
            },
            "elegant": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FFFFCC",  # Light yellow (AABBGGRR format)
                "outline_color": "&H00000000",  # No outline
                "outline_width": "0",
                "shadow": False,
                "background": True,
                "background_color": "&H99000000",  # Subtle background
                "font_weight": "normal",
                "font_style": "italic"
            },
            "bold": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H0000FF00",  # Red (AABBGGRR format: BB=00, GG=00, RR=FF)
                "outline_color": "&H00FFFFFF",  # White outline
                "outline_width": "2",  # Reduced from 4 to 2 for more balanced look
                "shadow": True,
                "background": True,
                "background_color": "&HFF000000",  # Solid black background
                "font_weight": "bold",
                "font_style": "normal"
            },
            "minimal": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FFFFFF",  # White
                "outline_color": "&H00000000",  # No outline
                "outline_width": "0",
                "shadow": False,
                "background": False,
                "background_color": "&H00000000",
                "font_weight": "normal",
                "font_style": "normal"
            },
            "gradient": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FF80FF",  # Pink
                "outline_color": "&H00FF8000",  # Blue outline
                "outline_width": "1",  # Reduced from 2 to 1 for thinner outline
                "shadow": True,
                "background": True,
                "background_color": "&H80000000",  # Semi-transparent background
                "font_weight": "bold",
                "font_style": "normal"
            },
            "retro": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H0000FF00",  # Green (AABBGGRR format: BB=00, GG=FF, RR=00)
                "outline_color": "&H00000000",  # No outline
                "outline_width": "0",
                "shadow": False,
                "background": True,
                "background_color": "&HFF000000",  # Solid black background
                "font_weight": "normal",
                "font_style": "normal"
            },
            "glow": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H0000FFFF",  # Yellow (AABBGGRR format)
                "outline_color": "&H00FFFF00",  # Cyan glow
                "outline_width": "1.5",  # Reduced from 5 to 1.5 for thinner glow
                "shadow": True,
                "background": False,
                "background_color": "&H00000000",
                "font_weight": "bold",
                "font_style": "normal"
            },
            "thin": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FFFFFF",  # White
                "outline_color": "&H00000000",  # Black outline
                "outline_width": "0.5",  # Very thin outline for subtle definition
                "shadow": False,
                "background": False,
                "background_color": "&H00000000",
                "font_weight": "normal",
                "font_style": "normal"
            },
            "soft": {
                "font_size": global_font_size,  # Use global font size
                "color": "&H00FFFFFF",  # White
                "outline_color": "&H00000000",  # Black outline
                "outline_width": "0.8",  # Soft, thin outline
                "shadow": True,
                "background": True,
                "background_color": "&H66000000",  # Very subtle background
                "font_weight": "normal",
                "font_style": "normal"
            }
        }
        
        # Return the selected preset or classic as fallback
        selected_preset = presets.get(preset, presets["classic"])
        print(f"🎨 Selected preset config: {selected_preset}")
        
        # Validate that all required fields are present
        required_fields = ["font_size", "color", "outline_color", "outline_width", "background", "background_color", "font_weight", "font_style"]
        for field in required_fields:
            if field not in selected_preset:
                print(f"⚠️ Missing field '{field}' in preset '{preset}'")
                selected_preset[field] = presets["classic"][field]
        
        # Allow manual override of outline width if user has set a custom value
        if hasattr(self, 'caption_outline_width') and self.caption_outline_width.get() != "1.0":
            try:
                manual_outline = float(self.caption_outline_width.get())
                selected_preset["outline_width"] = str(manual_outline)
                print(f"🎨 Manual outline width override: {manual_outline}")
            except ValueError:
                print(f"⚠️ Invalid manual outline width: {self.caption_outline_width.get()}")
        
        # FIXED: All styles now use GLOBAL FONT SIZE - no override needed
        # This ensures consistent font size across all caption styles
        # Apply global font size to all presets
        selected_preset["font_size"] = self.get_global_font_size()
        print(f"🎨 Font size: GLOBAL ({selected_preset['font_size']}px)")
        
        print(f"🎨 Final preset config: {selected_preset}")
        return selected_preset
    
    def get_caption_animation_filter(self):
        """Get FFmpeg filter for caption animation"""
        animation = self.caption_animation.get()
        
        if animation == "none":
            return ""
        elif animation == "fade":
            return "fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5"
        elif animation == "slide":
            return "slide=slide=up:duration=0.5"
        elif animation == "bounce":
            return "bounce=period=0.5:amplitude=10"
        elif animation == "typewriter":
            # Typewriter effect for subtitles - use fade in/out with staggered timing
            return "fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3"
        elif animation == "zoom":
            return "zoompan=z='min(zoom+0.0015,1.5)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=640x360"
        elif animation == "shake":
            return "crop=w=in_w:h=in_h:x='if(gt(mod(t,0.1),0.05),2,0)':y='if(gt(mod(t,0.1),0.05),2,0)'"
        
        return ""
    
    def generate_typewriter_subtitle(self, text, start_time, duration):
        """Generate typewriter effect subtitle by splitting text into progressive segments"""
        try:
            # Split text into words
            words = text.split()
            if not words:
                return None
            
            # Calculate timing for typewriter effect
            total_words = len(words)
            word_duration = duration / total_words
            
            # Create progressive subtitle segments
            segments = []
            for i, word in enumerate(words):
                segment_start = start_time + (i * word_duration)
                segment_end = start_time + ((i + 1) * word_duration)
                
                # Build progressive text (show words up to current position)
                progressive_text = " ".join(words[:i+1])
                
                segment = {
                    'start': segment_start,
                    'end': segment_end,
                    'text': progressive_text
                }
                segments.append(segment)
            
            return segments
        except Exception as e:
            print(f"⚠️ Error generating typewriter subtitle: {e}")
            return None
    
    def get_caption_color_hex(self, color_name):
        """Convert color name to hex format for FFmpeg"""
        color_map = {
            "white": "&Hffffff",
            "yellow": "&H00ffff", 
            "cyan": "&Hffff00",
            "green": "&H00ff00",
            "orange": "&H0080ff",
            "pink": "&Hff80ff",
            "red": "&H0000ff",
            "blue": "&Hff0000"
        }
        return color_map.get(color_name, "&Hffffff")
    
    def create_caption_preview(self, canvas, style_config):
        """Create a visual preview of caption style on canvas"""
        print(f"🎨 Creating preview with config: {style_config}")
        # Clear canvas
        canvas.delete("all")
        
        # Canvas dimensions
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # If canvas is not properly sized yet, use default dimensions
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 400
            canvas_height = 80
        
        # Set canvas background to dark for better visibility
        canvas.configure(bg=self.colors['bg_primary'])
        
        # Get style configuration
        font_size = style_config.get("font_size", 24)
        color = style_config.get("color", "&H00FFFFFF")
        outline_color = style_config.get("outline_color", "&H00000000")
        
        # Handle decimal outline width values (e.g., "1.5", "0.8")
        try:
            outline_width = float(style_config.get("outline_width", "2"))
        except ValueError:
            outline_width = 2.0  # Fallback to default
        
        background = style_config.get("background", False)
        background_color = style_config.get("background_color", "&H80000000")
        
        print(f"🎨 Style values - Font: {font_size}, Color: {color}, Outline: {outline_color}, Width: {outline_width}, BG: {background}")
        
        # Convert ASS subtitle colors to RGB for canvas display
        def ass_to_rgb(ass_color):
            try:
                if ass_color.startswith("&H"):
                    ass_color = ass_color[2:]
                
                # Handle ASS subtitle format: AABBGGRR (Alpha, Blue, Green, Red)
                if len(ass_color) == 8:
                    # AABBGGRR format (with alpha)
                    a = int(ass_color[0:2], 16)
                    b = int(ass_color[2:4], 16)
                    g = int(ass_color[4:6], 16)
                    r = int(ass_color[6:8], 16)
                    return f"#{r:02x}{g:02x}{b:02x}"
                elif len(ass_color) == 6:
                    # BBGGRR format (no alpha, assume fully opaque)
                    b = int(ass_color[0:2], 16)
                    g = int(ass_color[2:4], 16)
                    r = int(ass_color[4:6], 16)
                    return f"#{r:02x}{g:02x}{b:02x}"
                else:
                    print(f"⚠️ Unknown ASS color format: {ass_color}")
                    return "#ffffff"
            except Exception as e:
                print(f"⚠️ Error parsing ASS color {ass_color}: {e}")
                return "#ffffff"
        
        text_color = ass_to_rgb(color)
        outline_rgb = ass_to_rgb(outline_color)
        bg_rgb = ass_to_rgb(background_color) if background else None
        
        print(f"🎨 Colors - Text: {color} -> {text_color}, Outline: {outline_color} -> {outline_rgb}, BG: {background_color} -> {bg_rgb}")
        
        # Sample text
        sample_text = self.caption_preview_text.get() or "Sample Caption Text"
        
        # Calculate text position (center of canvas)
        x = canvas_width // 2
        y = canvas_height // 2
        
        # Create background rectangle if enabled
        if background and bg_rgb:
            # Estimate text bounding box
            text_width = len(sample_text) * font_size * 0.6
            text_height = font_size * 1.2
            padding = 10
            
            bg_x1 = x - text_width // 2 - padding
            bg_y1 = y - text_height // 2 - padding
            bg_x2 = x + text_width // 2 + padding
            bg_y2 = y + text_height // 2 + padding
            
            canvas.create_rectangle(bg_x1, bg_y1, bg_x2, bg_y2, 
                                  fill=bg_rgb, outline="", tags="preview")
        
        # Get font weight and style from config
        font_weight = style_config.get("font_weight", "normal")
        font_style = style_config.get("font_style", "normal")
        
        # Build font string
        font_parts = ["Arial", str(font_size)]
        if font_weight == "bold":
            font_parts.append("bold")
        if font_style == "italic":
            font_parts.append("italic")
        font_string = " ".join(font_parts)
        
        # Create outline text (multiple layers for thickness)
        if outline_width > 0:
            # Convert outline width to integer for loop, but maintain visual effect
            outline_layers = max(1, int(outline_width * 2))  # Scale for better visual effect
            
            for dx in range(-outline_layers, outline_layers + 1):
                for dy in range(-outline_layers, outline_layers + 1):
                    if dx != 0 or dy != 0:
                        canvas.create_text(x + dx, y + dy, text=sample_text,
                                         font=font_string,
                                         fill=outline_rgb, tags="preview")
        
        # Create main text
        canvas.create_text(x, y, text=sample_text,
                         font=font_string,
                         fill=text_color, tags="preview")
    

    
    def update_caption_preview_settings(self):
        """Update the caption preview in settings tab when settings change"""
        if hasattr(self, 'caption_preview_canvas_settings'):
            # Get current style configuration
            style_config = self.get_caption_style_preset()
            print(f"🔄 Updating preview with style: {self.caption_style_preset.get()}")
            print(f"📋 Style config: {style_config}")
            
            # Force immediate update with multiple delays to ensure it takes effect
            self.root.after(50, lambda: self.create_caption_preview(self.caption_preview_canvas_settings, style_config))
            self.root.after(200, lambda: self.create_caption_preview(self.caption_preview_canvas_settings, style_config))
            self.root.after(500, lambda: self.create_caption_preview(self.caption_preview_canvas_settings, style_config))
            
            # Additional validation
            if style_config:
                print(f"✅ Style config loaded successfully:")
                print(f"   - Color: {style_config.get('color')}")
                print(f"   - Outline: {style_config.get('outline_color')}")
                print(f"   - Font size: {style_config.get('font_size')}")
                print(f"   - Background: {style_config.get('background')}")
            else:
                print(f"⚠️ Style config is empty!")
    
    def on_caption_style_change(self, *args):
        """Handle caption style preset change"""
        print(f"🎨 Style changed to: {self.caption_style_preset.get()}")
        # Force immediate update
        self.update_caption_preview_settings()
        self.update_style_description()
        # Force multiple updates with delays to ensure it takes effect
        self.root.after(100, self.update_caption_preview_settings)
        self.root.after(300, self.update_caption_preview_settings)
        self.root.after(600, self.update_caption_preview_settings)
        # Auto-save settings after change
        self.root.after(1000, self.save_settings)
    
    def update_style_description(self):
        """Update style description based on selected preset"""
        preset = self.caption_style_preset.get()
        
        descriptions = {
            "classic": "Classic: White text with thin black outline (1px)",
            "modern": "Modern: Bold white text with background, no outline",
            "neon": "Neon: Cyan text with thin white glow effect (1.5px)",
            "elegant": "Elegant: Light yellow italic text with subtle background",
            "bold": "Bold: Large red text with thin white outline (2px) and background",
            "minimal": "Minimal: Clean white text without effects",
            "gradient": "Gradient: Pink text with thin blue outline (1px)",
            "retro": "Retro: Green text on black background, no outline",
            "glow": "Glow: Yellow text with thin cyan glow effect (1.5px)",
            "thin": "Thin: White text with very thin outline (0.5px) for subtle definition",
            "soft": "Soft: White text with soft outline (0.8px) and subtle background"
        }
        
        description = descriptions.get(preset, "Classic: White text with black outline")
        
        if hasattr(self, 'style_description_settings'):
            self.style_description_settings.config(text=description)
    
    def on_caption_animation_change(self, *args):
        """Handle caption animation change"""
        self.update_caption_preview_settings()
        self.update_animation_description()
        # Auto-save settings after change
        self.root.after(1000, self.save_settings)
    
    def update_animation_description(self):
        """Update animation description based on selected animation"""
        animation = self.caption_animation.get()
        
        descriptions = {
            "none": "Animation: No animation",
            "fade": "Animation: Fade in/out effect",
            "slide": "Animation: Slide up from bottom",
            "bounce": "Animation: Bounce effect",
            "typewriter": "Animation: Typewriter effect",
            "zoom": "Animation: Zoom in effect",
            "shake": "Animation: Shake effect"
        }
        
        description = descriptions.get(animation, "Animation: No animation")
        
        if hasattr(self, 'animation_description_settings'):
            self.animation_description_settings.config(text=description)
    
    def on_caption_color_change(self, *args):
        """Handle caption color change"""
        self.update_caption_preview_settings()
    
    def on_emotion_change(self, *args):
        """Handle emotion focus change and update description"""
        selected_emotion = self.emotion_focus.get()
        
        emotion_descriptions = {
            "excitement": "🎯 Semangat & Energi Tinggi",
            "funny": "😄 Humor & Lucu", 
            "dramatic": "🎭 Ketegangan & Konflik",
            "inspiring": "💪 Motivasi & Inspirasi",
            "shocking": "😱 Kejutan & Tidak Terduga",
            "emotional": "💝 Menyentuh Hati",
            "sad": "😢 Kesedihan & Melankolis",
            "melancholic": "🌙 Nostalgia & Perasaan Dalam",
            "touching": "💕 Mengharukan & Emosional"
        }
        
        if hasattr(self, 'emotion_desc_label'):
            description = emotion_descriptions.get(selected_emotion, "")
            self.emotion_desc_label.config(text=description)
            
            # Update status with emotion context
            if selected_emotion in ["sad", "melancholic", "touching"]:
                self.update_status(f"🎭 Fokus emosi: {description} - AI akan mencari momen sedih dan mengharukan")
            else:
                self.update_status(f"🎭 Fokus emosi: {description}")
    
    def on_compact_emotion_change(self, *args):
        """Handle emotion focus change for compact mode"""
        selected_emotion = self.emotion_focus.get()
        
        emotion_descriptions = {
            "excitement": "🎯 Semangat & Energi Tinggi",
            "funny": "😄 Humor & Lucu", 
            "dramatic": "🎭 Ketegangan & Konflik",
            "inspiring": "💪 Motivasi & Inspirasi",
            "shocking": "😱 Kejutan & Tidak Terduga",
            "emotional": "💝 Menyentuh Hati",
            "sad": "😢 Kesedihan & Melankolis",
            "melancholic": "🌙 Nostalgia & Perasaan Dalam",
            "touching": "💕 Mengharukan & Emosional"
        }
        
        if hasattr(self, 'compact_emotion_desc'):
            description = emotion_descriptions.get(selected_emotion, "")
            self.compact_emotion_desc.config(text=description)
            
            # Update status with emotion context
            if selected_emotion in ["sad", "melancholic", "touching"]:
                self.update_status(f"🎭 Fokus emosi: {description} - AI akan mencari momen sedih dan mengharukan")
            else:
                self.update_status(f"🎭 Fokus emosi: {description}")
    
    def save_settings(self):
        """Save all current settings to a JSON file"""
        try:
            settings = {
                # API Settings
                'gemini_api_key': self.gemini_api_key.get(),
                
                # AI Analysis Settings
                'emotion_focus': self.emotion_focus.get(),
                'smart_duration': self.smart_duration.get(),
                'clip_duration': self.clip_duration.get(),
                'max_clips': self.max_clips.get(),
                'min_clip_duration': self.min_clip_duration.get(),
                'max_clip_duration': self.max_clip_duration.get(),
                'transcript_mode': self.transcript_mode.get(),
                'model_choice': self.model_choice.get(),
                
                # Caption Settings
                'auto_caption': self.auto_caption.get(),
                'caption_style_preset': self.caption_style_preset.get(),
                'caption_animation': self.caption_animation.get(),
                'caption_color': self.caption_color.get(),
                'caption_outline': self.caption_outline.get(),
                'caption_shadow': self.caption_shadow.get(),
                'caption_background': self.caption_background.get(),
                'caption_background_color': self.caption_background_color.get(),
                'caption_preview_text': self.caption_preview_text.get(),
                'caption_font_size': self.caption_font_size.get(),
                'caption_outline_width': self.caption_outline_width.get() if hasattr(self, 'caption_outline_width') else "1.0",

                'caption_language': self.caption_language.get(),
                'caption_style': self.caption_style.get(),
                
                # Output Settings
                'output_folder': self.output_folder.get(),
                
                # Anti-Copyright Settings
                'remove_metadata': self.remove_metadata.get(),
                'add_custom_author': self.add_custom_author.get(),
                'custom_author_name': self.custom_author_name.get(),
                'add_watermark': self.add_watermark.get(),
                'watermark_file': self.watermark_file.get(),
                'watermark_position': self.watermark_position.get(),
                'watermark_size': self.watermark_size.get(),
                'convert_to_portrait': self.convert_to_portrait.get(),
                'aspect_ratio': self.aspect_ratio.get(),
                
                # UI Settings
                'current_tab': self.current_tab if hasattr(self, 'current_tab') else 'start',
                'window_geometry': self.root.geometry(),
                
                # Timestamp
                'last_saved': datetime.now().isoformat()
            }
            
            # Create settings directory if it doesn't exist
            settings_dir = os.path.join(os.path.expanduser('~'), '.ai_clipper')
            os.makedirs(settings_dir, exist_ok=True)
            
            # Save to file
            settings_file = os.path.join(settings_dir, 'settings.json')
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Settings saved to: {settings_file}")
            
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
    
    def load_settings(self):
        """Load settings from JSON file"""
        try:
            settings_file = os.path.join(os.path.expanduser('~'), '.ai_clipper', 'settings.json')
            
            if not os.path.exists(settings_file):
                print("📝 No saved settings found, using defaults")
                return
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Load API Settings
            if 'gemini_api_key' in settings:
                self.gemini_api_key.set(settings['gemini_api_key'])
            
            # Load AI Analysis Settings
            if 'emotion_focus' in settings:
                self.emotion_focus.set(settings['emotion_focus'])
            if 'smart_duration' in settings:
                self.smart_duration.set(settings['smart_duration'])
            if 'clip_duration' in settings:
                self.clip_duration.set(settings['clip_duration'])
            if 'max_clips' in settings:
                self.max_clips.set(settings['max_clips'])
            if 'min_clip_duration' in settings:
                self.min_clip_duration.set(settings['min_clip_duration'])
            if 'max_clip_duration' in settings:
                self.max_clip_duration.set(settings['max_clip_duration'])
            if 'transcript_mode' in settings:
                self.transcript_mode.set(settings['transcript_mode'])
            if 'model_choice' in settings:
                self.model_choice.set(settings['model_choice'])
            
            # Load Caption Settings
            if 'auto_caption' in settings:
                self.auto_caption.set(settings['auto_caption'])
            if 'caption_style_preset' in settings:
                self.caption_style_preset.set(settings['caption_style_preset'])
            if 'caption_animation' in settings:
                self.caption_animation.set(settings['caption_animation'])
            if 'caption_color' in settings:
                self.caption_color.set(settings['caption_color'])
            if 'caption_outline' in settings:
                self.caption_outline.set(settings['caption_outline'])
            if 'caption_shadow' in settings:
                self.caption_shadow.set(settings['caption_shadow'])
            if 'caption_background' in settings:
                self.caption_background.set(settings['caption_background'])
            if 'caption_background_color' in settings:
                self.caption_background_color.set(settings['caption_background_color'])
            if 'caption_preview_text' in settings:
                self.caption_preview_text.set(settings['caption_preview_text'])
            if 'caption_font_size' in settings:
                self.caption_font_size.set(settings['caption_font_size'])
            if 'caption_outline_width' in settings and hasattr(self, 'caption_outline_width'):
                self.caption_outline_width.set(settings['caption_outline_width'])
            
            if 'caption_language' in settings:
                self.caption_language.set(settings['caption_language'])
            if 'caption_style' in settings:
                self.caption_style.set(settings['caption_style'])
            
            # Load Output Settings
            if 'output_folder' in settings:
                self.output_folder.set(settings['output_folder'])
            
            # Load Anti-Copyright Settings
            if 'remove_metadata' in settings:
                self.remove_metadata.set(settings['remove_metadata'])
            if 'add_custom_author' in settings:
                self.add_custom_author.set(settings['add_custom_author'])
            if 'custom_author_name' in settings:
                self.custom_author_name.set(settings['custom_author_name'])
            if 'add_watermark' in settings:
                self.add_watermark.set(settings['add_watermark'])
            if 'watermark_file' in settings:
                self.watermark_file.set(settings['watermark_file'])
            if 'watermark_position' in settings:
                self.watermark_position.set(settings['watermark_position'])
            if 'watermark_size' in settings:
                self.watermark_size.set(settings['watermark_size'])
            if 'convert_to_portrait' in settings:
                self.convert_to_portrait.set(settings['convert_to_portrait'])
            if 'aspect_ratio' in settings:
                self.aspect_ratio.set(settings['aspect_ratio'])
            
            # Load UI Settings
            if 'current_tab' in settings and hasattr(self, 'switch_tab'):
                self.root.after(100, lambda: self.switch_tab(settings['current_tab']))
            if 'window_geometry' in settings:
                self.root.geometry(settings['window_geometry'])
            
            print(f"✅ Settings loaded from: {settings_file}")
            
            # Update UI based on loaded settings
            self.root.after(200, self.update_ui_from_settings)
            
        except Exception as e:
            print(f"❌ Error loading settings: {e}")
    
    def update_ui_from_settings(self):
        """Update UI elements based on loaded settings"""
        try:
            # Update smart duration toggle
            if hasattr(self, 'smart_duration_frame') and hasattr(self, 'fixed_duration_frame'):
                if self.smart_duration.get():
                    self.fixed_duration_frame.pack_forget()
                    self.smart_duration_frame.pack(fill='x')
                else:
                    self.smart_duration_frame.pack_forget()
                    self.fixed_duration_frame.pack(fill='x')
            
            # Update caption options visibility (Settings Tab only)
            if hasattr(self, 'caption_options_settings'):
                if self.auto_caption.get():
                    self.caption_options_settings.pack(fill='x', pady=(5, 0))
                else:
                    self.caption_options_settings.pack_forget()
            
            # Update metadata options
            if hasattr(self, 'metadata_options'):
                if self.add_metadata.get():
                    self.metadata_options.pack(fill='x', pady=(5, 0))
                else:
                    self.metadata_options.pack_forget()
            
            # Update custom author options
            if hasattr(self, 'custom_author_options'):
                if self.custom_author.get():
                    self.custom_author_options.pack(fill='x', pady=(5, 0))
                else:
                    self.custom_author_options.pack_forget()
            
            # Update watermark options
            if hasattr(self, 'watermark_options'):
                if self.add_watermark.get():
                    self.watermark_options.pack(fill='x', pady=(5, 0))
                else:
                    self.watermark_options.pack_forget()
            
            print("✅ UI updated from loaded settings")
            
        except Exception as e:
            print(f"❌ Error updating UI from settings: {e}")
    
    def on_closing(self):
        """Handle application closing - save settings before exit"""
        try:
            print("💾 Saving settings before exit...")
            self.save_settings()
            self.root.destroy()
        except Exception as e:
            print(f"❌ Error saving settings on exit: {e}")
            self.root.destroy()
    
    def validate_and_improve_boundaries(self, ai_analysis):
        """Validate and improve clip boundaries for better content completeness"""
        if not ai_analysis:
            return ai_analysis
            
        improved_analysis = []
        
        for clip_info in ai_analysis:
            start_time = clip_info['start_time']
            end_time = clip_info['end_time']
            
            # Find the actual segment indices for these times
            start_segment_idx = self.find_segment_index(start_time)
            end_segment_idx = self.find_segment_index(end_time)
            
            if start_segment_idx is None or end_segment_idx is None:
                continue
                
            # Improve start boundary - look for better starting point
            improved_start = self.find_better_start_boundary(start_segment_idx, start_time)
            
            # Improve end boundary - look for better ending point
            improved_end = self.find_better_end_boundary(end_segment_idx, end_time)
            
            # Update clip info with improved boundaries
            improved_clip = clip_info.copy()
            improved_clip['start_time'] = improved_start
            improved_clip['end_time'] = improved_end
            improved_clip['original_start'] = start_time
            improved_clip['original_end'] = end_time
            improved_clip['boundary_improved'] = True
            
            improved_analysis.append(improved_clip)
            
        return improved_analysis
    
    def find_segment_index(self, time_seconds):
        """Find the segment index for a given time"""
        for i, segment in enumerate(self.transcript['segments']):
            if segment['start'] <= time_seconds <= segment['end']:
                return i
        return None
    
    def find_better_start_boundary(self, segment_idx, original_time):
        """Find a better starting boundary by looking at context"""
        if segment_idx <= 0:
            return original_time
            
        # Look at previous segments for natural starting points
        for i in range(segment_idx, max(0, segment_idx - 3), -1):
            segment = self.transcript['segments'][i]
            
            # Check if this is a good starting point
            if self.is_good_starting_boundary(segment, i):
                return segment['start']
                
        return original_time
    
    def find_better_end_boundary(self, segment_idx, original_time):
        """Find a better ending boundary by looking at context"""
        if segment_idx >= len(self.transcript['segments']) - 1:
            return original_time
            
        # Look at next segments for natural ending points
        for i in range(segment_idx, min(len(self.transcript['segments']), segment_idx + 3)):
            segment = self.transcript['segments'][i]
            
            # Check if this is a good ending point
            if self.is_good_ending_boundary(segment, i):
                return segment['end']
                
        return original_time
    
    def is_good_starting_boundary(self, segment, segment_idx):
        """Check if a segment is a good starting boundary"""
        # Check for natural starting indicators
        text = segment['text'].strip()
        
        # Good starting indicators
        good_starters = [
            'jadi', 'nah', 'oke', 'baik', 'sekarang', 'mari', 'ayo',
            'pertama', 'kedua', 'selanjutnya', 'berikutnya',
            'jadi begini', 'nah begini', 'oke begini',
            'pertama-tama', 'yang pertama', 'yang kedua'
        ]
        
        # Check if text starts with good starter
        for starter in good_starters:
            if text.lower().startswith(starter.lower()):
                return True
                
        # Check if previous segment has a long pause (natural break)
        if segment_idx > 0:
            prev_segment = self.transcript['segments'][segment_idx - 1]
            gap = segment['start'] - prev_segment['end']
            if gap > 1.5:  # Gap lebih dari 1.5 detik
                return True
                
        return False
    
    def is_good_ending_boundary(self, segment, segment_idx):
        """Check if a segment is a good ending boundary"""
        # Check for natural ending indicators
        text = segment['text'].strip()
        
        # Good ending indicators
        good_enders = [
            'jadi', 'nah', 'oke', 'baik', 'begitu', 'demikian',
            'itulah', 'begitulah', 'demikianlah', 'sekian',
            'terima kasih', 'sampai jumpa', 'selamat tinggal',
            'jadi begitulah', 'nah begitulah', 'oke begitulah'
        ]
        
        # Check if text ends with good ender
        for ender in good_enders:
            if text.lower().endswith(ender.lower()):
                return True
                
        # Check if next segment has a long pause (natural break)
        if segment_idx < len(self.transcript['segments']) - 1:
            next_segment = self.transcript['segments'][segment_idx + 1]
            gap = next_segment['start'] - segment['end']
            if gap > 1.5:  # Gap lebih dari 1.5 detik
                return True
                
        return False
    
    def generate_fallback_clips(self):
        """Generate fallback clips when AI analysis fails"""
        try:
            self.update_status("🔄 Membuat fallback clips berdasarkan transcript analysis...")
            
            if not self.transcript or 'segments' not in self.transcript:
                return []
                
            segments = self.transcript['segments']
            total_duration = segments[-1]['end'] if segments else 0
            
            if total_duration == 0:
                return []
                
            # Calculate optimal clip distribution
            max_clips = int(self.max_clips.get())
            target_duration = int(self.clip_duration.get()) if not self.smart_duration.get() else 60
            
            fallback_clips = []
            
            if self.smart_duration.get():
                # Smart duration fallback: find natural breaks
                fallback_clips = self.find_natural_break_clips(segments, max_clips)
            else:
                # Fixed duration fallback: distribute evenly
                fallback_clips = self.find_fixed_duration_clips(segments, max_clips, target_duration)
                
            if not fallback_clips:
                # Ultimate fallback: simple time-based division
                fallback_clips = self.create_simple_time_clips(total_duration, max_clips, target_duration)
                
            return fallback_clips
            
        except Exception as e:
            self.update_status(f"❌ Fallback clipping gagal: {str(e)}")
            return []
    
    def find_natural_break_clips(self, segments, max_clips):
        """Find clips based on natural breaks in transcript"""
        clips = []
        min_duration = int(self.min_clip_duration.get())
        max_duration = int(self.max_clip_duration.get())
        
        # Find segments with long pauses (natural breaks)
        break_points = []
        for i, segment in enumerate(segments):
            if i < len(segments) - 1:
                next_segment = segments[i + 1]
                gap = next_segment['start'] - segment['end']
                if gap > 1.0:  # Gap lebih dari 1 detik
                    break_points.append({
                        'time': segment['end'],
                        'gap': gap,
                        'segment_idx': i
                    })
        
        # Sort by gap length (longer gaps = better breaks)
        break_points.sort(key=lambda x: x['gap'], reverse=True)
        
        # Create clips from natural breaks
        for i, break_point in enumerate(break_points[:max_clips]):
            start_time = self.find_clip_start(segments, break_point['segment_idx'], min_duration)
            end_time = break_point['time']
            
            if end_time - start_time >= min_duration:
                clips.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'reason': f"Natural break dengan pause {break_point['gap']:.1f}s",
                    'emotion_score': 7,
                    'title': f"Clip {i+1} - Natural Break",
                    'content_summary': f"Bagian dengan natural pause {break_point['gap']:.1f} detik",
                    'boundary_confidence': 'high',
                    'fallback_generated': True
                })
                
        return clips
    
    def find_fixed_duration_clips(self, segments, max_clips, target_duration):
        """Find clips with fixed duration from transcript"""
        clips = []
        total_duration = segments[-1]['end'] if segments else 0
        
        if total_duration == 0:
            return clips
            
        # Calculate clip intervals
        interval = total_duration / max_clips
        
        for i in range(max_clips):
            start_time = i * interval
            end_time = min(start_time + target_duration, total_duration)
            
            # Adjust boundaries to segment boundaries
            start_time = self.adjust_to_segment_boundary(segments, start_time, 'start')
            end_time = self.adjust_to_segment_boundary(segments, end_time, 'end')
            
            if end_time > start_time:
                clips.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'reason': f"Fixed duration clip {i+1}",
                    'emotion_score': 6,
                    'title': f"Clip {i+1} - Fixed Duration",
                    'content_summary': f"Clip dengan durasi tetap {target_duration} detik",
                    'boundary_confidence': 'medium',
                    'fallback_generated': True
                })
                
        return clips
    
    def create_simple_time_clips(self, total_duration, max_clips, target_duration):
        """Create simple time-based clips as ultimate fallback"""
        clips = []
        
        for i in range(max_clips):
            start_time = i * (total_duration / max_clips)
            end_time = min(start_time + target_duration, total_duration)
            
            clips.append({
                'start_time': start_time,
                'end_time': end_time,
                'reason': f"Simple time-based clip {i+1}",
                'emotion_score': 5,
                'title': f"Clip {i+1} - Time Based",
                'content_summary': f"Clip berdasarkan pembagian waktu sederhana",
                'boundary_confidence': 'low',
                'fallback_generated': True
            })
            
        return clips
    
    def find_clip_start(self, segments, end_segment_idx, min_duration):
        """Find appropriate start time for a clip ending at given segment"""
        target_start = segments[end_segment_idx]['end'] - min_duration
        
        # Find the best starting segment
        for i in range(end_segment_idx, -1, -1):
            if segments[i]['start'] <= target_start:
                return segments[i]['start']
                
        return max(0, target_start)
    
    def adjust_to_segment_boundary(self, segments, time, boundary_type):
        """Adjust time to nearest segment boundary"""
        if not segments:
            return time
            
        if boundary_type == 'start':
            # Find segment that starts closest to the time
            best_segment = min(segments, key=lambda s: abs(s['start'] - time))
            return best_segment['start']
        else:  # end
            # Find segment that ends closest to the time
            best_segment = min(segments, key=lambda s: abs(s['end'] - time))
            return best_segment['end']
    
    def preview_clip_boundaries(self, clip_info):
        """Preview clip boundaries with context for user validation"""
        if not self.transcript or 'segments' not in self.transcript:
            return "Tidak ada transcript tersedia"
            
        start_time = clip_info['start_time']
        end_time = clip_info['end_time']
        
        # Find surrounding context
        start_segment_idx = self.find_segment_index(start_time)
        end_segment_idx = self.find_segment_index(end_time)
        
        if start_segment_idx is None or end_segment_idx is None:
            return "Boundary tidak valid"
            
        preview = f"🎬 CLIP PREVIEW: {clip_info.get('title', 'Untitled')}\n"
        preview += f"⏱️ Durasi: {end_time - start_time:.1f} detik\n"
        preview += f"🎯 Confidence: {clip_info.get('boundary_confidence', 'unknown')}\n\n"
        
        # Show context before start
        if start_segment_idx > 0:
            prev_segment = self.transcript['segments'][start_segment_idx - 1]
            preview += f"📝 Sebelum start ({prev_segment['start']:.1f}s):\n"
            preview += f"   ...{prev_segment['text'][-50:]}...\n\n"
            
        # Show start boundary
        start_segment = self.transcript['segments'][start_segment_idx]
        preview += f"🚀 START ({start_time:.1f}s):\n"
        preview += f"   {start_segment['text']}\n\n"
        
        # Show end boundary
        end_segment = self.transcript['segments'][end_segment_idx]
        preview += f"🏁 END ({end_time:.1f}s):\n"
        preview += f"   {end_segment['text']}\n\n"
        
        # Show context after end
        if end_segment_idx < len(self.transcript['segments']) - 1:
            next_segment = self.transcript['segments'][end_segment_idx + 1]
            preview += f"📝 Setelah end ({next_segment['start']:.1f}s):\n"
            preview += f"   ...{next_segment['text'][:50]}...\n\n"
            
        # Show boundary quality indicators
        preview += "🔍 BOUNDARY QUALITY:\n"
        
        # Start boundary quality
        start_quality = self.assess_boundary_quality(start_segment_idx, 'start')
        preview += f"   Start: {start_quality['score']}/10 - {start_quality['reason']}\n"
        
        # End boundary quality
        end_quality = self.assess_boundary_quality(end_segment_idx, 'end')
        preview += f"   End: {end_quality['score']}/10 - {end_quality['reason']}\n"
        
        # Overall quality
        overall_score = (start_quality['score'] + end_quality['score']) / 2
        preview += f"   Overall: {overall_score:.1f}/10\n"
        
        return preview
    
    def assess_boundary_quality(self, segment_idx, boundary_type):
        """Assess the quality of a boundary (start or end)"""
        if segment_idx < 0 or segment_idx >= len(self.transcript['segments']):
            return {'score': 0, 'reason': 'Invalid segment index'}
            
        segment = self.transcript['segments'][segment_idx]
        text = segment['text'].strip()
        score = 5  # Base score
        
        if boundary_type == 'start':
            # Check for good starting indicators
            good_starters = [
                'jadi', 'nah', 'oke', 'baik', 'sekarang', 'mari', 'ayo',
                'pertama', 'kedua', 'selanjutnya', 'berikutnya',
                'jadi begini', 'nah begini', 'oke begini',
                'pertama-tama', 'yang pertama', 'yang kedua'
            ]
            
            for starter in good_starters:
                if text.lower().startswith(starter.lower()):
                    score += 3
                    break
                    
            # Check for pause before
            if segment_idx > 0:
                prev_segment = self.transcript['segments'][segment_idx - 1]
                gap = segment['start'] - prev_segment['end']
                if gap > 1.5:
                    score += 2
                    reason = f"Natural pause {gap:.1f}s sebelum start"
                elif gap > 0.5:
                    score += 1
                    reason = f"Small pause {gap:.1f}s sebelum start"
                else:
                    reason = "Tidak ada pause sebelum start"
            else:
                reason = "Start dari awal video"
                
        else:  # end boundary
            # Check for good ending indicators
            good_enders = [
                'jadi', 'nah', 'oke', 'baik', 'begitu', 'demikian',
                'itulah', 'begitulah', 'demikianlah', 'sekian',
                'terima kasih', 'sampai jumpa', 'selamat tinggal',
                'jadi begitulah', 'nah begitulah', 'oke begitulah'
            ]
            
            for ender in good_enders:
                if text.lower().endswith(ender.lower()):
                    score += 3
                    break
                    
            # Check for pause after
            if segment_idx < len(self.transcript['segments']) - 1:
                next_segment = self.transcript['segments'][segment_idx + 1]
                gap = next_segment['start'] - segment['end']
                if gap > 1.5:
                    score += 2
                    reason = f"Natural pause {gap:.1f}s setelah end"
                elif gap > 0.5:
                    score += 1
                    reason = f"Small pause {gap:.1f}s setelah end"
                else:
                    reason = "Tidak ada pause setelah end"
            else:
                reason = "End di akhir video"
                
        # Cap score at 10
        score = min(10, score)
        
        return {'score': score, 'reason': reason}
    
    def get_clip_quality_score(self, clip_info):
        """Calculate overall quality score for a clip"""
        if not self.transcript or 'segments' not in self.transcript:
            return 0
            
        start_time = clip_info['start_time']
        end_time = clip_info['end_time']
        
        start_segment_idx = self.find_segment_index(start_time)
        end_segment_idx = self.find_segment_index(end_time)
        
        if start_segment_idx is None or end_segment_idx is None:
            return 0
            
        # Boundary quality scores
        start_quality = self.assess_boundary_quality(start_segment_idx, 'start')
        end_quality = self.assess_boundary_quality(end_segment_idx, 'end')
        
        # Content completeness score
        content_score = self.assess_content_completeness(start_segment_idx, end_segment_idx)
        
        # Duration appropriateness score
        duration_score = self.assess_duration_appropriateness(end_time - start_time)
        
        # Calculate weighted average
        overall_score = (
            start_quality['score'] * 0.3 +  # Start boundary importance
            end_quality['score'] * 0.3 +    # End boundary importance
            content_score * 0.3 +           # Content completeness
            duration_score * 0.1            # Duration appropriateness
        )
        
        return round(overall_score, 1)
    
    def assess_content_completeness(self, start_idx, end_idx):
        """Assess how complete the content is within the clip boundaries"""
        if start_idx >= end_idx:
            return 0
            
        # Count complete sentences
        complete_sentences = 0
        total_segments = end_idx - start_idx + 1
        
        for i in range(start_idx, end_idx + 1):
            if i < len(self.transcript['segments']):
                text = self.transcript['segments'][i]['text'].strip()
                # Simple sentence completion check
                if text.endswith(('.', '!', '?', ':', ';')):
                    complete_sentences += 1
                    
        # Calculate completeness ratio
        if total_segments > 0:
            completeness_ratio = complete_sentences / total_segments
            return min(10, completeness_ratio * 10)
        else:
            return 0
    
    def assess_duration_appropriateness(self, duration):
        """Assess if the clip duration is appropriate"""
        min_duration = int(self.min_clip_duration.get())
        max_duration = int(self.max_clip_duration.get())
        
        if duration < min_duration:
            return max(0, 10 - (min_duration - duration) * 2)
        elif duration > max_duration:
            return max(0, 10 - (duration - max_duration) * 0.5)
        else:
            # Optimal duration range
            optimal_range = (min_duration + max_duration) / 2
            deviation = abs(duration - optimal_range)
            return max(5, 10 - deviation * 0.5)
    
    def suggest_boundary_improvements(self, clip_info):
        """Suggest improvements for clip boundaries"""
        if not self.transcript or 'segments' not in self.transcript:
            return "Tidak ada transcript tersedia"
            
        start_time = clip_info['start_time']
        end_time = clip_info['end_time']
        
        start_segment_idx = self.find_segment_index(start_time)
        end_segment_idx = self.find_segment_index(end_time)
        
        if start_segment_idx is None or end_segment_idx is None:
            return "Boundary tidak valid"
            
        suggestions = []
        
        # Check start boundary
        start_quality = self.assess_boundary_quality(start_segment_idx, 'start')
        if start_quality['score'] < 7:
            suggestions.append(f"🚀 Start boundary bisa diperbaiki:")
            suggestions.append(f"   - Score saat ini: {start_quality['score']}/10")
            suggestions.append(f"   - Alasan: {start_quality['reason']}")
            
            # Suggest better start point
            better_start = self.find_better_start_boundary(start_segment_idx, start_time)
            if better_start != start_time:
                suggestions.append(f"   - Saran: Mulai dari {better_start:.1f}s")
                
        # Check end boundary
        end_quality = self.assess_boundary_quality(end_segment_idx, 'end')
        if end_quality['score'] < 7:
            suggestions.append(f"🏁 End boundary bisa diperbaiki:")
            suggestions.append(f"   - Score saat ini: {end_quality['score']}/10")
            suggestions.append(f"   - Alasan: {end_quality['reason']}")
            
            # Suggest better end point
            better_end = self.find_better_end_boundary(end_segment_idx, end_time)
            if better_end != end_time:
                suggestions.append(f"   - Saran: Akhiri di {better_end:.1f}s")
                
        if not suggestions:
            return "✅ Boundary sudah optimal!"
        else:
            return "\n".join(suggestions)

def main():
    root = tk.Tk()
    app = AIAutoClipper(root)
    root.mainloop()

if __name__ == "__main__":
    main() 