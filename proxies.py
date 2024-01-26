from sqlalchemy.future import select
import asyncio
import models
import json

"""class JSONProxy:
	def __init__(self, dict_={}):
		self.dict = dict_
	def __getattr__(self, name):
		if name == "dict":
			return self.dict
		elif name in self.dict.keys():
			attr = self.dict[name]
			if type(attr) == dict:
				return JSONProxy(attr)
			else:
				return attr
		else:
			return None
	def __setattr__(self, name, value):
		if name == "dict":
			self.dict = value
			return
		self.dict[name] = value
"""

class BaseProxy:
	def __init__(self, model, *args, **kwargs):
		self.model_link = model
		print(kwargs)
		self.add = kwargs
	def __getattr__(self, k):
		if k in self.__dict__:
			return self.__dict__[k]
		elif k in self.add:
			return self.add[k]
		return self.model_link.__dict__[k]
	def json(self):
		b = self.__dict__.copy()
		b.pop("model_link")
		b.pop("add")
		for k, v in self.model_link.__dict__.items():
			if k not in b and k not in ['model_link', '_sa_instance_state']:
				b[k] = v
		return b

class PlayerProxy(BaseProxy):
	type = "player"
	def sync_from(self):
		self.state = json.loads(self.model_link.state)
		self.appearance = json.loads(self.model_link.appearance)
	def sync_to(self):
		self.model_link.state = json.dumps(self.state)
		self.model_link.appearance = json.dumps(self.appearance)


class StaticEntityProxy(BaseProxy):
	def sync_from(self):
		self.statedata = json.loads(self.model_link.state)
		self.appearancedata = json.loads(self.model_link.appearance)
	def sync_to(self):
		self.model_link.state = json.dumps(self.statedata)
		self.model_link.appearance = json.dumps(self.appearancedata)

class ItemProxy(BaseProxy):
	def sync_from(self):
		self.description = json.loads(self.model_link.description)
		self.state = json.loads(self.model_link.state)
	def sync_to(self):
		self.model_link.description = json.dumps(self.description)
		self.model_link.state = json.dumps(self.state)

class ItemPool:
	pool = dict()
	session = models.async_session()

	async def get(self, id):
		if not id in self.pool.keys():
			await self.add_item(id)
		return self.pool[id]

	async def add_item(self, id):
		item = (await self.session.execute(select(models.Item).where(models.Item.id == id))).one_or_none()[0]
		proxy = ItemProxy(item)
		proxy.sync_from()
		self.pool[id] = proxy

	async def save(self, id = None):
		if id == None:
			for i, j in self.pool.items():
				j.sync_to()
		else:
			self.pool[id].sync_to()
		await self.session.commit()

class PlayerPool:
	pool = dict()
	session = models.async_session()

	async def add_item(self, dbid, poolid):
		item = (await self.session.execute(select(models.Player).where(models.Player.id == dbid))).one_or_none()[0]
		proxy = PlayerProxy(item)
		proxy.sync_from()
		self.pool[poolid] = proxy

	async def save(self, id):
		self.pool[id].sync_to()
		await self.session.commit()

class StaticEntitiesPool:
	pool = dict()
	session = models.async_session()

	async def add_item(self, dbid, poolid):
		item = (await self.session.execute(select(models.StaticEntity).where(models.StaticEntity.id == dbid))).one_or_none()[0]
		proxy = StaticEntityProxy(item)
		proxy.sync_from()
		self.pool[poolid] = proxy

	async def save(self, id = None):
		for i, j in self.pool.items():
			j.sync_to()
		self.session.commit()

class SlotProxy(BaseProxy):
	def sync_from(self):
		self.criteria = self.model_link.criteria
		self.item_id = self.model_link.item
	def sync_to(self):
		self.model_link.criteria = self.criteria
		self.model_link.item = self.item_id
	@property
	def item(self):
		return asyncio.run(self.itempool.get(self.item_id))

class SlotPool:
	pool = dict()
	session = models.async_session()

	def __init__(self, pool):
		self.itempool = pool

	async def add_item(self, dbid, poolid):
		item = (await self.session.execute(select(models.Slot).where(models.Slot.id == dbid))).one_or_none()[0]
		proxy = SlotProxy(item, itempool=self.itempool)
		proxy.sync_from()
		self.pool[poolid] = proxy

	async def save(self, id = None):
		for i, j in self.pool.items():
			j.sync_to()
		self.session.commit()

class Inventory:
	slots = dict()
	def __init__(self, pool):
		self.pool = pool
	def load(self, id_):
		self.id = id_
		for k, v in self.pool.pool.items():
			if v.inventory == id_:
				self.slots[k] = v
	@property
	def data(self):
		return {k: self.pool.pool[v] for k, v in self.slots.items()}