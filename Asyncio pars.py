from bs4 import BeautifulSoup
import re
import pandas as pd
import openpyxl
import asyncio
import aiohttp
import sys


class AntaParser:
    def __init__(self):
        self.headers = {
            'Connection': 'close', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, '
                                                 'like Gecko) Chrome/86.0.4240.111 Safari/537.36'
        }

        self.anta_pages = [
            "https://anta-sport.ru/new",
            "https://anta-sport.ru/cat/muzhskaya-odezhda",
            "https://anta-sport.ru/cat/zhenskoe",
            "https://anta-sport.ru/cat/aksessuary",
            "https://anta-sport.ru/cat/deti",
            "https://anta-sport.ru/discount"
        ]

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
                        pass
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
        values = []

        for key, value in self.art_dict.items():
            keys.append(key)
            values.append(value)

        df = pd.DataFrame({
            "art.n": keys,
            "visible": values
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
                    title = soup.find_all("a", {"class": "js-product-link"})
                    if title:
                        for card in title:
                            href = "https://anta-sport.ru" + card["href"]
                            self.anta_hrefs.append(href)
                    else:
                        is_pars = False
            await session.close()
            strr += 1

    async def anta_card(self, href):
        for hrf in href:
            await asyncio.sleep(1)
            async with aiohttp.ClientSession() as session:
                async with session.get(url=hrf, headers=self.headers, timeout=20) as resp:
                    responce = await resp.text()
                    soup = BeautifulSoup(responce, "html.parser")
                    descriptions = soup.find("div", class_="product-description-section")
                    txt = descriptions.text
                    art = re.search('Артикул: (.+?)\n', txt)

                    button = soup.find(class_="btn btn-default buy-btn j-add-product")
                    if button:
                        if art:
                            article = art.group(1)
                            status = button.text
                        else:
                            article = href
                            status = button.text
                        self.art_dict[article] = status
                    else:
                        article = art.group(1)
                        self.art_dict[article] = "Недоступно к заказу"
                    sys.stdout.write("\rСбор данных со страницы:" + f" Обработано {self.bash} из {self.len_bash}")
                    sys.stdout.flush()
                    self.bash += 1
            await session.close()

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
