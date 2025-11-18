#!/usr/bin/env python3
"""
Auto ChromeDriver Manager
========================

Automatically downloads and manages ChromeDriver for web scraping.
Platform-agnostic solution that works on macOS, Linux, and Windows.
"""

import os
import sys
import platform
import zipfile
import requests
import shutil
from pathlib import Path

class AutoChromeDriver:
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.chrome_version = None
        
    def get_chrome_version(self):
        """Get Chrome version from system"""
        try:
            if self.system == "darwin":  # macOS
                result = os.popen('"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version').read().strip()
                if "Google Chrome" in result:
                    version = result.split("Google Chrome ")[1].split(".")[0]
                    return version
            elif self.system == "linux":
                # Try different commands
                for cmd in ['google-chrome --version', 'chromium-browser --version']:
                    try:
                        result = os.popen(cmd).read().strip()
                        if "Chrome" in result or "Chromium" in result:
                            version = result.split()[2].split('.')[0]
                            return version
                    except:
                        continue
            elif self.system == "windows":
                result = os.popen('reg query "HKLM\SOFTWARE\Google\Chrome\BLBeacon" /v version').read()
                if result:
                    version = result.split()[-1].split('.')[0]
                    return version
        except:
            pass
        
        return None
    
    def get_latest_chromedriver_version(self):
        """Get latest ChromeDriver version"""
        try:
            response = requests.get('https://chromedriver.storage.googleapis.com/LATEST_RELEASE', timeout=10)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Error getting latest version: {e}")
            return None
    
    def download_chromedriver(self, version):
        """Download ChromeDriver for current platform"""
        print(f"📥 Downloading ChromeDriver {version}...")
        
        # Determine download URL based on platform
        if self.system == "darwin":  # macOS
            filename = "chromedriver_mac64.zip"
        elif self.system == "linux":
            filename = "chromedriver_linux64.zip"
        elif self.system == "windows":
            filename = "chromedriver_win32.zip"
        else:
            print(f"❌ Unsupported platform: {self.system}")
            return False
        
        url = f"https://chromedriver.storage.googleapis.com/{version}/{filename}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def extract_chromedriver(self, version):
        """Extract ChromeDriver from zip"""
        try:
            if self.system == "darwin":
                zip_file = "chromedriver_mac64.zip"
            elif self.system == "linux":
                zip_file = "chromedriver_linux64.zip"
            elif self.system == "windows":
                zip_file = "chromedriver_win32.zip"
            else:
                return False
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall('.')
            
            # Find chromedriver executable
            if self.system == "windows":
                chromedriver_name = "chromedriver.exe"
            else:
                chromedriver_name = "chromedriver"
            
            if os.path.exists(chromedriver_name):
                # Make executable on Unix systems
                if self.system != "windows":
                    os.chmod(chromedriver_name, 0o755)
                
                print(f"✅ ChromeDriver extracted: {chromedriver_name}")
                return True
            else:
                print(f"❌ ChromeDriver not found after extraction")
                return False
                
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return False
    
    def install_chromedriver(self):
        """Install ChromeDriver to system PATH"""
        chromedriver_path = "chromedriver"
        if self.system == "windows":
            chromedriver_path = "chromedriver.exe"
        
        if not os.path.exists(chromedriver_path):
            print("❌ chromedriver executable not found")
            return False
        
        # Determine installation path
        if self.system == "darwin":  # macOS
            install_path = "/usr/local/bin/chromedriver"
        elif self.system == "linux":
            install_path = "/usr/local/bin/chromedriver"
        elif self.system == "windows":
            install_path = "C:/Windows/System32/chromedriver.exe"
        else:
            print(f"❌ Unsupported platform: {self.system}")
            return False
        
        try:
            if self.system == "windows":
                # Windows installation
                shutil.copy2(chromedriver_path, install_path)
            else:
                # Unix installation (needs sudo)
                print("🔐 Installing to system location (may require sudo)...")
                import subprocess
                result = subprocess.run(['sudo', 'cp', chromedriver_path, install_path], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    subprocess.run(['sudo', 'chmod', '755', install_path])
                    print(f"✅ Installed to: {install_path}")
                else:
                    # Try user directory
                    user_path = os.path.expanduser("~/bin/chromedriver")
                    os.makedirs(os.path.dirname(user_path), exist_ok=True)
                    shutil.copy2(chromedriver_path, user_path)
                    os.environ['PATH'] = f"{os.path.dirname(user_path)}:{os.environ.get('PATH', '')}"
                    print(f"✅ Installed to user directory: {user_path}")
                    return user_path
            
            print(f"✅ ChromeDriver installed to: {install_path}")
            return install_path
            
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up downloaded files"""
        files_to_remove = [
            "chromedriver_mac64.zip",
            "chromedriver_linux64.zip", 
            "chromedriver_win32.zip",
            "chromedriver.exe"
        ]
        
        for filename in files_to_remove:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"🗑️ Cleaned up: {filename}")
    
    def test_installation(self):
        """Test if ChromeDriver is working"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=options)
            driver.get('https://www.google.com')
            title = driver.title
            driver.quit()
            
            print(f"✅ ChromeDriver test successful! (Title: {title})")
            return True
            
        except Exception as e:
            print(f"❌ ChromeDriver test failed: {e}")
            return False
    
    def install(self):
        """Main installation process"""
        print("🚀 Auto ChromeDriver Installer")
        print("=" * 40)
        
        # Check if already installed
        try:
            from selenium import webdriver
            driver = webdriver.Chrome()
            driver.quit()
            print("✅ ChromeDriver already installed and working!")
            return True
        except:
            pass
        
        print("📊 System Information:")
        print(f"   Platform: {self.system}")
        print(f"   Architecture: {self.arch}")
        
        # Check Chrome version
        self.chrome_version = self.get_chrome_version()
        if self.chrome_version:
            print(f"   Chrome version: {self.chrome_version}")
        else:
            print("   ⚠️ Chrome version not detected")
        
        # Get latest ChromeDriver version
        print("\n🔍 Checking for latest ChromeDriver...")
        latest_version = self.get_latest_chromedriver_version()
        if not latest_version:
            print("❌ Could not determine latest version")
            return False
        
        print(f"   Latest ChromeDriver version: {latest_version}")
        
        # Download
        print(f"\n📥 Installing ChromeDriver {latest_version}...")
        if not self.download_chromedriver(latest_version):
            return False
        
        # Extract
        if not self.extract_chromedriver(latest_version):
            return False
        
        # Install
        install_path = self.install_chromedriver()
        if not install_path:
            return False
        
        # Test
        print(f"\n🧪 Testing ChromeDriver...")
        if not self.test_installation():
            print("⚠️ Installation completed but test failed")
            return False
        
        # Clean up
        print(f"\n🧹 Cleaning up...")
        self.cleanup()
        
        print("\n🎉 ChromeDriver installation completed successfully!")
        print(f"📍 Location: {install_path}")
        return True

def get_chrome_driver():
    """Auto-install ChromeDriver and return webdriver"""
    try:
        # Try to get existing driver first
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        return driver
        
    except Exception as e:
        print(f"❌ ChromeDriver not available: {e}")
        print("🔧 Running auto-installer...")
        
        installer = AutoChromeDriver()
        if installer.install():
            # Try again after installation
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            return webdriver.Chrome(options=options)
        else:
            raise Exception("Failed to install ChromeDriver")

if __name__ == "__main__":
    installer = AutoChromeDriver()
    success = installer.install()
    
    if success:
        print("\n🌟 Ready for web scraping!")
        sys.exit(0)
    else:
        print("\n❌ Installation failed")
        sys.exit(1)