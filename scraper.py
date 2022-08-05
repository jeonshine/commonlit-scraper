import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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
        # over 50000 string in one cell ==> error
        print(f"{index} index got error while gspread writing")

def init_driver(url, version):

    # option for browser
    browser = uc.Chrome(version_main=version, suppress_welcome=True)
    browser.maximize_window()
    browser.implicitly_wait(10)

    # init browser
    browser.get(url)

    # cloudflare protection ==> wait 5sec
    time.sleep(6)

    return browser

def login(browser):
    time.sleep(1)
    login_button = browser.find_element(By.XPATH, '//a[@id="login"]')
    login_button.click()

    email_input = browser.find_element(By.XPATH, '//input[@name="login"]')
    password_input = browser.find_element(By.XPATH, '//input[@name="password"]')

    email_input.send_keys("hojongjeon@lxper.com")
    password_input.send_keys("hojongjeon@lxper.com")
    password_input.send_keys(Keys.RETURN)

def get_last_page(browser):

    try:
        time.sleep(2)
        last_page = browser.find_elements(By.CSS_SELECTOR, "a.page-number-link")[-2].text
    except:
        print("no pagination element load!")

    return int(last_page)

def scrape(browser, content_links, worksheet, content_count):

    for index, content in enumerate(content_links):
        
        result = []

        time.sleep(1)
        browser.get(content)
        
        # start scrape [meta data]
        link = browser.current_url

        try:
            img = browser.find_element(By.CSS_SELECTOR, "div.cl-text__excerpt img").get_attribute("src")
        except:
            img = ""

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
            grade = browser.find_elements(By.CSS_SELECTOR, ".grade-lexile-container span")[0].text.split(" ")[0]
        except:
            grade = ""            
        
        try:
            lexile = browser.find_elements(By.CSS_SELECTOR, ".grade-lexile-container span")[-1].text.split(" ")[-1]
        except:
            lexile = ""
        
        # start scrape [text]
        try:
            text = ""

            # div > p or h2 > nodes
            divs = browser.find_elements(By.CSS_SELECTOR, "div.cl-text__excerpt-line-container")
            
            paragraphs = browser.find_elements(By.CSS_SELECTOR, "p.cl-text__excerpt-line")

            # one paragraph
            if len(divs) == 1:

                span_nodes = divs[0].find_elements(By.XPATH, './/span[@data-read-aloud-highlight="true"]')

                # span_nodes = necessary text
                for span_node in span_nodes:
                    text += f"{span_node.text } " if span_node != span_nodes[-1] else f"{span_node.text}"

                result.extend([
                    link, 
                    img,
                    title, 
                    author,
                    created,
                    grade,
                    lexile,
                    text])
                
                write_gspread(worksheet, content_count+index+1, result)

                continue

            # several paragraphs
            for div in divs:

                paragraph = ""

                # h2
                if div.find_element(By.XPATH, "./*").tag_name == "h2":

                    h2 = div.find_element(By.XPATH, "./h2")
                    text += f"\n\n{h2.text}\n\n"

                # p
                if div.find_element(By.XPATH, "./*").tag_name == "p":

                    p = div.find_element(By.XPATH, "./p")

                    nodes = p.find_elements(By.XPATH, './*')
                    span_nodes = p.find_elements(By.XPATH, './/span[@data-read-aloud-highlight="true"]')

                    # if a p consist of several nodes
                    if len(nodes) > 1:
                        
                        # span_nodes = necessary text
                        for span_node in span_nodes:
                            paragraph += f"{span_node.text } " if span_node != span_nodes[-1] else f"{span_node.text}"

                        # paragraph ==> text
                        text += f"{paragraph}\n" if p != paragraphs[-1] else f"{paragraph}"

                    # if a paragraph consists of only one node
                    else:
                        text += f"{p.text}\n" if p != paragraphs[-1] else f"{p.text}"
            
        except:
            text = "" 

        result.extend([
            link, 
            img,
            title, 
            author,
            created,
            grade,
            lexile,
            text])
        
        write_gspread(worksheet, content_count+index+1, result)
        print(f"{index+1} / {len(content_links)} done")

if  __name__  ==  "__main__" :
    
    # google sperad 
    GSPREAD = "Reading Text Scraping"
    RETRY_SHEET = "retry"
    TEXTS_SHEET = "CommonLit texts"
    sheets = connect_gspread(GSPREAD)
    worksheet = sheets.worksheet(TEXTS_SHEET)
    retry_worksheet = sheets.worksheet(RETRY_SHEET)
    
    # commonlit url
    ROOT_URL = "https://www.commonlit.org"
    TEXTS_URL = "https://www.commonlit.org/en/library?contentTypes=text&initiatedFrom=library"
    
    # chorme version
    CHROME_VERSION = 103
    browser = init_driver(TEXTS_URL, CHROME_VERSION)
    
    # last page number
    last_page = get_last_page(browser)

    # some contents are not accessed without login
    login(browser)

    # re-try 
    content_links = retry_worksheet.col_values(1)
    if content_links:
        scrape(browser, content_links, retry_worksheet, content_count=0)

    # start page loop
    content_count = 0
    for page in range(1, last_page+1):
        print(f"========== {page} / {last_page} page start ==========")

        time.sleep(2)
        browser.get(f"{TEXTS_URL}&page={page}")
        
        # contents per page
        contents = browser.find_elements(By.XPATH, '//a[@data-test="cl-card-link"]')
        content_links = [content.get_attribute("href") for content in contents]

        scrape(browser, content_links, worksheet, content_count)
        content_count += len(content_links)

        print(f"========== {page} / {last_page} page finish ==========") 
           
    print("debug")

