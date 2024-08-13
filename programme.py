from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

url = "https://www.largus.fr/fiche-technique/Suzuki/Across/I/2020/Break+5+Portes/25+Hybride+Rechargeable-2387848.html"

chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--use_subprocess")

with uc.Chrome(options=chrome_options) as driver:
    driver.get(url)
    print("Page URL:", driver.current_url)
    print("Page Title:", driver.title)
    page_content = driver.page_source
    print(page_content)


