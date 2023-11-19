from sqlalchemy.future import select
from noise import pnoise3 as noise
from collections import Counter
from config import *
from models import * 
import random
import json

def get_neighboor(map, x, y, dx, dy):
	#print(map)
	if dx < 0 and x == 0:
		return None
	if dx == 1 and x == (len(map[0])-1):
		return None
	if dy < 0 and y == 0:
		return None
	if dy == 1 and y == (len(map[0]))-1:
		return None
	try:
		return map[y+dy][x+dx]
	except:
		print(y+dy, x+dx, dx,)
		raise ZeroDivisionError

def generate_chunk(x, y):
	data = [[0 for i in range(16)] for j in range(16)]

	null_x = x*CELL_STEP
	null_y = y*CELL_STEP
	print([null_x, null_y])

	for y_ in range(16):
		for x_ in range(16):
			relative_x = x*16 + x_
			relative_y = y*16 + y_
			data[y_][x_] = int(noise(relative_x*CELL_STEP, relative_y*CELL_STEP, 1/PERLIN_SEED, octaves=16, persistence=0.5, lacunarity=6)-0.003 < 0)

	neighboor = lambda x1,y1,dx,dy: get_neighboor(data, x1, y1, dx, dy)

	new_wave = [[0 for i in range(16)] for j in range(16)]
	for y_ in range(16):
		for x_ in range(16):
			neighboors = [neighboor(x_,y_,-1,-1), neighboor(x_,y_,0,-1), neighboor(x_,y_,1,-1),
							neighboor(x_,y_,0,-1),						 neighboor(x_,y_,0,1), 
							neighboor(x_,y_,1,-1),	neighboor(x_,y_,1,0),	neighboor(x_,y_,1,1)]
			neighboor_counter = Counter(neighboors)
			if data[y_][x_] == 1:
				if neighboor_counter.get(0,0)>0:
					new_wave[y_][x_] = 2
					continue
			new_wave[y_][x_] = data[y_][x_]
	data = new_wave

	new_wave = [[0 for i in range(16)] for j in range(16)]
	for y_ in range(16):
		for x_ in range(16):
			neighboors = [neighboor(x_,y_,-1,-1), neighboor(x_,y_,0,-1), neighboor(x_,y_,1,-1),
							neighboor(x_,y_,0,-1),						 neighboor(x_,y_,0,1), 
							neighboor(x_,y_,1,-1),	neighboor(x_,y_,1,0),	neighboor(x_,y_,1,1)]
			neighboor_counter = Counter(neighboors)
			if neighboor_counter.get(2,0)>4:
				if random.random() <0.03:
					new_wave[y_][x_] = 2
					continue
			new_wave[y_][x_] = data[y_][x_]
	data = new_wave

	new_wave = [[0 for i in range(16)] for j in range(16)]
	for y_ in range(16):
		for x_ in range(16):
			neighboors = [neighboor(x_,y_,-1,-1), neighboor(x_,y_,0,-1), neighboor(x_,y_,1,-1),
							neighboor(x_,y_,0,-1),						 neighboor(x_,y_,0,1), 
							neighboor(x_,y_,1,-1),	neighboor(x_,y_,1,0),	neighboor(x_,y_,1,1)]
			neighboor_counter = Counter(neighboors)
			if data[y_][x_] == 0:
				if neighboor_counter.get(2,0) > 0:
					new_wave[y_][x_] = 3
					continue
			new_wave[y_][x_] = data[y_][x_]
	data = new_wave
	return Chunk(x=x, y=y, content=json.dumps(data))

def merge_chunks(c1, c2, horizontal):
	result = []
	if horizontal:
		for i in range(len(c1)):
			result.append([*c1[i], *c2[i]])
	else:
		result = [*c1, *c2]
	return result

def _3on3():
	result = []
	for i in range(3):
		row = []
		for j in range(3):
			row.append(generate_chunk(j,i))
		result.append(merge_chunks(merge_chunks(json.loads(row[0].content), json.loads(row[1].content), True), json.loads(row[2].content), True))
	return merge_chunks(merge_chunks(result[0], result[1], False), result[2], False)

chunksession = async_session()
chunkspool = {}

async def get_chunk(x, y):
	if (x, y) in chunkspool.keys():
		return chunkspool[(x, y)]
	chunks = (await chunksession.execute(select(Chunk).where(Chunk.x == x and Chunk.y == y))).one_or_none()
	if chunks != None:
		chunkspool[(x, y)] = chunks[0]
		return chunks[0]
	chunk = generate_chunk(x, y)
	chunksession.add(chunk)
	await chunksession.commit()
	chunkspool[(x, y)] = chunk
	return chunk