import os
import re
import sys
import time

import requests
from platformdirs import user_downloads_dir
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Chrome()


def run_selenium(url: str, prompt: str, message: str):
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
    print(version)

    generate_video(prompt)

    # Interact with elements using the new method
    # Submit button
    if version != "v3.0":
        while True:
            if wait_for_presence("//*[contains(text(),'credits')]"):
                wait_and_click("//p[text()='Create New']/parent::*/parent::a")
                generate_video(prompt)
                if wait_for_presence("//button[.//text()[contains(., 'Stock')]]"):
                    break
            else:
                break

        wait_and_click("//*[contains(text(),'Continue')]")
        wait_and_click("//*[contains(text(),'Continue')]")
        wait_and_click("(//*[contains(text(),'Edit & Download')])[2]")
        # wait_and_click("//*[contains(text(),'Continue')]")
        # wait_and_click("(//*[contains(text(),'Continue')])[2]")
        # wait_and_click("(//*[contains(text(),'Continue')])[2]")
    else:
        wait_and_click('//div[contains(text(),"Stock")]')
        # wait_and_click('//button[contains(@value,"1.0")]')
        wait_and_click("//*[contains(text(),'Continue')]")
        # continue button
    wait_and_click("//*[text()='Download']")  # Download button

    wait_and_click('//div[contains(text(),"Stock")]')  # Stock watermark
    wait_and_click('//div[contains(text(),"Normal")]')  # Normal button
    wait_and_click('//button[@value="480"]')  # Quality button
    if version != "v3.0":
        wait_and_click('(//*[contains(text(), "Continue")])[3]')
    else:
        wait_and_click('(//*[contains(text(), "Continue")])')
        # Continue button

    # Keep the browser open
    print("Script completed. Browser will remain open.")
    while True:
        time.sleep(1)
        wait_for_download(get_downloads_folder())
        latest_file = get_latest_file(get_downloads_folder())
        if latest_file:
            print(f"Downloaded file: {latest_file}")
            file = latest_file.replace('\\', "/")
            VideoPost().upload_to_both(message=message, video_file=file)
            return True
        else:
            return False


def generate_video(message):
    wait_and_sendkeys("//textarea[@name='brief']", message)
    wait_and_click("//*[contains(text(), 'Generate')]")


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


def is_element_present(xpath, timeout=99, poll_frequency=1):
    """Check if an element is present within the specified timeout."""
    start_time = time.time()
    while True:
        try:
            element = driver.find_element(By.XPATH, xpath)
            return True  # Element found
        except NoSuchElementException:
            if time.time() - start_time > timeout:
                return False  # Timeout reached, element not found
            time.sleep(poll_frequency)


# Function to check for element and click it
def wait_and_click(xpath, timeout=12000):
    element = wait_until_element(xpath, timeout)
    element.click()


def wait_and_sendkeys(xpath, message, timeout=12000):
    element = wait_until_element(xpath, timeout)
    element.send_keys(message)


def wait_for_presence(xpath, timeout=150):
    element = is_element_present(xpath, timeout=timeout)
    return element


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


class VideoContent:
    def __init__(self, blog_name, blog_description, blog_image, created_at, status, video_url):
        self.blog_name = blog_name
        self.blog_description = blog_description
        self.blog_image = blog_image
        self.created_at = created_at
        self.status = status
        self.video_url = video_url


class VideoPost:

    def __init__(self):
        try:
            response = requests.get("https://vivek05novvv.pythonanywhere.com/data")
            response.raise_for_status()
            data = response.json()

            self.facebook_page = data.get('facebook_page')
            self.insta_page = data.get('insta_page')
            self.page_access_token = data.get('page_access_token')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            self.facebook_page = None
            self.insta_page = None
            self.page_access_token = None

    def upload_to_facebook(self, video_file=None):
        """Uploads video to Facebook Page."""
        url = f"https://graph-video.facebook.com/v21.0/{self.facebook_page}/videos"

        if video_file:
            with open(video_file, 'rb') as video:
                files = {'file': video}
                payload = {
                    "access_token": self.page_access_token
                }
                response = requests.post(url, files=files, data=payload)

                if response.status_code == 200:
                    print("Facebook video uploaded successfully.")
                    res = response.json().get("id")
                    time.sleep(15)
                    return self.get_facebook_video_url(res), True
                else:
                    print("Facebook upload failed:", response.text)
                    return response.text

    def upload_to_instagram(self, message, video_file=None):
        """Uploads video to Instagram and ensures it's ready before publishing."""
        upload_url = f"https://graph.facebook.com/v21.0/{self.insta_page}/media"

        upload_payload = {
            "access_token": self.page_access_token,
            "media_type": "REELS",
            "video_url": video_file,
            "caption": message
        }

        # Step 1: Upload video data to Instagram
        upload_response = requests.post(upload_url, data=upload_payload)
        upload_data = upload_response.json()

        if 'id' not in upload_data:
            print("Instagram upload failed:", upload_response.text)
            return None

        media_id = upload_data['id']
        print("Instagram media uploaded. Media ID:", media_id)

        # Step 2: Poll for media processing status
        status_url = f"https://graph.facebook.com/v21.0/{media_id}"
        for attempt in range(10):  # Poll up to 10 times (adjust as needed)
            time.sleep(5)  # Wait before each poll
            status_response = requests.get(status_url, params={
                "access_token": self.page_access_token,
                "fields": "status"
            })
            status_data = status_response.json()
            if 'status' in status_data:
                processing_status = status_data['status']
                print(f"Attempt {attempt + 1}: Media status - {processing_status}")
                if 'Finished' in processing_status:
                    break
                elif processing_status == 'ERROR':
                    print("Instagram media processing failed:", status_data)
                    return False
            else:
                print("Error fetching media status:", status_data)
                return False
        else:
            print("Media processing timed out.")
            return False

            # Step 3: Publish the uploaded media
        publish_url = f"https://graph.facebook.com/v21.0/{self.insta_page}/media_publish"
        publish_payload = {
            "access_token": self.page_access_token,
            "creation_id": media_id
        }
        publish_response = requests.post(publish_url, data=publish_payload)
        if publish_response.status_code == 200:
            print("Video published on Instagram successfully.")
            return True
        else:
            print("Instagram publishing failed:", publish_response.text)
            return False

    def get_facebook_video_url(self, video_id):
        print("[*] Getting Facebook video URL...")
        url = f"https://graph.facebook.com/v21.0/{video_id}?fields=permalink_url,source&access_token={self.page_access_token}"
        response = requests.get(url)
        res_json = response.json()

        video_url = res_json.get('source')  # Direct .mp4 URL
        if not video_url:
            raise Exception("Video source URL not found.")

        print(f"[+] Facebook video URL: {video_url}")
        return video_url

    def upload_to_both(self, message, video_file):
        """Uploads video to both Facebook and Instagram."""
        video_url, facebook_result = self.upload_to_facebook(video_file)
        if facebook_result:
            instagram_result = self.upload_to_instagram(message, video_url)
            return instagram_result
        else:
            return False


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://invideo.io/"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Enter a prompt for the video"
    message = sys.argv[3] if len(sys.argv) > 3 else " Make 15 seconds promotional video for the Cat on the moving train"
    run_selenium(url, prompt, message)
