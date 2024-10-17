import sys
import time

from bs4 import BeautifulSoup
import re
import pandas as pd
import cloudscraper


class AntaHrefs:
    def __init__(self):
        self.href_list = []

        self.time_sleep = 1

        self.pages = [
            "https://anta-sport.ru/new",
            "https://anta-sport.ru/cat/muzhskaya-odezhda",
            "https://anta-sport.ru/cat/zhenskoe",
            "https://anta-sport.ru/cat/aksessuary",
            "https://anta-sport.ru/cat/deti",
            "https://anta-sport.ru/discount"
        ]

        self.article_name = []
        self.descriptions = []
        self.discount = []
        self.visible = []
        self.errors = []

    def connection(self):
        try:
            for page in self.pages:
                self.scraper = cloudscraper.create_scraper()
                is_pars = True
                strr = 1
                while is_pars:
                    site_page = page + f"?page={strr}"
                    connect = self.scraper.get(site_page)
                    if connect.status_code == 200:
                        is_pars = self.get_hrefs(connect)
                    else:
                        pass
                    strr += 1
                sys.stdout.flush()
                sys.stdout.write(f"Done - {page} with {strr-2} pages \n")
                sys.stdout.flush()
            self.get_card_info()
        except:
            pass

    def get_hrefs(self, page):
        try:
            soup = BeautifulSoup(page.text, "html.parser")
            product_cards = soup.find_all("a", class_="js-product-link")
            if product_cards:
                for card in product_cards:
                    href = "https://anta-sport.ru" + card["href"]
                    if href not in self.href_list:
                        self.href_list.append(href)
                return True
            else:
                return False
        except:
            pass

    def get_card_info(self):
        lenght = len(self.href_list)
        number_href = 0

        for href in self.href_list:
            number_href += 1
            errors = 0
            while errors != 3:
                try:
                    self.scraper = cloudscraper.create_scraper(browser={
                                                                'custom': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299',
                                                            },)
                    time.sleep(self.time_sleep)
                    connect = self.scraper.get(href)
                    time.sleep(self.time_sleep)

                    self.get_card_information(connect, href)
                    errors = 3
                except Exception as e:
                    time.sleep(20)
                    self.time_sleep += 8
                    sys.stdout.flush()
                    sys.stdout.write(f"{e}\n.......{href}")
                    errors += 1

            self.time_sleep = 1

            sys.stdout.flush()
            sys.stdout.write(f"Обработано {number_href} из {lenght} .... {href}\n")
            sys.stdout.flush()

        df = pd.DataFrame({
            "art.n": self.article_name,
            "descriptions": self.descriptions,
            "discount": self.discount,
            "visibles": self.visible,
        })
        df.to_excel('art1.xlsx')

        df_err = pd.DataFrame({
            "ERROR": self.errors,
        })
        df_err.to_excel('Error.xlsx')

    def get_card_information(self, connect, href):
        self.art_name_var = "None"
        self.descr_var = "None"
        self.disc_var = "None"
        self.visible_var = "None"

        soup = BeautifulSoup(connect.text, "html.parser")

        """Вычисляем артикул с товара"""
        try:
            descriptions = soup.find("div", class_="product-description-section")
            txt = descriptions.text
            art = re.search('Артикул: (.+?)\n', txt)
            if art:
                self.art_name_var = art.group(1)
            else:
                self.art_name_var = href

            """Описания"""
            text = txt.replace("\n", "").replace("\t", "").split(" ")
            description = []
            is_art = False
            is_sost = False
            for i in text:
                if is_art == False:
                    if i.startswith(art.group(1)):
                        is_art = True
                else:
                    try:
                        if i == "":
                            pass
                        elif i.startswith("СОСТАВ") or i.startswith("Состав") or i.startswith("состав"):
                            is_sost = True
                        else:
                            if is_sost == False:
                                description.append(i)
                    except:
                        pass
            if len(description) > 4:
                self.descr_var = "Описание найдено"
            else:
                self.descr_var = "Описание отсутствует"

            """Скидка"""

            discount = soup.find("span", class_="sale-badge")
            if discount:
                self.disc_var = discount.text
            else:
                self.disc_var = "0%"

            """Доступность карточки"""

            button = soup.find(class_="btn btn-default buy-btn j-add-product")
            if button:
                self.visible_var = button.text
            else:
                self.visible_var = "Недоступно для заказа"
        except:
            self.art_name_var=href

        self.article_name.append(self.art_name_var)
        self.descriptions.append(self.descr_var)
        self.discount.append(self.disc_var)
        self.visible.append(self.visible_var)


if __name__ == "__main__":
    start = AntaHrefs()
    start.connection()
