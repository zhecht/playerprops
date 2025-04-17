from collections import defaultdict
import nodriver as uc
import unicodedata
import git
import json
import numpy as np
import os
from datetime import datetime

def commitChanges():
	repo = git.Repo(".")
	repo.git.add(A=True)
	repo.index.commit("test")

	origin = repo.remote(name="origin")
	origin.push()
	#print("Successful commit")

def getSuffix(num):
	if num >= 11 and num <= 13:
		return "th"
	elif num % 10 == 1:
		return "st"
	elif num % 10 == 2:
		return "nd"
	elif num % 10 == 3:
		return "rd"
	return "th"

def linearRegression(x, y):
	n = len(x)
	sum_x = np.sum(x)
	sum_y = np.sum(y)
	sum_xy = np.sum(np.multiply(x, y))
	sum_xx = np.sum(np.square(x))

	slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
	intercept = (sum_y - slope * sum_x) / n

	predicted_y = [slope * xi + intercept for xi in x]

	return {"slope": slope, "intercept": intercept, "predicted_y": predicted_y}

# Write open/closing line values
def writeHistorical(date, book, gameStarted=None):
	book = book.replace("365", "b365")
	if not gameStarted:
		with open("static/mlb/schedule.json") as fh:
			schedule = json.load(fh)
		gameStarted = {}
		for gameData in schedule[date]:
			if gameData["start"] == "LIVE":
				gameStarted[gameData["game"]] = True
			else:
				dt = datetime.strptime(gameData["start"], "%I:%M %p")
				dt = int(dt.strftime("%H%M"))
				gameStarted[gameData["game"]] = int(datetime.now().strftime("%H%M")) > dt
	hist = {}
	with open(f"static/dingers/{book}.json") as fh:
		lines = json.load(fh)
	if os.path.exists(f"static/dingers/{book}_historical.json"):
		with open(f"static/dingers/{book}_historical.json") as fh:
			hist = json.load(fh)
	hist.setdefault(date, {})
	for game in lines:
		if gameStarted.get(game, True):
			continue
		for player in lines[game]:
			hist[date].setdefault(game, {})
			hist[date][game].setdefault(player, {})
			hist[date][game][player]["close"] = lines[game][player]["fd"]
			if "open" not in hist[date][game][player]:
				hist[date][game][player]["open"] = lines[game][player]["fd"]
	with open(f"static/dingers/{book}_historical.json", "w") as fh:
		json.dump(hist, fh)

async def writeCZToken():
	url = f"https://sportsbook.caesars.com/us/mi/bet/"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)
	await page.wait_for(selector=".eventContainer")
	cookies = await browser.cookies.get_all()
	for cookie in cookies:
		if cookie.name == "aws-waf-token":
			with open("token", "w") as fh:
				fh.write(cookie.value)
			break
	browser.stop()

def nested_dict():
	return defaultdict(nested_dict)

def convert_to_dict(d):
	if isinstance(d, defaultdict):
		d = {k: convert_to_dict(v) for k,v in d.items()}
	return d

def merge_dicts(d1, d2, forceReplace=False):
	for k,v in d2.items():
		#print(k,k in d1,d1.get(k, None) is dict, v is dict)
		if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
			merge_dicts(d1[k], v, forceReplace)
		elif k in d1 and isinstance(v, str):
			if "/" in d1[k]:
				if len(d1[k].split("/")) != 2:
					continue
				o,u = map(int, d1[k].split("/"))
			else:
				o,u = d1[k],""

			if forceReplace:
				o = int(v.split("/")[0])
			else:
				o = max(int(o), int(v.split("/")[0]))

			if "/" in v:
				if "/" in str(u) and not forceReplace:
					u = max(int(u.split("/")[-1]), int(v.split("/")[-1]))
				else:
					u = v.split("/")[-1]
			if u:
				d1[k] = f"{o}/{u}"
			else:
				d1[k] = str(o)
		else:
			d1[k] = v

def convertAmericanOdds(avg):
	if avg >= 2:
		avg = (avg - 1) * 100
	else:
		avg = -100 / (avg - 1)
	return round(avg)

def convertDecOdds(odds):
	if odds == 0:
		return 0
	if odds > 0:
		decOdds = 1 + (odds / 100)
	else:
		decOdds = 1 - (100 / odds)
	return decOdds
	
def convertImpOdds(odds):
	if odds == 0:
		return 0
	if odds > 0:
		impOdds = 100 / (odds+100)
	else:
		impOdds = -odds / (-odds+100)
	return impOdds

def convertAmericanFromImplied(odds):
	if odds == 0:
		return 0
	if odds >= 0.5:
		odds = -(odds / (1 - odds)) * 100
	else:
		odds = ((1 - odds) / odds) * 100
	return round(odds)

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3
		pass
	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
	return str(text)


def shortName(player):
	if player == "kerry carpenter":
		return "K Carpenter"
	return player.split(" ")[-1].title()

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "")
	player = player.split(" (")[0]

	if player.endswith(" iv"):
		player = player[:-3]
	if player == "jadeney":
		return "jaden ivey"
	elif player == "ivanan":
		return "ivan ivan"
	elif player.startswith("sebastian aho"):
		return "sebastian aho"
	elif player == "alex sarr":
		return "alexandre sarr"
	elif player == "nicolas claxton":
		return "nic claxton"
	elif player == "marc casado torras":
		return "marc casado"
	elif player == "jay dasilva":
		return "jay da silva"
	# NHL
	elif player == "matthew boldy":
		return "matt boldy"
	elif player == "cameron atkinson":
		return "cam atkinson"
	elif player == "nick paul":
		return "nicholas paul"
	elif player == "mitchell marner":
		return "mitch marner"
	elif player == "mikey eyssimont":
		return "michael eyssimont"
	elif player == "john jason peterka":
		return "jj peterka"
	elif player == "alexander nylander":
		return "alex nylander"
	# MLB
	elif player == "kike hernandez" or player == "e hernandez":
		return "enrique hernandez"
	elif player == "brandon nimno":
		return "brandon nimmo"
	elif player == "c encarnacion strand":
		return "christian encarnacion strand"

	return player

def convertMLBTeam(team):
	team = team.lower().replace(".", "")
	t = team.replace(" ", "")[:3]
	if "cubs" in team:
		return "chc"
	elif t == "chi":
		return "chw"
	elif t in ["kan", "kcr"]:
		return "kc"
	elif "dodgers" in team:
		return "lad"
	elif t == "los":
		return "laa"
	elif t == "new":
		if "yankees" in team:
			return "nyy"
		return "nym"
	elif t == "ath" or t == "the":
		return "ath"
	elif t == "was":
		return "wsh"
	elif t == "sdp":
		return "sd"
	elif t == "sfg":
		return "sf"
	elif t == "san":
		if "padres" in team:
			return "sd"
		return "sf"
	elif t in ["tam", "tbr"]:
		return "tb"

	if t == "oak":
		return "ath"
	return t

def convertMGMTeam(team):
	if team == "diamondbacks":
		return "ari"
	elif team == "braves":
		return "atl"
	elif team == "orioles":
		return "bal"
	elif team.replace(" ", "") == "redsox":
		return "bos"
	elif team == "cubs":
		return "chc"
	elif team.replace(" ", "") == "whitesox":
		return "chw"
	elif team == "reds":
		return "cin"
	elif team == "guardians":
		return "cle"
	elif team == "rockies":
		return "col"
	elif team == "tigers":
		return "det"
	elif team == "astros":
		return "hou"
	elif team == "royals":
		return "kc"
	elif team == "angels":
		return "laa"
	elif team == "dodgers":
		return "lad"
	elif team == "marlins":
		return "mia"
	elif team == "brewers":
		return "mil"
	elif team == "twins":
		return "min"
	elif team == "mets":
		return "nym"
	elif team == "yankees":
		return "nyy"
	elif team == "athletics":
		return "ath"
	elif team == "phillies":
		return "phi"
	elif team == "pirates":
		return "pit"
	elif team == "padres":
		return "sd"
	elif team == "giants":
		return "sf"
	elif team == "mariners":
		return "sea"
	elif team == "cardinals":
		return "stl"
	elif team == "rays":
		return "tb"
	elif team == "rangers":
		return "tex"
	elif team.replace(" ", "") == "bluejays":
		return "tor"
	elif team == "nationals":
		return "wsh"
	return team

def convertSavantLogoId(logoId):
	if logoId == "120":
		return "wsh"
	elif logoId == "141":
		return "tor"
	elif logoId == "140":
		return "tex"
	elif logoId == "139":
		return "tb"
	elif logoId == "138":
		return "stl"
	elif logoId == "137":
		return "sf"
	elif logoId == "136":
		return "sea"
	elif logoId == "135":
		return "sd"
	elif logoId == "134":
		return "pit"
	elif logoId == "143":
		return "phi"
	elif logoId == "133":
		return "ath"
	elif logoId == "147":
		return "nyy"
	elif logoId == "121":
		return "nym"
	elif logoId == "142":
		return "min"
	elif logoId == "158":
		return "mil"
	elif logoId == "146":
		return "mia"
	elif logoId == "119":
		return "lad"
	elif logoId == "108":
		return "laa"
	elif logoId == "118":
		return "kc"
	elif logoId == "117":
		return "hou"
	elif logoId == "116":
		return "det"
	elif logoId == "145":
		return "chw"
	elif logoId == "115":
		return "col"
	elif logoId == "114":
		return "cle"
	elif logoId == "113":
		return "cin"
	elif logoId == "112":
		return "chc"
	elif logoId == "111":
		return "bos"
	elif logoId == "110":
		return "bal"
	elif logoId == "109":
		return "ari"
	elif logoId == "144":
		return "atl"

def convertNHLTeam(team):
	team = team.lower()
	t = team[:3].strip()
	if t == "was":
		return "wsh"
	elif t == "cal":
		return "cgy"
	elif t in ["co!", "ct"]:
		return "col"
	elif (t == "col" and "columbus" in team) or t == "clb":
		return "cbj"
	elif t == "flo":
		return "fla"
	elif t == "pht":
		return "phi"
	elif t == "cht":
		return "chi"
	elif t == "los":
		return "la"
	elif t == "nas":
		return "nsh"
	elif t == "mon":
		return "mtl"
	elif t == "nyt":
		return "nyi"
	elif t == "new" or t == "ny":
		if "rangers" in team:
			return "nyr"
		elif "island" in team:
			return "nyi"
		return "nj"
	elif t == "san":
		return "sj"
	elif t == "tam":
		return "tb"
	elif t == "st.":
		return "stl"
	elif t in ["veg", "vgk", "vgi"]:
		return "vgk"
	elif t == "win":
		return "wpg"
	elif t == "uta":
		return "utah"
	return t

def convertSoccer(team):
	team = team.lower().replace("-", " ").replace(".", "").replace("/", " ").replace("'", "")
	team = team.replace("munchen", "munich").replace(" utd", " united").replace(" city", "").replace(" town", "").replace(" county", "").replace(" rovers", "")
	team = strip_accents(team)

	if len(team) > 2:
		if (team[2] == " " and team[:2] in ["ac", "ad", "as", "bb", "ca", "cd", "cf", "cs", "fc", "fk", "kv", "ld", "nk", "rb", "rc", "sc", "sd", "sk", "sm", "ss", "sv", "uc", "us", "vv"]) or team[:3] in ["aep", "afc", "bvv", "csm", "fcv", "fsv", "pfk", "ogc", "scr", "ssc", "ssd", "ssv", "stv", "tsc", "tsg", "tsv", "usl", "vfb", "vfl"]:
			team = team[3:].strip()
	if len(team) > 2:
		if (team[-3] == " " and team[-2:] in ["ac", "cf", "fc", "eh", "ff", "fk", "if", "ik", "rc", "sc", "sk", "sv", "tc", "vv"]) or team[-3:] in ["afc", "cfc", "pfk"]:
			team = team[:-3].strip()

	j = {
		"1 fc nuremberg": "nuremberg",
		"accrington stanley": "accrington",
		"ael limassol": "ael",
		"amsterdamsche": "amsterdam",
		"royal antwerp": "antwerp",
		"anorthosis famagusta": "anorthosis",
		"apoel nicosia": "apoel",
		"araz naxcivan": "araz nakhchivan",
		"arg juniors": "argentinos juniors",
		"aris fc limassol": "aris limassol",
		"aris": "aris thessaloniki",
		"atl tucuman": "atletico tucuman",
		"atletico nacional medellin": "atletico nacional",
		"a klagenfurt": "austria klagenfurt",
		"avs": "avs futebol sad",
		"avs futebol": "avs futebol sad",
		"az": "az alkmaar",
		"balzan youths": "balzan",
		"istanbul basaksehir": "basaksehir",
		"ist basaksehir": "basaksehir",
		"k beerschot va": "beerschot",
		"kfco beerschot wilrijk": "beerschot",
		"real betis": "betis",
		"bodrum belediyesi bodrumspor": "bodrumspor",
		"bolton wanderers": "bolton",
		"borac banja": "borac banja luka",
		"borussia mgladbach": "monchengladbach",
		"ballymena": "ballymena united",
		"stade brest": "brest",
		"brighton & hove albion": "brighton",
		"brighton and hove albion": "brighton",
		"briton ferry llansawel": "briton ferry",
		"burton albion": "burton",
		"cambuur leeuwarden": "cambuur",
		"carlisle united": "carlisle",
		"catanzaro 1929": "catanzaro",
		"cc mariners": "central coast mariners",
		"central cordoba (sde)": "central cordoba",
		"central cordoba sde": "central cordoba",
		"dynamo ceske budejovice": "ceske budejovice",
		"cfr 1907 cluj": "cfr cluj",
		"sporting de charleroi": "charleroi",
		"royal charleroi": "charleroi",
		"charlton athletic": "charlton",
		"cercle": "cercle brugge",
		"cf america": "club america",
		"clermont foot": "clermont",
		"club america mexico": "club america",
		"club aurora cochabamba": "club aurora",
		"colchester united": "colchester",
		"nuova cosenza": "cosenza",
		"crewe alexandra": "crewe",
		"crusaders belfast": "crusaders",
		"csd coban imperial": "coban imperial",
		"cukaricki belgrade": "cukaricki",
		"darmstadt 98": "darmstadt",
		"dender eh": "dender",
		"deportivo": "deportivo la coruna",
		"dep la coruna": "deportivo la coruna",
		"borussia dortmund": "dortmund",
		"dungannon swifts": "dungannon",
		"djurgardens": "djurgarden",
		"dynamo kyiv": "dynamo kiev",
		"07 elversberg": "elversberg",
		"enosis neon": "enosis neon paralimni",
		"ein braunschweig": "braunschweig",
		"es thaon": "thaon",
		"espanyol barcelona": "espanyol",
		"estoril praia": "estoril",
		"estudiantes de la plata": "estudiantes",
		"estrela da amadora": "estrela",
		"estrela amadora": "estrela",
		"club football estrela": "estrela",
		"excelsior rotterdam": "rotterdam",
		"ferencvarosi": "ferencvaros",
		"frankfurt": "eintracht frankfurt",
		"r santander": "racing santander",
		"racing de ferrol": "ferrol",
		"racing club de ferrol": "ferrol",
		"sittard": "fortuna sittard",
		"dusseldorf": "fortuna dusseldorf",
		"sporting gijon": "gijon",
		"buzau": "gloria buzau",
		"furth": "greuther furth",
		"gimnasia la plata": "gimnasia",
		"gimnasia y esgrima": "gimnasia",
		"glentoran belfast": "glentoran",
		"goztepe izmir": "goztepe",
		"lamontville golden arrows": "golden arrows",
		"vitoria guimaraes": "guimaraes",
		"grenoble foot": "grenoble",
		"gzira united": "gzira",
		"almelo": "heracles",
		"kiel": "holstein kiel",
		"hnk hajduk split": "hajduk split",
		"hnk sibenik": "sibenik",
		"hnk rijeka": "rijeka",
		"imt novi beograd": "imt",
		"novi belgrade": "imt",
		"independiente avellaneda": "independiente",
		"independiente (ecu)": "independiente del valle",
		"instituto ac cordoba": "instituto",
		"inter milan": "inter",
		"internazionale": "inter",
		"istra": "istra 1961",
		"jagiellonia": "jagiellonia bialystock",
		"regensburg": "jahn regensburg",
		"club jorge wilstermann": "jorge wilstermann",
		"kapaz ganja": "kapaz",
		"karmiotissa polemidion": "karmiotissa",
		"karlsruhe": "karlsruher",
		"atletico lanus": "lanus",
		"lask": "lask linz",
		"ldu quito": "ldu",
		"le puy foot 43 auvergne": "le puy",
		"rb leipzig": "leipzig",
		"bayer leverkusen": "leverkusen",
		"leeds united": "leeds",
		"legia warszawa": "legia warsaw",
		"oh leuven": "leuven",
		"oud heverlee leuven": "leuven",
		"oud heverlee": "leuven",
		"lille osc": "lille",
		"lok zagreb": "lokomotiva",
		"lokomotiva zagreb": "lokomotiva",
		"ludogorets razgrad": "ludogorets",
		"mainz": "mainz 05",
		"1 fsv mainz 05": "mainz 05",
		"manchester": "man",
		"man united": "manchester united",
		"mantova 1911": "mantova",
		"yellow red mechelen": "mechelen",
		"m petah tikva": "maccabi petach tikva",
		"maccabi bnei raina": "maccabi bnei reineh",
		"mac bney reine": "maccabi bnei reineh",
		"maccabi bnei reina": "maccabi bnei reineh",
		"monza brianza": "monza",
		"mgladbach": "monchengladbach",
		"napredak krusevac": "napredak",
		"newcastle united": "newcastle",
		"nijmegen": "nec nijmegen",
		"n salamina famagusta": "nea salamis",
		"nec": "nec nijmegen",
		"noah yerevan": "noah",
		"nottm forest": "nottingham forest",
		"notts county": "notts",
		"notts co": "notts",
		"olimpija ljubljana": "olimpija",
		"olympiacos": "olympiakos",
		"omonia nicosia": "omonia",
		"omonia fc aradippou": "omonia aradippou",
		"als omonia": "omonia",
		"omonia 29 may": "omonia",
		"otelul": "otelul galati",
		"real oviedo": "oviedo",
		"pafos": "paphos",
		"panaitolikos": "panetolikos",
		"paok salonika": "paok",
		"paris st g": "paris st germain",
		"plymouth argyle": "plymouth",
		"psg": "paris st germain",
		"partizan": "partizan belgrade",
		"municipal perez zeledon": "perez zeledon",
		"peterborough united": "peterborough",
		"petrocub hincesti": "petrocub",
		"acs petrolul 52 ploiesti": "petrolul ploiesti",
		"acs petrolul 52": "petrolul ploiesti",
		"pisa sporting club": "pisa",
		"politehnica iasi": "poli iasi",
		"psv eindhoven": "psv",
		"racing club avellaneda": "racing club",
		"rapid wien": "rapid vienna",
		"vallecano": "rayo vallecano",
		"reggiana 1919": "reggiana",
		"stade reims": "reims",
		"rigas futbola skola": "rigas fs",
		"qpr": "queens park rangers",
		"crvena zvezda": "red star belgrade",
		"red bull salzburg": "salzburg",
		"red star saint ouen": "red star",
		"rigas": "rigas fs",
		"rodez aveyron": "rodez",
		"rosario": "rosario central",
		"ross co": "ross",
		"rotherham united": "rotherham",
		"sabah masazir": "sabah",
		"sumqayit": "sumgayit",
		"sarmiento de junin": "sarmiento",
		"us sassuolo calcio": "sassuolo",
		"sassuolo calcio": "sasuolo",
		"schalke": "schalke 04",
		"acs sepsi osk": "sepsi",
		"shakhtar donetsk": "shakhtar",
		"sheff united": "sheffield united",
		"sheff wed": "sheffield wednesday",
		"sheffield wed": "sheffield wednesday",
		"hnk sibenik": "sibenik",
		"slaven": "slaven belupo",
		"real sociedad": "sociedad",
		"sint truidense": "sint truiden",
		"spartak": "spartak subotica",
		"spezia calcio": "spezia",
		"sporting": "sporting lisbon",
		"sporting cp": "sporting lisbon",
		"sankt gallen": "st gallen",
		"st liege": "standard liege",
		"standard": "standard liege",
		"strasbourg alsace": "strasbourg",
		"saint etienne": "st etienne",
		"laval": "stade lavallois",
		"sudtirol alto adige": "sudtirol",
		"sumqayit sheher": "sumqayit",
		"swindon town": "swindon",
		"deportes tolima": "tolima",
		"tottenham hotspur": "tottenham",
		"tns": "the new saints",
		"estac troyes": "troyes",
		"tsc": "backa topola",
		"ulm 1846": "ulm",
		"union de santa fe": "union santa fe",
		"royale union st gilloise": "union st gilloise",
		"union saint gilloise": "union st gilloise",
		"union sg": "union st gilloise",
		"u saint gilloise": "union st gilloise",
		"saint gilloise": "union st gilloise",
		"saint johnstone": "st johnstone",
		"union": "union berlin",
		"unirea 2004 slobozia": "unirea slobozia",
		"usc cortenais": "usc corte",
		"velez sarsfield": "velez",
		"vikingur": "vikingur reykjavik",
		"plzen": "viktoria plzen",
		"waalwijk": "rkc waalwijk",
		"w phoenix": "wellington pheonix",
		"bremen": "werder bremen",
		"west bromwich": "west brom",
		"west ham united": "west ham",
		"wolverhampton": "wolves",
		"wolverhampton wanderers": "wolves",
		"wigan athletic": "wigan",
		"wycombe wanderers": "wycombe",
		"csd xelaju mc": "xelaju",
		"csd xelaju": "xelaju",
		"real zaragoza": "zaragoza",
		"pec zwolle": "zwolle"
	}
	return j.get(team, team)

def convertMGMMLBTeam(team):
	team = team.lower()
	if team == "diamondbacks":
		return "ari"
	elif team == "braves":
		return "atl"
	elif team == "orioles":
		return "bal"
	elif team == "red sox":
		return "bos"
	elif team == "cubs":
		return "chc"
	elif team == "white sox":
		return "chw"
	elif team == "reds":
		return "cin"
	elif team == "guardians":
		return "cle"
	elif team == "rockies":
		return "col"
	elif team == "tigers":
		return "det"
	elif team == "astros":
		return "hou"
	elif team == "royals":
		return "kc"
	elif team == "angels":
		return "laa"
	elif team == "dodgers":
		return "lad"
	elif team == "marlins":
		return "mia"
	elif team == "brewers":
		return "mil"
	elif team == "twins":
		return "min"
	elif team == "mets":
		return "nym"
	elif team == "yankees":
		return "nyy"
	elif team == "athletics":
		return "ath"
	elif team == "phillies":
		return "phi"
	elif team == "pirates":
		return "pit"
	elif team == "padres":
		return "sd"
	elif team == "giants":
		return "sf"
	elif team == "mariners":
		return "sea"
	elif team == "cardinals":
		return "stl"
	elif team == "rays":
		return "tb"
	elif team == "rangers":
		return "tex"
	elif team == "blue jays":
		return "tor"
	elif team == "nationals":
		return "wsh"
	return team