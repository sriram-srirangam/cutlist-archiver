from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from threading import Thread

from utils import build_url, get_complete_url_parameter, print_page_to_pdf

HIGHEST_MOVIE_ID = 100000
N_THREADS = 10
THREAD_SIZE = HIGHEST_MOVIE_ID // N_THREADS

def run_scraping(region_code: str, year_suffix: str, thread_id: int):
    lower_bound = thread_id * THREAD_SIZE
    upper_bound = thread_id * (THREAD_SIZE + 1)

    options = Options()
    options.headless = True

    driver = webdriver.Chrome(options=options)

    consecutive_misses = 0
    for movie_id in range(lower_bound, upper_bound):
        if consecutive_misses >= 20:
            # Stop archiving movies for this thread
            break

        url = build_url(region_code, year_suffix, movie_id)
        url_param = get_complete_url_parameter(region_code, year_suffix, movie_id)

        print(f"{url_param} - Navigating to URL: {url}")
        driver.get(url)

        # Wait for loading bar to go away
        print(f"{url_param} - Waiting for page to load...")
        WebDriverWait(driver, 90).until(EC.invisibility_of_element_located((By.ID, "bar-loader")))

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


if __name__ == "__main__":
    year_suffix = "18"
    region_code = "10"

    threads = []
    for i in range(N_THREADS):
        thread = Thread(target=run_scraping, args=(region_code, year_suffix, i))
        threads.append((i, thread))
        thread.start()
    
    for index, thread in threads:
        print(f"Main: before joining thread {index}")
        thread.join()
        print(f"Main: thread {index} done")
