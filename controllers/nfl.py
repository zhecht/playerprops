
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
	elif team.endswith("chiefs"):
		return "kc"
	elif team.endswith("saints"):
		return "no"
	elif team.endswith("buccaneers"):
		return "tb"
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

	with open(f"{prefix}static/nfl/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	teamGame = {}
	for game in fdLines:
		away, home = map(str, game.split(" @ "))
		if away not in teamGame:
			teamGame[away] = game
		if home not in teamGame:
			teamGame[home] = game

	props = ["56_first_touchdown_scorer", "62_anytime_touchdown_scorer", "60_longest_completion", "59_longest_reception", "58_longest_rush", "30_passing_attempts", "10_pass_completions", "11_passing_tds", "9_passing_yards", "17_receiving_tds", "16_receiving_yards", "15_receptions", "18_rushing_attempts", "13_rushing_tds", "12_rushing_yards", "70_tackles_assists"]

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
		else:
			prop = "_".join(actionProp.split("_")[1:]).replace("rushing", "rush").replace("passing", "pass").replace("receiving", "rec").replace("yards", "yd").replace("attempts", "att").replace("reception", "rec")
			if prop == "longest_completion":
				prop = "longest_pass"

		if prop.endswith("s"):
			prop = prop[:-1]

		with open(path) as fh:
			j = json.load(fh)

		if "markets" not in j:
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

	with open(f"{prefix}static/nfl/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def writePointsbet():
	url = "https://api.mi.pointsbet.com/api/v2/sports/american-football/events/featured?includeLive=false"
	outfile = f"outPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	for gameId in games:
		#print(gameId)
	#for gameId in [games[0]]:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"outPB"
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

			if prop.startswith("point spread"):
				prop = f"{prefix}spread"
			elif prop.startswith("moneyline"):
				if "3 way" in prop:
					continue
				prop = f"{prefix}ml"
			elif prop.startswith("total"):
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
			else:
				continue

			if "ml" not in prop:
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			if market["hiddenOutcomes"] and prop == "total":
				outcomes.extend(market["hiddenOutcomes"])
			skip = 1 if prop == "attd" else 2
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

				if "ml" in prop:
					res[game][prop] = ou
				elif prop == "attd":
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
					if "spread" in prop and points[0] != "-":
						points = "+"+points
					res[game][prop][points] = ou

	with open("static/nfl/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "outPN"
	game = games[gameId]

	#print(game)
	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o outPN'

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

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o outPN'

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
		prop = row["type"]
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
				if "spread" in prop and handicap[0] != "-":
					handicap = "+"+handicap
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

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/889/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o outPN'

	os.system(url)
	outfile = f"outPN"
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
	outfile = f"outBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

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

			if desc in ["game lines", "alternate lines", "touchdown scorers", "receiving props", "receiving yards", "qb yardage props", "qb passing totals", "rushing props", "rushing yards"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["description"].lower() == "first half":
						prefix = "1h_"
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
					elif prop.startswith("total passing attempts"):
						prop = "pass_att"
					elif prop.startswith("total passing completions"):
						prop = "pass_cmp"
					elif prop.startswith("longest pass completions"):
						prop = "longest_pass"
					elif prop.startswith("total interceptions"):
						prop = "int"
					elif prop.startswith("total rush attempts"):
						prop = "rush_att"
					elif prop.startswith("total rushing yards"):
						prop = "rush_yd"
					elif prop.startswith("total rush attempts"):
						prop = "rush_att"
					else:
						continue

					prop = f"{prefix}{prop}"

					if not len(market["outcomes"]):
						continue

					if "ml" not in prop and prop not in res[game]:
						res[game][prop] = {}

					if "ml" in prop:
						res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
					elif "total" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif "spread" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							handicap = market["outcomes"][i]["price"]["handicap"]
							if handicap[0] != "-":
								handicap = "+"+handicap
							res[game][prop][handicap] = ou
					elif prop == "attd":
						for i in range(0, len(market["outcomes"]), 1):
							player = parsePlayer(market["outcomes"][i]["description"])
							res[game][prop][player] = market["outcomes"][i]["price"]["american"].replace("EVEN", "100")
					else:
						handicap = market["outcomes"][0]["price"]["handicap"]
						player = parsePlayer(market["description"].split(" - ")[-1])
						res[game][prop][player] = f"{handicap} {market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")


	with open("static/nfl/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM():

	res = {}

	url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35"

	url = f"https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=11&regionId=9&competitionId=35&compoundCompetitionId=1:35&widgetId=/mobilesports-v1.0/layout/layout_us/modules/competition/defaultcontainereventsfutures-redesign&shouldIncludePayload=true"
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
		ids.append(row["id"])

	#ids = ["14277289"]
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
		for row in data["games"]:
			prop = row["name"]["value"].lower()

			prefix = player = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "1st quarter" in prop:
				prefix = "1q_"

			if prop.endswith("money line"):
				prop = "ml"
			elif prop == "total games" or "totals" in prop:
				prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif prop == "which player will score a touchdown in the game?":
				prop = "attd"
			elif prop.startswith("how many "):
				if prop.startswith("how many points will be scored in the game") or "field goals" in prop or "kicking" in prop or "extra points" in prop:
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
							p = "tackles_assists"
						else:
							continue
					elif p == "passing":
						p = "pass_"+prop.split(" ")[3].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "rushing":
						p = "rush_"+prop.split(" ")[3].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "receiving":
						p = "rec_"+prop.split(" ")[3].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "receptions":
						p = "rec"
					prop = p
			else:
				continue

			prop = prefix+prop

			results = row['results']
			ou = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
			if "ml" in prop:
				res[game][prop] = ou
			elif len(results) >= 2:
				skip = 1 if prop == "attd" else 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop and prop not in ["attd"]:
						continue
					else:
						val = val.split(" ")[-1]
					#print(game, prop, player)
					if prop == "attd":
						ou = str(results[idx]['americanOdds'])
					else:
						ou = f"{results[idx]['americanOdds']}/{results[idx+1]['americanOdds']}"

					if prop == "attd":
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
							if "spread" in prop and v[0] != "-":
								v = "+"+v
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
		away, home = map(str, game.split(" @ "))
		games = []
		for team in [away, home]:
			t = team.split(" ")[0]
			if t == "la":
				t = "lac"
				if "rams" in team:
					t = "lar"
			elif t == "ny":
				t = "nyj"
				if "giants" in team:
					t = "nyg"
			elif t == "jax":
				t = "jac"
			games.append(t)
		game = " @ ".join(games)
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	#eventIds = {'det @ kc': 1019645125}
	#data['det lions @ kc chiefs'] = {}
	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		#away, home = fullTeam[away], fullTeam[home]
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
			if label == "total points - including overtime":
				label = "total"
			elif "handicap - including overtime" in label:
				label = "spread"
			elif "handicap - 1st half" in label:
				label = "1h_spread"
			elif "handicap - 2nd half" in label:
				label = "2h_spread"
			elif "handicap - quarter 1" in label:
				label = "1q_spread"
			elif "total points - 1st half" in label:
				label = "1h_total"
			elif "total points - 2nd half" in label:
				label = "2h_total"
			elif "total points - quarter 1" in label:
				label = "1q_total"
			elif f"total points by {away} - quarter 1" in label:
				label = "1q_away_total"
			elif f"total points by {home} - quarter 1" in label:
				label = "1q_home_total"
			elif f"total points by {away} - 1st half" in label:
				label = "1h_away_total"
			elif f"total points by {home} - 1st half" in label:
				label = "1h_home_total"
			elif f"total points by {away} - including overtime" in label:
				label = "away_total"
			elif f"total points by {home} - including overtime" in label:
				label = "home_total"
			elif label == "including overtime":
				label = "ml"
			elif label == "draw no bet - 1st half":
				label = "1h_ml"
			elif label == "draw no bet - 2nd half":
				label = "2h_ml"
			elif label == "draw no bet - quarter 1":
				label = "1q_ml"
			elif label == "touchdown scorer - including overtime":
				playerProp = True
				label = "attd"
			elif (label.endswith("by the player - including overtime") or label.endswith("by the player")) and label.startswith("total"):
				playerProp = True
				label = "_".join(label[6:].replace(" - including overtime", "").split(" by the player")[0].split(" "))
				label = label.replace("passing", "pass").replace("yards", "yd").replace("rushing", "rush").replace("receiving", "rec").replace("touchdowns", "td").replace("receptions", "rec").replace("interceptions_thrown", "int")
				if "&" in label:
					continue
				if label == "touchdown_passes_thrown":
					label = "pass_td"
				elif label == "pass_completions":
					label = "cmp"
				elif "longest_rec" in label:
					label = "longest_rec"
				elif "longest_rush" in label:
					label = "longest_rush"
				elif "longest_completed" in label:
					label = "longest_pass"
				elif "defensive_tackles" in label:
					label = "tackles_assists"
			else:
				#print(label)
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
			else:
				if label not in data[game]:
					data[game][label] = {}
				if not playerProp:
					line = betOffer["outcomes"][0]["line"] / 1000
					if betOffer["outcomes"][0]["label"] == "Under" or convertNFLTeam(betOffer["outcomes"][0]["label"].lower()) == home:
						line = betOffer["outcomes"][1]["line"] / 1000
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					data[game][label][line] = ou
				elif label in ["attd"]:
					data[game][label][player] = ou
				else:
					line = betOffer["outcomes"][0]["line"] / 1000
					if betOffer["outcomes"][0]["label"] == "Under":
						line = betOffer["outcomes"][1]["line"] / 1000
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					if player not in data[game][label]:
						data[game][label][player] = {}
					data[game][label][player][line] = ou


	with open(f"{prefix}static/nfl/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

def parsePlayer(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")

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
  "https://mi.sportsbook.fanduel.com/football/nfl/detroit-lions-@-kansas-city-chiefs-32343729",
  "https://mi.sportsbook.fanduel.com/football/nfl/san-francisco-49ers-@-pittsburgh-steelers-32345213",
  "https://mi.sportsbook.fanduel.com/football/nfl/carolina-panthers-@-atlanta-falcons-32345218",
  "https://mi.sportsbook.fanduel.com/football/nfl/houston-texans-@-baltimore-ravens-32345221",
  "https://mi.sportsbook.fanduel.com/football/nfl/cincinnati-bengals-@-cleveland-browns-32345225",
  "https://mi.sportsbook.fanduel.com/football/nfl/tampa-bay-buccaneers-@-minnesota-vikings-32345228",
  "https://mi.sportsbook.fanduel.com/football/nfl/arizona-cardinals-@-washington-commanders-32345259",
  "https://mi.sportsbook.fanduel.com/football/nfl/tennessee-titans-@-new-orleans-saints-32345229",
  "https://mi.sportsbook.fanduel.com/football/nfl/jacksonville-jaguars-@-indianapolis-colts-32345288",
  "https://mi.sportsbook.fanduel.com/football/nfl/philadelphia-eagles-@-new-england-patriots-32344372",
  "https://mi.sportsbook.fanduel.com/football/nfl/las-vegas-raiders-@-denver-broncos-32345226",
  "https://mi.sportsbook.fanduel.com/football/nfl/los-angeles-rams-@-seattle-seahawks-32345266",
  "https://mi.sportsbook.fanduel.com/football/nfl/green-bay-packers-@-chicago-bears-32345275",
  "https://mi.sportsbook.fanduel.com/football/nfl/miami-dolphins-@-los-angeles-chargers-32345284",
  "https://mi.sportsbook.fanduel.com/football/nfl/dallas-cowboys-@-new-york-giants-32344726",
  "https://mi.sportsbook.fanduel.com/football/nfl/buffalo-bills-@-new-york-jets-32343946"
]

	lines = {}
	for game in games:
	#for game in [games[0]]:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away = convertNFLTeam(game.split(" @ ")[0])
		home = convertNFLTeam(game.split(" @ ")[1])
		game = f"{away} @ {home}"
		if game in lines:
			continue
		lines[game] = {}

		outfile = "outnfl"

		#for tab in ["", "passing-props", "receiving-props", "rushing-props", "1st-half", "2nd-half", "1st-quarter"]:
		for tab in ["", "passing-props", "receiving-props", "rushing-props"]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue
			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				runners = data["attachments"]["markets"][market]["runners"]

				if marketName in ["moneyline"] or "any time touchdown" in marketName or marketName.startswith("1st half") or marketName.startswith("1st quarter") or marketName.startswith("alternate") or marketName.split(" - ")[-1] in ["pass completions", "passing tds", "passing attempts", "passing yds", "receiving yds", "receiving tds", "total receptions", "longest pass", "longest rush", "longest reception", "rushing yds", "rushing attempts"]:
					prop = ""
					if marketName == "moneyline":
						prop = "ml"
					elif marketName == "total points" or marketName.startswith("alternate total points"):
						prop = "total"
					elif marketName == "1st half total points":
						prop = "1h_total"
					elif marketName == "1st quarter total points":
						prop = "1q_total"
					elif marketName == "spread" or marketName.startswith("alternate spread"):
						prop = "spread"
					elif marketName == "1st half moneyline":
						prop = "1h_ml"
					elif marketName == "1st half spread":
						prop = "1h_spread"
					elif marketName == "1st quarter moneyline":
						prop = "1q_ml"
					elif marketName == "1st quarter spread":
						prop = "1q_spread"
					elif marketName == "any time touchdown scorer":
						prop = "attd"
					elif " - " in marketName:
						marketName = marketName.split(" - ")[-1]
						prop = "_".join(marketName.split(" ")).replace("completions", "cmp").replace("tds", "td").replace("passing", "pass").replace("attempts", "att").replace("yds", "yd").replace("receiving", "rec").replace("total_receptions", "rec").replace("reception", "rec").replace("rushing", "rush")
					else:
						continue

					handicap = runners[0]["handicap"]
					ou = str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])

					if runners[0]["runnerName"] == "Under":
						ou = str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])

					if "ml" in prop:
						lines[game][prop] = ou
					else:
						if prop not in lines[game]:
							lines[game][prop] = {}

						skip = 1 if prop in ["spread", "total", "attd"] else 2
						for i in range(0, len(runners), skip):
							handicap = runners[i]["handicap"]
							odds = runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
							if prop in ["spread", "total"]:
								handicap = runners[i]["runnerName"].split(" ")[-1][1:-1]
								runnerType = runners[i]["result"]["type"]
								if "spread" in prop and runnerType in ["HOME", "UNDER"]:
									handicap = str(float(handicap) * -1)
									if handicap[0] != "-":
										handicap = "+"+handicap
								
								if str(handicap) not in lines[game][prop]:
									lines[game][prop][str(handicap)] = ""
								if runners[i]["result"]["type"] == "OVER" or runners[i]["result"]["type"] == "AWAY":
									lines[game][prop][str(handicap)] = str(odds)+lines[game][prop][str(handicap)]
								else:
									lines[game][prop][str(handicap)] += f"/{odds}"
							elif "spread" in prop or "total" in prop:
								lines[game][prop][str(handicap)] = ou
							else:
								if prop == "attd":
									player = parsePlayer(runners[i]["runnerName"])
									lines[game][prop][player] = str(odds)
								else:
									player = parsePlayer(" ".join(runners[i]["runnerName"].split(" ")[:-1]))
									lines[game][prop][player] = f"{handicap} {ou}"
	
	with open(f"{prefix}static/nfl/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr"):

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

		evData[player]["fairVal"] = fairVal
		evData[player]["implied"] = implied
	
	evData[player]["ev"] = ev

def writeDK():
	url = "https://sportsbook.draftkings.com/leagues/football/nfl"

	mainCats = {
		"game lines": 492,
		"attd": 1003,
		"passing": 1000,
		"rush/rec": 1001,
		"quarters": 527,
		"halves": 526,
		"team": 530
	}
	
	subCats = {
		492: [4518, 13195, 13196, 9712],
		1000: [9525, 9524, 9522, 9517, 9516, 9526],
		1001: [9514, 9512, 9519, 9518, 9533, 9527],
		530: [4653, 10514]
	}

	lines = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/88808/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outncaaf"
			call(["curl", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				game = event["name"].lower()
				away = game.split(" @ ")[0].split(" ")[0]
				home = game.split(" @ ")[1].split(" ")[0]
				game = f"{away} @ {home}"
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
							elif label.endswith("team total points"):
								team = label.split(":")[0]
								if game.startswith(team):
									label = "away_total"
								else:
									label = "home_total"
							elif "total" in label:
								if "field goals" in label or "touchdown" in label:
									continue
								label = "total"
							elif label == "first td scorer":
								label = "ftd"
							elif label == "anytime td scorer":
								label = "attd"
							elif label == "receptions":
								label = "rec"
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
									if "spread" in label and line[0] != "-":
										line = "+"+line
									lines[game][label][line] = f"{outcomes[i]['oddsAmerican']}/{outcomes[i+1]['oddsAmerican']}"
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

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines
	}

	with open(f"{prefix}static/nfl/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	teamGame = {}
	for game in pnLines:
		away, home = map(str, game.split(" @ "))
		teamGame[away] = teamGame[home] = game

	for game in mgmLines:
		if teamArg and teamArg not in game:
			continue
		for prop in mgmLines[game]:
			if propArg and prop != propArg:
				continue
			if notd and prop in ["attd", "ftd"]:
				continue

			if type(mgmLines[game][prop]) is not dict:
				continue
				pass

			handicaps = {}
			for book in lines:
				lineData = lines[book]
				if game in lineData and prop in lineData[game]:
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

					if game in actionnetwork and prop in actionnetwork[game] and handicap in actionnetwork[game][prop]:
						for book in actionnetwork[game][prop][handicap]:
							if book in ["betrivers", "mgm", "fanduel", "pointsbet", "caesars", "draftkings"]:
								continue
							val = actionnetwork[game][prop][handicap][book]
							
							if player:
								if type(val) is dict:
									if playerHandicap not in val:
										continue
									val = actionnetwork[game][prop][handicap][book][playerHandicap]
								else:
									if prop != "attd" and playerHandicap != val.split(" ")[0]:
										continue
									val = val.split(" ")[-1]

							try:
								o = val.split(" ")[-1].split("/")[i]
								ou = val.split(" ")[-1]
							except:
								if i == 1:
									continue
								o = val
								ou = val

							highestOdds.append(int(o))
							odds.append(ou)
							books.append(book)

					for book in lines:
						lineData = lines[book]
						if game in lineData and prop in lineData[game] and handicap in lineData[game][prop]:
							val = lineData[game][prop][handicap]

							if player:
								if type(val) is dict:
									if playerHandicap not in val:
										continue
									val = lineData[game][prop][handicap][playerHandicap]
								else:
									if prop != "attd" and playerHandicap != val.split(" ")[0]:
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

					#print(game, prop, handicap, highestOdds, books, odds)

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
					if kambi:
						books.append("kambi")
						l.append(kambi)
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

	data = []
	for player in evData:
		d = evData[player]
		data.append((d["ev"], d["game"], player, d["playerHandicap"], d["line"], d["book"], d["odds"], d))

	for row in sorted(data):
		print(row[:-1])

	output = "\t".join(["EV", "EV Book", "Game", "Player", "Prop", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] != "attd":
			continue
		arr = [row[0], row[-1]["book"], row[1].upper(), row[-1]["player"].title(), row[-1]["prop"]]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi"]:
			arr.append(row[-1]["bookOdds"].get(book, "-"))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nfl/attd.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "EV Book", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] in ["attd", "ftd"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], row[-1]["book"], row[1].upper(), row[-1]["player"].title(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
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
	parser.add_argument("--pb", action="store_true", help="Pointsbet")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("--pn", action="store_true", help="Pinnacle")
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

	if args.update:
		writeFanduel()
		writePinnacle(args.date)
		writeActionNetwork()
		writeKambi()
		writeMGM()
		writePointsbet()
		writeBV()
		writeDK()

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

	