# Avito Car Offers Parser

## Description
This Python script is designed for parsing car offers from the Avito website, a popular classified ads platform. The script focuses on collecting data for a predefined set of car brands, extracting key information such as brand, model, year, power, price, and region for each offer, and saving the data into brand-specific Excel files. 

The script leverages the Selenium WebDriver for web scraping, enabling dynamic interaction with the Avito website to navigate through pages of car offers. It supports limiting the number of offers to parse, making the data collection process flexible and tailored to specific needs.

## Features
- Dynamic web scraping with Selenium WebDriver.
- Parsing car offers for predefined car brands.
- Extracting key details: Brand, Model, Year, Power, Price, Region.
- Saving parsed data into brand-specific Excel files.
- Option to limit the number of offers to parse.

## Requirements
- Python 3.x
- Selenium WebDriver
- Pandas Library
- Openpyxl Library (for Pandas to work with Excel files)

## Setup
1. Ensure Python 3.x is installed on your system.
2. Install required Python libraries:
```
pip install selenium pandas openpyxl
```

3. Download the appropriate WebDriver for your browser and ensure it's in your PATH.
- For Chrome, download [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/).

## Usage
1. Prepare a text file `brands.txt` containing the car brands to parse, one brand per line.
2. Create a directory `links/` with text files named `links_<brand>.txt`, each containing links to Avito pages for the respective brand.
3. Run the script:
```
python avito_parser_popular.py --limit <number>
python avito_parser_nonpopular.py --limit <number>
```

- Replace `<number>` if necessary with the maximum number of offers you want to parse for each brand. Omit `--limit` to parse all available offers.

## Example Files Structure

avito_parser_popular.py
brands.txt
links/
links_toyota.txt
links_volkswagen.txt

## Contributing
Feel free to fork the repository and submit pull requests with any enhancements or bug fixes.

## License
Specify your project's license here, if applicable.

## Disclaimer
This script is intended for educational purposes and personal projects. Please respect Avito's terms of service when using this script.