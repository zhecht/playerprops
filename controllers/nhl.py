
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

def convertFDTeam(team):
	if team.endswith("predators"):
		team = "nsh"
	elif team.endswith("lightning"):
		team = "tb"
	elif team.endswith("blackhawks"):
		team = "chi"
	elif team.endswith("penguins"):
		team = "pit"
	elif team.endswith("kraken"):
		team = "sea"
	elif team.endswith("knights"):
		team = "vgk"
	elif team.endswith("senators"):
		team = "ott"
	elif team.endswith("hurricanes"):
		team = "car"
	elif team.endswith("canadiens"):
		team = "mtl"
	elif team.endswith("leafs"):
		team = "tor"
	elif team.endswith("jets"):
		team = "wpg"
	elif team.endswith("flames"):
		team = "cgy"
	elif team.endswith("oilers"):
		team = "edm"
	elif team.endswith("canucks"):
		team = "van"
	elif team.endswith("avalanche"):
		team = "col"
	elif team.endswith("kings"):
		team = "la"
	elif team.endswith("wings"):
		team = "det"
	elif team.endswith("devils"):
		team = "nj"
	elif team.endswith("flyers"):
		team = "phi"
	elif team.endswith("jackets"):
		team = "cbj"
	elif team.endswith("rangers"):
		team = "nyr"
	elif team.endswith("sabres"):
		team = "buf"
	elif team.endswith("bruins"):
		team = "bos"
	elif team.endswith("panthers"):
		team = "fla"
	elif team.endswith("sharks"):
		team = "sj"
	elif team.endswith("coyotes"):
		team = "ari"
	elif team.endswith("capitals"):
		team = "wsh"
	elif team.endswith("islanders"):
		team = "nyi"
	elif team.endswith("wild"):
		team = "min"
	elif team.endswith("blues"):
		team = "stl"
	elif team.endswith("stars"):
		team = "dal"
	elif team.endswith("ducks"):
		team = "ana"
	return team

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

def getPropData(date=None, teams=""):
	if not date:
		date = str(datetime.now())[:10]

	with open(f"static/hockeyreference/totals.json") as fh:
		stats = json.load(fh)

	with open(f"static/hockeyreference/scores.json") as fh:
		scores = json.load(fh)

	with open(f"static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	with open(f"static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open("static/nhl/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open("static/nhl/draftkings.json") as fh:
		dkLines = json.load(fh)



actionNetworkBookIds = {
	1541: "draftkings",
	69: "fanduel",
	#15: "betmgm",
	283: "mgm",
	348: "betrivers",
	351: "pointsbet",
	355: "caesars"
}

def writeActionNetwork(dateArg = None):

	with open(f"{prefix}static/nhl/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	teamGame = {}
	for game in fdLines:
		away, home = map(str, game.split(" @ "))
		if away not in teamGame:
			teamGame[away] = game
		if home not in teamGame:
			teamGame[home] = game

	props = ["56_first_touchdown_scorer", "62_anytime_touchdown_scorer", "60_longest_completion", "59_longest_reception", "58_longest_rush", "30_passing_attempts", "10_pass_completions", "11_passing_tds", "9_passing_yards", "17_receiving_tds", "16_receiving_yards", "15_receptions", "18_rushing_attempts", "13_rushing_tds", "12_rushing_yards", "70_tackles_assists"]
	props = ["70_tackles_assists"]

	odds = {}
	optionTypes = {}

	if not dateArg:
		date = datetime.now()
		date = str(date)[:10]
	else:
		date = dateArg

	if datetime.now().hour > 21:
		date = str(datetime.now() + timedelta(days=1))[:10]

	for actionProp in props:
		time.sleep(0.2)
		path = f"nflout.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/1/props/core_bet_type_{actionProp}?bookIds=69,1541,283,348,351,355&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		prop = ""
		if "touchdown" in actionProp:
			prop = "ftd"
			if "anytime" in actionProp:
				prop = "attd"
		elif "tackles_assist" in actionProp:
			prop = "tackles+ast"
		else:
			prop = "_".join(actionProp.split("_")[1:]).replace("rushing", "rush").replace("passing", "pass").replace("receiving", "rec").replace("yards", "yd").replace("attempts", "att").replace("reception", "rec")
			if prop == "longest_completion":
				prop = "longest_pass"

		if prop.endswith("s"):
			prop = prop[:-1]

		with open(path) as fh:
			j = json.load(fh)

		if "markets" not in j or not j["markets"]:
			continue
		market = j["markets"][0]

		if "teams" not in market:
			continue

		for option in market["rules"]["options"]:
			optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

		teamIds = {}
		for row in market["teams"]:
			team = row["abbr"].lower()
			if team == "la":
				team = "lar"
			teamIds[row["id"]] = team

		playerIds = {}
		for row in market["players"]:
			playerIds[row["id"]] = parsePlayer(row["full_name"])

		books = market["books"]
		for bookData in books:
			bookId = bookData["book_id"]
			if bookId not in actionNetworkBookIds or not actionNetworkBookIds[bookId]:
				continue
				pass
			for oddData in bookData["odds"]:
				player = playerIds[oddData["player_id"]]
				team = teamIds[oddData["team_id"]]
				game = teamGame[team]
				overUnder = "over"
				try:
					overUnder = optionTypes[oddData["option_type_id"]]
				except:
					pass
				book = actionNetworkBookIds.get(bookId, "")
				value = str(oddData["value"])

				if game not in odds:
					odds[game] = {}
				if prop not in odds[game]:
					odds[game][prop] = {}
				if player not in odds[game][prop]:
					odds[game][prop][player] = {}

				if book not in odds[game][prop][player]:
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[game][prop][player][book] = f"{v}{oddData['money']}"
				elif overUnder == "over":
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[game][prop][player][book] = f"{v}{oddData['money']}/{odds[game][prop][player][book].replace(v, '')}"
				else:
					odds[game][prop][player][book] += f"/{oddData['money']}"
				sp = odds[game][prop][player][book].split("/")
				if odds[game][prop][player][book].count("/") == 3:
					odds[game][prop][player][book] = sp[1]+"/"+sp[2]

	with open(f"{prefix}static/nhl/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)


def writeCZ(date=None):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/icehockey/events/schedule/?competitionIds=b7b715a9-c7e8-4c47-af0a-77385b525e09"
	outfile = "nhloutCZ"
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"][:20]:
		games.append(event["id"])

	#games = ["41550ae2-bbd8-4c44-8e34-6b3e4e165025"]
	res = {}
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/events/{gameId}"
		time.sleep(0.2)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		#print(data["name"], data["startTime"])

		if str(datetime.strptime(data["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue

		game = data["name"].lower().replace("|", "").replace(" at ", " @ ")
		away, home = map(str, game.split(" @ "))
		game = f"{convertFDTeam(away)} @ {convertFDTeam(home)}"
		res[game] = {}

		for market in data["markets"]:
			if "name" not in market:
				continue

			if market["active"] == False:
				continue
			prop = market["name"].lower().replace("|", "").split(" (")[0]
			template = market["templateName"].lower().replace("|", "")

			prefix = player = ""
			playerProp = False
			if "1st period" in prop:
				prefix = "1p_"
			elif "2nd period" in prop:
				prefix = "2p_"
			elif "3rd period" in prop:
				prefix = "3p_"

			if prop in ["money line"]:
				prop = "ml"
			elif prop == "60 minutes betting":
				prop = "3-way"
			elif prop == "player to score a goal":
				prop = "atgs"
			elif "total saves" in prop:
				player = parsePlayer(prop.split(" total saves")[0])
				prop = "saves"
			elif "total shots" in prop:
				player = parsePlayer(prop.split(" total shots")[0])
				prop = "sog"
			elif "blocked shots" in prop:
				player = parsePlayer(prop.split(" blocked shots")[0])
				prop = "bs"
			elif prop.startswith("player to be credited"):
				if "power play" in prop:
					prop = "pp_pts"
				elif "assists" in prop:
					prop = "ast"
				elif "point" in prop:
					prop = "pts"
			elif "total goals" in prop or "total goals" in template:
				if "odd/even" in template:
					continue
				if template == "x team goals":
					if game.startswith(convertFDTeam(prop.split(" total")[0])):
						prop = "away_total"
					elif game.endswith(convertFDTeam(prop.split(" total")[0])):
						prop = "home_total"
				else:
					prop = "total"
			elif "puck line" in prop:
				prop = "spread"
			else:
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			selections = market["selections"]
			skip = 1 if prop in ["atgs", "ast", "pts", "pp_pts"] else 2
			if prop == "3-way":
				skip = 3
			mainLine = ""
			for i in range(0, len(selections), skip):
				try:
					ou = str(selections[i]["price"]["a"])
				except:
					continue
				if skip == 2:
					ou += f"/{selections[i+1]['price']['a']}"
					if selections[i]["name"].lower().replace("|", "") in ["under", "home"]:
						ou = f"{selections[i+1]['price']['a']}/{selections[i]['price']['a']}"

				if "ml" in prop:
					res[game][prop] = ou
				elif "3-way" in prop:
					res[game][prop] = f"{selections[0]['price']['a']}/{selections[-1]['price']['a']}"
				elif prop == "atgs":
					player = parsePlayer(selections[i]["name"].replace("|", ""))
					res[game][prop][player] = {
						"0.5": ou
					}
				elif prop in ["pts", "ast", "pp_pts"]:
					line = str(float(market["name"].split(" ")[5][1:]) - 0.5)
					player = parsePlayer(selections[i]["name"].replace("|", ""))
					if player not in res[game][prop]:
						res[game][prop][player] = {}
					res[game][prop][player][line] = ou
				elif "spread" in prop:
					line = str(float(market["line"]) * -1)
					mainLine = line
					res[game][prop][line] = ou
				elif "total" in prop:
					if "line" in market:
						line = str(float(market["line"]))
						if prop == "total":
							mainLine = line
						res[game][prop][line] = ou
					else:
						line = str(float(selections[i]["name"].split(" ")[-1]))
						if prop == "total":
							mainLine = line
						if line not in res[game][prop]:
							res[game][prop][line] = ou
						else:
							res[game][prop][line] += "/"+ou
				else:
					try:
						line = str(float(market["line"]))
					except:
						line = "0.5"
					res[game][prop][player] = {
						line: ou
					}

			#print(market["name"], prop, mainLine)
			if prop in ["spread", "total"]:
				try:
					linePrices = market["movingLines"]["linePrices"]
				except:
					continue
				for prices in linePrices:
					selections = prices["selections"]
					if prop == "spread":
						line = float(prices["line"])
						ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
						if selections[0]["selectionType"] == "home":
							line *= -1
							ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"
						line = str(line)
					else:
						line = str(float(prices["line"]))
						ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
						if selections[0]["selectionType"] == "under":
							ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"
					if line == mainLine:
						continue
					res[game][prop][line] = ou


	with open("static/nhl/caesars.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePointsbet(date=None):
	url = "https://api.mi.pointsbet.com/api/v2/competitions/1/events/featured?includeLive=false&page=1"
	outfile = f"nhloutPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for row in data["events"]:
		games.append(row["key"])

	if not date:
		date = str(datetime.now())[:10]

	#games = ["336956"]
	res = {}
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"nhloutPB"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		startDt = datetime.strptime(data["startsAt"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if startDt.day != int(date[-2:]):
			continue

		game = data["name"].lower()
		fullAway, fullHome = map(str, game.split(" @ "))
		game = convertFDTeam(f"{fullAway} @ {fullHome}")
		res[game] = {}

		playerIds = {}
		try:
			filters = data["presentationData"]["presentationFilters"]
			for row in filters:
				playerIds[row["id"].split("-")[-1]] = row["name"].lower()
			for row in data["presentationData"]["presentations"]:
				if row["columnTitles"] and "Anytime TD" in row["columnTitles"]:
					for r in row["rows"]:
						playerIds[r["rowId"].split("-")[-1]] = r["title"].lower()

					break
		except:
			pass

		for market in data["fixedOddsMarkets"]:
			prop = market["name"].lower().split(" (")[0]
			playerProps = False
			prefix = ""
			if "first 5 innings" in prop:
				prefix = "1p_"
			elif "first 3 innings" in prop:
				prefix = "2p_"
			elif "first 7 innings" in prop:
				prefix = "3p_"

			if prop.startswith("run line") or prop.startswith("alternate run line"):
				if "3-way" in prop or "bands" in prop or "exact" in prop or "odd/even" in prop:
					continue
				prop = f"{prefix}spread"
			elif prop.startswith("moneyline"):
				if "3-way" in prop or "pitchers" in market["eventClass"].lower():
					continue
				prop = f"{prefix}ml"
			elif prop.startswith("total runs") or prop.startswith("alternate total runs"):
				if "3-way" in prop or "bands" in prop or "exact" in prop or "odd/even" in prop:
					continue
				prop = "total"
				prop = f"{prefix}total"
			elif prop == f"{fullAway} total runs" or prop == f"{fullAway} alternate total runs":
				prop = f"{prefix}away_total"
			elif prop == f"{fullHome} total runs" or prop == f"{fullHome} alternate total runs":
				prop = f"{prefix}home_total"
			elif prop.startswith("player") or prop.startswith("pitcher"):
				playerProps = True
				p = prop.split(" ")[1]
				if "to get" in prop:
					continue
				if p == "home":
					prop = "hr"
				elif p == "hits":
					prop = "h"
				elif "runs batted in" in prop:
					prop = "rbi"
				elif p == "stolen":
					prop = "sb"
				elif p == "total":
					prop = "tb"
				elif p == "strikeouts":
					prop = "k"
				elif "win" in prop:
					prop = "w"
			else:
				continue

			if "ml" not in prop:
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			skip = 1 if False else 2
			for i in range(0, len(outcomes), skip):
				points = str(outcomes[i]["points"])
				if outcomes[i]["price"] == 1:
					continue
				over = convertAmericanOdds(outcomes[i]["price"])
				under = ""
				try:
					under = convertAmericanOdds(outcomes[i+1]["price"])
				except:
					pass
				ou = f"{over}"

				if under:
					ou += f"/{under}"

					if "ml" in prop and game.startswith(convertFDTeam(outcomes[i+1]["name"])):
						ou = f"{under}/{over}"

				if "ml" in prop:
					res[game][prop] = ou
				elif playerProps:
					#player = parsePlayer(outcomes[i]["name"].lower().split(" over")[0].split(" to ")[0])
					try:
						player = parsePlayer(playerIds[outcomes[i]["playerId"]])
					except:
						continue
					if prop == "w":
						res[game][prop][player] = f"{ou}"
					else:
						res[game][prop][player] = f"{outcomes[i]['name'].split(' ')[-1]} {ou}"
				else:
					if "spread" in prop and outcomes[i]["side"] == "Home":
						points = str(outcomes[i+1]["points"])
						ou = f"{under}/{over}"
					res[game][prop][points] = ou

	with open("static/nhl/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "nhloutPN"
	game = games[gameId]

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o nhloutPN'

	time.sleep(0.3)
	os.system(url)
	try:
		with open(outfile) as fh:
			related = json.load(fh)
	except:
		retry.append(gameId)
		return

	relatedData = {}
	for row in related:
		if "special" in row:
			prop = row["units"].lower()

			if prop == "goals":
				prop = "atgs"
			elif prop == "shotsongoal":
				prop = "sog"
			elif prop == "assists":
				prop = "ast"
			elif prop == "points":
				prop = "pts"
			else:
				continue

			over = row["participants"][0]["id"]
			under = row["participants"][1]["id"]
			if row["participants"][0]["name"] == "Under":
				over, under = under, over
			player = parsePlayer(row["special"]["description"].split(" (")[0])
			relatedData[row["id"]] = {
				"player": player,
				"prop": prop,
				"over": over,
				"under": under
			}

	if debug:
		with open("t", "w") as fh:
			json.dump(relatedData, fh, indent=4)

		with open("t2", "w") as fh:
			json.dump(related, fh, indent=4)

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o nhloutPN'

	time.sleep(0.3)
	os.system(url)
	try:
		with open(outfile) as fh:
			data = json.load(fh)
	except:
		retry.append(gameId)
		return

	if debug:
		with open("t3", "w") as fh:
			json.dump(data, fh, indent=4)

	res[game] = {}

	for row in data:
		prop = row["type"]
		try:
			keys = row["key"].split(";")
		except:
			continue

		prefix = ""

		overId = underId = 0
		player = ""
		if keys[1] == "1":
			prefix = "1p_"
		if keys[1] == "2":
			prefix = "2p_"
		elif keys[1] == "3":
			prefix = "3p_"

		if row["matchupId"] != int(gameId):
			if row["matchupId"] not in relatedData:
				continue
			player = relatedData[row["matchupId"]]["player"]
			prop = relatedData[row["matchupId"]]["prop"]
			overId = relatedData[row["matchupId"]]["over"]
			underId = relatedData[row["matchupId"]]["under"]
		else:
			if prop == "moneyline":
				prop = f"{prefix}ml"
				if keys[1] == "6":
					prop = f"3-way"
			elif prop == "spread":
				prop = f"{prefix}spread"
			elif prop == "total":
				prop = f"{prefix}total"
			elif prop == "team_total":
				awayHome = row['side']
				prop = f"{prefix}{awayHome}_total"

		if debug:
			print(prop, row["matchupId"], keys)

		prices = row["prices"]
		switched = 0
		if overId:
			try:
				ou = f"{prices[0]['price']}/{prices[1]['price']}"
			except:
				continue
			if prices[0]["participantId"] == underId:
				ou = f"{prices[1]['price']}/{prices[0]['price']}"
				switched = 1

			if prop not in res[game]:
				res[game][prop] = {}

			if "points" in prices[0] and prop not in []:
				handicap = str(float(prices[switched]["points"]))
				res[game][prop][player] = {
					handicap: ou
				}
			else:
				res[game][prop][player] = ou
		else:
			ou = f"{prices[0]['price']}/{prices[1]['price']}"
			if prices[0]["designation"] in ["home", "under"]:
				ou = f"{prices[1]['price']}/{prices[0]['price']}"
				switched = 1

			if "points" in prices[0]:
				handicap = str(float(prices[switched]["points"]))
				if prop not in res[game]:
					res[game][prop] = {}

				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

def writePinnacle(date):
	debug = False

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/hockey/nhl/matchups#period:0"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/1456/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o nhloutPN'

	os.system(url)
	outfile = f"nhloutPN"
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	for row in data:
		if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
		if row["type"] == "matchup" and not row["parent"]:
			player1 = row["participants"][0]["name"].lower()
			player2 = row["participants"][1]["name"].lower()
			games[str(row["id"])] = f"{convertFDTeam(player2)} @ {convertFDTeam(player1)}"

	#games = {'1580049987': 'ari @ nj'}
	res = {}
	retry = []
	for gameId in games:
		parsePinnacle(res, games, gameId, retry, debug)

	for gameId in retry:
		parsePinnacle(res, games, gameId, retry, debug)

	with open("static/nhl/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBV():
	url = "https://www.bovada.lv/sports/hockey/nhl"

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/hockey/nhl?marketFilterId=def&liveOnly=False&eventsLimit=5000&lang=en"
	outfile = f"nhloutBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	ids = [r["link"] for r in data[0]["events"]]

	res = {}
	#ids = ["/hockey/nhl/seattle-kraken-nashville-predators-202310122000"]
	for link in ids:
		if "goals" in link:
			continue
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)

		os.system(f"curl \"{url}\" --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0' -H 'Accept: application/json, text/plain, */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://www.bovada.lv/' -H 'X-CHANNEL: desktop' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'X-SPORT-CONTEXT: ' -H 'Connection: keep-alive' -H 'Cookie: Device-Type=Desktop|false; LANG=en; AB=variant; VISITED=true; affid=14995; JOINED=true; url-prefix=/; ln_grp=1; odds_format=AMERICAN; TSD4E5KQ1M=T5mCLsoZdxfxCbEQD4qVATcG0sKVJAEQ; variant=v:0|lgn:0|dt:d|os:w|cntry:US|cur:USD|jn:1|rt:o|pb:0; JSESSIONID=79EAD6CF313245D69DB5B4BAFE4325BF; TS01ed9118=014b5d5d077747c6c55fa8f9f0eed7c4ffb9827efa99f5edf3213c3de6b0106b0501b972a707dab0397a11c3f2813e791df962eca970ba71e00ace4d692d2fb3aee5d1cc0c7696d376fab4329dbde7037083ba5f81342b1138c2b7fc149c52438ad4a4c5cc' -H 'TE: trailers' -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		#print(url)

		comp = data[0]['events'][0]['competitors']
		game = data[0]['events'][0]['description'].lower()
		if "@" not in game:
			continue
		fullAway, fullHome = game.split(" @ ")
		game = f"{convertFDTeam(fullAway)} @ {convertFDTeam(fullHome)}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "player props", "goalscorers", "shots on goal"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["description"].lower() == "1st period":
						prefix = "1p_"
					elif market["period"]["description"].lower() == "2nd period":
						prefix = "2p_"
					elif market["period"]["description"].lower() == "3rd period":
						prefix = "3p_"

					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "3-way moneyline":
						prop = "3-way"
					elif prop == "total":
						prop = "total"
						if market["period"]["abbreviation"] == "RT":
							continue
					elif prop == "spread":
						prop = "spread"
						if market["period"]["abbreviation"] == "RT":
							continue
					elif prop == f"total goals o/u - {fullAway}":
						prop = "away_total"
					elif prop == f"total goals o/u - {fullHome}":
						prop = "home_total"
					elif prop == "anytime goalscorer":
						prop = "atgs"
					elif prop.startswith("total saves"):
						prop = "saves"
					elif prop.startswith("total shots on goal"):
						prop = "sog"
					elif prop.startswith("player to record"):
						if "powerplay" in prop:
							prop = "pp_pts"
						elif "points" in prop:
							prop = "pts"
						elif "assists" in prop:
							prop = "ast"
					else:
						continue

					prop = f"{prefix}{prop}"

					if not len(market["outcomes"]):
						continue

					if "ml" not in prop and prop not in res[game]:
						res[game][prop] = {}

					if "ml" in prop or "3-way" in prop:
						res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
					elif "total" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
								if market["outcomes"][i]["description"] == "Under":
									ou = f"{market['outcomes'][i+1]['price']['american']}/{market['outcomes'][i]['price']['american']}".replace("EVEN", "100")
								handicap = market["outcomes"][i]["price"]["handicap"]
							except:
								continue
							#print(handicap, ou)
							res[game][prop][handicap] = ou
					elif "spread" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							except:
								continue
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif prop in ["saves", "sog"]:
						try:
							handicap = market["outcomes"][0]["price"]["handicap"]
							player = parsePlayer(market["description"].split(" - ")[-1].split(" (")[0])
							ou = f"{market['outcomes'][0]['price']['american']}"
							if len(market["outcomes"]) > 1:
								ou += f"/{market['outcomes'][1]['price']['american']}"
							res[game][prop][player] = {
								handicap: f"{ou}".replace("EVEN", "100")
							}
						except:
							continue
					else:
						for i in range(0, len(market["outcomes"]), 1):
							player = parsePlayer(market['outcomes'][i]["description"].split(" - ")[-1].split(" (")[0])
							player = " ".join([x for x in player.split(" ") if x])
							if prop == "atgs":
								handicap = "0.5"
							else:
								handicap = str(float(market["description"].split(" ")[3].replace("+", "")) - 0.5)
							ou = f"{market['outcomes'][i]['price']['american']}"
							if not player:
								continue
							if player not in res[game][prop]:
								res[game][prop][player] = {}
							res[game][prop][player][handicap] = ou.replace("EVEN", "100")


	with open("static/nhl/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM(date=None):

	res = {}

	if not date:
		date = str(datetime.now())[:10]

	url = "https://sports.mi.betmgm.com/en/sports/hockey-12/betting/usa-9/nhl-34"

	url = f"https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=12&regionId=9&competitionId=34&compoundCompetitionId=1:34&widgetId=/mobilesports-v1.0/layout/layout_us/modules/competition/defaultcontainereventsfutures-redesign&shouldIncludePayload=true"
	outfile = f"outMGM"

	time.sleep(0.3)
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	rows = data["widgets"][0]["payload"]["items"][0]["activeChildren"][0]["payload"]["fixtures"]
	ids = []
	for row in rows:
		if row["stage"].lower() == "live":
			continue
		if "2023/2024" in row["name"]["value"] or "2023/24" in row["name"]["value"]:
			continue

		if str(datetime.strptime(row["startDate"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
		ids.append(row["id"])

	#ids = ["14476196"]
	for mgmid in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		data = data["fixture"]

		if " at " not in data["name"]["value"]:
			continue
		game = strip_accents(data["name"]["value"].lower()).replace(" at ", " @ ")
		fullTeam1, fullTeam2 = game.split(" @ ")
		game = f"{convertFDTeam(fullTeam1)} @ {convertFDTeam(fullTeam2)}"

		res[game] = {}
		for row in data["games"]:
			prop = row["name"]["value"].lower()

			prefix = player = ""
			if "1st period" in prop:
				prefix = "1p_"
			elif "2nd period" in prop:
				prefix = "2p_"
			elif "3rd period" in prop:
				prefix = "3p_"

			if prop.endswith("money line"):
				prop = "ml"
			elif "totals" in prop:
				prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif "3-way" in prop:
				prop = "3-way"
			elif prop == "goalscorer (including overtime)":
				prop = "atgs"
			elif "how many saves" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "saves"
			elif "how many shots" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "sog"
			elif "how many points" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "pts"
			elif "how many powerplay points" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "pp_pts"
			elif "how many assists" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "ast"
			elif "how many blocked shots" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "bs"
			else:
				continue

			prop = prefix+prop

			results = row['results']
			if "ml" in prop:
				res[game][prop] = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
			elif "3-way" in prop:
				res[game][prop] = f"{results[0]['americanOdds']}/{results[-1]['americanOdds']}"
			elif len(results) >= 2:
				if prop not in res[game]:
					res[game][prop] = {}
				skip = 1 if prop == "atgs" else 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop and prop not in ["atgs"]:
						continue
					elif prop not in ["atgs"]:
						val = val.split(" ")[-1]
					
					#print(game, prop, player)
					ou = f"{results[idx]['americanOdds']}"

					try:
						if skip == 2:
							ou += f"/{results[idx+1]['americanOdds']}"
					except:
						pass

					if player:
						player = parsePlayer(player)
						res[game][prop][player] = {
							val: ou
						}
					elif prop == "atgs":
						res[game][prop][parsePlayer(val)] = ou
					else:
						try:
							v = str(float(val))
							res[game][prop][v] = ou
						except:
							pass

	with open("static/nhl/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi():
	data = {}
	outfile = f"outnhl.json"
	url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/ice_hockey/nhl"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/ice_hockey/nhl/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	fullTeam = {}
	eventIds = {}
	for event in j["events"]:
		game = event["event"]["name"].lower()
		away, home = map(str, game.split(" @ "))
		homeFull, awayFull = map(str, event["event"]["englishName"].lower().split(" - "))
		games = []
		for team, full in zip([away, home], [awayFull, homeFull]):
			t = team.split(" ")[0]
			if t == "vgs":
				t = "vgk"
			elif "rangers" in team:
				t = "nyr"
			elif "islanders" in team:
				t = "nyi"
			fullTeam[t] = full
			games.append(t)
		game = " @ ".join(games)
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	#eventIds = {'stl @ dal': 1019965185}
	#data['stl @ dal'] = {}
	#print(eventIds)
	#exit()
	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		awayFull, homeFull = fullTeam[away], fullTeam[home]
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		i = 0
		for betOffer in j["betOffers"]:
			playerProp = False
			label = betOffer["criterion"]["label"].lower()
			prefix = ""
			if "period 1" in label:
				prefix = "1p_"
			elif "period 2" in label:
				prefix = "2p_"
			elif "period 3" in label:
				prefix = "3p_"

			if "handicap" in label:
				if "regular time" in label:
					continue
				label = "spread"
			elif f"total goals by {awayFull}" in label:
				label = "away_total"
			elif f"total goals by {homeFull}" in label:
				label = "home_total"
			elif "total goals" in label:
				if "odd/even" in label or "regular time" in label or ":" in label:
					continue
				label = "total"
			elif label == "match":
				label = "ml"
			elif label == "match odds":
				label = "3-way"
			elif label == "first team to score":
				label = "first_score"
			elif label == "to score - including overtime":
				label = "atgs"
				playerProp = True
			elif "points - " in label:
				label = "pts"
				playerProp = True
			elif "power play point - " in label:
				label = "pp_pts"
				playerProp = True
			elif "by the player" in label:
				playerProp = True
				label = "_".join(label.split(" by the player")[0].split(" "))

				if label == "shots_on_goal":
					label = "sog"
			else:
				#print(label)
				continue

			label = f"{prefix}{label}"

			if "oddsAmerican" not in betOffer["outcomes"][0]:
				continue

			try:
				ou = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
			except:
				ou = betOffer["outcomes"][0]["oddsAmerican"]
			player = ""
			if playerProp:
				player = parsePlayer(betOffer["outcomes"][0]["participant"])
				try:
					last, first = map(str, player.split(", "))
					player = f"{first} {last}"
				except:
					pass
			if "ml" in label:
				data[game][label] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label == "3-way":
				data[game][label] = betOffer["outcomes"][-1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			else:
				if label not in data[game]:
					data[game][label] = {}
				if not playerProp:
					#print(betOffer["criterion"]["label"], label)
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer["outcomes"][0]["label"] == "Under" or convertFDTeam(betOffer["outcomes"][0]["label"].lower()) == home:
						line = str(float(line) * -1)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]

					data[game][label][line] = ou
				else:
					if label in ["sog"]:
						line = betOffer["outcomes"][0]["label"].split(" ")[-1]
					else:
						try:
							line = str(betOffer["outcomes"][0]["line"] / 1000)
						except:
							line = "0.5"
					if betOffer["outcomes"][0]["label"].split(" ")[0] in ["Under", "No"]:
						if label not in ["sog"]:
							line = str(betOffer["outcomes"][1]["line"] / 1000)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]

					if player not in data[game][label]:
						data[game][label][player] = {}

					if label == "atgs":
						line = "0.5"
					elif label in ["pts"]:
						line = str(float(line) - 0.5)
					data[game][label][player][line] = ou


	with open(f"static/nhl/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")
	if player == "michael eyssimont":
		return "mikey eyssimont"
	return player

def writeFanduelManual():
	js = """

	let data = {};
	{

		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.toLowerCase().substring(0, 3);
			if (t == "was") {
				t = "wsh";
			} else if (t == "cal") {
				t = "cgy";
			} else if (t == "col" && team.indexOf("columbus") >= 0) {
				t = "cbj";
			} else if (t == "flo") {
				t = "fla";
			} else if (t == "los") {
				t = "la";
			} else if (t == "nas") {
				t = "nsh";
			} else if (t == "mon") {
				t = "mtl";
			} else if (t == "new") {
				t = "nj";
				if (team.indexOf("rangers") > 0) {
					t = "nyr";
				} else if (team.indexOf("island") > 0) {
					t = "nyi";
				}
			} else if (t == "san") {
				t = "sj";
			} else if (t == "tam") {
				t = "tb";
			} else if (t == "st.") {
				t = "stl";
			} else if (t == "veg") {
				t = "vgk";
			} else if (t == "win") {
				t = "wpg";
			}
			return t;
		}

		function parsePlayer(player) {
			player = player.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
			if (player == "michael eyssimont") {
				return "mikey eyssimont";
			}
			return player;
		}

		let game = document.querySelector("h1").innerText.toLowerCase().replace(" odds", "");
		let awayFull = game.split(" @ ")[0];
		let homeFull = game.split(" @ ")[1];
		let away = convertTeam(game.split(" @ ")[0]);
		let home = convertTeam(game.split(" @ ")[1]);
		game = away+" @ "+home;
		if (!data[game]) {
			data[game] = {};
		}

		const arrows = document.querySelectorAll("div[data-test-id='ArrowAction']");

		for (const arrow of arrows) {
			let li = arrow;
			let idx = 0;
			while (li.nodeName != "LI") {
				li = li.parentElement;
				idx += 1;
				if (idx > 10) {
					break;
				}
			}

			if (idx > 10) {
				break;
			}

			let prop = "";
			let line = "";
			let player = "";
			let label = arrow.innerText.toLowerCase();
			if (label.indexOf("game lines") >= 0) {
				prop = "lines";
			} else if (label.indexOf("any time goal scorer") >= 0) {
				prop = "atgs";
			} else if (label.indexOf("player to record") >= 0) {
				line = (parseFloat(label.split(" ")[3].replace("+", "")) - 0.5).toString();
				if (label.indexOf("shots on goal") > 0) {
					prop = "sog";
				} else if (label.indexOf("+ points") > 0) {
					prop = "pts";
				} else if (label.indexOf("+ powerplay points") > 0) {
					prop = "pp_pts";
				} else if (label.indexOf("+ assists") > 0) {
					prop = "ast";
				}
			} else if (label.indexOf("alternate puck line") >= 0) {
				prop = "spread";
			} else if (label.indexOf("alternate total goals") >= 0) {
				prop = "total";
			} else if (label.indexOf("total saves") >= 0) {
				player = parsePlayer(label.split(" -")[0]);
				prop = "saves";
			} else if (label.indexOf("shots on goal") >= 0) {
				player = parsePlayer(label.split(" shots")[0]);
				prop = "sog";
			} else if (label.indexOf(awayFull+" total goals") >= 0) {
				prop = "away_total";
			} else if (label.indexOf(homeFull+" total goals") >= 0) {
				prop = "home_total";
			}

			if (!prop) {
				continue;
			}

			if (arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
				arrow.click();
			}
			let el = arrow.parentElement.parentElement.querySelector("div[aria-label='Show more']");
			if (el) {
				el.click();
			}

			if (prop != "lines" && !data[game][prop]) {
				data[game][prop] = {};
			}

			let skip = 1;
			if (["saves", "away_total", "home_total"].indexOf(prop) >= 0) {
				skip = 2;
			} else if (prop == "sog" && player) {
				skip = 2;
			}
			let btns = Array.from(li.querySelectorAll("div[role=button]"));
			btns.shift();

			if (prop == "lines") {
				data[game]["ml"] = btns[1].getAttribute("aria-label").split(", ")[1].split(" ")[0]+"/"+btns[4].getAttribute("aria-label").split(", ")[1].split(" ")[0];
				line = btns[0].getAttribute("aria-label").split(", ")[1];
				data[game]["spread"] = {};
				data[game]["spread"][line.replace("+", "")] = btns[0].getAttribute("aria-label").split(", ")[2].split(" ")[0] + "/" + btns[3].getAttribute("aria-label").split(", ")[2].split(" ")[0];
				line = btns[2].getAttribute("aria-label").split(", ")[2].split(" ")[1];
				data[game]["total"] = {};
				data[game]["total"][line] = btns[2].getAttribute("aria-label").split(", ")[3].split(" ")[0] + "/" + btns[5].getAttribute("aria-label").split(", ")[3].split(" ")[0];
			}

			for (let i = 0; i < btns.length; i += skip) {
				const btn = btns[i];
				if (btn.getAttribute("data-test-id")) {
					continue;
				}
				const ariaLabel = btn.getAttribute("aria-label");
				if (ariaLabel == "Show more" || ariaLabel == "Show less") {
					continue;
				}
				let odds = ariaLabel.split(", ")[1];
				if (odds.indexOf("unavailable") >= 0) {
					continue;
				}
				if (prop == "lines") {

				} else if (["spread"].indexOf(prop) >= 0) {
					let arr = ariaLabel.split(", ")[0].split(" ");
					line = arr[arr.length - 1];
					arr.pop();
					let team = convertTeam(arr.join(" "));

					let isAway = true;
					if (team == game.split(" @ ")[1]) {
						line = (parseFloat(line) * -1).toString();
						isAway = false;
					}

					line = line.replace("+", "");

					if (isAway) {
						data[game][prop][line] = odds;
					} else if (!data[game][prop][line]) {
						data[game][prop][line] = "-/"+odds;
					} else {
						data[game][prop][line] += "/"+odds;
					}
				} else if (["total"].indexOf(prop) >= 0) {
					let arr = ariaLabel.split(", ")[0].split(" ");
					line = arr[arr.length - 1];

					let isAway = true;
					if (arr[0] == "Under") {
						isAway = false;
					}

					line = line.replace("+", "");

					if (isAway) {
						data[game][prop][line] = odds;
					} else if (!data[game][prop][line]) {
						data[game][prop][line] = "-/"+odds;
					} else {
						data[game][prop][line] += "/"+odds;
					}
				} else if (skip == 2 && player) {
					// 2 sides
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop][player][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
				} else if (skip == 2) {
					line = ariaLabel.split(", ")[2].split(" ")[1];
					odds = ariaLabel.split(", ")[3].split(" ")[0];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop] = {};
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
				} else {
					player = parsePlayer(ariaLabel.split(",")[0]);
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}

					if (["atgs"].indexOf(prop) >= 0) {
						data[game][prop][player] = odds;
					} else {
						data[game][prop][player][line] = odds;
					}
				}
			}
		}

		console.log(data);
	}

"""

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.getElementsByTagName("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/ice-hockey/nhl") >= 0) {
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
  "https://mi.sportsbook.fanduel.com/ice-hockey/nhl---matches/pittsburgh-penguins-@-detroit-red-wings-32725918"
]

	#games = ["https://mi.sportsbook.fanduel.com/ice-hockey/nhl---matches/nashville-predators-@-tampa-bay-lightning-32450515"]
	lines = {}
	for game in games:	
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away, home = map(str, game.split(" @ "))
		game = f"{convertFDTeam(away)} @ {convertFDTeam(home)}"
		lines[game] = {}

		outfile = "outnhl"

		for tab in ["", "points-assists", "shots"]:
			time.sleep(2.2)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			#call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-H", 'x-px-context: _px3=c402b3ed30e4c127a527513499624707d7461377294b1fdb6fc0da482d6c799d:hQzUhc35G2KLlhekJJmqTKmCNZoX75mKi7X9Xihzu/cX8CE8a+xat+EddyilXY+F0zQKqR51TfkfTxKfXYZnFA==:1000:yaktVjRcUsLEEvFv6dvaUtKaq67RVL4P9s0A735J5G5bJnuV/RcyF07Z3jZt+d7vPVBnd8jN5wvsvK5ozJE04aWoJmREo9s3xpESxPMKOKm4xDi8c7yRJhpLBl5ApZHEJMLuw3q5Re/Vxjq7qDmp938eD/hF6SctkXZCj3U8FUxqKde51JMeF9ErXaWatBWxN3AZVcONO7H+197jqRFkCZGqnnVy2JVbc3ll8f3LGLQ=;_pxvid=00692951-e181-11ed-a499-ebf9b9755f04;pxcts=006939ed-e181-11ed-a499-537250516c45;', "-H", 'X-Sportsbook-Region: MI', "-k", url, "-o", outfile])
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue

			if data["attachments"]["events"][str(gameId)]["inPlay"]:
				if game in lines:
					del lines[game]
				continue

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				runners = data["attachments"]["markets"][market]["runners"]

				if marketName in ["moneyline", "any time goal scorer"] or "3 way" in marketName or "total goals" in marketName or "puck line" in marketName or marketName.startswith("alternate") or marketName.startswith("player to record") or marketName.endswith("saves") or "shots on goal" in marketName:

					if "parlay" in marketName:
						continue

					prefix = ""
					if "1st period" in marketName:
						prefix = "1p_"
					elif "2nd period" in marketName:
						prefix = "2p_"
					elif "3rd period" in marketName:
						prefix = "3p_"

					alt = False
					prop = ""
					playerHandicap = ""
					if "moneyline" in marketName or "money line" in marketName:
						if "/" in marketName:
							continue
						prop = "ml"
					elif "3 way" in marketName:
						prop = "3-way"
					elif "alternate" in marketName:
						alt = True
						prop = "total"
						if "puck line" in marketName:
							prop = "spread"
					elif "total goals" in marketName:
						if "flat line" in marketName:
							continue
						if marketName == f"{away} total goals":
							prop = "away_total"
						elif marketName == f"{home} total goals":
							prop = "home_total"
						else:
							prop = "total"
					elif "puck line" in marketName:
						prop = "spread"
					elif marketName.endswith("saves"):
						prop = "saves"
					elif marketName == "any time goal scorer":
						prop = "atgs"
						alt = True
					elif "shots on goal" in marketName:
						prop = "sog"
						if marketName.startswith("player to"):
							alt = True
							playerHandicap = str(float(marketName.split(" ")[-4][:-1]) - 0.5)
					elif marketName == "player to record 1+ assists":
						prop = "ast"
						playerHandicap = "0.5"
						alt = True
					elif marketName.endswith("points"):
						prop = "pts"
						alt = True
						if "power" in marketName:
							continue
						playerHandicap = str(float(marketName.split(" ")[-2][:-1]) - 0.5)
					elif " - " in marketName:
						marketName = marketName.split(" - ")[-1]
						prop = "_".join(marketName.split(" ")).replace("strikeouts", "k")
					else:
						continue

					prop = f"{prefix}{prop}"

					handicap = runners[0]["handicap"]
					skip = 1 if alt else 2
					try:
						ou = str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
						if skip == 2:
							ou += "/"+str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					except:
						continue

					if runners[0]["runnerName"] == "Under":
						ou = str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])

					if "ml" not in prop:
						if prop not in lines[game]:
							lines[game][prop] = {}

					if "ml" in prop:
						lines[game][prop] = ou
					elif "3-way" in prop:
						lines[game][prop] = f"{runners[0]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[-1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"
					elif prop in ["saves"]:
						player = parsePlayer(marketName.split(" - ")[0])
						lines[game][prop][player] = {
							handicap: ou
						}
					elif prop in ["sog", "pts"]:
						for i in range(0, len(runners), skip):
							player = parsePlayer(runners[i]["runnerName"].split(" - ")[0])
							if player not in lines[game][prop]:
								lines[game][prop][player] = {}
							if playerHandicap:
								lines[game][prop][player][playerHandicap] = str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							else:
								handicap = runners[i]["handicap"]
								lines[game][prop][player][handicap] = f"{runners[i]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"
					else:
						for i in range(0, len(runners), skip):
							handicap = str(runners[i]["handicap"])
							try:
								odds = str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							except:
								continue
							if alt:
								if "spread" in prop or "total" in prop:
									handicap = float(runners[i]["runnerName"].split(" ")[-1].replace("(", "").replace(")", ""))
									if "spread" in prop and runners[i]["result"].get("type", "") == "HOME" or " ".join(runners[i]["runnerName"].lower().split(" ")[:-1]) == home:
										handicap *= -1
									handicap = str(handicap)
								else:
									handicap = parsePlayer(runners[i]["runnerName"])

								if handicap not in lines[game][prop]:
									lines[game][prop][handicap] = odds
									if "total" not in prop and "spread" not in prop:
										lines[game][prop][handicap] = f"0.5 {odds}"
								else:
									if runners[i]["runnerName"].startswith("Under") or runners[i]["result"].get("type", "") == "HOME" or " ".join(runners[i]["runnerName"].lower().split(" ")[:-1]) == home:
										if len(lines[game][prop][handicap].split("/")) == 2:
											if int(odds) > int(lines[game][prop][handicap].split("/")[-1]):
												lines[game][prop][handicap] = f"{lines[game][prop][handicap].split('/')[0]}/{odds}"

										else:
											lines[game][prop][handicap] += f"/{odds}"
									else:
										if len(lines[game][prop][handicap].split("/")) == 2:
											if int(odds) > int(lines[game][prop][handicap].split("/")[0]):
												lines[game][prop][handicap] = f"{odds}/{lines[game][prop][handicap].split('/')[-1]}"
										else:
											lines[game][prop][handicap] = f"{odds}/{lines[game][prop][handicap]}"
							elif "spread" in prop or "total" in prop:
								lines[game][prop][handicap] = ou
							else:
								if "over" in runners[i]["runnerName"].lower() or "under" in runners[i]["runnerName"].lower():
									player = parsePlayer(runners[i]["runnerName"].replace(" Over", "").replace(" Under", ""))
								else:
									player = parsePlayer(runners[i]["runnerName"].lower())
								lines[game][prop][player] = f"{handicap} {ou}"
	
	with open(f"static/nhl/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr", sharp=False):

	prefix = ""
	if sharp:
		prefix = "pn_"

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
		u = 1.07 - impliedOver
		if u > 1:
			return
		if over > 0:
			under = int((100*u) / (-1+u))
		else:
			under = int((100 - 100*u) / u)
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

	if player not in evData:
		evData[player] = {}
	evData[player][f"{prefix}fairVal"] = fairVal
	evData[player][f"{prefix}implied"] = implied
	
	evData[player][f"{prefix}ev"] = ev

def writeDK(date=None):
	url = "https://sportsbook.draftkings.com/leagues/hockey/nfl"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 496,
		"goalscorer": 1190,
		"sog": 1189,
		"player": 550,
		"goalie": 1064,
		"team totals": 1193
	}
	
	subCats = {
		496: [4525, 4999, 13192, 13189],
		1190: [12041],
		1189: [12040],
		550: [5586, 5587, 7983, 10296],
		1064: [10283, 10284, 12436],
		1193: [12055]
	}

	propIds = {
		4999: "3-way", 12041: "atgs", 12040: "sog", 5586: "pts", 5587: "ast", 13189: "spread", 13192: "total", 10283: "saves", 10284: "goals_against", 12436: "shutout", 7983: "pp_pts", 10296: "bs"
	}

	if False:
		mainCats = {
			"game lines": 493
		}

		subCats = {
			493: [13168]
		}

	lines = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/42133/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outnhl"
			call(["curl", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			prop = propIds.get(subCat, "")

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
				startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=4)
				if startDt.day != int(date[-2:]):
					continue
					pass
				game = event["name"].lower()
				games = []
				for team in game.split(" @ "):
					t = team.split(" ")[0]
					if t == "was":
						t = "wsh"
					elif "rangers" in team:
						t = "nyr"
					elif "islanders" in team:
						t = "nyi"
					games.append(t)
				game = " @ ".join(games)
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
					prop = cRow["name"].lower()
					for offerRow in cRow["offerSubcategory"]["offers"]:
						for row in offerRow:
							try:
								game = events[row["eventId"]]
							except:
								continue

							#if game != "texas a&m @ miami fl":
							#	continue

							if "label" not in row:
								continue

							if subCat in propIds:
								prop = propIds[subCat]
							else:
								prop = row["label"].lower().split(" [")[0]
							
								prefix = ""
								if "1st period" in prop:
									prefix = "1p_"
								elif "2nd period" in prop:
									prefix = "2p_"
								elif "3rd period" in prop:
									prefix = "3p_"

								if "moneyline" in prop:
									prop = "ml"
								elif "puck line" in prop:
									prop = "spread"
								elif prop.endswith("team total goals"):
									team = prop.split(" ")[0]
									if team == "was":
										team = "wsh"
									elif "rangers" in prop:
										team = "nyr"
									elif "islanders" in prop:
										team = "nyi"
									if game.startswith(team.split(" ")[0]):
										prop = "away_total"
									else:
										prop = "home_total"
								elif "total" in prop:
									prop = "total"
								else:
									continue


								prop = prop.replace(" alternate", "")
								prop = f"{prefix}{prop}"

							
							if "ml" not in prop:
								if prop not in lines[game]:
									lines[game][prop] = {}

							outcomes = row["outcomes"]
							ou = ""
							try:
								ou = f"{outcomes[0]['oddsAmerican']}/{outcomes[1]['oddsAmerican']}"
							except:
								continue

							if "ml" in prop:
								lines[game][prop] = ou
							elif prop == "3-way":
								lines[game][prop] = f"{outcomes[0]['oddsAmerican']}/{outcomes[-1]['oddsAmerican']}"
							elif "total" in prop or "spread" in prop:
								for i in range(0, len(outcomes), 1):
									line = str(float(outcomes[i]["line"]))
									odds = str(outcomes[i]['oddsAmerican'])
									team = outcomes[i]["label"].lower().split(" ")[0]
									if team == "was":
										team = "wsh"
									elif "rangers" in outcomes[i]["label"].lower():
										team = "nyr"
									elif "islanders" in outcomes[i]["label"].lower():
										team = "nyi"

									if game.endswith(team):
										line = str(float(line) * -1)
									if line not in lines[game][prop]:
										lines[game][prop][line] = odds
									else:
										if team == "under" or game.endswith(team):

											if len(lines[game][prop][line].split("/")) == 2:
												if int(odds) > int(lines[game][prop][line].split("/")[-1]):
													lines[game][prop][line] = f"{lines[game][prop][line].split('/')[0]}/{odds}"
											else:
												lines[game][prop][line] += "/"+odds
										else:
											if len(lines[game][prop][line].split("/")) == 2:
												if int(odds) > int(lines[game][prop][line].split("/")[0]):
													lines[game][prop][line] = f"{odds}/{lines[game][prop][line].split('/')[-1]}"
											else:
												lines[game][prop][line] = odds+"/"+lines[game][prop][line]
							elif prop in ["atgs"]:
								for outcome in outcomes:
									if outcome["criterionName"] != "Anytime Scorer":
										continue
									player = parsePlayer(outcome["label"])
									try:
										lines[game][prop][player] = {
											"0.5": outcome['oddsAmerican']
										}
									except:
										continue
							else:
								player = parsePlayer(outcomes[0]["participant"].split(" (")[0])
								lines[game][prop][player] = {}

								handicap = ""
								if prop == "shutout":
									pass
								else:
									handicap = f"{outcomes[0]['line']}"

								if not handicap:
									lines[game][prop][player] = f"{outcomes[0]['oddsAmerican']}"
									if len(row["outcomes"]) > 1:
										lines[game][prop][player] += f"/{outcomes[1]['oddsAmerican']}"
								else:
									lines[game][prop][player][handicap] = f"{outcomes[0]['oddsAmerican']}"
									if len(row["outcomes"]) > 1:
										lines[game][prop][player][handicap] += f"/{outcomes[1]['oddsAmerican']}"
										if "under" in outcomes[0]["label"].lower():
											lines[game][prop][player][handicap] = f"{outcomes[1]['oddsAmerican']}/{outcomes[0]['oddsAmerican']}"

	with open("static/nhl/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B18/C20902960/D43/E181378/F43/"

	js = """
	const data = {};

	{
		const main = document.querySelector(".gl-MarketGroupContainer");
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
		let prefix = "";
		if (title.indexOf("1st half") >= 0) {
			prefix = "1h_";
		} else if (title.indexOf("1st quarter") >= 0) {
			prefix = "1q_";
		}

		if (title == "game lines" || title == "1st half" || title == "1st quarter") {
			title = "lines";
		} else if (title == "player assists") {
			title = "ast";
		} else if (title === "player points") {
			title = "pts";
		} else if (title === "player rebounds") {
			title = "reb";
		} else if (title === "player steals") {
			title = "stl";
		} else if (title === "player turnovers") {
			title = "to";
		} else if (title === "player blocks") {
			title = "blk";
		} else if (title === "player threes made") {
			title = "3ptm";
		} else if (title === "alternative point spread" || title == "alternative spread" || title == "alternative 1st quarter point spread") {
			title = prefix+"spread";
		} else if (title === "alternative game total") {
			title = prefix+"total";
		}

		if (title.indexOf("spread") >= 0 || title.indexOf("total") >= 0) {
			for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
				const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" v ", " @ ");
				if (div.classList.contains("src-FixtureSubGroup_Closed")) {
					div.click();
				}

				let lines = [];
				for (const lineOdds of div.querySelectorAll(".gl-Market_General")[0].querySelectorAll(".gl-Market_General-cn1")) {
					let line = "";

					if (title == "total") {
						line = lineOdds.innerText;
					} else {
						line = lineOdds.querySelector(".gl-ParticipantCentered_Name").innerText;
					}

					lines.push(line);
					if (!data[game]) {
						data[game] = {};
					}
					if (!data[game][title]) {
						data[game][title] = {};
					}
					data[game][title][line] = "";

					if (title != "total") {
						const odds = lineOdds.querySelector(".gl-ParticipantCentered_Odds").innerText;
						data[game][title][line] = odds;
					}
				}

				let idx = 0;
				for (const lineOdds of div.querySelectorAll(".gl-Market_General")[1].querySelectorAll(".gl-Participant_General")) {
					let odds = "";
					if (title == "total") {
						odds = lineOdds.innerText;
					} else {
						odds = lineOdds.querySelector(".gl-ParticipantCentered_Odds").innerText;
					}

					if (title != "total") {
						data[game][title][lines[idx++]] += "/"+odds;
					} else {
						data[game][title][lines[idx++]] = odds;
					}
				}

				if (title == "total") {
					idx = 0;
					for (const lineOdds of div.querySelectorAll(".gl-Market_General")[2].querySelectorAll(".gl-Participant_General")) {
						let odds = lineOdds.innerText;
						let line = lines[idx++];
						data[game][title][line] += "/"+odds;
					}

					lines = [];
					for (const lineOdds of div.querySelectorAll(".gl-Market_General")[3].querySelectorAll(".gl-Market_General-cn1")) {
						const line = lineOdds.innerText;
						lines.push(line);
					}

					idx = 0;
					for (const lineOdds of div.querySelectorAll(".gl-Market_General")[4].querySelectorAll(".gl-Participant_General")) {
						const odds = lineOdds.innerText;
						data[game][title][lines[idx++]] = odds;
					}

					idx = 0;
					for (const lineOdds of div.querySelectorAll(".gl-Market_General")[5].querySelectorAll(".gl-Participant_General")) {
						const odds = lineOdds.innerText;
						data[game][title][lines[idx++]] += "/"+odds;
					}
				}
			}
		} else if (title != "lines") {
			for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
				const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" v ", " @ ");
				if (div.classList.contains("src-FixtureSubGroup_Closed")) {
					div.click();
				}
				let playerList = [];
				for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
					let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(". ", "").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
					let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];
					
					if (!data[game]) {
						data[game] = {};
					}
					if (!data[game][title]) {
						data[game][title] = {};
					}
					data[game][title][player] = "";
					playerList.push([game, player]);
				}

				let idx = 0;
				for (playerDiv of div.getElementsByClassName("gl-Market")[1].getElementsByClassName("gl-ParticipantCenteredStacked")) {
					let team = playerList[idx][0];
					let player = playerList[idx][1];

					let line = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Handicap")[0].innerText;
					let odds = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
					data[team][title][player] = line+" "+odds;
					idx += 1;
				}

				idx = 0;
				for (playerDiv of div.getElementsByClassName("gl-Market")[2].getElementsByClassName("gl-ParticipantCenteredStacked")) {
					let team = playerList[idx][0];
					let player = playerList[idx][1];

					data[team][title][player] += "/" + playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
					idx += 1;
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
					break;
				}
				const away = div.querySelectorAll(".scb-ParticipantFixtureDetailsHigherBasketball_Team")[0].innerText.toLowerCase();
				const home = div.querySelectorAll(".scb-ParticipantFixtureDetailsHigherBasketball_Team")[1].innerText.toLowerCase();
				const game = away+" @ "+home;
				games.push(game);

				if (!data[game]) {
					data[game] = {};
				}
			}

			const props = ["spread", "total", "ml"];
			let p = 0;
			for (const prop of props) {
				idx = 0;
				let divs = main.querySelectorAll(".gl-Market_General")[p+1].querySelectorAll(".gl-Participant_General");
				p += 1;
				for (let i = 0; i < divs.length; i += 2) {
					let game = games[idx];

					if (!game) {
						break;
					}

					let over = divs[i].innerText;
					let under = divs[i+1].innerText;

					if (prop == "ml") {
						if (over !== "" && under !== "") {
							data[game][prefix+prop] = over+"/"+under;
						}
					} else {
						let over = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
						let under = divs[i+1].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
						let line = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Handicap").innerText.replace("O ", "");
						if (!data[game][prefix+prop]) {
							data[game][prefix+prop] = {};
						}
						data[game][prefix+prop][line] = over+"/"+under;
					}
					idx += 1;
				}
			}
		}

		console.log(data);
	}

	"""
	pass

def writeEV(propArg="", bookArg="fd", teamArg="", notd=None, boost=None, overArg=None, underArg=None, nocz=None):

	if not boost:
		boost = 1

	#with open(f"{prefix}static/nhl/bet365.json") as fh:
	#	bet365Lines = json.load(fh)

	#with open(f"{prefix}static/nhl/actionnetwork.json") as fh:
	#	actionnetwork = json.load(fh)

	with open(f"{prefix}static/nhl/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/nhl/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/nhl/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nhl/mgm.json") as fh:
		mgmLines = json.load(fh)

	#with open(f"{prefix}static/nhl/pointsbet.json") as fh:
	#	pbLines = json.load(fh)

	with open(f"{prefix}static/nhl/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nhl/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	with open(f"{prefix}static/hockeyreference/totals.json") as fh:
		totals = json.load(fh)

	with open(f"{prefix}static/hockeyreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	with open(f"{prefix}static/nhl/caesars.json") as fh:
		czLines = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		#"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines
	}

	with open(f"{prefix}static/nhl/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	teamGame = {}
	for game in pnLines:
		away, home = map(str, game.split(" @ "))
		teamGame[away] = teamGame[home] = game

	games = []
	for book in lines:
		for game in lines[book]:
			if game not in games:
				games.append(game)

	for game in games:
		if teamArg:
			if game.split(" @ ")[0] not in teamArg.split(",") and game.split(" @ ")[1] not in teamArg.split(","):
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

			if not propArg and prop in []:
				#pass
				continue

			handicaps = {}
			for book in lines:
				lineData = lines[book]
				if game in lineData and prop in lineData[game]:
					if type(lineData[game][prop]) is not dict:
						handicaps[(" ", " ")] = ""
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
							if " " in lineData[game][prop][player]:
								playerHandicap = lineData[game][prop][player].split(" ")[0]
								handicaps[(handicap, playerHandicap)] = player
							elif type(lineData[game][prop][player]) is dict:
								for h in lineData[game][prop][player]:
									handicaps[(handicap, h)] = player

			for handicap, playerHandicap in handicaps:
				player = handicaps[(handicap, playerHandicap)]

				# last year stats
				lastTotalOver = lastTotalGames = 0
				totalOver = totalGames = 0
				totalSplits = []
				if player:
					convertedProp = prop.replace("sog", "s").replace("ast", "a").replace("saves", "sv").replace("atgs", "g")
					away, home = map(str, game.split(" @ "))
					team = away
					name = f"{player[0].upper()}. {player.split(' ')[-1].title()}"
					if name == "J. Ek":
						name = "J. Eriksson Ek"
					if home in playerIds and name in playerIds[home]:
						team = home
					if team in lastYearStats and name in lastYearStats[team] and lastYearStats[team][name]:
						for d in lastYearStats[team][name]:
							minutes = lastYearStats[team][name][d]["toi/g"]
							if minutes > 0 and (convertedProp == "pp_pts" or convertedProp in lastYearStats[team][name][d]):
								lastTotalGames += 1
								val = 0
								if convertedProp == "pp_pts":
									val = lastYearStats[team][name][d]["ppg"] + lastYearStats[team][name][d]["ppa"]
								else:
									val = lastYearStats[team][name][d][convertedProp]
								if val > float(playerHandicap):
									lastTotalOver += 1
					if lastTotalGames:
						lastTotalOver = int(lastTotalOver * 100 / lastTotalGames)

					for d in os.listdir(f"static/hockeyreference/{team}"):
						with open(f"static/hockeyreference/{team}/{d}") as fh:
							teamStats = json.load(fh)
						if name in teamStats:
							minutes = teamStats[name]["toi"]
							if minutes > 0 and (convertedProp == "pts" or convertedProp in teamStats[name]):
								totalGames += 1
								if convertedProp == "pts":
									val = teamStats[name]["g"] + teamStats[name]["a"]
								else:
									val = teamStats[name][convertedProp]
								totalSplits.append(str(int(val)))
								if val > float(playerHandicap):
									totalOver += 1

					if totalGames:
						totalOver = int(totalOver * 100 / totalGames)

				for i in range(2):

					if overArg and i == 1:
						continue
					elif underArg and i == 0:
						continue

					if lastTotalOver and i == 1:
						lastTotalOver = 100 - lastTotalOver
					if totalOver and i == 1:
						totalOver = 100 - totalOver
					highestOdds = []
					books = []
					odds = []

					for book in lines:
						lineData = lines[book]
						if game in lineData and prop in lineData[game]:
							#print(book, game, prop, handicap)
							if type(lineData[game][prop]) is str:
								val = lineData[game][prop]
							else:
								if handicap not in lineData[game][prop]:
									continue
								val = lineData[game][prop][handicap]

							if player.strip():
								if type(val) is dict:
									if playerHandicap not in val:
										continue
									val = lineData[game][prop][handicap][playerHandicap]
								else:
									if " " in val and playerHandicap != val.split(" ")[0]:
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

							if not o or o == "-":
								continue

							#print(prop, player, o)

							if book == "cz" and prop in ["pp_pts", "pts", "ast"]:
								continue
							highestOdds.append(int(o))
							odds.append(ou)
							books.append(book)

					if len(books) < 2:
						continue

					#print(game, prop, handicap, highestOdds, books, odds)

					pn = ""
					try:
						bookIdx = books.index("pn")
						pn = odds[bookIdx]
						odds.remove(pn)
						books.remove("pn")
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
					#print(maxOU in l, maxOU, l)
					l.remove(maxOU)
					books.remove(evBook)
					if pn:
						books.append("pn")
						l.append(pn)

					avgOver = []
					avgUnder = []
					for book in l:
						if book and book != "-":
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
						
					key = f"{game} {handicap} {prop} {'over' if i == 0 else 'under'}"
					if key in evData:
						continue
					if True:
						pass
						#print(key, ou, line)
						devig(evData, key, ou, line, prop=prop)
						if pn:
							if i == 1:
								pn = f"{pn.split('/')[1]}/{pn.split('/')[0]}"
							devig(evData, key, pn, line, prop=prop, sharp=True)
						#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
						if key not in evData:
							#print(key)
							continue
						if float(evData[key]["ev"]) > 0:
							#print(evData[key]["ev"], game, handicap, prop, int(line), ou, books)
							pass
						evData[key]["lastYearTotal"] = lastTotalOver
						evData[key]["totalOver"] = totalOver
						evData[key]["totalSplits"] = ",".join(totalSplits)
						evData[key]["game"] = game
						evData[key]["prop"] = prop
						evData[key]["book"] = evBook
						evData[key]["books"] = books
						evData[key]["ou"] = ou
						evData[key]["under"] = i == 1
						evData[key]["line"] = line
						evData[key]["fullLine"] = maxOU
						evData[key]["handicap"] = handicap
						evData[key]["playerHandicap"] = playerHandicap
						evData[key]["odds"] = l
						evData[key]["player"] = player
						j = {b: o for o, b in zip(l, books)}
						j[evBook] = maxOU
						evData[key]["bookOdds"] = j

	with open(f"{prefix}static/nhl/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def sortEV(propArg):
	with open(f"{prefix}static/nhl/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], d["game"], player, d["playerHandicap"], d["line"], d["book"], j, d["lastYearTotal"], d["totalOver"], d))

	for row in sorted(data):
		if propArg != "atgs" and row[-1]["prop"] in ["atgs"]:
			continue
		if propArg != "3-way" and row[-1]["prop"] in ["3-way"]:
			continue
		print(row[:-1])

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "BV", "CZ", "PN", "Kambi/BR", "LYR", "SZN", "Splits"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] in ["3-way", "atgs"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		
		implied = 0
		if row[-1]["line"] > 0:
			implied = 100 / (row[-1]["line"] + 100)
		else:
			implied = -1*row[-1]["line"] / (-1*row[-1]["line"] + 100)
		implied *= 100
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), f"{round(implied)}%", row[1].upper(), row[-1]["player"].title(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "bv", "cz", "pn", "kambi"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))

		for h in ["lastYearTotal", "totalOver"]:
			if not row[-1][h]:
				arr.append("-")
			else:
				arr.append(f"{row[-1][h]}%")
		arr.append(",".join(row[-1]["totalSplits"].split(",")[-10:]))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nhl/props.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Player", "Prop", "FD", "DK", "MGM", "BV", "CZ", "PN", "Kambi/BR", "LYR", "SZN"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] != "atgs":
			continue
		implied = 0
		if row[-1]["line"] > 0:
			implied = 100 / (row[-1]["line"] + 100)
		else:
			implied = -1*row[-1]["line"] / (-1*row[-1]["line"] + 100)
		implied *= 100
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), f"{round(implied)}%", row[1].upper(), row[-1]["player"].title(), row[-1]["prop"]]
		for book in ["fd", "dk", "mgm", "bv", "cz", "pn", "kambi"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		for h in ["lastYearTotal", "totalOver"]:
			if not row[-1][h]:
				arr.append("-")
			else:
				arr.append(f"{row[-1][h]}%")
		arr.append(",".join(row[-1]["totalSplits"].split(",")[-10:]))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nhl/atgs.csv", "w") as fh:
		fh.write(output)



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--avg", action="store_true", help="AVG")
	parser.add_argument("--all", action="store_true", help="ALL AVGs")
	parser.add_argument("--fd", action="store_true", help="Fanduel")
	parser.add_argument("--dk", action="store_true", help="Fanduel")
	parser.add_argument("--writeBV", action="store_true", help="Bovada")
	parser.add_argument("--bv", action="store_true", help="Bovada")
	parser.add_argument("--pb", action="store_true", help="Pointsbet")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("--pn", action="store_true", help="Pinnacle")
	parser.add_argument("--cz", action="store_true", help="Caesars")
	parser.add_argument("--mgm", action="store_true", help="MGM")
	parser.add_argument("-p", "--print", action="store_true", help="Print")
	parser.add_argument("-g", "--game", help="Game")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("-k", "--k", action="store_true", help="Ks")
	parser.add_argument("--ml", action="store_true", help="Moneyline and Totals")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("--under", action="store_true", help="Under")
	parser.add_argument("--over", action="store_true", help="Over")
	parser.add_argument("--nocz", action="store_true", help="No CZ Lines")
	parser.add_argument("--no365", action="store_true", help="No 365 Devig")
	parser.add_argument("--nobr", action="store_true", help="No BR/Kambi lines")
	parser.add_argument("--dinger", action="store_true", help="Dinger Tues")
	parser.add_argument("--plays", action="store_true", help="Plays")
	parser.add_argument("--summary", action="store_true", help="Summary")
	parser.add_argument("--text", action="store_true", help="Text")
	parser.add_argument("--lineups", action="store_true", help="Lineups")
	parser.add_argument("--lineupsLoop", action="store_true", help="Lineups")
	parser.add_argument("--notd", action="store_true", help="Not ATTD FTD")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--player", help="Book")

	args = parser.parse_args()

	if args.lineups:
		writeLineups(plays)

	if args.lineupsLoop:
		while True:
			writeLineups(plays)
			time.sleep(30)

	dinger = False
	if args.dinger:
		dinger = True


	if args.action:
		writeActionNetwork(args.date)

	if args.fd:
		writeFanduel()

	if args.mgm:
		writeMGM(args.date)

	if args.pb:
		writePointsbet(args.date)

	if args.dk:
		writeDK(args.date)

	if args.kambi:
		writeKambi()

	if args.pn:
		writePinnacle(args.date)

	if args.bv:
		writeBV()

	if args.cz:
		writeCZ(args.date)

	if args.update:
		#writeFanduel()
		writePinnacle(args.date)
		writeKambi()
		writeMGM(args.date)
		writeBV()
		writeDK(args.date)
		writeCZ(args.date)

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, teamArg=args.team, notd=args.notd, boost=args.boost, overArg=args.over, underArg=args.under, nocz=args.nocz)

	if args.print:
		sortEV(args.prop)