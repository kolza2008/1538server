from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from generate import generate_chunk
from aiohttp import web, WSMsgType
import aiohttp_cors
import asyncio
import hashlib
import secrets
import models
import uuid
import json

state = {}
tokens = {}
wslist = []
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


async def my_first_websocket_route(request):
  ws = web.WebSocketResponse()
  await ws.prepare(request)

  token = request.rel_url.query['token']

  session = models.async_session()

  if not token in tokens.keys():
    await ws.send_str('!404')  #пользователя с таким id не существует
    await ws.close()
    return

  user_id = tokens[token]
  user = (await session.execute(
      select(models.User).where(models.User.id == user_id))).one_or_none()[0]
  if user is None:
    await ws.send_str('!404')  #пользователя с таким id не существует
    await ws.close()
    return

  if len(user.players) == 0:
    await ws.send_str('|404')  #у данного пользователя нет ни одного аватара
    persona = await ws.receive_str()
    persona = persona.replace("'", '"')
    persona = json.loads(persona)
    """
        if list(persona.keys()) == ['']:
            pass
        """
    print(persona)
    player = models.Player(owner=user_id,
                           nickname=persona['nickname'],
                           appearance=str(persona['appearance']),
                           state='{"position": [0, 0], "health": 100}',
                           skills=str(persona['skills']))
    session.add(player)
    await session.commit()
    print(player)
  else:
    player = user.players[0]

  print(player)

  wslist.append(ws)

  print('hih')

  id_ = uuid.uuid4().hex
  state.update({id_: player})

  await ws.send_str(f'#{id_}')

  loop = asyncio.get_event_loop()
  loop.create_task(broadcast_user(ws))

  async for msg in ws:
    if msg.type == WSMsgType.TEXT:
      if msg.data[0] == "@":
        data = json.loads(state[id_].state)
        data['position'][0] += int(msg.data[1:].split('.')[0])
        data['position'][1] += int(msg.data[1:].split('.')[1])
      elif msg.data[0] == "?":
        msgtype = msg.data[1:].split('.')[0]
        if msgtype == "chunk":
          coords = [int(msg.data[1:].split('.')[1]), int(msg.data[1:].split('.')[2])]
          chunk = models.Chunk.get_chunk(coords[0], coords[1])
          await ws.send_message(f'${coords[0]}.{coords[1]}|{chunk.content}')

      state[id_].state = json.dumps(data)
    elif msg.type == WSMsgType.ERROR:
      print('ws connection closed with exception %s' % ws.exception())
      state.pop(id_)
      break


async def broadcast_user(ws):
  while True:
    await ws.send_str(
          "." + json.dumps({
            k: {
                'id': v.id,
                'name': v.nickname,
                'appearence': json.loads(v.appearance),
                'state': json.loads(v.state)
            }
            for k, v in state.items()
        }))
    await asyncio.sleep(1 / 10)


async def create_user(request):
  payload = await request.json()

  try:
    user = models.User(nickname=payload.get('login'),
                       password_hash=hashlib.md5(
                           payload.get('password').encode('utf8')).hexdigest())

    session = models.async_session()
    session.add(user)
    await session.commit()
  except IntegrityError:
    raise web.HTTPConflict()

  return web.json_response({"user_id": user.id})


async def get_token(request):
  payload = await request.json()

  login = payload.get('login')
  password = payload.get('password')

  if any([i == None for i in [login, password]]):
    raise web.HTTPBadRequest(reason="one from fields is none")

  session = models.async_session()

  user = (await session.execute(
      select(models.User).where(models.User.nickname == login)
  )).one_or_none()[0]
  if user == None:
    raise web.HTTPBadRequest("user's name is not found")
  if user.password_hash != hashlib.md5(password.encode('utf8')).hexdigest():
    raise web.HTTPBadRequest("wrong password")

  token = secrets.token_urlsafe()
  tokens.update({token: user.id})

  print(tokens)

  return web.json_response({"token": token})


async def chunk_update():
  session = models.async_session()

  chunks = (await session.execute(select(models.Chunk))).all()
  print(chunks)
  if len(chunks) == 0:
    session.add(generate_chunk(0, 0))
    await session.commit()


app = web.Application()
cors = aiohttp_cors.setup(app,
                          defaults={
                              "*":
                              aiohttp_cors.ResourceOptions(
                                  allow_credentials=True,
                                  expose_headers="*",
                                  allow_headers="*")
                          })

app.router.add_get('/ws', my_first_websocket_route)
app.router.add_post('/api/user/new', create_user)
app.router.add_post('/api/user', get_token)

for route in list(app.router.routes()):
  cors.add(route)

asyncio.run(models.start())
asyncio.run(chunk_update())
web.run_app(app, host='0.0.0.0')