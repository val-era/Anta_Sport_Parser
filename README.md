Данный скрипт - асинхронный парсинг сайта Anta-sport.ru


- Т.К. сайт и его блоки могут меняться и перстраиваться, надо проверять блоки для BS4.
- Обратите внимание, на некоторые блоки в данном коде:

17 строка (Список ссылок для парсинга и сбора информации, можно менять по своему усмотрению):
~~~
self.anta_pages = [
            "https://anta-sport.ru/new",
            "https://anta-sport.ru/cat/muzhskaya-odezhda",
            "https://anta-sport.ru/cat/zhenskoe",
            "https://anta-sport.ru/cat/aksessuary",
            "https://anta-sport.ru/cat/deti",
            "https://anta-sport.ru/discount"
        ]
~~~

84 строка (Сбор карточек с каждой страницы ):
Скрипт ищет каждую карточку и получает аргумент href. Если скрипт не работает, проверьте данный блок

~~~
soup = BeautifulSoup(responce, "html.parser")
                    title = soup.find_all("a", {"class": "js-product-link"})
                    if title:
                        for card in title:
                            href = "https://anta-sport.ru" + card["href"]
                            self.anta_hrefs.append(href)
~~~

![image](https://github.com/val-era/Anta_Sport_Parser/assets/115217591/307e43e5-dabb-4ff2-a11b-7db255a439bc)

101 строка (Сбор артикула с каждой карточки, проверка карточек на доступность к заказу):
Скрипт переходит по каждой карточке по скрипту выше, вытаскивает артикул и проверяет доступность к заказу

~~~
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
~~~

![image](https://github.com/val-era/Anta_Sport_Parser/assets/115217591/ebc25951-db4c-41fb-86da-1a56bec0e096)

@VAL_ERA
