import requests

from bs4 import BeautifulSoup

# Constant name of items quality
QUALITIES = {
    "normal": "ItemQualityID=0",
    "fine": "ItemQualityID=1",
    "superior": "ItemQualityID=2",
    "epic": "ItemQualityID=3",
    "legendary": "ItemQualityID=4",
    }

DIV_QUALITIES = {
    "normal": "item-quality-normal",
    "fine": "item-quality-fine",
    "superior": "item-quality-superior",
    "epic": "item-quality-epic",
    "legendary": "item-quality-legendary",
    }


def calc_maximum_pages(items_url):
    # Set very big num to page to get real last page
    if "&page=" in items_url:
        page_num_length = len(items_url.split("&page=")[1])
        num = "100000"
        items_url = items_url[:-page_num_length] + num
    else:
        items_url = items_url + "&page=100000000"

    page = requests.get(items_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    captcha = soup.find("div", {"class": "g-recaptcha"})
    if captcha:
        print("We catch captcha, go here: {}".format(items_url))
        input("Press ENTER:")
    page = requests.get(items_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    num_page = soup.find("li", {"class": "active"})

    return num_page.text


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
    item_quality = ''
    for key, value in QUALITIES.items():
        if value in url:
            db_filename = url + "_" + key
            item_quality = DIV_QUALITIES[key]
            break
    captcha = soup.find("div", {"class": "g-recaptcha"})
    if captcha:
        print("We catch captcha, go here: {}".format(url))
        print("Then press ENTER")
        input()
    all_names_list = []
    all_names = soup.findAll("div", {"class": item_quality})
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


def get_items_with_suggested_price(base_items_url, page_count=None):

    item_quality = "item-quality-epic"
    # Check quality of items
    db_filename = "db"
    for key, value in QUALITIES.items():
        if value in base_items_url:
            db_filename = db_filename + "_" + key
            item_quality = DIV_QUALITIES[key]
            break

    print("Getting items with suggested prices:\n"
          "Base Link = {}\n"
          "Page Count = {}\n"
          "Database Filename = {}\n".format(base_items_url, page_count, db_filename))

    # Once open file for write titles
    with open(db_filename, 'w+') as db_file:
        db_file.write("{:>35} {:>40}\n".format("Item", "Suggested price"))

    # Check page argument in url
    if "&page=" in base_items_url:
        page_num_length = len(base_items_url.split("&page=")[1])
        base_items_url = base_items_url[:-page_num_length] + "1"
    else:
        base_items_url = base_items_url + "&page=0"

    # Write all data
    for i in range(page_count):
        base_items_url = base_items_url.replace("&page=" + str(i), "&page=" + str(i + 1))
        page = requests.get(base_items_url)
        soup = BeautifulSoup(page.text, 'html.parser')

        # Check for captcha
        if not soup.find("table", {"class": "trade-list-table"}):
            print("We catch captcha, go to:\n {}".format(base_items_url))
            input("Then press Enter here:")
            page = requests.get(base_items_url)
            soup = BeautifulSoup(page.text, 'html.parser')

        # Get all body elements
        tbody_elem = soup.find("tbody")
        list_of_items = tbody_elem.findAll("tr")
        for item in list_of_items:
            if not item.has_attr("class"):
                if item.find("span", {"class": "gold-amount bold"}):
                    suggested_price = item.find("span", {"class": "gold-amount bold"})
                    suggested_price = filtering_data(suggested_price)
                    name = item.find("div", {"class": item_quality}).text.strip()
                    whole_string = "{:>40} {:>30}\n".format(name, suggested_price)
                    with open(db_filename, 'a') as db_file:
                        db_file.write(whole_string)
        print("Page {}/{} complete!".format(i + 1, page_count))


def get_suggested_items_from_db(filename):
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


def recent_items_calc(recent_items_url, suggested_items_dict, matches_db_filename, page_count, coef):

    with open(matches_db_filename, "w") as matches_db:
        matches_db.write("{:>50} {:>25} {:>30} {:>30} {:>33}\n".format(
            "Item name", "Current Price", "Suggested Price", "Location", "User"))
    # Check page url format
    if "&page=" in recent_items_url:
        page_num_length = len(recent_items_url.split("&page=")[1])
        recent_items_url = recent_items_url[:-page_num_length] + "1"
    else:
        recent_items_url = recent_items_url + "&page=1"

    for i in range(1, page_count + 1):
        recent_items_url = recent_items_url.replace("&page=" + str(i), "&page=" + str(i + 1))
        page = requests.get(recent_items_url)
        soup = BeautifulSoup(page.text, 'html.parser')

        # Get names of items
        item_names = alternate_get_item_names(soup, recent_items_url)

        # Get trader and location info
        # This fields have the same class of element, we need to get them all and then sort it like list of tuples
        trader_or_location_list_unsorted = []
        trader_location_list_sorted = []
        traders_and_locations = soup.findAll("td", {"class": "hidden-xs"})
        for trader_or_location in traders_and_locations:
            trader_or_location = filtering_data(trader_or_location, num_type=None, digit=False)
            if trader_or_location != '':
                trader_or_location_list_unsorted.append(trader_or_location)

        for ind in range(0, len(trader_or_location_list_unsorted) - 1, 2):
            trader_location_list_sorted.append((trader_or_location_list_unsorted[ind + 1],
                                                trader_or_location_list_unsorted[ind]))

        flag = False
        # Get prices and create new db file with matches
        all_prices = soup.findAll("td", {"class": "gold-amount bold"})
        for price, item_name in zip(all_prices, item_names):
            if suggested_items_dict.get(item_name):
                price = filtering_data(price, num_type=None, digit=False)
                price = price.split('X')[0]
                if suggested_items_dict.get(item_name) > int(price) * coef:
                    index = item_names.index(item_name)
                    trader_name = trader_location_list_sorted[index][0]
                    trader_location = trader_location_list_sorted[index][1]
                    with open(matches_db_filename, "a") as matches_db:
                        matches_db.write(
                            "{:>50} {:>20} {:>30} {:>50} {:>20}\n".format(
                                item_name, price, suggested_items_dict.get(item_name), trader_name, trader_location))
                    flag = True

        print("Page {}/{} is done!".format(str(i), str(page_count)))
        if flag:
            print("We found something! Check db")
        else:
            print("Empty...")
        # time.sleep(5)
    print("Search done, check {} file".format(matches_db_filename))


def main():
    coefficient = 1.5
    page_count = 50
    items_with_suggested_prices_url_fine = "https://eu.tamrieltradecentre.com/pc/Trade/SearchResult?ItemID" \
                                           "=&SearchType=PriceCheck&ItemNamePattern=&ItemCategory1ID=3" \
                                           "&ItemCategory2ID=11&ItemCategory3ID=37&ItemTraitID=&ItemQualityID" \
                                           "=&IsChampionPoint=false&LevelMin=&LevelMax=&MasterWritVoucherMin" \
                                           "=&MasterWritVoucherMax= "
    items_with_suggested_prices_url_epic = \
        'https://eu.tamrieltradecentre.com/pc/Trade/SearchResult?ItemID=&SearchType=PriceCheck' \
        '&ItemNamePattern=&ItemCategory1ID=3&ItemCategory2ID=17&ItemTraitID=&ItemQualityID=3' \
        '&IsChampionPoint=false&LevelMin=&LevelMax=&MasterWritVoucherMin=&MasterWritVoucherMax=&page=1'
    suggested_items_db_filename = "db"
    # Check quality of

    print("Collect suggested items or recent? (1/2)")
    answer = input()
    if answer == "1":
        items_url = input("Paste url with suggested items: ")
        page_ans = input("Calc all pages or insert num of pages(Y/Number): ")
        if page_ans == "Y":
            page_count = calc_maximum_pages(items_url)
            get_items_with_suggested_price(items_url, page_count=int(page_count))
        else:
            get_items_with_suggested_price(items_url, page_count=int(page_ans))
    elif answer == "2":
        filename = input("Insert filename of db with suggested items:")
        suggested_items_dict = get_suggested_items_from_db(filename)
        recent_items_url = input("Paste link with items:")
        print("Searching with coefficient: {}, total pages: {}\n".format(coefficient, page_count))
        recent_items_calc(recent_items_url=recent_items_url, suggested_items_dict=suggested_items_dict,
                          matches_db_filename="matches_db.txt", coef=coefficient, page_count=page_count)
    else:
        print("Wrong answer, try again...")
        return 0


if __name__ == '__main__':
    main()
