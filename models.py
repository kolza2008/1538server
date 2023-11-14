from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.future import select
from noise import pnoise3 as noise
from sqlalchemy.orm import Mapped
from sqlalchemy import ForeignKey
from collections import Counter
from config import *
import asyncio
import random
import json

DATABASE_URL = "sqlite+aiosqlite:///database.db"

engine = create_async_engine(DATABASE_URL, echo=True)	#, echo=True
async_session = sessionmaker(engine,
														 class_=AsyncSession,
														 expire_on_commit=False)


def get_neighboor(map, x, y, dx, dy):
	#print(map)
	if dx < 0 and x == 0:
		return None
	if dx == 1 and x == (len(map[0]) - 1):
		return None
	if dy < 0 and y == 0:
		return None
	if dy == 1 and y == (len(map[0])) - 1:
		return None
	try:
		return map[y + dy][x + dx]
	except:
		print(
				y + dy,
				x + dx,
				dx,
		)
		raise ZeroDivisionError


class Base(AsyncAttrs, DeclarativeBase):
	pass


class Player(Base):
	__tablename__ = "players"

	id: Mapped[int] = mapped_column(primary_key=True)
	nickname: Mapped[str]
	appearance: Mapped[str]
	skills: Mapped[str]
	state: Mapped[str]
	owner: Mapped[int] = mapped_column(ForeignKey('users.id'))

	def json(self):
		return {
				'type': 'player',
				'id': self.id,
				'name': self.nickname,
				'appearence': self.proxy.appearancedata,
				'state': self.proxy.statedata
		}


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(primary_key=True)
	nickname: Mapped[str] = mapped_column(unique=True)
	password_hash: Mapped[str]
	players: Mapped[list] = relationship(Player, lazy="selectin")


class Chunk(Base):
	__tablename__ = "chunks"

	id: Mapped[int] = mapped_column(primary_key=True)
	x: Mapped[int]
	y: Mapped[int]
	content: Mapped[str]

	@staticmethod
	def generate_chunk(x, y):
		data = [[0 for i in range(16)] for j in range(16)]

		null_x = x * CELL_STEP
		null_y = y * CELL_STEP
		print([null_x, null_y])

		for y_ in range(16):
			for x_ in range(16):
				relative_x = x * 16 + x_
				relative_y = y * 16 + y_
				data[y_][x_] = int(
						noise(relative_x * CELL_STEP,
									relative_y * CELL_STEP,
									1 / PERLIN_SEED,
									octaves=16,
									persistence=0.5,
									lacunarity=6) - 0.003 < 0)

		neighboor = lambda x1, y1, dx, dy: get_neighboor(data, x1, y1, dx, dy)

		new_wave = [[0 for i in range(16)] for j in range(16)]
		for y_ in range(16):
			for x_ in range(16):
				neighboors = [
						neighboor(x_, y_, -1, -1),
						neighboor(x_, y_, 0, -1),
						neighboor(x_, y_, 1, -1),
						neighboor(x_, y_, 0, -1),
						neighboor(x_, y_, 0, 1),
						neighboor(x_, y_, 1, -1),
						neighboor(x_, y_, 1, 0),
						neighboor(x_, y_, 1, 1)
				]
				neighboor_counter = Counter(neighboors)
				if data[y_][x_] == 1:
					if neighboor_counter.get(0, 0) > 0:
						new_wave[y_][x_] = 2
						continue
				new_wave[y_][x_] = data[y_][x_]
		data = new_wave

		new_wave = [[0 for i in range(16)] for j in range(16)]
		for y_ in range(16):
			for x_ in range(16):
				neighboors = [
						neighboor(x_, y_, -1, -1),
						neighboor(x_, y_, 0, -1),
						neighboor(x_, y_, 1, -1),
						neighboor(x_, y_, 0, -1),
						neighboor(x_, y_, 0, 1),
						neighboor(x_, y_, 1, -1),
						neighboor(x_, y_, 1, 0),
						neighboor(x_, y_, 1, 1)
				]
				neighboor_counter = Counter(neighboors)
				if neighboor_counter.get(2, 0) > 4:
					if random.random() < 0.03:
						new_wave[y_][x_] = 2
						continue
				new_wave[y_][x_] = data[y_][x_]
		data = new_wave

		new_wave = [[0 for i in range(16)] for j in range(16)]
		for y_ in range(16):
			for x_ in range(16):
				neighboors = [
						neighboor(x_, y_, -1, -1),
						neighboor(x_, y_, 0, -1),
						neighboor(x_, y_, 1, -1),
						neighboor(x_, y_, 0, -1),
						neighboor(x_, y_, 0, 1),
						neighboor(x_, y_, 1, -1),
						neighboor(x_, y_, 1, 0),
						neighboor(x_, y_, 1, 1)
				]
				neighboor_counter = Counter(neighboors)
				if data[y_][x_] == 0:
					if neighboor_counter.get(2, 0) > 0:
						new_wave[y_][x_] = 3
						continue
				new_wave[y_][x_] = data[y_][x_]
		data = new_wave
		return Chunk(x=x, y=y, content=json.dumps(data))

	@staticmethod
	async def get_chunk(x, y):
		print(x, y)
		session = async_session()

		chunk = await session.execute(
				select(Chunk).where(Chunk.x == x, Chunk.y == y))
		chunk = chunk.one_or_none()

		print(chunk)

		if chunk != None:
			chunk = chunk[0]
		else:
			chunk = Chunk.generate_chunk(x, y)
			session.add(chunk)
			await session.commit()

		return chunk


class StaticEntity(Base):
	__tablename__ = "static.entities"
	id: Mapped[str] = mapped_column(primary_key=True)
	type: Mapped[str]
	appearance: Mapped[str]
	state: Mapped[str]

class Item(Base):
	__tablename__ = 'items'
	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str]
	category: Mapped[str] 
	description: Mapped[str]
	state: Mapped[str]	
	

async def start():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)