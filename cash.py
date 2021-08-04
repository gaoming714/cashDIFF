"""
市场代码，上海是0， 深圳是1。判断深圳的办法是看代码0或者3开头。
深圳用的是re模块进行分析，上海用的是XPATH，最终存储到ticker_list & ticker_detail
ticker_list 是基础，从网页上爬下来的list。
当replaceFlag（现金替代）True是允许现金替代，False是必须，False也就是意味着reportAmount需要设置为0.

essential:
config.json
geckodriver.exe


run:
poetry run python cash.py

build for exe-onefile:
poetry run pyinstaller cash.py --onefile

"""


import re
import json
import time
import pendulum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located

software_build = "20210720A"

ticker_list = []
ticker_detail = {}
ticker_real_json = {}
ticker_market = ""
report_str = ""
welcome_msg = ""
debug_flag = None
quary_str = ""
market_time = ""

def tickerInit():
    global report_str
    global welcome_msg
    global debug_flag
    global ticker_real_json
    global ticker_market
    # get config
    data = None
    with open("config.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    ETF_code= data["ETFcode"]
    welcome_msg = data["welcome"]
    debug_flag = data["debug"]
    ticker_real_json = data["realAmount"]
    ticker_market = data["market"]
    # create query report
    date_str = str(pendulum.now("Asia/Shanghai").format("YYYYMMDD"))
    if ticker_market == "SZ" or ticker_market == "1":
        report_str = "http://reportdocs.static.szse.cn/files/text/etf/ETF" + ETF_code + date_str + ".txt?random=0.1"
    else:
        report_str = "http://www.sse.com.cn/disclosure/fund/etflist/detail.shtml?type=004&fundid=" + ETF_code + "&etfClass=1"
    if debug_flag == True:
        print("申购赎回清单 访问地址：")
        print(report_str)
        print()



def tickerWelcome():
    print("软件版本\t",software_build)
    print("当前运行时间\t", pendulum.now("Asia/Shanghai"))
    print(welcome_msg)
    print("\n申购赎回清单 访问地址：" , report_str, "\n")
    if ticker_market == "SZ" or ticker_market == "1":
        options = Options()
        options.add_argument('-headless') # headless
        with webdriver.Firefox(executable_path='geckodriver', options=options) as driver:
            wait = WebDriverWait(driver, 10)
            driver.get(report_str)
            # driver.get("http://reportdocs.static.szse.cn/files/text/etf/ETF15978320210706.txt")
            page_source = driver.page_source
            prettytableSZ(page_source)
    else:
        options = Options()
        options.add_argument('-headless') # headless
        with webdriver.Firefox(executable_path='geckodriver', options=options) as driver:
            wait = WebDriverWait(driver, 10)
            driver.get(report_str)
            xpath_str = "/html/body/div[8]/div[2]/div[2]/div[2]/div/div/div/div[1]/div[2]/div[4]/div[2]/div/div[2]/table/tbody"
            table_element = driver.find_element(By.XPATH,xpath_str)
            prettytableSH(table_element)
    # get detail  for market
    prettyquary()
    # show init message
    # print("全部申购赎回组合证券只数（不含 159900 证券） : ", len(ticker_list), "\n")
    if debug_flag == True:
        print("有效持仓数量")
        print(len(ticker_list))
        print()
        print("持仓列表")
        print(ticker_list)
        print()
        print("申购赎回清单json")
        print(ticker_detail)
        print()


def prettytableSZ(raw):
    global ticker_list
    global ticker_detail
    if debug_flag == True:
        print("申赎清单原始")
        print(raw)
        print()
    raw_list = re.split("---*\n",raw)[7]
    # report_list = re.split("挂牌市场\n|深圳市场\n|上海市场\n",report_raw)
    report_list = re.split("市场\n\s*",raw_list)
    report_list.pop(0)
    report_list.pop()
    for record in report_list:
        record_list = re.split("\s{3,}",record)
        code = record_list[0].strip()
        if code == "159900" :
            continue
        name = record_list[1].strip()
        realAmount =ticker_real_json[code]
        reportAmount = record_list[2].strip().replace(",","")
        if record_list[3].strip() == "允许":
            replaceFlag = True
        else:
            replaceFlag = False
        marketName = record_list[8].strip()
        if marketName == "深圳":
            marketFlag = "1"
        else:
            marketFlag = "0"

        ticker_list.append(code)
        ticker_detail[code]={}
        ticker_detail[code]["code"] = code
        ticker_detail[code]["name"] = name
        ticker_detail[code]["realAmount"] = realAmount
        ticker_detail[code]["reportAmount"] = reportAmount
        ticker_detail[code]["replaceFlag"] = replaceFlag
        ticker_detail[code]["marketName"] = marketName
        ticker_detail[code]["marketFlag"] = marketFlag
        ticker_detail[code]["codeAPI"] = marketFlag+code
        if replaceFlag == False:
            ticker_detail[code]["reportAmount"] = 0

def prettytableSH(element):
    global ticker_list
    global ticker_detail
    if debug_flag == True:
        print("申赎清单原始")
        print(element.text)
        print()
    code_els = element.find_elements(By.XPATH, "./tr/td[1]")
    name_els = element.find_elements(By.XPATH, "./tr/td[2]")
    reportAmount_els = element.find_elements(By.XPATH, "./tr/td[3]")
    replaceFlag_els = element.find_elements(By.XPATH, "./tr/td[4]")
    # code_els = element.find_elements(By.XPATH, "//tr/td[5]")
    # code_els = element.find_elements(By.XPATH, "//tr/td[6]")
    # code_els = element.find_elements(By.XPATH, "//tr/td[7]")
    for index, code_el in enumerate(code_els):
        code = code_el.text
        name = name_els[index].text
        realAmount = ticker_real_json[code]
        reportAmount = reportAmount_els[index].text
        if replaceFlag_els[index].text == "允许":
            replaceFlag = True
        else:
            replaceFlag = False
        if code[0] == "0" or code[0] == "3":
            marketFlag = "1"
        else:
            marketFlag = "0"
        ticker_list.append(code)
        ticker_detail[code]={}
        ticker_detail[code]["code"] = code
        ticker_detail[code]["name"] = name
        ticker_detail[code]["realAmount"] = realAmount
        ticker_detail[code]["reportAmount"] = reportAmount
        ticker_detail[code]["replaceFlag"] = replaceFlag
        # ticker_detail[code]["marketName"] = marketName
        ticker_detail[code]["marketFlag"] = marketFlag
        ticker_detail[code]["codeAPI"] = marketFlag+code
        if replaceFlag == False:
            ticker_detail[code]["reportAmount"] = 0
    # print(ticker_list)
    # print(ticker_detail)

def prettyquary():
    global quary_str
    quary_str += "http://api.money.126.net/data/feed/"
    for ticker in ticker_list:
        quary_str += ticker_detail[ticker]["codeAPI"]
        quary_str += ","
    quary_str += "0000001"



def tickerSelenium():
    global market_time
    global ticker_detail
    #This example requires Selenium WebDriver 3.13 or newer
    options = Options()
    options.add_argument('-headless') # headless
    with webdriver.Firefox(executable_path='geckodriver', options=options) as driver:
        wait = WebDriverWait(driver, 10)
        # driver.get("http://api.money.126.net/data/feed/"+ticker_raw)
        driver.get(quary_str)
        detail_raw = driver.find_element(By.XPATH, "/html/body/pre").text
        # print(ticker_raw)
        # print(driver.find_element(By.XPATH, "/html/body/pre").text)
        json_raw = re.split('[()]',detail_raw)[1]
        json_dict = json.loads(json_raw)
        for key, value in json_dict.items():
            tmp_key = value["symbol"]
            tmp_dict = {}
            # tmp_dict["code"] = value["symbol"]
            # tmp_dict["name"] = value["name"]
            tmp_dict["type"] = value["type"]
            tmp_dict["time"] = value["time"]
            tmp_dict["yestclose"] = value["yestclose"]
            tmp_dict["price"] = value["price"]
            tmp_dict["increase"] = value["price"] - value["yestclose"]
            if key != "0000001":
                ticker_detail[tmp_key].update(tmp_dict)
            else:
                market_time = value["time"]
    if debug_flag == True:
        print("带行情的详细信息")
        print(ticker_detail)
        print()

def tickerAddMargin():
    for code in ticker_list:
        realone = float(ticker_detail[code]["realAmount"])
        reportone = float(ticker_detail[code]["reportAmount"]) 
        increaseone = float(ticker_detail[code]["increase"])
        margin = (realone - reportone) * increaseone
        ticker_detail[code]["margin"] = margin

def tickerShow():
    total = 0
    for ticker in ticker_list:
        total = total + ticker_detail[ticker]["margin"]
    print(market_time, "   ", round(total,2))


if __name__=="__main__":
    tickerInit()
    tickerWelcome()
    # tickerInput()
    while True:
        tickerSelenium()
        tickerAddMargin()
        tickerShow()
        time.sleep(3)
