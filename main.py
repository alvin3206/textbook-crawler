# -*- coding: utf-8 -*-
# 一、把取得的html純文字送給BeautifulSoup，產生BeautifulSoup類別
from bs4 import BeautifulSoup
import requests
import time
start_time = time.time()
import pandas as pd

# 設定參數=================================================================
nation = "United States"
exclude_word = ["international edition", "international"]
include_word = ["international ship", "ship internation"]
income_diff = 0.01
timeout = 15
# order = 200

# ========================================================================
# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

# ========================================================================
# 加入資料庫(利用 Pandas)
# Larger source
df = pd.read_csv("Book-Data-Sheet.csv")

# Smaller test case
# df = pd.read_csv("Book-Data-Sheet-cut.csv")
isbn_lib = df["ISBN/ID"].tolist()
temp_lib = isbn_lib[:]

for i in isbn_lib:
    try:
        if (len(i) != 10) and (len(i) != 13) or i.isdigit() == False :
            temp_lib.remove(i)
    except:
        temp_lib.remove(i)
isbn_lib = temp_lib[:]
filter_len = len(isbn_lib);
print("--- Data Filter Finished in %5.3f seconds. Got %i usable records ---" % (time.time() - start_time, filter_len))

# ========================================================================
count = 0
earn_count = 0
# temp_time = time.time()
f_text = open("bookBenefit.txt", "w")

# proxies = {"https": "https://142.93.62.60:3128", "http": "http://142.93.62.60:3128"}
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36", "Accept-Encoding": "identity"}

print("Stat scraping data from internet...")
# print progress bar
printProgressBar(0, filter_len, prefix = 'Progress:', suffix = 'Complete', length = 50)
# 遞迴ISBN資料庫
for book in isbn_lib:
    # print progress bar
    count += 1
    printProgressBar(count, filter_len, prefix = 'Progress:', suffix = 'Complete', length = 50)

    # temp test break
    # if count >= order:
    #     break
    # count += 1
    # print(str(count) + ":" + str(time.time() - temp_time))
    # temp_time = time.time()

    # 每本書的參數
    income = 0.0
    buy_price = 0.0
    lowest_used_price = 0

    try:
        req = requests.get("https://www.bookfinder.com/search/?keywords=" + book +
                "&currency=USD&destination=us&mode=basic&lang=en&st=sh&ac=qr&submit=", headers = headers, timeout = timeout)
                # , proxies=proxies
    except (requests.exceptions.Timeout,):
        print("requests timeout")
        continue

    soup = BeautifulSoup(req.text, "lxml")

    # <尋找收購價格>
    # 建立篩選器
    selector_buy_price = "#buyback_table a"
    try:
        # 取得價格字串並轉換
        temp_bp_selector = soup.select(selector_buy_price)
        # 價格為篩選過後最後一個<a>
        str_buy_price = temp_bp_selector[len(temp_bp_selector) - 1].string
        # 去除$符號
        buy_price = float(str_buy_price[1:len(str_buy_price)])

    # 排除為空list的情況，跳至下一本書(isbn)
    except (AttributeError,IndexError):
        continue


    # <尋找二手書籍的最低價>
    # 找出 class 為 results-table-Logo
    result_table = soup.find_all("table", "results-table-Logo")

    # 排除沒有新書的情況(只有二手書時，len(result_talbe) == 1)
    if len(result_table) > 1:
        # print("================")
        # 重設暫存參數
        temp_used_price = 0
        good_data_row = []

        # 讀取每筆資料
        used_data_row = result_table[1].find_all("tr")


        # 多重判斷，只留下比收購價低的二手書 且 二手書來自美國網站 且 敘述中沒有提到"internation edition"的版本
        for row in used_data_row:

            # 尋找第一筆二手書的價格
            try :
                temp_used_price = float(row["data-price"])

            # 排除標題(沒有 "data-price" 屬性)
            except (NameError,KeyError):
                continue

            else:
                # 二手書的價格高於收購價時
                if temp_used_price > buy_price:
                    next_book = True
                    break

                # 二手書的價格低於收購價時
                else:

                    # 建立來自"美國網站"的過濾器selector
                    src_temp_selector = row.select(".results-table-center .results-explanatory-text-Logo")
                    # 二次過濾，"United States"為list的最後一個index的內容
                    src_nation = src_temp_selector[len(src_temp_selector) - 1].string.lower()

                    # 排除非"United States"的書籍(轉小寫比對)
                    if nation.lower() not in src_nation:
                        continue

                    # 排除敘述中有提到"international edition"的版本
                    else:
                        desc = str(row.select(".item-note")[0]).lower()
                        is_in = False
                        for e in exclude_word:
                            if (e in desc):
                                is_in = True
                                break
                                # 沒有提到"international edition"
                            else:
                                continue

                        if is_in == True:
                            continue
                        else:
                            # 儲存價格和連結
                            lowest_used_price = temp_used_price
                            link_src = row.select(".results-price a")[0]["href"]
                            good_data_row.append([lowest_used_price,src_nation,link_src])

        # 二手書的價格低於收購價時 且 good_data_row 沒有內容時，換一本
        if next_book == True and len(good_data_row) == 0 :
            continue

    # 沒有新書的情況(只有新書時，len(result_table) == 1)
    else:
        continue

    # Save file
    income = buy_price - good_data_row[0][0]
    if income > income_diff:
        earn_count += 1
        print("start-----------------------------")
        print("Isbn:", isbn)
        print("Isbn:", book , " 收益",income)
        print("賣出:", buy_price, "買入",good_data_row[0][0])
        for line in good_data_row:
            print(line[0],line[1])
        print("----------------------------------")
        f_text = open("bookBenefit.txt", "a")
        f_text.write("-----------------------------\n")
        f_text.write(time.strftime("%Y-%m-%d %H:%M:%S")+"\n")
        f_text.write("Isbn:" + book + "\n")
        f_text.write("收益" + str(income) + "\n")
        f_text.write("賣出:" + str(buy_price) + "買入" + str(good_data_row[0][0]) + "\n")
        f_text.close()

# browser.quit()
print("--- Found %i textbooks are profitable. Done in %s seconds ---" % (earn_count, time.time() - start_time))
