from datetime import datetime
import time
import os
import asyncio
import nest_asyncio

import pandas as pd

from modules.largus import Largus, TechnicalDataSearch
from modules.mullvadvpn import MullVadVPN

largus = Largus()
technical_data_search = TechnicalDataSearch()
vpn = MullVadVPN()

is_view_save = True
limit_scraper = 50

folder_file_path = "../Data/Version_Technical_Details.csv"
save_folder_df = "../Data/Fiches Technical Details"
path_save_df = 'liste_fiches_technical_details.csv'


async def process_data(waiting_time, with_vpn=True):
    try:
        if not os.path.exists(save_folder_df):
            os.makedirs(save_folder_df)
            print("Le dossier {} a été créé avec succès.".format(save_folder_df))
    except OSError as e:
        print(f"Une erreur est survenue lors de la création du dossier : {e}")

    path_file_save_df = os.path.join(save_folder_df, path_save_df)

    start = time.time()
    end_time = start + waiting_time * 60
    while time.time() <= end_time:
        if technical_data_search.captcha_abus:
            break

        if with_vpn:
            vpn.get_current_ip()

        if vpn.current_ip:
            print(f"Current IP: {vpn.current_ip}")

        print(f"Début du traitement à {datetime.now().strftime('%H:%M:%S')}")
        technical_data_search.get_driver()
        time.sleep(2)
        data = technical_data_search.process_vehicle_data(
            folder_file_path=folder_file_path,
            is_view_save=is_view_save,
            limit_scraper=limit_scraper
        )

        if technical_data_search.is_captcha_detected:
            technical_data_search.close_driver()
            continue

        technical_data_search.close_driver()

        if len(data) > 0:
            try:
                technical_data_search.process_create_fiche_technical_df(data, path_file_save_df)
                print(f"Données traitées et sauvegardées à {datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                error_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
                error_message = f"Erreur lors du traitement des données à {error_time}: {str(e)}"
                log_folder = '../Data/Log'

                try:
                    if not os.path.exists(log_folder):
                        os.makedirs(log_folder)
                    print(f"Le dossier {log_folder} a été créé avec succès.")
                except OSError as e:
                    print(f"Une erreur est survenue lors de la création du dossier : {e}")

                error_log_file = os.path.join(log_folder, f'error_log_{error_time}_.txt')
                error_data_log_file = os.path.join(log_folder, f'error_data_log_{error_time}_.csv')
                with open(error_log_file, 'a') as f:
                    f.write(error_message + '\n')

                # Enregistrement des données ayant causé l'erreur
                error_df = pd.DataFrame(data)
                error_df.to_csv(error_data_log_file, index=False)

                print(error_message)
        else:
            print(f"Aucune donnée trouvée à {datetime.now().strftime('%H:%M:%S')}")

        next_execution_time = largus.get_next_execution_time(waiting_time)
        print(f"En attente de {waiting_time} minutes avant la prochaine exécution à : "
              f"{next_execution_time.strftime('%Y-%m-%d %H:%M:%S')}.")

        await asyncio.sleep(waiting_time * 60)


# Fonction asynchrone pour exécuter le traitement pendant une durée donnée
async def run(duration, frequency):
    start_time = time.time()
    while time.time() < start_time + 60 * duration:
        if technical_data_search.captcha_abus:
            break
        await process_data(frequency, False)

    if technical_data_search.is_captcha_detected is not True:
        print(f"Les {duration} minutes sont écoulées à {datetime.now().strftime('%H:%M:%S')}.")


async def main():
    await run(duration=120, frequency=5)


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())

