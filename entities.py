from typing import *
import json


class Slot:
    def __init__(self, pool, criteria: List[str]):
        self.itemid = None
        self.pool = pool
        self.criteria = criteria #list of avaiable categoies
    @property
    def item(self):
        return self.pool[self.itemid]
    def set(self, id):
        if (self.pool[id].category in self.criteria or self.criteria == []) and id != None:
            self.itemid = id   
    def save(self):
        return {
            "item": self.itemid,
            "criteria": self.criteria
        }