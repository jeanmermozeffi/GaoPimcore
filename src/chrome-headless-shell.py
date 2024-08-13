import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configurer les options de Chrome pour le mode sans tête
chrome_options = Options()
chrome_options.binary_location = "/path/to/chrome-headless-shell"  # Chemin vers chrome-headless-shell
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver_path = os.getenv('DRIVER_PATH')

# Vérifier si la variable est définie
if driver_path is None:
    raise EnvironmentError("La variable d'environnement DRIVER_PATH n'est pas définie.")

#
# # Créer une instance de WebDriver
# driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
#
# # Naviguer vers la page cible
# url = "https://www.largus.fr/fiche-technique/Bmw/Serie+5/Vi+G30/2024/Berline+4+Portes/518da+150+Bus+Design+Steptro-2396970.html"
# driver.get(url)
#
# # Attendre que la page se charge complètement
# time.sleep(5)
#
# # Extraire les informations désirées
# try:
#     # Exemple pour extraire le titre de la page
#     title = driver.title
#     print(f"Title: {title}")
#
#     # Exemple pour extraire d'autres éléments, comme les spécifications techniques
#     # Note: Vous devrez ajuster les sélecteurs en fonction de la structure HTML réelle de la page
#     spec_elements = driver.find_elements(By.CLASS_NAME, 'technical-spec')
#     for elem in spec_elements:
#         print(elem.text)
# finally:
#     # Fermer le navigateur
#     driver.quit()
