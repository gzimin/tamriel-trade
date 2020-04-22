import requests

from bs4 import BeautifulSoup

import time

import re


def filtering_data(value, num_type=None, digit=True):
    if num_type is None or num_type in value.text:
        value = value.text
        if num_type:
            value = value.replace(num_type, "")
        value = value.replace("\n", "")
        value = value.replace("\r", "")
        value = value.replace(" ", "")
        value = value.replace(",", "")
        if digit:
            if "." in value:
                value = value.split(".")[0]
            value = int(value)
        return value
    return False


def alternate_get_item_names(soup, url):
    captcha = soup.find("div", {"class": "g-recaptcha"})
    if captcha:
        print("We catch captcha, go here: {}".format(url))
        print("Then press ENTER")
        input()
    all_names_list = []
    all_names = soup.findAll("div", {"class": "item-quality-epic"})
    for name in all_names:
        name = name.text.strip()
        all_names_list.append(name)
    return all_names_list


def get_item_names(soup, items_url):
    # Here we takes names of the products, return list of names
    trade_table = soup.find(class_="trade-list-table")
    item_names = []
    try:
        trade_table.tbody
    except AttributeError:
        print("Seems like we catch captcha, check {}".format(items_url))
        print("If there is a captcha, pass it, than type OK")
        ok = input()
        if ok == "OK":
            page = requests.get(items_url)
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
    return item_names


def suggested_items_calc(items_with_suggested_prices_url, file_name):

    page = requests.get(items_with_suggested_prices_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    suggested_prices = soup.findAll("span", {"class": "gold-amount bold"})

    item_names = alternate_get_item_names(soup, items_with_suggested_prices_url)
    # Gather all suggested prices
    # We need to create some flag to get only half of this values
    first_suggested_prices = []
    flag = True
    for suggested_price in suggested_prices:
        # import pdb; pdb.set_trace()
        if flag:
            first_price = filtering_data(suggested_price)
            if first_price:
                first_suggested_prices.append(first_price)
        flag = not flag

    # Write Item and suggested price to db file
    file = open(file_name, "a")
    for item_name, suggested_price in zip(item_names, first_suggested_prices):
        whole_string = "{:>40} {:>30}\n".format(item_name, suggested_price)
        file.write(whole_string)
    file.close()


def suggested_items_print():
    items_with_suggested_prices_url = 'https://eu.tamrieltradecentre.com/pc/Trade/SearchResult?ItemID=&SearchType=PriceCheck' \
                                 '&ItemNamePattern=&ItemCategory1ID=3&ItemCategory2ID=17&ItemTraitID=&ItemQualityID=3' \
                                 '&IsChampionPoint=false&LevelMin=&LevelMax=&MasterWritVoucherMin=&MasterWritVoucherMax=&page=1'
    page = requests.get(items_with_suggested_prices_url)
    soup = BeautifulSoup(page.text, 'html.parser')

    # get last page of this database
    page_list = soup.findAll("a", {"class": "hidden-sm hidden-xs"})
    last_page = int(page_list[1].text)

    print("Type database filename:")
    file_name = input()
    print("This file will be overrided")
    file = open(file_name, "w")
    print("file {} was cleaned".format(file_name))
    file.write("{:>35} {:>40}\n".format("Item", "Suggested price"))
    file.close()
    start_time = time.time()
    print("Calculating...\n")

    for i in range(1, last_page + 1):
        items_with_suggested_prices_url = \
            items_with_suggested_prices_url.replace("&page=" + str(i), "&page=" + str(i + 1))
        suggested_items_calc(items_with_suggested_prices_url,  file_name)
        print(items_with_suggested_prices_url[-10:])
        print("Page {}/{} complete!".format(str(i), str(last_page)))
    end_time = time.time()

    print("Done, check {} file".format(file_name))
    print("Elapsed time: {:03.2f} seconds".format(end_time - start_time))


def get_suggested_items_from_db(filename):
    suggested_items_list = []
    suggested_items_dict = {}
    with open(filename, 'r+') as suggested_items_file:
        suggested_items_list = suggested_items_file.readlines()
    suggested_items_list = suggested_items_list[1:]
    for item in suggested_items_list:
        test = item.replace("  ", " ")
        test = ' '.join(test.split())
        name = ' '.join(test.split()[:-1])
        price = int(test.split(' ')[-1])
        suggested_items_dict[name] = price
    return suggested_items_dict


def recent_items_calc(suggested_items_dict, matches_db_filename, page_count=50):
    recent_items_url = "https://eu.tamrieltradecentre.com/pc/Trade/SearchResult?ItemID=&SearchType=Sell" \
                       "&ItemNamePattern=&ItemCategory1ID=3&ItemCategory2ID=17&ItemTraitID=&ItemQualityID=3" \
                       "&IsChampionPoint=false&LevelMin=&LevelMax=&MasterWritVoucherMin=&MasterWritVoucherMax" \
                       "=&AmountMin=&AmountMax=&PriceMin=&PriceMax=&page=1 "

    matches_db = open(matches_db_filename, 'w+')
    matches_db.write("{:>30} {:>20} {:>20}".format("Item name", "Current Price", "Suggested Price"))
    for i in range(1, page_count + 1):
        database_url = recent_items_url.replace("&page=" + str(i), "&page=" + str(i + 1))
        page = requests.get(database_url)
        soup = BeautifulSoup(page.text, 'html.parser')

        # Get names of items
        item_names = alternate_get_item_names(soup, database_url)

        flag = False
        # Get prices and create new db file with matches
        all_prices = soup.findAll("td", {"class": "gold-amount bold"})
        for price, item_name in zip(all_prices, item_names):
            if suggested_items_dict.get(item_name):
                price = filtering_data(price, num_type=None, digit=False)
                price = price.split('X')[0]
                if suggested_items_dict.get(item_name) > int(price) * 1.5:
                    matches_db.write("{} {} {}".format(item_name, price, suggested_items_dict.get(item_name)))
                    flag = True

        print("Page {}/{} is done!".format(str(i), str(page_count)))
        if flag:
            print("We found something! Check db")
        else:
            print("Empty...")
        time.sleep(5)
    matches_db.close()
    print("Search done, check {} file".format(matches_db_filename))


def main():
    print("Collect suggested items or recent? (1/2)")
    answer = input()
    if answer == "1":
        suggested_items_print()
    elif answer == "2":
        print("Insert filename of db with suggested items:")
        filename = input()
        suggested_items_dict = get_suggested_items_from_db(filename)
        recent_items_calc(suggested_items_dict=suggested_items_dict, matches_db_filename="matches_db")
    else:
        print("Wrong answer, try again...")
        return 0


if __name__ == '__main__':
    main()
