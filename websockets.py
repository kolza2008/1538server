from sqlalchemy.future import select
from aiohttp import web, WSMsgType
from generate import *
from global_ import *
import json, uuid
import asyncio
import models


async def broadcast_user(ws, id_):
	try:
		while True:
			await ws.send_str("." + json.dumps({**get_players(), **get_static_entities()}))
			await asyncio.sleep(1 / 10)
	except ConnectionResetError:
		print('ws connection closed with id:	%s' % id_)
		await player_pool.save(id_)
		player_pool.pool.pop(id_)


async def my_first_websocket_route(request):
	ws = web.WebSocketResponse()
	await ws.prepare(request)

	token = request.rel_url.query['token']

	session = models.async_session()

	if not token in tokens.keys():
		await ws.send_str('!404')	#пользователя с таким id не существует
		await ws.close()
		return

	user_id = tokens[token]
	user = (await session.execute(select(models.User).where(models.User.id == user_id))).one_or_none()[0]
	if user is None:
		await ws.send_str('!404')	#пользователя с таким id не существует
		await ws.close()
		return

	if len(user.players) == 0:
		await ws.send_str('|404')	#у данного пользователя нет ни одного аватара
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
	else:
		player = user.players[0]

	id_ = uuid.uuid4().hex
	
	await player_pool.add_item(player.id, id_)
	player = player_pool.pool[id_]

	wslist.append(ws)

	print('hih')
	
	state.update({id_: player})

	await ws.send_str(f'#{id_}')

	loop = asyncio.get_event_loop()
	loop.create_task(broadcast_user(ws, id_))

	obj = state[id_]

	async for msg in ws:
		if msg.type == WSMsgType.TEXT:
			if msg.data[0] == "@":
				obj.state['position'][0] += int(msg.data[1:].split('.')[0])
				obj.state['position'][1] += int(msg.data[1:].split('.')[1])
				obj.state['position'][0] = max(0, obj.state['position'][0])
				obj.state['position'][1] = max(0, obj.state['position'][1])
			elif msg.data[0] == "?":
				msgtype = msg.data[1:].split('.')[0]
				if msgtype == "chunk":
					coords = [
							int(msg.data[1:].split('.')[1]),
							int(msg.data[1:].split('.')[2])
					]
					chunk = await get_chunk(coords[0], coords[1])
					await ws.send_str(f'${coords[0]}.{coords[1]}|{chunk.content}')
		elif msg.type == WSMsgType.ERROR:
			print('ws connection closed with exception %s' % ws.exception())
			state.pop(id_)
			break