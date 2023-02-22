import base64, os

from selenium.webdriver.chrome.webdriver import WebDriver


def get_padded_movie_id(movie_id: int) -> str:
    """
    Pad ID with leading zeroes to format it such that it always has five digits.
    """
    return str(movie_id).zfill(5)

def get_complete_url_parameter(region_code: str, year_suffix: str, movie_id: int) -> str:
    padded_id = get_padded_movie_id(movie_id)
    return f"1000{region_code}29{year_suffix}000{padded_id}"

def build_url(region_code: str, year_suffix: str, movie_id: int) -> str:
    url_parameter = get_complete_url_parameter(region_code, year_suffix, movie_id)
    return f'https://www.ecinepramaan.gov.in/cbfc/?a=Certificate_Detail&i={url_parameter}'

def print_page_to_pdf(driver: WebDriver, region_code: str, year_suffix: str, movie_id: int):
    path = os.path.join(".", "certificates", year_suffix, region_code)
    if not os.path.isdir(path):
        os.makedirs(path)
    file_path = os.path.join(path, f"{get_padded_movie_id(movie_id)}.pdf")

    encoded_pdf = driver.print_page()
    with open(file_path, 'wb') as fout:
        fout.write(base64.b64decode(encoded_pdf))
