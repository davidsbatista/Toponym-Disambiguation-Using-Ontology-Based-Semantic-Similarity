##import psycopg2
import psycopg2.extensions

# Register the UNICODE typecaster globally to receive uniformly all string 
# output in python unicode objects
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

GEOPLANET = ''
GEONET = ''

_user = ''
_passwd = ''
_dbname = 
_host = ''

conn = psycopg2.connect(database=_dbname, user=_user,
                        password=_passwd, host=_host)
cur = conn.cursor()

def get_parents(geonet_id):
  cur.execute('''
    SELECT f_id1
    FROM adm_feature_relationship
    WHERE f_id2 = %s AND
          frt_id = 'PRT'
  ''', (geonet_id,))
  
  return [i[0] for i in cur]

  
def get_ancestry(geonet_id):
  ancestry = set()
  todo = [geonet_id]
  while todo:
    current = todo.pop(0)
    yield current
    
    for parent in get_parents(current):
      if parent in ancestry:
        continue
      todo.append(parent)
      ancestry.add(parent)


def get_type(geonet_id):
  cur.execute('''
    SELECT t_id
    FROM adm_feature
    WHERE f_id = %s
  ''', (geonet_id,))
  row = cur.fetchone()
  if row:
    return row[0]
  else:
    return None


def get_first_municipality(ids_iterator):
  for geonet_id in ids_iterator:
    type_id = get_type(geonet_id)
    if type_id == "CON":
      return geonet_id
  
  return None


def get_name(geonet_id):
  cur.execute('''
    SELECT n_cap_name
    FROM adm_name
    JOIN adm_feature ON adm_feature.n_id = adm_name.n_id
    WHERE f_id = %s
  ''', (geonet_id,))
  
  row = cur.fetchone()
  if row:
    return row[0]
  else:
    return None


def get_municipality_name(geonet_id, _cache={}):
  if geonet_id in _cache:
    return _cache[geonet_id]
  
  ancestry_iterator = get_ancestry(geonet_id)
  municipality = get_first_municipality(ancestry_iterator)
  name = get_name(municipality)
  
  _cache[geonet_id] = name
  return name


def find_by_name(name, _cache={}):
  if name in _cache:
    return _cache[name]
  
  cur.execute('''
    SELECT f_id, t_id
    FROM adm_feature
    JOIN adm_name ON adm_name.n_id = adm_feature.n_id
    WHERE n_cap_name = %s
  ''', (name,))
  
  result = list(cur)
  _cache[name] = result
  return result


