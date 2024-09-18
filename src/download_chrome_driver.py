import os
import re
import requests
import zipfile
import shutil
import logging


class ChromeDownloader:

    def __init__(self, log_level="DEBUG") -> None:
        """_summary_

        Args:
            log_level (str, optional): 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'. Defaults to "DEBUG".
        """

        self.logger = logging.getLogger('ChromeDownloader')
        self.logger.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.version = None

    def set_chromium_version(self, version: str):
        self.version = version

    def get_specific_chromedriver_version(self, chrome_major_version):
        """根據 Chrome 主版本號檢查是否存在對應的 ChromeDriver"""
        try:
            url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_major_version}"
            response = requests.get(url)

            if response.status_code == 200:
                version = response.text.strip()
                self.logger.info(f"找到與 Chrome {chrome_major_version} 對應的 ChromeDriver 版本: {version}")
                return version
            else:
                self.logger.info(f"未找到與 Chrome {chrome_major_version} 對應的 ChromeDriver 版本。")
                return None
        except Exception as e:
            self.logger.error(f"錯誤: {e}")
            return None

    def get_chromium_version_by_chromium_browser(self):
        """自動檢測 Chromium/Chrome 的版本"""
        try:
            version_output = os.popen("chromium-browser --version").read().strip()
            version = re.search(r"(\d+\.\d+\.\d+\.\d+)", version_output).group(1)
            self.logger.info(f"Chromium version: {self.version}")
            self.version = version
            return self.version
        except Exception as e:
            self.logger.error(f"Error detecting Chromium version: {e}")
            return None

    def download_driver(self, version):
        """根據 Chromium/Chrome 版本下載對應的 ChromeDriver"""
        major_version = version.split('.')[0]  # 提取主版本號
        driver_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"

        try:
            # 獲取對應版本的 ChromeDriver 版本號
            driver_version = requests.get(driver_url).text.strip()
            self.logger.info(f"ChromeDriver version: {driver_version}")

            # 下載對應的 ChromeDriver
            download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_linux64.zip"
            self.logger.info(f"Downloading ChromeDriver from: {download_url}")
            driver_zip_path = "chromedriver_linux64.zip"

            response = requests.get(download_url)
            with open(driver_zip_path, 'wb') as file:
                file.write(response.content)

            self.logger.info("Download complete.")
            return driver_zip_path
        except Exception as e:
            self.logger.error(f"Error downloading ChromeDriver: {e}")
            return None

    def install_driver(self, zip_path):
        """解壓並安裝 ChromeDriver"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("chromedriver")
            shutil.move("chromedriver/chromedriver", "/usr/local/bin/chromedriver")
            os.chmod("/usr/local/bin/chromedriver", 0o755)  # 設置可執行權限
            self.logger.info("ChromeDriver successfully installed.")
        except Exception as e:
            self.logger.error(f"Error installing ChromeDriver: {e}")

    def main(self):
        # 步驟 1: 自動偵測 Chromium/Chrome 版本
        if self.version == None:
            version = self.get_chromium_version_by_chromium_browser()

            if not version:
                self.logger.error("Could not detect Chromium version. Exiting.")
                return
            else:
                self.set_chromium_version(version)

        version = self.get_specific_chromedriver_version(self.version)

        # 步驟 2: 根據版本下載相應的 ChromeDriver
        zip_path = self.download_driver(version)
        if not zip_path:
            self.logger.error("Failed to download ChromeDriver. Exiting.")
            return

        # 步驟 3: 安裝 ChromeDriver
        self.install_driver(zip_path)

        # 清理下載的 ZIP 文件
        os.remove(zip_path)
        shutil.rmtree("chromedriver", ignore_errors=True)
