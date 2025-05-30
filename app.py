import os
import re
import sys
import time
import pyperclip
from platformdirs import user_downloads_dir
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

options = Options()
options.binary_location = '/usr/bin/chromium-browser'  # important fix
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(), options=options)


def run_selenium(url: str, browser_type: str):
    driver.set_window_size(1920, 1200)
    wait = WebDriverWait(driver, 1200)

    # Open temp mail page
    driver.get("https://temp-mail.io/en")
    time.sleep(10)
    email_input = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='email']")))
    email = email_input.get_attribute('value')
    print("Temporary Email:", email)

    # Open target website
    driver.execute_script("window.open('', '_blank');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(url)

    # Click "Sign up"
    signup_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Sign up']")))
    signup_button.click()

    # Fill email field
    email_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='email_id']")))
    email_field.send_keys(email)

    # Click "Create account"S
    create_account_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Create account']")))
    create_account_btn.click()

    # Wait for OTP email
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(20)
    otp_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class,'message__subject')]")))
    otp_text = otp_element.text
    otp_match = re.search(r"\d+", otp_text)
    otp = otp_match.group() if otp_match else ""
    print("Extracted OTP:", otp)

    if not otp:
        print("Failed to extract OTP.")
        return  # No quit, to keep the browser open

    # Enter OTP
    driver.switch_to.window(driver.window_handles[1])
    otp_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='code']")))
    otp_input.send_keys(otp)

    # Re-locate and click the "Create account" button again to prevent stale element error
    create_account_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Create account']")))
    create_account_btn.click()

    # Fill user details
    full_name_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='userFullName']")))
    full_name_input.send_keys("Wellmedic")

    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    submit_button.click()

    # Select Instagram
    instagram_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@id='instagram']")))
    instagram_button.click()
    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    submit_button.click()

    # Select Content Creator
    content_creator_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "(//div[text()='Content creator']//parent::div)[1]")))
    content_creator_button.click()
    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    submit_button.click()

    # Enter birth year
    birth_year_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='userBirthDate.year']")))
    birth_year_input.send_keys("1997")
    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    submit_button.click()

    # Enter brief
    brief_input = wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[@name='brief']")))
    brief_input.send_keys("Make a video on cat moving on the boat")

    generate_video = wait.until(
        EC.presence_of_element_located((By.XPATH, "//button[.//text()[contains(., 'Generate a video')]]")))
    generate_video.click()

    # Interact with elements using the new method
    wait_and_click('//div[contains(text(),"Stock")]')
    # wait_and_click('//button[contains(@value,"1.0")]')
    wait_and_click("//*[text()='Continue']")  # Submit button
    wait_and_click("//*[text()='Download']")  # Download button

    wait_and_click('//div[contains(text(),"Stock")]')  # Stock watermark
    wait_and_click('//div[contains(text(),"Normal")]')  # Normal button
    # wait_and_click('//div[contains(text(),"1080")]')  # Quality button
    wait_and_click('//div[contains(text(),"Continue")]')  # Continue button

    # Keep the browser open
    print("Script completed. Browser will remain open.")
    try:
        while True:
            time.sleep(1)
            wait_for_download(get_downloads_folder())

            latest_file = get_latest_file(get_downloads_folder())
            if latest_file:
                print(f"Downloaded file: {latest_file}")
                break
            # Keeps script running
    except KeyboardInterrupt:
        print("\nExiting script...")


def wait_until_element(xpath, timeout=99, poll_frequency=1):
    """Keep checking for the presence of an element until timeout."""
    start_time = time.time()
    while True:
        try:
            element = driver.find_element(By.XPATH, xpath)
            return element  # Return element if found
        except NoSuchElementException:
            if time.time() - start_time > timeout:
                raise Exception(f"Timeout: Element not found -> {xpath}")
            time.sleep(poll_frequency)  # Wait before retrying


# Function to check for element and click it
def wait_and_click(xpath, timeout=12000):
    element = wait_until_element(xpath, timeout)
    element.click()


def wait_for_download(download_dir, timeout=1500):
    """
    Wait every second for a new file (not .crdownload) to appear in download_dir.
    Returns the full path of the downloaded file once complete.
    Raises TimeoutError if no file is fully downloaded within timeout.
    """
    print("Waiting for file download to complete...")
    initial_files = set(os.listdir(download_dir))
    deadline = time.time() + timeout

    while time.time() < deadline:
        time.sleep(1)
        current_files = set(os.listdir(download_dir))
        new_files = current_files - initial_files

        # Filter out temporary download files
        complete_files = [f for f in new_files if not f.endswith('.crdownload')]
        print(complete_files)

        if complete_files:
            latest_file = max(
                (os.path.join(download_dir, f) for f in complete_files),
                key=os.path.getmtime
            )
            print(f"Download complete: {latest_file}")
            return latest_file

    raise TimeoutError("Timed out waiting for download to complete.")


def get_latest_file(download_dir):
    files = [os.path.join(download_dir, f) for f in os.listdir(download_dir)]
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def get_downloads_folder():
    if os.name == 'posix':  # Unix/Linux/MacOS
        downloads_path = os.path.expanduser('~/Downloads')
    elif os.name == 'nt':  # Windows
        downloads_path = os.path.join(os.getenv('USERPROFILE'), 'Downloads')
    else:
        raise RuntimeError("Unsupported operating system")

    return downloads_path


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://invideo.io/"
    browser_type = sys.argv[2] if len(sys.argv) > 2 else "chrome"
    run_selenium(url, browser_type)
