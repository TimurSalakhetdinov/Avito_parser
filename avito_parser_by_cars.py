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
import argparse

# Brands that have less then 5000 cars on a page, so it can be parsed with one iteration
brands =  [
          'ac', 'acura', 'adler', 'aito', 'alfa_romeo', 'alpina', 'amc', 'amphicar', 'arcfox', 'aro', 'asia', 
          'aston_martin', 'aurus', 'austin', 'avatr', 'baic', 'bajaj', 'baltijas_dzips', 'baojun', 'barkas', 'baw', 
          'belgee', 'bentley', 'blaval', 'borgward', 'brilliance', 'bugatti', 'buick', 'byd', 'cadillac',  
          'changfeng', 'cheryexeed', 'chrysler', 'citroen', 'coggiola', 'cord', 'cupra', 'dacia', 'dadi', 
          'daewoo', 'daihatsu', 'datsun', 'dayun', 'denza', 'derways', 'dodge', 'dongfeng', 'doninvest', 'ds', 
          'dw_hower', 'eagle', 'evolute', 'fang_cheng_bao', 'faw', 'ferrari', 'fiat', 'forthing', 
          'foton', 'fso', 'gac', 'genesis', 'gmc', 'golden_dragon', 'great wall', 'groz', 'hafei', 'haima', 'hanomag', 
          'hawtai', 'hiphi', 'hispano-suiza', 'hongqi', 'huanghai', 'hudson', 'humber', 'hummer', 'hycan',  
          'infiniti', 'iran_khodro', 'isuzu', 'iveco', 'jac', 'jaecoo', 'jaguar', 'jeep', 'jensen', 'jetour', 'jetta', 'jinbei', 'jmc', 
          'jonway', 'junfeng', 'kaiyi', 'kangaroo_electro', 'karry', 'kawei', 'kg_mobility', 'koenigsegg', 'kyc', 'lamborghini', 'lancia',
          'land_rover', 'landwind', 'ldv', 'leapmotor', 'lexus', 'lifan', 'lincoln', 'livan', 'lixiang', 'lotus', 'lti', 'lucid', 'luxgen', 'lynk_and_co', 
          'mahindra', 'man', 'maserati', 'maxus', 'maybach', 'mazda', 'mclaren', 'mengshi', 'mercury', 'metrocab', 
          'mg', 'mini', 'mitsuoka', 'morris', 'neta', 'nio', 'nysa', 'oldsmobile',
          'ora', 'oshan', 'packard', 'pagani', 'peugeot', 'plymouth', 'polar_stone_jishi', 'polestar', 'pontiac', 'porsche', 'proton', 
          'puch', 'ram', 'ravon', 'rayton_fissore', 'reliant', 'renault_samsung', 'rising_auto', 
          'rivian', 'roewe', 'rolls-royce', 'rover', 'saab', 'saturn', 'scion', 'seat', 'seres', 'shuanghuan', 'simca', 
          'skywell', 'sma', 'smart', 'sol', 'solaris', 'sollers', 'soueast', 'ssangyong', 'steyr', 'subaru', 'suzuki', 'swm',  
          'tank', 'tata', 'tatra', 'tazzari', 'tesla', 'tianma', 'tianye', 'trabant', 'triumph', 'trumpchi', 'tvr', 'vauxhall', 'venucia', 'vgv', 
          'volvo', 'vortex', 'voyah', 'wanderer', 'wartburg', 'weltmeister', 'wey', 'wiesmann', 'willys', 'wuling', 'xin_kai', 
          'xpeng', 'zeekr', 'zotye', 'zuk', 'zx', 'avtokam', 'bogdan', 'vis', 'eraz', 'zaz', 'zil', 
          'zis', 'izh', 'luaz', 'moskvich', 'raf', 'smz', 'tagaz', 'uaz']

# Function to read brand names
def load_brand_names(file_name):
    with open(file_name, 'r') as file:
        # Read each line in the file, strip leading/trailing whitespace, and ignore empty lines
        brand_names = [line.strip() for line in file if line.strip()]
    return brand_names

# Load brand names
brand_name = load_brand_names('brands.txt')

# Function to parse brands with less then 5000 cars the Avito website
def avito_parser(limit=None, save_to_db=False):
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")
    options.add_argument("start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(15)

    offers = []
    collected = 0
    stop_processing = False

    for brand in brands:
        if stop_processing:  # Check if we should stop processing before starting the next brand
            break
        try:
            brand_url = f"https://www.avito.ru/all/avtomobili/{brand}"
            driver.get(brand_url)
            
            # Check if there are any cars listed for the brand, if not, skip to the next brand
            if not driver.find_elements(by=By.CSS_SELECTOR, value='div[data-marker="item"]'):
                print(f"No cars listed for brand {brand}. Skipping to next brand.")
                continue

            while True:
                elems = driver.find_elements(by=By.CSS_SELECTOR, value='div[data-marker="item"]')
                for elem in elems:
                    if limit and collected >= limit:
                        stop_processing = True  # Set the flag to true to stop processing further brands
                        break  # Break out of the inner loop

                    try:
                        avito_id = int(elem.get_attribute("id")[1:])

                        # Selector for item_title based on the structure provided
                        item_title_container = elem.find_element(by=By.XPATH, value='.//div[contains(@class, "titleStep")]//h3')
                        item_title = item_title_container.text.strip()

                        # Split the title by commas to separate the title from other details like the year
                        split_title = item_title.split(',')

                        # Extract the brand and model from the first part of the split title
                        brand_model_cleaned = split_title[0].strip()

                        # Find the longest matching brand in the cleaned title
                        matched_brand = ''
                        for brand in brand_name:
                            if brand_model_cleaned.lower().startswith(brand.lower()) and len(brand) > len(matched_brand):
                                matched_brand = brand

                        # If a brand is matched, extract it and the subsequent text as the model
                        if matched_brand:
                            model = brand_model_cleaned[len(matched_brand):].strip()
                        else:
                            # If no brand is matched, further logic will be needed to handle this case
                            model = brand_model_cleaned  # Fallback to using the entire cleaned text as the model

                        # Extract the year from the second part, if it exists
                        year = re.search(r'\b\d{4}\b', split_title[1]).group() if len(split_title) > 1 else None

                        # You now have the brand, model, and year extracted
                        brand = matched_brand if matched_brand else 'Unknown'

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
                        region_full_text = region_container.text
                        region = region_full_text.split(',')[0].strip()

                        today = datetime.now().date()

                        result = {
                            "ID": avito_id,
                            "Brand": brand,
                            "Model": model,
                            "Year": year if year else None,
                            "Power": power if power else None,
                            "Price": price if price else None,
                            "Region": region if region else None,
                            "Today": today,
                        }
                        offers.append(result)
                        collected += 1

                    except Exception as e:
                        print(f"An error occurred while processing {brand} at {collected}: {e}")
                        traceback.print_exc()

                if stop_processing or (limit and collected >= limit):
                    break

                try:
                    next_button = driver.find_element(by=By.XPATH, value='//a[@data-marker="pagination-button/nextPage"]')
                    driver.execute_script("arguments[0].click();", next_button)
                    sleep(randint(2, 6))  # Sleep for a short while to wait for the page to load

                except NoSuchElementException:
                    print(f"No more pages to parse for {brand}.")
                    break

        except Exception as e:
            print(f"An error occurred while trying to access the page for brand {brand}: {e}")
            traceback.print_exc()
            continue  # Skip to the next brand

    driver.quit()

    if save_to_db:
        save_to_database(offers)
    else:
        save_to_excel(offers)

    return offers

# Function to save data to Excel
def save_to_excel(offers):
    df = pd.DataFrame(offers)
    df.to_excel('avito_cars_less_5000.xlsx', index=False)

# Function to save data to db
def save_to_database(offers):
    conn = sqlite3.connect('avito_cars.db')
    c = conn.cursor()
    # Create the table with the matching columns
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            ID INTEGER PRIMARY KEY,
            Brand TEXT,
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
            INSERT INTO cars (ID, Brand, Model, Year, Power, Price, Region, Today)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            offer["ID"], 
            offer["Brand"], 
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
    # Initialize the parser
    parser = argparse.ArgumentParser(description='Parse Avito for car offers.')
    # Add the 'limit' argument
    parser.add_argument('--limit', type=int, help='Limit the number of cars to parse', default=None)
    # Add the 'save_to_db' argument
    parser.add_argument('--save_to_db', action='store_true', help='Save the results to the database')

    # Parse the arguments
    args = parser.parse_args()

    # Call the avito_parser function with the provided arguments
    offers = avito_parser(limit=args.limit, save_to_db=args.save_to_db)