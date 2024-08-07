from .messages.action import Action
from .messages.notice import Notice
from typing import Callable, List
import websockets
import logging

class Client:
    """
    Nektome Client class
    """

    ws_endpoint: str = "wss://im.nekto.me/socket.io/?EIO=3&transport=websocket"

    def __init__(self, token: str) -> None:
        self.token = token
        self.callbacks = {}

    def add_callback(self, notice: str, callback: Callable) -> None:
        self.callbacks[notice] = callback

    def open_dialog(self, dialog) -> None:
        setattr(self, "dialog", dialog)
        logging.info(f"Opened dialog: {dialog.id}")
    
    def remove_dialog(self) -> None:
        if hasattr(self, "dialog"):
            logging.info(f"Removing dialog: {self.dialog.id}")
            delattr(self, "dialog")

    async def close_dialog(self) -> None:
        if hasattr(self, "dialog"):
            action = Action("anon.leaveDialog", {
                "dialogId": self.dialog.id
            })
            await self.ws.send(action.to_string())
            logging.info(f"Dialog closed: {self.dialog.id}")
            self.remove_dialog()

    async def login(self):
        auth_action = Action("auth.sendToken", {"token": self.token})
        await self.ws.send(auth_action.to_string())
        logging.info("Logged in")

    async def search(self, 
                     my_sex: str, 
                     wish_sex: str, 
                     my_age: List[int],
                     wish_age: List[List[int]]
            ) -> None:
        action = Action(name="search.run", params={
            "mySex": my_sex,
            "myAge": my_age,
            "wishSex": wish_sex,
            "wishAge": wish_age,
        })
        await self.ws.send(action.to_string())
        logging.info(f"Search started: my_sex={my_sex}, wish_sex={wish_sex}")

    async def connect(self) -> None:
        logging.info("Connecting to websocket")
        async with websockets.connect(self.ws_endpoint, ping_interval=None) as connection:
            self.ws = connection
            await self.login()
            async for message in connection:
                if message == "2":
                    await self.ws.send("2")
                    continue
                notice = Notice.parse(message)
                if notice:
                    if notice.name == "auth.successToken":
                        self.id = notice.params.get("id")
                    callback = self.callbacks.get(notice.name)
                    if callback:
                        await callback(self, notice)
            logging.info("Connection closed")
