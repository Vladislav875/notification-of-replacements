import asyncio
import datetime
import json
import logging
import os
import random
import pandas as pd
import requests
from vkbottle.bot import Bot

logging.basicConfig(filename='logs.log', filemode='w',
                    format='%(asctime)s | %(levelname)s: %(message)s',
                    level=logging.WARNING)

settings = json.load(open("settings.json", 'rb'))
# Подгрузка настроек

TOKEN = settings.get("token")
api = Bot(token=TOKEN)
print(f"Load. Logging (token: {TOKEN})")
logging.info(f"Токен подгружен. Бот работает.")
myVK_ID = settings.get("peer_id")
# https://vk.com/club206974172

u1HOUR = 3600  # 1 час
u1DAY = 86400  # день
notFindChangesSleepDelay = u1HOUR * 4
group = settings.get("group").upper()
print(group)
lastNotification = None  # Когда было посление уведомление о заменах

stickers = settings.get("stickers")


async def main():
    global lastNotification
    bchanges = False
    try:
        today = datetime.date.today() + datetime.timedelta(days=1)
        # print("lastNotification", lastNotification, "\ntoday", today)
        if lastNotification == today or datetime.datetime.now().hour <= 15:
            # <= 15 что бы он с самого утра не проверял каждый час появление замен
            raise ChildProcessError
        month = today.month if len(str(today.month)) == 2 else "0" + str(today.month)
        changes = requests.get(f"http://tpcol.ru/images/Расписание_и_Замены/{today.day}.{month}.{today.year}.xlsx")
        # http://tpcol.ru/images/Расписание_и_Замены/26.05.2022.xlsx
        if stickers:
            await api.api.messages.send(peer_id=myVK_ID,
                                        random_id=random.randrange(999999),
                                        sticker_id=stickers[random.randrange(len(stickers))])
        await api.api.messages.send(peer_id=myVK_ID,
                                    random_id=random.randrange(999999),
                                    message=f"Проверяю замены на {today.day}.{month}.{today.year} для группы \"{group}\".")
        if changes.status_code == 200 and "<!DOCTYPE html>" not in str(changes.content):  # Файл есть
            logging.info(f"Ищем замену на {today.day}.{month}.{today.year}. Файл скачен")
            open(f"{today.day}.{month}.{today.year}.xlsx", "wb").write(changes.content)
            changesexcel = pd.read_excel(f'{today.day}.{month}.{today.year}.xlsx')
            for i in changesexcel.itertuples():
                try:
                    name_group_change = str(i[4]).upper()
                    if name_group_change == group:
                        bchanges = True
                        logging.info(f"Найдена замена на {today.day}.{month}.{today.year} для группы \"{group}\".")
                        await api.api.messages.send(peer_id=myVK_ID,
                                                    random_id=random.randrange(999999),
                                                    message=f"""
🔔 Замена на {i[3]} паре
🤓 Замена на: {i[6]}
👥 Преподаватель: {i[5]}
🏚 Кабинет: {i[7]} каб.""")
                        lastNotification = today
                except Exception as e:
                    await api.api.messages.send(peer_id=myVK_ID,
                                                random_id=random.randrange(999999),
                                                message=f"*v.nazukin(Мой начальник), замена найдена, но при "
                                                        f"выполнении произошла ошибка, иди проверь.\n\n{e}")
                    logging.info(f"Замена найдена, но при выполнении произошла ошибка. {e}")
            if not bchanges:
                await api.api.messages.send(peer_id=myVK_ID,
                                            random_id=random.randrange(999999),
                                            message=f"Замен для группы \"{group}\" нету, но возможно я ошибаюсь...")
                logging.info(f"Замен на {today.day}.{month}.{today.year} для группы \"{group}\" нету.")
                lastNotification = today
        else:
            logging.info(f"Замены на {today.day}.{month}.{today.year} ещё не выложили. Проверю ещё раз через 4 часа")
            await api.api.messages.send(peer_id=myVK_ID,
                                        random_id=random.randrange(999999),
                                        message=f"Замены на {today.day}.{month}.{today.year} "
                                                f"ещё не выложили или их нет. Перепроверю ещё раз через 4 часа")
            await asyncio.sleep(notFindChangesSleepDelay)
            raise NotImplementedError
        try:
            os.remove(f"{today.day}.{month}.{today.year}.xlsx")
        except Exception as e:
            logging.warning(f"Ошибка при удалении файла {e}")
        await asyncio.sleep(u1HOUR * 1)
        # await asyncio.sleep(10)
    except NotImplementedError:
        logging.error("Проверяю ещё раз наличие замен спустя 4 часа.")
    except ChildProcessError:
        logging.error("Сегодня уже было уведомление о заменах или сейчас <= 15 часов, скипаю на 1 час.")
        await asyncio.sleep(u1HOUR * 1)
    except Exception as e:
        logging.error(f"Произошла ошибка {e}.")


if __name__ == "__main__":
    while True:
        loop = asyncio.new_event_loop()
        tasks = [
            loop.create_task(main())
        ]
        loop.run_until_complete(asyncio.wait(tasks))
