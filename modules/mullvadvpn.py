import os
import random
import time
import requests


class MullVadVPN:
    def __init__(self):
        self.url_api = "https://api.mullvad.net/www/relays/all/"
        self.api_url_valid = "https://am.i.mullvad.net/json"
        self.relays = self.fetch_relays()
        self.current_ip = None

    def fetch_relays(self):
        response = requests.get(self.url_api)
        response.raise_for_status()
        return response.json()

    def reconnect_vpn(self):
        # Filtrer les serveurs actifs
        active_relays = [relay for relay in self.relays if relay['active']]

        # Choisir un serveur aléatoirement
        selected_relay = random.choice(active_relays)

        # Déconnecter Mullvad VPN
        os.system("mullvad disconnect")
        time.sleep(5)  # Attendre un peu avant de se reconnecter

        country_code = selected_relay["country_code"]
        city_code = selected_relay["city_code"]
        hostname = selected_relay["hostname"]
        country_name = selected_relay["country_name"]
        city_name = selected_relay["city_name"]

        # Se reconnecter à un serveur spécifique
        os.system(f"mullvad relay set location {country_code} {city_code}")
        os.system("mullvad connect")
        print(f"Connecting to Mullvad VPN server: {hostname} in {city_name.upper()}, {country_name.upper()}")
        time.sleep(5)  # Attendre un peu pour que la connexion soit établie

    def get_current_ip(self):
        self.reconnect_vpn()

        try:
            response = requests.get(self.api_url_valid)
            response.raise_for_status()  # Vérifie les erreurs HTTP
            self.current_ip = response.json()["ip"]
            return response.json()["ip"]
        except requests.RequestException as e:
            print(f"Failed to get current IP: {e}")
            return None

    def main(self):
        for i in range(1):
            # Se reconnecter à Mullvad pour changer d'IP
            self.get_current_ip()

            if self.current_ip:
                print(f"Current IP: {self.current_ip}")


if __name__ == "__main__":
     mullvad = MullVadVPN()
     mullvad.main()

