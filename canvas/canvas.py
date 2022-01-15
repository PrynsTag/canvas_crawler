import os
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from canvas import constant as const

BASE_DIR = Path(__file__).resolve().parent.parent
env_file = os.path.join(BASE_DIR, ".env")
load_dotenv(env_file)


class Canvas(webdriver.Chrome):
    def __init__(self):
        self.docs_dir = Path.home() / "Documents"
        self.wait = WebDriverWait(self, 1.5)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--verbose")
        chrome_options.add_argument("--keep-alive-for-test")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(self.docs_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing_for_trusted_sources_enabled": False,
                "safebrowsing.enabled": True,
            },
        )
        chrome_options.add_experimental_option("detach", True)  # Doesn't work.
        super().__init__(
            options=chrome_options,
            executable_path=ChromeDriverManager().install(),
        )
        self.maximize_window()
        self.courses = []

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def get_first_page(self):
        self.get(const.BASE_URL)

    def login(self):
        email_input = self.find_element(By.ID, "i0116")
        email_input.send_keys(os.getenv("EMAIL"))

        submit_btn = self.find_element(By.ID, "idSIButton9")
        submit_btn.click()

        password_input = self.find_element(By.ID, "i0118")
        password_input.send_keys(os.getenv("PASSWORD"))

        self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[value="Sign in"]'))
        ).click()

        confirm_btn = self.find_element(By.CSS_SELECTOR, 'input[value="Yes"]')
        confirm_btn.click()

    def get_course_links(self):
        course_links = self.find_elements(By.CLASS_NAME, "ic-DashboardCard__link")
        for course in course_links:
            self.courses.append(course.get_attribute("href"))

    def get_course_materials(self):
        for course in self.courses:
            self.get(f"{course}/modules")
            course_material_links = self.find_element(
                By.CSS_SELECTOR, "div.module-item-title > span > a"
            )
            self.get(course_material_links.get_attribute("href"))

            while True:
                self.download_files()
                self.download_videos()

                # Check course material is locked
                try:
                    self.wait.until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "lock_explanation")
                        )
                    )
                    break
                except NoSuchElementException:
                    pass
                except TimeoutException:
                    pass

                # Check next button is present.
                try:
                    self.wait.until(
                        EC.element_to_be_clickable((By.LINK_TEXT, "Next"))
                    ).click()
                except NoSuchElementException:
                    break
                except TimeoutException:
                    break

    def download_files(self):
        try:
            files_to_download = self.wait.until(
                EC.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR, 'a[download="true"], a.file_download_btn')
                )
            )

            for file in files_to_download:
                if file.is_displayed():
                    file.click()
                    time.sleep(0.5)
        except NoSuchElementException:
            pass
        except TimeoutException:
            pass

    def download_videos(self):
        try:
            video_link = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "#wiki_page_show > div.show-content.user_content.clearfix.enhanced > p > iframe",
                    )
                )
            ).get_attribute("src")
            video_id = video_link.split("/")[-2]

            download_url = f"https://drive.google.com/uc?id={video_id}&export=download"
            self.get(download_url)

            download_btn = self.find_element(By.ID, "uc-download-link")
            download_btn.click()

            self.back()
        except NoSuchElementException:
            pass
        except TimeoutException:
            pass
