import sqlite3


def check_database(offers):
    with sqlite3.connect("realty.db") as connection:
        cursor = connection.cursor()
        for offer in offers:
            avito_id = offer["ID"]  # Assuming 'ID' is the key for avito_id in your offer dictionary
            cursor.execute("SELECT avito_id FROM offers WHERE avito_id = ?", (avito_id,))
            result = cursor.fetchone()
            if result is None:
                # Prepare data tuple according to the new table structure
                data = (avito_id, offer.get("Model"), offer.get("Year"),
                        offer.get("Power"), offer.get("Price"), offer.get("Region"),
                        offer.get("Time"), offer.get("URL"))
                
                cursor.execute("""
                    INSERT INTO offers (avito_id, model, year, power, price, region, time, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, data)
                
                connection.commit()
                print(f"Объявление {avito_id} добавлено в базу данных")
            else:
                print(f"Объявление {avito_id} уже существует в базе данных")



def create_table():
    connection = sqlite3.connect("realty.db")
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avito_id INTEGER UNIQUE NOT NULL,
            model TEXT,
            year INTEGER,
            power INTEGER,
            price REAL NOT NULL,
            region TEXT,
            time TEXT,
            url TEXT NOT NULL,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    connection.close()



def main():
    create_table()


if __name__ == "__main__":
    main()
