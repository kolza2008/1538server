import proxies

state = {}
tokens = {}
wslist = []
static_entities = {}

player_pool = proxies.PlayerPool()
sentities_pool = proxies.StaticEntitiesPool()
itempool = proxies.ItemsPool()

def get_players():
	return {k: v.json() for k, v in player_pool.pool.items()}

def get_static_entities():
	return {k: v.json() for k, v in sentities_pool.pool.items()}