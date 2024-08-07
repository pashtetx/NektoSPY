from .client import Client
from .messages.action import Action

from time import time
import random


class Dialog:

    def __init__(self, id: int, client: Client) -> None:
        self.client = client
        self.id = id

    async def send_message(self, text: str) -> None:
        action = Action(name="anon.message", params={
            "dialogId":self.id,
            "fileId":None,
            "message":text,
            "randomId":f"{self.client.id}_{time()}0.{random.randint(10000000, 1000000000)}",
        })
        await self.client.ws.send(action.to_string())
    
    async def read_message(self, id: int) -> None:
        action = Action(name="anon.readMessages", params={
            "dialogId":self.id,
            "lastMessageId":id
        })
        await self.client.ws.send(action.to_string())