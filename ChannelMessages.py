import configparser
import json
from datetime import datetime, timedelta

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)


# some functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)


async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() is False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    user_input_channel = input('enter entity(telegram URL or entity id):')

    if user_input_channel.isdigit():
        entity = PeerChannel(int(user_input_channel))
    else:
        entity = user_input_channel

    my_channel = await client.get_entity(entity)

    offset_id = 0
    limit = 100
    all_messages = []
    total_messages = 0
    total_count_limit = 0

    users_ids = []

    while True:
        print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)

        today = datetime.today()
        first = today.replace(day=1)
        last_month = first - timedelta(days=1)

        history = await client(GetHistoryRequest(
            peer=my_channel,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        messages = list(filter(lambda x: datetime(year=x.date.year, month=x.date.month, day=x.date.day) > last_month, history.messages))

        if not messages:
            break

        for message in messages:
            all_messages.append(message.to_dict())
            try:
                user_id = message.from_id.user_id
                if user_id not in users_ids:
                    users_ids.append(user_id)
            except AttributeError:
                pass

        offset_id = messages[len(messages) - 1].id
        total_messages = len(all_messages)

        if total_messages == 10000:  # total_count_limit != 0 and total_messages >= total_count_limit:
            break

    text_file = open('unique_users_ids_from_messages.txt', mode='wt', encoding='utf-8')
    for user_id in users_ids:
        text_file.write(str(user_id) + '\n')
    text_file.close()

    with open('channel_messages.json', 'w', encoding='utf-8') as outfile:
        json.dump(all_messages, outfile, cls=DateTimeEncoder, ensure_ascii=False)


with client:
    client.loop.run_until_complete(main(phone))
