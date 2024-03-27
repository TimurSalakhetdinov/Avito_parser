from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import pandas as pd
import re
import sqlite3
from datetime import datetime
from random import randint
import traceback

URL_AVITO = "https://www.avito.ru/all/avtomobili"

brands_5000 = ['audi', 'bmw', 'changan', 'chery', 'chevrolet', 'exeed', 'ford', 'geely', 'haval', 'honda', 'hyundai', 'kia', 'mercedes-benz', 'mitsubishi', 'nissan', 
               'omoda', 'opel', 'renault', 'skoda', 'toyota', 'volkswagen', 'vaz_lada']

# Function to parse brands from the Avito website with more then 5000
def avito_parser_5000(limit=None, save_to_db=False):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(15)
    driver.get(URL_AVITO)

    offers = []
    collected = 0
    
    # Wait for the main page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-marker="catalog-serp"]'))
    )

    # Locate brand links using part of the href attribute
    brands_elements = driver.find_elements(by=By.XPATH, value="//a[contains(@href, '/all/avtomobili/') and contains(@class, 'link-link')]")

    # Loop through each brand
    for brand_elem in brands_elements:
        # Click the brand link to navigate to the brand-specific page
        brand_href = brand_elem.get_attribute('href')
        driver.get(brand_href)

        # Wait for the brand page to load and detect the presence of the catalog
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-marker="catalog-serp"]'))
        )
        
        # Click the "All" button to list all models
        all_models_button = driver.find_element(by=By.XPATH, value='//button[@data-marker="catalog-filters/expand"]')
        driver.execute_script("arguments[0].click();", all_models_button)
        
        # Wait until models are loaded (You may need to adjust this wait time)
        sleep(3)

        # Find all model links
        model_links = driver.find_elements(by=By.CSS_SELECTOR, value='a[data-marker="link"]')
        
        # Loop through each model
        for model_link in model_links:
            driver.execute_script("arguments[0].click();", model_link)
            
            # Wait until the model page is loaded
            sleep(3)

            while True:
                elems = driver.find_elements(by=By.CSS_SELECTOR, value='div[data-marker="item"]')
                for elem in elems:
                    if limit and collected >= limit:
                        break

                    try:
                        avito_id = int(elem.get_attribute("id")[1:])

                        # Adjusted selector for item_title based on the structure provided
                        item_title_container = elem.find_element(by=By.XPATH, value='.//div[contains(@class, "titleStep")]//h3')
                        item_title = item_title_container.text.split(', ')
                        full_title = item_title[0].strip()
                        model_parts = full_title.split()[:-2]
                        model = ' '.join(model_parts)
                        year = re.search(r'\b\d{4}\b', item_title[1]).group()

                        # Locate the container for specific parameters using the data-marker attribute item-specific-params
                        item_params_container = elem.find_element(by=By.XPATH, value='.//div[contains(.//p/@data-marker, "item-specific-params")]')
                        item_params = item_params_container.find_element(by=By.CSS_SELECTOR, value='p').text
                        power_match = re.search(r'\((\d+)\s*л\.с\.\)', item_params)
                        power = power_match.group(1) if power_match else "N/A"

                        # Locate the parent `div` of the `p` element that contains the price
                        item_price_container = elem.find_element(by=By.XPATH, value='.//div[contains(.//p/@data-marker, "item-price")]')
                        item_price = item_price_container.find_element(by=By.CSS_SELECTOR, value='p').text
                        price = ''.join(re.findall(r'\d+', item_price))

                        # Locate the container for the region using a class name that seems to be consistent
                        region_container = elem.find_element(by=By.XPATH, value='.//div[contains(@class, "geo-root")]//span')
                        region = region_container.text

                        today = datetime.now().date()

                        result = {
                            "ID": avito_id,
                            "Model": model,
                            "Year": year if year else None,
                            "Power": power if power else None,
                            "Price": price if price else None,
                            "Region": region if region else None,
                            "Today": today
                        }
                        offers.append(result)
                        collected += 1

                    except Exception as e:
                        print(f"An error occurred at {collected}: {e}")
                        traceback.print_exc()

                if limit and collected >= limit:
                    break

                # Pagination to go through all the pages of the model
                try:
                    next_button = driver.find_element(by=By.XPATH, value='//a[@data-marker="pagination-button/next"]')
                    driver.execute_script("arguments[0].click();", next_button)
                    sleep(randint(5, 10))  # Sleep for a short while to wait for the page to load
                except NoSuchElementException:
                    print("No more pages for this model.")
                    break

            # After finishing with one model, navigate back to the brand's models list
            driver.execute_script("window.history.go(-1)")

        # Close the brand tab and switch back to the main window
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    driver.quit()

    if save_to_db:
        save_to_database(offers)
    else:
        save_to_excel(offers)

    return offers

def save_to_excel(offers):
    df = pd.DataFrame(offers)
    df.to_excel('avito_offers.xlsx', index=False)

def save_to_database(offers):
    conn = sqlite3.connect('avito_cars.db')
    c = conn.cursor()
    # Create the table with the matching columns
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            ID INTEGER PRIMARY KEY,
            Model TEXT,
            Year INTEGER,
            Power INTEGER,
            Price INTEGER,
            Region TEXT,
            Today DATE
        )
    ''')

    # Insert data into the table
    for offer in offers:
        c.execute('''
            INSERT INTO cars (ID, Model, Year, Power, Price, Region, Today)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            offer["ID"], 
            offer["Model"], 
            offer["Year"], 
            offer["Power"], 
            offer["Price"], 
            offer["Region"], 
            offer["Today"]
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    offers = avito_parser_5000(limit=5, save_to_db=False)  # Set limit=None to process all cars, set save_to_db=True to save to the database