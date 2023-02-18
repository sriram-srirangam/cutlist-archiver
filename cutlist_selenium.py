from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import build_url, print_page_to_pdf

options = Options()
options.headless = True

driver = webdriver.Chrome(options=options)

for region in range(10, 100, 10):
    region_code = str(region)
    for year in range(18, 24):
        year_suffix = str(year)
        consecutive_misses = 0
        for movie_id in range(100000):
            if consecutive_misses >= 20:
                # Stop archiving movies for this region / year
                break

            url = build_url(region_code, year_suffix, movie_id)

            print(f"Navigating to URL: {url}")
            driver.get(url)

            # Wait for loading bar to go away
            print("Waiting for page to load...")
            WebDriverWait(driver, 60).until(EC.invisibility_of_element_located((By.ID, "bar-loader")))

            try:
                # Look for text indicating missing certificate
                driver.find_element(By.XPATH, "//*[contains(text(), 'This certificate does not exist in our database')]")
                consecutive_misses += 1
                print("No certificate found at this URL")
                print(f"Consecutive misses: {consecutive_misses}")
                continue
            except NoSuchElementException:
                consecutive_misses = 0

                try:
                    # Look for cutlist
                    cert_info = driver.find_element(By.XPATH, "//*[contains(text(), 'Cert No')]")
                    print(f"Found cutlist! Info: {cert_info.text}")

                    # Save PDF
                    print_page_to_pdf(driver, region_code, year_suffix, movie_id)
                    print("Saved certificate as PDF")
                except NoSuchElementException:
                    print("The film associated with this URL does not have a cutlist")
            finally:
                # Print separator line
                print("-" * 20)

driver.quit()
