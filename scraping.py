import selenium
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

"""Por algum motivo, às vezes o atributo .text retorna uma string vazia,
portanto usei o método que obtém o valor do atributo innerHTML."""

options = Options()
# Talvez seja necessário comentar a linha abaixo ou especificar o caminho do navegador
options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"
driver = webdriver.Firefox(options=options)

url = "https://genshin-impact.fandom.com/wiki/Category:Characters_by_Release_Date"
driver.get(url)

# Define listas para armazenar os dados
_hp = [0] * 14
_atk = _hp.copy()
_def = _hp.copy()
character_urls = []
data = []
levels = ["01/20", "20/20", "20/40", "40/40", "40/50", "50/50", "50/60",
        "60/60", "60/70", "70/70", "70/80", "80/80", "80/90", "90/90"]

elem = driver.find_element(By.CLASS_NAME, "category-page__members-for-char")
for item in elem.find_elements(By.TAG_NAME, "li"):
    character_urls.append(item.find_element(By.TAG_NAME, "a").get_attribute("href"))

# Execution time is approximately 2 minutes
for url in character_urls:
    driver.get(url)
    card = driver.find_element(By.CLASS_NAME, "portable-infobox")
    # Traveler has a different layout and shouldn't be included
    name = card.find_element(By.TAG_NAME, "h2").get_attribute("innerHTML")
    if name in ["Traveler", "Aloy"]:
        continue

    # driver.find_element(By.CLASS_NAME, "mw-customtoggle-toggle-ascension").find_element(
    #     By.XPATH, "//parent::*").click()
    stat_table = driver.find_element(By.CLASS_NAME, "ascension-stats").find_element(By.TAG_NAME, "tbody")
    rows = stat_table.find_elements(By.TAG_NAME, "tr")
    # Skips unreleased characters
    if len(rows) < 14:
        continue

    td = card.find_element(By.XPATH, "//section/table/tbody/tr").find_elements(By.TAG_NAME, "td")
    # Adds a new row to the data
    data.append([])
    new_data = data[-1]
    # Adds the name of the character, rarity, weapon, element, sex, region and release date
    new_data.append(name)
    new_data.append(td[0].find_element(By.TAG_NAME, "img").get_attribute("title")[0])
    new_data.append(td[1].get_attribute("innerHTML"))
    new_data.append(td[2].get_attribute("innerHTML"))
    new_data.append(card.find_element(By.XPATH,
        "//section[2]/div[2]/div/div/a").get_attribute("title").split()[1][0])  # Tall Female -> F
    try:
        new_data.append(card.find_element(By.XPATH,
            "//section[2]/div[2]/div[@data-source='region']/div/a").get_attribute("title").split()[0])
    except selenium.common.exceptions.NoSuchElementException:
        new_data.append(card.find_element(By.XPATH,
            "//section[2]/div[2]/div[@data-source='region']/div/ul/li/a").get_attribute("title").split()[0])
    text = card.find_element(By.XPATH,
        "//section[2]/div[2]/div[@data-source='releaseDate']/div").get_attribute("innerHTML")

    # new_data.append(datetime.strptime(text[:text.find("\n"), "%B %d, %Y").date())
    # datetime.date object made from character release date in format "January 01, 2020"
    new_data.append(datetime.strptime(text[:text.find("<br>")], "%B %d, %Y").date())

    # Gets the name of the ascension stat and changes any elemental damage bonus to the same name
    ascension = stat_table.find_element(By.XPATH, "//tr/th[6]/span/b/a").get_attribute("innerHTML")
    if ascension.endswith("Bonus"):
        ascension = "Elemental DMG"
    new_data.append(ascension)
    # Always the same sequence
    new_data.append(levels)

    index = 0
    for row in rows[1:]:
        if row.get_attribute("class").split()[0] == "ascension":
            continue
        row_data = row.find_elements(By.TAG_NAME, "td")
        correction = index % 2
        _hp[index] = row_data[2 - correction].get_attribute("innerHTML")
        _atk[index] = row_data[3 - correction].get_attribute("innerHTML")
        _def[index] = row_data[4 - correction].get_attribute("innerHTML")
        index += 1

    new_data.append(_hp.copy())
    new_data.append(_atk.copy())
    new_data.append(_def.copy())



df = pd.DataFrame(columns=["Name", "Rarity", "Weapon", "Element", "Sex", "Region", "Release Date",
                        "Ascension Stat", "Level", "HP", "ATK", "DEF"], data=data)
df.explode(["Level", "HP", "ATK", "DEF"]).set_index("Name").to_csv("data/genshin.csv", sep=";")

driver.close()
