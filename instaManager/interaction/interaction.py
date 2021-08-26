import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def click(driver, xpath, max_time=2):
    try:
        element = WebDriverWait(driver, max_time).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
    except TimeoutException as bad_except:
        print(bad_except)
        raise bad_except
    except selenium.common.exceptions.ElementClickInterceptedException as bad_except:
        raise bad_except
    except selenium.common.exceptions.NoSuchElementException as bad_except:
        raise bad_except
    except Exception as bad_except:
        raise bad_except


def get(driver, url):
    try:
        driver.get(url)
    except Exception as bad_except:
        raise bad_except


def send_keys(driver, xpath, keys, max_time=2):
    try:
        element = WebDriverWait(driver, max_time).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.send_keys(keys)
    except TimeoutException as bad_except:

        raise bad_except
    except selenium.common.exceptions.NoSuchElementException as bad_except:
        raise bad_except
    except Exception as bad_except:
        raise bad_except
