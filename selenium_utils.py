# selenium_utils.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import os
import logging
from config import CONFIG

logger = logging.getLogger(__name__)
SCREENSHOT_PATH = "screenshot.png"
SELENIUM_TIMEOUT = 30  # Таймаут ожидания загрузки элементов


def make_confluence_screenshot():
    """
    Делает скриншот целевой страницы Confluence (из конфига)
    """
    logger.info("📸 Делаю скриншот календаря...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.delete_all_cookies()
        logger.info("🌐 Переходим на страницу входа в Confluence")
        driver.get(CONFIG["CONFLUENCE"]["LOGIN_URL"])

        logger.info("⏳ Ждём поля ввода логина")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "os_username"))
        ).send_keys(CONFIG["CONFLUENCE"]["USERNAME"])
        driver.find_element(By.ID, "os_password").send_keys(CONFIG["CONFLUENCE"]["PASSWORD"])
        driver.find_element(By.ID, "loginButton").click()

        logger.info("⏳ Ждём загрузки главной страницы")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        logger.info(f"🌐 Открываем целевую страницу: {CONFIG['CONFLUENCE']['TARGET_URL']}")
        driver.get(CONFIG["CONFLUENCE"]["TARGET_URL"])

        logger.info("⏳ Ждём завершения загрузки страницы")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        current_url = driver.current_url
        logger.info(f"🌐 Загружена страница: {current_url}")

        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)

        logger.info(f"📷 Сохраняем скриншот в: {os.path.abspath(SCREENSHOT_PATH)}")
        success = driver.save_screenshot(SCREENSHOT_PATH)

        if success:
            logger.info("✅ Скриншот успешно создан")
        else:
            logger.error("❌ Не удалось сохранить скриншот")
        return success

    except Exception as e:
        logger.error(f"🚨 Ошибка создания скриншота Confluence: {str(e)}", exc_info=True)
        return False

    finally:
        try:
            driver.quit()
            logger.info("🛑 Закрыли драйвер Selenium")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось корректно завершить драйвер: {str(e)}")


def make_jira_screenshot(jira_url: str):
    """
    Делает скриншот по ссылке в JIRA
    """
    logger.info(f"📸 Начинаем создание скриншота JIRA: {jira_url}")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        logger.info("🌐 Переходим на страницу входа в JIRA")
        driver.get(CONFIG["JIRA"]["LOGIN_URL"])

        logger.info("⏳ Ждём поля логина")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "login-form-username"))
        ).send_keys(CONFIG["JIRA"]["USERNAME"])
        driver.find_element(By.ID, "login-form-password").send_keys(CONFIG["JIRA"]["PASSWORD"])
        driver.find_element(By.ID, "login-form-submit").click()

        logger.info("⏳ Ждём загрузки главной страницы JIRA")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        logger.info(f"🌐 Открываем задачу: {jira_url}")
        driver.get(jira_url)

        logger.info("⏳ Ждём загрузки тела страницы")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)

        logger.info(f"📷 Сохраняем скриншот в: {os.path.abspath(SCREENSHOT_PATH)}")
        success = driver.save_screenshot(SCREENSHOT_PATH)

        if success:
            logger.info("✅ Скриншот успешно создан")
        else:
            logger.error("❌ Не удалось сохранить скриншот")
        return success

    except Exception as e:
        logger.error(f"🚨 Ошибка создания скриншота JIRA: {str(e)}", exc_info=True)
        return False

    finally:
        try:
            driver.quit()
            logger.info("🛑 Закрыли драйвер Selenium")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось корректно завершить драйвер: {str(e)}")


def make_confluence_screenshot_page(confluence_url: str):
    """
    Делает скриншот по произвольной ссылке в Confluence
    """
    logger.info(f"📸 Начинаем создание скриншота Confluence: {confluence_url}")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.delete_all_cookies()
        logger.info("🌐 Переходим на страницу входа в Confluence")
        driver.get(CONFIG["CONFLUENCE"]["LOGIN_URL"])

        logger.info("⏳ Ждём поля ввода логина")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "os_username"))
        ).send_keys(CONFIG["CONFLUENCE"]["USERNAME"])
        driver.find_element(By.ID, "os_password").send_keys(CONFIG["CONFLUENCE"]["PASSWORD"])
        driver.find_element(By.ID, "loginButton").click()

        logger.info("⏳ Ждём загрузки главной страницы")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        logger.info(f"🌐 Открываем страницу: {confluence_url}")
        driver.get(confluence_url)

        logger.info("⏳ Ждём загрузки тела страницы")
        WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height)

        logger.info(f"📷 Сохраняем скриншот в: {os.path.abspath(SCREENSHOT_PATH)}")
        success = driver.save_screenshot(SCREENSHOT_PATH)

        if success:
            logger.info("✅ Скриншот успешно создан")
        else:
            logger.error("❌ Не удалось сохранить скриншот")
        return success

    except Exception as e:
        logger.error(f"🚨 Ошибка создания скриншота Confluence: {str(e)}", exc_info=True)
        return False

    finally:
        try:
            driver.quit()
            logger.info("🛑 Закрыли драйвер Selenium")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось корректно завершить драйвер: {str(e)}")