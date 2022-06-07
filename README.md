# Что это и зачем оно мне надо
> Learning Bot - это бот с открытым исходным кодом для удобного оповещения в беседах группы о заменах для студентов.

# Установка
Для начала работы нужно установить `Python3.8 или выше`
Установить все зависимости:
```
asyncio
logging
pandas
vkbottle
```

# Использование
Для начала использования вам нужно переименовать `dafaultsettings.json` в `settings.json`, создать группу, создать в ней токен, и после вставить этот токен вместо фразы `token here`, после чего вам нужно включить возможность добалять сообщество в группы, добавить его в беседу (ваших сверсников) и выдать ему доступ ко всей переписки или просто админку.

# Описание полей в файле `settings.json`
Этот файл предназначен для быстрого редактирования настроек бота (при этом всем его требуется перезапускать для внесения изменений)

> `token` - токен сообщества

> `peer_id` - по стандарту если вы не писали в ЛС сообщества которое добавили в беседу = **2000000001**

> `group` - название вашей группы

> `stickers` - ID стикеров для рандомной отправкой перед сообщением о начале проверки замен (можно оставить пустым массивом)

> `startNotification` - прислать оповещение после запуска на этот день


# [Telegram разработчика](https://t.me/vladislav_osipov89)
