import requests


from bs4 import BeautifulSoup

import webbrowser

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


def check_for_captcha(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    captcha = soup.find("div", {"class": "g-recaptcha"})
    if captcha:
        print("We catch captcha, go here if browser didn't open: {}".format(url))
        webbrowser.open(url, new=2)
        input("Press ENTER:")


def calc_maximum_pages(items_url):
    # Set very big num to page to get real last page
    if "&page=" in items_url:
        page_num_length = len(items_url.split("&page=")[1])
        num = "100000"
        items_url = items_url[:-page_num_length] + num
    else:
        items_url = items_url + "&page=100000000"

    check_for_captcha(items_url)
    page = requests.get(items_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    num_page = soup.find("li", {"class": "active"})

    return num_page.text


def filtering_data(value, num_type=None, digit=True):
    if not isinstance(value, str):
        value = value.text
    value = value.replace("\n", "")
    value = value.replace("\r", "")
    value = value.replace(" ", "")
    value = value.replace(",", "")
    if digit:
        if "." in value:
            value = value.split(".")[0]
        value = int(value)
    return value


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

        # Check for captcha
        check_for_captcha(base_items_url)
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


def gather_recent_items(recent_items_url, page_count, coef, suggested_items_db):

    # Check page url format
    if "&page=" in recent_items_url:
        page_num_length = len(recent_items_url.split("&page=")[1])
        recent_items_url = recent_items_url[:-page_num_length] + "1"
    else:
        recent_items_url = recent_items_url + "&page=1"

    # Set items quality and matches filename
    item_quality = ''
    matches_db_filename = "matches.txt"
    for key, value in QUALITIES.items():
        if value in recent_items_url:
            matches_db_filename = "matches_" + key + '.txt'
            item_quality = DIV_QUALITIES[key]
            break

    # Write titles to the file
    with open(matches_db_filename, "w") as matches_db:
        matches_db.write("{:>50} {:>25} {:>30} {:>30} {:>33}\n".format(
            "Item name", "Current Price", "Suggested Price", "Location", "User"))

    # Gather all information
    for i in range(1, page_count + 1):
        recent_items_url = recent_items_url.replace("&page=" + str(i), "&page=" + str(i + 1))
        check_for_captcha(recent_items_url)
        page = requests.get(recent_items_url)
        soup = BeautifulSoup(page.text, 'html.parser')
        all_items = soup.findAll("tr", {"class": "cursor-pointer"})

        for item in all_items:
            name = item.find("div", {"class": item_quality}).text.strip()
            if name in suggested_items_db.keys():
                price = filtering_data(item.find("td", {"class": "gold-amount bold"}).text.split("X")[0], digit=True)
                if suggested_items_db.get(name) > float(price) * coef:

                    # If we found something, then we can take location and trader info
                    trader_and_locations = item.findAll("td", {"class": "hidden-xs"})
                    location = ""
                    trader_name = ""

                    for index in range(1, len(trader_and_locations) - 1):
                        location += filtering_data(trader_and_locations[index].text.strip(), digit=False)
                    trader_name = item.find("div", {"class": "text-small-width"}).text.strip()

                    with open(matches_db_filename, "a") as matches_db:
                        matches_db.write(
                            "{:>50} {:>20} {:>30} {:>50} {:>20}\n".format(
                                name, price, suggested_items_db.get(name), location, trader_name))
                    print("Found something! Check {} file".format(matches_db_filename))
        print("Page {}/{} done!".format(i, page_count))


def main():
    answer = input("Collect suggested items or recent? (1/2): ")
    if answer == "1":
        items_url = input("Paste url with suggested items: ")
        page_ans = input("Calc all pages or insert num of pages(Y/Number): ")
        if page_ans == "Y":
            page_count = calc_maximum_pages(items_url)
            get_items_with_suggested_price(items_url, page_count=int(page_count))
        else:
            get_items_with_suggested_price(items_url, page_count=int(page_ans))
    elif answer == "2":
        # TODO: Make check of this file
        db_filename = input("Insert filename of db with suggested items: ")
        # Get suggested items from db
        suggested_items_db = get_suggested_items_from_db(db_filename)
        recent_items_url = input("Paste link with items (Make sure you choose Item Quality): ")
        coef = float(input("Write coef of benefit (example 1.5): "))
        max_pages = calc_maximum_pages(recent_items_url)
        page_count = int(input("Write count of pages for scan (for this link max is {}): ".format(max_pages)))
        gather_recent_items(recent_items_url, page_count, coef, suggested_items_db)
    else:
        print("Wrong answer, try again...")
        return 0


if __name__ == '__main__':
    main()
