# говнокод писал @migainis и shw3pz @fuxsocy1
import asyncio
from nektome.client import Client
from nektome.dialog import Dialog
from nektome.messages.notice import Notice
import aioconsole
import logging
import os
import json
from colorama import init, Fore
from datetime import datetime

init(autoreset=True)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='log.txt')

TOKEN_FILE = 'tokens.json'

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
        'male_token': male_token,
        'female_token': female_token
    }
    save_tokens(tokens)
    return tokens

async def setup_clients():
    tokens = load_tokens()
    if not tokens:
        tokens = await get_token_input()

    male_client = Client(tokens['male_token'])
    female_client = Client(tokens['female_token'])
    return male_client, female_client

async def reconnect_and_search(client: Client, my_sex: str, wish_sex: str):
    try:
        if client.ws is None or client.ws.closed:
            logging.info(f"Reconnecting {my_sex} client...")
            await client.connect()
        await client.search(my_sex=my_sex, wish_sex=wish_sex, wish_age=[[1, 17]], my_age=[1, 17])
    except Exception as e:
        logging.error(f"Error while reconnecting or searching: {e}")

async def on_found(client: Client, notice: Notice) -> None:
    print("Connected!")
    logging.info(f"Client {client.token} connected with notice: {notice.params}")
    client.open_dialog(Dialog(notice.params.get("id"), client))

async def on_message(client: Client, notice: Notice) -> None:
    logging.info(f"New message for client {client.token}: {notice.params}")
    if notice.params.get("senderId") == client.id:
        return

    if hasattr(client, "dialog"):
        await client.dialog.read_message(notice.params.get("id"))
        message = notice.params.get("message")
        
        target_client = female_client if client == male_client else male_client
        if hasattr(target_client, "dialog"):
            await target_client.dialog.send_message(message)
            current_time = datetime.now().strftime('%H:%M:%S')
            prefix = 'F' if client == male_client else 'M'
            color = Fore.LIGHTMAGENTA_EX if prefix == 'F' else Fore.LIGHTBLUE_EX
            print(f"{color}{prefix} | {current_time}: {message}")
    else:
        logging.warning(f"Client {client.token} does not have an open dialog")

async def on_start(client: Client, notice: Notice, my_sex: str, wish_sex: str) -> None:
    logging.info(f"Start client with notice: {notice.params}")
    if notice.params.get("statusInfo"):
        client.open_dialog(Dialog(notice.params.get("statusInfo").get("anonDialogId"), client))
    print(f"Close dialog ({Fore.LIGHTBLUE_EX}male{Fore.RESET})" if client == male_client else f"Close dialog ({Fore.LIGHTMAGENTA_EX}female{Fore.RESET})")
    await client.close_dialog()
    await reconnect_and_search(client, my_sex, wish_sex)

async def on_close(client: Client, notice: Notice) -> None:
    logging.info(f"Dialog closed for client {client.token}")
    client_type = f"{Fore.LIGHTBLUE_EX}male{Fore.RESET}" if client == male_client else f"{Fore.LIGHTMAGENTA_EX}female{Fore.RESET}"
    print(f"Dialog closed for {client_type} client")

    await reconnect_and_search(male_client, "M", "F")
    await reconnect_and_search(female_client, "F", "M")

async def send_all(message: str) -> None:
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"YOU | {current_time}: {message}")
    if hasattr(male_client, "dialog"):
        await male_client.dialog.send_message(message)
    if hasattr(female_client, "dialog"):
        await female_client.dialog.send_message(message)

async def input_wait():
    while True:
        if hasattr(male_client, "dialog") and hasattr(female_client, "dialog"):
            await send_all(await aioconsole.ainput(">>> "))
        await asyncio.sleep(1)

async def main():
    global male_client, female_client
    print("Starting main function")
    logging.info("Starting main function")
    
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
        input_wait()
    )

asyncio.run(main())
