import asyncio
import logging
import os
import pandas as pd

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.spimex import Spimex
from db.models.database import db_helper
from db.config import settings

log = logging.getLogger(__name__)


def safe_float_conversion(value):
    """Безопасное преобразование значения в float."""
    try:
        return float(Decimal(str(value)))
    except:
        return 0.0


def prepare_data(df):

    start_idx = df[
        df.iloc[:, 1].str.contains("Единица измерения: Метрическая тонна", na=False)
    ].index[0]
    data = df.iloc[start_idx + 2 :].copy()
    data.columns = df.iloc[start_idx + 1].values

    data["Объем\nДоговоров\nв единицах\nизмерения"] = data[
        "Объем\nДоговоров\nв единицах\nизмерения"
    ].apply(safe_float_conversion)
    data["Обьем\nДоговоров,\nруб."] = data["Обьем\nДоговоров,\nруб."].apply(
        safe_float_conversion
    )
    data["Количество\nДоговоров,\nшт."] = (
        data["Количество\nДоговоров,\nшт."]
        .replace("-", "0")
        .apply(safe_float_conversion)
    )

    return data[data["Количество\nДоговоров,\nшт."] > 0]


async def insert_to_db(
    session: AsyncSession, data: pd.DataFrame, file_date: datetime.date
):
    spimex_list = []

    for _, row in data.iterrows():
        if not isinstance(row["Код\nИнструмента"], str):
            continue
        try:
            spimex_list.append(
                Spimex(
                    exchange_product_id=str(row["Код\nИнструмента"]),
                    exchange_product_name=str(row["Наименование\nИнструмента"]),
                    oil_id=str(row["Код\nИнструмента"])[:4],
                    delivery_basis_id=str(row["Код\nИнструмента"])[4:7],
                    delivery_basis_name=str(row["Базис\nпоставки"]),
                    delivery_type_id=str(row["Код\nИнструмента"])[-1],
                    volume=safe_float_conversion(
                        row["Объем\nДоговоров\nв единицах\nизмерения"]
                    ),
                    total=safe_float_conversion(row["Обьем\nДоговоров,\nруб."]),
                    count=safe_float_conversion(row["Количество\nДоговоров,\nшт."]),
                    date=file_date,
                )
            )
        except Exception as e:
            log.error(f"Ошибка в строке {row}: {str(e)}")

    session.add_all(spimex_list)
    await session.commit()


async def process_file(file_path: str, file_date: datetime.date):
    try:
        log.info(f"Обработка файла: {os.path.basename(file_path)} (дата: {file_date})")

        df = await asyncio.to_thread(
            pd.read_excel, file_path, sheet_name="TRADE_SUMMARY"
        )
        filtered_data = prepare_data(df)

        if filtered_data.empty:
            log.warning(f"Нет данных для вставки в файле {os.path.basename(file_path)}")
            return

        async with db_helper.session_factory() as session:
            await insert_to_db(session, filtered_data, file_date)

    except Exception as e:
        log.error(f"Ошибка при обработке файла {os.path.basename(file_path)}: {e}")


async def process_all_files():
    xls_files = [f for f in os.listdir(settings.cf.download_dir) if f.endswith(".xls")]

    if not xls_files:
        log.warning(f"Не найдены XLS файлы в директории {settings.cf.download_dir}")
        return

    log.info(f"Найдено {len(xls_files)} файлов для обработки")

    # Создаем семафор для ограничения количества одновременно обрабатываемых файлов
    semaphore = asyncio.Semaphore(settings.cf.concurrent_processing)

    async def process_with_semaphore(file_name):
        async with semaphore:
            file_path = os.path.join(settings.cf.download_dir, file_name)

            date_str = file_name[:10]
            trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            await process_file(file_path, trade_date)

    tasks = [process_with_semaphore(file_name) for file_name in xls_files]

    await asyncio.gather(*tasks)

    log.info("Обработка всех файлов завершена")


async def main():
    try:
        log.info("Обработка файлов...")
        await process_all_files()
    finally:
        log.info("Обработка завершена")
        await db_helper.dispose()
