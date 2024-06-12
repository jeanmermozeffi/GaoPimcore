import requests
import os
import re
import time
from datetime import datetime
import unidecode
import uuid

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

import pandas as pd
from pandas.errors import EmptyDataError
import numpy as np


class Largus:
    def __init__(self):
        pass

    @staticmethod
    def click_accept_cookies(driver):
        try:
            # Attendre que le pop-up des cookies soit présent
            cookie_popup = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'didomi-popup-view'))
            )

            # Trouver et cliquer sur le bouton "Accepter"
            accept_button = cookie_popup.find_element(By.ID, 'didomi-notice-agree-button')
            accept_button.click()
            print("Bouton 'Accepter' des cookies cliqué avec succès.")

        except Exception as e:
            print(f"Erreur lors du clic sur le bouton 'Accepter'")

    @staticmethod
    def detect_captcha(driver):
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        iframe = soup.find('iframe')
        if iframe is not None:
            # Obtenir la valeur de l'attribut src de l'iframe
            src = iframe.get('src')
            if src is not None:
                # Vérifier si l'attribut src commence par le lien spécifique du captcha
                if src.startswith('https://geo.captcha-delivery.com/captcha/?initialCid='):
                    return True
        # Retourner False si aucun iframe n'est trouvé ou si l'attribut src ne commence pas par le lien spécifique
        return False

    @staticmethod
    def download_image(url, folder_path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(folder_path, 'wb') as f:
                f.write(response.content)
            print(f"Image téléchargée avec succès: {folder_path}")
        else:
            print(f"Échec du téléchargement de l'image depuis l'URL: {url}")

    @staticmethod
    def load_and_concatenate_csvs(folder_path):
        """
         Chargez tous les fichiers CSV dans le dossier spécifié et concaténez-les dans un seul DataFrame.

         Paramètres:
         dossier_path (str): Le chemin d'accès au dossier contenant les fichiers CSV.

         Retour:
         pd.DataFrame : Le DataFrame concaténé contenant toutes les données des fichiers CSV.
        """

        dataframes = []

        # Parcourir tous les fichiers dans le dossier et les sous-dossiers
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                if filename.endswith('.csv'):
                    file_path = os.path.join(root, filename)
                    # Lire le fichier CSV et l'ajouter à la liste des DataFrames
                    _df = pd.read_csv(file_path)
                    dataframes.append(_df)

        # Concaténer tous les DataFrames en un seul
        final_df = pd.concat(dataframes, ignore_index=True)
        return final_df

    @staticmethod
    def get_driver():
        chrome_option = Options()
        headless = True
        chrome_option.binary_location = '/Applications/Brave Browser.app'
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_option)

        return driver

    @staticmethod
    def extract_vehicle_info(driver):
        # Trouver tous les éléments de produit
        try:
            products_elements = driver.find_elements(By.CSS_SELECTOR, 'a.product-wrap')
            if not products_elements:
                print("No product elements found.")
                return []
        except NoSuchElementException:
            print("Error finding product elements.")
            return []

        vehicles = []

        # Extraire les informations pour chaque véhicule
        for element in products_elements:
            try:
                vehicle_url = element.get_attribute('href')
                vehicle_model = element.get_attribute('data-model')
                vehicle_make = element.get_attribute('data-make')
                vehicle_title = element.find_element(By.CSS_SELECTOR, 'span.product-title').text

                # Add extracted information to the list
                vehicles.append({
                    'url': vehicle_url,
                    'model': vehicle_model,
                    'make': vehicle_make,
                    'title': vehicle_title
                })
            except NoSuchElementException as e:
                print(f"Error extracting data from element: {e}")
                continue

        return vehicles

    @staticmethod
    def save_vehicles_to_csv(vehicles):
        if vehicles:
            folder = "Modeles"
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"Folder created at {folder}")

            file_name = f"{vehicles[0]['make']}.csv"
            save_path = os.path.join(folder, file_name)
            pd.DataFrame(vehicles).to_csv(save_path, index=False)
            print(f"Data saved to {save_path}")

    def scrape_multiple_urls(self, driver, url):
        print(f"Scraping URL: {url}")
        driver.get(url)

        vehicles_info = self.extract_vehicle_info(driver)

        if vehicles_info:
            self.save_vehicles_to_csv(vehicles_info)

    @staticmethod
    def process_links(driver, dataframe):
        filtered_df = dataframe[dataframe['Traiter'] == 1]
        treated_links = set(filtered_df['lien_url'])  # Un ensemble pour stocker les liens déjà traités

        # Vérifier si la colonne Traiter existe déjà
        if 'Traiter' not in dataframe.columns:
            dataframe['Traiter'] = 0

        counter = 0
        for index, row in dataframe.iterrows():
            link_url = row['lien_url']
            # Vérifier si le lien a déjà été traité

            if link_url in treated_links:
                continue

            if link_url not in treated_links:
                scrape_multiple_urls(driver, link_url)
                dataframe.at[index, 'Traiter'] = 1
                treated_links.add(link_url)
                dataframe.to_json("marques.json", orient="records")
                counter += 1

                print(f"Waiting for 1 minute before the next URL...{counter}")
                time.sleep(1)

            if counter >= 50:
                print("Arrêt après 50 itérations.")
                break
        print(f"Arrêt toutes les liens, un total de {counter} ont été traitées !.")


class TechnicalSearch:
    def __init__(self):
        self.driver = None
        self.server = None
        self.service = Service()
        self.options = Options()
        self.base_url = 'https://www.largus.fr'
        self.largus = Largus()
        self.is_captcha_detected = False

        # Définir les en-têtes
        self.headers_chrome = headers_chrome_mac = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.6',
            'content-type': 'application/json',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="99", "Chromium";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Mac OS X"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-gpc': '1',
            'referrer': 'https://www.largus.fr',
            'referrerPolicy': 'strict-origin-when-cross-origin',
        }

    def start_driver(self):
        print('Initializing driver...')
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def get_driver(self):
        try:
            self.options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
            self.options.add_argument('--window-size=1920,1080')
            self.options.add_argument('--disable-extensions')
            # self.options.add_argument('--remote-debugging-port=9222')
            self.options.add_argument('--start-fullscreen')
            self.driver = webdriver.Chrome(service=self.service, options=self.options)
            return self.driver
        except Exception as e:
            print(f"Erreur lors de la création du driver: {e}")
            return None, None

    def close_driver(self):
        self.driver.quit()

    @staticmethod
    def extract_make_from_url(url):
        match = re.search(r'/fiche-technique/([^/]+)/', url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def sanitize_filename(filename):
        return re.sub(r'[\/:*?"<>|]', '_', filename)

    @staticmethod
    def extract_year_from_libelle(libelle):
        try:
            match = re.search(r'\b\d{4}\b', libelle)
            if match:
                return match.group(0)
            return None
        except Exception as e:
            print(f"Error extracting year from libelle: {e}")
            return None

    # Fonction pour extraire le lien "Toutes les fiches techniques"
    @staticmethod
    def extract_all_fiches_techniques_url(html_content):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            section = soup.select_one('section.stacking-block.section-fiches-techniques')

            if section:
                lien_tout = section.select_one('a.lien-tout')
                if lien_tout:
                    return lien_tout.get('href')
            return None
        except Exception as e:
            print(f"Error extracting 'lien-tout': {e}")
            return None

    # Fonction pour extraire les fiches techniques d'une page donnée
    def extract_fiches_techniques(self, url, model):
        try:
            self.driver.get(url)
            time.sleep(1)
            response = self.driver.page_source
        except Exception as e:
            print(f"Error fetching URL: {url}. Exception: {e}")
            return []

        try:
            soup = BeautifulSoup(response, 'html.parser')
            fiches = []
            marque = self.extract_make_from_url(url)
        except Exception as e:
            print(f"Error parsing HTML content from URL: {url}. Exception: {e}")
            return []

        try:
            for item in soup.select('ul.liste-millesimes li a.item'):
                try:
                    libelle = item.select_one('span.libelle').text.strip()
                    lien = item.get('href')
                    year = self.extract_year_from_libelle(libelle)
                    fiches.append({
                        'Libelle': libelle,
                        'Marque': marque,
                        'Model': model,
                        'Lien': f"https://www.largus.fr{lien}",
                        'Annee': year
                    })
                except AttributeError as e:
                    print(f"Error extracting data from an item: {e}")
        except Exception as e:
            print(f"Error processing items from URL: {url}. Exception: {e}")
            return []

        return fiches

    def process_all_fiches_techniques(self, html_content_fiche, model):
        all_urls = self.extract_all_fiches_techniques_url(html_content_fiche)

        if all_urls:
            # Compléter l'URL si nécessaire
            if not all_urls.startswith('http'):
                all_urls = f'https://www.largus.fr{all_urls}'

            # Extraire les fiches techniques de la page "Toutes les fiches techniques"
            fiches_techniques = self.extract_fiches_techniques(all_urls, model)

            if fiches_techniques:
                # Sauvegarder les fiches techniques dans un fichier CSV
                df_fiches_technique = pd.DataFrame(fiches_techniques)
                marque = df_fiches_technique['Marque'][0].capitalize()
                sanitized_marque = self.sanitize_filename(marque)
                folder_path = f"Data/Fiches Techniques/{sanitized_marque.capitalize()}"

                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    print(f"Répertoire créé à : {folder_path}")

                file_name = f"fiches_techniques_{marque.lower()}_{model.lower()}.csv"
                sanitized_file_name = self.sanitize_filename(file_name)
                save_path = os.path.join(folder_path, sanitized_file_name)
                # print(f"Sauvegarde du fichier à : {save_path}")
                df_fiches_technique.to_csv(save_path, index=False)
                return df_fiches_technique
            else:
                print("Aucune fiche technique trouvée.")
                return None
        else:
            print("Lien vers Toutes les fiches techniques non trouvé.")
            return None

    def process_fiche_technique_file_links(self, df_path="Data/all_models.csv", column="url"):
        dataframe = pd.read_csv(df_path)
        print(f"Données à traiter : {dataframe[dataframe['Traiter'] == 0].shape[0]}")

        if dataframe[dataframe['Traiter'] == 0].shape[0] == 0:
            print("Tout le fichier a été traitée !!!")
            return None

        if 'Traiter' not in dataframe.columns:
            dataframe['Traiter'] = 0

        filtered_df = dataframe[dataframe['Traiter'] == 1]
        treated_links_length = len(dataframe[dataframe['Traiter'] == 1])

        treated_links = set(filtered_df[column])

        counter = 0
        self.is_captcha_detected = False
        for index, row in dataframe[treated_links_length:].iterrows():
            link_url = row[column]
            model = row['model']
            make = row['make']

            if link_url in treated_links:
                continue

            try:
                self.driver.get(link_url)

                if self.largus.detect_captcha(self.driver):
                    self.is_captcha_detected = True
                    print("La page n'a pas pu être analysée. Il est possible qu'un captcha soit détecté.")
                    break

                if counter == 0:
                    self.largus.click_accept_cookies(self.driver)

                html_content_fiche = self.driver.page_source
                df_fiches_technique = self.process_all_fiches_techniques(html_content_fiche, model)

                if df_fiches_technique is None:
                    dataframe.drop(index, inplace=True)
                    dataframe.reset_index(drop=True, inplace=True)
                    dataframe.to_csv(df_path, index=False)
                    continue

                dataframe.at[index, 'Traiter'] = 1
                treated_links.update(link_url)

                counter += 1

                print(f"Waiting for 1 minute before the next URL...{counter}")
                time.sleep(1)

                save_file_path = f"Models/{make}.csv"
                save_file_path = unidecode.unidecode(save_file_path).strip().lower().replace(' ', '_').replace("'", "")
                dataframe.to_csv(df_path, index=False)
                if counter >= 25:
                    print(f"Arrêt après {counter} itérations.")
                    print(f"Données traitées et sauvegardées à {datetime.now().strftime('%H:%M:%S')}")
                    break
            except WebDriverException as e:
                print(f"Erreur lors de l'accès à {link_url}: {e}")
                continue

        if self.is_captcha_detected is not True:
            print(f"Arrêt toutes les liens, un total de {counter} liens ont été traitées !.")

    @staticmethod
    def process_create_fiche_technical(data, df_folder_path):
        columns = ['Libelle', 'Marque', 'Model', 'Lien', 'Annee']

        # Vérifier si le fichier existe et charger les données existantes, sinon créer un DataFrame vide
        if os.path.exists(df_folder_path):
            try:
                df_save = pd.read_csv(df_folder_path)
            except EmptyDataError:
                df_save = pd.DataFrame(columns=columns)
        else:
            df_save = pd.DataFrame(columns=columns)

        df_fiche = pd.DataFrame(data)

        # Concaténer le DataFrame original avec le nouveau DataFrame
        df_save = pd.concat([df_save, df_fiche], ignore_index=True)
        # Enregistrer le DataFrame concaténé dans le fichier CSV
        df_save.to_csv(df_folder_path, index=False)

        return df_save
 
    
class DataVersion:
    def __init__(self):
        self.largus = Largus()

    def extract_version_data(self, driver, url_version, html_content, df_rows):
        """
        Extract version data from a given URL and HTML content using Selenium and BeautifulSoup.

        Parameters:
        driver (WebDriver): The Selenium WebDriver instance.
        url_version (str): The URL containing the version information.
        html_content (str): The HTML content of the page.

        Returns:
        list: A list of lists containing version data.
        str: The filename for the CSV file.
        """
        # Extraire l'année de l'URL à l'aide d'une expression régulière
        match = re.search(r'/(\d{4})\.html', url_version)
        if match:
            year = match.group(1)
        else:
            year = datetime.now().year

        # Localiser la table
        table = driver.find_element(By.ID, 'listeVersions')

        if table is not None:
            # Extraire les lignes de la table
            rows = table.find_elements(By.TAG_NAME, 'tr')

            # Préparer une liste pour stocker les données
            data_versions = []
            mark = df_rows['Marque']
            model = df_rows['Model']

            # Boucler à travers les lignes pour extraire les données
            for row in rows[1:]:  # Ignorer l'en-tête
                cols = row.find_elements(By.TAG_NAME, 'td')
                if cols:
                    version = cols[0].text
                    version_link = cols[0].find_element(By.TAG_NAME, 'a').get_attribute('href')
                    carrosserie = cols[1].text
                    energy = cols[2].text
                    boite = cols[3].text
                    puissance_fiscale = cols[4].text
                    data_versions.append([version, carrosserie, energy, boite, puissance_fiscale, version_link, year, mark, model])

            # Déterminer le nom du fichier CSV
            if data_versions:
                soup = BeautifulSoup(html_content, "html.parser")
                title_tag = soup.find('h1', class_='title lvl1-title')
                if title_tag:
                    title_text = title_tag.text.strip().lower()
                    title_text = re.sub(r'\s+', '_', title_text)  # Remplacer les espaces par des underscores
                    csv_filename = f'{normalize_label(title_text)}.csv'
                else:
                    csv_filename = f'fiches_techniques_{year}.csv'

                # Créer un DataFrame Pandas à partir des données
                df_versions = pd.DataFrame(data_versions, columns=['Version', 'Carrosserie', 'Energie', 'Boîte', 'Puissance Fiscale', 'Url', 'Année', 'Marque', 'Modele'])
                folder_path = f"Versions/{mark}/{model}"

                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                save_path = os.path.join(folder_path, csv_filename)

                df_versions.to_csv(save_path, index=False)

            return data_versions

    def process_versions_links(self, driver, column_link='Lien'):
        df_path = "Data/Fiches Techniques/fiches_techniques_final.csv"
        dataframe = pd.read_csv(df_path)

        # Vérifier si la colonne Traiter existe déjà
        if 'Traiter' not in dataframe.columns:
            dataframe['Traiter'] = 0

        filtered_df = dataframe[dataframe['Traiter'] == 1]
        treated_links = set(filtered_df[column_link])  # Un ensemble pour stocker les liens déjà traités

        counter = 0
        captcha = 0
        for index, row in dataframe[len(treated_links):].iterrows():
            link_url = row[column_link]

            # Vérifier si le lien a déjà été traité
            if link_url in treated_links:
                continue

            if link_url not in treated_links:
                driver.get(link_url)
                time.sleep(1)
                html_content = driver.page_source
                data_versions = self.extract_version_data(driver, link_url, html_content, row)

                if data_versions is None:
                    captcha += 1
                    continue

                dataframe.at[index, 'Traiter'] = 1
                treated_links.update(link_url)
                save_file_path = "Fiches Techniques/fiches_techniques_final.csv"
                dataframe.to_csv(save_file_path, index=False)

                counter += 1

                print(f"Waiting for 1 minute before the next URL...{counter}")
                time.sleep(1)

            if captcha >= 2:
                print("Detection de captcha")
                break

            if counter >= 50:
                print("Arrêt après 50 itérations.")
                break

        print(f"Arrêt toutes les liens, un total de {counter} liens ont été traitées !.")


class TechnicalDataSearch:
    def __init__(self):
        self.driver = None
        self.server = None
        self.service = Service()
        self.options = Options()
        self.base_url = 'https://www.largus.fr'
        self.largus = Largus()
        self.is_captcha_detected = False

        # Définir les en-têtes
        self.headers_chrome = headers_chrome_mac = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.6',
            'content-type': 'application/json',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="99", "Chromium";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Mac OS X"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-gpc': '1',
            'referrer': 'https://www.largus.fr',
            'referrerPolicy': 'strict-origin-when-cross-origin',
        }

    def start_driver(self):
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def get_driver(self):
        try:
            self.options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
            # self.options.add_argument('--proxy-server={0}'.format(proxy.proxy))
            self.options.add_argument('--disable-gpu')
            self.options.add_argument('--window-size=1920,1080')
            self.options.add_argument('--disable-extensions')
            self.options.add_argument('--remote-debugging-port=9222')
            self.options.add_argument('--start-fullscreen')
            self.driver = webdriver.Chrome(service=self.service, options=self.options)
            return self.driver
        except Exception as e:
            print(f"Erreur lors de la création du driver: {e}")
            return None, None

    def close_driver(self):
        self.driver.quit()

    def stop_server(self):
        self.server.stop()

    @staticmethod
    def extract_vehicle_name(header):
        vehicle_name_tag = header.find('span', class_='libelle-vehicule')
        vehicle_name = vehicle_name_tag.text.strip() if vehicle_name_tag else None
        return vehicle_name

    @staticmethod
    def extract_date_lancement(header):
        date_lancement_tag = header.find('span', class_='date-lancement')
        date_lancement = date_lancement_tag.text.strip() if date_lancement_tag else None
        return date_lancement

    @staticmethod
    def extract_prix(header):
        prix_tag = header.find('div', class_='prix')
        prix = prix_tag.text.strip().replace('\u00a0', ' ') if prix_tag else None
        return prix

    @staticmethod
    def extract_gallery_images(soup, base_url="https://www.largus.fr"):
        gallery_div = soup.find('div', class_='galerieFT')
        images = gallery_div.find_all('img') if gallery_div else []
        image_urls = [base_url + img['src'] for img in images if 'src' in img.attrs]
        return image_urls

    def extract_header_data(self, soup):
        """
        Extract vehicle information from the header section.

        Parameters:
        soup (BeautifulSoup): The BeautifulSoup object of the page.

        Returns:
        dict: A dictionary containing the vehicle name, date of launch, and price.
        """
        # Extraire les informations
        header = soup.find('div', class_='title-bar clearfix')
        vehicle = self.extract_vehicle_name(header)
        date = self.extract_date_lancement(header)
        price = self.extract_prix(header)

        return [vehicle, price, date]

    @staticmethod
    def normalize_label(label):
        return unidecode.unidecode(label).strip().replace(' ', '_').replace("'", "")

    def extract_vehicle_resume(self, soup):
        resume_div = soup.find('div', id='resume')

        details = {}
        # Extraire les informations détaillées
        info_lines = resume_div.find_all('div', class_='ligneInfo')

        for line in info_lines:
            label = line.find('span', class_='labelInfo').text.strip().lower().replace(' ', '_')
            value_element = line.find('span', class_='valeur')

            if value_element:
                value = ' '.join(value_element.text.split())
            else:
                value = '-'

            details[self.normalize_label(label)] = value

        return details

    def extract_dimensions(self, soup):
        dimensions = {}
        dimensions_div = soup.find_all('div', class_='panel-dimPoids')
        if dimensions_div:
            for div in dimensions_div:
                if div.find('h3', class_='sous-titre').text.strip().upper() == "DIMENSIONS":
                    dimension_lines = div.find_all('div', class_='ligneInfo')
                    for line_div in dimension_lines:
                        label = line_div.find('span', class_='labelInfo').text.strip().lower().replace(' ', '_')
                        value = ' '.join(line_div.find('span', class_='valeur').text.split())
                        dimensions[self.normalize_label(label)] = value
            return dimensions

    def extract_weight(self, soup):
        weights = {}
        weight_divs = soup.find_all('div', class_='panel-dimPoids')
        for div in weight_divs:
            if div.find('h3', class_='sous-titre').text.strip().lower() == "poids":
                weight_lines = div.find_all('div', class_='ligneInfo')
                for line in weight_lines:
                    label = line.find('span', class_='labelInfo').text.strip().lower().replace(' ', '_')
                    value = ' '.join(line.find('span', class_='valeur').text.split())
                    weights[self.normalize_label(label)] = value
        return weights

    def extract_habitability(self, soup):
        habitability = {}
        habitability_divs = soup.find_all('div', class_='panel-dimPoids')
        for div in habitability_divs:
            if div.find('h3', class_='sous-titre').text.strip().lower() == "habitabilité":
                habitability_lines = div.find_all('div', class_='ligneInfo')
                for line in habitability_lines:
                    label = line.find('span', class_='labelInfo').text.strip().lower().replace(' ', '_')
                    value = ' '.join(line.find('span', class_='valeur').text.split())
                    habitability[self.normalize_label(label)] = value
        return habitability

    def extract_tires(self, soup):
        tires = {}
        tires_divs = soup.find_all('div', class_='panel-dimPoids')
        for div in tires_divs:
            if div.find('h3', class_='sous-titre').text.strip().lower() == "pneumatiques":
                tires_lines = div.find_all('div', class_='ligneInfo')
                for line in tires_lines:
                    label = line.find('span', class_='labelInfo').text.strip().lower().replace(' ', '_')
                    value = ' '.join(line.find('span', class_='valeur').text.split())
                    tires[self.normalize_label(label)] = value
        return tires

    def extract_vehicle_details(self, soup):
        return [self.extract_dimensions(soup), self.extract_weight(soup), self.extract_habitability(soup),
                self.extract_tires(soup)]

    def extract_engine_details(self, soup):
        engine_details = {}
        engine_div = soup.find('h3', class_='sous-titre', string='Moteur').find_next('div', class_='conteneur-infosFT')
        if engine_div:
            engine_lines = engine_div.find_all('div', class_='ligneInfo')
            for line in engine_lines:
                label = line.find('span', class_='labelInfo').text
                value = ' '.join(line.find('span', class_='valeur').text.split())
                engine_details[self.normalize_label(label)] = value
        return engine_details

    def extract_transmission_details(self, soup):
        transmission_details = {}
        transmission_div = soup.find('h3', class_='sous-titre', string='Transmission').find_next('div',
                                                                                                 class_='conteneur-infosFT')
        if transmission_div:
            transmission_lines = transmission_div.find_all('div', class_='ligneInfo')
            for line in transmission_lines:
                label = line.find('span', class_='labelInfo').text
                value = ' '.join(line.find('span', class_='valeur').text.split())
                transmission_details[self.normalize_label(label)] = value
        return transmission_details

    def extract_technical_details(self, soup):
        technical_details = {}
        technical_div = soup.find('h3', class_='sous-titre', string='Technique').find_next('div',
                                                                                           class_='conteneur-infosFT')
        if technical_div:
            technical_lines = technical_div.find_all('div', class_='ligneInfo')
            for line in technical_lines:
                label = line.find('span', class_='labelInfo').text
                value = ' '.join(line.find('span', class_='valeur').text.split())
                technical_details[self.normalize_label(label)] = value
        return technical_details

    def extract_vehicle_characteristics(self, soup):
        characteristics = {
            'Engine': [self.extract_engine_details(soup)],
            'Transmission': [self.extract_transmission_details(soup)],
            'Technical': [self.extract_technical_details(soup)],
        }
        return characteristics

    def extract_performance(self, soup):
        performance_div = soup.find('div', class_='panel-heading', id='titre-pc')
        if performance_div:
            _div = performance_div.find_next_sibling('div', class_='panel-collapse').find('h3', string='Performances')
            if _div:
                performance_div = _div.find_next_sibling('div', class_='conteneur-infosFT')
                if performance_div:
                    performance_data = {}
                    for info in performance_div.find_all('div', class_='ligneInfo'):
                        label = info.find('span', class_='labelInfo').text.strip()
                        value = info.find('span', class_='valeur').text.strip()
                        performance_data[self.normalize_label(label)] = value
                    return performance_data

    def extract_consumption(self, soup):
        consumption_div = soup.find('div', class_='panel-heading', id='titre-pc')
        if consumption_div:
            _div = consumption_div.find_next_sibling('div', class_='panel-collapse').find('h3', string='Consommations')
            if _div:
                consumption_div = _div.find_next('div', class_='conteneur-infosFT')
                if consumption_div:
                    consumption_data = {}
                    for info in consumption_div.find_all('div', class_='ligneInfo'):
                        label = info.find('span', class_='labelInfo').text.strip()
                        value = info.find('span', class_='valeur').text.strip()
                        consumption_data[self.normalize_label(label)] = value
                    return consumption_data
        return None

    @staticmethod
    def combine_dataframes(fiche_technical_detail):
        df_fiche_technical_detail = pd.concat(fiche_technical_detail, ignore_index=False, axis=1)
        return df_fiche_technical_detail

    @staticmethod
    def read_csv_files_from_directory(root_dir):
        all_dataframes = []

        # Parcours du répertoire racine et de ses sous-répertoires
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith('.csv'):
                    file_path = os.path.join(dirpath, filename)
                    try:
                        _df = pd.read_csv(file_path)
                        all_dataframes.append(_df)
                    except Exception as e:
                        print(f"Erreur lors de la lecture de {file_path}: {e}")

        # Concaténer tous les DataFrames en un seul DataFrame
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
        else:
            combined_df = pd.DataFrame()

        return combined_df

    @staticmethod
    def generate_immatriculation():
        return str(uuid.uuid4())

    def process_vehicle_data(self, folder_file_path, column_link='Url'):
        dataframe = pd.read_csv(folder_file_path)

        # Vérifier si la colonne Traiter existe déjà
        if 'Traiter' not in dataframe.columns:
            dataframe['Traiter'] = 0

        filtered_df = dataframe[dataframe['Traiter'] == 1]
        treated_links = set(filtered_df[column_link])

        counter = 0
        details = {
            'Marque': [],
            'Modele': [],
            'Annee': [],
            'Vehicule': [],
            'Prix': [],
            'Date Publication': [],
            'Resumer': [],
            'Dimensions': [],
            'Weight': [],
            'Habitability': [],
            'Tires': [],
            'Engine': [],
            'Transmission': [],
            'Technical': [],
            'Performance': [],
            'Consumption': [],
            'Gallery Images': [],
        }

        self.is_captcha_detected = False
        for index, row in dataframe[len(treated_links):].iterrows():
            link_url = row[column_link]

            # Vérifier si le lien a déjà été traité
            if link_url in treated_links:
                continue

            model = row['Modele']
            mark = row['Marque']
            year = row['Année']

            self.driver.get(link_url)
            time.sleep(1)

            if self.largus.detect_captcha(self.driver):
                self.is_captcha_detected = True
                print("La page n'a pas pu être analysée. Il est possible qu'un captcha soit détecté.")
                break

            if counter == 0:
                self.largus.click_accept_cookies(self.driver)

            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            data_header = self.extract_header_data(soup)
            vehicle_resume = self.extract_vehicle_resume(soup)
            vehicle_details = self.extract_vehicle_details(soup)
            vehicle_characteristics = self.extract_vehicle_characteristics(soup)
            performance_data = self.extract_performance(soup)
            consumption_data = self.extract_consumption(soup)
            gallery_images = self.extract_gallery_images(soup)

            details['Marque'].append(mark)
            details['Modele'].append(model)
            details['Annee'].append(year)
            details['Vehicule'].append(data_header[0])
            details['Prix'].append(data_header[1])
            details['Date Publication'].append(data_header[2])
            details['Resumer'].append(vehicle_resume)
            details['Dimensions'].append(vehicle_details[0])
            details['Weight'].append(vehicle_details[1])
            details['Habitability'].append(vehicle_details[2])
            details['Tires'].append(vehicle_details[3])
            details['Engine'].append(vehicle_characteristics['Engine'])
            details['Transmission'].append(vehicle_characteristics['Transmission'])
            details['Technical'].append(vehicle_characteristics['Technical'])
            details['Performance'].append(performance_data)
            details['Consumption'].append(consumption_data)
            details['Gallery Images'].append(gallery_images)

            dataframe.at[index, 'Traiter'] = 1
            treated_links.update(link_url)
            counter += 1

            print(f"Waiting for 1 minute before the next URL...{counter}")
            time.sleep(1)

            if counter >= 50:
                break

        dataframe.to_csv(folder_file_path, index=False)

        if self.is_captcha_detected is not True:
            print(f"Arrêt après un total de {counter} itérations.")

        return details

    def process_create_fiche_technical_df(self, data, df_folder):
        columns = ['Resumer', 'Dimensions', 'Weight', 'Habitability', 'Tires', 'Engine',
                   'Transmission', 'Technical', 'Performance', 'Consumption']

        # Vérifier si le fichier existe et charger les données existantes, sinon créer un DataFrame vide
        if os.path.exists(df_folder):
            try:
                df_save = pd.read_csv(df_folder)
            except EmptyDataError:
                df_save = pd.DataFrame(columns=['Marque', 'Modele', 'Annee', 'Vehicule', 'Prix', 'Date Publication',
                                                'Resumer', 'Dimensions', 'Weight', 'Habitability', 'Tires', 'Engine',
                                                'Transmission', 'Technical', 'Performance', 'Consumption',
                                                'Gallery Images'])
        else:
            df_save = pd.DataFrame(columns=['Marque', 'Modele', 'Annee', 'Vehicule', 'Prix', 'Date Publication',
                                            'Resumer', 'Dimensions', 'Weight', 'Habitability', 'Tires', 'Engine',
                                            'Transmission', 'Technical', 'Performance', 'Consumption',
                                            'Gallery Images'])

        df_fiche = pd.DataFrame(data)

        # Ajouter une colonne Immatriculation avec des valeurs uniques
        df_fiche['Immatriculation'] = df_fiche.apply(lambda _: self.generate_immatriculation(), axis=1)

        # Ajouter une colonne object_folder avec le chemin formaté
        df_fiche['object_folder'] = df_fiche.apply(
            lambda row: f"Vehiculs/Version/{row['Marque'].capitalize()}/{row['Annee']}/{row['Vehicule'].lower()}",
            axis=1
        )

        for column in columns:
            # Ajouter la clé Immatriculation dans chaque dictionnaire de colonne
            df_fiche[column] = df_fiche.apply(
                lambda row: {**row[column], 'Immatriculation': row['Immatriculation']} if isinstance(row[column],
                                                                                                     dict) else row[
                    column], axis=1
            )
            # Ajouter la clé Object_Folder_{column} dans chaque dictionnaire de colonne
            df_fiche[column] = df_fiche.apply(
                lambda row: {**row[column],
                             f"Object_Folder_{column}": f"Vehiculs/Models/{row['Marque'].upper()}/{column}"} if isinstance(
                    row[column], dict) else row[column], axis=1
            )

        # Concaténer le DataFrame original avec le nouveau DataFrame
        df_save = pd.concat([df_save, df_fiche], ignore_index=True)
        # Enregistrer le DataFrame concaténé dans le fichier CSV
        df_save.to_csv(df_folder, index=False)

        return df_save
