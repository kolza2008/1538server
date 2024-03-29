from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy import ForeignKey
from config import *
import asyncio


engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
		engine, class_=AsyncSession, expire_on_commit=False
)


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

class StaticEntity(Base):
	__tablename__ = "staticentities"
	id: Mapped[int] = mapped_column(primary_key=True)	 
	type: Mapped[str] 
	name: Mapped[str] 
	state: Mapped[str]
	category: Mapped[str]

class Slot(Base):
	__tablename__ = 'slots'
	id: Mapped[str] = mapped_column(primary_key=True)
	inventory: Mapped[str]
	item: Mapped[int] = mapped_column(ForeignKey('items.id'))
	criteria: Mapped[str]

class Item(Base):
	__tablename__ = 'items'
	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str]
	description: Mapped[str]
	state: Mapped[str]
	category: Mapped[str]
	

async def start():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
