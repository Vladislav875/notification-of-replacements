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

u1HOUR = 3600  # 1 час
u1DAY = 86400  # день
notFindChangesSleepDelay = u1HOUR * 4
group = settings.get("group").upper()
lastNotification = None  # Когда было посление уведомление о заменах

stickers = settings.get("stickers")


async def main():
    global lastNotification
    bchanges = False
    try:
        today = datetime.date.today() + datetime.timedelta(days=1)
        # print("lastNotification", lastNotification, "\ntoday", today)
        if lastNotification == today:  # or datetime.datetime.now().hour <= 15
            # <= 15 что бы он с самого утра не проверял каждый час появление замен
            raise ChildProcessError
        monthformat = today.month if len(str(today.month)) == 2 else "0" + str(today.month)
        dayformat = today.day if len(str(today.day)) == 2 else "0" + str(today.day)
        changes = requests.get(f"http://tpcol.ru/images/Расписание_и_Замены/{dayformat}.{monthformat}.{today.year}.xlsx")
        # http://tpcol.ru/images/Расписание_и_Замены/26.05.2022.xlsx
        if stickers:
            await api.api.messages.send(peer_id=myVK_ID,
                                        random_id=random.randrange(999999),
                                        sticker_id=stickers[random.randrange(len(stickers))])
        await api.api.messages.send(peer_id=myVK_ID,
                                    random_id=random.randrange(999999),
                                    message=f"Проверяю замены на {today.day}.{monthformat}.{today.year} для группы \"{group}\".")
        if changes.status_code == 200 and "<!DOCTYPE html>" not in str(changes.content):  # Файл есть
            logging.info(f"Ищем замену на {today.day}.{monthformat}.{today.year}. Файл скачен")
            open(f"{today.day}.{monthformat}.{today.year}.xlsx", "wb").write(changes.content)
            changesexcel = pd.read_excel(f'{today.day}.{monthformat}.{today.year}.xlsx')
            for i in changesexcel.itertuples():
                try:
                    name_group_change = str(i[4]).upper()
                    if name_group_change == group:
                        bchanges = True
                        logging.info(
                            f"Найдена замена на {today.day}.{monthformat}.{today.year} для группы \"{group}\".")
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
                logging.info(f"Замен на {today.day}.{monthformat}.{today.year} для группы \"{group}\" нету.")
                lastNotification = today
        else:
            logging.info(
                f"Замены на {today.day}.{monthformat}.{today.year} ещё не выложили. Проверю ещё раз через 4 часа")
            # await api.api.messages.send(peer_id=myVK_ID,
            #                             random_id=random.randrange(999999),
            #                             message=f"Замены на {today.day}.{monthformat}.{today.year} "
            #                                     f"ещё не выложили или их нет. Перепроверю ещё раз через 4 часа")
            raise NotImplementedError
        try:
            os.remove(f"{today.day}.{monthformat}.{today.year}.xlsx")
        except Exception as e:
            logging.warning(f"Ошибка при удалении файла {e}")
        await asyncio.sleep(u1HOUR * 1)
        # await asyncio.sleep(10)
    except NotImplementedError:
        # Когда при загрузке файла его не было
        await asyncio.sleep(u1HOUR * 1)
        logging.error("Проверяю ещё раз наличие замен спустя 1 час.")
    except ChildProcessError:
        logging.error("Сегодня уже было уведомление о заменах, скипаю на 1 час.")
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
