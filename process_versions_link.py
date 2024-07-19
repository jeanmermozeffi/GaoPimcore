from datetime import datetime
import time
import asyncio
import nest_asyncio

from modules.largus import Largus, TechnicalSearch, DataVersion, TechnicalDataSearch
from modules.mullvadvpn import MullVadVPN

largus = Largus()
process_version = DataVersion()
vpn = MullVadVPN()


async def process_data(waiting_time):
    start = time.time()
    end_time = start + waiting_time * 60
    while time.time() <= end_time:
        vpn.get_current_ip()

        if vpn.current_ip:
            print(f"Current IP: {vpn.current_ip}")

        print(f"Début du traitement à {datetime.now().strftime('%H:%M:%S')}")
        process_version.get_driver()

        process_version.process_versions_links()

        if process_version.is_captcha_detected:
            process_version.close_driver()
            continue

        process_version.close_driver()

        next_execution_time = largus.get_next_execution_time(waiting_time)
        print(f"En attente de {waiting_time} minutes avant la prochaine exécution à : {next_execution_time.strftime('%Y-%m-%d %H:%M:%S')}.")
        await asyncio.sleep(waiting_time * 60)


async def run(duration, frequency):
    start_time = time.time()
    while time.time() < start_time + 60 * duration:
        await process_data(frequency)

    if process_version.is_captcha_detected is not True:
        print(f"Les {duration} minutes sont écoulées à {datetime.now().strftime('%H:%M:%S')}.")


async def main():
    await run(duration=30, frequency=5)


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
