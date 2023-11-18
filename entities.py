from typing import *
import json


class Slot:
    def __init__(self, pool, id, criteria: List[str]):
        self.id = id
        self.item = None
        self.pool = pool
        self.criteria = criteria #list of avaiable categoies
    def set(self, id):
        if self.pool[id].category in self.criteria or self.criteria == []:
            self.item = self.pool[id]   
    def json(self):
        return {
            "id": self.id,
            "contain": self.item.json() if self.item else None
        }

class Container:
    slots = []
    def json(self):
        return {i.id: i.json() for i in self.slots}