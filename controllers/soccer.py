
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import math
import json
import os
import re
import argparse
import unicodedata
import time
from twilio.rest import Client

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def convertTeam(game):
	game = strip_accents(game).replace(".", "").replace("-", " ").replace("'", "").replace("/", " ")
	if " @ " in game:
		away, home = map(str, game.split(" @ "))
	else:
		away = game
		home = ""
	g = []
	for team in [away, home]:
		if not team:
			continue
		t = team
		for suffix in ["sp", "rj", "fr", "ce", "ba", "pr", "rs", "rb", "rc", "ssc", "sc", "cf", "bb", "as", "fc", "se", "te", "ba", "jk", "tc", "nk", "calcio", "fbc", "fk", "ac", "mg", "ad", "town", "athletic", "county", "rovers", "cd", "ec", "sk", "u21"]:
			if t.endswith(f" {suffix}"):
				t = t[:-1*(len(suffix) + 1)]
		for prefix in ["sc", "aa", "ac", "as", "jk", "sk", "us", "sd", "ec", "aep", "ns", "ssd", "ssc", "kaa", "fks", "csd", "sm", "rb", "em", "rks", "bk", "hsk", "se"]:
			if t.startswith(f"{prefix} "):
				t = t[(len(prefix) + 1):]
		g.append(t)

	if len(g) == 2:
		game = " @ ".join(g)
	else:
		game = g[0]
	game = game.replace("fc ", "").replace("1 ", "").replace("cf ", "").replace("fk ", "").replace("sv ", "").replace("vfb ", "").replace("nk ", "").replace(" *", "").replace("united", "utd").replace("saint ", "st ")
	# cities
	game = game.replace("new york city", "nyc").replace("san jose", "sj").replace("por ", "portland ").replace("col ", "colorado ").replace("chi ", "chicago ").replace("chicago fire", "chicago").replace("phi ", "philadelphia ").replace("orl ", "orlando ").replace("hou ", "houston ").replace("lafc", "los angeles").replace("van ", "vancouver ").replace("sea ", "seattle ").replace("min ", "minnesota ")
	tr = {
		"atletica ponte preta": "ponte preta",
		"aberystwyth town": "aberystwyth",
		"accrington stanley": "accrington",
		"ca bucaramanga": "atletico bucaramanga",
		"ae zakakiou": "aez zakakiou",
		"ae kifisia": "kifisia",
		"kifisias": "kifisia",
		"abc rn": "abc",
		"abc natal rn": "abc",
		"amazulu durban": "amazulu",
		"albacete balompie": "albacete",
		"ajax cape": "cape town spurs",
		"ajax amsterdam": "ajax",
		"apoel nicosia": "apoel",
		"athletic club bilbao": "athletic bilbao",
		"atl paranaense": "paranaense",
		"athletico pr": "paranaense",
		"athletico paranaense": "paranaense",
		"atletico go": "atletico goianiense",
		"bayer leverkusen": "leverkusen",
		"benfica lisbon": "benfica",
		"besiktas istanbul": "besiktas",
		"birmingham city": "birmingham",
		"blackburn rovers": "blackburn",
		"bohemians dublin": "bohemians",
		"bolton wanderers": "bolton",
		"ad pasto": "deportivo pasto",
		"borussia dortmund": "dortmund",
		"breidablik kopavogur": "breidablik",
		"brighton & hove albion": "brighton",
		"brighton and hove albion": "brighton",
		"bsc young boys bern": "young boys",
		"bsc young boys": "young boys",
		"caernarfon town": "caernarfon",
		"cajamarca utc": "utc de cajamarca",
		"utc cajamarca": "utc de cajamarca",
		"universidad tecnica de cajamarca": "utc de cajamarca",
		"cardiff city": "cardiff",
		"carlisle utd": "carlisle",
		"catanzaro 1929": "catanzaro",
		"cd hermanos colmenarez": "hermanos colmenarez",
		"cd hermanos colmenares": "hermanos colmenarez",
		"cd cuenca": "deportivo cuunca",
		"cd mirandes": "mirandes",
		"charlton athletic": "charlton",
		"cherno more varna": "cherno more",
		"colorado rapids": "colorado",
		"columbus crew": "columbus",
		"colchester utd": "colchester",
		"como 1907": "como",
		"coventry city": "coventry",
		"coquimbo unido": "coquimbo",
		"crewe alexandra": "crewe",
		"crvena zvezda": "red star belgrade",
		"cska 1948 sofia": "cska 1948",
		"cukaricki belgrade": "cukaricki",
		"darmstadt 98": "darmstadt",
		"defensa justicia": "defensa y justicia",
		"deportivo alaves": "alaves",
		"deportivo binacional": "binacional",
		"derby county": "derby",
		"dungannon swifts": "dungannon",
		"drogheda utd": "drogheda",
		"estudiantes de merida": "estudiantes merida",
		"exeter city": "exeter",
		"ferencvarosi": "ferencvaros",
		"forest green rovers": "forest green",
		"futebol clube de arouca": "arouca",
		"gazisehir gaziantep": "gaziantep",
		"girondins de bordeaux": "bordeax",
		"goianiense go": "atletico goianiense",
		"glentoran belfast": "glentoran",
		"hamburger sv": "hamburg",
		"honka espoo": "honka",
		"ilves tampere": "ilves",
		"tampereen ilves": "ilves",
		"inter milan": "inter",
		"internazionale": "inter",
		"internacional rs": "internacional",
		"houston dynamo": "houston",
		"sporting kansas city": "kansas city",
		"sporting kc": "kansas city",
		"lausanne": "lausanne sport",
		"lamontville golden arrows": "golden arrows",
		"lask": "lask linz",
		"ldu quito": "ldu",
		"leeds utd": "leeds",
		"leicester city": "leicester",
		"los angeles galaxy": "la galaxy",
		"lincoln": "lincoln city",
		"ludogorets razgrad": "ludogorets",
		"luton town": "luton",
		"pludogorets": "ludogorets",
		"manchester city": "man city",
		"man utd": "manchester utd",
		"mezokovesd zsory": "mezokovesd",
		"minnesota utd": "minnesota",
		"minnesota stars": "minnesota",
		"montreal impact": "montreal",
		"mk dons": "milton keynes dons",
		"mura murska sobota": "mura",
		"newcastle utd": "newcastle",
		"newry city": "newry",
		"nordsj earthquakesaelland": "nordsjaelland",
		"norwich city": "norwich",
		"notts co": "notts",
		"notts county": "notts",
		"nuova cosenza": "cosenza",
		"olimpija ljubljana": "olimpija",
		"olympiacos": "olympiakos",
		"olympiakos piraeus": "olympiakos",
		"olympique marseille": "marseille",
		"ogc nice": "nice",
		"orense sporting club": "orense",
		"paderborn 07": "paderborn",
		"pafos": "paphos",
		"paks": "paksi",
		"paris st g": "paris st germain",
		"paris sg": "paris st germain",
		"pas lamia 1964": "lamia",
		"pcska sofia": "cska sofia",
		"peterborough utd": "peterborough",
		"philadelphia union": "philadelphia",
		"pludogorets razgrad": "ludogorets",
		"plokomotiv plovdiv": "lokomotiv plovdiv",
		"plymouth argyle": "plymouth",
		"preston north end": "preston",
		"pslavia sofia": "slavia sofia",
		"psg": "paris st germain",
		"psv eindhoven": "psv",
		"puskas": "puskas akademia",
		"puskas academy": "puskas akademia",
		"qpr": "queens park rangers",
		"qarabagh": "qarabag",
		"racing strasbourg": "strasbourg",
		"rc lens": "lens",
		"real sociedad": "sociedad",
		"real betis": "betis",
		"real zaragoza": "zaragoza",
		"red bull salzburg": "salzburg",
		"royal antwerp": "antwerp",
		"ruzomberok": "mruzomberok",
		"seattle sounders": "seattle",
		"acs sepsi osk": "spesi",
		"sepsi osk": "sepsi",
		"servette geneve": "servette",
		"shakhtar donetsk": "shakhtar",
		"sheffield wed": "sheffield wednesday",
		"sheff wed": "sheffield wednesday",
		"shelbourne dublin": "shelbourne",
		"shrewsbury town": "shrewsbury",
		"sligo rovers": "sligo",
		"sport boys (per)": "sport boys", 
		"sankt gallen": "st gallen",
		"schalke": "schalke 04",
		"sport recife pe": "sport recife",
		"sport recife pe": "sport recife",
		"sport club do recife": "sport recife",
		"st patricks athletic": "st patricks",
		"st gilloise": "union st gilloise",
		"stade rennes": "rennes",
		"stoke city": "stoke",
		"swanseattle city": "swansea",
		"swallows": "moroka swallows",
		"cd tolima": "tolima",
		"deportes tolima": "tolima",
		"tallinna flora": "flora tallinn",
		"tranmere rovers": "tranmere",
		"ud las palmas": "las palmas",
		"university college dublin": "ucd",
		"uni college dublin": "ucd",
		"univ college dublin": "ucd",
		"uc dublin": "ucd",
		"vitoria salvador": "vitoria",
		"vfl osnabruck": "osnabruck",
		"vfl 1899 osnabruck": "osnabruck",
		"vitesse arnhem": "vitesse",
		"debrecen": "debreceni vsc",
		"vallecano": "rayo vallecano",
		"verona": "hellas verona",
		"villarreal b": "villarreal ii",
		"vsc debrecen": "debreceni vsc",
		"widzew odz": "widzew lodz",
		"west ham utd": "west ham",
		"west bromwich albion": "west brom",
		"wycombe wanderers": "wycombe",
		"zorya luhansk": "zorya",
		"zalaegerszegi": "zalaegerszeg",
		"zorya lugansk": "zorya",
		"zrinjski": "zrinjski mostar"
	}
	return tr.get(game, game)

def parsePlayer(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def convertDecOdds(odds):
	if odds == 0:
		return 0
	if odds > 0:
		decOdds = 1 + (odds / 100)
	else:
		decOdds = 1 - (100 / odds)
	return decOdds

def convertAmericanOdds(avg):
	if avg >= 2:
		avg = (avg - 1) * 100
	else:
		avg = -100 / (avg - 1)
	return round(avg)

def writeTotals(teamArg=""):
	outfile = f"soccerout"

	with open("static/soccer/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open("static/soccer/corners.json") as fh:
		corners = json.load(fh)

	with open("static/soccer/totals.json") as fh:
		totals = json.load(fh)

	for game in fdLines:
		for team in game.split(" @ "):
			if teamArg and team != teamArg:
				continue
			if team in corners:
				time.sleep(0.3)
				os.system(f"curl 'https://www.windrawwin.com/results/{corners[team]['link']}/' --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.windrawwin.com/results/houston/' -H 'Alt-Used: www.windrawwin.com' -H 'Connection: keep-alive' -H 'Cookie: ASPSESSIONIDCUCSSQDA=HHEJKDNAFOCPOKLJBGFHEMPC; ASPSESSIONIDSGASSQDC=BPCMDAKAMJEFEDHEJCKPCFGO; ASPSESSIONIDQGAQTSBD=LEJCKKBBBABAADPNEPCLABOK; ASPSESSIONIDSGCRRTDD=NCHDOFOAPEEKDHKLNBOGBFAJ; ASPSESSIONIDAWCRQRBA=AMCJLPHAGNKDNMLIOCOMPNIP; ASPSESSIONIDSECRRQBC=NFHDHIKAAEAEOMKOGHFGMLFM; ASPSESSIONIDCWBTSRCA=IKKMLILABMLJPHJFKCBOEKDN; ASPSESSIONIDCWDRQQAB=JBPBCDDBENAMAKALOGMDGIHM; ASPSESSIONIDCUBRSRBA=DHLOOPIAGACHNJLMCHHJDFKH; ASPSESSIONIDCUASQQAB=ECDMPFNACBJAMOMGBGKMONOE; ASPSESSIONIDCUBSRRAA=MFKEMAMAKIEALAJCOBIODOFK; ASPSESSIONIDCWATSQBD=CGEDIALACLIBEALNDCHMEFPK; ASPSESSIONIDSGDSQTCC=AKHHIHHAMJMPGKJMHLIHLHFN; ASPSESSIONIDAWCTTQAD=EIFOMCCBKOAIKPAGLDCEEGHJ; ASPSESSIONIDSGATRSDC=NDOAGCBBDDJOFCDIJDOMNLOA; ASPSESSIONIDCWBSRQAA=BPMABIJANMELHBNLLBFDAHEK; ASPSESSIONIDQGBQRSDC=FPDIBMGBJPIFODLKHJNINGOI; ASPSESSIONIDAUAQTQAB=HNBMIJOAHFJPALBNFPNBPNHO; ASPSESSIONIDQGCQTRAD=LJEJFDEBPBEHIDCGDBBEBHOG; ASPSESSIONIDAUDTSSAA=HJJIDBNAJNAHGEOGGJHPFCEO; ASPSESSIONIDSEBSQRDD=JEPIMLFBBLIAHDHPCGCEMNDM; ASPSESSIONIDAUARQSCA=KPFHEMGBGECIIFMCLEJBMICL; ASPSESSIONIDCWBSQRBB=DDLJILEBGHOMMHOOKAMOEBKL; ASPSESSIONIDSECSQRAC=AKPDOKCBPIIMIOHENMMPHMKP; ASPSESSIONIDAUCTTRAC=MDCGEKABKMGEIEFLHJLIHPJK; ASPSESSIONIDAWAQRQBD=OAFHGMHBNEJGNOGLDIBFCLBC; ASPSESSIONIDCWDSSQAA=LMALIPJBLDEOIEGLABGNPMGA; ASPSESSIONIDAUCSTRAC=CGKIBNJBMFOPLEDNFFLNEMAJ; ASPSESSIONIDAUCRRTCA=AODPGFLBLHPNCPJGHAGMNMHD; ASPSESSIONIDAUAQRQCA=EBNKINABAILCPGBHILFMEEBJ; ASPSESSIONIDCUBRRRDB=PKBPBCABKELBKGDIHCPBBPGI; ASPSESSIONIDQEDSRQBD=JKEJKMIBBEPDOKHJKCJEKKHG' -o {outfile}")

				soup = BS(open(outfile, 'rb').read(), "lxml")

				totals[team] = {}
				for row in soup.findAll("tr")[2:]:
					if row.get("class") and ("hidden" in row.get("class") or "unhidden" in row.get("class") or "vtop" in row.get("class")):
						continue
					if len(row.findAll("td")) < 7:
						continue
					if " v " not in row.findAll("td")[1].text:
						continue
					matchup = row.findAll("td")[1].text.split(" v ")[1].lower()
					isAway = convertTeam(matchup) == team
					opp = row.findAll("td")[1].text.split(" v ")[1].lower()
					if isAway:
						opp = row.findAll("td")[1].text.split(" v ")[0].lower()
					opp = convertTeam(opp)
					#print(matchup, isAway)
					teamScore, oppScore = map(int, row.findAll("td")[2].text.split("-"))
					teamScoreHalf, oppScoreHalf = map(int, row.findAll("td")[3].text.split("-"))
					if isAway:
						teamScore, oppScore = oppScore, teamScore
						teamScoreHalf, oppScoreHalf = oppScoreHalf, teamScoreHalf

					idx = 0
					which = "opp" if isAway else ""
					hdrs = ["pos", "corners", "fouls", "shots_on_target", "shots_off_target"]
					j = {}
					for td in row.findAll("td")[4:-1]:
						if idx == 5:
							which = "" if isAway else "opp"
						hdr = hdrs[idx % 5]
						if which:
							hdr = which+"_"+hdr
						if "%" in td.text or not strip_accents(td.text):
							j[hdr] = strip_accents(td.text)
						else:
							j[hdr] = int(td.text)
						idx += 1

					j["opp"] = opp
					j["total"] = teamScore
					j["opp_total"] = oppScore
					j["game_total"] = teamScore + oppScore
					j["1h_total"] = teamScoreHalf
					j["1h_opp_total"] = oppScoreHalf
					j["1h_game_total"] = teamScoreHalf + oppScoreHalf
					j["total_shots"] = j["shots_on_target"] + j["shots_off_target"]
					j["opp_total_shots"] = j["opp_shots_on_target"] + j["opp_shots_off_target"]
					j["game_total_shots"] = j["total_shots"] + j["opp_total_shots"]

					for hdr in j:
						if hdr not in totals[team]:
							totals[team][hdr] = []
						totals[team][hdr].append(j[hdr])


	with open("static/soccer/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def writeCorners():
	outfile = f"soccerout"

	time.sleep(0.3)
	os.system(f"curl 'https://www.windrawwin.com/statistics/corners/usa-major-league-soccer/' --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.windrawwin.com/results/houston/' -H 'Alt-Used: www.windrawwin.com' -H 'Connection: keep-alive' -H 'Cookie: ASPSESSIONIDCUCSSQDA=HHEJKDNAFOCPOKLJBGFHEMPC; ASPSESSIONIDSGASSQDC=BPCMDAKAMJEFEDHEJCKPCFGO; ASPSESSIONIDQGAQTSBD=LEJCKKBBBABAADPNEPCLABOK; ASPSESSIONIDSGCRRTDD=NCHDOFOAPEEKDHKLNBOGBFAJ; ASPSESSIONIDAWCRQRBA=AMCJLPHAGNKDNMLIOCOMPNIP; ASPSESSIONIDSECRRQBC=NFHDHIKAAEAEOMKOGHFGMLFM; ASPSESSIONIDCWBTSRCA=IKKMLILABMLJPHJFKCBOEKDN; ASPSESSIONIDCWDRQQAB=JBPBCDDBENAMAKALOGMDGIHM; ASPSESSIONIDCUBRSRBA=DHLOOPIAGACHNJLMCHHJDFKH; ASPSESSIONIDCUASQQAB=ECDMPFNACBJAMOMGBGKMONOE; ASPSESSIONIDCUBSRRAA=MFKEMAMAKIEALAJCOBIODOFK; ASPSESSIONIDCWATSQBD=CGEDIALACLIBEALNDCHMEFPK; ASPSESSIONIDSGDSQTCC=AKHHIHHAMJMPGKJMHLIHLHFN; ASPSESSIONIDAWCTTQAD=EIFOMCCBKOAIKPAGLDCEEGHJ; ASPSESSIONIDSGATRSDC=NDOAGCBBDDJOFCDIJDOMNLOA; ASPSESSIONIDCWBSRQAA=BPMABIJANMELHBNLLBFDAHEK; ASPSESSIONIDQGBQRSDC=FPDIBMGBJPIFODLKHJNINGOI; ASPSESSIONIDAUAQTQAB=HNBMIJOAHFJPALBNFPNBPNHO; ASPSESSIONIDQGCQTRAD=LJEJFDEBPBEHIDCGDBBEBHOG; ASPSESSIONIDAUDTSSAA=HJJIDBNAJNAHGEOGGJHPFCEO; ASPSESSIONIDSEBSQRDD=JEPIMLFBBLIAHDHPCGCEMNDM; ASPSESSIONIDAUARQSCA=KPFHEMGBGECIIFMCLEJBMICL; ASPSESSIONIDCWBSQRBB=DDLJILEBGHOMMHOOKAMOEBKL; ASPSESSIONIDSECSQRAC=AKPDOKCBPIIMIOHENMMPHMKP; ASPSESSIONIDAUCTTRAC=MDCGEKABKMGEIEFLHJLIHPJK; ASPSESSIONIDAWAQRQBD=OAFHGMHBNEJGNOGLDIBFCLBC; ASPSESSIONIDCWDSSQAA=LMALIPJBLDEOIEGLABGNPMGA; ASPSESSIONIDAUCSTRAC=CGKIBNJBMFOPLEDNFFLNEMAJ; ASPSESSIONIDAUCRRTCA=AODPGFLBLHPNCPJGHAGMNMHD; ASPSESSIONIDAUAQRQCA=EBNKINABAILCPGBHILFMEEBJ; ASPSESSIONIDCUBRRRDB=PKBPBCABKELBKGDIHCPBBPGI; ASPSESSIONIDQEDSRQBD=JKEJKMIBBEPDOKHJKCJEKKHG' -o {outfile}")

	soup = BS(open(outfile, 'rb').read(), "lxml")
	totals = {}

	leagues = {}
	for league in soup.find("select", id="leaguenav").findAll("option"):
		if league.get("value"):
			leagues[league.text.lower()] = league.get("value").split("/")[-2]

	for league in leagues:
		time.sleep(0.3)
		os.system(f"curl 'https://www.windrawwin.com/statistics/corners/{leagues[league]}/' --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.windrawwin.com/results/houston/' -H 'Alt-Used: www.windrawwin.com' -H 'Connection: keep-alive' -H 'Cookie: ASPSESSIONIDCUCSSQDA=HHEJKDNAFOCPOKLJBGFHEMPC; ASPSESSIONIDSGASSQDC=BPCMDAKAMJEFEDHEJCKPCFGO; ASPSESSIONIDQGAQTSBD=LEJCKKBBBABAADPNEPCLABOK; ASPSESSIONIDSGCRRTDD=NCHDOFOAPEEKDHKLNBOGBFAJ; ASPSESSIONIDAWCRQRBA=AMCJLPHAGNKDNMLIOCOMPNIP; ASPSESSIONIDSECRRQBC=NFHDHIKAAEAEOMKOGHFGMLFM; ASPSESSIONIDCWBTSRCA=IKKMLILABMLJPHJFKCBOEKDN; ASPSESSIONIDCWDRQQAB=JBPBCDDBENAMAKALOGMDGIHM; ASPSESSIONIDCUBRSRBA=DHLOOPIAGACHNJLMCHHJDFKH; ASPSESSIONIDCUASQQAB=ECDMPFNACBJAMOMGBGKMONOE; ASPSESSIONIDCUBSRRAA=MFKEMAMAKIEALAJCOBIODOFK; ASPSESSIONIDCWATSQBD=CGEDIALACLIBEALNDCHMEFPK; ASPSESSIONIDSGDSQTCC=AKHHIHHAMJMPGKJMHLIHLHFN; ASPSESSIONIDAWCTTQAD=EIFOMCCBKOAIKPAGLDCEEGHJ; ASPSESSIONIDSGATRSDC=NDOAGCBBDDJOFCDIJDOMNLOA; ASPSESSIONIDCWBSRQAA=BPMABIJANMELHBNLLBFDAHEK; ASPSESSIONIDQGBQRSDC=FPDIBMGBJPIFODLKHJNINGOI; ASPSESSIONIDAUAQTQAB=HNBMIJOAHFJPALBNFPNBPNHO; ASPSESSIONIDQGCQTRAD=LJEJFDEBPBEHIDCGDBBEBHOG; ASPSESSIONIDAUDTSSAA=HJJIDBNAJNAHGEOGGJHPFCEO; ASPSESSIONIDSEBSQRDD=JEPIMLFBBLIAHDHPCGCEMNDM; ASPSESSIONIDAUARQSCA=KPFHEMGBGECIIFMCLEJBMICL; ASPSESSIONIDCWBSQRBB=DDLJILEBGHOMMHOOKAMOEBKL; ASPSESSIONIDSECSQRAC=AKPDOKCBPIIMIOHENMMPHMKP; ASPSESSIONIDAUCTTRAC=MDCGEKABKMGEIEFLHJLIHPJK; ASPSESSIONIDAWAQRQBD=OAFHGMHBNEJGNOGLDIBFCLBC; ASPSESSIONIDCWDSSQAA=LMALIPJBLDEOIEGLABGNPMGA; ASPSESSIONIDAUCSTRAC=CGKIBNJBMFOPLEDNFFLNEMAJ; ASPSESSIONIDAUCRRTCA=AODPGFLBLHPNCPJGHAGMNMHD; ASPSESSIONIDAUAQRQCA=EBNKINABAILCPGBHILFMEEBJ; ASPSESSIONIDCUBRRRDB=PKBPBCABKELBKGDIHCPBBPGI; ASPSESSIONIDQEDSRQBD=JKEJKMIBBEPDOKHJKCJEKKHG' -o {outfile}")

		soup = BS(open(outfile, 'rb').read(), "lxml")
		for row in soup.findAll("div", class_="wttr2"):
			if not row.find("a") or not row.find("div", class_="statteam"):
				continue
			team = convertTeam(row.find("a").text.lower()).replace("sj", "sj earthquakes")
			corners = float(row.find("div", class_="statpld").text)
			cornersAgainst = float(row.find("div", class_="statnum").text)

			totals[team] = {
				"corners": corners,
				"cornersAgainst": cornersAgainst,
				"cornersTotal": round(corners+cornersAgainst, 1),
				"link": row.find("a").get("href").split("/")[-2],
				"league": league
			}

	with open("static/soccer/corners.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def writeLeagues(bookArg):
	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)

	for book in ["pn", "bv", "dk", "kambi"]:
		if bookArg and book != bookArg:
			continue
		outfile = "outsoccer"

		if book == "pn":
			url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/sports/29/leagues?all=false&brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile
			os.system(url)
			with open(outfile) as fh:
				data = json.load(fh)

			leagues["pn"] = {}
			for row in data:
				name = row["name"].lower()
				leagues["pn"][name] = row["id"]
		elif book == "bv":
			url = "https://services.bovada.lv/services/sports/event/v2/nav/A/description/soccer?lang=en"
			os.system(f"curl -k \"{url}\" -o {outfile}")
			with open(outfile) as fh:
				data = json.load(fh)

			links = []
			print()
			for row in data["children"]:
				links.append(row["link"])

			leagues["bv"] = {}
			childLinks = []
			for link in links:
				url = f"https://services.bovada.lv/services/sports/event/v2/nav/A/description{link}?lang=en"
				time.sleep(0.2)
				os.system(f"curl -k \"{url}\" -o {outfile}")
				with open(outfile) as fh:
					data = json.load(fh)
				for row in data["children"]:
					childLinks.append(row["link"])

			for link in childLinks:
				url = f"https://services.bovada.lv/services/sports/event/v2/nav/A/description{link}?lang=en"
				time.sleep(0.2)
				os.system(f"curl -k \"{url}\" -o {outfile}")
				with open(outfile) as fh:
					data = json.load(fh)
				current = data["current"]["description"]
				for row in data["children"]:
					leagues["bv"][current+" "+row["description"]] = row["link"]
		elif book == "dk":
			url = "https://sportsbook.draftkings.com/sports/soccer"
			time.sleep(0.2)
			#os.system(f"curl -k \"{url}\" -o {outfile}")

			soup = BS(open(outfile, 'rb').read(), "lxml")

			data = "{}"
			for script in soup.findAll("script"):
				if not script.string:
					continue
				if "__INITIAL_STATE" in script.string:
					m = re.search(r"__INITIAL_STATE__ = {(.*?)};", script.string)
					if m:
						data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
						data = f"{{{data}}}"
						break

			data = eval(data)
			leagues["dk"] = {}
			for row in data["sports"]["data"]:
				if row["displayName"] != "Soccer":
					continue
				for event in row["eventGroupInfos"]:
					leagues["dk"][event["eventGroupId"]] = event["eventGroupName"]
		elif book == "kambi":
			url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/group.json?lang=en_US&market=US&client_id=2&ncid=1695395534961"

			time.sleep(0.2)
			os.system(f"curl -k \"{url}\" -o {outfile}")
			with open(outfile) as fh:
				data = json.load(fh)

			leagues["kambi"] = {}
			for group in data["group"]["groups"]:
				if group["name"] != "Soccer":
					continue
				for league in group["groups"]:
					leagues["kambi"][league["termKey"]] = league["id"]
	

	with open("static/soccer/leagues.json", "w") as fh:
		json.dump(leagues, fh, indent=4)


def writePinnacle(date):
	debug = False
	if not date:
		date = str(datetime.now())[:10]

	outfile = f"socceroutPN"

	res = {}
	
	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)

	for league in leagues["pn"]:
		url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/'+str(leagues["pn"][league])+'/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile

		time.sleep(0.2)
		os.system(url)
		with open(outfile) as fh:
			data = json.load(fh)

		ids = []
		for row in data:
			if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
				continue
			if row["parent"] and row["parent"]["id"] not in ids:
				ids.append(row["parent"]["id"])

		#ids = ["1578036428"]
		for bid in ids:
			url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

			time.sleep(0.3)
			os.system(url)
			with open(outfile) as fh:
				related = json.load(fh)

			relatedData = {}
			for row in related:
				if True or "special" in row:
					try:
						prop = row["units"].lower()
					except:
						continue

					over = under = 0
					if "id" in row["participants"][0]:
						over = row["participants"][0]["id"]
						under = row["participants"][1]["id"]
						if row["participants"][0]["name"] == "Under":
							over, under = under, over
					player = ""
					if "special" in row:
						player = parsePlayer(row["special"]["description"].split(" (")[0])
					relatedData[row["id"]] = {
						"player": player,
						"prop": prop,
						"over": over,
						"under": under
					}

			if debug:
				with open("t2", "w") as fh:
					json.dump(related, fh, indent=4)

			url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

			time.sleep(0.3)
			os.system(url)
			with open(outfile) as fh:
				data = json.load(fh)

			if debug:
				with open("t3", "w") as fh:
					json.dump(data, fh, indent=4)

			try:
				gamesMatchup = related[0]["id"] if related[0]["units"] == "Games" else related[1]["id"]
			except:
				gamesMatchup = ""
			try:
				player1 = related[0]["participants"][0]["name"].lower()
				player2 = related[0]["participants"][1]["name"].lower()
			except:
				continue

			game = f"{convertTeam(player1)} @ {convertTeam(player2)}"
			if game in res:
				continue
			res[game] = {}

			for row in data:
				try:
					prop = row["type"]
				except:
					continue
				keys = row["key"].split(";")

				prefix = ""
				if keys[1] == "1":
					prefix = "1h_"
				elif keys[1] == "3":
					prefix = "2h_"

				overId = underId = 0
				player = ""

				#if row["matchupId"] == 1578461072:
				#	print(relatedData[1578461072])

				if row["matchupId"] != int(bid):
					if row["matchupId"] not in relatedData:
						continue
					player = relatedData[row["matchupId"]]["player"]
					prop = relatedData[row["matchupId"]]["prop"]
					overId = relatedData[row["matchupId"]]["over"]
					underId = relatedData[row["matchupId"]]["under"]

					if "regular" in prop:
						if "draw no bet" in player:
							prop = "dnb"
						elif player == "both teams to score?" or player == "both teams to score? 1st half":
							prop = "btts"
						else:
							continue

					elif prop == "corners" and row["type"] == "spread":
						prop = "corners_spread"
				else:
					pass

				if prop == "moneyline":
					continue

				prop = f"{prefix}{prop}"
				switched = 0
				prices = row["prices"]
				if overId:
					try:
						ou = f"{prices[0]['price']}/{prices[1]['price']}"
					except:
						continue
					if prices[0]["participantId"] == underId:
						ou = f"{prices[1]['price']}/{prices[0]['price']}"
						switched = 1

					if "dnb" in prop or "btts" in prop:
						res[game][prop] = ou
						continue

					if prop not in res[game]:
						res[game][prop] = {}

					if "points" in prices[0] and prop not in []:
						handicap = str(prices[switched]["points"])
						res[game][prop][player] = handicap+" "+ou
					else:
						res[game][prop][player] = ou
				else:
					ou = f"{prices[0]['price']}/{prices[1]['price']}"
					if "points" in prices[0]:
						handicap = str(prices[0]["points"])
						if prop not in res[game]:
							res[game][prop] = {}
						try:
							res[game][prop][handicap] = ou
						except:
							continue
					else:
						res[game][prop] = ou

	with open("static/soccer/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)


def writeMGM(date=None):

	if not date:
		date = str(datetime.now())[:10]

	res = {}
	#leagues = {102849: "mls", 102855: "champions", 102856: "uefa europa league", 102919: "efa europa conference league", 102841: "epl", 102829: "la liga", 	102842: "bundesliga", 102846: "serie a", 102843: "ligue 1", 102373: "liga mx", 101551: "league one", 101550: "league two", 102782: "efl", 102717: "china"}
	for tourney in [None]:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&offerCategories=Gridable&fixtureCategories=Gridable,NonGridable,Other&sportIds=4&regionIds=&competitionIds=&conferenceIds=&isPriceBoost=false&statisticsModes=SeasonStandings&skip=0&take=150&sortBy=StartDate"
		outfile = f"socceroutMGM"

		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		ids = []
		for row in data["fixtures"]:
			if str(datetime.strptime(row["startDate"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
				continue
			ids.append(row["id"])

		#ids = ["2:6114325"]
		for mgmid in ids:
			url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=false&statisticsModes=All"
			time.sleep(0.3)
			os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			try:
				data = data["fixture"]
			except:
				continue
			game = strip_accents(data["name"]["value"].lower())

			try:
				p1, p2 = map(str, game.split(" - "))
				game = f"{convertTeam(p1)} @ {convertTeam(p2)}"
			except:
				continue

			res[game] = {}
			for row in data["optionMarkets"]:
				prop = row["name"]["value"].lower()

				prefix = ""
				if "1st half" in prop:
					prefix = "1h_"
				if "2nd half" in prop:
					prefix = "2h_"

				if ";" in prop:
					continue
				if "draw no bet" in prop:
					if "and" in prop:
						continue
					prop = "dnb"
				elif "both teams to score" in prop:
					if "and" in prop or "both halves" in prop:
						continue
					prop = "btts"
				elif "anytime goalscorer" in prop:
					prop = "atgs"
				elif "2way handicap" in prop:
					prop = "spread"
				elif "total corners" in prop:
					if ":" in prop or "odd" in prop:
						continue
					if p1 in prop:
						prop = "away_corners"
					elif p2 in prop:
						prop = "home_corners"
					else:
						prop = "corners"
				elif "total goals" in prop:
					if "exact" in prop or "odd/even" in prop or "bands" in prop or "and" in prop or ":" in prop:
						continue
					if "match result" in prop or "double chance" in prop:
						continue
					if p1 in prop:
						prop = "away_total"
					elif p2 in prop:
						prop = "home_total"
					else:
						prop = "total"
				else:
					continue

				prop = f"{prefix}{prop}"

				results = row['options']
				try:
					ou = f"{results[0]['price']['americanOdds']}"
				except:
					continue
				if len(results) > 1 and "americanOdds" in results[1]["price"]:
					ou += f"/{results[1]['price']['americanOdds']}"
				if "dnb" in prop or "btts" in prop:
					res[game][prop] = ou
				elif len(results) >= 2:
					if prop not in res[game]:
						res[game][prop] = {}

					skip = 1 if prop == "atgs" else 2
					for idx in range(0, len(results), skip):
						val = results[idx]["name"]["value"].lower()
						if "spread" in prop:
							val = val.split(" ")[-1][1:-1]
						elif "corners" in prop:
							val = val.split(" ")[-1]
						ou = str(results[idx]['price']["americanOdds"])
						if prop in ["atgs"]:
							val = parsePlayer(val)
							res[game][prop][val] = ou
						else:
							try:
								ou = f"{results[idx]['price']['americanOdds']}/{results[idx+1]['price']['americanOdds']}"
							except:
								continue
							res[game][prop][str(float(val.replace(',', '.').split(" ")[-1]))] = ou

	with open("static/soccer/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBovada(date=None):
	url = "https://www.bovada.lv/sports/soccer/"

	if not date:
		date = str(datetime.now())[:10]

	leagues = []

	leagues.extend([
		"europe/belgium/first-division-a",
		"europe/england/championship",
		"europe/england/premier-league", 
		"europe/england/league-one",
		"europe/france/ligue-1",
		"europe/germany/1-bundesliga",
		"europe/italy/serie-a",
		"europe/spain/la-liga",

		"international-club/uefa-champions-league",
		"international-club/uefa-europa-conference-league",
		"international-club/uefa-europa-league",

		"north-america/united-states/mls",
		"north-america/mexico/liga-mx-apertura"

		"south-america/argentina/copa-de-la-liga-profesional",
		"south-america/argentina/primera-nacional",
		"south-america/brazil/brasileirao-serie-a",
		"south-america/brazil/brasileiro-serie-b",
		"south-america/chile/primera-b",
		"south-america/chile/primera-division",
		"south-america/colombia/primera-a-clausura",
		"south-america/colombia/primera-b",
		"south-america/peru/primera-division",
	])

	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)["bv"]

	ids = []
	for which in leagues:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{leagues[which]}?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
		outfile = f"socceroutBV"

		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			for link in data[0]["events"]:
				if str(datetime.fromtimestamp(link["startTime"] / 1000) - timedelta(hours=2))[:10] != date:
					continue
				ids.append(link["link"])
		except:
			continue

	res = {}
	
	#ids = ['/soccer/north-america/united-states/mls/cf-montreal-fc-cincinnati-202309201930']
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			comp = data[0]['events'][0]['competitors']
		except:
			continue
		player1 = strip_accents(comp[0]['name'].lower())
		player2 = strip_accents(comp[1]['name'].lower())
		game = f"{convertTeam(player1)} @ {convertTeam(player2)}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "both teams to score", "player props", "corner props", "game stats"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["abbreviation"] == "1H":
						prefix = "1h_"

					prop = market["description"].lower()
					if prop == "spread" or prop == "goal spread":
						prop = "spread"
					elif "draw no bet" in prop:
						prop = "dnb"
					elif prop == "total" or "total goals" in prop:
						if "exact" in prop or "&" in prop or "and" in prop:
							continue
						if player1 in strip_accents(prop):
							prop = "away_total"
						elif player2 in strip_accents(prop):
							prop = "home_total"
						else:
							prop = "total"
					elif prop == "both teams to score":
						prop = "btts"
					elif prop == "anytime goal scorer":
						prop = "atgs"
					elif prop == "to assist a goal":
						prop = "assist"
					elif prop == "to score or assist a goal":
						prop = "goal_assist"
					elif "total corners" in prop:
						if player1 in strip_accents(prop):
							prop = "away_corners"
						elif player2 in strip_accents(prop):
							prop = "home_corners"
						elif prop == "total corners handicap":
							prop = "corners_spread"
						else:
							prop = "corners"
					elif "total attempts" in prop:
						suffix = ""
						if "on-target" in prop:
							suffix = "_on_target"

						if player1 in strip_accents(prop):
							prop = "away_shots"
						elif player2 in strip_accents(prop):
							prop = "home_shots"
						elif prop == "total attempts" or prop == "total attempts on target":
							prop = "game_shots"
						else:
							prop = "player_shots"

						prop += suffix
					elif "total tackles" in prop:
						if player1 in strip_accents(prop):
							prop = "away_tackles"
						elif player2 in strip_accents(prop):
							prop = "home_tackles"
						elif prop == "total tackles":
							prop = "tackles"
						else:
							prop = "player_tackles"
					elif "total offsides" in prop:
						if player1 in strip_accents(prop):
							prop = "away_offsides"
						elif player2 in strip_accents(prop):
							prop = "home_offsides"
						else:
							prop = "offsides"
					else:
						continue

					prop = f"{prefix}{prop}"

					#if market["period"]["main"] == False:
					#	continue

					if not len(market["outcomes"]):
						continue

					if "dnb" in prop or prop in ["btts"]:
						try:
							res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
						except:
							continue
					else:
						if prop not in res[game]:
							res[game][prop] = {}

						outcomes = market["outcomes"]
						skip = 1 if prop in ["atgs", "assist", "goal_assist"] else 2
						for idx in range(0, len(outcomes), skip):
							if "handicap" not in outcomes[idx]["price"]:
								if "tackles" in prop or "offsides" in prop or "shots" in prop:
									handicap = outcomes[idx]["description"].split(" ")[-1]
								else:
									handicap = parsePlayer(outcomes[idx]["description"].split(" - ")[-1])
							else:
								handicap = str(float(outcomes[idx]["price"]["handicap"]))
								if "handicap2" in outcomes[idx]["price"]:
									handicap = str((float(handicap) + float(outcomes[idx]["price"]["handicap2"])) / 2)

							ou = f"{market['outcomes'][idx]['price']['american']}"
							if skip == 2:
								try:
									ou += f"/{market['outcomes'][idx+1]['price']['american']}"
								except:
									continue

							if "player" in prop:
								handicap = parsePlayer(market["description"].split(" - ")[-1])
								if handicap not in res[game][prop]:
									res[game][prop][handicap] = {}
								line = outcomes[idx]["description"].split(" ")[-1]
								res[game][prop][handicap][line] = ou.replace("EVEN", "100")
							elif prop == "assist":
								if handicap not in res[game][prop]:
									res[game][prop][handicap] = {}
								res[game][prop][handicap]["0.5"] = ou.replace("EVEN", "100")
							else:
								res[game][prop][handicap] = ou.replace("EVEN", "100")

	with open("static/soccer/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi(date=None):
	data = {}
	outfile = f"soccerout.json"

	if not date:
		date = str(datetime.now())[:10]

	leagues = [
		"brazil/brasileirao_serie_a",
		"brazil/brasileirao_serie_b",
		"champions_league/all",
		"china/super_league",
		"england/premier_league",
		"england/efl_cup",
		"england/league_one",
		"england/league_two",
		"england/the_championship",
		"europa_conference_league/all",
		"europa_league/all",
		"france/ligue_1",
		"france/ligue_2",
		"germany/bundesliga",
		"italy/serie_a",
		"italy/serie_b",
		"mexico/liga_mx",
		"spain/la_liga",
		"spain/la_liga_2",
		"uefa_nations_league__w_",
		"usa/mls",
	]

	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)["kambi"]

	for gender in leagues:
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/football/{gender}/all/all/matches.json?lang=en_US&market=US"
		time.sleep(0.2)
		os.system(f"curl -k \"{url}\" -o {outfile}")
		
		with open(outfile) as fh:
			j = json.load(fh)

		eventIds = {}

		if "events" not in j:
			continue

		fullTeams = {}
		for event in j["events"]:
			game = event["event"]["name"].lower()
			player1, player2 = map(str, game.split(f" {event['event']['nameDelimiter']} "))
			game = f"{convertTeam(player1)} @ {convertTeam(player2)}"
			fullTeams[game] = [strip_accents(player1).replace("munich", "munchen"), strip_accents(player2).replace("munich", "munchen")]
			if game in eventIds:
				continue

			if event["event"]["state"] == "STARTED":
				continue
			eventIds[game] = event["event"]["id"]
			data[game] = {}


		#eventIds = {"houston dynamo @ vancouver whitecaps": 1019281138}
		for game in eventIds:
			eventId = eventIds[game]
			teamIds = {}

			player1, player2 = fullTeams[game]
			
			time.sleep(0.3)
			url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
			os.system(f"curl -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				j = json.load(fh)

			if "closed" not in j["betOffers"][0]:
				continue

			if str(datetime.strptime(j["betOffers"][0]["closed"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
				continue

			player1 = strip_accents(j["events"][0]["homeName"].lower())
			player2 = strip_accents(j["events"][0]["awayName"].lower())

			i = 0
			for betOffer in j["betOffers"]:
				label = strip_accents(betOffer["criterion"]["label"].lower())

				prefix = ""
				if "1st half" in label:
					prefix = "1h_"
				if "2nd half" in label:
					prefix = "2h_"

				if "total goals" in label:
					if player1 in label:
						label = "away_total"
					elif player2 in label:
						label = "home_total"
					else:
						label = "total"
				elif "asian total" in label:
					if player1 in label:
						label = "away_asian_total"
					elif player2 in label:
						label = "home_asian_total"
					else:
						label = "asian_total"
				elif "both teams to score" in label:
					if "and" in label or "halves" in label:
						continue
					label = "btts"
				elif "asian handicap" in label:
					label = "spread"
				elif "draw no bet" in label:
					label = "dnb"
				elif label == "to score":
					label = "atgs"
				elif label == "to give an assist":
					label = "assist"
				elif "total shots" in label:
					suffix = ""
					if "on target" in label:
						suffix = "_on_target"
					if player1 in label:
						label = "away_shots"
					elif player2 in label:
						label = "home_shots"
					else:
						label = "game_shots"

					label += suffix
				elif "player's shots" in label:
					suffix = ""
					if "on target" in label:
						suffix = "_on_target"

					label = "player_shots"
					label += suffix
				elif "total corners" in label:
					#print(label, (player1, player2), player1 in label, player2 in label)
					if player1 in label:
						label = "away_corners"
					elif player2 in label:
						label = "home_corners"
					else:
						label = "corners"
				else:
					continue

				label = f"{prefix}{label}"
				if "oddsAmerican" not in betOffer["outcomes"][0]:
					continue
				if len(betOffer["outcomes"]) == 1 or "oddsAmerican" not in betOffer["outcomes"][1]:
					ou = betOffer["outcomes"][0]["oddsAmerican"]
				else:
					ou = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
					if betOffer["outcomes"][0]["label"] == "Under" or betOffer["outcomes"][0]["label"] == "No":
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
				if "btts" in label or "dnb" in label:
					data[game][label] = ou
				else:
					if label not in data[game]:
						data[game][label] = {}

					line = ""
					try:
						line = betOffer["outcomes"][0]["line"] / 1000
					except:
						pass

					if "player" in label or label in ["atgs", "assist"]:
						player = betOffer["outcomes"][0]["participant"]
						try:
							last, first = map(str, player.split(", "))
							player = parsePlayer(f"{first} {last}")
						except:
							player = parsePlayer(player)
						if player not in data[game][label]:
							data[game][label][player] = {}

						if label in ["atgs"]:
							data[game][label][player] = ou
						elif label == "assist":
							data[game][label][player]["0.5"] = ou
						else:
							data[game][label][player][line] = ou
					else:
						data[game][label][line] = ou

		with open(f"static/soccer/kambi.json", "w") as fh:
			json.dump(data, fh, indent=4)

def writeFanduel():
	url = "https://mi.sportsbook.fanduel.com/soccer"

	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/soccer/") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && (time.innerText.split(" ")[0] === "MON" || time.innerText.split(" ").length < 3)) {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/soccer/bosnia-and-herzegovina---premier-league/zrinjski-v-fk-velez-mostar-32723810",
  "https://mi.sportsbook.fanduel.com/soccer/bosnia-and-herzegovina---premier-league/borac-banja-luka-v-sarajevo-32723930",
  "https://mi.sportsbook.fanduel.com/soccer/wales---premiership/connahs-quay-v-bala-town-32724089",
  "https://mi.sportsbook.fanduel.com/soccer/costa-rican-primera-division/ad-guanacasteca-v-cs-herediano-32714200",
  "https://mi.sportsbook.fanduel.com/soccer/brazilian-serie-a/gremio-v-athletico-pr-32688180",
  "https://mi.sportsbook.fanduel.com/soccer/brazilian-serie-a/coritiba-v-cuiaba-32688184",
  "https://mi.sportsbook.fanduel.com/soccer/brazilian-serie-a/america-mg-v-botafogo-32688185",
  "https://mi.sportsbook.fanduel.com/soccer/us-major-league-soccer/inter-miami-cf-v-charlotte-fc-32703234",
  "https://mi.sportsbook.fanduel.com/soccer/costa-rican-primera-division/cs-cartagines-v-ad-san-carlos-32712543",
  "https://mi.sportsbook.fanduel.com/soccer/brazilian-serie-a/bahia-v-internacional-32688186",
  "https://mi.sportsbook.fanduel.com/soccer/brazilian-serie-a/vasco-da-gama-v-fortaleza-ec-32688179",
  "https://mi.sportsbook.fanduel.com/soccer/brazilian-serie-a/goias-v-sao-paulo-32689650",
  "https://mi.sportsbook.fanduel.com/soccer/colombian-primera-a/millonarios-v-union-magdalena-32672222",
  "https://mi.sportsbook.fanduel.com/soccer/costa-rican-primera-division/ld-alajuelense-v-municipal-perez-zeledon-32714428"
]

	lines = {}
	#games = ["https://mi.sportsbook.fanduel.com/soccer/uefa-champions-league/ac-milan-v-newcastle-32607038"]
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		away, home = map(str, game.split(" @ "))
		game = f"{convertTeam(away)} @ {convertTeam(home)}"

		lines[game] = {}

		outfile = "soccerout"

		for tab in ["popular", "goals", "shots", "corners", "passes"]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-fasAgent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-H", 'x-px-context: _px3=02c9ab1c8d0655c3f57f55884b4aaa616a9a3995e8935408345199e8e71aef9e:Fa57xPlp9jkOygctuLr5buwfVIYS/s9bO7ouGbCabNNgpUmFDpOmHSEedRAOBuNRxPAv/bz5ZXCcbuf8AzLaYg==:1000:vo2IkE270qC7lKtbOjenvuAG6ddT1JVIo+uu+qpt6skvw99qELnBjQKNUJoJrlg3IZ6UwbIRlDbUMwcBi88eewvV3nAE9NYPdsHmAUqexdpyhIiakXRXRePc2VtDTnTF2mePGiJx30FP9Mi0V8pxH1qYSTM/Z9SJX9VlWy6f3gs1EFMZHHAD1WwUR1gA/Jq24xaKyiwvt48GHU85aLLH75mTWhCByf5k4nR7R8Kc+H0=;_pxvid=00692951-e181-11ed-a499-ebf9b9755f04;pxcts=006939ed-e181-11ed-a499-537250516c45;', "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue

			if data["attachments"]["events"][str(gameId)]["inPlay"]:
				continue

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				runners = data["attachments"]["markets"][market]["runners"]

				if marketName in ["both teams to score", "to score or assist", "anytime goalscorer", "anytime assist", "tie no bet", "match shots on target"] or "over/under" in marketName or marketName.startswith("player to have") or marketName.startswith("team to have") or "total corners" in marketName:

					prefix = ""
					if "1st half" in marketName or "first half" in marketName:
						prefix = "1h_"
					elif "each half" in marketName:
						prefix = "bh_"

					prop = ""
					if marketName == "both teams to score":
						prop = "btts"
					elif marketName == "anytime goalscorer":
						prop = "atgs"
					elif marketName == "tie no bet":
						prop = "dnb"
					elif marketName == "to score or assist":
						prop = "score_assist"
					elif marketName == "anytime assist":
						prop = "assist"
					elif "over/under" in marketName:
						if marketName.startswith("home team"):
							prop = "away_total"
						elif marketName.startswith("away team"):
							prop = "home_total"
						else:
							prop = "total"
					elif marketName.startswith("player to have"):
						prop = "player_shots"
						if "on target" in marketName:
							prop += "_on_target"
					elif marketName.startswith("team to have"):
						prop = "team_shots"
						if "on target" in marketName:
							prop += "_on_target"
					elif marketName == "match shots on target":
						prop = "game_shots_on_target"
					elif "total corners" in marketName:
						if marketName.startswith("home"):
							prop = "away_corners"
						elif marketName.startswith("away"):
							prop = "home_corners"
						else:
							prop = "corners"
					else:
						continue

					prop = f"{prefix}{prop}"

					if prop not in ["btts", "dnb"] and prop not in lines[game]:
						lines[game][prop] = {}

					if prop in ["score_assist", "assist", "atgs"] or "shots" in prop:
						skip = 1
						for i in range(0, len(runners), skip):
							runner = runners[i]
							player = parsePlayer(runner["runnerName"])

							if runner["runnerStatus"] == "SUSPENDED":
								continue
							if "team_shots" in prop:
								player = "away" if player == away else "home"

							try:
								ou = str(runner['winRunnerOdds']['americanDisplayOdds']['americanOdds'])
							except:
								continue
							if skip == 2:
								ou += "/"+str(runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds'])

							if "team_shots" in prop:
								if prop in lines[game]:
									del lines[game][prop]
								p = (player+"_"+prop).replace("_team", "")
								if p not in lines[game]:
									lines[game][p] = {}
								handicap = str(float(marketName.split(" ")[3]) - 0.5)
								lines[game][p][handicap] = ou
							elif "player_shots" in prop:
								handicap = str(float(marketName.split(" ")[3]) - 0.5)
								if player not in lines[game][prop]:
									lines[game][prop][player] = {}
								lines[game][prop][player][handicap] = ou
							elif prop == "game_shots_on_target":
								handicap = str(float(runner["runnerName"].split(" ")[0]) - 0.5)
								lines[game][prop][handicap] = ou
							elif prop == "assist":
								if player not in lines[game][prop]:
									lines[game][prop][player] = {}
								lines[game][prop][player]["0.5"] = ou
							else:
								lines[game][prop][player] = ou
					else:
						for i in range(0, len(runners), 2):
							handicap = ""
							try:
								if "corners" in prop:
									handicap = marketName.split(" ")[-1]
								else:
									handicap = marketName.split(" ")[-2]
							except:
								pass

							try:
								ou = f"{runners[i]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"
							except:
								continue
							if runners[i]["runnerName"].startswith("Under"):
								ou = f"{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[i]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"

							if prop in ["btts", "dnb"]:
								lines[game][prop] = ou
							else:
								lines[game][prop][handicap] = ou
	
	with open(f"static/soccer/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr", sharp=False):

	prefix = ""
	if sharp:
		prefix = "pn_"
	if player not in evData:
		evData[player] = {}

	impliedOver = impliedUnder = 0
	over = int(ou.split("/")[0])
	if over > 0:
		impliedOver = 100 / (over+100)
	else:
		impliedOver = -1*over / (-1*over+100)

	bet = 100
	profit = finalOdds / 100 * bet
	if finalOdds < 0:
		profit = 100 * bet / (finalOdds * -1)

	if "/" not in ou:
		ev = impliedOver * profit + (1-impliedOver) * -1 * bet
		ev = round(ev, 1)
	else:
		under = int(ou.split("/")[1])
		if under > 0:
			impliedUnder = 100 / (under+100)
		else:
			impliedUnder = -1*under / (-1*under+100)

		x = impliedOver
		y = impliedUnder
		while round(x+y, 8) != 1.0:
			k = math.log(2) / math.log(2 / (x+y))
			x = x**k
			y = y**k

		dec = 1 / x
		if dec >= 2:
			fairVal = round((dec - 1)  * 100)
		else:
			fairVal = round(-100 / (dec - 1))
		#fairVal = round((1 / x - 1)  * 100)
		implied = round(x*100, 2)
		#ev = round(x * (finalOdds - fairVal), 1)

		#multiplicative 
		mult = impliedOver / (impliedOver + impliedUnder)
		add = impliedOver - (impliedOver+impliedUnder-1) / 2

		evs = []
		for method in [x, mult, add]:
			ev = method * profit + (1-method) * -1 * bet
			ev = round(ev, 1)
			evs.append(ev)

		ev = min(evs)

		evData[player][f"{prefix}fairVal"] = fairVal
		evData[player][f"{prefix}implied"] = implied
	
	evData[player][f"{prefix}ev"] = ev

def writeDK(date):
	url = "https://sportsbook.draftkings.com/leagues/soccer/champions-league"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 490,
		"goalscorer": 537,
		"shots/assists": 1113,
		"game props": 540,
		"team props": 541,
		"corners": 543
	}

	subCats = {
		490: [6497, 13171, 13170],
		537: [4690, 11783],
		1113: [11004, 11005, 11006, 12377],
		540: [5645],
		543: [4846, 4849, 4845, 5462]
	}

	subCatProps = {
		6497: "dnb", 13171: "total", 13170: "spread", 4690: "atgs", 11783: "score_assist", 11004: "player_shots_on_target", 11005: "player_shots", 11006: "assist", 12377: "bh_player_shots_on_target", 5645: "btts", 4846: "corners", 4845: "1h_corners", 5462: "2h_corners"
	}

	if False:
		mainCats = {"corners": 543}
		subCats = {543: [4846, 4849, 4845, 5462]}

	lines = {}
	fullGame = {}
	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)["dk"]

	for league in leagues:
		for mainCat in mainCats:
			for subCat in subCats.get(mainCats[mainCat], [0]):
				time.sleep(0.3)
				url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/{league}/categories/{mainCats[mainCat]}"
				if subCat:
					url += f"/subcategories/{subCat}"
				url += "?format=json"
				outfile = "outsoccer"
				call(["curl", "-k", url, "-o", outfile])

				with open(outfile) as fh:
					data = json.load(fh)

				events = {}
				if "eventGroup" not in data:
					continue

				for event in data["eventGroup"]["events"]:
					start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
					startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=4)
					if startDt.day != int(date[-2:]):
						continue
						pass
					game = event["name"].lower().replace(" vs ", " @ ")
					away, home = map(str, game.split(" @ "))
					game = f"{convertTeam(away)} @ {convertTeam(home)}"
					fullGame[game] = event["name"].lower().replace(" vs ", " @ ")
					if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
						continue

					if game not in lines:
						lines[game] = {}

					events[event["eventId"]] = game

				for catRow in data["eventGroup"]["offerCategories"]:
					if catRow["offerCategoryId"] != mainCats[mainCat]:
						continue
					if "offerSubcategoryDescriptors" not in catRow:
						continue
					for cRow in catRow["offerSubcategoryDescriptors"]:
						if "offerSubcategory" not in cRow:
							continue
						for offerRow in cRow["offerSubcategory"]["offers"]:
							for row in offerRow:
								try:
									game = events[row["eventId"]]
								except:
									continue

								away, home = map(str, fullGame[game].split(" @ "))

								if "label" not in row:
									continue

								label = row["label"].lower().split(" [")[0]

								if subCatProps.get(subCat, ""):
									label = subCatProps[subCat]
								else:
									if "team total goals" in label:
										if label.startswith(away):
											label = "away_total"
										else:
											label = "home_total"
									elif "team total corners" in label:
										if label.startswith(away):
											label = "away_corners"
										else:
											label = "home_corners"

								if label in ["dnb", "btts"]:
									if len(row['outcomes']) == 0:
										continue
									if row["label"].lower() == "both teams to score no draw":
										continue

									if len(row['outcomes']) == 1:
										continue
									lines[game][label] = f"{row['outcomes'][0]['oddsAmerican']}"
									lines[game][label] += f"/{row['outcomes'][1]['oddsAmerican']}"
								else:
									if label not in lines[game]:
										lines[game][label] = {}

									outcomes = row["outcomes"]
									skip = 1 if label in ["atgs", "score_assist", "assist"] or "shots" in label else 2
									for i in range(0, len(outcomes), skip):
										if skip == 1:
											try:
												line = parsePlayer(outcomes[i]["participant"])
											except:
												continue
											if not line:
												line = parsePlayer(outcomes[i]["label"])
											if "criterionName" in outcomes[i] and outcomes[i]["criterionName"] != "Anytime Scorer":
												continue
										else:
											try:
												line = str(outcomes[i]["line"])
											except:
												continue
										try:
											ou = str(outcomes[i]['oddsAmerican'])
											if skip == 2:
												ou += f"/{outcomes[i+1]['oddsAmerican']}"
												if outcomes[i]['label'] == 'Under':
													ou = f"{outcomes[i+1]['oddsAmerican']}/{outcomes[i]['oddsAmerican']}"

											if "shots" in label or label in ["assist"]:
												if line not in lines[game][label]:
													lines[game][label][line] = {}
												handicap = str(float(row["label"].split(" ")[3]) - 0.5)
												lines[game][label][line][handicap] = ou
											else:
												lines[game][label][line] = ou
										except:
											continue
								

	with open("static/soccer/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writePointsbet(date=None):
	url = "https://api.mi.pointsbet.com/api/v2/sports/soccer/events/nextup"
	outfile = f"socceroutPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	if not date:
		date = str(datetime.now())[:10]

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	#games = ["331623"]
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"socceroutPB"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		try:
			with open(outfile) as fh:
				data = json.load(fh)
		except:
			continue

		startDt = datetime.strptime(data["startsAt"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if startDt.day != int(date[-2:]):
			continue

		playerIds = {}
		try:
			filters = data["presentationData"]["presentationFilters"]
			for row in filters:
				playerIds[row["id"].split("-")[-1]] = parsePlayer(row["name"].lower())
			for row in data["presentationData"]["presentations"]:
				if row["columnTitles"] and "Anytime TD" in row["columnTitles"]:
					for r in row["rows"]:
						playerIds[r["rowId"].split("-")[-1]] = parsePlayer(r["title"].lower())

					break
		except:
			pass

		game = away = home= ""
		try:
			for market in data["fixedOddsMarkets"]:
				if market["eventName"].lower() == "draw no bet":
					away = market["outcomes"][0]["name"].lower()
					home = market["outcomes"][1]["name"].lower()
					game = f"{convertTeam(away)} @ {convertTeam(home)}"
					break
		except:
			continue

		res[game] = {}

		for market in data["fixedOddsMarkets"]:
			prop = market["name"].lower().split(" (")[0]
			playerProp = False

			prefix = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "2nd half" in prop:
				prefix = "2h_"

			if "&" in prop or "odd/even" in prop or "both halves" in prop or "number" in prop:
				continue
			if "draw no bet" in prop:
				prop = f"dnb"
			elif "both teams to score" in prop:
				if "and" in prop or "yes/no" in prop:
					continue
				prop = f"btts"
			elif "anytime goalscorer" in prop:
				prop = f"atgs"
			elif "anytime goalscorer" in prop:
				prop = f"atgs"
			elif prop == "alternate spread" or "spread" in prop:
				if "-" in prop or "3 way" in prop:
					continue
				prop = "spread"
			elif prop.endswith("goals") or prop.endswith("total") or prop.endswith("total 1st half") or prop.endswith("total 2nd half"):
				if "exact" in prop or "+" in prop:
					continue
				if prop in [f"1st half {away} total goals", f"1st half {home} total goals", f"2nd half {away} total goals", f"2nd half {home} total goals"]:
					continue
				if away in prop:
					prop = "away_total"
				elif home in prop:
					prop = "home_total"
				else:
					prop = "total"
			elif "total corners" in prop:
				if "exact" in prop:
					continue
				if away in prop:
					prop = "away_corners"
				elif home in prop:
					prop = "home_corners"
				else:
					prop = "corners"
			elif "total assists" in prop:
				playerProp = True
				prop = "assist"
			elif "total passes" in prop:
				playerProp = True
				prop = "player_passes"
			elif "total shots" in prop:
				playerProp = True
				suffix = ""
				if "outside" in prop:
					suffix += "_outside_box"
				if "on target" in prop:
					suffix += "_on_target"

				if "player" in prop:
					prop = "player_shots"
				else:
					prop = "total_shots"
				prop += suffix
			else:
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			outcomes = market["outcomes"]
			skip = 1 if prop in ["atgs", "assist", "player_passes"] or "shots" in prop else 2
			for i in range(0, len(outcomes), skip):
				if outcomes[i]["price"] == 1:
					continue
				over = convertAmericanOdds(outcomes[i]["price"])
				under = ""
				try:
					if skip == 2:
						under = convertAmericanOdds(outcomes[i+1]["price"])
				except:
					pass
				ou = f"{over}"

				if under:
					ou += f"/{under}"
					if outcomes[i]["name"].startswith("Under") or outcomes[i]["name"] == "No":
						ou = f"{under}/{over}"
					elif prop == "spread" and outcomes[i]["side"] == "Away":
						ou = f"{under}/{over}"

				ou = ou.replace("Even", "100")

				if "btts" in prop or "dnb" in prop:
					res[game][prop] = ou
				else:
					if prop not in res[game]:
						res[game][prop] = {}

					if playerProp:
						try:
							player = playerIds[outcomes[i]["playerId"]]
						except:
							continue
						if player not in res[game][prop]:
							res[game][prop][player] = {}
						points = str(float(outcomes[i]["points"]) - 0.5)
						#if player == "emile smith rowe":
						#	print(prop, points, ou, market["name"])
						res[game][prop][player][points] = ou
					elif prop in ["atgs"]:
						try:
							player = playerIds[outcomes[i]["playerId"]]
						except:
							continue
						res[game][prop][player] = ou
					else:
						points = str(float(outcomes[i]["points"]))
						if points == "0.0":
							continue
						res[game][prop][points] = ou

	with open("static/soccer/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B13/C20904590/D7/E83/F4/"

	js = """
	
	const data = {};

	{
		for (const main of document.querySelectorAll(".gl-MarketGroupContainer")) {
			let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
			let prop = title.replace("moneyline", "ml");

			if (prop == "team corners") {
				prop = "corners";
			}

			if (["set", "total_sets", "set1_total", "away_total"].indexOf(prop) >= 0) {
				for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
					let game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" vs ", " @ ").replaceAll(".", "").replaceAll("/", " / ");
					let away = game.split(" @ ")[0];
					let home = game.split(" @ ")[1];
					if (away.indexOf(" / ") >= 0) {
						let away1 = away.split(" / ")[0];
						let away2 = away.split(" / ")[1];
						let home1 = home.split(" / ")[0];
						let home2 = home.split(" / ")[1];
						game = away1.split(" ")[away1.split(" ").length - 1]+" / "+away2.split(" ")[away2.split(" ").length - 1]+" @ "+home1.split(" ")[home1.split(" ").length - 1]+" / "+home2.split(" ")[home2.split(" ").length - 1];
					} else {
						away = away.split(" ")[away.split(" ").length - 1];
						home = home.split(" ")[home.split(" ").length - 1];
						game = away+" @ "+home;
					}

					if (data[game] === undefined) {
						data[game] = {};
					}

					if (div.classList.contains("src-FixtureSubGroup_Closed")) {
						div.click();
					}

					if (prop == "away_total") {
						let ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[0].innerText.replace("Over ", "");
						
						data[game]["away_total"] = {};
						data[game]["away_total"][ou] = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[0].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[1].innerText;

						ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[2].innerText.replace("Over ", "");
						data[game]["home_total"] = {};
						data[game]["home_total"][ou] = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[2].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[3].innerText;
					} else if (prop == "total_sets") {
						data[game][prop] = {};

						let ou = div.querySelectorAll(".gl-Participant_General")[1].querySelector(".gl-ParticipantBorderless_Odds").innerText+"/"+div.querySelectorAll(".gl-Participant_General")[0].querySelector(".gl-ParticipantBorderless_Odds").innerText;
						data[game][prop]["2.5"] = ou;
					} else {
						data[game][prop] = {};
						let arr = [];
						for (const set of div.querySelector(".gl-Market").querySelectorAll(".gl-Market_General-cn1")) {
							arr.push(set.innerText);
						}

						let idx = 0;
						for (const playerDiv of div.querySelectorAll(".gl-Participant_General")) {
							let set = arr[idx % arr.length];
							const odds = playerDiv.querySelector(".gl-ParticipantOddsOnly_Odds").innerText;

							if (prop == "set") {
								if (idx >= arr.length) {
									let s1 = set.split("-")[0];
									let s2 = set.split("-")[1];
									set = s2+"-"+s1;
								}
								
								data[game][prop][set] = odds;
							} else {
								if (idx < arr.length) {
									data[game][prop][set] = odds;
								} else {
									data[game][prop][set] += "/"+odds;
								}
							}
							idx += 1;
						}
					}
				}
			} else {
				let games = [];
				let idx = 0;
				for (div of main.querySelector(".gl-Market_General").children) {
					if (idx === 0 || div.classList.contains("Hidden")) {
						idx += 1;
						continue;
					}
					if (div.classList.contains("rcl-MarketHeaderLabel-isdate")) {
						//break;
						continue;
					}
					let away = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[0].innerText.toLowerCase().replaceAll(".", "");
					let home = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[1].innerText.toLowerCase().replaceAll(".", "");
					let game = (away+" @ "+home).replaceAll("/", " / ");
					if (away.indexOf("/") >= 0) {
						let away1 = away.split("/")[0];
						let away2 = away.split("/")[1];
						let home1 = home.split("/")[0];
						let home2 = home.split("/")[1];
						game = away1.split(" ")[away1.split(" ").length - 1]+" / "+away2.split(" ")[away2.split(" ").length - 1]+" @ "+home1.split(" ")[home1.split(" ").length - 1]+" / "+home2.split(" ")[home2.split(" ").length - 1];
					} else {
						away = away.split(" ")[away.split(" ").length - 1];
						home = home.split(" ")[home.split(" ").length - 1];
						game = away+" @ "+home;
					}
					games.push(game);

					if (!data[game]) {
						data[game] = {};
					}
				}

				idx = 0;
				let divs = main.querySelectorAll(".gl-Market_General")[1].querySelectorAll(".gl-Participant_General");
				for (let i = 0; i < divs.length; i += 1) {
					let game = games[idx];

					if (!game) {
						break;
					}

					if (prop.indexOf("ml") >= 0) {
						let odds = divs[i].querySelector(".sgl-ParticipantOddsOnly80_Odds").innerText;
						data[game][prop] = odds;
					} else {
						let line = divs[i].querySelector(".src-ParticipantCenteredStacked80_Handicap").innerText;
						let odds = divs[i].querySelector(".src-ParticipantCenteredStacked80_Odds").innerText;
						if (!data[game][prop]) {
							data[game][prop] = {};
						}
						line = parseFloat(line).toString();
						data[game][prop][line] = odds;
					}
					idx += 1;
				}

				idx = 0;
				divs = main.querySelectorAll(".gl-Market_General")[2].querySelectorAll(".gl-Participant_General");
				for (let i = 0; i < divs.length; i += 1) {
					let game = games[idx];

					if (!game) {
						break;
					}

					if (prop.indexOf("ml") >= 0) {
						let odds = divs[i].querySelector(".sgl-ParticipantOddsOnly80_Odds").innerText;
						data[game][prop] += "/"+odds;
					} else {
						let line = divs[i].querySelector(".src-ParticipantCenteredStacked80_Handicap").innerText;
						let odds = divs[i].querySelector(".src-ParticipantCenteredStacked80_Odds").innerText;
						if (prop.indexOf("spread") >= 0) {
							line = (parseFloat(line) * -1).toString();
						} else {
							line = parseFloat(line).toString();
						}

						data[game][prop][line] += "/"+odds;
					}
					idx += 1;
				}
			}
		}
		console.log(data);
	}

	"""
	pass

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None, singles=None, doubles=None):
	if not boost:
		boost = 1

	with open(f"{prefix}static/soccer/draftkings.json") as fh:
		dkLines = json.load(fh)

	#with open(f"{prefix}static/soccer/bet365.json") as fh:
	#	bet365Lines = json.load(fh)

	with open(f"{prefix}static/soccer/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/soccer/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/soccer/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/soccer/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/soccer/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/soccer/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/soccer/ev.json") as fh:
		evData = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		#"bet365": bet365Lines,
		#"cz": czLines
	}

	evData = {}
	for game in fdLines:
		if teamArg and teamArg not in game:
			continue

		#print(game)

		try:
			team1, team2 = map(str, game.split(" @ "))
		except:
			continue

		props = {}
		for book in lines:
			if game not in lines[book]:
				continue
			for prop in lines[book][game]:
				props[prop] = 1

		for prop in props:

			if propArg and prop != propArg:
				continue

			handicaps = {}
			for book in lines:
				lineData = lines[book]
				if game in lineData and prop in lineData[game]:
					if type(lineData[game][prop]) is not dict:
						handicaps[("", "")] = ""
						break
					for handicap in lineData[game][prop]:
						player = playerHandicap = ""
						try:
							player = float(handicap)
							player = ""
							handicaps[(handicap, playerHandicap)] = player
						except:
							player = handicap
							playerHandicap = ""
							if type(lineData[game][prop][player]) is dict:
								for h in lineData[game][prop][player]:
									handicaps[(handicap, h)] = player
							else:
								if " " in lineData[game][prop][player]:
									playerHandicap = lineData[game][prop][player].split(" ")[0]
								handicaps[(handicap, playerHandicap)] = player

			for handicap, playerHandicap in handicaps:
				player = handicaps[(handicap, playerHandicap)]

				for i in range(2):
					highestOdds = []
					books = []
					odds = []

					for book in lines:
						lineData = lines[book]
						if game in lineData and prop in lineData[game]:

							if type(lineData[game][prop]) is not dict:
								val = lineData[game][prop]
							else:
								if handicap not in lineData[game][prop]:
									continue
								val = lineData[game][prop][handicap]

								if player:
									if type(val) is dict:
										if playerHandicap not in val:
											continue
										val = lineData[game][prop][handicap][playerHandicap]
									else:
										if prop not in ["atgs", "goal_assist"] and playerHandicap != val.split(" ")[0]:
											continue
										val = lineData[game][prop][handicap].split(" ")[-1]

							try:
								o = val.split(" ")[-1].split("/")[i]
								ou = val.split(" ")[-1]
							except:
								if i == 1:
									continue
								o = val
								ou = val

							if not o:
								continue
							highestOdds.append(int(o))
							odds.append(ou)
							books.append(book)

					if len(books) < 2:
						continue

					kambi = ""
					try:
						bookIdx = books.index("kambi")
						kambi = odds[bookIdx]
						odds.remove(kambi)
						books.remove("kambi")
					except:
						pass

					pn = ""
					try:
						bookIdx = books.index("pn")
						pn = odds[bookIdx]
						odds.remove(pn)
						books.remove("pn")
					except:
						pass

					bet365 = ""
					try:
						bookIdx = books.index("bet365")
						bet365 = odds[bookIdx]
						odds.remove(bet365)
						books.remove("bet365")
					except:
						pass

					evBook = ""
					l = odds
					if bookArg:
						if bookArg not in books:
							continue
						evBook = bookArg
						idx = books.index(bookArg)
						maxOU = odds[idx]
						try:
							line = maxOU.split("/")[i]
						except:
							continue
					else:
						maxOdds = []
						for odds in l:
							try:
								maxOdds.append(int(odds.split("/")[i]))
							except:
								maxOdds.append(-10000)

						if not maxOdds:
							continue

						maxOdds = max(maxOdds)
						maxOU = ""
						for odds, book in zip(l, books):
							try:
								if str(int(odds.split("/")[i])) == str(maxOdds):
									evBook = book
									maxOU = odds
									break
							except:
								pass

						line = maxOdds

					line = convertAmericanOdds(1 + (convertDecOdds(int(line)) - 1) * boost)

					l.remove(maxOU)
					books.remove(evBook)
					if kambi:
						books.append("kambi")
						l.append(kambi)
					if pn:
						books.append("pn")
						l.append(pn)
					if bet365:
						books.append("bet365")
						l.append(bet365)

					avgOver = []
					avgUnder = []

					for book in l:
						if book:
							avgOver.append(convertDecOdds(int(book.split("/")[0])))
							if "/" in book:
								avgUnder.append(convertDecOdds(int(book.split("/")[1])))
					if avgOver:
						avgOver = float(sum(avgOver) / len(avgOver))
						avgOver = convertAmericanOdds(avgOver)
					else:
						avgOver = "-"
					if avgUnder:
						avgUnder = float(sum(avgUnder) / len(avgUnder))
						avgUnder = convertAmericanOdds(avgUnder)
					else:
						avgUnder = "-"

					if i == 1:
						ou = f"{avgUnder}/{avgOver}"
					else:
						ou = f"{avgOver}/{avgUnder}"

					if ou == "-/-" or ou.startswith("-/"):
						continue

					if ou.endswith("/-"):
						ou = ou.split("/")[0]

					if not line:
						continue

					key = f"{game} {prop} {handicap} {'over' if i == 0 else 'under'} {playerHandicap}"
					if key in evData:
						continue
					if True:
						pass
						devig(evData, key, ou, line, prop=prop)
						if pn:
							if i == 1:
								pn = f"{pn.split('/')[1]}/{pn.split('/')[0]}"
							devig(evData, key, pn, line, prop=prop, sharp=True)
						#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
						if key not in evData:
							print(key)
							continue
						if float(evData[key]["ev"]) > 0:
							#print(evData[key]["ev"], game, prop, handicap, int(line), ou, evBook, "\n\t", l)
							pass
						evData[key]["game"] = game
						evData[key]["player"] = player
						evData[key]["book"] = evBook
						evData[key]["books"] = books
						evData[key]["ou"] = ou
						evData[key]["under"] = i == 1
						evData[key]["odds"] = l
						evData[key]["line"] = line
						evData[key]["fullLine"] = maxOU
						evData[key]["handicap"] = handicap
						evData[key]["playerHandicap"] = playerHandicap
						evData[key]["prop"] = prop
						j = {b: o for o, b in zip(l, books)}
						j[evBook] = maxOU
						evData[key]["bookOdds"] = j

	with open(f"static/soccer/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def printEV(propArg):

	with open(f"static/soccer/ev.json") as fh:
		evData = json.load(fh)

	with open("static/soccer/corners.json") as fh:
		corners = json.load(fh)

	with open("static/soccer/totals.json") as fh:
		totals = json.load(fh)

	with open("static/soccer/winLoss.json") as fh:
		winLoss = json.load(fh)

	data = []
	for game in evData:
		d = evData[game]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], game, d["line"], d["book"], j, d))

	for row in sorted(data):
		if not propArg and (row[-1]["prop"] in ["atgs", "assist"] or "player_shots" in row[-1]["prop"]):
			continue
		print(row[:-1])

	output = "\t".join(["EV", "PN EV", "EV Book", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] not in ["atgs", "assist"] and "player_shots" not in row[-1]["prop"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], row[-1].get("pn_ev", "-"), str(row[-1]["line"])+" "+row[-1]["book"].upper(), row[-1]["game"], row[-1]["player"], row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/soccer/atgs.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "PN EV", "EV Book", "Game", "Prop", "O/U", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi"]) + "\n"
	for row in sorted(data, reverse=True):
		if "player_shots" in row[-1]["prop"] or row[-1]["prop"] in ["atgs", "assist", "dnb", "btts"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], row[-1].get("pn_ev", "-"), str(row[-1]["line"])+" "+row[-1]["book"].upper(), row[-1]["game"], row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))

		for team in row[-1]["game"].split(" @ "):
			if team in totals:
				f = a = t = ""
				if "corners" in row[-1]["prop"] and "corners" in totals[team]:
					f = round(sum(totals[team]["corners"]) / len(totals[team]["corners"]), 1)
					a = round(sum(totals[team]["opp_corners"]) / len(totals[team]["opp_corners"]), 1)
					t = round((sum(totals[team]["corners"]) + sum(totals[team]["opp_corners"])) / len(totals[team]["opp_corners"]), 1)
				elif "shots_on" in row[-1]["prop"] and "shots_on_target" in totals[team]:
					f = round(sum(totals[team]["shots_on_target"]) / len(totals[team]["shots_on_target"]), 1)
					a = round(sum(totals[team]["opp_shots_on_target"]) / len(totals[team]["opp_shots_on_target"]), 1)
					t = round((sum(totals[team]["shots_on_target"]) + sum(totals[team]["opp_shots_on_target"])) / len(totals[team]["opp_corners"]), 1)
				elif "shots" in row[-1]["prop"] and "total_shots" in totals[team]:
					f = round(sum(totals[team]["total_shots"]) / len(totals[team]["total_shots"]), 1)
					a = round(sum(totals[team]["opp_total_shots"]) / len(totals[team]["opp_total_shots"]), 1)
					t = round((sum(totals[team]["game_total_shots"])) / len(totals[team]["game_total_shots"]), 1)
				elif "total" in row[-1]["prop"] and "2h" not in row[-1]["prop"] and "total" in totals[team]:
					h = ""
					if "1h" in row[-1]["prop"]:
						h = "1h_"
					f = round(sum(totals[team][h+"total"]) / len(totals[team][h+"total"]), 1)
					a = round(sum(totals[team][h+"opp_total"]) / len(totals[team][h+"opp_total"]), 1)
					t = round((sum(totals[team][h+"game_total"])) / len(totals[team][h+"game_total"]), 1)
				if t:
					arr.append(f"{f} - {a} - {t}")
				else:
					arr.append("-")
			else:
				arr.append("-")

		if False and row[-1]["game"] in winLoss and row[-1]["prop"] in ["corners", "away_corners", "home_corners"]:
			wl = "L"
			cond = False

			if row[-1]["prop"] == "corners":
				cond = winLoss[row[-1]["game"]]["away"] + winLoss[row[-1]["game"]]["home"] < float(ou.split(" ")[-1])
			elif row[-1]["prop"] == "corners_spread":
				cond = winLoss[row[-1]["game"]]["away"] - winLoss[row[-1]["game"]]["home"] < float(ou.split(" ")[-1])
			else:
				cond = winLoss[row[-1]["game"]][row[-1]["prop"].split("_")[0]] < float(ou.split(" ")[-1])

			if (row[-1]["under"] and cond) or (not row[-1]["under"] and not cond):
				wl = "W"

			#arr.append(wl)
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/soccer/props.csv", "w") as fh:
		fh.write(output)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--avg", action="store_true", help="AVG")
	parser.add_argument("--all", action="store_true", help="ALL AVGs")
	parser.add_argument("--fd", action="store_true", help="Fanduel")
	parser.add_argument("--dk", action="store_true", help="Fanduel")
	parser.add_argument("--pb", action="store_true", help="Pointsbet")
	parser.add_argument("--writeBV", action="store_true", help="Bovada")
	parser.add_argument("--bv", action="store_true", help="Bovada")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("--mgm", action="store_true", help="MGM")
	parser.add_argument("--pn", action="store_true", help="Pinnacle")
	parser.add_argument("-p", "--print", action="store_true", help="Print")
	parser.add_argument("-g", "--game", help="Game")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("-k", "--k", action="store_true", help="Ks")
	parser.add_argument("--ml", action="store_true", help="Moneyline and Totals")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("--under", action="store_true", help="Under")
	parser.add_argument("--nocz", action="store_true", help="No CZ Lines")
	parser.add_argument("--no365", action="store_true", help="No 365 Devig")
	parser.add_argument("--nobr", action="store_true", help="No BR/Kambi lines")
	parser.add_argument("--dinger", action="store_true", help="Dinger Tues")
	parser.add_argument("--plays", action="store_true", help="Plays")
	parser.add_argument("--summary", action="store_true", help="Summary")
	parser.add_argument("--text", action="store_true", help="Text")
	parser.add_argument("--lineups", action="store_true", help="Lineups")
	parser.add_argument("--singles", action="store_true", help="Singles")
	parser.add_argument("--doubles", action="store_true", help="Doubles")
	parser.add_argument("--lineupsLoop", action="store_true", help="Lineups")
	parser.add_argument("--totals", action="store_true", help="Totals")
	parser.add_argument("--corners", action="store_true", help="Corners")
	parser.add_argument("--leagues", action="store_true", help="Leagues")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--player", help="Player")

	args = parser.parse_args()

	if args.leagues:
		writeLeagues(args.book)

	if args.totals:
		writeTotals(args.team)

	if args.corners:
		writeCorners()

	if args.fd:
		writeFanduel()

	if args.dk:
		writeDK(args.date)

	if args.kambi:
		writeKambi(args.date)

	if args.bv:
		writeBovada(args.date)

	if args.mgm:
		writeMGM(args.date)

	if args.pn:
		writePinnacle(args.date)

	if args.pb:
		writePointsbet(args.date)

	if args.update:
		writeFanduel()
		writeDK(args.date)
		writeBovada(args.date)
		writeKambi(args.date)
		writeMGM(args.date)
		writePointsbet(args.date)
		writePinnacle(args.date)

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, boost=args.boost, doubles=args.doubles, singles=args.singles, teamArg=args.team)

	if args.print:
		printEV(args.prop)