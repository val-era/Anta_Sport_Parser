import sys
import time
import os
from bs4 import BeautifulSoup
import re
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from io import BytesIO
import pandas as pd
import cloudscraper
import requests
import base64
from PIL import Image as PILImage


class AntaHrefs:
    def __init__(self):
        self.href_list = []

        self.scraper = cloudscraper.create_scraper(browser={
            'custom': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299',
        }, )

        self.time_sleep = 1

        self.pages = [
            'https://anta-sport.ru/cat/outlet',
            'https://anta-sport.ru/cat/new',
            'https://anta-sport.ru/cat/muzhskaya-odezhda',
            'https://anta-sport.ru/cat/zhenskoe',
            'https://anta-sport.ru/cat/aksessuary',
            'https://anta-sport.ru/cat/deti'
        ]

        self.article_name = []
        self.img_urls = []
        self.model_name = []
        self.rrp = []
        self.descriptions = []
        self.description_info = []
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
                sys.stdout.write(f"Done - {page} with {strr - 2} pages \n")
                sys.stdout.flush()
            self.get_card_info()
        except:
            pass

    def get_hrefs(self, page):
        try:
            soup = BeautifulSoup(page.text, "html.parser")
            product_cards = soup.find_all("a", class_="fast-view-btn js-product-link")
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

    def get_card_info(self, href=None):
        if href != None:
            self.href_list = [href]
        lenght = len(self.href_list)
        number_href = 0

        for href in self.href_list:
            number_href += 1
            errors = 0
            while errors != 3:
                try:
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
            "img": self.img_urls,
            "model": self.model_name,
            "RRP": self.rrp,
            "discount": self.discount,
            "description": self.description_info,
            "description_var": self.descriptions,
            "visibles": self.visible,
        })
        df.to_excel('art1.xlsx', index=False)
        df.to_excel('w_ophart1.xlsx', index=False)

        # Добавляем изображения со сжатием
        self.add_images_direct()
        print("✅ Изображения добавлены в файл")

        df_err = pd.DataFrame({
            "ERROR": self.errors,
        })
        df_err.to_excel('Error.xlsx')

    def compress_image(self, image_data, quality=60):
        """
        Сжимает изображение на заданный процент

        Args:
            image_data: байты изображения
            quality: качество сжатия (1-100, меньше = сильнее сжатие)
                   60 = сжатие на ~40%
        """
        try:
            # Открываем изображение с помощью PIL
            img = PILImage.open(BytesIO(image_data))

            # Конвертируем в RGB если необходимо
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = PILImage.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            # Сжимаем и сохраняем в BytesIO
            output_buffer = BytesIO()
            img.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            compressed_data = output_buffer.getvalue()

            # Вычисляем процент сжатия
            original_size = len(image_data)
            compressed_size = len(compressed_data)
            compression_percent = (1 - compressed_size / original_size) * 100

            print(
                f"      Сжатие: {original_size / 1024:.1f}KB -> {compressed_size / 1024:.1f}KB ({compression_percent:.1f}%)")

            return compressed_data

        except Exception as e:
            print(f"      Ошибка сжатия: {e}, использую оригинал")
            return image_data

    def add_images_direct(self, excel_filename='art1.xlsx'):
        """
        Добавляет изображения в Excel файл по URL со сжатием
        """

        # Загружаем Excel файл для вставки изображений
        wb = load_workbook(excel_filename)
        ws = wb.active

        # Настраиваем колонку для изображений
        ws.column_dimensions['B'].width = 20

        successful = 0
        failed = 0
        compressed = 0
        total = len(self.img_urls)

        # Проходим по всем URL изображений
        for idx, img_url in enumerate(self.img_urls):
            row_num = idx + 2

            if img_url and isinstance(img_url, str) and img_url.startswith('http'):
                try:
                    # Скачиваем изображение
                    response = self.scraper.get(img_url, timeout=30)

                    if response.status_code == 200:
                        # Сжимаем изображение (quality=60 = сжатие на ~40%)
                        compressed_data = self.compress_image(response.content, quality=60)

                        # Создаем изображение из сжатых данных
                        image_buffer = BytesIO(compressed_data)
                        img = Image(image_buffer)

                        # Устанавливаем размер
                        img.width = 100
                        img.height = 100

                        # Привязываем к ячейке
                        img.anchor = f'B{row_num}'

                        # Добавляем изображение
                        ws.add_image(img)

                        # Очищаем ячейку от URL
                        ws.cell(row=row_num, column=2, value="")

                        # Устанавливаем высоту строки
                        ws.row_dimensions[row_num].height = 80

                        successful += 1
                        if len(compressed_data) < len(response.content):
                            compressed += 1
                        print(f"  ✓ Строка {row_num}: изображение добавлено")
                    else:
                        print(f"  ✗ Строка {row_num}: статус {response.status_code}")
                        ws.cell(row=row_num, column=2, value=f"[HTTP {response.status_code}]")
                        failed += 1

                except Exception as e:
                    print(f"  ✗ Строка {row_num}: ошибка - {str(e)[:50]}")
                    ws.cell(row=row_num, column=2, value="[Ошибка загрузки]")
                    failed += 1

                # Небольшая задержка между запросами
                time.sleep(0.5)
            else:
                ws.cell(row=row_num, column=2, value="[Нет URL]")
                failed += 1

        # Сохраняем изменения
        wb.save(excel_filename)

        print(f"\n{'=' * 50}")
        print(f"📊 Статистика добавления изображений:")
        print(f"   - Всего товаров: {total}")
        print(f"   - Успешно: {successful}")
        print(f"   - Сжато: {compressed}")
        print(f"   - Ошибок: {failed}")
        print(f"{'=' * 50}")

    def get_card_information(self, connect, href):
        self.art_name_var = None
        self.description_info_var = None
        self.descr_var = None
        self.rrp_var = None
        self.disc_var = None
        self.visible_var = None
        self.img_url_var = None
        self.model_name_var = None

        soup = BeautifulSoup(connect.text, "html.parser")

        try:
            """Вычисляем артикул с товара"""
            new_art = soup.find("div", class_="product-code")
            txt = new_art.text
            art = txt.replace("Артикул: ", "")
            print(art)
            if art:
                self.art_name_var = art
            else:
                self.art_name_var = href

            """Описания"""
            try:
                descriptions = soup.find("div", class_="tabs-show-more-wrapper")
                txt = descriptions.text
                text = txt.replace("\n", "").replace("\t", "")
                self.description_info_var = text
                description = text.split(" ")
                if len(description) > 5:
                    self.descr_var = "Описание найдено"
                else:
                    self.descr_var = "Описание отсутствует"
            except:
                self.description_info_var = ""
                self.descr_var = "Описание отсутствует"

            """Скидка"""
            discount = soup.find("span", class_="sale-badge js-sale-badge")
            if discount:
                self.disc_var = discount.text
            else:
                self.disc_var = "0%"

            """Доступность карточки"""
            button = soup.find("a", class_="btn btn-default buy-btn j-add-product js-add-product")
            if button:
                self.visible_var = button.text
            else:
                self.visible_var = "Недоступно для заказа"

            """Получаем РРЦ"""
            if self.disc_var == "0%":
                rrp_label = soup.find("span", class_="current_price js-current_price")
            else:
                rrp_label = soup.find("span", class_="old-price js-old-price")
            rrp = rrp_label.text.replace(" ₽", "")
            self.rrp_var = rrp

            """Получаем наименование модели"""
            name_label = soup.find("h1", itemprop="name")
            self.model_name_var = name_label.text

            """Получаем изображение"""
            img_src = soup.find("div", class_="product-preview-tiles").find("a", class_="item").find("img")['src']
            self.img_url_var = img_src

        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
            self.art_name_var = href
            self.img_url_var = None

        # Добавляем все значения в списки
        self.article_name.append(self.art_name_var)
        self.img_urls.append(self.img_url_var)
        self.model_name.append(self.model_name_var)
        self.rrp.append(self.rrp_var)
        self.discount.append(self.disc_var)
        self.description_info.append(self.description_info_var)
        self.descriptions.append(self.descr_var)
        self.visible.append(self.visible_var)


if __name__ == "__main__":
    start = AntaHrefs()
    start.connection()