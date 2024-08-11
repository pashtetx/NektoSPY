# говнокод писал @migainis и shw3pz @fuxsocy1
import asyncio
import aioconsole
import eel
import json
import logging
import os
import sys
import threading


from nektome.client import Client
from nektome.dialog import Dialog
from nektome.messages.notice import Notice

eel.init("web")

TOKEN_FILE = 'tokens.json'
UNCOMPLETE_MESSAGES = []

class BotManager:
    def __init__(self):
        self.male_client = None
        self.female_client = None
        self.is_started = False

    def load_tokens(self):
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
        return None

    def save_tokens(self, tokens):
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f)

    async def get_token_input(self):
        tokens = {
            'male_token': await aioconsole.ainput("Введите токен для мужского клиента: "),
            'female_token': await aioconsole.ainput("Введите токен для женского клиента: ")
        }
        self.save_tokens(tokens)
        return tokens

    async def setup_clients(self):
        tokens = self.load_tokens()
        if not tokens:
            tokens = await self.get_token_input()

        self.male_client = Client(tokens['male_token'])
        self.female_client = Client(tokens['female_token'])

        self.register_callbacks(self.male_client, "M", "F")
        self.register_callbacks(self.female_client, "F", "M")

    def register_callbacks(self, client, my_sex, wish_sex):
        client.add_callback("dialog.opened", self.on_found)
        client.add_callback("auth.successToken", lambda c, n: self.on_start(c, n, my_sex, wish_sex))
        client.add_callback("messages.new", self.on_message)
        client.add_callback("dialog.closed", self.on_close)

    async def on_found(self, client, notice):
        logging.info(f"Client {client.token} connected with notice: {notice.params}")
        client.open_dialog(Dialog(notice.params.get("id"), client))
        if hasattr(self.male_client, "dialog") and hasattr(self.female_client, "dialog"):
            eel.appendMessage("OPEN", "Dialog started!")

        for message in UNCOMPLETE_MESSAGES:
            await client.dialog.send_message(message)

    async def on_message(self, client, notice):
        logging.info(f"New message for client {client.token}: {notice.params}")

        message = notice.params.get("message")
        
        if notice.params.get("senderId") == client.id:
            return

        target_client = self.female_client if client == self.male_client else self.male_client
        eel.appendMessage('F' if client == self.male_client else 'M', message)            
        
        if hasattr(target_client, "dialog"):
            await target_client.dialog.send_message(message)
        else:
            UNCOMPLETE_MESSAGES.append(message)

    async def on_start(self, client, notice, my_sex, wish_sex):
        logging.info(f"Start client with notice: {notice.params}")
        await client.close_dialog()
        await client.search(my_sex=my_sex, wish_sex=wish_sex, wish_age=[[1, 17]], my_age=[1, 17])

    async def on_close(self, client, notice):
        UNCOMPLETE_MESSAGES.clear()
        logging.info(f"Dialog closed for client {client.token}")
        eel.appendMessage("CLOSED", "Dialog closed")
        
        target_client = self.female_client if client == self.male_client else self.male_client
        client.remove_dialog()

        if not hasattr(self.male_client, "dialog"):
            await self.male_client.search(my_sex="M", wish_sex="F", wish_age=[[1, 17]], my_age=[1, 17])
        if not hasattr(self.female_client, "dialog"):
            await self.female_client.search(my_sex="M", wish_sex="F", wish_age=[[1, 17]], my_age=[1, 17])

    async def send_all(self, message):
        logging.info(f"Sending message: {message}")
        eel.appendMessage("YOU", message)
        if hasattr(self.male_client, "dialog"):
            await self.male_client.dialog.send_message(message)
        if hasattr(self.female_client, "dialog"):
            await self.female_client.dialog.send_message(message)

    async def wait_for_close(self):
        while self.is_started:
            await asyncio.sleep(1)

    async def run(self):
        await self.setup_clients()
        await asyncio.gather(
            self.male_client.connect(),
            self.female_client.connect(),
            self.wait_for_close()
        )

bot_manager = BotManager()

@eel.expose
def start_bots():
    bot_manager.is_started = True
    threading.Thread(target=lambda: asyncio.run(bot_manager.run())).start()

@eel.expose
def send(message):
    asyncio.run(bot_manager.send_all(message))

def on_close_app(name, *args):
    logging.info(f"Application {name} closed")
    bot_manager.is_started = False
    sys.exit()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='log.txt')

    try:
        # Пытаемся запустить с Edge
        eel.start("index.html", close_callback=on_close_app, size=(500, 700), mode='edge')
    except EnvironmentError as e:
        logging.error(f"Failed to start with Edge: {e}")
        try:
            # Если не удалось с Edge, пробуем с Firefox
            eel.start("index.html", close_callback=on_close_app, size=(500, 700), mode='firefox')
        except EnvironmentError as e:
            logging.critical(f"Failed to start with Firefox as well: {e}")
            sys.exit(1)
