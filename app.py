import os
import re
import sys
import time
import requests
from platformdirs import user_downloads_dir
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Chrome()


def run_selenium(url: str, message: str):
    global public_url
    driver.set_window_size(1382, 744)
    global wait
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

    version = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-state='closed']")))
    version = version.text

    # Enter brief
    brief_input = wait.until(EC.presence_of_element_located((By.XPATH, "//textarea[@name='brief']")))
    brief_input.send_keys(message)

    generate_video = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Generate')]")))
    generate_video.click()

    # Interact with elements using the new method
    wait_and_click('//div[contains(text(),"Stock")]')
    # wait_and_click('//button[contains(@value,"1.0")]')
    wait_and_click("//*[text()='Continue']")  # Submit button
    if version != "v3.0":
        wait_and_click("(//*[text()='Continue'])[2]")
        # continue button
    wait_and_click("//*[text()='Download']")  # Download button

    wait_and_click('//div[contains(text(),"Stock")]')  # Stock watermark
    wait_and_click('//div[contains(text(),"Normal")]')  # Normal button
    # wait_and_click('//div[contains(text(),"1080")]')  # Quality button
    if version != "v3.0":
        wait_and_click('(//*[text()="Continue"])[2]')
    else:
        wait_and_click('(//*[text()="Continue"])')
        # Continue button

    # Keep the browser open
    print("Script completed. Browser will remain open.")
    try:
        while True:
            time.sleep(1)
            wait_for_download(get_downloads_folder())

            latest_file = get_latest_file(get_downloads_folder())
            if latest_file:
                print(f"Downloaded file: {latest_file}")
                public_url = upload_to_fileio(latest_file)
                print("Shareable public URL:", public_url)
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
    downloads_path = user_downloads_dir()
    return downloads_path


def upload_to_fileio(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post('https://file.io', files={'file': f})
    if response.ok:
        public_url = response.json()['link']
        print("Public URL:", public_url)
        return public_url
    else:
        raise Exception("Upload failed:", response.text)


def retry_click(xpath, max_attempts=3):
    attempts = 0
    while attempts < max_attempts:
        try:
            generate_video = wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            generate_video.click()
            print("Clicked successfully!")
            break
        except TimeoutException:
            print(f"Attempt {attempts + 1}: Timed out waiting for element. Retrying...")
            attempts += 1
    else:
        print("Failed to click after maximum attempts.")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://invideo.io/"
    message = sys.argv[2] if len(sys.argv) > 2 else "Cat on the moving train"
    run_selenium(url, message)
