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
                    level=logging.INFO)

settings = json.load(open("settings.json", 'rb'))
# Подгрузка настроек

u1MINUTE = 600  # 1 минута
u1HOUR = 3600   # 1 час
u1DAY = 86400   # день
notFindChangesSleepDelay = u1HOUR * 4
group = settings.get("group").upper()
lastNotification = None if settings.get("startNotification", False) else datetime.date.today() + datetime.timedelta(days=1)
# False - не будет оповещения на некст день сразу после запуска, True - будет
# Ставим когда было последние уведомление о заменах


async def main():
    global lastNotification, settings
    settings = json.load(open("settings.json", 'rb'))
    # Подгрузка настроек
    bchanges = False
    myVK_ID = settings.get("peer_id")
    TOKEN = settings.get("token")
    api = Bot(token=TOKEN)
    try:
        today = datetime.date.today() + datetime.timedelta(days=1)
        if lastNotification == today:
            raise ChildProcessError
        # elif today.isoweekday() == 7:
        #     raise BrokenPipeError
        monthformat = today.month if len(str(today.month)) == 2 else "0" + str(today.month)
        dayformat = today.day if len(str(today.day)) == 2 else "0" + str(today.day)
        changeslist = []
        changes = requests.get(f"http://tpcol.ru/images/Расписание_и_Замены/{dayformat}.{monthformat}.{today.year}.xlsx")
        # http://tpcol.ru/images/Расписание_и_Замены/26.05.2022.xlsx
        if changes.status_code == 200 and "<!DOCTYPE html>" not in str(changes.content):  # Файл есть
            logging.info(f"Ищем замену на {today.day}.{monthformat}.{today.year}. Файл скачен")
            lastNotification = today
            open(f"{today.day}.{monthformat}.{today.year}.xlsx", "wb").write(changes.content)
            changesexcel = pd.read_excel(f'{today.day}.{monthformat}.{today.year}.xlsx')
            if settings.get("stickers"):
                await api.api.messages.send(peer_id=myVK_ID,
                                            random_id=random.randrange(999999),
                                            sticker_id=settings.get("stickers")[random.randrange(len(settings.get("stickers")))])
            await api.api.messages.send(peer_id=myVK_ID,
                                        random_id=random.randrange(999999),
                                        message=f"@all {str(changesexcel.keys()[4]).capitalize()} для группы \"{group}\".")
            for i in changesexcel.itertuples():
                try:
                    name_group_change = str(i[4]).upper()
                    if name_group_change == group:
                        bchanges = True
                        logging.info(
                            f"Найдена замена на {today.day}.{monthformat}.{today.year} для группы \"{group}\".")
                        changeslist.append([int(i[3]), i[6], i[5], i[7]])
                except Exception as e:
                    await api.api.messages.send(peer_id=myVK_ID,
                                                random_id=random.randrange(999999),
                                                message=f"*v.nazukin(Мой начальник), замена найдена, но при "
                                                        f"выполнении произошла ошибка, иди проверь.\n\n{e}")
                    logging.info(f"Замена найдена, но при выполнении произошла ошибка. {e}")
            if not bchanges:
                await api.api.messages.send(peer_id=myVK_ID,
                                            random_id=random.randrange(999999),
                                            message=f"Замен для группы \"{group}\" нету.")
                logging.info(f"Замен на {today.day}.{monthformat}.{today.year} для группы \"{group}\" нету.")
                lastNotification = today
            changeslist.sort()
            for lschange in changeslist:
                if lschange[1].lower() == "нет":
                    await api.api.messages.send(peer_id=myVK_ID,
                                                random_id=random.randrange(999999),
                                                message=f"💦 {lschange[0]} пары не будет")
                else:
                    await api.api.messages.send(peer_id=myVK_ID,
                                                random_id=random.randrange(999999),
                                                message=f"""
    🔔 Замена на {lschange[0]} паре
    🤓 Замена на: {lschange[1]}
    👥 Преподаватель: {lschange[2]}
    🏚 Кабинет: {lschange[3]} каб.""")
                
        else:
            logging.info(
                f"Замены на {today.day}.{monthformat}.{today.year} ещё не выложили. Проверю ещё раз через 1 минуту")
            # await api.api.messages.send(peer_id=myVK_ID,
            #                             random_id=random.randrange(999999),
            #                             message=f"Замены на {today.day}.{monthformat}.{today.year} "
            #                                     f"ещё не выложили или их нет. Перепроверю ещё раз через 4 часа")
            await asyncio.sleep(u1MINUTE)
            raise NotImplementedError
        try:
            os.remove(f"{today.day}.{monthformat}.{today.year}.xlsx")
        except Exception as e:
            logging.warning(f"Ошибка при удалении файла {e}")
        await asyncio.sleep(u1MINUTE)
        # await asyncio.sleep(10)
    except NotImplementedError:
        # Когда при загрузке файла его не было
        logging.error("Проверяю ещё раз наличие замен спустя 10 минут.")
    except ChildProcessError:
        logging.error("Сегодня уже было уведомление о заменах, скипаю на 1 час.")
        await asyncio.sleep(u1HOUR * 1)
    except BrokenPipeError:
        logging.error("Сегодня суббота, через 4 часа ещё раз посмотрю.")
        await asyncio.sleep(u1HOUR * 4)
    # except Exception as e:
    #     logging.error(f"Произошла ошибка {e}.")


if __name__ == "__main__":
    logging.info(f"Токен подгружен. Бот работает.")
    while True:
        loop = asyncio.new_event_loop()
        tasks = [
            loop.create_task(main())
        ]
        loop.run_until_complete(asyncio.wait(tasks))
