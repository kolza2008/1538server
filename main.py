from sqlalchemy.future import select
from generate import generate_chunk
from aiohttp import web
import aiohttp_cors
import asyncio
import models

"""
Что значат первые символы сообщений:
    # - данные от серва, не связанные с стейтом игры
    ! - ошибка, за которой последует закрытие сокета
    | - ошибка, которая должна быть исправлена клиентом
    $ - подгрузка статичной инфы
    . - стейт игры
    ? - запрос статики
    @ - запрос на изменение стейта
"""

from websockets import *
from routes import *


async def preload():
  global static_entities
  session = models.async_session()

  chunks = (await session.execute(select(models.Chunk))).all()
  print(chunks)
  if len(chunks) == 0:
    session.add(generate_chunk(0, 0))
    await session.commit()

  """sentities = (await session.execute(select(models.Chunk))).all()
  for i in sentities:
    i.load()
    static_entities.update({f"stent#{i.id}": i})"""

app = web.Application()
cors = aiohttp_cors.setup(app, defaults = {
  "*" : aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")
})

app.router.add_get('/ws', my_first_websocket_route)
app.router.add_post('/api/user/new', create_user)
app.router.add_post('/api/user', get_token)

for route in list(app.router.routes()):
  cors.add(route)

asyncio.run(models.start())
asyncio.run(preload())
web.run_app(app, host='0.0.0.0')