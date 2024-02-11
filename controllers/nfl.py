
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

def convertNFLTeam(team):
	team = team.lower()
	if team.endswith("packers"):
		return "gb"
	elif team.endswith("49ers"):
		return "sf"
	elif team.endswith("patriots"):
		return "ne"
	elif team.endswith("giants"):
		return "nyg"
	elif team.endswith("jets"):
		return "nyj"
	elif team.endswith("chargers"):
		return "lac"
	elif team.endswith("rams"):
		return "lar"
	elif team.endswith("raiders"):
		return "lv"
	elif "chiefs" in team:
		return "kc"
	elif team.endswith("saints"):
		return "no"
	elif team.endswith("buccaneers"):
		return "tb"
	elif team.endswith("jaguars"):
		return "jac"
	return team[:3]

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

	with open(f"{prefix}static/nfl/draftkings.json") as fh:
		fdLines = json.load(fh)

	teamGame = {}
	for game in fdLines:
		away, home = map(str, game.split(" @ "))
		if away not in teamGame:
			teamGame[away] = game
		if home not in teamGame:
			teamGame[home] = game

	props = ["56_first_touchdown_scorer", "62_anytime_touchdown_scorer", "60_longest_completion", "59_longest_reception", "58_longest_rush", "30_passing_attempts", "10_pass_completions", "11_passing_tds", "9_passing_yards", "17_receiving_tds", "16_receiving_yards", "15_receptions", "18_rushing_attempts", "13_rushing_tds", "12_rushing_yards", "70_tackles_assists"]
	#props = ["70_tackles_assists"]

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
			prop = "_".join(actionProp.split("_")[1:]).replace("rushing", "rush").replace("passing", "pass").replace("receiving", "rec").replace("yards", "yd").replace("attempts", "att").replace("completion", "cmp").replace("reception", "rec")
			if prop == "longest_cmp":
				prop = "longest_pass"

		if prop not in ["longest_pass"] and prop.endswith("s"):
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
				try:
					player = playerIds[oddData["player_id"]]
					team = teamIds[oddData["team_id"]]
					game = teamGame[team]
				except:
					continue
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

	with open(f"{prefix}static/nfl/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)


def writeCZ():
	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/americanfootball/events/schedule/?competitionIds=007d7c61-07a7-4e18-bb40-15104b6eac92"
	outfile = "outCZ"
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"][:20]:
		games.append(event["id"])


	#games = ["9d0e039c-1764-4be4-aa38-161e41a61260"]
	res = {}
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/events/{gameId}"
		time.sleep(0.2)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		game = data["name"].lower().replace("|", "").replace("at", "@")
		away = convertNFLTeam(game.split(' @ ')[0])
		home = convertNFLTeam(game.split(' @ ')[1])
		game = f"{away} @ {home}"
		res[game] = {}

		for market in data["markets"]:
			if "name" not in market:
				continue
			prop = market["name"].lower().replace("|", "").split(" (")[0]
			name = market["templateName"].lower().replace("|", "")

			prefix = player = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "1st quarter" in prop:
				prefix = "1q_"
			elif "2nd half" in prop:
				prefix = "2h_"

			if "money line" in prop:
				prop = "ml"
			elif "total points" in prop or "alternative points" in prop:
				if "away points" in name:
					prop = "away_total"
				elif "home points" in name:
					prop = "home_total"
				else:
					prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif prop == "player to score a touchdown":
				prop = "attd"
			elif prop == "first touchdown scorer":
				prop = "ftd"
			elif "total passing" in prop or "total rushing" in prop or "total receiving" in prop or "total receptions" in prop or "longest" in prop or "total defensive tackles" in prop or "total made field" in prop or "total kicking points" in prop:
				p = prop.split(" total")[0].split(" longest")[0]
				player = parsePlayer(p)
				prop = prop.split(p+" ")[-1].replace("total ", "").replace(" ", "_").replace("passing", "pass").replace("rushing", "rush").replace("touchdowns", "td").replace("yards", "yd").replace("receiving", "rec").replace("receptions", "rec").replace("reception", "rec").replace("completions", "cmp").replace("attempts", "att").replace("interceptions", "int").replace("made_field_goals", "fgm").replace("points", "pts")
				if prop == "longest_pass_completion":
					prop = "longest_pass"
				elif prop == "defensive_tackles_+_assists":
					prop = "tackles+ast"
				elif "rush_+_rec" in prop:
					prop = "rush+rec"
			else:
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			selections = market["selections"]
			skip = 1 if prop in ["attd", "ftd"] else 2
			for i in range(0, len(selections), skip):
				try:
					ou = str(selections[i]["price"]["a"])
				except:
					continue
				if skip == 2:
					try:
						ou += f"/{selections[i+1]['price']['a']}"
					except:
						continue
					if selections[i]["name"].lower().replace("|", "") == "under":
						ou = f"{selections[i+1]['price']['a']}/{selections[i]['price']['a']}"

				if "ml" in prop:
					res[game][prop] = ou
				elif "spread" in prop:
					line = str(float(market["line"]) * -1)
					res[game][prop][line] = ou
				elif "total" in prop:
					if "line" not in market:
						continue
					line = str(float(market["line"]))
					res[game][prop][line] = ou
				elif prop in ["attd", "ftd"]:
					player = parsePlayer(selections[i]["name"].replace("|", ""))
					res[game][prop][player] = ou
				else:
					try:
						line = str(float(market["line"]))
						res[game][prop][player] = f"{line} {ou}"
					except:
						continue

			if prop in ["spread", "total"]:
				try:
					linePrices = market["movingLines"]["linePrices"]
				except:
					continue
				for prices in linePrices:
					selections = prices["selections"]
					if prop == "spread":
						line = str(float(prices["line"]) * -1)
						ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"
					else:
						line = str(float(prices["line"]))
						ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
						if selections[0]["selectionType"] == "under":
							ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"

					
					res[game][prop][line] = ou


	with open("static/nfl/caesars.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePointsbet():
	url = "https://api.mi.pointsbet.com/api/v2/sports/american-football/events/featured?includeLive=false"
	outfile = f"nfloutPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	#games = ["275622"]
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		game = data["name"].lower()
		fullAway, fullHome = map(str, game.split(" @ "))
		game = f"{convertNFLTeam(fullAway)} @ {convertNFLTeam(fullHome)}"
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

			prefix = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "1st quarter" in prop:
				prefix = "1q_"

			if prop.startswith("point spread") or prop == "pick your own line":
				prop = f"{prefix}spread"
			elif prop.startswith("moneyline"):
				if "3 way" in prop:
					continue
				prop = f"{prefix}ml"
			elif prop.startswith("total") or prop == "alternate totals":
				if "touchdowns" in prop:
					continue
				prop = "total"
				prop = f"{prefix}total"
			elif prop.startswith(f"{fullAway} total"):
				prop = f"{prefix}away_total"
			elif prop.startswith(f"{fullHome} total"):
				prop = f"{prefix}home_total"
			elif prop.startswith("receiving yards"):
				prop = "rec_yd"
			elif prop.startswith("rushing yards"):
				prop = "rush_yd"
			#elif prop.startswith("passing yards"):
			#	prop = "pass_yd"
			elif prop.startswith("rushing attempts over/under"):
				prop = "rush_att"
			elif prop.startswith("player receptions"):
				prop = "rec"
			elif prop.startswith("quarterback pass attempts"):
				prop = "pass_att"
			elif prop.startswith("quarterback pass completions"):
				prop = "pass_cmp"
			elif prop.split(" (")[0] == "anytime touchdown scorer":
				prop = "attd"
			elif prop.split(" (")[0] == "first touchdown scorer":
				prop = "ftd"
			else:
				continue

			if "ml" not in prop:
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			if market["hiddenOutcomes"] and prop in ["total"]:
				outcomes.extend(market["hiddenOutcomes"])
			skip = 1 if prop == "attd" else 2
			for i in range(0, len(outcomes), skip):
				points = str(outcomes[i]["points"])
				if outcomes[i]["price"] == 1:
					continue
				over = str(convertAmericanOdds(outcomes[i]["price"]))
				under = ""
				try:
					under = convertAmericanOdds(outcomes[i+1]["price"])
					ou = f"{over}/{under}"
					if "spread" in prop or "ml" in prop and outcomes[i]["side"] == "Home":
						ou = f"{under}/{over}"
				except:
					pass

				if "ml" in prop:
					res[game][prop] = ou
				elif prop in ["attd", "ftd"]:
					if "d/st" in outcomes[i]["name"].lower():
						player = outcomes[i]["name"].lower().replace("d/st", "defense")
					else:
						try:
							player = parsePlayer(playerIds[outcomes[i]["playerId"]])
						except:
							player = outcomes[i]["name"].lower()
					res[game][prop][player] = str(over)
				elif prop.startswith("rec") or prop.startswith("pass") or prop.startswith("rush"):
					player = parsePlayer(outcomes[i]["name"].lower().split(" over")[0])
					res[game][prop][player] = f"{outcomes[i]['name'].split(' ')[-1]} {ou}"
				else:
					if "spread" in prop and outcomes[i]["side"] == "Home":
						points = str(outcomes[i+1]["points"])
						ou = f"{under}/{over}"
					res[game][prop][points] = ou

	with open("static/nfl/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "nfloutPN"
	game = games[gameId]

	#print(game)
	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o nfloutPN'

	time.sleep(0.5)
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
			prop = row["units"].lower().replace("yards", "_yd").replace("receiving", "rec").replace("passing", "pass").replace("rushing", "rush").replace("interceptions", "int")
			if prop == "touchdownpasses":
				prop = "pass_td"
			elif prop == "1st touchdown":
				prop = "ftd"
			elif prop == "touchdowns":
				prop = "attd"
			elif prop == "longestreception":
				prop = "longest_rec"
			elif prop == "longestpasscomplete":
				prop = "longest_pass"
			elif prop == "passreceptions":
				prop = "rec"

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

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o nfloutPN'

	time.sleep(0.5)
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
		try:
			prop = row["type"]
		except:
			continue
		keys = row["key"].split(";")

		prefix = ""
		if keys[1] == "1":
			prefix = "1h_"
		elif keys[1] == "3":
			prefix = "1q_"

		overId = underId = 0
		player = ""

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

			if "points" in prices[0] and prop not in ["ftd", "attd", "last touchdown"]:
				handicap = str(prices[switched]["points"])
				res[game][prop][player] = handicap+" "+ou
			else:
				res[game][prop][player] = ou
		else:
			ou = f"{prices[0]['price']}/{prices[1]['price']}"
			if prices[0]["designation"] in ["home", "under"]:
				ou = f"{prices[1]['price']}/{prices[0]['price']}"
				switched = 1

			if "points" in prices[0]:
				handicap = str(prices[switched]["points"])
				if prop not in res[game]:
					res[game][prop] = {}

				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

def writePinnacle(date):
	debug = False

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/football/nfl/matchups#period:0"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/889/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 410040c0-e1fcf090-53cb2c91-be5a5dbd" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o nfloutPN'

	os.system(url)
	outfile = f"nfloutPN"
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	for row in data:
		#if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
		#	continue
		if row["type"] == "matchup" and not row["parent"]:
			player1 = convertNFLTeam(row["participants"][0]["name"].lower())
			player2 = convertNFLTeam(row["participants"][1]["name"].lower())
			games[str(row["id"])] = f"{player2} @ {player1}"

	res = {}
	#games = {'1573148913': 'det @ kc'}
	retry = []
	for gameId in games:
		parsePinnacle(res, games, gameId, retry, debug)

	for gameId in retry:
		parsePinnacle(res, games, gameId, retry, debug)

	with open("static/nfl/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBV():
	url = "https://www.bovada.lv/sports/football/nfl"

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/football/nfl?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
	outfile = f"nfloutBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	if False:
		ids = ["/football/super-bowl/san-francisco-49ers-kansas-city-chiefs-202402111830"]
		#ids = ["/football/nfl/san-francisco-49ers-kansas-city-chiefs-202402111830"]
	else:
		if not data:
			return
		ids = [r["link"] for r in data[0]["events"]]
	
	res = {}
	#print(ids)
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		comp = data[0]['events'][0]['competitors']
		game = data[0]['events'][0]['description'].lower()
		fullAway, fullHome = game.split(" @ ")
		game = f"{convertNFLTeam(fullAway)} @ {convertNFLTeam(fullHome)}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "touchdown scorers", "receiving props", "receiving yards", "qb yardage props", "qb passing totals", "rushing props", "rushing yards", "defensive player props", "special teams", "special bets", "td scorer parlays"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["description"].lower() == "first half":
						prefix = "1h_"
					elif market["period"]["description"].lower() == "second half":
						prefix = "2h_"
					elif market["period"]["description"].lower() == "1st quarter":
						prefix = "1q_"
					elif market["period"]["description"].lower() == "2nd quarter":
						prefix = "2q_"
					elif market["period"]["description"].lower() == "3rd quarter":
						prefix = "3q_"
					elif market["period"]["description"].lower() == "4th quarter":
						prefix = "4q_"

					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "total" or prop == "total points":
						prop = "total"
					elif prop == "point spread" or prop == "spread":
						prop = "spread"
					elif prop == f"total points - {fullAway}":
						prop = "away_total"
					elif prop == f"total points - {fullHome}":
						prop = "home_total"
					elif prop == "anytime touchdown scorer":
						prop = "attd"
					elif prop == "first touchdown scorer":
						prop = "ftd"
					elif desc == "receiving yards":
						prop = "rec_yd"
					elif prop.startswith("total receptions"):
						prop = "rec"
					elif prop.startswith("longest reception"):
						prop = "longest_rec"
					elif prop.startswith("total passing yards"):
						prop = "pass_yd"
					elif prop.startswith("total passing touchdowns"):
						prop = "pass_td"
					elif prop.startswith("total passing attempts") or prop == "passattempts":
						prop = "pass_att"
					elif prop.startswith("total passing completions") or prop == "completions":
						prop = "pass_cmp"
					elif prop.startswith("longest pass completions"):
						prop = "longest_pass"
					elif prop.startswith("total interceptions"):
						prop = "int"
					elif prop.startswith("total rush attempts"):
						prop = "rush_att"
					elif prop.startswith("total rushing & rec"):
						prop = "rush+rec"
					elif prop.startswith("total rushing yards"):
						prop = "rush_yd"
					elif prop.startswith("total rush attempts"):
						prop = "rush_att"
					elif prop.startswith("total tackles and assists"):
						prop = "tackles+ast"
					elif prop.startswith("total kicking points"):
						prop = "kicking_pts"
					elif prop == "player sacks":
						prop = "sacks"
					elif prop in ["touchdown scorer parlays", "anytime touchdown scorer / game winner parlay"]:
						prop = "td_parlay"
					else:
						continue

					prop = f"{prefix}{prop}"

					if not len(market["outcomes"]):
						continue

					if "ml" not in prop and prop not in res[game]:
						res[game][prop] = {}

					if "ml" in prop:
						try:
							res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
						except:
							continue
					elif "total" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							except:
								continue
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif "spread" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							except:
								continue
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif prop in ["attd", "ftd"]:
						for i in range(0, len(market["outcomes"]), 1):
							player = parsePlayer(market["outcomes"][i]["description"])
							res[game][prop][player] = market["outcomes"][i]["price"]["american"].replace("EVEN", "100")
					elif prop == "td_parlay":
						for outcome in market["outcomes"]:
							desc = outcome["description"]

							attd = []
							ftd = []
							ml = ""

							if "1+ anytime" in desc.lower():
								attdPlayers = desc.lower().split(" 1+ anytime")[0]
								for player in attdPlayers.split(", "):
									if "&" in player:
										for p in player.split(" & "):
											if " " in p:
												p = parsePlayer(p)
											attd.append(p.replace(".", ". "))
									else:
										if " " in player:
											player = parsePlayer(player)
										attd.append(player.replace(".", ". "))
							elif "1st touchdowns" in desc.lower():
								players = desc.lower().split(" to score")[0]
								for player in players.split(" & "):
									p = player.split(" (")[0]
									ftd.append(parsePlayer(p))
							elif "to score anytime" in desc.lower() and desc.endswith("to win"):
								player = desc.lower().split(" to score")[0]
								team = convertNFLTeam(desc.lower().split("/ ")[-1][:-7])
								attd.append(parsePlayer(player))
								ml = team
							elif "1st touchdown of the match" in desc.lower():
								if " or " in desc.lower():
									for player in desc.lower().split(", "):
										if " or " in player:
											for p in player.split(" or "):
												ftd.append(p.split(" (")[0].split("(")[0])
										else:
											ftd.append(player.split(" (")[0].split("(")[0])
								else:
									ftd.append(parsePlayer(desc.lower().split(" to score the 1st")[0].split(" (")[0].split("(")[0]))
									attd.append(parsePlayer(desc.lower().split(" to score anytime")[0].split(" and ")[-1].split(" (")[0].split("(")[0]))

							res[game][prop][desc] = {
								"attd": attd,
								"ftd": ftd,
								"ml": ml,
								"odds": outcome["price"]["american"]
							}
					elif prop == "sacks":
						for outcome in market["outcomes"]:
							player = parsePlayer(outcome["description"].split(" to ")[0])
							if player not in res[game][prop]:
								res[game][prop][player] = str(outcome["price"]["american"])
							else:
								if "not" in outcome["description"]:
									res[game][prop][player] += f"/{outcome['price']['american']}"
								else:
									res[game][prop][player] = f"{outcome['price']['american']}/{res[game][prop][player]}"
								res[game][prop][player] = "0.5 "+res[game][prop][player].replace("EVEN", "100")
					else:
						try:
							handicap = market["outcomes"][0]["price"]["handicap"]
							player = parsePlayer(market["description"].split(" - ")[-1].split(" (")[0])
							res[game][prop][player] = f"{handicap} {market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
						except:
							continue


	with open("static/nfl/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM():

	res = {}

	url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35"

	url = f"https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=11&regionId=9&competitionId=35&compoundCompetitionId=1:35&widgetId=/mobilesports-v1.0/layout/layout_us/modules/competition/defaultcontainereventsfutures-redesign&shouldIncludePayload=true"
	outfile = f"nfloutMGM"

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
		ids.append(row["id"])

	#ids = ["14873974"]
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
		game = f"{convertNFLTeam(fullTeam1)} @ {convertNFLTeam(fullTeam2)}"

		res[game] = {}
		d = data["games"]
		if not d:
			d = data["optionMarkets"]
		for row in d:
			prop = row["name"]["value"].lower()

			prefix = player = ""
			if "1st half" in prop or "first half" in prop:
				prefix = "1h_"
			elif "2nd half" in prop or "second half" in prop:
				prefix = "2h_"
			elif "1st quarter" in prop or "first quarter" in prop:
				prefix = "1q_"
			elif "2nd quarter" in prop or "second quarter" in prop:
				prefix = "2q_"
			elif "3rd quarter" in prop or "third quarter" in prop:
				prefix = "3q_"
			elif "4th quarter" in prop or "fourth quarter" in prop:
				prefix = "4q_"

			if prop.endswith("money line"):
				prop = "ml"
			elif prop == "total games" or "totals" in prop:
				prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif prop == "anytime touchdown scorer":
				prop = "attd"
			elif prop == "first touchdown scorer":
				prop = "ftd"
			elif "): " in prop:
				if "odd" in prop or "o/u" in prop:
					continue
				player = prop.split(" (")[0]
				prop = prop.split("): ")[-1]
				prop = prop.replace("receiving", "rec").replace("rushing", "rush").replace("passing", "pass").replace("yards", "yd").replace("receptions made", "rec").replace("reception", "rec").replace("field goals made", "fgm").replace("points", "pts").replace("longest pass completion", "longest_pass").replace("completions", "cmp").replace("completion", "cmp").replace("attempts", "att").replace("touchdowns", "td").replace("assists", "ast").replace("defensive interceptions", "int").replace("interceptions thrown", "int").replace(" ", "_")
				if prop == "total_pass_and_rush_yd":
					prop = "pass+rush"
				elif prop == "total_rush_and_rec_yd":
					prop = "pass+rush"
				elif "and_ast" in prop:
					prop = "tackles+ast"
			elif prop.startswith("how many "):
				if prop.startswith("how many points will be scored in the game") or "extra points" in prop or "combine" in prop:
					continue
				if fullTeam1 in prop or fullTeam2 in prop:
					p = "away_total"
					team = prop.split(" will ")[-1].split(" score")[0]
					if fullTeam2 in prop:
						p = "home_total"
					prop = p
				else:
					if "his 1st" in prop:
						continue
					player = prop.split(" (")[0].split(" will ")[-1]
					p = prop.split(" ")[2].replace("interceptions", "int")
					if "longest" in prop:
						end = prop.split(" ")[-1][:-1].replace("completion", "pass").replace("reception", "rec")
						if end not in ["rush", "pass", "rec"]:
							continue
						p = "longest_"+end
					elif "tackles" in prop:
						if "tackles and assists" in prop:
							p = "tackles+ast"
						else:
							continue
					elif "passing and rushing yards" in prop:
						p = "pass+rush"
					elif "rushing and receiving yards" in prop:
						p = "rush+rec"
					elif p == "passing":
						p = "pass_"+prop.split(" ")[3].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "rushing":
						p = "rush_"+prop.split(" ")[3].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "receiving":
						p = "rec_"+prop.split(" ")[3].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "receptions":
						p = "rec"
					elif p == "points":
						p = "kicking_pts"
					elif p == "made" or p == "field":
						p = "fgm"
					prop = p
			else:
				continue

			if prop in ["touchdowns"]:
				continue

			prop = prefix+prop

			results = row.get('results', row['options'])
			price = results[0]
			if "price" in price:
				price = price["price"]
			if "americanOdds" not in price:
				continue
			#print(prop, price, row["name"]["value"].lower())
			if len(results) < 2:
				ou = f"{price['americanOdds']}"
			else:
				ou = f"{price['americanOdds']}/{results[1].get('americanOdds', results[1]['price']['americanOdds'])}"
			if "ml" in prop:
				res[game][prop] = ou
			elif len(results) >= 2:
				skip = 1 if prop in ["attd", "ftd"] else 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop and prop not in ["attd", "ftd"]:
						continue
					else:
						val = val.split(" ")[-1]
					#print(game, prop, player)
					if prop in ["attd", "ftd"]:
						try:
							ou = str(results[idx].get('americanOdds', results[idx]['price']['americanOdds']))
						except:
							continue
					else:
						ou = f"{results[idx].get('americanOdds', results[idx]['price']['americanOdds'])}/{results[idx+1].get('americanOdds', results[idx+1]['price']['americanOdds'])}"

					if prop in ["attd", "ftd"]:
						player = results[idx]["name"]["value"].lower()
						player = parsePlayer(player)
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = ou
					elif player:
						player = parsePlayer(player)
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = val+" "+ou
					else:
						if prop not in res[game]:
							res[game][prop] = {}
						try:
							v = str(float(val))
							res[game][prop][v] = ou
						except:
							pass

	with open("static/nfl/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi():
	data = {}
	outfile = f"outnfl.json"
	url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/american_football/nfl"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/american_football/nfl/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	fullTeam = {}
	eventIds = {}
	for event in j["events"]:
		game = event["event"]["name"].lower()
		if " @ " in game:
			away, home = map(str, game.split(" @ "))
		else:
			away, home = map(str, game.split(" vs "))
		games = []
		for team in [away, home]:
			t = convertNFLTeam(team)
			fullTeam[t] = team
			games.append(t)
		game = " @ ".join(games)
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	#eventIds = {'min @ phi': 1019646714}
	#data['det lions @ kc chiefs'] = {}
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
			if "1st half" in label:
				prefix = "1h_"
			elif "2nd half" in label:
				prefix = "2h_"
			elif "quarter 1" in label:
				prefix = "1q_"
			elif "quarter 2" in label:
				prefix = "2q_"

			if label.split(" -")[0] == "total points":
				label = "total"
			elif label.split(" -")[0] == "handicap":
				label = "spread"
			elif "total points by" in label:
				team = convertNFLTeam(label.split(" by ")[-1].split(" - ")[0])
				if team == away:
					label = "away_total"
				else:
					label = "home_total"
			elif label == "including overtime" or label.split(" -")[0] == "draw no bet":
				label = "ml"
			elif label == "touchdown scorer - including overtime":
				playerProp = True
				label = "attd"
			elif label == "first touchdown scorer - including overtime":
				playerProp = True
				label = "ftd"
			elif (label.endswith("by the player - including overtime") or label.endswith("by the player")) and label.startswith("total"):
				playerProp = True
				label = "_".join(label[6:].replace(" - including overtime", "").split(" by the player")[0].split(" "))
				label = label.replace("passing", "pass").replace("yards", "yd").replace("rushing", "rush").replace("receiving", "rec").replace("touchdowns", "td").replace("receptions", "rec").replace("interceptions_thrown", "int").replace("points", "pts").replace("attempts", "att")
				if "defensive_tackles" in label:
					label = "tackles+ast"
				elif "pass_&_rush" in label:
					label = "pass+rush"
				elif "rush_&_rec" in label:
					label = "rush+rec"

				if "&" in label:
					continue
				if label == "touchdown_passes_thrown":
					label = "pass_td"
				elif label == "pass_completions":
					label = "pass_cmp"
				elif "longest_rec" in label:
					label = "longest_rec"
				elif "longest_rush" in label:
					label = "longest_rush"
				elif "longest_completed" in label:
					label = "longest_pass"
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
				if convertNFLTeam(betOffer["outcomes"][0]["participant"].lower()) == away:
				 	data[game][label] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]

			else:
				if label not in data[game]:
					data[game][label] = {}
				if not playerProp:
					if "line" not in betOffer["outcomes"][0]:
						continue
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer["outcomes"][0]["label"] == "Under" or convertNFLTeam(betOffer["outcomes"][0]["label"].lower()) == home:
						line = str(betOffer["outcomes"][1]["line"] / 1000)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					data[game][label][line] = ou
				elif label in ["attd"]:
					data[game][label][player] = ou
				elif label == "ftd":
					for outcome in betOffer["outcomes"]:
						try:
							player = parsePlayer(outcome["participant"])
							last, first = map(str, player.split(", "))
							player = f"{first} {last}"
							data[game][label][player] = f"{outcome['oddsAmerican']}"
						except:
							continue
				else:
					if "line" not in betOffer["outcomes"][0]:
						continue
					line = betOffer["outcomes"][0]["line"] / 1000
					if betOffer["outcomes"][0]["label"] == "Under":
						line = betOffer["outcomes"][1]["line"] / 1000
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					if player not in data[game][label]:
						data[game][label][player] = {}
					data[game][label][player][line] = ou


	with open(f"static/nfl/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "")
	if player == "josh palmer":
		player = "joshua palmer"
	elif player == "gabe davis":
		player = "gabriel davis"
	elif player == "trevon moehrig woodard":
		player = "trevon moehrig"
	elif player == "chig okonkwo":
		player = "chigoziem okonkwo"
	return player

def writeFanduelManual():
	js = """

	let data = {};
	{

		function convertTeam(team) {
			let t = team.toLowerCase().substring(0, 3);
			if (t == "kan") {
				t = "kc";
			} else if (t == "los") {
				t = "lar";
				if (team.indexOf("chargers") >= 0) {
					t = "lac";
				}
			} else if (t == "gre") {
				t = "gb";
			} else if (t == "san") {
				t = "sf";
			} else if (t == "tam") {
				t = "tb";
			} else if (t == "las") {
				t = "lv";
			} else if (t == "new") {
				t = "ne";
				if (team.indexOf("giants") > 0) {
					t = "nyg";
				} else if (team.indexOf("jets") > 0) {
					t = "nyj";
				} else if (team.indexOf("saints") >= 0) {
					t = "nor";
				}
			}
			return t;
		}

		function parsePlayer(player) {
			return player.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
		}

		let game = document.querySelector("h1").innerText.toLowerCase().replace(" 1st half odds", "").replace(" 2nd half odds", "").replace(" 1st quarter odds", "").replace(" odds", "");
		let awayFull = game.split(" @ ")[0];
		let awayName = awayFull.split(" ")[awayFull.split(" ").length - 1];
		let homeFull = game.split(" @ ")[1];
		let homeName = homeFull.split(" ")[homeFull.split(" ").length - 1];
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

			let prefix = "";
			if (label.indexOf("1st half") >= 0 || label.indexOf("first half") >= 0) {
				prefix = "1h_";
			} else if (label.indexOf("2nd half") >= 0 || label.indexOf("second half") >= 0) {
				prefix = "2h_";
			} else if (label.indexOf("1st quarter") >= 0) {
				prefix = "1q_";
			}

			if (label.indexOf("game lines") >= 0) {
				prop = "lines";
			} else if (label == "touchdown scorers") {
				prop = "attd";
			} else if (label.indexOf("kicking points") >= 0) {
				player = true;
				prop = "kicking_pts";
			} else if (label.indexOf("player") >= 0) {
				player = true;

				if (label.indexOf("most") >= 0 || label.indexOf("of the game") >= 0 || label.indexOf("first") >= 0 || label.indexOf("1st") >= 0) {
					continue
				}

				if (label.indexOf("player to record a ") >= 0) {
					continue;
				}

				if (label.indexOf("passing + rushing") >= 0) {
					prop = "pass+rush";
				} else if (label.indexOf("rushing + receiving") >= 0) {
					prop = "rush+rec";
				} else if (label.indexOf("longest pass") >= 0) {
					prop = "longest_pass";
				} else if (label.indexOf("longest rush") >= 0) {
					prop = "longest_rush";
				} else if (label.indexOf("longest rec") >= 0) {
					prop = "longest_rec";
				} else if (label.indexOf("pass") >= 0) {
					prop = "pass";
				} else if (label.indexOf("rush") >= 0) {
					prop = "rush";
				} else if (label.indexOf("receiving") >= 0 || label.indexOf("receptions") >= 0) {
					prop = "rec";
				}

				if (label.indexOf("yds") >= 0) {
					prop += "_yd";
				} else if (label.indexOf("tds") >= 0) {
					prop += "_td";
				} else if (label.indexOf("completions") >= 0) {
					prop += "_cmp";
				} else if (label.indexOf("attempts") >= 0) {
					prop += "_att";
				}
			} else if (label.indexOf("spread") >= 0) {
				if (label.indexOf("/") >= 0) {
					continue;
				}
				prop = "spread";
			} else if (label.indexOf("winner") >= 0) {
				if (label.indexOf("3-way") >= 0) {
					continue;
				}
				prop = "ml";
			} else if (label.indexOf("alternate total points") >= 0 || label.indexOf("first half total") >= 0 || label.indexOf("second half total") >= 0 || label.indexOf("1st quarter total") >= 0) {
				if (label.indexOf("odd/even") >= 0 || label.indexOf("exact") >= 0) {
					continue;
				}
				prop = "total";
			} else if (label.indexOf(awayName+" total points") >= 0) {
				prop = "away_total";
			} else if (label.indexOf(homeName+" total points") >= 0) {
				prop = "home_total";
			}

			if (!prop) {
				continue;
			}

			prop = prefix+prop;

			if (arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
				arrow.click();
			}
			let el = arrow.parentElement.parentElement.querySelector("div[aria-label='Show more']");
			if (el) {
				el.click();
			}
			el = arrow.parentElement.parentElement.querySelector("div[aria-label='Show more correct score options']");
			if (el) {
				el.click();
			}

			if (prop != "lines" && !data[game][prop]) {
				data[game][prop] = {};
			}

			let skip = 1;
			if (["attd", "away_total", "home_total", "spread"].indexOf(prop) >= 0 || prefix || player) {
				skip = 2;
			}
			if (prop == "attd") {
				skip = 3;
			}
			let btns = Array.from(li.querySelectorAll("div[role=button]"));
			btns.shift();

			if (prop == "attd") {
				btns.shift();
			}

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
				if (!ariaLabel || ariaLabel.indexOf("Show more") >= 0 || ariaLabel.indexOf("Show less") >= 0 || ariaLabel.indexOf("unavailable") >= 0) {
					continue;
				}
				let odds = ariaLabel.split(", ")[1];

				//console.log(btn, odds);

				if (odds.indexOf("unavailable") >= 0) {
					continue;
				}
				if (prop == "lines") {

				} else if (prefix) {
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (prop.indexOf("ml") >= 0) {
						odds = ariaLabel.split(", ")[1];
						data[game][prop] = odds;
						if (btns[i+1].getAttribute("aria-label").split(", ")[1]) {
							data[game][prop] += "/"+btns[i+1].getAttribute("aria-label").split(", ")[1];
						}
					} else if (prop.indexOf("spread") >= 0) {
						data[game][prop][line] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[2];
					} else if (prop.indexOf("total") >= 0) {
						line = ariaLabel.split(", ")[2].split(" ")[1];
						odds = ariaLabel.split(", ")[3].split(" ")[0];
						data[game][prop][line] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
					}
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

					odds = ariaLabel.split(", ")[1].split(" ")[0];
					line = line.replace("+", "");

					if (btns[i+1].getAttribute("aria-label").split(", ")[1] === undefined) {
						continue;
					}

					if (isAway) {
						data[game][prop][line] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[1].split(" ")[0];
					} else {
						data[game][prop][line] = btns[i+1].getAttribute("aria-label").split(", ")[1].split(" ")[0]+"/"+odds;
					}
				} else if (["total"].indexOf(prop) >= 0) {
					let odds = ariaLabel.split(", ")[2].split(" ")[0];
					let line = ariaLabel.split(", ")[1].split(" ")[0];

					let isAway = true;
					if (ariaLabel.split(", ")[1].indexOf("Under") >= 0) {
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
				} else if (prop == "kicking_pts") {
					player = parsePlayer(arrow.innerText.toLowerCase().split(" - ")[0]);
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					data[game][prop][player] = {};
					data[game][prop][player][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2].split(" ")[0];
				} else if (skip == 2 && player && prop != "attd") {
					// 2 sides
					player = parsePlayer(ariaLabel.split(", ")[0]);
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}
					line = ariaLabel.split(", ")[1].split(" ")[1];
					odds = ariaLabel.split(", ")[2].split(" ")[0];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop][player][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2].split(" ")[0];
				} else if (skip == 2 && prop != "attd") {
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop] = {};
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
				} else {
					player = parsePlayer(ariaLabel.split(",")[0]);
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}

					if (["attd"].indexOf(prop) >= 0) {
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
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("football/nfl") >= 0) {
				urls[a.href] = 1;
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/football/nfl/jacksonville-jaguars-@-new-orleans-saints-32705962",
  "https://mi.sportsbook.fanduel.com/football/nfl/cleveland-browns-@-indianapolis-colts-32705963",
  "https://mi.sportsbook.fanduel.com/football/nfl/washington-commanders-@-new-york-giants-32705965",
  "https://mi.sportsbook.fanduel.com/football/nfl/atlanta-falcons-@-tampa-bay-buccaneers-32705970",
  "https://mi.sportsbook.fanduel.com/football/nfl/buffalo-bills-@-new-england-patriots-32705972",
  "https://mi.sportsbook.fanduel.com/football/nfl/las-vegas-raiders-@-chicago-bears-32705973",
  "https://mi.sportsbook.fanduel.com/football/nfl/detroit-lions-@-baltimore-ravens-32705979",
  "https://mi.sportsbook.fanduel.com/football/nfl/pittsburgh-steelers-@-los-angeles-rams-32705967",
  "https://mi.sportsbook.fanduel.com/football/nfl/arizona-cardinals-@-seattle-seahawks-32705974",
  "https://mi.sportsbook.fanduel.com/football/nfl/los-angeles-chargers-@-kansas-city-chiefs-32705968",
  "https://mi.sportsbook.fanduel.com/football/nfl/green-bay-packers-@-denver-broncos-32705969",
  "https://mi.sportsbook.fanduel.com/football/nfl/miami-dolphins-@-philadelphia-eagles-32705975",
  "https://mi.sportsbook.fanduel.com/football/nfl/san-francisco-49ers-@-minnesota-vikings-32705977"
]

	games = ["https://mi.sportsbook.fanduel.com/football/nfl/jacksonville-jaguars-@-new-orleans-saints-32705962"]
	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away = convertNFLTeam(game.split(" @ ")[0])
		home = convertNFLTeam(game.split(" @ ")[1])
		game = f"{away} @ {home}"
		if game in lines:
			continue
		lines[game] = {}

		outfile = "outnfl"

		for tab in ["", "passing-props", "receiving-props", "rushing-props", "defensive-props", "1st-half", "2nd-half", "1st-quarter"]:
		#for tab in ["1st-half"]:
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])
			time.sleep(2.1)

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue
			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				marketType = data["attachments"]["markets"][market]["marketType"]
				runners = data["attachments"]["markets"][market]["runners"]

				prefix = ""
				if "1st half" in marketName or "first half" in marketName:
					prefix = "1h_"
				elif "2nd half" in marketName or "second half" in marketName:
					prefix = "2h_"
				elif "1st quarter" in marketName or "1st quarter" in marketName:
					prefix = "1q_"


				if marketName in ["moneyline"] or "any time touchdown" in marketName or "first touchdown" in marketName or marketName.startswith("1st half") or marketName.startswith("1st quarter") or marketName.startswith("alternate") or "total points" in marketName or marketName == "player to record a sack" or marketName.split(" - ")[-1] in ["pass completions", "passing tds", "passing attempts", "passing yds", "receiving yds", "receiving tds", "total receptions", "longest pass", "longest rush", "longest reception", "rushing yds", "rushing attempts", "rushing + receiving yds"]:

					prop = ""
					if "moneyline" in marketName:
						prop = "ml"
					elif "total points" in marketName or marketName.startswith("alternate total points"):
						if "/" in marketName:
							continue
						if "AWAY_TOTAL_POINTS" in marketType or "AWAY_TEAM_TOTAL_POINTS" in marketType:
							prop = "away_total"
						elif "HOME_TOTAL_POINTS" in marketType or "HOME_TEAM_TOTAL_POINTS" in marketType:
							prop = "home_total"
						else:
							prop = "total"
					elif "spread" in marketName or marketName.startswith("alternate spread"):
						if "/" in marketName:
							continue
						prop = "spread"
					elif marketName == "any time touchdown scorer":
						prop = "attd"
					elif marketName == "first touchdown scorer":
						prop = "ftd"
					elif marketName == "player to record a sack":
						prop = "sacks"
					elif " - " in marketName:
						if "total touchdowns" in marketName:
							continue
						marketName = marketName.split(" - ")[-1]
						prop = "_".join(marketName.split(" ")).replace("completions", "cmp").replace("tds", "td").replace("passing", "pass").replace("attempts", "att").replace("yds", "yd").replace("receiving", "rec").replace("total_receptions", "rec").replace("reception", "rec").replace("rushing", "rush")
						if prop == "rush_+_rec_yd":
							prop = "rush+rec"
					else:
						continue

					prop = f"{prefix}{prop}"

					handicap = runners[0]["handicap"]
					skip = 1 if prop in ["spread", "total", "attd", "sacks", "ftd"] else 2
					try:
						ou = str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
						if skip == 2:
							ou += "/"+str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					except:
						continue

					if runners[0]["runnerName"] == "Under":
						ou = str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])

					if "ml" in prop:
						lines[game][prop] = ou
					else:
						if prop not in lines[game]:
							lines[game][prop] = {}

						for i in range(0, len(runners), skip):
							handicap = str(float(runners[i]["handicap"]))
							try:
								odds = str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							except:
								continue
							if prop in ["spread", "total"]:
								handicap = str(float(runners[i]["runnerName"].split(" ")[-1][1:-1]))
								runnerType = runners[i]["result"]["type"]
								if "spread" in prop and runnerType in ["HOME", "UNDER"]:
									handicap = str(float(handicap) * -1)
								
								if handicap not in lines[game][prop]:
									lines[game][prop][handicap] = ""
								if runners[i]["result"]["type"] == "OVER" or runners[i]["result"]["type"] == "AWAY":
									lines[game][prop][handicap] = str(odds)+lines[game][prop][handicap]
								else:
									lines[game][prop][handicap] += f"/{odds}"
							elif "spread" in prop or "total" in prop:
								lines[game][prop][handicap] = ou
							else:
								if prop in ["attd", "ftd"]:
									player = parsePlayer(runners[i]["runnerName"])
									lines[game][prop][player] = odds
								elif prop == "sacks":
									player = parsePlayer(runners[i]["runnerName"].split(" to ")[0])
									if player not in lines[game][prop]:
										lines[game][prop][player] = odds
									else:
										if "not" in runners[i]["runnerName"]:
											lines[game][prop][player] += f"/{odds}"
										else:
											lines[game][prop][player] = f"{odds}/{lines[game][prop][player]}"
										lines[game][prop][player] = "0.5 "+lines[game][prop][player]
								else:
									player = parsePlayer(" ".join(runners[i]["runnerName"].split(" ")[:-1]))
									lines[game][prop][player] = f"{handicap} {ou}"
	
	with open(f"static/nfl/fanduelLines.json", "w") as fh:
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

def writeDK():
	url = "https://sportsbook.draftkings.com/leagues/football/nfl"

	mainCats = {
		"game lines": 492,
		"attd": 1003,
		"passing": 1000,
		"rush/rec": 1001,
		"defense": 1002,
		"quarters": 527,
		"halves": 526,
		"team": 530
	}
	
	subCats = {
		492: [4518, 13195, 13196, 9712],
		1000: [9525, 9524, 9522, 9517, 9516, 9526],
		1001: [9514, 9512, 9519, 9518, 9533, 9527, 9523, 12096],
		1002: [11812, 9521, 9529, 9520],
		530: [4653, 10514],
		526: [4631, 13582, 13584]
	}

	if False:
		mainCats = {
			"team": 530
		}
		subCats = {
			530: [10514],
		}

	lines = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/88808/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outnfl"
			call(["curl", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				game = event["name"].lower()
				games = []
				for team in game.split(" @ "):
					t = team.split(" ")[0].replace("jax", "jac")
					if "giants" in team:
						t += "g"
					elif "jets" in team:
						t += "j"
					elif "rams" in team:
						t += "r"
					elif "chargers" in team:
						t += "c"
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

							label = row["label"].lower().split(" [")[0]
							
							prefix = ""
							if "1st half" in label:
								prefix = "1h_"
							elif "2nd half" in label:
								prefix = "2h_"
							elif "1st quarter" in label:
								prefix = "1q_"

							if "moneyline" in label:
								label = "ml"
							elif "spread" in label:
								label = "spread"
							elif "team total points" in label:
								team = label.split(":")[0]
								t = team.split(" ")[0].replace("jax", "jac")
								if "giants" in team:
									t += "g"
								elif "jets" in team:
									t += "j"
								elif "rams" in team:
									t += "r"
								elif "chargers" in team:
									t += "c"
								if game.startswith(t):
									label = "away_total"
								else:
									label = "home_total"
							elif "total" in label:
								if "field goals" in label or "touchdown" in label:
									continue
								if "sacks" in label:
									label = "sacks"
									# uses o0.75, o0.25
									#continue
								else:
									label = "total"
							elif label == "first td scorer":
								label = "ftd"
							elif label == "anytime td scorer":
								label = "attd"
							elif label == "receptions":
								label = "rec"
							elif label.endswith("field goal made"):
								label = "fgm"
							elif label.endswith("kicking points"):
								label = "kicking_pts"
							elif label.endswith("tackles + assists"):
								label = "tackles+ast"
							elif label.endswith("total sacks"):
								label = "sacks"
							elif prop in ["pass tds", "pass yds", "rec tds", "rec yds", "rush tds", "rush yds", "interceptions", "longest pass", "longest rush", "longest reception", "pass attempts", "pass completions"]:
								label = prop.replace(" ", "_").replace("tds", "td").replace("yds", "yd").replace("interceptions", "int").replace("reception", "rec").replace("attempts", "att").replace("completions", "cmp")
							else:
								continue


							label = label.replace(" alternate", "")
							label = f"{prefix}{label}"

							if label == "halftime/fulltime":
								continue

							if "ml" not in label:
								if label not in lines[game]:
									lines[game][label] = {}

							outcomes = row["outcomes"]
							ou = ""
							try:
								ou = f"{outcomes[0]['oddsAmerican']}/{outcomes[1]['oddsAmerican']}"
							except:
								continue

							if "ml" in label:
								lines[game][label] = ou
							elif "total" in label or "spread" in label:
								for i in range(0, len(outcomes), 2):
									line = str(float(outcomes[i]["line"]))
									ou = f"{outcomes[i]['oddsAmerican']}"
									try:
										ou += f"/{outcomes[i+1]['oddsAmerican']}"
									except:
										pass
									lines[game][label][line] = ou
							elif label in ["ftd", "attd"]:
								for outcome in outcomes:
									player = parsePlayer(outcome["participant"].split(" (")[0])
									try:
										lines[game][label][player] = f"{outcome['oddsAmerican']}"
									except:
										continue
							else:
								player = parsePlayer(outcomes[0]["participant"].split(" (")[0])
								lines[game][label][player] = f"{outcomes[0]['line']} {outcomes[0]['oddsAmerican']}"
								if len(row["outcomes"]) > 1:
									lines[game][label][player] += f"/{outcomes[1]['oddsAmerican']}"

	with open("static/nfl/draftkings.json", "w") as fh:
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

def bvParlay():
	with open(f"{prefix}static/nfl/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/nfl/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/nfl/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nfl/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/nfl/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/nfl/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nfl/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/nfl/caesars.json") as fh:
		czLines = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines
	}

	ev = []
	evData = {}
	for game in bvLines:
		away, home = map(str, game.split(" @ "))
		if "td_parlay" not in bvLines[game]:
			continue
		abbr = {}
		shouldBreak = False
		for prop in ["rush_yd", "rec"]:
			try:
				for player in bvLines[game][prop]:
					abbr[player.split(" ")[0][0]+". "+player.split(" ")[-1]] = player
			except:
				shouldBreak = True

		if shouldBreak:
			continue

		for desc in bvLines[game]["td_parlay"]:
			tdParlay = bvLines[game]["td_parlay"][desc]
			if tdParlay["ml"] or (len(tdParlay["ftd"]) == 1 and len(tdParlay["attd"]) == 1):
				pass
			else:
				if tdParlay["ftd"] or "Anytime" not in desc or "1st" in desc:
					continue

			#if desc != "A.J. Brown & D'Andre Swift 1+ Anytime Touchdown Each":
			#	continue

			fairVals = []
			legs = []
			players = 0
			for prop in ["attd", "ftd"]:
				for player in tdParlay[prop]:
					players += 1
					if "." in player:
						try:
							player = abbr[player]
						except:
							continue
					maxOdds = []
					books = []
					for book in lines:
						if game in lines[book] and prop in lines[book][game] and player in lines[book][game][prop]:
								books.append(book)
								maxOdds.append(int(lines[book][game][prop][player].split("/")[0]))

					if not maxOdds:
						continue
					odds = max(maxOdds)
					idx = maxOdds.index(odds)
					book = books[idx]
					legs.append(f"{player.title()} {odds} {book.upper()}")
					if odds > 0:
						implied = 100 / (odds + 100)
					else:
						implied = -1*odds / (-1*odds + 100)

					fairVals.append(implied)

			if players != len(fairVals):
				continue

			if tdParlay["ml"]:
				maxOdds = []
				books = []
				for book in lines:
					if game in lines[book] and prop in lines[book][game]:
							i = 0
							if tdParlay["ml"] == home:
								i = 1
							books.append(book)
							maxOdds.append(int(lines[book][game]["ml"].split("/")[i]))

				if not maxOdds:
					continue
				odds = max(maxOdds)
				idx = maxOdds.index(odds)
				book = books[idx]
				legs.append(f"{tdParlay['ml'].upper()} ML {odds} {book.upper()}")
				if odds > 0:
					implied = 100 / (odds + 100)
				else:
					implied = -1*odds / (-1*odds + 100)
				fairVals.append(implied)

			odds = 1
			for o in fairVals:
				odds *= o
			
			fairValue = round((100 * (1 - odds)) / odds)

			evData[desc] = {}
			devig(evData, desc, str(fairValue), int(tdParlay["odds"]))
			if "ev" in evData[desc]:
				ev.append((evData[desc]["ev"], desc, fairValue, tdParlay['odds'], legs))

	for row in sorted(ev):
		print(f"{row[0]}, {row[1]}, fairval={row[2]}, bvOdds={row[3]} {row[4]}")
		pass

	output = "\t".join(["EV", "Parlay", "BV Odds", "Fair Value"])+"\n"
	for row in sorted(ev, reverse=True):
		arr = [row[0], row[1], row[3], row[2]]
		arr.extend(row[-1])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nfl/bvParlays.csv", "w") as fh:
		fh.write(output)


def writeEV(propArg="", bookArg="fd", teamArg="", notd=None, boost=None):

	if not boost:
		boost = 1

	#with open(f"{prefix}static/nfl/bet365.json") as fh:
	#	bet365Lines = json.load(fh)

	with open(f"{prefix}static/nfl/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/nfl/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/nfl/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/nfl/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nfl/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/nfl/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/nfl/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nfl/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/nfl/caesars.json") as fh:
		czLines = json.load(fh)

	# temp fix with FD locking us out
	if False:
		fdLines = {}
		for game in actionnetwork:
			fdLines[game] = {}

			for prop in actionnetwork[game]:
				fdLines[game][prop] = {}
				for player in actionnetwork[game][prop]:
					if "fanduel" in actionnetwork[game][prop][player]:
						fdLines[game][prop][player] = actionnetwork[game][prop][player]["fanduel"]

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines
	}

	with open(f"{prefix}static/nfl/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	teamGame = {}
	for game in pnLines:
		away, home = map(str, game.split(" @ "))
		teamGame[away] = teamGame[home] = game

	for game in mgmLines:
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
			if notd and prop in ["attd", "ftd"]:
				continue
			
			if prop in ["sacks", "spread", "1h_ml"]:
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
						except:
							player = handicap
							playerHandicap = ""
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
									if prop not in ["attd", "sacks", "ftd"] and playerHandicap != val.split(" ")[0]:
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
						if book and book != "-" and book.split("/")[0] != "-":
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
							print(key)
							continue
						if float(evData[key]["ev"]) > 0:
							#print(evData[key]["ev"], game, handicap, prop, int(line), ou, books)
							pass
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

	with open(f"{prefix}static/nfl/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def sortEV():
	with open(f"{prefix}static/nfl/ev.json") as fh:
		evData = json.load(fh)

	with open(f"static/nfl/totals.json") as fh:
		totals = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], d.get("pn_ev", 0), d["game"], player, d["playerHandicap"], d["line"], d["book"], j, d))

	for row in sorted(data):
		print(row[:-1])

	output = "\t".join(["EV", "EV Book", "Game", "Player", "Prop", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi", "CZ"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] != "attd":
			continue
		arr = [row[0], row[-1]["book"].upper().replace("KAMBI", "BR"), row[2].upper(), row[-1]["player"].title(), row[-1]["prop"]]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi", "cz"]:
			arr.append(row[-1]["bookOdds"].get(book, "-"))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nfl/attd.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "EV Book", "Game", "Player", "Prop", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi", "CZ"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] != "ftd":
			continue
		arr = [row[0], row[-1]["book"].upper().replace("KAMBI", "BR"), row[2].upper(), row[-1]["player"].title(), row[-1]["prop"]]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi", "cz"]:
			arr.append(row[-1]["bookOdds"].get(book, "-"))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nfl/ftd.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "PN EV", "EV Book", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi", "CZ", "AVG", "% Over", "Splits"]) + "\n"
	for row in sorted(data, reverse=True):
		player = row[-1]["player"]
		prop = row[-1]["prop"]
		if row[-1]["prop"] in ["attd", "ftd"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if player:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], row[-1].get("pn_ev", "-"), str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), row[2].upper(), player.title(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi", "cz"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		avg = over = 0
		splits = ""
		if "total" in prop:
			team = ""
			if "away" in prop:
				team = row[2].split(" @ ")[0]
			elif "home" in prop:
				team = row[2].split(" @ ")[1]
			
		elif player and player in totals and prop in totals[player]:
			avg = round(totals[player][prop] / totals[player]["gamesPlayed"], 1)
			a = [x for x in totals[player][prop+"Splits"] if x > float(row[-1]["playerHandicap"])]
			if row[-1]["under"]:
				a = [x for x in totals[player][prop+"Splits"] if x < float(row[-1]["playerHandicap"])]
			over = len(a) / len(totals[player][prop+"Splits"]) * 100
			splits = ",".join([str(int(x)) for x in totals[player][prop+"Splits"]])
			arr.extend([avg, f"{int(over)}", splits])
		elif player and player in totals and prop == "rush+rec":
			num = totals[player].get("rush_yd", 0) + totals[player]["rec_yd"]
			avg = round(num / totals[player]["gamesPlayed"], 1)
			a = []
			rushArr = totals[player].get("rush_ydSplits", [0]*len(totals[player]["rec_ydSplits"]))
			for rush, rec in zip(rushArr, totals[player]["rec_ydSplits"]):
				if not row[-1]["under"] and rush + rec > float(row[-1]["playerHandicap"]):
					a.append(rush+rec)
				elif row[-1]["under"] and rush + rec < float(row[-1]["playerHandicap"]):
					a.append(rush+rec)
			over = len(a) / len(totals[player]["rec_ydSplits"]) * 100
			splits = ",".join([str(int(x) + int(y)) for x, y in zip(rushArr, totals[player]["rec_ydSplits"])])
			arr.extend([avg, f"{int(over)}", splits])
		else:
			arr.extend(["-", "-", "-"])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nfl/props.csv", "w") as fh:
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
	parser.add_argument("--bvParlay", action="store_true", help="Bovada TD Parlay")
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
		writeMGM()

	if args.pb:
		writePointsbet()

	if args.dk:
		writeDK()

	if args.kambi:
		writeKambi()

	if args.pn:
		writePinnacle(args.date)

	if args.bv:
		writeBV()

	if args.bvParlay:
		bvParlay()

	if args.cz:
		writeCZ()

	if args.update:
		#writeFanduel()
		print("pn")
		writePinnacle(args.date)
		print("kambi")
		writeKambi()
		print("mgm")
		writeMGM()
		print("pb")
		writePointsbet()
		print("bv")
		writeBV()
		print("dk")
		writeDK()
		print("cz")
		writeCZ()
		writeActionNetwork()

	print(convertAmericanOdds(1 + (convertDecOdds(int(140)) - 1) * 1.5))
	print(convertAmericanOdds(1 + (convertDecOdds(int(-180)) - 1) * 1.5))

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, teamArg=args.team, notd=args.notd, boost=args.boost)

	if args.print:
		sortEV()

	if args.player:
		#with open(f"{prefix}static/nfl/draftkings.json") as fh:
		#	dkLines = json.load(fh)

		#with open(f"{prefix}static/nfl/bet365.json") as fh:
		#	bet365Lines = json.load(fh)

		with open(f"{prefix}static/nfl/fanduelLines.json") as fh:
			fdLines = json.load(fh)

		#with open(f"{prefix}static/nfl/bovada.json") as fh:
		#	bvLines = json.load(fh)

		with open(f"{prefix}static/nfl/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"{prefix}static/nfl/mgm.json") as fh:
			mgmLines = json.load(fh)

		with open(f"{prefix}static/nfl/pinnacle.json") as fh:
			pnLines = json.load(fh)
	
		player = args.player

		for game in mgmLines:
			for prop in mgmLines[game]:
				if args.prop and args.prop != prop:
					continue

				if player not in mgmLines[game][prop]:
					continue

				mgm = mgmLines[game][prop][player]
				dk = fd = bet365 = kambi = bv = mgm = pn = ""
				try:
					fd = fdLines[game][prop][player]
				except:
					pass
				try:
					bet365 = bet365Lines[game][prop][player]
				except:
					pass
				try:
					kambi = kambiLines[game][prop][player]
				except:
					pass
				try:
					bv = bvLines[game][prop][player]
				except:
					pass
				try:
					pn = pnLines[game][prop][player]
				except:
					pass

				print(f"{prop} fd='{fd}'\ndk='{dk}'\n365='{bet365}'\nkambi='{kambi}'\nbv='{bv}'\npn={pn}\nmgm={mgm}")
