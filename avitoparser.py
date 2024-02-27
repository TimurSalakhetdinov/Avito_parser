from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import pandas as pd
import re
import sqlite3
from datetime import datetime
from random import randint
import traceback

URL_AVITO = "https://www.avito.ru/all/avtomobili"

brands = [
    "AC", "Acura", "Adler", "AITO", "Alfa Romeo", "Alpina", "Alpine", "AMC", "Amphicar", "Arcfox", "Aro", "Asia",
    "Aston Martin", "Audi", "Aurus", "Austin", "Avatr", "BAIC", "Baltijas Dzips", "Baojun", "Barkas", "BAW", "Belgee",
    "Bentley", "BMW", "Borgward", "Brilliance", "Bugatti", "Buick", "BYD", "Cadillac", "Changan", "ChangFeng",
    "Changhe", "Chery", "CheryExeed", "Chevrolet", "Chrysler", "Citroen", "Coggiola", "Cupra", "Dacia", "Dadi",
    "Daewoo", "Daihatsu", "Datsun", "Dayun", "Denza", "Derways", "DKW", "Dodge", "Dongfeng", "Doninvest", "DS",
    "DW Hower", "Eagle", "E-Car", "Evolute", "EXEED", "Fang Cheng Bao", "FAW", "Ferrari", "FIAT", "Ford", "Forthing",
    "Foton", "FSO", "GAC", "Geely", "Genesis", "GMC", "Golden Dragon", "Great Wall", "Groz", "Hafei", "Haima",
    "Hanomag", "Hanteng", "Haval", "Hawtai", "HiPhi", "Hispano-Suiza", "Honda", "Hongqi", "Huanghai", "Hudson",
    "Hummer", "Hyundai", "Infiniti", "Iran Khodro", "Isuzu", "Iveco", "JAC", "JAECOO", "Jaguar", "Jeep", "Jetour",
    "Jetta", "Jinbei", "JMC", "Kaiyi", "Kangaroo Electro", "Kawei", "KG Mobility", "Kia", "Koenigsegg", "KYC",
    "Lamborghini", "Lancia", "Land Rover", "Landwind", "LDV", "Leapmotor", "Lexus", "LIFAN", "Lincoln", "Livan",
    "LiXiang", "Lotus", "Lucid", "Luxgen", "Lynk & Co", "Mahindra", "MAN", "Maserati", "Maxus", "Maybach", "Mazda",
    "McLaren", "Mengshi", "Mercedes-Benz", "Mercury", "Metrocab", "MG", "M-HERO", "MINI", "Mitsubishi", "Mitsuoka",
    "Morris", "Neta", "NIO", "Nissan", "Nysa", "Oldsmobile", "OMODA", "Opel", "Ora", "Oshan", "Packard", "Pagani",
    "Peugeot", "Plymouth", "Polar Stone (Jishi)", "Polestar", "Pontiac", "Porsche", "Proton", "PUCH", "Qiyuan",
    "Qoros", "Radar", "RAM", "Ravon", "Rayton Fissore", "Reliant", "Renault", "Renault Samsung", "Rising Auto",
    "Rivian", "Roewe", "Rolls-Royce", "Rover", "Saab", "Saic", "Saturn", "Scion", "SEAT", "Seres", "Shuanghuan",
    "Simca", "Skoda", "Skywell", "SMA", "Smart", "Sollers", "Soueast", "SsangYong", "Steyr", "StreetScooter",
    "Subaru", "Suzuki", "SWM", "Talbot", "Tank", "Tata", "Tatra", "Tesla", "Tianma", "Tianye", "Toyota", "Trabant",
    "Triumph", "Trumpchi", "Vauxhall", "Venucia", "VGV", "Volkswagen", "Volvo", "Vortex", "Voyah", "Wanderer",
    "Wartburg", "Weltmeister", "Wey", "Wiesmann", "Willys", "Wuling", "Xin Kai", "XPeng", "Zastava", "Zeekr", "Zhiji", "ZOTYE",
    "Zuk", "ZX", "Автокам", "Богдан", "ВАЗ (LADA)", "ВИС", "ГАЗ", "ЕрАЗ", "ЗАЗ", "ЗИЛ", "ЗиС", "ИЖ", "Канонир",
    "Комбат", "ЛуАЗ", "Москвич", "РАФ", "Руссо-Балт", "СМЗ", "ТагАЗ", "УАЗ"]

# Function to parse the Avito website
def avito_parser(limit=None, save_to_db=False):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(15)
    driver.get(URL_AVITO)

    offers = []
    collected = 0

    while True:
        elems = driver.find_elements(by=By.CSS_SELECTOR, value='div[data-marker="item"]')
        for elem in elems:
            if limit and collected >= limit:
                break

            try:
                avito_id = int(elem.get_attribute("id")[1:])
                url = elem.find_element(by=By.CSS_SELECTOR, value='a[itemprop="url"]').get_attribute("href")

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

                # Locate the container for date using a class name that seems to be consistent
                item_date_container = elem.find_element(by=By.XPATH, value='.//div[contains(.//p/@data-marker, "item-date")]')
                time = item_date_container.find_element(by=By.CSS_SELECTOR, value='p').text

                today = datetime.now().date()

                result = {
                    "ID": avito_id,
                    "Model": model,
                    "Year": year if year else None,
                    "Power": power if power else None,
                    "Price": price if price else None,
                    "Region": region if region else None,
                    "Time": time,
                    "Today": today,
                    "URL": url,
                }
                offers.append(result)
                collected += 1

            except Exception as e:
                print(f"An error occurred at {collected}: {e}")
                traceback.print_exc()
                # Save the data before exiting
                #save_to_excel(offers, f'avito_offers_{collected}_partial.xlsx')
                #print(f"Data partially saved for {collected}")

        if limit and collected >= limit:
            break

        try:
            next_button = driver.find_element(by=By.XPATH, value='//a[@data-marker="pagination-button/nextPage"]')
            driver.execute_script("arguments[0].click();", next_button)
            sleep(randint(5, 10))  # Sleep for a short while to wait for the page to load

        except NoSuchElementException:
            print("No more pages to parse.")
            break

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
            Time TEXT,
            Today DATE,
            URL TEXT
        )
    ''')

    # Insert data into the table
    for offer in offers:
        c.execute('''
            INSERT INTO cars (ID, Model, Year, Power, Price, Region, Time, Today, URL)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            offer["ID"], 
            offer["Model"], 
            offer["Year"], 
            offer["Power"], 
            offer["Price"], 
            offer["Region"], 
            offer["Time"], 
            offer["Today"], 
            offer["URL"]
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    offers = avito_parser(limit=5, save_to_db=False)  # Set limit=None to process all cars, set save_to_db=True to save to the database