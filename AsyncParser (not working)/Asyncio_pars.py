from bs4 import BeautifulSoup
import re
import pandas as pd
import openpyxl
import asyncio
import aiohttp
import sys
import cloudscraper


class AntaParser:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299'}


        self.anta_pages = [
            "https://anta-sport.ru/new",
            "https://anta-sport.ru/cat/muzhskaya-odezhda",
            "https://anta-sport.ru/cat/zhenskoe",
            "https://anta-sport.ru/cat/aksessuary",
            "https://anta-sport.ru/cat/deti",
            "https://anta-sport.ru/discount"
        ]

        self.scraper = cloudscraper.create_scraper()

        self.anta_pages_new = []

        self.bash = 1
        self.len_bash = 0

        self.anta_hrefs = []

        self.art_dict = {}

    async def start(self):
        is_correct = "N"
        sys.stdout.write(f"\nПроверьте актуальность ссылок:\n{self.anta_pages}\n\n[-] Если ссылки корректны, введите Y;\n[-] Если некорректны, вводите ссылки на основные категории по примеру [https://anta-sport.ru/cat/muzhskaya-odezhda] в строку ниже по одной,затем нажимайте Enter;\n[+] Как ссылки закончатся введите в консоль Y+Enter;\n[!]Если вам нужна информация разработчика, введите val")
        sys.stdout.flush()
        while is_correct != "Y":
            is_correct = input("\n[!]Введите ссылку, если ссылки внесены то Y: ")
            if is_correct != "Y":
                if is_correct.startswith("https://anta-sport.ru/"):
                    self.anta_pages_new.append(is_correct)
                else:
                    if is_correct == "val":
                        sys.stdout.write("\n https://github.com/val-era/Anta_Sport_Parser (Check README.md")
                        sys.stdout.flush()
                    else:
                        sys.stdout.write("[-] Проверьте ссылку на корректность. Формат ссылки [https://anta-sport.ru/new]")
                        sys.stdout.flush()
            else:
                pass
        if self.anta_pages_new:
            self.anta_pages = self.anta_pages_new
            await asyncio.gather(self.parsing_anta())
        else:
            await asyncio.gather(self.parsing_anta())

        sys.stdout.write("\nНачинаем запись в файл")
        sys.stdout.flush()


        keys = []
        description = []
        discount = []
        visible = []

        for key, value in self.art_dict.items():
            keys.append(key)
            description.append(value[0])
            discount.append(value[1])
            visible.append(value[2])

        df = pd.DataFrame({
            "art.n": keys,
            "visible": visible,
            "discount": discount,
            "description": description
        })
        df.to_excel(r"AS art's.xlsx")

    async def connect_anta(self, page):
        is_pars = True
        strr = 1
        while is_pars:
            await asyncio.sleep(1)
            async with aiohttp.ClientSession() as session:
                async with session.get(url=f'{page}/?page={strr}', headers=self.headers, timeout=20) as resp:
                    responce = await resp.text()
                    soup = BeautifulSoup(responce, "html.parser")
                    print(soup.text)
                    title = soup.find_all("a", {"class": "fast-view-btn"})
                    if title:
                        for card in title:
                            href = "https://anta-sport.ru" + card["href"]
                            self.anta_hrefs.append(href)
                    else:
                        is_pars = False
            strr += 1
        await session.close()

    async def anta_card(self, href):
        for hrf in href:
            try:
                await asyncio.sleep(1)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=hrf, headers=self.headers, timeout=40) as resp:
                        responce = await resp.text()
                await session.close()
                soup = BeautifulSoup(responce, "html.parser")
                descriptions = soup.find("div", class_="product-description-section")
                txt = descriptions.text
                art = re.search('Артикул: (.+?)\n', txt)

                df_information = []

                text = txt.replace("\n", " ").replace("\t", " ").split(" ")
                description = []

                is_art = False
                is_sost = False
                for i in text:
                    if is_art == False:
                        if i.startswith(art.group(1)):
                            is_art = True
                    else:
                        if i == "":
                            pass
                        elif i.startswith("СОСТАВ") or i.startswith("Состав") or i.startswith("состав"):
                            is_sost = True
                        else:
                            if is_sost == False:
                                description.append(i)

                if len(description) > 4:
                    df_information.append("Описание найдено")
                else:
                    df_information.append("Описание отсутствует")

                discount = soup.find("span", class_="sale-badge")
                if discount:
                    df_information.append(discount.text)
                else:
                    df_information.append("0%")

                button = soup.find(class_="btn btn-default buy-btn j-add-product")
                if button:
                    if art:
                        article = art.group(1)
                        status = button.text
                    else:
                        article = href
                        status = button.text
                    df_information.append(status)
                    self.art_dict[article] = df_information
                else:
                    article = art.group(1)
                    df_information.append("Недоступно к заказу")
                    self.art_dict[article] = df_information
                sys.stdout.write("\rСбор данных со страницы:" + f" Обработано {self.bash} из {self.len_bash}")
                sys.stdout.flush()
                self.bash += 1
            except Exception as e:
                print(f"Для {hrf} произошла ошибка {e} обратитесь к разработчику")

    async def parsing_anta(self):
        tasks = []
        sys.stdout.write(f"\rЗапускаю обработку страниц \n{self.anta_pages} \nОжидайте")
        sys.stdout.flush()
        for page in self.anta_pages:
            task = asyncio.create_task(self.connect_anta(page))
            tasks.append(task)
        await asyncio.gather(*tasks)
        anta_sport = list(set(self.anta_hrefs))
        self.len_bash = len(anta_sport)
        sys.stdout.write(f"\r\nКарточек на сайте {str(self.len_bash)}. Начинаем обработку")
        sys.stdout.flush()

        len_arr = self.len_bash + 1
        start_range = 0
        hrefs_arr = []

        while start_range < len_arr:
            href_arr = anta_sport[start_range:start_range+200]
            hrefs_arr.append(href_arr)
            start_range += 200

        for page in hrefs_arr:
            task = asyncio.create_task(self.anta_card(page))
            tasks.append(task)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = AntaParser()
    asyncio.run(start.start())
