from sqlalchemy.future import select
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

class PlayerProxy:
	def __init__(self, model):
		self.model_link = model
	def sync_from(self):
		self.state = json.loads(self.model_link.state)
		self.appearance = json.loads(self.model_link.appearance)
	def sync_to(self):
		self.model_link.state = json.dumps(self.state)
		self.model_link.appearance = json.dumps(self.appearance)
	def json(self):
		return {
			'type': 'player',
			'id': self.model_link.id,
			'name': self.model_link.nickname,
			'appearence': self.appearance,
			'state': self.state
		}

class StaticEntityProxy:
	def __init__(self, model):
		self.model_link = model
	def sync_from(self):
		self.statedata = json.loads(self.model_link.state)
		self.appearancedata = json.loads(self.model_link.appearance)
	def sync_to(self):
		self.model_link.state = json.dumps(self.statedata)
		self.model_link.appearance = json.dumps(self.appearancedata)
	def json(self):
		return {
			'id': self.model_link.id,
			'type': self.model_link.type,
			'appearance': self.appearancedata,
			'state': self.statedata
		}

class ItemProxy:
	def __init__(self, model):
		self.model_link = model
	def sync_from(self):
		self.description = json.loads(self.model_link.description)
		self.state = json.loads(self.model_link.state)
	def sync_to(self):
		self.model_link.description = json.dumps(self.description)
		self.model_link.state = json.self.state(self.state)
	def json(self):
		return {
			"id": self.model_link.id,
			"name": self.model_link.name,
			"category": self.model_link.category,
			"description": self.description,
			"state": self.state
		}

class ItemPool:
	pool = dict()
	session = models.async_session()

	async def add_item(self, id):
		item = (await self.session.execute(select(models.Item).where(models.User.id == id))).one_or_none()[0]
		proxy = ItemProxy(item)
		proxy.sync_from()
		self.pool[id] = proxy

	async def save(self, id = None):
		if id == None:
			for i, j in self.pool.items():
				j.sync_to()
		else:
			self.pool[id].sync_to()
		self.session.commit()

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
		item = (await self.session.execute(select(models.StaticEntity).where(models.StaticEntity.id == id))).one_or_none()[0]
		proxy = StaticEntityProxy(item)
		proxy.sync_from()
		self.pool[poolid] = proxy

	async def save(self, id = None):
		for i, j in self.pool.items():
			j.sync_to()
		self.session.commit()