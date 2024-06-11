from datetime import datetime
import time
import asyncio
import nest_asyncio

from modules.largus import Largus, TechnicalDataSearch, TechnicalSearch
from modules.mullvadvpn import MullVadVPN

largus = Largus()
technique_search = TechnicalSearch()
technical_data_search = TechnicalDataSearch()
vpn = MullVadVPN()


async def process_data(waiting_time):
    start = time.time()
    end_time = start + waiting_time * 60
    while time.time() <= end_time:
        vpn.get_current_ip()

        if vpn.current_ip:
            print(f"Current IP: {vpn.current_ip}")

        print(f"Début du traitement à {datetime.now().strftime('%H:%M:%S')}")
        technique_search.get_driver()
        technique_search.process_fiche_technique_file_links()

        if technique_search.is_captcha_detected:
            technique_search.close_driver()
            continue

        technique_search.close_driver()

        print(f"En attente de {waiting_time} minutes avant la prochaine exécution.")
        await asyncio.sleep(waiting_time * 60)


async def run(duration, frequency):
    start_time = time.time()
    while time.time() < start_time + 60 * duration:
        await process_data(frequency)

    if technical_data_search.is_captcha_detected is not True:
        print(f"Les {duration} minutes sont écoulées à {datetime.now().strftime('%H:%M:%S')}.")


async def main():
    await run(duration=60, frequency=5)


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
