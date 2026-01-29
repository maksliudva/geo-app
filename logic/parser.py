# waw4free.pl
# polecane wydarzenia sekcja
# https://waw4free.pl/

from bs4 import BeautifulSoup, SoupStrainer
import requests as r
from dataclasses import dataclass
from typing import List
from functools import lru_cache

@dataclass
class EventBox:
    title: str
    image:str #img - string? actual image?
    district: str
    address: str
    plink: str # url
    box_category : List = None # voidable
    start_date: str = None
    end_date: str = None
    date: str = None # or date?
    time: str = None # or date time? hour?

@dataclass
class OtherBox:
    title: str
    image:str # url
    info: str
    plink: str # url


# https://waw4free.pl/warszawa-wydarzenia-2026-1-29
# "https://waw4free.pl/"
URL = "https://waw4free.pl/"
recommended_html = r.get(URL)
DISTRICTS = ["Mokotów","Praga-Południe","Białołęka","Wola","Ursynów","Bielany","Bielany","Praga-Południe","Śródmieście","Wawer","Ochota","Ursus","Praga-Północ","Wesoła","Żoliborz","Wilanów","Włochy", "Rembertów"]
# with open("") as fp:
#     soup = BeautifulSoup(fp, 'html.parser')

# i need to create a structure
# i should make a dictionary of boxes


# function that loads boxes:
#   get soup
#   returns boxes list of EventBoxes filled

# if box = box info-box then  stop

# function that checks if the box is valid
# jesli string z informacja nie jest jak trzeba zapisze sie w atrybut info

#function that gives address (goes to link and finds on page)

def rm_matched_in_list(text, code_list):
    text = text.replace(',','')
    address_list = text.split(" ")
    for word in address_list:
        if word in code_list:
            # print("FOUND: ", word)
            text = text.replace(word,'')
            break
    return text

def get_address(url):
    """
    req:
        - url, string
    returns:
        - addres - str
    """
    phtml =  r.get(url)
    soup = BeautifulSoup(phtml.text,'html.parser')
    address = soup.find(attrs={"itemprop":'location'}).text.strip("Warszawa")
    address = rm_matched_in_list(address, DISTRICTS)
    # print("GET_ADDRESS FUNCTION: ")
    # print(address)
    if not (address is None):
        return address
    else:
        return "Brak adresu."


def print_box(box):
    str = "nazwa: ",box.title,"\ndzień: ",box.date,"\ngodzina: ", box.time, "\ndzielnica: ",box.district, "\naddress: ", box.address,"\nkategorie", box.box_category, "\nlink:", box.plink,"\n\n"
    if (box.date1 is not None or box.date2 is not None):
        str = str + "date1:", box.date1,  "date2:", box.date2
    print(str)

def open_calendar_page(day,month,year):
    # defensive checks
    url = URL+"/warszawa-wydarzenia-" + str(year) + "-" + str(month) + "-" + str(day)
    page = r.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    if not (soup.find(string="W tym dniu nie ma jeszcze żadnych wydarzeń.") is None):
        # nie ma wydarzeń
        print("Nie ma wydarzeń.")

    if not (soup.find(string="Strona, której szukasz nie istnieje.") is None):
        print("Strona nie istnieje.")

    loadBoxes(soup,boxes)
    # if (soup.find("span").text == "Nie ma takiej strony! :-("):
    #     print("NIE MA TAKIEJ STRONY")
    # print(alert.text)

def check_interval(str):
    # to divide on pieces
    # to find a index of "-"
    # 1 date is index -1
    # 2 date is index+ 1
    date1 = None
    date2 = None
    list = str.split()
    try:
        separator = list.index("-")
    except ValueError as valueerr:
        separator = -1
    if (separator != -1):
        date1 = list[separator - 1].strip(", ")
        date2 = list[separator + 1].strip(",. ")
    return date1, date2

def parse_data(str):
    # to find district
    # to find if there is interval
    # to find date
    # to find time
    str = str.strip('\n')
    found_items = list(filter(lambda d: d in str, DISTRICTS))
    if (len(found_items) != 0 ):
        district = found_items[0]
    else:
        district = None
    # print(district)
    
    start_date, end_date = check_interval(str)
    print("start_date=",start_date, "end_date=",end_date, "district=",district)
    return start_date, end_date, district
    

def loadBoxes(soup, boxes):
    """
    req:
        -  bs4.Tag object(soup)
        -  empty list of boxes to be filled
    returns:
        -  boxes list loaded with parsed information about events
    """
    found_boxes = soup.find_all('div', class_="box")
    i = 0
    for box in found_boxes:
        try:

            a = box.find("a")
            a_attrs = a.attrs
            event_title = a_attrs['title']
            link = URL + a_attrs['href']    
            image = URL + box.find('div', class_='box-image').attrs['style'].lstrip('background-image: url(\'').rstrip('\');')
            date_line = box.find('div', class_='box-data').text 
            # print(date_line)
            start_date, end_date,district = parse_data(date_line)
            #from bottom
            box_category = box.find('div', class_='box-category').text.replace("\n\t,"," ").split()
            address = get_address(link)
            if (district is not None):

                if (start_date is None and end_date is None):
                    print("Inside the 1 date-box:\n ")
                    date,time,district = date_line.strip('\n-').split(" ",-1)

                    time = time.strip(',\t\n')
                    date = date.strip(',\t\n')
                    event = EventBox(title=event_title,image=image,date=date,time=time,district=district,address=address,box_category=box_category,plink=link,start_date=start_date,end_date=end_date)
                    print_box(event)
                else:
                    print("This branch has 2 data-box:\n")
                    event = EventBox(title=event_title,image=image,date=None,time=None,district=district,address=address,box_category=box_category,plink=link,start_date=start_date,end_date=end_date)
                    # print("nazwa: ",event_title,"\ndzień: ",date,"\ngodzina: ", time, "\ndzielnica: ",district, "\nkategorie", box_category, "\nlink:", link,"\n\n")
                    print_box(event)
                boxes.append(event)
            else:

                info = date_line.strip('\n\t,').split(" ",-1)
                print("INFO: ", info)
                otherevent = OtherBox(event_title,image,info,link)
                boxes.append(otherevent)

        except Exception as e:
            print(e)
        finally:
            i = i + 1
    print("loadBoxes() has returned:",len(boxes)," eventboxes.")
    return boxes


soup = BeautifulSoup(recommended_html.text, 'html.parser')

#cashing
boxes = []

# loadBoxes(soup, boxes)
# print("END OF FUNCTION")
# print(boxes)


# get_address("https://waw4free.pl/wydarzenie-147368-final-wosp-w-sgh-spotkanie-z-alpakami")

# open_calendar_page(27, 1,2026)
# parse_data("asdaslfjasjf, Ursynów     , opa")
# check_interval("12.03.2056 - 12.05.2057, sdfdsjl wqljelj -----")


url = URL+"/warszawa-wydarzenia-" + "2026" + "-" + "1" + "-" + "1"
page = r.get(url)
soup = BeautifulSoup(page.text, 'html.parser')
pretty_soup = soup.prettify()
print(pretty_soup)
