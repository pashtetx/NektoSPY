from typing import Dict
import json
import logging

class Action:
    
    def __init__(self, name: str, params: Dict) -> None:
        self.params = params
        self.params.update({"action": name})

    def to_serializable(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return obj

    def to_string(self) -> str:
        serializable_params = {key: self.to_serializable(value) for key, value in self.params.items()}
        logging.info(f"Serializing action: {serializable_params}")
        return "42" + json.dumps(["action", serializable_params])
