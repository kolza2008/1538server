from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.future import select
from generate import generate_chunk
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

	@staticmethod
	async def get_chunk(x, y):
		session = async_session()
		chunks = (await session.execute(select(Chunk).where(Chunk.x == x and Chunk.y == y))).one_or_none()
		if chunks != None:
			return chunks[0]
		chunk = generate_chunk(x, y)
		session.add(chunk)
		await session.commit()
		session.close()
		return chunk

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
