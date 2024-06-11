from datetime import datetime
import time
import asyncio
import nest_asyncio

from modules.largus import Largus, TechnicalDataSearch
from modules.mullvadvpn import MullVadVPN

largus = Largus()
technical_data_search = TechnicalDataSearch()
vpn = MullVadVPN()


async def process_data(waiting_time):
    folder_file_path = "Data/Versions/Bmw/Bmw.csv"
    save_file_df = "Data/Fiches Technical Details/fiches_technical_details.csv"

    start = time.time()
    end_time = start + waiting_time * 60
    while time.time() <= end_time:
        vpn.get_current_ip()

        if vpn.current_ip:
            print(f"Current IP: {vpn.current_ip}")

        print(f"Début du traitement à {datetime.now().strftime('%H:%M:%S')}")
        technical_data_search.get_driver()
        data = technical_data_search.process_vehicle_data(folder_file_path)

        if technical_data_search.is_captcha_detected:
            technical_data_search.close_driver()
            # technical_data_search.stop_server()
            continue

        technical_data_search.close_driver()
        # technical_data_search.stop_server()

        if len(data) > 0:
            try:
                technical_data_search.process_create_fiche_technical_df(data, save_file_df)
                print(f"Données traitées et sauvegardées à {datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"Erreur lors de l'envoi du lot de données d'événement")
        else:
            print(f"Aucune donnée trouvée à {datetime.now().strftime('%H:%M:%S')}")

        print(f"En attente de {waiting_time} minutes avant la prochaine exécution.")
        await asyncio.sleep(waiting_time * 60)


# Fonction asynchrone pour exécuter le traitement pendant une durée donnée
async def run(duration, frequency):
    start_time = time.time()
    while time.time() < start_time + 60 * duration:
        await process_data(frequency)

    if technical_data_search.is_captcha_detected is not True:
        print(f"Les {duration} minutes sont écoulées à {datetime.now().strftime('%H:%M:%S')}.")


# run(float(sys.argv[1]), float(sys.argv[2]))

# Fonction principale asynchrone
async def main():
    await run(duration=60, frequency=5)


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())

