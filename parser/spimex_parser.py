import asyncio
import aiohttp
import aiofiles
import ssl
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import logging

from db.config import settings

log = logging.getLogger(__name__)

os.makedirs(settings.cf.download_dir, exist_ok=True)


ssl_context = ssl.create_default_context()
semaphore = asyncio.Semaphore(settings.cf.concurrent_downloads)


async def fetch_bulletins(session, page: int):
    url = f"{settings.cf.base_url}?page=page-{page}&bxajaxid=d609bce6ada86eff0b6f7e49e6bae904"
    try:
        async with session.get(url, ssl=ssl_context, timeout=10) as response:
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            bulletins = []

            items = soup.select(".accordeon-inner__item")
            for item in items:
                link = item.select_one("a.accordeon-inner__item-title.link.xls")
                date_element = item.select_one(
                    ".accordeon-inner__item-inner__title span"
                )

                if link and date_element:
                    url_file = urljoin(settings.cf.base_url, link["href"])
                    trade_date = datetime.strptime(
                        date_element.text.strip(), "%d.%m.%Y"
                    ).strftime("%Y-%m-%d")

                    if (
                        datetime.strptime(trade_date, "%Y-%m-%d")
                        < settings.cf.target_date
                    ):
                        log.info(
                            f"Достигнута целевая дата {settings.cf.target_date.date()}, стоп."
                        )
                        return bulletins, True

                    filename = f"{trade_date}.xls"
                    bulletins.append(
                        {"url": url_file, "filename": filename, "date": trade_date}
                    )
            return bulletins, False

    except Exception as e:
        log.error(f"Ошибка при получении страницы {page}: {e}")
        return [], False


async def download_file(session, url, filename):
    filepath = os.path.join(settings.cf.download_dir, filename)

    for attempt in range(1, settings.cf.max_retries + 1):
        async with semaphore:
            try:
                async with session.get(url, ssl=ssl_context, timeout=20) as response:
                    response.raise_for_status()

                    async with aiofiles.open(filepath, "wb") as f:
                        while True:
                            chunk = await response.content.read(65536)  # 64 KB
                            if not chunk:
                                break
                            await f.write(chunk)

                log.info(f"Загрузка завершена: {filepath}")
                return

            except aiohttp.ClientResponseError as e:
                log.error(
                    f"HTTP ошибка {e.status} при загрузке {filename}: {e.message} | Попытка {attempt}"
                )
            except aiohttp.ClientConnectorError as e:
                log.error(
                    f"Ошибка соединения при загрузке {filename}: {e} | Попытка {attempt}"
                )
            except Exception as e:
                log.error(
                    f"Неизвестная ошибка при загрузке {filename}: {e} | URL: {url} | Попытка {attempt}"
                )

        await asyncio.sleep(0.5)


async def main():
    all_bulletins = []
    stop = False
    page = 1
    log.info("Загрузка файлов с сайта СПбМТСБ...")
    async with aiohttp.ClientSession() as session:
        while not stop:
            log.info(f"Обработка страницы {page}")
            bulletins, stop = await fetch_bulletins(session, page)
            all_bulletins.extend(bulletins)
            page += 1

        log.info(f"Найдено бюллетеней: {len(all_bulletins)}")

        tasks = [
            download_file(session, bulletin["url"], bulletin["filename"])
            for bulletin in all_bulletins
        ]
        await asyncio.gather(*tasks)
        log.info("Загрузка завершена")
