import re
import unicodedata

YEAR = 2022
CURR_WEEK = 19
curr_week = CURR_WEEK

TEAM_TRANS = {
	"rav": "bal",
	"htx": "hou",
	"oti": "ten",
	"sdg": "lac",
	"ram": "lar",
	"clt": "ind",
	"crd": "ari",
	"gnb": "gb",
	"kan": "kc",
	"nwe": "ne",
	"rai": "lv",
	"sfo": "sf",
	"tam": "tb",
	"nor": "no"
}

SORTED_TEAMS = ['ari', 'atl', 'bal', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'hou', 'ind', 'jax', 'kan', 'lac', 'lar', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'ten', 'was']

SNAP_LINKS = ["ari", "atl", "bal", "buf", "car", "chi", "cin", "cle", "dal", "den", "det", "gb", "hou", "ind", "jax", "kc", "lac", "lar", "lv", "mia", "min", "no", "ne", "nyg", "nyj", "phi", "pit", "sea", "sf", "tb", "ten", "was"]

afc_teams = ['rav', 'buf', 'cin', 'cle', 'den', 'htx', 'clt', 'jax', 'kan', 'sdg', 'rai', 'mia', 'nwe', 'nyj', 'pit', 'ten']
nfc_teams = ['crd', 'atl', 'car', 'chi', 'dal', 'det', 'gnb', 'ram', 'min', 'nor', 'nyg', 'phi', 'sea', 'sfo', 'tam', 'was']

def fixName(name):
	name = name.lower().replace("'", "").strip()
	name = re.sub(r" (v|iv|iii|ii|jr|sr)(\.?)$", " ", name).replace(".", "").strip()

	if name == "elijah mitchell":
		return "eli mitchell"
	elif name == "ken walker":
		return "kenneth walker"
	elif name == "mike badgley":
		return "michael badgley"
	elif name == "pat surtain":
		return "patrick surtain"
	elif name == "green bay packers":
		return "gnb"
	elif name == "las vegas raiders":
		return "rai"
	elif name == "new england patriots":
		return "nwe"
	elif name == "seattle seahawks":
		return "sea"
	elif name == "chicago bears":
		return "chi"
	elif name == "carolina panthers":
		return "car"
	elif name == "arizona cardinals":
		return "crd"
	elif name == "indianapolis colts":
		return "clt"
	elif name == "denver broncos":
		return "den"
	elif name == "tampa bay buccaneers":
		return "tam"
	elif name == "atlanta falcons":
		return "atl"
	elif name == "miami dolphins":
		return "mia"
	elif name == "philadelphia eagles":
		return "phi"
	elif name == "jacksonville jaguars":
		return "jax"
	elif name == "baltimore ravens":
		return "rav"
	elif name == "pittsburgh steelers":
		return "pit"
	elif name == "houston texans":
		return "htx"
	elif name == "kansas city chiefs":
		return "kan"
	elif name == "los angeles rams":
		return "ram"
	elif name == "washington commanders":
		return "was"
	elif name == "new york giants":
		return "nyg"
	elif name == "san francisco 49ers":
		return "sfo"
	elif name == "cincinnati bengals":
		return "cin"
	elif name == "tennessee titans":
		return "oti"
	elif name == "minnesota vikings":
		return "min"
	elif name == "los angeles chargers":
		return "sdg"
	elif name == "new york jets":
		return "nyj"
	elif name == "buffalo bills":
		return "buf"
	elif name == "detroit lions":
		return "det"
	elif name == "new orleans saints":
		return "nor"
	elif name == "cleveland browns":
		return "cle"
	elif name == "dallas cowboys":
		return "dal"
	elif name == "off":
		return "OFF"
	elif name == "def":
		return "DEF"
	return name

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

def convertCollege(team):
	return college.get(team, team)