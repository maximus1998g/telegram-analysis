import configparser

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import *
from telethon.tl.types import *
from telethon.tl.types import (
    PeerChannel
)

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
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    user_input_channel = input("enter entity(telegram URL or entity id):")

    if user_input_channel.isdigit():
        entity = PeerChannel(int(user_input_channel))
    else:
        entity = user_input_channel

    my_channel = await client.get_entity(entity)

    offset = 0
    limit = 10000
    all_participants = []

    while True:
        participants = await client(GetParticipantsRequest(
            my_channel, ChannelParticipantsRecent(), offset, limit,
            hash=0
        ))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset += len(participants.users)

    users_ids = []
    with open('unique_users_ids_from_messages.txt') as file:
        users_ids = [int(line.rstrip()) for line in file]

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
               x.id in users_ids,
               all_participants)
    )

    text_file = open('usernames.txt', mode='wt', encoding='utf-8')
    for participant in filtered_participants:
        text_file.write('@' + participant.username + '\n')
    text_file.close()

    # https://t.me/fpmi_abitu

    # all_user_details = []

    # for participant in filtered_participants:
    #     all_user_details.append({"id": participant.username})

    # with open('user_data.json', 'w') as outfile:
    #     json.dump(all_user_details, outfile)


with client:
    client.loop.run_until_complete(main(phone))
