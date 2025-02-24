import base64, os, re
from datetime import datetime

from selenium.webdriver.chrome.webdriver import WebDriver


def get_padded_movie_id(movie_id: int) -> str:
    """
    Pad ID with leading zeroes to format it such that it always has five digits.
    """
    return str(movie_id).zfill(5)


def get_complete_url_parameter(
    region_code: str, year_suffix: str, movie_id: int
) -> str:
    padded_id = get_padded_movie_id(movie_id)
    return f"1000{region_code}29{year_suffix}000{padded_id}"


def build_url(region_code: str, year_suffix: str, movie_id: int) -> str:
    url_parameter = get_complete_url_parameter(region_code, year_suffix, movie_id)
    return (
        f"https://www.ecinepramaan.gov.in/cbfc/?a=Certificate_Detail&i={url_parameter}"
    )


def print_page_to_pdf(
    driver: WebDriver, region_code: str, year_suffix: str, movie_id: int
):
    path = os.path.join(".", "certificates", year_suffix, region_code)
    if not os.path.isdir(path):
        os.makedirs(path)
    file_path = os.path.join(path, f"{get_padded_movie_id(movie_id)}.pdf")

    print_succeeded = False
    while not print_succeeded:
        try:
            encoded_pdf = driver.print_page()
            print_succeeded = True
        except Exception as e:
            url_param = get_complete_url_parameter(region_code, year_suffix, movie_id)
            print(f"{url_param} - Failed printing with exception {e}")
            print(f"{url_param} - Retrying printing")
    with open(file_path, "wb") as fout:
        fout.write(base64.b64decode(encoded_pdf))


def get_max_certificate_id_for_region_in_year(
    year_suffix: str, region_code: str
) -> int:
    region_path = os.path.join("certificates", year_suffix, region_code)
    if not os.path.isdir(region_path):
        return None

    pdf_numbers = [
        int(re.match(r"(\d{5})\.pdf", pdf_file).group(1))
        for pdf_file in os.listdir(region_path)
        if re.match(r"(\d{5})\.pdf", pdf_file)
    ]

    if not pdf_numbers:
        return None

    return max(pdf_numbers)


def get_max_certificate_id_for_region(region_code: str) -> int:
    max_certificate_by_year = []
    base_path = os.path.join("certificates")
    for year_suffix in (
        dirname for dirname in os.listdir(base_path) if dirname.isdigit()
    ):
        year_path = os.path.join(base_path, year_suffix)
        if os.path.isdir(year_path):
            region_path = os.path.join(year_path, region_code)
            if os.path.isdir(region_path):
                max_certificate = get_max_certificate_id_for_region_in_year(
                    year_suffix, region_code
                )
                if max_certificate is not None:
                    max_certificate_by_year.append(max_certificate)

    return max(max_certificate_by_year) if max_certificate_by_year else None


def get_predicted_max_certificate_id_for_region_in_current_year(
    region_code: str,
) -> int:
    today = datetime.today()
    day_of_year = today.timetuple().tm_yday
    days_in_year = 366 if today.year % 4 == 0 else 365

    max_certificate_id = get_max_certificate_id_for_region(region_code)
    if max_certificate_id is None:
        return None

    return max(int(max_certificate_id * (day_of_year / days_in_year)), 100)
