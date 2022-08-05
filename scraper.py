import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

from oauth2client.service_account import ServiceAccountCredentials
import gspread

import time

def connect_gspread(file_name):
    scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    ]
    json_file_name = 'lxper.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
    gc = gspread.authorize(credentials)
    sheets = gc.open(file_name)

    return sheets

def write_gspread(worksheet, index, result):
    last_alphabet = chr(65 + len(result))

    try:
        worksheet.update(f"A{index}:{last_alphabet}{index}", [result])
    except:
        print(f"{index} index got error while gspread writing")

def init_driver(url, version):
    # option for browser
    browser = uc.Chrome(version_main=version, suppress_welcome=False)
    browser.maximize_window()
    browser.implicitly_wait(10)

    # init
    browser.get(url)

    # cloudflare force wait 5sec
    time.sleep(6)

    return browser

def get_total_page(browser):

    try:
        time.sleep(2)
        total_page = browser.find_elements(By.CSS_SELECTOR, "a.page-number-link")[-2].text
    except:
        print("no pagination element load!")

    return int(total_page)

def scrape_text_content():
    pass

if  __name__  ==  "__main__" :
    CHROME_VERSION = 103
    GSPREAD = "Reading Text Scraping"
    TEXT_URL = "https://www.commonlit.org/en/library?contentTypes=text&initiatedFrom=library"
    
    browser = init_driver(TEXT_URL, CHROME_VERSION)
    
    total_page = get_total_page(browser)

    # start page loop
    for page in range(1, total_page+1):
        print(f"========== {page} page start ==========")

        time.sleep(2)
        browser.get(f"{TEXT_URL}&page={page}")
        
        contents = browser.find_elements(By.CSS_SELECTOR, ".content-cards li")
        
        # start contents loop
        for index, content in enumerate(contents):
            time.sleep(2)
            content.click()

            browser.find_elements(By.CSS_SELECTOR, "h1")
            
            # start scrape [meta data]
            link = browser.current_url

            try:
                title = browser.find_element(By.CSS_SELECTOR, "h1").text
            except:
                title = ""

            try:
                author = [item for item in browser.find_elements(By.CSS_SELECTOR, ".cl-text__author-info-subinfo h2")][0].text
                if "by" in author: author = author.split("by ")[-1]
            except:
                author = ""

            try:
                created = [item for item in browser.find_elements(By.CSS_SELECTOR, ".cl-text__author-info-subinfo h2")][-1].text
            except:
                created = ""

            try:
                grade = browser.find_elements(By.CSS_SELECTOR, ".grade-lexile-container span")[0].text.split(" ")[-1]
            except:
                grade = ""            
            
            try:
                lexile = browser.find_elements(By.CSS_SELECTOR, ".grade-lexile-container span")[-1].text.split(" ")[-1]
            except:
                lexile = ""
            
            # start scrape [text]
            try:
                text = ""

                # div
                divs = browser.find_elements(By.CSS_SELECTOR, "div.cl-text__excerpt-line-container")
                
                paragraphs = browser.find_elements(By.CSS_SELECTOR, "p.cl-text__excerpt-line")

                for div in divs:

                    paragraph = ""

                    if div.find_element(By.XPATH, "./*").tag_name == "h2":
                        h2 = div.find_element(By.XPATH, "./h2")
                        text += f"/n/n{h2.text}/n/n"

                    if div.find_element(By.XPATH, "./*").tag_name == "p":
                        p = div.find_element(By.XPATH, "./p")

                        nodes = p.find_elements(By.XPATH, './*')
                        span_nodes = p.find_elements(By.XPATH, './span[@data-read-aloud-highlight="true"]')

                        # if a paragraph consist of several nodes
                        if len(nodes) > 1:
                            
                            # span node = necessary text
                            # span nodes ==> paragraph
                            for span_node in span_nodes:
                                paragraph += f"{span_node.text } " if span_node != span_nodes[-1] else f"{span_node.text}"

                            # paragraph ==> text
                            text += f"{paragraph}\n" if p != paragraphs[-1] else f"{paragraph}"

                        # if a paragraph consists of only one node
                        else:
                            text += f"{p.text}\n" if p != paragraphs[-1] else f"{p.text}"
                
            except:
                text = "" 
            
            browser.back()
            print(f"{index+1} / {len(contents)} done")

        print(f"========== {page} page finished ==========") 
           
    print("debug")

