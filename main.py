import chromedriver_autoinstaller
import requests
import string
import time
import json
from selenium import webdriver
from newspaper import Article
from collections import Counter
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By


# const for strings
BBC_URL = "https://bbc.com"
BBC_URL_NEWS = "https://bbc.com/news"
BBC_SPORT_URL = "https://www.bbc.com/sport/cricket/60050911"
ENGLISH = 'en'
BEN_GURION_URL = "http://www.iaa.gov.il/he-IL/airports/BenGurion/Pages/OnlineFlights.aspx"
STRING_CHECK = "@Nadav Halevy"
FIRST_ROW = 0
LAST_ROW = 88
SLEEP_TIME = 10
HEADERS_XPATH = "//table[@id='flight_board-arrivel_table']//thead"
TABLE_XPATH = "//tbody"
SENTENCE_THAT_APPEAR_IN_TEXT = "Big Bash match"
SENTENCE_THAT_APPEAR_IN_FLIGHT_ROW = "זמן עדכני"


class BbcArticle:

    def __init__(self):
        self.news_urls = []

    def response_for_soup(self, url):

        response = requests.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        return soup

    def save_links_from_main_page(self, url):
        print("Wait while the system loads the articles from the main page, can take about a minute")
        new_links = (self.response_for_soup(url)).findAll("a")
        for link in new_links:
            href = link.get("href")
            if href.startswith("/news") and href[-1].isdigit():
                news_url = BBC_URL + href
                self.news_urls.append(news_url)

    # print all articles from main page
    def print_all_url_articles(self, url):

        soup = self.response_for_soup(url)
        all_nouns = []
        for one_url in self.news_urls[:10]:
            print("Fetching {}".format(one_url))
            words = soup.text.split()
            nouns = [word for word in words if word.isalpha() and word[0] in string.ascii_uppercase]
            all_nouns += nouns
        print(Counter(all_nouns).most_common(100))

    # download and save article
    def get_article_text(self, url):

        new_article = Article(url, language=ENGLISH)  # English language='en'
        new_article.download()
        new_article.parse()
        return new_article.text

    # Check if a word or phrase appears in the article
    def check_if_appear_in_the_article(self, url, sentence):

        new_article = Article(url, language=ENGLISH)  # English language='en'
        new_article.download()
        new_article.parse()
        if sentence in new_article.text:
            print("The sentence: '%s' query found" % sentence)
        else:
            print("The sentence: '%s' query not found" % sentence)


class FlightsTable:

    def __init__(self, new_driver):
        self.driver = new_driver

    # download and save headers table from web
    def get_column_info(self):

        column_info = []
        time.sleep(SLEEP_TIME)
        new_columns = self.driver.find_elements(By.XPATH, HEADERS_XPATH)
        for column in new_columns:
            column_info.append(str(column.text))
        split_columns = column_info[0].split(" ")
        sort_columns = [split_columns[0] + " " + split_columns[1],
                        split_columns[2],
                        split_columns[3] + " " + split_columns[4],
                        split_columns[5],
                        split_columns[6] + " " + split_columns[7],
                        split_columns[8] + " " + split_columns[9],
                        split_columns[10]]
        return sort_columns

    def get_data_from_table(self):

        data_info = []
        time.sleep(SLEEP_TIME)
        data = self.driver.find_elements(By.XPATH, TABLE_XPATH)
        for d in data:
            data_info.append(str(d.text))
        tabledata = data_info[2].split("\n")
        return tabledata

    def get_one_row_from_table(self, new_table_data, index):

        element = [new_table_data[index],
                   new_table_data[index + 1],
                   new_table_data[index + 2],
                   new_table_data[index + 3],
                   new_table_data[index + 4] + ", " + new_table_data[index + 5],
                   new_table_data[index + 6],
                   new_table_data[index + 7]]
        return element;

    def make_row_to_json(self, column_table, element):

        string_flight = {
            column_table[0]: element[0],
            column_table[1]: element[1],
            column_table[2]: element[2],
            column_table[3]: element[3],
            column_table[4]: element[4],
            column_table[5]: element[5],
            column_table[6]: element[6],
        }
        json_flight = json.dumps(string_flight, ensure_ascii=False)
        return json_flight

    def check_if_appear_in_a_json(self, json_data, sentence):
        if sentence in json_data:
            print("%s is found in JSON data" % sentence)
        else:
            print("%s is not found in JSON data" % sentence)


if __name__ == '__main__':

    # Function test - BBC

    article = BbcArticle()
    # save all url articles from main page
    article.save_links_from_main_page(BBC_URL_NEWS)
    print("The system print all url articles from main page: (can take about a minute)")
    article.print_all_url_articles(BBC_URL_NEWS)
    print("The system print a specific article text")
    print(article.get_article_text(BBC_SPORT_URL))
    print("The system check if sentence apper in a specific article")
    article.check_if_appear_in_the_article(BBC_SPORT_URL, STRING_CHECK)
    article.check_if_appear_in_the_article(BBC_SPORT_URL, SENTENCE_THAT_APPEAR_IN_TEXT)

    # test - download data from flights table

    # Check if the current version of chromedriver exists
    # and if it doesn't exist, download it automatically,
    # then add chromedriver to path
    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    driver.get(BEN_GURION_URL)
    table = FlightsTable(driver)
    columns = table.get_column_info()
    table_data = table.get_data_from_table()
    print("The system print all flight table data")
    print(table_data)
    # Select a row from the flight table,
    # first row starts at 0,
    # second row starts at 8,
    # row 3 at 16 and so on until last row (12) starts at 88ץ
    first_element = table.get_one_row_from_table(table_data, FIRST_ROW)
    last_element = table.get_one_row_from_table(table_data, LAST_ROW)
    print("The system print the first row in table")
    print(table.make_row_to_json(columns, first_element))
    print("The system print the last row in table")
    print(table.make_row_to_json(columns, last_element))
    json_element = table.make_row_to_json(columns, first_element)
    print("The system check if sentence apper in a json")
    table.check_if_appear_in_a_json(json_element,STRING_CHECK)
    table.check_if_appear_in_a_json(json_element, SENTENCE_THAT_APPEAR_IN_FLIGHT_ROW)
    driver.close()

