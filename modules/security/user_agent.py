import time

import requests
from random import randint

from selenium import webdriver
# from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
service = Service()
options.headless = True

SCRAPEOPS_API_KEY = '1cdf4aa4-55a5-4534-bfcf-aa6872a9e7da'


def get_headers_list():
    response = requests.get('http://headers.scrapeops.io/v1/browser-headers?api_key=' + SCRAPEOPS_API_KEY)
    json_response = response.json()
    return json_response.get('result', [])


def get_user_agent_list():
    response = requests.get('http://headers.scrapeops.io/v1/user-agents?api_key=' + SCRAPEOPS_API_KEY)
    json_response = response.json()
    return json_response.get('result', [])


def get_random_header(header_list):
    random_index = randint(0, len(header_list) - 1)
    return header_list[random_index]


def interceptor():
    # header_lists = get_headers_list()
    user_agent_lists = get_user_agent_list()
    return get_random_header(user_agent_lists)


def get_driver():
    headers = interceptor()
    try:
        print('Initializing driver...')
        options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
        options.add_argument('--user-agent=%s' % headers)
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--start-fullscreen')
        drive = webdriver.Chrome(service=service, options=options)
        # Définir les headers pour toutes les requêtes
        # for request in driver.requests:
        #     request.headers.update(headers)
        # drive.request_interceptor = interceptor
        return drive
    except Exception as e:
        print(f"Erreur lors de la création du driver: {e}")
        return None, None


if __name__ == '__main__':
    driver = get_driver()
    if driver is not None:
        driver.get("https://www.whatismybrowser.com/")
        time.sleep(2)

        user_agent_actuel = driver.execute_script("return navigator.userAgent;")
        print("User Agent actuel :", user_agent_actuel)

        driver.quit()
    else:
        print("Le driver n'a pas pu être initialisé.")





