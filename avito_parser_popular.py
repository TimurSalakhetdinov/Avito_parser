from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from time import sleep
import pandas as pd
import re
import sqlite3
from datetime import datetime
from random import randint
import traceback
import argparse

# Function to read brand names
def load_brand_names(file_name):
    with open(file_name, 'r') as file:
        brand_names = [line.strip() for line in file if line.strip()]
    return brand_names

# Load brands
brand_name = load_brand_names('brands.txt')

# Function to read links from a file within the 'links/' folder
def load_links(brand):
    # Construct the filename with 'links_' prefix and the brand name
    file_path = f"links/links_{brand}.txt"
    with open(file_path, 'r') as file:
        links = [line.strip() for line in file if line.strip()]
    return links

# Function to transform data
def transform_data(offers, brand_name):
    transformed_offers = []
    
    pattern = r'(\s+\d+\.\d+)?\s+(MT|AT|CVT|AMT)$'

    for offer in offers:
        brand_model_cleaned = offer['Brand']

        # Remove the engine size and transmission type from the end of the brand_model_cleaned string
        brand_model_cleaned = re.sub(pattern, '', brand_model_cleaned, flags=re.IGNORECASE)

        # Find the longest matching brand in the cleaned title
        matched_brand = ''
        for brand in brand_name:
            if brand_model_cleaned.lower().startswith(brand.lower()) and len(brand) > len(matched_brand):
                matched_brand = brand

        # If a brand is matched, extract it and the subsequent text as the model
        if matched_brand:
            model = brand_model_cleaned[len(matched_brand):].strip()
        else:
            model = brand_model_cleaned  # Fallback to using the entire cleaned text as the model

        # Update the offer with the cleaned and split brand and model
        offer['Brand'] = matched_brand if matched_brand else 'Unknown'
        offer['Model'] = model

        transformed_offers.append(offer)

    return transformed_offers

# List of brands for which you have corresponding text files
# brands = ['audi', 'bmw', 'changan', 'chery', 'chevrolet', 'exeed', 'ford', 'geely', 'haval', 'honda', 'hyundai', 'kia', 'mazda',
            #'mercedes-benz', 'mitsubishi', 'nissan', 'omoda', 'opel', 'renault', 'skoda', 'toyota', 'omoda', 'toyota', 'volkswagen', 'gaz', 'vaz_lada',
brands = ['gruzovik']

# Function to parse brands from the Avito website
def avito_parser_popular(brand, links, brand_name):
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(15)

    offers = []

    for link in links:

        try:
            driver.get(link)

            while True:
                elems = driver.find_elements(by=By.CSS_SELECTOR, value='div[data-marker="item"]')
                for elem in elems:

                    try:
                        # Parse ID of the advertisement
                        avito_id = int(elem.get_attribute("id")[1:])

                        # Selector for item_title based on the structure provided
                        item_title_container = elem.find_element(by=By.XPATH, value='.//div[contains(@class, "titleStep")]//h3')
                        item_title = item_title_container.text.strip()
                        split_title = item_title.split(',')

                        # Extract the brand and model from the first part of the split title
                        brand_model = split_title[0].strip()

                        # Extract the year from the second part, if it exists and check if it is less than 2012
                        year = re.search(r'\b\d{4}\b', split_title[1]).group() if len(split_title) > 1 else None

                        # Locate the container for specific parameters using the data-marker attribute item-specific-params
                        item_params_container = elem.find_element(by=By.XPATH, value='.//div[contains(.//p/@data-marker, "item-specific-params")]')
                        item_params = item_params_container.find_element(by=By.CSS_SELECTOR, value='p').text
                        power_match = re.search(r'\((\d+)\s*л\.с\.\)', item_params)
                        power = power_match.group(1) if power_match else "N/A"

                        # Check for 'Битый' in the item-specific parameters and mark it
                        try:
                            is_damaged = 'Yes' if 'Битый' in item_params else 'No'
                        except NoSuchElementException:
                            is_damaged = 'No'  # Assume not damaged if the element is not found

                        # Locate the parent `div` of the `p` element that contains the price
                        item_price_container = elem.find_element(by=By.XPATH, value='.//div[contains(.//p/@data-marker, "item-price")]')
                        item_price = item_price_container.find_element(by=By.CSS_SELECTOR, value='p').text
                        price = ''.join(re.findall(r'\d+', item_price))

                        result = {
                            "ID": avito_id,
                            "Brand": brand_model,
                            "Year": year,
                            "Power": power if power else None,
                            "Damaged": is_damaged,
                            "Price": price if price else None,
                        }
                        offers.append(result)
                        collected += 1

                    except Exception as e:
                        print(f"An error occurred while processing {link} at {collected}: {e}")
                        traceback.print_exc()

                try:
                    next_button = driver.find_element(by=By.XPATH, value='//a[@data-marker="pagination-button/nextPage"]')
                    driver.execute_script("arguments[0].click();", next_button)
                    
                    # Wait for the next set of car elements to be loaded
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-marker="item"]'))
                    )
                except NoSuchElementException:
                    print(f"Finished with link: {link}")
                    break
                except TimeoutException:
                    print("Timed out waiting for page to load")
                    break  # Break the loop if new items don't appear or page load times out

        except Exception as e:
            print(f"An error occurred while trying to access {link}: {e}")
            traceback.print_exc()
            continue  # Skip to the next link if an error occurs

    driver.quit()

    # Apply transformations after parsing is complete for one brand
    transformed_offers = transform_data(offers, brand_name)
    
    # Save to an Excel file specific to the brand
    save_to_excel(transformed_offers, brand)

# Function to save data to Excel, named after the brand
def save_to_excel(offers, brand):
    df = pd.DataFrame(offers)
    filename = f'avito_cars_{brand}.xlsx'
    df.to_excel(filename, index=False)
    print(f"Data for {brand} saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse Avito for car offers using provided links from brand-specific files within the "links" folder.')
    parser.add_argument('--limit', type=int, help='Limit the number of cars to parse', default=None)
    args = parser.parse_args()

    for brand in brands:
        links = load_links(brand)
        avito_parser_popular(brand, links, limit=args.limit, brand_name=brand_name)