from typing import Dict, Self

import json


class Notice:

    @staticmethod
    def parse(received_message: bytes) -> Self:
        try:
            if received_message.startswith("42"):
                params = json.loads(received_message[2:])[1]
                name, data = params.get("notice"), params.get("data")
                if not name:
                    raise ValueError("Uncorrent notice message!")
                return Notice(name, data)
        except IndexError:
            raise ValueError("Uncorrect notice message!")
    
    def __init__(self, name: str, params: Dict) -> None:
        self.params = params
        self.name = name