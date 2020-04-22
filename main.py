import requests

from bs4 import BeautifulSoup

import time


def make_num_from_string(value, num_type=None):
    if num_type is None or num_type in value.text:
        value = value.text
        if num_type:
            value = value.replace(num_type, "")
        value = value.replace("\n", "")
        value = value.replace("\r", "")
        value = value.replace(" ", "")
        value = value.replace(",", "")
        if "." in value:
            value = value.split(".")[0]
        value = int(value)
        return value
    return False


def main_calculation(database_url, file_name):
    page = requests.get(database_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    aggregate_prices = soup.findAll("div", {"class": "bold"})
    suggested_prices = soup.findAll("span", {"class": "gold-amount bold"})
    trade_table = soup.find(class_="trade-list-table")
    item_names = []
    # Here we takes names of the products
    try:
        trade_table.tbody
    except AttributeError:
        print("Seems like we catch captcha, check {}".format(database_url))
        print("If there is a captcha, pass it, than type OK")
        ok = input()
        if ok == "OK":
            page = requests.get(database_url)
            soup = BeautifulSoup(page.text, 'html.parser')
            trade_table = soup.find(class_="trade-list-table")
            pass
        else:
            print("Trying to get trade table with another class\n")
            trade_table = soup.find(class_="trade-list-table max-width")
    for column in trade_table.tbody:
        try:
            name = column.div.text.strip()
            item_names.append(name)
        except AttributeError:
            pass

    # Calc min prices
    min_prices = []
    for price in aggregate_prices:
        # import pdb; pdb.set_trace()
        price = make_num_from_string(price, "Min:")
        if price:
            min_prices.append(price)

    # We need to create some flag to get only half of this values
    first_suggested_prices = []
    flag = True
    for suggested_price in suggested_prices:
        # import pdb; pdb.set_trace()
        if flag:
            first_price = make_num_from_string(suggested_price)
            if first_price:
                first_suggested_prices.append(first_price)
        flag = not flag

    # Write all useful information to file
    file = open(file_name, "a")
    for min_price, suggested_price in zip(min_prices, first_suggested_prices):
        if (suggested_price / min_price) >= 2:
            price_index = min_prices.index(min_price)
            whole_string = "{:>40} {:>30} {:>30}\n".format(
                item_names[price_index], str(min_price), str(suggested_price))
            # whole_string = item_names[price_index] + '\t\t\t\t\t\t' + \
            #                str(min_price) + '\t\t\t\t' + str(suggested_price) + '\n'
            file.write(whole_string)
    file.close()


def main():
    database_url = "https://eu.tamrieltradecentre.com/pc/Trade/SearchResult?ItemID=&SearchType=PriceCheck" \
                   "&ItemNamePattern=&ItemCategory1ID=3&ItemCategory2ID=17&ItemTraitID=&ItemQualityID=3" \
                   "&IsChampionPoint=false&LevelMin=&LevelMax=&MasterWritVoucherMin=&MasterWritVoucherMax=&page=1 "
    page = requests.get(database_url)
    soup = BeautifulSoup(page.text, 'html.parser')

    # get last page of this database
    page_list = soup.findAll("a", {"class": "hidden-sm hidden-xs"})
    last_page = int(page_list[1].text)
    # import pdb; pdb.set_trace()

    print("Type database filename:")
    file_name = input()
    print("This file will be overrided")
    file = open(file_name, "w")
    print("file {} was cleaned".format(file_name))
    file.write("{:>25} {:>45} {:>30}\n".format("Item", "Min. price", "Suggested price"))
    file.close()
    start_time = time.time()
    print("Calculating...\n")

    for i in range(1, last_page):
        database_url = database_url.replace("&page=" + str(i), "&page=" + str(i + 1))
        main_calculation(database_url, file_name)
        print("Page {}/{} complete!".format(str(i), str(last_page)))
    end_time = time.time()

    print("Done, check {} file".format(file_name))
    print("Elapsed time: {:03.2f} seconds".format(end_time - start_time))


main()
# def test():
#     first = "asdasdasdasdasda"
#     second = "123.123123"
#     third = "121231233.12"
#     f_1 = "1233333333333333"
#     s_2 = "0"
#     t_3 = "12312312312312"
#     print("{:>15} {:>15} {:>15}".format(f_1, s_2, t_3))
#     print("{:>15} {:>15} {:>15}".format(first, second, third))
# test()