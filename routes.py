from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from aiohttp import web
from global_ import *
import hashlib
import secrets
import models


async def create_user(request):
  payload = await request.json()
  try:
    user = models.User(nickname=payload.get('login'), password_hash=hashlib.md5(payload.get('password').encode('utf8')).hexdigest())
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

  user = (await session.execute(select(models.User).where(models.User.nickname == login))).one_or_none()[0]
  if user == None:
    raise web.HTTPBadRequest("user's name is not found")
  if user.password_hash != hashlib.md5(password.encode('utf8')).hexdigest():
    raise web.HTTPBadRequest("wrong password")

  token = secrets.token_urlsafe()
  tokens.update({token: user.id})

  print(tokens)

  return web.json_response({"token": token})