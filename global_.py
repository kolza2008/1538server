import proxies

state = {}
tokens = {}
wslist = []
static_entities = {}

player_pool = proxies.PlayerPool()
entities_pool = proxies.StaticEntitiesPool()

def get_players():
  return {k: v.json() for k, v in player_pool.pool.items()}

def get_static_entities():
  return {}