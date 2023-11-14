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
						row.append(Chunk.generate_chunk(j,i))
				result.append(merge_chunks(merge_chunks(json.loads(row[0].content), json.loads(row[1].content), True), json.loads(row[2].content), True))
		return merge_chunks(merge_chunks(result[0], result[1], False), result[2], False)

"""a = _3on3()
f = open('landscaft.json', 'w')
f.write(json.dumps(a))
f.close()"""