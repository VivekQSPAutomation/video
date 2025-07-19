import os
import random
import re
import sys
import time

import requests
from platformdirs import user_downloads_dir
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, \
    NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Initialize the Chrome driver
chrome_options = Options()

# Experimental options (including your download prefs)
chrome_options.add_experimental_option("prefs", {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
})
driver = webdriver.Chrome(options=chrome_options)


def run_selenium(url: str, prompt: str, message: str):
    driver.set_window_size(1382, 744)
    global wait
    wait = WebDriverWait(driver, 1200)

    # Open temp mail page
    while not (email := use_email()):
        driver.refresh()

    # Open target website
    driver.execute_script("window.open('', '_blank');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(url)

    # Click "Sign up"
    wait_and_click("(//*[contains(text(),'Create')])[1]")

    # Click on the login button
    wait_and_click("//button[text()='Log In']")

    # Signup button
    wait_and_click("//*[contains(text(),'Sign Up')]")

    # Email
    wait_and_sendkeys("//div[@class='signup-email']//input", message=email)

    wait_and_sendkeys("//div[@class='signup-password']//input", message="Hemraj@5")

    wait_and_sendkeys("//div[@class='signup-confirm']//input", message="Hemraj@5")

    wait_and_click("//button[@class='signup-verification-button']")

    # Wait for OTP email
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(20)
    otp_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class,'message__body')]")))
    otp_text = otp_element.text
    otp_match = re.search(r"\d+", otp_text)
    otp = otp_match.group() if otp_match else ""
    print("Extracted OTP:", otp)

    if not otp:
        print("Failed to extract OTP.")
        return  # No quit, to keep the browser open

    # Enter OTP
    driver.switch_to.window(driver.window_handles[1])
    wait_and_sendkeys("//div[@class='signup-verification']//input", message=otp)

    wait_and_click("//*[contains(text(),'Continue')]")
    wait_and_click("//div[@class='index-header']//*[contains(text(),'Story ')]")
    if wait_for_presence("//button[text()='Got It']"):
        wait_and_click("//button[text()='Got It']", retry_delay=4)
        wait_and_click("//*[@class='hotSellingTemplate-drawerCloseInon']", retry_delay=4)
    wait_and_click("//*[contains(text(),'Portrait')]/../../..")
    wait_and_click("//*[@class='arco-select-view-icon']")
    wait_and_click("//li[contains(@class, 'arco-select-option') and .//div[text()='हिन्दी']]")
    wait_and_click(f"(//*[@class='box-icon'])[{random.randint(a=1, b=18)}]")
    quotes = get_random_quote()
    wait_and_sendkeys("//textarea[contains(@placeholder,'Supports')]", quotes + " Create a kids Story on it",
                      with_clear=True)
    wait_and_click("(//*[contains(@class,'starter-right-buttom-left-list-item')])[1]")
    wait_and_click("//button[text()='Next']", retry_delay=5)
    wait_and_click("//button[text()='Next']", retry_delay=20)
    wait_and_click("//*[contains(text(),'Auto-Cast')]", retry_delay=8)
    wait_and_click("//button[text()='Next']", retry_delay=10)
    wait_until_absent("//*[@class='card-state-text']")
    wait_and_click("//button[text()='Next']", retry_delay=10)
    wait_and_click("//div[@class='arco-modal']//*[text()='Next']", retry_delay=6)
    wait_and_click("//div[@class='header-right']//*[text()='Generate']", retry_delay=5)
    if wait_for_presence("//div[text()='9:16']/parent::*"):
        wait_and_click("//div[text()='9:16']/parent::*")
        wait_and_click("(//div[@class='arco-modal']//button[text()='Ok'])[1]", retry_delay=10)
    wait_until_absent("//div[contains(text(),'Exiting')]")
    time.sleep(5)
    if wait_for_presence("//div[@class='arco-modal']//button[text()='Submit']"):
        wait_and_click("//button[text()='Submit']", retry_delay=5)
    wait_and_click("(//div[@class='confirm-modal confirm-modal--dark']//*[text()='Cancel'])[1]", retry_delay=10)
    wait_hover_and_click("//*[contains(@class,'header-action') and text()='Download']",
                         "(//div[@class='arco-trigger-popup-wrapper']//descendant::*//li//span)[1]")

    while True:
        time.sleep(1)
        wait_for_download(get_downloads_folder())
        latest_file = get_latest_file(get_downloads_folder())
        if latest_file:
            print(f"Downloaded file: {latest_file}")
            file = latest_file.replace('\\', "/")
            VideoPost(app_key="magiclight").upload_to_both(message=message, video_file=file)
            return True
        else:
            return False


def wait_until_absent(xpath):
    if not driver.find_elements("xpath", xpath):
        return False
    time.sleep(1)
    return wait_until_absent(xpath)


def use_email():
    driver.get("https://temp-mail.io/en")
    time.sleep(20)
    email_input = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='email']")))
    email = email_input.get_attribute('value')
    return email


def get_random_quote():
    url = "https://zenquotes.io/api/random"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        quote = data[0]['q']
        return quote

    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


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
def wait_and_click(xpath, timeout=12000, retries=3, retry_delay=2):
    element = wait_until_element(xpath, timeout)

    for attempt in range(retries):
        try:
            element.click()
            return  # success
        except ElementClickInterceptedException:
            if attempt < retries - 1:
                time.sleep(retry_delay)  # wait before retrying
            else:
                raise
        finally:
            time.sleep(retry_delay)


def wait_and_mouse_click(driver, xpath, timeout=30, retry_delay=5):
    """Waits for the element and performs a mouse (left) click via ActionChains."""
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            element = WebDriverWait(driver, retry_delay).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            ActionChains(driver).move_to_element(element).click().perform()
            return True  # Click successful
        except Exception as e:
            print(f"Retrying click on {xpath} due to: {e}")
            time.sleep(retry_delay)

    raise TimeoutError(f"Element with XPath {xpath} not clickable after {timeout} seconds.")


def wait_hover_and_click(hover_xpath, click_xpath, timeout=12000, retries=3, retry_delay=2):
    hover_element = wait_until_element(hover_xpath, timeout)

    for attempt in range(retries):
        try:
            # Hover over the element
            ActionChains(driver).move_to_element(hover_element).perform()
            time.sleep(1)  # slight delay to allow hover-triggered elements to appear

            # Wait and find the clickable element
            click_element = wait_until_element(click_xpath, timeout)
            ActionChains(driver).move_to_element(click_element).click().perform()
            return  # success
        except (ElementClickInterceptedException, ElementNotInteractableException, NoSuchElementException):
            if attempt < retries - 1:
                time.sleep(retry_delay)
            else:
                raise


def wait_and_sendkeys(xpath, message, timeout=12000, with_clear=False):
    element = wait_until_element(xpath, timeout)
    if with_clear:
        element.clear()
    element.send_keys(message)


def wait_and_get_message(xpath, timeout=12000):
    element = wait_until_element(xpath, timeout)
    return element.text


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

    def __init__(self, app_key=None):
        try:
            response = requests.get(f"https://vivek05novvv.pythonanywhere.com/data?app_key={app_key}")
            response.raise_for_status()
            data = response.json()
            print(data)
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
        url = f"https://graph-video.facebook.com/v23.0/{self.facebook_page}/videos"

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
        for attempt in range(50):  # Poll up to 10 times (adjust as needed)
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
        print("[*] Getting Facebook video URL...", video_id)
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
    url = sys.argv[1] if len(sys.argv) > 1 else "https://magiclight.ai/"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Make 15 seconds promotional video for the Cat on the moving train"
    message = sys.argv[3] if len(sys.argv) > 3 else " Make 15 seconds promotional video for the Cat on the moving train"
    run_selenium(url, prompt, message)
