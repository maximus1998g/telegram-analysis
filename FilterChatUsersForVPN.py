import configparser
import time
from datetime import timedelta

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import *
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import *

# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = int(config['Telegram']['api_id'])
api_hash = str(config['Telegram']['api_hash'])

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)

chats = list(dict.fromkeys(
    [
        'https://t.me/fpmi_abitu',
        'https://t.me/mm_abiturient',
        'https://t.me/ranepa_vision',
        'https://t.me/abiturienti2020yil',
        'https://t.me/abiturientDNMU',
        'https://t.me/abitMAI3_2021',
        'https://t.me/abit090302',
        'https://t.me/beskonechnoe_stradanie',
        'https://t.me/riveria_students',
        'https://t.me/magistraturakz2022',
        'https://t.me/magistr2021qarshi',
        'https://t.me/samdumagistr1kurs2022',
        'https://t.me/fapriem',
        'https://t.me/ignbakalavriat',
        'https://t.me/soflhseba2022',
        'https://t.me/practika2022',
        'https://t.me/gist_bio_agma',
        'https://t.me/sinergiyandmosap',
        'https://t.me/matematika_chat',
        'https://t.me/mirea_chat_postuplenie_2022',
        'https://t.me/nesadmissions2023',
        'https://t.me/abituramgmsu_chat',
        'https://t.me/abituramgtu',
        'https://t.me/abiturient_itmo',
        'https://t.me/abit_ct_2022',
        'https://t.me/physics_itmo',
        'https://t.me/abit_ct',
        'https://t.me/bakalavr_iknt_2023'
    ]
))

users_send_messages_last_month_ids = []
filtered_usernames = []


def get_last_month():
    today = datetime.today()
    first = today.replace(day=1)
    return first - timedelta(days=1)


async def auth():
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() is False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))


async def main():
    await auth()

    for chat in chats:
        print('\n')
        print(str(chats.index(chat) + 1) + '/' + str(len(chats)))
        print('Chat: ' + chat)
        # get chat entity
        if chat.isdigit():
            entity = PeerChannel(int(chat))
        else:
            entity = chat

        chat_entity = await client.get_entity(entity)

        # get unique user ids by messages for the last month
        offset_id = 0
        limit = 10000
        total_messages = 0
        max_messages_count = 10000
        all_messages = []

        while True:
            print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
            time.sleep(1)
            # noinspection PyTypeChecker
            history = await client(GetHistoryRequest(
                peer=chat_entity,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            messages = list(
                filter(lambda x: datetime(year=x.date.year, month=x.date.month, day=x.date.day) > get_last_month(),
                       history.messages)
            )

            if not messages:
                break

            for message in messages:
                all_messages.append(message)
                try:
                    user_id = message.from_id.user_id
                    if user_id not in users_send_messages_last_month_ids:
                        users_send_messages_last_month_ids.append(user_id)
                except AttributeError:
                    pass

            offset_id = messages[len(messages) - 1].id

            total_messages = len(all_messages)
            if total_messages == max_messages_count:
                break

        # filter users
        offset = 0
        all_participants = []
        while True:
            time.sleep(1)
            # noinspection PyTypeChecker
            participants = await client(GetParticipantsRequest(
                channel=chat_entity,
                filter=ChannelParticipantsRecent(),
                offset=offset,
                limit=limit,
                hash=0
            ))
            if not participants.users:
                break

            all_participants.extend(participants.users)
            offset += len(participants.users)

        filtered_participants = list(
            filter(lambda x:
                   x.deleted is False and
                   x.fake is False and
                   x.restricted is False and
                   x.scam is False and
                   x.support is False and
                   x.bot is False and
                   x.username is not None and
                   isinstance(x.status, UserStatusRecently) and
                   x.id in users_send_messages_last_month_ids,
                   all_participants)
        )

        filtered_usernames.extend([user.username for user in filtered_participants])
        print("Filtered users:", len(filtered_participants))

    # remove duplicates
    unique_usernames = list(dict.fromkeys(filtered_usernames))
    # save filtered usernames to file
    text_file = open('usernames.txt', mode='wt', encoding='utf-8')
    for unique_username in unique_usernames:
        text_file.write('@' + unique_username + '\n')
    text_file.close()


client.loop.run_until_complete(main())
