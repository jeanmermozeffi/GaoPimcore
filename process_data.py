from datetime import datetime
import time
import asyncio
import nest_asyncio


async def process_data(waiting_time):
    folder = "Versions/Bmw/Bmw.csv"
    save_file_path = "Fiches Technical Details/fiches_technical_details.csv"

    async with True:
        start = time.time()
        while time.time() <= start + waiting_time * 60:
            driver = get_driver()
            data = process_vehicle_data(driver, save_file_path)
            driver.quit()

            if len(data) > 0:
                try:
                    process_create_fiche_technical_df(data, folder)
                except Exception as e:
                    print(f"Error sending event data batch")
            print(f"Données traitées et sauvegardées. En attente de {waiting_time} minutes avant la prochaine exécution.")
            await asyncio.sleep(waiting_time * 60)


def run(duration, frequency):
    start_time = time.time()
    while time.time() < start_time + 60 * duration:
        asyncio.run(process_data(frequency))


def main():
    run(duration=30, frequency=5)