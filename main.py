#говнокод писал @migainis и shw3pz @fuxsocy1
import asyncio
from nektome.client import Client
from nektome.dialog import Dialog
from nektome.messages.notice import Notice
import aioconsole
import logging
import os
import json
import sys

import eel
import threading

eel.init("web")

IS_STARTED = False

TOKEN_FILE = 'tokens.json'

UNCOMPLETE_MESSAGES = []

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    else:
        return None

def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

async def get_token_input():
    male_token = await aioconsole.ainput("Введите токен для мужского клиента: ")
    female_token = await aioconsole.ainput("Введите токен для женского клиента: ")
    tokens = {
        'male_token': male_token
        'female_token': female_token
    }
    save_tokens(tokens)
    return tokens

async def setup_clients():
    tokens = load_tokens()
    if not tokens:
        tokens = await get_token_input()

    male_client = Client(tokens['male_token'],
    female_client = Client(tokens['female_token']))
    return male_client, female_client

async def on_found(client: Client, notice: Notice) -> None:
    print("Connected!")
    logging.info(f"Client {client.token} connected with notice: {notice.params}")
    client.open_dialog(Dialog(notice.params.get("id"), client))
    delattr(client, "searching")
    if hasattr(male_client, "dialog") and hasattr(female_client, "dialog"):
        eel.appendMessage("OPEN", "Dialog started!")
    
    if len(UNCOMPLETE_MESSAGES) > 0:
        print(UNCOMPLETE_MESSAGES)
        for message in UNCOMPLETE_MESSAGES:
            await client.dialog.send_message(message)

async def on_message(client: Client, notice: Notice) -> None:
    logging.info(f"New message for client {client.token}: {notice.params}")
    print(notice.params.get("message"))
    if notice.params.get("senderId") == client.id:
        return

    if hasattr(client, "dialog"):
        await client.dialog.read_message(notice.params.get("id"))
        message = notice.params.get("message")
        
        target_client = female_client if client == male_client else male_client
        eel.appendMessage('F' if client == male_client else 'M', message)            
        print(f"{'F' if client == male_client else 'M'}: {message}")

        if hasattr(target_client, "dialog"):
            await target_client.dialog.send_message(message)
        else:
            UNCOMPLETE_MESSAGES.append(notice.params.get("message"))
    else:
        logging.warning(f"Client {client.token} does not have an open dialog")

async def on_start(client: Client, notice: Notice, my_sex: str, wish_sex: str) -> None:
    logging.info(f"Start client with notice: {notice.params}")
    if notice.params.get("statusInfo"):
        client.open_dialog(Dialog(notice.params.get("statusInfo").get("anonDialogId"), client))
        print(f"Close dialog ({'male' if client == male_client else 'female'})")
    await client.close_dialog()
    await client.search(my_sex=my_sex, wish_sex=wish_sex, wish_age=[[1, 17]], my_age=[1, 17])

async def on_close(client: Client, notice: Notice) -> None:
    UNCOMPLETE_MESSAGES.clear()
    logging.info(f"Dialog closed for client {client.token}")
    eel.appendMessage("CLOSED","Dialog closed")
    print(f"Dialog closed for {'male' if client == male_client else 'female'} client")

    target_client = female_client if client == male_client else male_client

    client.remove_dialog()

    if hasattr(target_client, "dialog"):
        await target_client.close_dialog()
    
    if not hasattr(male_client, "dilog") and not hasattr(male_client, "searching"):
        await male_client.search(my_sex="M", wish_sex="F", wish_age=[[1, 17]], my_age=[1, 17])
    if not hasattr(female_client, "dialog") and not hasattr(female_client, "searching"):
        await female_client.search(my_sex="M", wish_sex="F", wish_age=[[1, 17]], my_age=[1, 17])


async def send_all(message: str) -> None:
    print(f"YOU: {message}")
    eel.appendMessage("YOU", message)
    if hasattr(male_client, "dialog"):
        await male_client.dialog.send_message(message)
    if hasattr(female_client, "dialog"):
        await female_client.dialog.send_message(message)

async def wait_for_close():
    while True:
        if not IS_STARTED:
            print(IS_STARTED)
            sys.exit()
        await asyncio.sleep(1)

async def main():
    global male_client, female_client
    print("Starting main function")
    logging.info("Starting main function")

    asyncio.ensure_future(wait_for_close())
    
    male_client, female_client = await setup_clients()

    male_client.add_callback("dialog.opened", on_found)
    male_client.add_callback("auth.successToken", lambda client, notice: on_start(client, notice, "M", "F"))
    male_client.add_callback("messages.new", on_message)
    male_client.add_callback("dialog.closed", on_close)

    female_client.add_callback("dialog.opened", on_found)
    female_client.add_callback("auth.successToken", lambda client, notice: on_start(client, notice, "F", "M"))
    female_client.add_callback("messages.new", on_message)
    female_client.add_callback("dialog.closed", on_close)

    await asyncio.gather(
        male_client.connect(),
        female_client.connect(),
    )

nektome_bot = threading.Thread(target=asyncio.run, args=(main(),))

@eel.expose
def start_bots():
    nektome_bot.start()

@eel.expose
def send(message: str) -> None:
    asyncio.run(send_all(message))

def on_close_app(name: str, *args, **kwargs):
    print(name, "closed")
    global IS_STARTED
    IS_STARTED = False
    sys.exit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='log.txt')
    IS_STARTED = True
    eel.start("index.html", close_callback=on_close_app, size=(500, 700))

