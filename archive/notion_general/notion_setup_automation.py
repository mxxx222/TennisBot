#!/usr/bin/env python3
"""
Notion Setup Automation Script
Automates the creation of Notion integration and initial page setup for TennisBot ROI System.
"""

import sys
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

def install_dependencies():
    """Install required dependencies if not present."""
    global ChromeDriverManager
    if ChromeDriverManager is None:
        print("Installing required dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "selenium", "webdriver-manager"])
        print("Dependencies installed successfully.")
        # Import after installation
        from webdriver_manager.chrome import ChromeDriverManager
        print("Import successful after installation.")
    else:
        print("Dependencies already installed.")

def setup_driver():
    """Set up Chrome WebDriver with non-headless mode."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Not headless as requested
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Please ensure Chrome is installed and try again.")
        sys.exit(1)

def wait_for_login(driver):
    """Wait for user to manually log in to Notion."""
    print("Opening Notion integrations page...")
    driver.get("https://www.notion.so/my-integrations")

    print("Please log in to Notion in the browser window that opened.")
    print("Waiting for you to complete login...")

    try:
        # Wait for the integrations page to load (look for 'New integration' button)
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'New integration') or contains(@class, 'new-integration')]"))
        )
        print("Login detected. Proceeding with automation...")
    except TimeoutException:
        print("Timeout waiting for login. Please ensure you're logged in and try again.")
        driver.quit()
        sys.exit(1)

def create_integration(driver):
    """Create new Notion integration."""
    try:
        # Click 'New integration' button
        new_int_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'New integration') or contains(@class, 'new-integration')]"))
        )
        new_int_button.click()

        # Wait for form to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='name'], input[placeholder*='integration']"))
        )

        # Fill integration name
        name_field = driver.find_element(By.CSS_SELECTOR, "input[name='name'], input[placeholder*='integration']")
        name_field.clear()
        name_field.send_keys("TennisBot ROI System")

        # Select permissions - look for checkboxes related to content and databases
        # Common permission selectors (may need adjustment based on Notion's UI)
        permissions_to_select = [
            "Read content",
            "Update content",
            "Insert content",
            "Read databases",
            "Update databases",
            "Insert databases",
            "Read pages",
            "Update pages",
            "Insert pages"
        ]

        for permission in permissions_to_select:
            try:
                # Try to find checkbox by label text
                checkbox = driver.find_element(By.XPATH, f"//label[contains(text(), '{permission}')]/preceding-sibling::input[@type='checkbox']")
                if not checkbox.is_selected():
                    checkbox.click()
            except NoSuchElementException:
                # Try alternative selector
                try:
                    checkbox = driver.find_element(By.XPATH, f"//input[@type='checkbox' and following-sibling::label[contains(text(), '{permission}')]]")
                    if not checkbox.is_selected():
                        checkbox.click()
                except NoSuchElementException:
                    print(f"Warning: Could not find checkbox for '{permission}' permission")

        # Submit the form
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Submit') or contains(text(), 'Create')]")
        submit_button.click()

        print("Integration created successfully.")

    except Exception as e:
        print(f"Error creating integration: {e}")
        driver.quit()
        sys.exit(1)

def extract_integration_token(driver):
    """Extract the Internal Integration Token from the page."""
    try:
        # Wait for the token to appear (usually in a code block or input field)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "code, input[value*='secret_'], .token-display"))
        )

        # Try different selectors for the token
        token_element = None
        selectors = [
            "code",
            "input[value*='secret_']",
            ".token-display",
            "[data-testid*='token']",
            ".integration-token"
        ]

        for selector in selectors:
            try:
                token_element = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue

        if token_element:
            token = token_element.text or token_element.get_attribute("value")
            print(f"Internal Integration Token: {token}")
            return token
        else:
            print("Could not find the integration token on the page.")
            return None

    except Exception as e:
        print(f"Error extracting token: {e}")
        return None

def create_notion_page(driver):
    """Navigate to Notion and create a new page."""
    try:
        print("Navigating to Notion main page...")
        driver.get("https://www.notion.so/")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notion-sidebar, [data-testid='sidebar'], .sidebar"))
        )

        # Try to find and click "New" button in sidebar
        new_button_selectors = [
            "//button[contains(text(), 'New')]",
            "//div[contains(@class, 'sidebar')]//button[contains(text(), 'New')]",
            "[data-testid='new-page-button']",
            ".new-page-button"
        ]

        new_button = None
        for selector in new_button_selectors:
            try:
                if selector.startswith("//"):
                    new_button = driver.find_element(By.XPATH, selector)
                else:
                    new_button = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue

        if new_button:
            new_button.click()
        else:
            # Fallback: try keyboard shortcut Ctrl+N
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys('n').key_up(Keys.CONTROL).perform()

        # Wait for new page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notion-page-content, [data-testid='page-content'], .page-content"))
        )

        # Set page title
        title_selectors = [
            ".notion-page-title, [data-testid='page-title'], .page-title",
            "h1[contenteditable='true']",
            "[placeholder*='Untitled']"
        ]

        title_element = None
        for selector in title_selectors:
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue

        if title_element:
            title_element.clear()
            title_element.send_keys("⚽ Jalkapallo ROI System")
            # Press Enter to confirm title
            from selenium.webdriver.common.keys import Keys
            title_element.send_keys(Keys.RETURN)
            print("New page created with title '⚽ Jalkapallo ROI System'")
        else:
            print("Warning: Could not set page title automatically")

    except Exception as e:
        print(f"Error creating Notion page: {e}")

def extract_page_id(driver):
    """Extract page ID from the current URL."""
    try:
        current_url = driver.current_url
        # Notion URLs typically look like: https://www.notion.so/workspace/page-id
        # or https://www.notion.so/page-id
        url_parts = current_url.split('/')
        page_id = None

        for part in url_parts:
            if len(part) == 32 and '-' in part:  # Notion page IDs are 32 chars with hyphens
                page_id = part
                break

        if page_id:
            print(f"Page ID: {page_id}")
            return page_id
        else:
            print("Could not extract page ID from URL")
            return None

    except Exception as e:
        print(f"Error extracting page ID: {e}")
        return None

def main():
    """Main automation function."""
    install_dependencies()

    driver = setup_driver()

    try:
        wait_for_login(driver)
        create_integration(driver)
        token = extract_integration_token(driver)

        create_notion_page(driver)
        page_id = extract_page_id(driver)

        print("\n--- SETUP COMPLETE ---")
        if token:
            print(f"Integration Token: {token}")
        if page_id:
            print(f"Page ID: {page_id}")

        input("Press Enter to close the browser...")

    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()