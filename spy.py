import asyncio
from datetime import datetime, timedelta, timezone
from sys import argv, exit
from telethon import TelegramClient, events, connection
from telethon.tl.types import UserStatusRecently, UserStatusEmpty, UserStatusOnline, UserStatusOffline, PeerUser, PeerChat, PeerChannel
from telethon.extensions import markdown
from time import mktime, sleep
import telethon.sync
from threading import Thread
import collections

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
API_HASH = 'e51a3154d2e0c45e5ed70251d68382de'
API_ID = '15787995'
BOT_TOKEN = "7731766567:AAE_ml1HV3qjkHefRcClV7TUYbChWygpVfk"

client = TelegramClient('data_thief', API_ID, API_HASH, system_version="4.16.30-vxCUSTOM")

client.connect()
client.start()
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
data = {}

help_messages = ['/start - start online monitoring ',
         '/stop - stop online monitoring ',
         '/help - show help ',
         '/add - add user to monitoring list "/add username (without @)"',
         '/list - show added users',
         '/clear - clear user list',
         '/remove - remove user from list with position in list (to show use /list command)"/remove 1"',
         '/setdelay - set delay between user check in seconds',
         '/logs - display command log',
         '/clearlogs - clear the command log file',
         '/cleardata - reset configuration',
         '/disconnect - disconnect bot',
         '/getall - status']


print('running')
class Contact:
    online = None
    last_offline = None
    last_online = None
    id = ''
    name = ''

    def __init__(self, name):
        self.name = name
    def __str__(self):
        return f'{self.name}'

@bot.on(events.NewMessage(pattern='^/logs$'))
async def logs(event):
    """Send a message when the command /start is issued."""
    try:
        with open('spy_log.txt', 'r') as file:
            str = file.read()
        await event.respond(str)
    except:
        pass

@bot.on(events.NewMessage(pattern='/clearlogs$'))
async def clearLogs(event):
    """Send a message when the command /start is issued."""
    open('spy_log.txt', 'w').close()
    await event.respond('logs has been deleted')

@bot.on(events.NewMessage(pattern='^/clear$'))
async def clear(event):
    """Send a message when the command /start is issued."""
    message = event.message
    id = message.chat_id
    data[id] = {}
    await event.respond('User list has been cleared')

@bot.on(events.NewMessage(pattern='^/help$'))
async def help(event):
    await event.respond('\n'.join(help_messages))

@bot.on(events.NewMessage())
async def log(event):
    """Send a message when the command /start is issued."""
    message = event.message
    id = message.chat_id
    printToFile(f'{datetime.now().strftime(DATETIME_FORMAT)}: [{id}]: {message.message}')

@bot.on(events.NewMessage(pattern='^/stop$'))
async def stop(event):
    """Send a message when the command /start is issued."""
    message = event.message
    id = message.chat_id
    if id not in data:
        data[id] = {}
    user_data = data[id]
    user_data['is_running'] = False
    await event.respond('Monitoring has been stopped')

@bot.on(events.NewMessage(pattern='^/cleardata$'))
async def clearData(event):
    data.clear()
    await event.respond('Data has been cleared')

@bot.on(events.NewMessage(pattern='^/start$'))
async def start(event):
    message = event.message
    id = message.chat_id
    if id not in data:
        data[id] = {}
    user_data = data[id]
    if('is_running' in user_data and user_data['is_running']):
        await event.respond('Spy is already started')
        return

    if 'contacts' not in user_data:
        user_data['contacts'] = []

    contacts = user_data['contacts']

    if(len(contacts) < 1):
        await event.respond('No contacts added')
        return
    await event.respond('Monitoring has been started')

    counter = 0
    user_data['is_running'] = True

    while True:
        user_data = data[id]
        if(not user_data['is_running'] or len(contacts) < 1):
            break;
        counter+=1
        tasks = []
        for contact in contacts:
            tasks.append(asyncio.create_task(check_status(contact, event)))
            await asyncio.gather(*tasks)
        delay = 1
        if('delay' in user_data):
            delay = user_data['delay']
        sleep(delay)
    user_data['is_running'] = False
    await event.respond(f'Spy gonna zzzzzz...')

@bot.on(events.NewMessage(pattern='^/add'))
async def add(event):
    message = event.message
    person_info = message.message.split()
    name = person_info[1]
    id = message.chat_id
    if id not in data:
        data[id] = {}
    user_data = data[id]

    if 'contacts' not in user_data:
        user_data['contacts'] = []
    contacts = user_data['contacts']
    contact = Contact(name)
    contacts.append(contact)
    await event.respond(f'@{name}: has been added')


@bot.on(events.NewMessage(pattern='^/remove'))
async def remove(event):
    message = event.message
    person_info = message.message.split()
    index = int(person_info[1])
    id = message.chat_id
    if id not in data:
        data[id] = {}
    user_data = data[id]

    if 'contacts' not in user_data:
        user_data['contacts'] = []
    contacts = user_data['contacts']

    if(len(contacts) > index):
        del contacts[index]
        await event.respond(f'User №{index} has been deleted')
    else:
        await event.respond('Incorrect index')

@bot.on(events.NewMessage(pattern='^/setdelay'))
async def setDelay(event):
    message = event.message
    person_info = message.message.split()
    index = int(person_info[1])
    id = message.chat_id
    if id not in data:
        data[id] = {}
    user_data = data[id]

    print(index)
    if(index >= 0):
        user_data['delay'] = index
        await event.respond(f'Delay has been updated to {index}')
    else:
        await event.respond('Incorrect delay')

@bot.on(events.NewMessage(pattern='^/disconnect$'))
async def disconnect(event):
    await event.respond('Bot gonna disconnect')
    await bot.disconnect()

@bot.on(events.NewMessage(pattern='/list'))
async def list(event):
    message = event.message
    id = message.chat_id
    if id not in data:
        data[id] = {}
    user_data = data[id]

    if 'contacts' not in user_data:
        user_data['contacts'] = []
    contacts = user_data['contacts']
    response = 'List is empty'
    if(len(contacts)):
        response = 'User list: \n' + '\n' + '\n'.join([f'{index} - @{x}' for index, x in enumerate(contacts)])
        await event.respond(response)

@bot.on(events.NewMessage(pattern='/getall'))
async def getAll(event):
    response = 'list: '
    for key, value in data.items():
        response += f'{key}:\n'
        for j, i in value.items():
            if (isinstance(i, collections.abc.Sequence)):
                response += f'{j}: ' + '\n'.join([str(f'@{x}') for x in i]) + '\n'
            else:
                response += f'{j}: {i}\n'
        response += '\n'
    await event.respond(response)

def main():
    """Start the bot."""
    bot.run_until_disconnected()


async def check_status(contact, event):
    account = await client.get_entity(contact.name)

    if isinstance(account.status, UserStatusOnline):
        if contact.online != True:
            contact.online = True
            contact.last_offline = datetime.now()
            was_offline='unknown offline time'
            if contact.last_online is not None:
                contact.last_offline = contact.last_offline.replace(tzinfo=timezone.utc)
                was_offline = contact.last_offline - contact.last_online
                await event.respond(f'{get_interval(was_offline)}: @{contact.name} Online')
    elif isinstance(account.status, UserStatusOffline):
        if contact.online == True:
            contact.online = False
            last_time_online = utc2localtime(datetime.fromtimestamp(account.status.was_online.timestamp()))
            if (last_time_online is None):
                last_time_online = datetime.now()
            contact.last_online = account.status.was_online

            was_online='unknown online time'
            if contact.last_offline is not None:
                contact.last_offline = contact.last_offline.replace(tzinfo=timezone.utc)
            was_online = contact.last_online - contact.last_offline
            await event.respond(f'{get_interval(was_online)}: @{contact.name} Offline')
        contact.last_offline = None
    else:
        if contact.online == True:
            contact.online = False
            contact.last_online = datetime.now()

            was_online='unknown online time'
            if contact.last_offline is not None:
              was_online = contact.last_online - contact.last_offline
            await event.respond(f'{get_interval(was_online)}: @{contact.name} Offline')
            contact.last_offline = None

def utc2localtime(utc):
    pivot = mktime(utc.timetuple())
    offset = datetime.fromtimestamp(pivot) - datetime.utcfromtimestamp(pivot)
    utc_with_offset = utc + offset
    utc_with_offset = utc_with_offset.replace(tzinfo=timezone.utc)
    local_time = utc_with_offset.astimezone(tz=None)
    return local_time




def printToFile(str):
    file_name = 'spy_log.txt'
    with open(file_name,'a') as f:
        print(str)
        f.write(str + '\n')

def get_interval(date):
    if date == 'unknown online time':
        return 'unknown'

    if isinstance(date, timedelta):
        days = date.days
        hours, remainder = divmod(date.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if date.days < 0:
            days = -days

        formatted_time = f'{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}'
        return formatted_time
    else:
        return 'unknown'








if __name__ == '__main__':
    main()
