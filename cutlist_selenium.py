import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from threading import Thread

from utils import build_url, get_complete_url_parameter, print_page_to_pdf

LOWEST_MOVIE_ID = 1000
HIGHEST_MOVIE_ID = 2000
N_THREADS = 20
THREAD_SIZE = (HIGHEST_MOVIE_ID - LOWEST_MOVIE_ID) // N_THREADS

MAX_ALLOWED_MISSES = 40

def run_scraping(region_code: str, year_suffix: str, thread_id: int):
    lower_bound = LOWEST_MOVIE_ID + thread_id * THREAD_SIZE
    upper_bound = LOWEST_MOVIE_ID + (thread_id + 1) * THREAD_SIZE

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    time.sleep(thread_id)
    driver = webdriver.Chrome(options=options)

    consecutive_misses = 0
    for movie_id in range(lower_bound, upper_bound):
        if consecutive_misses >= MAX_ALLOWED_MISSES:
            # Stop archiving movies for this thread
            with open("finished.txt", "a") as f:
                f.write(f"EARLY EXIT - Thread {thread_id} hit max attempts on ID {movie_id}, IDs: {lower_bound} : {upper_bound}\n")
            break

        url = build_url(region_code, year_suffix, movie_id)
        url_param = get_complete_url_parameter(region_code, year_suffix, movie_id)

        succeeded = False
        while not succeeded:
            try:
                print(f"{url_param} - Navigating to URL: {url}")
                driver.get(url)

                # Wait for loading bar to go away
                print(f"{url_param} - Waiting for page to load...")
                WebDriverWait(driver, 120).until(EC.invisibility_of_element_located((By.ID, "bar-loader")))
                succeeded = True
            except:
                with open("finished.txt", "a") as f:
                    f.write(f"{url_param} - Retrying\n")
                print(f"{url_param} - Retrying")

        try:
            # Look for text indicating missing certificate
            driver.find_element(By.XPATH, "//*[contains(text(), 'This certificate does not exist in our database')]")
            consecutive_misses += 1
            print(f"{url_param} - No certificate found at this URL")
            print(f"{url_param} - Consecutive misses: {consecutive_misses}")
            continue
        except NoSuchElementException:
            consecutive_misses = 0

            try:
                # Look for cutlist
                cert_info = driver.find_element(By.XPATH, "//*[contains(text(), 'Cert No')]")
                print(f"{url_param} - Found cutlist! Info: {cert_info.text}")

                # Save PDF
                print_page_to_pdf(driver, region_code, year_suffix, movie_id)
                print(f"{url_param} - Saved certificate as PDF")
            except NoSuchElementException:
                print(f"{url_param} - The film associated with this URL does not have a cutlist")
        finally:
            # Print separator line
            # print("-" * 20)
            pass
            
    driver.quit()

    with open("finished.txt", "a") as f:
        f.write(f"COMPLETED - Thread {thread_id} ran to completion\n")


if __name__ == "__main__":
    year_suffix = "23"
    for region in range(10, 100, 10):
        region_code = str(region)
        with open("finished.txt", "a") as f:
            f.write("=" * 100 + "\n")
            f.write(f"Running year {year_suffix} region {region_code}\n")

        threads = []
        for i in range(N_THREADS):
            thread = Thread(target=run_scraping, args=(region_code, year_suffix, i))
            threads.append(thread)
            thread.start()
        
        for index, thread in enumerate(threads):
            print(f"Main: before joining thread {index}")
            thread.join()
            print(f"Main: thread {index} done")
