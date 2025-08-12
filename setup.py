#!/usr/bin/env python3
"""
Setup script untuk TikTok Video Downloader
Script ini akan menginstall semua dependencies yang diperlukan
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {description} berhasil")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} gagal")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("✗ Python 3.7 atau lebih baru diperlukan")
        print(f"  Versi saat ini: {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor} kompatibel")
    return True

def check_pip():
    """Check if pip is available"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✓ pip tersedia")
        return True
    except subprocess.CalledProcessError:
        print("✗ pip tidak ditemukan")
        return False

def install_requirements():
    """Install required packages"""
    requirements = [
        "yt-dlp>=2024.12.13",
        "requests>=2.31.0"
    ]
    
    for package in requirements:
        if not run_command(f"{sys.executable} -m pip install {package}", 
                          f"Installing {package}"):
            return False
    return True

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        print("✓ tkinter tersedia")
        return True
    except ImportError:
        print("✗ tkinter tidak tersedia")
        print("  Install Python dengan tkinter support")
        return False

def check_ffmpeg():
    """Check if FFmpeg is available (optional)"""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, 
                      capture_output=True)
        print("✓ FFmpeg tersedia (fitur hapus metadata aktif)")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ FFmpeg tidak ditemukan (fitur hapus metadata nonaktif)")
        print("  Install FFmpeg jika ingin menggunakan fitur hapus metadata:")
        print("  - Windows: Download dari https://ffmpeg.org")
        print("  - macOS: brew install ffmpeg")
        print("  - Linux: sudo apt install ffmpeg")
        return False

def main():
    print("TikTok Video Downloader - Setup")
    print("=" * 40)
    
    success = True
    
    # Check Python version
    print("\n1. Checking Python version...")
    if not check_python_version():
        success = False
    
    # Check pip
    print("\n2. Checking pip...")
    if not check_pip():
        success = False
    
    # Check tkinter
    print("\n3. Checking tkinter...")
    if not check_tkinter():
        success = False
    
    if not success:
        print("\n✗ Setup gagal. Perbaiki masalah di atas terlebih dahulu.")
        return False
    
    # Install requirements
    print("\n4. Installing Python packages...")
    if not install_requirements():
        print("\n✗ Gagal install dependencies")
        return False
    
    # Check FFmpeg (optional)
    print("\n5. Checking FFmpeg...")
    check_ffmpeg()
    
    print("\n" + "=" * 40)
    print("✓ Setup selesai!")
    print("\nCara menjalankan aplikasi:")
    print("  python main.py")
    print("  atau")
    print("  python run.py")
    print("  atau (Windows)")
    print("  double-click run.bat")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup dibatalkan oleh user")
    except Exception as e:
        print(f"\nError tidak terduga: {e}")
    finally:
        input("\nTekan Enter untuk keluar...") 