from configparser import ConfigParser
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import subprocess
import logging
import time
import json
import os

from src.download_chrome_driver import ChromeDownloader
from webdriver_manager.chrome import ChromeDriverManager

parser = ArgumentParser()
parser.add_argument(
    '-c', '--conf', default=os.path.join('conf', 'config.ini'), help='設定檔路徑')
parser.add_argument(
    '-l', '--log_level', type=str,
    help='設定紀錄log等級',
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    default='INFO'
)
args = parser.parse_args()

logger = logging.getLogger('Get_YT_Cookies')
logger.setLevel(args.log_level)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


conf = ConfigParser()
conf.read(args.conf)

EMAIL = conf.get('YOUTUBE', 'EMAIL')
PASSWORD = conf.get('YOUTUBE', 'PASSWORD')
LOGIN_PAGE = (
    conf.get('YOUTUBE', 'LOGIN_PAGE')
    if conf.has_option('YOUTUBE', 'LOGIN_PAGE')
    else 'https://accounts.google.com/ServiceLogin?service=youtube'
)
CHROME_VERSION = conf.get('YOUTUBE', 'CHROME_VERSION')


def check_chromedriver_installed():
    """檢查系統中是否已安裝 ChromeDriver"""
    try:
        # 檢查 chromedriver 是否在系統路徑中
        result = subprocess.run(
            ['which', 'chromedriver'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.stdout.strip():
            logger.info(f"ChromeDriver 已安裝於: {result.stdout.strip()}")
            return True
        else:
            logger.info("ChromeDriver 未安裝或不在系統路徑中。")
            return False
    except Exception as e:
        logger.error(f"檢查 ChromeDriver 時發生錯誤: {e}")
        return False


def get_youtube_cookies():
    # 設置 Chrome 無頭模式
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 確保 ChromeDriver 已安裝並且正確設置 Service
    driver_service = Service(ChromeDriverManager().install())

    # 啟動 ChromeDriver
    driver = webdriver.Chrome(service=driver_service, options=chrome_options)

    # 開啟 YouTube 登入頁面
    driver.get(LOGIN_PAGE)

    # 自動化登入
    # 輸入 Google 帳號
    email_input = driver.find_element(By.ID, "identifierId")
    email_input.send_keys(EMAIL)
    driver.find_element(By.ID, "identifierNext").click()

    time.sleep(5)  # 等待頁面加載

    # 輸入密碼
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(PASSWORD)
    driver.find_element(By.ID, "passwordNext").click()

    # 等待登入完成
    time.sleep(10)

    # 取得 Cookies
    cookies = driver.get_cookies()
    logger.debug(f'cookies: {cookies}')

    # 保存 Cookies 為 JSON 文件
    with open("youtube_cookies.json", "w") as file:
        json.dump(cookies, file)

    driver.quit()


def convert_cookies_to_txt():
    with open("youtube_cookies.json", "r") as json_file:
        cookies = json.load(json_file)

    with open("cookies.txt", "w") as txt_file:
        for cookie in cookies:
            txt_file.write(
                f"{cookie['domain']}\tTRUE\t{cookie['path']}\tFALSE\t{cookie['expiry']}\t{cookie['name']}\t{cookie['value']}\n")


if __name__ == "__main__":
    get_youtube_cookies()
    logger.info("Cookies 已保存到 youtube_cookies.json")
    convert_cookies_to_txt()
