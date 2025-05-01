
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
from glob import glob
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

try:
	from shared import *
except:
	from controllers.shared import *

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

	with open(f"{prefix}static/nba/draftkings.json") as fh:
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
		path = f"nbaout.json"
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

	with open(f"{prefix}static/nba/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)


def writeCZ(date, token=None):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v4/sports/baseball/competitions/5806c896-4eec-4de1-874f-afed93114b8c/tabs/schedule"
	outfile = "outCZ"
	cookie = ""
	with open("token") as fh:
		cookie = fh.read()

	os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: b51ee484-42d9-40de-81ed-5c6df2f3122a' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.15.1' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'Priority: u=4' -H 'TE: trailers' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"][:20]:
		games.append(event["id"])


	#games = ["aba11601-f98d-4fb8-9e27-b72bea37784e"]
	res = {}
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v4/events/{gameId}"
		time.sleep(0.2)
		os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: b51ee484-42d9-40de-81ed-5c6df2f3122a' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.15.1' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'Priority: u=4' -H 'TE: trailers' -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		if str(datetime.strptime(data["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue

		if "Daily" in data["name"]:
			continue

		game = data["name"].lower().replace("|", "").replace(" at ", " @ ")
		away = convertNBATeam(game.split(' @ ')[0])
		home = convertNBATeam(game.split(' @ ')[1])
		game = f"{away} @ {home}"
		res[game] = {}

		for market in data["markets"]:
			if not market["display"]:
				continue
			if "name" not in market:
				continue
			prop = market["name"].lower().replace("|", "").split(" (")[0]
			name = market["templateName"].lower().replace("|", "")

			prefix = player = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "2nd half" in prop:
				prefix = "2h_"
			elif "1st quarter" in prop:
				prefix = "1q_"
			elif "2nd quarter" in prop:
				prefix = "2q_"
			elif "3rd quarter" in prop:
				prefix = "3q_"
			elif "4th quarter" in prop:
				prefix = "4q_"

			if "money line" in prop:
				prop = "ml"
			elif ("total points" in prop or "alternative points" in prop) and "player" not in name:
				if "away points" in name:
					prop = "away_total"
				elif "home points" in name:
					prop = "home_total"
				else:
					prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif prop == "first 3pt field goal scorer":
				prop = "first_3ptm"
			elif "player total" in name:
				p = prop.split(" total")[0]
				player = parsePlayer(p)
				prop = prop.split(p+" ")[-1].replace("total ", "").replace("points + assists + rebounds", "pts+reb+ast").replace("points + assists", "pts+ast").replace("points + rebounds", "pts+reb").replace("rebounds + assists", "reb+ast").replace("blocks + steals", "blk+stl").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("steals", "stl").replace("blocks", "blk").replace("3pt field goals", "3ptm")
			else:
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			selections = market["selections"]
			skip = 1 if prop == "first_3ptm" else 2
			for i in range(0, len(selections), skip):
				try:
					ou = str(selections[i]["price"]["a"])
				except:
					continue
				if skip == 2:
					ou += f"/{selections[i+1]['price']['a']}"
					if selections[i]["name"].lower().replace("|", "") == "under":
						ou = f"{selections[i+1]['price']['a']}/{selections[i]['price']['a']}"

				if "ml" in prop:
					res[game][prop] = ou
				elif "spread" in prop:
					line = str(float(market["line"]) * -1)
					res[game][prop][line] = ou
				elif "total" in prop:
					try:
						line = str(float(market["line"]))
						res[game][prop][line] = ou
					except:
						continue
				elif skip == 1:
					player = parsePlayer(selections[i]["name"].replace("|", "").strip())
					res[game][prop][player] = ou
				else:
					line = str(float(market["line"]))
					res[game][prop][player] = {
						line: ou
					}

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


	with open("static/nba/caesars.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePointsbet(date):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://api.mi.pointsbet.com/api/v2/competitions/5/events/featured?includeLive=false&page=1"
	outfile = f"nbaoutPB"
	os.system(f"curl -s \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	#games = ["340247"]
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"nbaoutPB"
		os.system(f"curl -s \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		startDt = datetime.strptime(data["startsAt"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if startDt.day != int(date[-2:]):
			continue

		game = data["name"].lower()
		fullAway, fullHome = map(str, game.split(" @ "))
		game = f"{convertNBATeam(fullAway)} @ {convertNBATeam(fullHome)}"
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
			elif "2nd half" in prop:
				prefix = "2h_"
			elif "1st quarter" in prop:
				prefix = "1q_"
			elif "2nd quarter" in prop:
				prefix = "2q_"
			elif "3rd quarter" in prop:
				prefix = "3q_"
			elif "4th quarter" in prop:
				prefix = "4q_"

			if prop.startswith("point spread") or prop == "pick your own line":
				if "3 way" in prop:
					continue
				prop = f"{prefix}spread"
			elif prop.startswith("moneyline"):
				if "3 way" in prop:
					continue
				prop = f"{prefix}ml"
			elif prop.startswith("total") or prop == "alternate totals":
				if "band" in prop:
					continue
				prop = "total"
				prop = f"{prefix}total"
			elif prop.startswith(f"{fullAway} total"):
				prop = f"{prefix}away_total"
			elif prop.startswith(f"{fullHome} total"):
				prop = f"{prefix}home_total"
			elif prop.startswith("player points over/under"):
				prop = "pts"
			elif prop.startswith("player rebounds over/under"):
				prop = "reb"
			elif prop.startswith("player 3-pointers made"):
				prop = "3ptm"
			elif prop.startswith("player assists over/under"):
				prop = "ast"
			elif "over/under" in prop and "+" in prop:
				prop = prop.split(" over/under")[0].split("player ")[-1].replace(" + ", "+").replace("asts", "ast").replace("rebs", "reb").replace("assists", "ast").replace("points", "pts").replace("rebounds", "reb")
			else:
				continue

			if "ml" not in prop:
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			if market["hiddenOutcomes"] and prop in ["total"]:
				outcomes.extend(market["hiddenOutcomes"])
			skip = 2
			for i in range(0, len(outcomes), skip):
				points = str(outcomes[i]["points"])
				if outcomes[i]["price"] == 1:
					continue
				over = str(convertAmericanOdds(outcomes[i]["price"]))
				under = ""
				try:
					under = convertAmericanOdds(outcomes[i+1]["price"])
					ou = f"{over}/{under}"
					if ("spread" in prop or "ml" in prop) and outcomes[i]["side"] == "Home":
						ou = f"{under}/{over}"
					elif "total" in prop and outcomes[i]["name"].startswith("Under"):
						ou = f"{under}/{over}"
				except:
					pass

				if "ml" in prop:
					res[game][prop] = ou
				elif prop in ["pts", "reb", "3ptm", "ast"] or "+" in prop:
					player = parsePlayer(outcomes[i]["name"].lower().split(" over")[0])
					res[game][prop][player] = {
						outcomes[i]['name'].split(' ')[-1]: ou
					}
				else:
					if "spread" in prop and outcomes[i]["side"] == "Home":
						points = str(outcomes[i+1]["points"])
						ou = f"{under}/{over}"
					res[game][prop][points] = ou

	with open("static/nba/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "nbaoutPN"
	game = games[gameId]

	#print(game)
	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o nbaoutPN'

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
			prop = row["units"].lower().replace("points", "pts").replace("assists", "ast").replace("assist", "ast").replace("rebounds", "reb").replace("threepointfieldgoals", "3ptm").replace("ptsrebast", "pts+reb+ast")

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

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o nbaoutPN'

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
		elif keys[1] == "4":
			prefix = "2q_"
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

		if prop == "doubledouble":
			prop = "double-double"
		elif prop == "tripledouble":
			prop = "triple-double"

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
				handicap = str(prices[switched]["points"])
				if prop not in res[game]:
					res[game][prop] = {}

				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

def writePinnacle(date, debug):

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/basketball/nba/matchups/#period:0"

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/leagues/487/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o nbaoutPN'

	os.system(url)
	outfile = f"nbaoutPN"
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	for row in data:
		if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
		if row["type"] == "matchup" and not row["parent"]:
			player1 = convertNBATeam(row["participants"][0]["name"].lower())
			player2 = convertNBATeam(row["participants"][1]["name"].lower())
			games[str(row["id"])] = f"{player2} @ {player1}"

	res = {}
	#games = {'1580434847': 'phx @ gs'}
	retry = []
	for gameId in games:
		#print(gameId, games[gameId])
		parsePinnacle(res, games, gameId, retry, debug)

	#print(retry)
	for gameId in retry:
		parsePinnacle(res, games, gameId, retry, debug)

	with open("static/nba/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBV(date):

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.bovada.lv/sports/basketball/nba"

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/nba?marketFilterId=def&preMatchOnly=false&eventsLimit=5000&lang=en"
	outfile = f"nbaoutBV"

	os.system(f"curl -s \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	ids = []
	for row in data[0]["events"]:
		if str(datetime.fromtimestamp(row["startTime"] / 1000))[:10] != date:
			continue
		ids.append(row["link"])

	#ids = ["/football/nba/kansas-city-chiefs-jacksonville-jaguars-202309171300"]
	res = {}
	#print(ids)
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -s \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		if not data:
			continue

		comp = data[0]['events'][0]['competitors']
		game = data[0]['events'][0]['description'].lower()
		fullAway, fullHome = game.split(" @ ")
		game = f"{convertNBATeam(fullAway)} @ {convertNBATeam(fullHome)}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "player points", "player rebounds", "assists & threes", "blocks & steals", "player turnovers", "player combos"]:
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
					elif prop.startswith("total points -"):
						prop = "pts"
					elif prop.startswith("total assists -"):
						prop = "ast"
					elif prop.startswith("total blocks -"):
						prop = "blk"
					elif prop.startswith("total steals -"):
						prop = "stl"
					elif prop.startswith("total turnovers -"):
						prop = "to"
					elif prop.startswith("total made 3"):
						prop = "3ptm"
					elif prop.startswith("total points, rebounds"):
						prop = "pts+reb+ast"
					elif prop.startswith("total points and rebounds"):
						prop = "pts+reb"
					elif prop.startswith("total points and assists"):
						prop = "pts+ast"
					elif prop.startswith("total rebounds and assists"):
						prop = "reb+ast"
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
					else:
						try:
							handicap = market["outcomes"][0]["price"]["handicap"]
							player = parsePlayer(market["description"].split(" - ")[-1].split(" (")[0])
							ou = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}"
							if market["outcomes"][0]["description"] == "Under":
								ou = f"{market['outcomes'][1]['price']['american']}/{market['outcomes'][0]['price']['american']}"
							res[game][prop][player] = {
								handicap: ou.replace("EVEN", "100")
							}
						except:
							continue


	with open("static/nba/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM(date):

	if not date:
		date = str(datetime.now())[:10]

	res = {}

	url = "https://sports.mi.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004"

	url = f"https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=7&regionId=9&competitionId=6004&compoundCompetitionId=1:6004&widgetId=/mobilesports-v1.0/layout/layout_us/modules/competition/defaultcontainereventsfutures-redesign&shouldIncludePayload=true"
	outfile = f"nbaoutMGM"

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

	#ids = ["15373852"]
	for mgmid in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		data = data["fixture"]

		if " at " not in data["name"]["value"]:
			continue
		game = strip_accents(data["name"]["value"].lower().split(" (")[0]).replace(" at ", " @ ")
		fullTeam1, fullTeam2 = game.split(" @ ")
		game = f"{convertNBATeam(fullTeam1)} @ {convertNBATeam(fullTeam2)}"

		res[game] = {}
		d = data["games"]
		if not d:
			d = data["optionMarkets"]
		for row in d:
			prop = row["name"]["value"].lower()

			prefix = player = ""
			if "1st half" in prop or "first half" in prop:
				prefix = "1h_"
			elif "1st quarter" in prop or "first quarter" in prop:
				prefix = "1q_"

			if prop.endswith("money line"):
				prop = "ml"
			elif "totals" in prop:
				prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif "double-double in the game" in prop:
				player = parsePlayer(prop.split(" (")[0][5:])
				prop = "double-double"
			elif prop.startswith("how many ") or prop.split("): ")[-1] in ["points", "three-pointers made", "blocks", "steals", "rebounds", "assists"] or ("):" in prop and prop.split("): ")[-1].split(" ")[0] == "total"):
				if prop.startswith("how many points will be scored in the game") or "extra points" in prop:
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
					player = parsePlayer(prop.split(" (")[0].split(" will ")[-1])
					p = prop.split(" will ")[0].split(" total ")[-1].split(" many ")[-1]
					if "):" in prop:
						p = prop.split(": ")[-1].split("total ")[-1]
					p = p.replace(" and ", "+").replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("three-pointers", "3ptm").replace(", ", "+").replace("asssists", "ast")
					if p == "pts+reb s":
						p = "pts+reb"
					elif p in ["ast+reb", "assist+reb"]:
						p = "reb+ast"
					elif p == "pts reb+ast":
						p = "pts+reb+ast"
					elif p == "steams+blk":
						p = "stl+blk"
					prop = p
			else:
				continue

			if prop.startswith("teals"):
				continue

			prop = prefix+prop

			try:
				results = row.get('results', row['options'])
			except:
				continue
			price = results[0]
			if "price" in price:
				price = price["price"]
			if "americanOdds" not in price:
				continue

			ou = f"{price['americanOdds']}"
			if len(results) < 2:
				continue
			if "americanOdds" in results[1]:
				ou += f"/{results[1].get('americanOdds', results[1]['price']['americanOdds'])}"
			if "ml" in prop:
				res[game][prop] = ou
			elif len(results) >= 2:
				skip = 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop and prop not in ["double-double"]:
						continue
					else:
						val = val.split(" ")[-1]
					
					ou = f"{results[idx].get('americanOdds', results[idx]['price']['americanOdds'])}"
					try:
						ou += f"/{results[idx+1].get('americanOdds', results[idx+1]['price']['americanOdds'])}"
					except:
						pass

					if prop in ["double-double"]:
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = ou
					elif player:
						player = parsePlayer(player)
						val = val.replace(",", ".")
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = {
							val: ou
						}
					else:
						if prop not in res[game]:
							res[game][prop] = {}
						try:
							v = str(float(val))
							res[game][prop][v] = ou
						except:
							pass

	with open("static/nba/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi(date):

	if not date:
		date = str(datetime.now())[:10]

	data = {}
	outfile = f"outnba.json"
	url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/basketball/nba"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/basketball/nba/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -s \"{url}\" --connect-timeout 30 -o {outfile}")
	
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
			t = convertNBATeam(team)
			fullTeam[t] = team
			games.append(t)
		game = " @ ".join(games)
		#print(game, away, home)
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	#eventIds = {'lak @ den': 1020018038}
	#data['lak @ den'] = {}

	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		awayFull, homeFull = fullTeam[away], fullTeam[home]
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -s \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		if not j["betOffers"] or "closed" not in j["betOffers"][0]:
			continue

		if str(datetime.strptime(j["betOffers"][0]["closed"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=5))[:10] != date:
			continue

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
			elif "quarter 3" in label:
				prefix = "3q_"
			elif "quarter 4" in label:
				prefix = "4q_"

			if label.split(" -")[0] == "total points":
				label = "total"
			elif label.split(" -")[0] == "handicap":
				label = "spread"
			elif "total points by" in label:
				team = convertNBATeam(label.split(" by ")[-1].split(" - ")[0])
				if team == away:
					label = "away_total"
				else:
					label = "home_total"
			elif label == "including overtime":
				label = "ml"
			elif "double-double" in label:
				label = "double-double"
				playerProp = True
			elif label.endswith("by the player - including overtime"):
				playerProp = True
				label = label.replace(" - including overtime", "").split(" by the player")[0]
				label = label.replace("points scored", "pts").replace("points, rebounds & assists", "pts+reb+ast").replace("3-point field goals made", "3ptm").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk")

				if "&" in label:
					continue
			else:
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
				if convertNBATeam(betOffer["outcomes"][0]["participant"].lower()) == away:
					data[game][label] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]

			else:
				if label not in data[game]:
					data[game][label] = {}
				if not playerProp:
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer["outcomes"][0]["label"] == "Under" or convertNBATeam(betOffer["outcomes"][0]["label"].lower()) == home:
						line = str(betOffer["outcomes"][1]["line"] / 1000)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					data[game][label][line] = ou
				elif label == "double-double":
					data[game][label][player] = ou
				else:
					line = betOffer["outcomes"][0]["line"] / 1000
					if betOffer["outcomes"][0]["label"] == "Under":
						line = betOffer["outcomes"][1]["line"] / 1000
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					if player not in data[game][label]:
						data[game][label][player] = {}
					data[game][label][player][line] = ou


	with open(f"static/nba/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "").replace(" iv", "")
	player = player.strip()
	if player == "k caldwell pope":
		player = "kentavious caldwell pope"
	elif player == "cameron thomas":
		player = "cam thomas"
	elif player == "jadeney":
		player = "jaden ivey"
	elif player == "nicolas claxton":
		player = "nic claxton"
	elif player == "gregory jackson":
		player = "gg jackson"
	elif player == "alex sarr":
		return "alexandre sarr"
	return player

def writeESPN():
	js = """
	
	{
		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.split(" ")[0];
			if (t == "la") {
				if (team.includes("clippers")) {
					return "lac";
				}
				return "lal";
			} else if (t == "uta") {
				return "utah";
			}
			return t;
		}

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			return player;
		}

		let status = "";

		async function readPage(game) {

			//for (tab of ["lines", "player props"]) {
			//console.log(game);
			for (tab of ["player props"]) {
				for (let t of document.querySelectorAll("button[data-testid='tablist-carousel-tab']")) {
					if (t.innerText.toLowerCase() == tab && t.getAttribute("data-selected") == null) {
						t.click();
						break;
					}
				}
				if (tab != "lines") {
					while (!window.location.href.includes(tab.replace(" ", "_"))) {
						await new Promise(resolve => setTimeout(resolve, 500));
					}
				}
				await new Promise(resolve => setTimeout(resolve, 3000));

				for (detail of document.querySelectorAll("details")) {
					let prop = detail.querySelector("h2").innerText.toLowerCase();
					let isOU = false;

					if (prop.includes("o/u")) {
						isOU = true;
					}

					let skip = 2;
					let player = "";
					if (prop == "moneyline") {
						prop = "ml";
					} else if (prop == "game spread") {
						prop = "spread";
					} else if (prop == "total points") {
						prop = "total";
					} else if (prop.includes("double double")) {
						prop = "double_double";
						skip = 3;
					} else if (prop.includes("triple double")) {
						prop = "triple_double";
						skip = 3;
					} else if (prop.indexOf("player") == 0) {
						if (prop.includes("first") || prop.includes("type")) {
							continue;
						}
						prop = prop.replace("player total ", "").replace("player ", "").replace(" o/u", "").replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("turnovers", "to").replace(" and ", "+").replace(", ", "+").replace("field goals", "fg").replace("free throws", "ft").replace("3-pointers", "3pt").replace(" attempted", "a").replace(" made", "m").replaceAll(" ", "_");
						if (prop == "ast+reb") {
							prop = "reb+ast";
						}
						skip = 1;
						if (isOU) {
							if (["pts", "reb", "ast", "3ptm"].includes(prop)) {
								skip = 2;
							} else {
								skip = 3;
							}
						}
					} else {
						continue;
					}

					let open = detail.getAttribute("open");
					if (open == null) {
						detail.querySelector("summary").click();
						while (detail.querySelectorAll("button").length == 0) {
							await new Promise(resolve => setTimeout(resolve, 500));
						}
					}

					if (!data[game][prop]) {
						data[game][prop] = {};
					}

					let sections = [detail];
					if (skip == 2) {
						sections = detail.querySelectorAll("div[aria-label='']");
					}

					for (section of sections) {
						let btns = section.querySelectorAll("button");

						if (skip == 2) {
							player = parsePlayer(btns[0].parentElement.parentElement.previousSibling.innerText);
							let last = player.split(" ");
							player = player.split(" ")[0][0]+" "+last[last.length - 1];
						}
						for (i = 0; i < btns.length; i += skip) {
							if (btns[i].innerText == "See All Lines") {
								continue;
							}
							if (skip != 3 && btns[i].getAttribute("disabled") != null) {
								continue;
							}

							let idx = i;
							if (skip == 3) {
								idx += 1;
							}

							let ou = "";
							try {
								ou = btns[idx].querySelectorAll("span")[1].innerText;
							} catch (err) {
								continue;
							}
							
							if (skip != 1 && btns[idx+1].getAttribute("disabled") == null) {
								ou += "/"+btns[idx+1].querySelectorAll("span")[1].innerText;
							}

							ou = ou.replace("Even", "+100");

							if (skip == 3) {
								player = parsePlayer(btns[i].innerText.toLowerCase().split(" total")[0].split(" to record")[0]);
								let last = player.split(" ");
								player = player.split(" ")[0][0]+" "+last[last.length - 1];
							}

							//console.log(prop, player, ou);

							if (prop == "ml") {
								data[game][prop] = ou;
							} else if (prop == "double_double" || prop == "triple_double") {
								data[game][prop][player] = ou;
							} else if (skip == 1) {
								player = parsePlayer(btns[i].parentElement.parentElement.querySelector("th").innerText);
								last = player.split(" ");
								player = player.split(" ")[0][0]+" "+last[last.length - 1];
								if (!data[game][prop][player]) {
									data[game][prop][player] = {};
								}
								line = btns[i].parentElement.id.split("-");
								line = (parseFloat(line[line.length - 1].replace("+", "")) - 0.5).toString();
								data[game][prop][player][line] = ou;
							} else {
								let line = btns[idx].querySelector("span").innerText;
								if (line.includes("+")) {
									line = (parseFloat(line.replace("+", "")) - 0.5).toFixed(1);
								} else {
									line = line.split(" ")[1];
								}

								if (!player) {
									continue;
								}

								if (!data[game][prop][player]) {
									data[game][prop][player] = {};
								}

								if (data[game][prop][player][line]) {
									let over = data[game][prop][player][line];
									if (parseInt(ou.split("/")[0]) > parseInt(over)) {
										over = ou.split("/")[0];
									}
									if (ou.includes("/")) {
										over += "/"+ou.split("/")[1];
									}
									data[game][prop][player][line] = over;
								} else {
									data[game][prop][player][line] = ou;
								}
							}
						}
					}
				}
			}
			status = "done";
		}

		async function main() {

			let awayTeam = convertTeam(document.querySelector("div[data-testid=away-team-card] h2").innerText);
			let homeTeam = convertTeam(document.querySelector("div[data-testid=home-team-card] h2").innerText);
			let game = awayTeam + " @ " + homeTeam;
			
			data[game] = {};

			status = "";
			readPage(game);

			while (status != "done") {
				await new Promise(resolve => setTimeout(resolve, 2000));
			}

			console.log(data);
		}

		main();
	}
	"""

def writeFanduelManual():
	js = """

	let data = {};
	{

		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.toLowerCase().substring(0, 3);
			if (t == "gol") {
				t = "gs";
			} else if (t == "san") {
				t = "sa";
			} else if (t == "bro") {
				t = "bkn";
			} else if (t == "okl") {
				t = "okc";
			} else if (t == "pho") {
				t = "phx";
			} else if (t == "uta") {
				t = "utah";
			} else if (t == "was") {
				t = "wsh";
			} else if (t == "los") {
				if (team.indexOf("clippers") > 0) {
					t = "lac";
				} else if (team.indexOf("lakers") > 0) {
					t = "lal";
				}
			} else if (t == "new") {
				t = "no";
				if (team.indexOf("knicks") > 0) {
					t = "ny";
				}
			}
			return t;
		}

		function parsePlayer(player) {
			return player.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
		}

		let game = document.querySelector("h1").innerText.toLowerCase().replace(" odds", "");
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
			let prefix = "";
			let label = arrow.innerText.toLowerCase();
			if (label.indexOf("game lines") >= 0) {
				prop = "lines";
			} else if (label.indexOf("player") >= 0) {
				player = true;

				if (label.indexOf("most") >= 0 || label.indexOf("of the game") >= 0 || label.indexOf("first") >= 0 || label.indexOf("blocks, and steals") >= 0 || label.indexOf("matchbet") >= 0) {
					continue
				}

				if (label.indexOf("pts + reb + ast") >= 0) {
					prop = "pts+reb+ast";
				} else if (label.indexOf("reb + ast") >= 0) {
					prop = "reb+ast";
				} else if (label.indexOf("pts + reb") >= 0) {
					prop = "pts+reb";
				} else if (label.indexOf("pts + ast") >= 0) {
					prop = "pts+ast";
				} else if (label.indexOf("assists") >= 0) {
					prop = "ast";
				} else if (label.indexOf("rebounds") >= 0) {
					prop = "reb";
				} else if (label.indexOf("made threes") >= 0) {
					prop = "3ptm";
				} else if (label.indexOf("points") >= 0) {
					prop = "pts";
				} else if (label.indexOf("steals") >= 0) {
					prop = "stl";
				} else if (label.indexOf("blocks") >= 0) {
					prop = "blk";
				}
			} else if (label.indexOf("alternative spread") >= 0) {
				prop = "spread";
			} else if (label.indexOf("alternate total points") >= 0) {
				prop = "total";
			} else if (label.indexOf(awayName+" total points") >= 0 || label == "away team total points") {
				prop = "away_total";
			} else if (label.indexOf(homeName+" total points") >= 0 || label == "home team total points") {
				prop = "home_total";
			} else if (label.indexOf("double double") >= 0) {
				prop = "double_double";
			} else if (label.indexOf("triple double") >= 0) {
				prop = "triple_double";
			}

			if (label.indexOf("1st half") >= 0) {
				prefix = "1h";
			} else if (label.indexOf("2nd half") >= 0) {
				prefix = "2h";
			}

			if (prefix) {
				if (label.indexOf("alternate") >= 0) {
					continue;
				}

				if (label.indexOf("winner") >= 0) {
					prop = "ml";
				} else if (label.indexOf("spread") >= 0) {
					prop = "spread";
				} else if (label.indexOf("total points") >= 0) {
					prop = "total";
				}
				if (!prop) {
					continue;
				}
				prop = prefix+"_"+prop;
				//continue;
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
			el = arrow.parentElement.parentElement.querySelector("div[aria-label='Show more correct score options']");
			if (el) {
				el.click();
			}

			if (prop != "lines" && !data[game][prop]) {
				data[game][prop] = {};
			}

			let skip = 1;
			if (["away_total", "home_total"].indexOf(prop) >= 0 || player) {
				skip = 2;
			} else if (prefix) {
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
				if (!ariaLabel || ariaLabel.indexOf("Show more") >= 0 || ariaLabel.indexOf("Show less") >= 0 || ariaLabel.indexOf("unavailable") >= 0) {
					continue;
				}
				let odds = ariaLabel.split(", ")[1];

				//console.log(btn, odds);

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

					odds = ariaLabel.split(", ")[1].split(" ")[0];
					line = line.replace("+", "");

					if (line == "1.5") {
						//console.log(odds, line, isAway);
					}

					if (isAway) {
						if (data[game][prop][line] == undefined) {
							data[game][prop][line] = odds;
						} else {
							data[game][prop][line] = odds + "/" + data[game][prop][line].replace("-/", "");
						}
					} else if (!data[game][prop][line]) {
						data[game][prop][line] = "-/"+odds;
					} else {
						data[game][prop][line] += "/"+odds;
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
				} else if (prop == "1h_ml" || prop == "2h_ml") {
					data[game][prop] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[1];
				} else if (prefix) {
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (prop == "1h_total") {
						line = ariaLabel.split(", ")[2].split(" ")[1];
						odds = ariaLabel.split(", ")[3].split(" ")[0];
						data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
					} else {
						data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
					}
				} else if (prop == "away_total" || prop == "home_total") {
					line = ariaLabel.split(", ")[2].split(" ")[1];
					odds = ariaLabel.split(", ")[3].split(" ")[0];
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
				} else if (skip == 2 && player) {
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
					try {
						data[game][prop][player][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2].split(" ")[0];
					} catch {
						data[game][prop][player][line] = odds;
					}
				} else if (skip == 2) {
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop] = {};
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
				} else {
					player = parsePlayer(ariaLabel.split(",")[0]);
					if (player.length == 0) {
						continue;
					}

					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}

					if (["double_double", "triple_double"].indexOf(prop) >= 0) {
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
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("basketball/nba") >= 0) {
				urls[a.href] = 1;
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
	"https://sportsbook.fanduel.com/basketball/nba/new-orleans-pelicans-@-orlando-magic-33121993",
	"https://sportsbook.fanduel.com/basketball/nba/sacramento-kings-@-washington-wizards-33121994",
	"https://sportsbook.fanduel.com/basketball/nba/chicago-bulls-@-houston-rockets-33121995",
	"https://sportsbook.fanduel.com/basketball/nba/brooklyn-nets-@-milwaukee-bucks-33121996",
	"https://sportsbook.fanduel.com/basketball/nba/utah-jazz-@-dallas-mavericks-33121998",
	"https://sportsbook.fanduel.com/basketball/nba/new-york-knicks-@-denver-nuggets-33121999",
	"https://sportsbook.fanduel.com/basketball/nba/atlanta-hawks-@-phoenix-suns-33121997",
	"https://sportsbook.fanduel.com/basketball/nba/boston-celtics-@-detroit-pistons-33124791",
	"https://sportsbook.fanduel.com/basketball/nba/oklahoma-city-thunder-@-toronto-raptors-33124795"
]
	
	#games = ["https://mi.sportsbook.fanduel.com/basketball/nba/milwaukee-bucks-@-charlotte-hornets-32803962"]
	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away = convertNBATeam(game.split(" @ ")[0])
		home = convertNBATeam(game.split(" @ ")[1])
		game = f"{away} @ {home}"
		if game in lines:
			continue
		lines[game] = {}

		outfile = "outnba"

		for tab in ["", "player-points", "player-threes", "player-rebounds", "player-assists", "player-combos", "player-defense"]:
		#for tab in ["player-combos"]:
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", url, "-o", outfile])
			time.sleep(0.6)

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

				alt = False
				if marketName in ["moneyline"] or marketName.startswith("1st half") or marketName.startswith("1st quarter") or marketName.startswith("alternative") or marketName.startswith("to score") or marketName.startswith("to record") or "made threes" in marketName or marketName.split(" - ")[-1] or "+" in marketName in ["first basket", "total points", "points", "assists", "rebounds", "steals", "blocks", "made threes", "spread betting", "home team total points", "away team total points"]:

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
					elif "spread" in marketName or marketName.startswith("alternative spread"):
						if "/" in marketName:
							continue
						if "alternative" in marketName:
							alt = True
						prop = "spread"
					elif marketName == "first basket":
						prop = "1st_fg"
					elif marketName in ["to record a double double"]:
						prop = "double_double"
						alt = True
					elif marketName in ["to record a triple double"]:
						prop = "triple_double"
						alt = True
					elif marketName.startswith("to score") or marketName.startswith("to record") or ("made threes" in marketName and "-" not in marketName):
						prop = "_".join(marketName.split("+ ")[-1].split(" ")).replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("made_threes", "3ptm")
						alt = True
					elif " - " in marketName:
						marketName = marketName.split(" - ")[-1]
						prop = "_".join(marketName.split(" ")).replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("made_threes", "3ptm")
						if "+" in prop:
							prop = prop.replace("_", "")
					else:
						continue

					prop = f"{prefix}{prop}"

					handicap = runners[0]["handicap"]
					skip = 1 if alt or prop in ["1st_fg"] else 2
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
								ou = str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
								if skip == 2:
									ou += "/"+str(runners[i+1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
									if runners[i]["runnerName"] == "Under":
										ou = str(runners[i+1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							except:
								continue
							if alt and prop == "spread":
								handicap = str(float(runners[i]["runnerName"].split(" ")[-1]))
								if runners[i]["result"]["type"] == "HOME":
									handicap = str(float(handicap) * -1)
									if handicap in lines[game][prop]:
										lines[game][prop][handicap] += "/"+ou
									else:
										lines[game][prop][handicap] = "/"+ou	
								else:
									if handicap in lines[game][prop]:
										lines[game][prop][handicap] = ou+"/"+lines[game][prop][handicap]
									else:
										lines[game][prop][handicap] = ou
							elif "spread" in prop or "total" in prop:
								lines[game][prop][handicap] = ou
							elif prop == "1st_fg" or prop in ["double_double", "triple_double"]:
								player = parsePlayer(runners[i]["runnerName"])
								lines[game][prop][player] = ou
							elif alt:
								player = parsePlayer(runners[i]["runnerName"])
								if player not in lines[game][prop]:
									lines[game][prop][player] = {}
								if prop == "3ptm":
									handicap = str(float(marketName.split(" ")[0][:-1]) - 0.5)
								else:
									handicap = str(float(marketName.split(" ")[2][:-1]) - 0.5)
								lines[game][prop][player][handicap] = ou
							else:
								player = parsePlayer(" ".join(runners[i]["runnerName"].split(" ")[:-1]))
								if player not in lines[game][prop]:
									lines[game][prop][player] = {}
								lines[game][prop][player][handicap] = ou
	
	with open(f"static/nba/fanduel.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def averageOdds(odds):
	avgOver = []
	avgUnder = []
	for o in odds:
		if o and o != "-" and o.split("/")[0] != "-":
			avgOver.append(convertDecOdds(int(o.split("/")[0])))
			if "/" in o:
				avgUnder.append(convertDecOdds(int(o.split("/")[1])))

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

	ou = f"{avgOver}/{avgUnder}"
	if ou.endswith("/-"):
		ou = ou.split("/")[0]
	return ou

def getFairValue(ou, method=None):
	try:
		over = int(ou.split("/")[0])
	except:
		return
	if over > 0:
		impliedOver = 100 / (over+100)
	else:
		impliedOver = -1*over / (-1*over+100)

	# assume 7.1% vig if no under
	if "/" not in ou:
		u = 1.071 - impliedOver
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

	# power method
	x = impliedOver
	y = impliedUnder
	while round(x+y, 8) != 1.0:
		k = math.log(2) / math.log(2 / (x+y))
		x = x**k
		y = y**k

	mult = impliedOver / (impliedOver + impliedUnder)
	add = impliedOver - (impliedOver+impliedUnder-1) / 2
	implied = min(x,mult,add)
	if method == "mult":
		return mult
	elif method == "add":
		return add
	elif method == "power":
		return x
	return implied

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

	if prop == "first_3ptm":
		mult = impliedOver
		ev = mult * profit + (1-mult) * -1 * bet
		ev = round(ev, 1)
		if player not in evData:
			evData[player] = {}
		evData[player][f"{prefix}fairVal"] = 0
		evData[player][f"{prefix}implied"] = 0
		
		evData[player][f"{prefix}ev"] = ev
		return

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

def writeDK(date, debug, keep):
	url = "https://sportsbook.draftkings.com/leagues/football/nba"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 487,
		"points": 1215,
		"rebounds": 1216,
		"assists": 1217,
		"threes": 1218,
		"blocks/steals": 1219,
		"combos": 583,
		"team": 523,
		"defense": 1293,
		"halves": 520,
		"quarters": 522,
		#"quick hits": 1157
	}
	
	subCats = {
		487: [4511, 13202, 13201],
		520: [4598, 4599, 6230, 14648, 12952],
		522: [4600, 4601, 4602, 4603],
		#487: [4511],
		1215: [12488, 16477],
		1216: [12492, 16479],
		1217: [12495, 16478],
		1218: [12497, 16480],
		1219: [12499, 12500, 12502],
		583: [16483, 16482, 16481, 9974, 5001, 9976, 9973],
		523: [4609, 14182],
		1157: [14793],
		1293: [13782, 13780, 13508, 13781, 16485, 16484],
	}

	propIds = {12488: "pts", 16477: "pts-alt", 12492: "reb", 16479: "reb-alt", 12495: "ast", 16478: "ast-alt", 12497: "3ptm", 16480: "3ptm-alt", 9976: "pts+reb-alt", 9973: "pts+ast-alt", 9974: "reb+ast-alt", 12499: "blk-alt", 12500: "stl-alt", 12502: "stl+blk-alt", 12504: "to-alt", 14793: "first_3ptm",
		16483: "pts+reb+ast-alt", 16482: "pts+reb-alt", 16481: "pts+ast-alt",
		9974: "reb+ast", 5001: "pts+reb+ast", 9976: "pts+reb", 9973: "pts+ast",
		13782: "to", 13780: "blk", 13508: "stl", 13781: "stl+blk", 16485: "stl-alt", 16484: "blk-alt"
	}

	if debug:
		mainCats = {
			#"game lines": 487,
			#"team": 523,
			#"halves": 520,
			"quarters": 522,
		}
		subCats = {
			487: [4511, 13202, 13201],
			523: [4609, 14182],
			520: [4598, 4599, 6230, 14648, 12952, 15599, 16720],
			522: [4600, 4601, 4602, 4603]
		}

	cookie = """-H 'Cookie: hgg=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWQiOiIxODU4ODA5NTUwIiwiZGtoLTEyNiI6IjgzM1RkX1lKIiwiZGtlLTEyNiI6IjAiLCJka2UtMjA0IjoiNzEwIiwiZGtlLTI4OCI6IjExMjgiLCJka2UtMzE4IjoiMTI2MCIsImRrZS0zNDUiOiIxMzUzIiwiZGtlLTM0NiI6IjEzNTYiLCJka2UtNDI5IjoiMTcwNSIsImRrZS03MDAiOiIyOTkyIiwiZGtlLTczOSI6IjMxNDAiLCJka2UtNzU3IjoiMzIxMiIsImRrZS04MDYiOiIzNDI2IiwiZGtlLTgwNyI6IjM0MzciLCJka2UtODI0IjoiMzUxMSIsImRrZS04MjUiOiIzNTE0IiwiZGtlLTgzNiI6IjM1NzAiLCJka2gtODk1IjoiOGVTdlpEbzAiLCJka2UtODk1IjoiMCIsImRrZS05MDMiOiIzODQ4IiwiZGtlLTkxNyI6IjM5MTMiLCJka2UtOTQ3IjoiNDA0MiIsImRrZS05NzYiOiI0MTcxIiwiZGtoLTE2NDEiOiJSMGtfbG1rRyIsImRrZS0xNjQxIjoiMCIsImRrZS0xNjUzIjoiNzEzMSIsImRrZS0xNjg2IjoiNzI3MSIsImRrZS0xNjg5IjoiNzI4NyIsImRrZS0xNzU0IjoiNzYwNSIsImRrZS0xNzYwIjoiNzY0OSIsImRrZS0xNzc0IjoiNzcxMCIsImRrZS0xNzgwIjoiNzczMSIsImRrZS0xNzk0IjoiNzgwMSIsImRraC0xODA1IjoiT0drYmxrSHgiLCJka2UtMTgwNSI6IjAiLCJka2UtMTgyOCI6Ijc5NTYiLCJka2UtMTg2MSI6IjgxNTciLCJka2UtMTg2OCI6IjgxODgiLCJka2UtMTg4MyI6IjgyNDMiLCJka2UtMTg5OCI6IjgzMTMiLCJka2gtMTk1MiI6ImFVZ2VEWGJRIiwiZGtlLTE5NTIiOiIwIiwiZGtzLTIwNzkiOiI5MTMzIiwiZGtlLTIwOTciOiI5MjA1IiwiZGtlLTIxMDAiOiI5MjIzIiwiZGtlLTIxMDMiOiI5MjQyIiwiZGtlLTIxMzUiOiI5MzkzIiwiZGtlLTIxNDEiOiI5NDM0IiwiZGtoLTIxNTAiOiJOa2JhU0Y4ZiIsImRrZS0yMTUwIjoiMCIsImRrZS0yMTYxIjoiOTUxNSIsImRrZS0yMTY1IjoiOTUzNSIsImRrcy0yMDE5IjoiODg0OCIsImRrcy0yMDIwIjoiODg1MCIsImRrZS0yMDYyIjoiOTA0OCIsImRrcy0yMTkzIjoiOTY1OSIsImRrcy0yMTk0IjoiOTY2MyIsImRrZS0yMTk1IjoiOTY2NSIsImRrZS0yMjIwIjoiOTc2OCIsImRrZS0yMjIyIjoiOTc3NCIsImRraC0yMjI0IjoicjBFQ0xod3MiLCJka2UtMjIyNCI6IjAiLCJka2UtMjIyNiI6Ijk3ODkiLCJka2UtMjIzNyI6Ijk4MzQiLCJka2UtMjIzOCI6Ijk4MzciLCJka2UtMjI0MCI6Ijk4NTciLCJka2UtMjI0MSI6Ijk4NjUiLCJka2UtMjI0MyI6Ijk4NzIiLCJka2UtMjI0NiI6Ijk4ODciLCJka2UtMjI2NCI6Ijk5NzAiLCJka2UtMjI4MSI6IjEwMDQyIiwiZGtlLTIyODgiOiIxMDA5MiIsImRrZS0yMjg5IjoiMTAwOTYiLCJka2UtMjI5MSI6IjEwMTAzIiwiZGtoLTIyOTIiOiJNbHdDUVFVTSIsImRrZS0yMjkyIjoiMCIsImRrZS0yMjk0IjoiMTAxMjYiLCJka2UtMjMwMyI6IjEwMjAwIiwiZGtlLTIzMDQiOiIxMDIwMyIsImRrZS0yMzEwIjoiMTAyNDYiLCJka2UtMjMxMSI6IjEwMjUwIiwiZGtlLTIzMTIiOiIxMDI1OCIsImRrZS0yMzE0IjoiMTAyNjMiLCJka2UtMjMxNiI6IjEwMjcxIiwiZGtlLTIzMTgiOiIxMDI4MCIsImRrZS0yMzIyIjoiMTAzMDciLCJka2UtMjMyNCI6IjEwMzIzIiwiZGtlLTIzMjciOiIxMDMzNCIsImRrZS0yMzI4IjoiMTAzMzgiLCJka2gtMjMzMSI6Ikd6ZXlsRG9YIiwiZGtlLTIzMzEiOiIwIiwiZGtlLTIzMzMiOiIxMDM3MSIsImRraC0yMzM2IjoieTNOOXlUU3giLCJka2UtMjMzNiI6IjAiLCJka2gtMjMzNyI6IlNrQkV5N0FQIiwiZGtlLTIzMzciOiIwIiwiZGtlLTIzMzgiOiIxMDM5NCIsImRrZS0yMzM5IjoiMTAzOTYiLCJka2UtMjM0MCI6IjEwNDA0IiwiZGtlLTIzNDEiOiIxMDQwNiIsImRrZS0yMzQyIjoiMTA0MTEiLCJka2gtMjM0NSI6ImJSRHR3U2lGIiwiZGtlLTIzNDUiOiIwIiwiZGtlLTIzNDYiOiIxMDQzMyIsImRrZS0yMzQ5IjoiMTA0NTgiLCJka2gtMjM1MCI6IlIyUXM3ZlpuIiwiZGtlLTIzNTAiOiIwIiwibmJmIjoxNzQ1NTM1ODkxLCJleHAiOjE3NDU1MzYxOTEsImlhdCI6MTc0NTUzNTg5MSwiaXNzIjoiZGsifQ.nnpD2pzFwlcagGpJRlvlp93wrCwtO79WiNIXDjh4lhk; STE="2025-04-24T23:35:10.1089114Z"; STIDN=eyJDIjoxMjIzNTQ4NTIzLCJTIjo5MTg3MDE2MDczMSwiU1MiOjk1ODM5MzI0MDE4LCJWIjoxODU4ODA5NTUwLCJMIjoxLCJFIjoiMjAyNS0wNC0yNFQyMzoyOToyNS43MDU2OTY2WiIsIlNFIjoiVVMtREsiLCJVQSI6ImplenpPMFA0eDZrRDlKWDNON3hNWDNXOFZlQVlaSG05STcxZ2g5N1FRU0U9IiwiREsiOiI2OGU5OWVkYi1kOWY4LTQ2ZTctYWVhMC05YmZiMDJhMWE1OTkiLCJESSI6ImViMDY0ZWM5LTUzNjYtNDc0Ny05ZDhiLThlZjUwM2FkNTMxZCIsIkREIjo1NzkxNDk4ODQwNX0=; STH=0a3f6f71ed3edde2f5ae4712e7fb8f89807c9066f284f0fd055c87548e908a0d; _abck=79207192B7A8C5C29A826D0111889DD3~0~YAAQ7xw/F7X6jkqWAQAALAEHag3jslEBQFv7soz5TMjRXZI8HsQAmsKx1RrZP0qeK/WA19+da4oS6boIHsAvgpCnP1quIdDP07FujYDA9rVv9PPKYvJhatuaVpnbwkfTSmRXBVhmTwIc99QsRKjw9LkSsj5mEnx4O6dUyAJilQ3H/5xWb+o1MTkUpI74lIfYZx/QQLF5E0vHOrIdPkaEHH4zxTUk9XKkyZNFULbqHKAKN6wl8W4HmGlhamJF5ra4xx6whu4HeIipY418ok9yY8/mTjF2jUct6frellgxNZX+j4/gWrLhIqHCL6aW2isbr0a0tKaYX2ezK8rtWf6MtbpdyOPr+8YGrgkh48brvaD6uVob9doOHrA0jb9dTn1GL/T2JUNfJa1PBRCEJqGOihac4cv8zfMLufuDubmqgDOaN6HC4xrhhwWT7cAM7yAzoV42or5ELTWCb94Lm+wrWAPMCn9sG7qr8pHdAMlnElnhSERJ/Uk1BNdIoSuxJwPFKdrSSZzeSYG0LzEfAYDtDXbHmoix968LhfBhfw3h0zIscMNK43DPDWnF8N8d0In/lyu+OZIhy13bqNdeoJmQJLDDEmQ8aEBxCN2W4fZ9CKEF0QIUEIno6QK5goX/Kt4kt6ZEqq1NBQpQT3LFZ+N1tQpfe9GNC3uh6LHGoPOYtAM9p0C+QhzNlM6uIB1QXp5j7D0WO8AGBf9o1ULn4GYbP10ksHGRllse3g==~-1~-1~-1; _dpm_id.16f4=b80869a3-625c-4846-a155-16a5fdfbfa10.1739405531.74.1745535574.1745448831.df71dedc-a81c-4818-b416-e196c2b36ba6; _tgpc=b4ba6823-4aa4-5ebb-b46d-9556fa0fabc0; _tglksd=eyJzIjoiMzFjM2JkMjUtMDQ3YS01ZjMyLWExZmUtNzYyNDNmOWYxZTgwIiwic3QiOjE3NDE3NDczOTc1NzksInNvZCI6IihkaXJlY3QpIiwic29kdCI6MTc0MDYwNjYwODcyMCwic29kcyI6Im8iLCJzb2RzdCI6MTc0MDYwNjYwODcyMH0=; _sp_srt_id.16f4=da0e1cd6-bc30-4c7a-8061-3ddf5c612d4e.1739405532.72.1745535567.1745438357.251ee7ff-77a8-44ad-9ade-9d648887e9b8.3a2b707a-a9e1-4ef0-a81e-6b874eecab67...0; _gcl_au=1.1.21040710.1739405532; _ga_QG8WHJSQMJ=GS1.1.1745535567.83.1.1745535909.60.0.0; _ga=GA1.2.295993567.1739405532; PRV=3P=0&V=1858809550&E=1740631139; ss-pid=1uGacOcdj7tnhbNzdPca; ab.storage.sessionId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%224b5db11f-ba67-6c5b-dc3d-2f6bf2afa20c%22%2C%22e%22%3A1745537373551%2C%22c%22%3A1745535568555%2C%22l%22%3A1745535573551%7D; _scid=f9fmQ3aISR4DACGy5G6BsoFsosxKelLYr1aeHw; _svsid=9d0929120b67695ad6ee074ccfd583b7; _ga_M8T3LWXCC5=GS1.2.1745535568.69.1.1745535573.55.0.0; _sctr=1%7C1745380800000; _hjSessionUser_2150570=eyJpZCI6Ijg2ZmNmOThiLTg5Y2YtNWRiMi04N2JlLTMxNmE2MmM4NGQxMCIsImNyZWF0ZWQiOjE3Mzk0OTM5MTM3MzUsImV4aXN0aW5nIjp0cnVlfQ==; _csrf=ba945d1a-57c4-4b50-a4b2-1edea5014b72; ss-id=CuYK3sXZ78urWSsJTkvv; _csrf=d90ba50a-ac17-4e0e-a925-72a7f838403b; ak_bmsc=5714B583A447855656455CB056E4F9F8~000000000000000000000000000000~YAAQ7xw/F3r6jkqWAQAARwAHahvbfGzZpQnvl8qteTtt5GSodXiTLXudzQi7mvlSrXlX9k1fZIcqtYsdii3zlC40k+1dLuVmjgFrSRLvSWLQxQ6pg6pYER6tdKTbJKKjlH2uLAltlY4a1221scCNB129MIZOoydP+IdTDE/Y05Flnq9uANLTm87yGjTsN0GRBVLLrCEWO3W6oiTcDxQX85RweKq2Z0P05vwtanxzXPfJVUr+r0+G2MSUEnXPfIrjSjYa+0HI7KrGJl95fcXVodIYH5EF0gRbvwsOzaQJGgVU8aoHGidla8YEiH0u14Trwbo+JyJDLjXR1dly9hLuZYW45iGuGT9RTbgxa/ygYGtdPvdosa+YHMCggQR93hrg13QwkUqjX+cm/cUl0eYrVOsbZ5x5iFIBiTRfdDZvxAUx1xM3ynk=; bm_sz=A19864A49966B76F816AC20969700833~YAAQVznJFy9x4CSWAQAAhj8MahvFcxqyIW+ZErw3/CF43OxrSaEfx+oG6S+sIGx/osyD9LrMfVQ4oH0OiggZtwuD1cgXTSZTWaQHXHjHQFjw1cTVFhLgxd5cv0gnJ6D0/ptisilXSrcpgfFcqXlcKM0LnB3b5hj4omZM5WeevKBjOx9dGkBFrkxlfRUxw7bGbLs+2vvdViuBPcZw7zF1G0jHpQtQWWds2koIQLm79UWQfNo8z74qspltqYpU5O9CeS05aQVoJdpGfE92ndw4dIvKYx4Iqa/+yJVwrXsggOZvMaqsMb8T2pD1B4CtwkQMjjD9j6J4t9pTvXZbYkohomqIlC3YnypMOcQhXkgCE35J0secGnQ488gvgsTfvIfcoHbClahJo+rlG10cCR7XZmnlDeP97UqsuUrW0lzjpUEps65b5gnCcow/evBUXmOFwlA=~4276805~3158593; bm_sv=4DBE463AC8179A113D657BFC74BD596B~YAAQVznJFy5x4CSWAQAAhj8Mahvus7yIyQokfBOkxAjT3TG89Kk+fQNMwf+KoOCl2GT4abs0X9WNscoThNYFcFwOEjBWJpQgTfxcTI/kKFa6JRbEizw/gb7tObvDk/zl1f3UXLTQi5ervMJ1G3SgaepauZDB5Zwc4bQ8pitafUaFWbXvp1ByGb94QPJjiudg1o6qzE4mleMQNcHipBp7qhVrO+apIUdLS9B/HrW+svIamosYkDnN2dPw6MEV9T0JNyxUhw==~1; _dpm_ses.16f4=*; _uetsid=c5d71500215f11f0ae48ad5a85f12547; _uetvid=d50156603a0211efbb275bc348d5d48b; _sp_srt_ses.16f4=*; _gid=GA1.2.525091085.1745535569; _scid_r=cNfmQ3aISR4DACGy5G6BsoFsosxKelLYr1aeaw; _hjSession_2150570=eyJpZCI6ImJjYWZlNjE1LWY0YzEtNDVlNC1hNTExLTgwMDVmYjEwOTIxZiIsImMiOjE3NDU1MzU1NzA0NzUsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _rdt_uuid=1739493910839.b8d9d6b9-37a2-49b2-9486-b9060fddaa81'"""

	lines = nested_dict()
	if keep:
		with open("static/nba/draftkings.json") as fh:
			lines = json.load(fh)

	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
				
			time.sleep(0.3)
			url = f"https://sportsbook-nash.draftkings.com/api/sportscontent/dkusmi/v1/leagues/42648/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			#print(url)
			outfile = "outnbaDK"
			#print(url)
			os.system(f"curl -s {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Referer: https://sportsbook.draftkings.com/' -H 'Origin: https://sportsbook.draftkings.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-site' -H 'Priority: u=0' -H 'TE: trailers' {cookie} -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			if debug:
				with open("out", "w") as fh:
					json.dump(data, fh, indent=4)

			prop = propIds.get(subCat, "")
			print(prop)

			events = {}
			if "events" not in data:
				print("events not found")
				continue

			started_events = {}
			for event in data["events"]:
				start = f"{event['startEventDate'].split('T')[0]}T{':'.join(event['startEventDate'].split('T')[1].split(':')[:2])}Z"
				startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=4)
				if startDt.day != int(date[-2:]):
					started_events[event["id"]] = game
					continue
					pass
				game = event["name"].lower()
				games = []
				for team in game.split(" @ "):
					t = convertNBATeam(team)
					games.append(t)
				game = " @ ".join(games)
				if event.get("status", "") == "STARTED":
					started_events[event["id"]] = game
					continue

				events[event["id"]] = game

			markets = {}
			for row in data["markets"]:
				markets[row["id"]] = row

			selections = {}
			for row in data["selections"]:
				selections.setdefault(row["marketId"], [])
				selections[row["marketId"]].append(row)

			for marketId, selections in selections.items():
				market = markets[marketId]
				if started_events.get(market["eventId"]):
					continue
				game = events[market["eventId"]]
				away,home = map(str, game.split(" @ "))
				catId = market["subcategoryId"]
				prop = propIds.get(catId, "")

				alt = False
				skip = 2
				fullProp = prop
				prefix = ""
				if prop:
					if "-alt" in prop:
						skip = 1
						prop = prop.replace("-alt", "")
				else:
					prop = market["name"].lower().split(" [")[0]
					fullProp = prop
					
					if "1st half" in prop:
						prefix = "1h_"
					elif "2nd half" in prop:
						prefix = "2h_"
					elif "1st quarter" in prop:
						prefix = "1q_"
					elif "2nd quarter" in prop:
						prefix = "2q_"
					elif "3rd quarter" in prop:
						prefix = "3q_"
					elif "4th quarter" in prop:
						prefix = "4q_"

					if "moneyline" in prop:
						prop = "ml"
					elif "spread" in prop:
						prop = "spread"
					elif "team total points" in prop or (prop.endswith("alternate total points") and mainCat == "team") or (prop.startswith("alternate") and "total points" in prop and mainCat == "halves"):
						team = prop.replace("alternate " , "").split(":")[0]
						t = team.split(" ")[0]
						if game.startswith(t):
							prop = "away_total"
						else:
							prop = "home_total"
					elif "total" in prop:
						prop = "total"

					prop = f"{prefix}{prop}"
				if not prop:
					continue


				for idx in range(0, len(selections), skip):
					selection = selections[idx]

					over = selection["displayOdds"]["american"].replace("\u2212", "-")
					ou = over
					if skip != 1:
						under = selections[idx+1]["displayOdds"]["american"].replace("\u2212", "-")

						isOver = selection["outcomeType"] in ["Over", "Away"]
						if not isOver:
							over,under = under,over
							pass
						ou = f"{over}/{under}"

					line = selection.get("points", "")
					if skip == 1 and "+" in selection["label"]:
						line = str(float(selection["label"].split("+")[0]) - 0.5)
					participants = [x for x in selection.get("participants", []) if x["type"] == "Player"]

					#print("==>",game, prop, ou, line, participants)
					if not line and not participants:
						lines[game][prop] = ou
					elif not line and participants:
						player = parsePlayer(participants[0]["name"])
						lines[game][prop][player] = ou
					else:
						line = str(float(line))

						if participants:
							player = parsePlayer(participants[0]["name"])
							if skip == 1 and line in lines[game][prop][player]:
								over = lines[game][prop][player][line].split("/")[0]
								rest = lines[game][prop][player][line].replace(over, "")
								if int(ou) > int(over):
									over = ou
								ou = f"{over}{rest}"

							lines[game][prop][player][line] = ou
						else:
							lines[game][prop][line] = ou

			"""
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
							away,home = map(str, game.split(" @ "))

							#if game != "texas a&m @ miami fl":
							#	continue

							if "label" not in row:
								continue

							prefix = fullProp = ""
							alt = True
							if subCat in propIds:
								prop = propIds[subCat]

								if prop.endswith("-ou"):
									alt = False
									prop = prop.replace("-ou", "")
							else:
								alt = False
								prop = row["label"].lower().split(" [")[0]
								fullProp = prop
								
								if "1st half" in prop:
									prefix = "1h_"
								elif "2nd half" in prop:
									prefix = "2h_"
								elif "1st quarter" in prop:
									prefix = "1q_"
								elif "2nd quarter" in prop:
									prefix = "2q_"
								elif "3rd quarter" in prop:
									prefix = "3q_"
								elif "4th quarter" in prop:
									prefix = "4q_"

								if "moneyline" in prop:
									prop = "ml"
								elif "spread" in prop:
									prop = "spread"
								elif "team total points" in prop or (prop.endswith("alternate total points") and mainCat == "team") or (prop.startswith("alternate") and "total points" in prop and mainCat == "halves"):
									team = prop.replace("alternate " , "").split(":")[0]
									t = team.split(" ")[0]
									if game.startswith(t):
										prop = "away_total"
									else:
										prop = "home_total"
								elif "total" in prop:
									prop = "total"
								else:
									continue


							prop = prop.replace(" alternate", "")
							prop = f"{prefix}{prop}"

							if prop == "halftime/fulltime":
								continue

							outcomes = row["outcomes"]
							skip = 1
							if not alt:
								skip = 2

							for i in range(0, len(outcomes), skip):
								outcome = outcomes[i]
								if "spread" in prop or "total" in prop:
									player = convertNBATeam(outcome["participant"])
								else:
									player = parsePlayer(outcome["participant"].split(" (")[0].strip())

								ou = outcome["oddsAmerican"]

								if "ml" in prop:
									lines[game][prop] = ou+"/"+outcomes[i+1]["oddsAmerican"]
								elif prop == "win":
									if i+1 >= len(outcomes):
										continue
									lines[game][prop][player] = ou+"/"+outcomes[i+1]["oddsAmerican"]
								elif alt:
									line = outcome.get("label", "")
									if "spread" in prop or "total" in prop:
										line = str(outcome["line"])
									if line:
										line = str(float(line.replace("+", "")) - 0.5)
										if line in lines[game][prop][player]:
											u = ""
											o = lines[game][prop][player][line].split("/")[0]
											if "/" in lines[game][prop][player][line]:
												o,u = map(str, lines[game][prop][player][line].split("/"))
											if int(ou) > int(o):
												o = ou
											lines[game][prop][player][line] = o
											if u:
												lines[game][prop][player][line] += "/"+u
										else:
											lines[game][prop][player][line] = ou
									else:
										lines[game][prop][player] = ou
								elif "spread" in prop or "total" in prop:
									line = str(float(outcome["line"]))
									lines[game][prop][line] = ou + "/" + outcomes[i+1]["oddsAmerican"]
								else: #o/u
									line = outcome.get("line", "")

									if i+1 >= len(outcomes):
										continue

									if not line or prop in ["single", "double", "triple"]:
										lines[game][prop][player] = ou+"/"+outcomes[i+1]["oddsAmerican"]
									else:
										line = str(float(line))
										lines[game][prop][player] [line] = ou+"/"+outcomes[i+1]["oddsAmerican"]
			"""
	with open("static/nba/draftkings.json", "w") as fh:
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

def convertTeamRankingsTeam(team):
	if team == "new orleans":
		return "no"
	elif team == "washington":
		return "wsh"
	elif team == "okla city":
		return "okc"
	elif team == "phoenix":
		return "phx"
	elif team == "san antonio":
		return "sa"
	elif team == "utah":
		return "utah"
	elif team == "brooklyn":
		return "bkn"
	elif team == "new york":
		return "ny"
	elif team == "golden state":
		return "gs"
	return team.replace(" ", "")[:3]

def writeRankings():
	baseUrl = "https://www.teamrankings.com/nba/stat/"
	pages = ["three-pointers-made-per-game", "opponent-three-pointers-made-per-game"]
	ids = ["3ptm", "opp_3ptm"]

	rankings = {}
	for idx, page in enumerate(pages):
		url = baseUrl+page
		outfile = "outnba3"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")
		ranking = ids[idx]

		for row in soup.find("table").find_all("tr")[1:]:
			tds = row.find_all("td")
			team = convertTeamRankingsTeam(row.find_all("a")[0].text.lower())

			if team not in rankings:
				rankings[team] = {
					"3ptm": 0,
					"opp_3ptm": 0
				}

			rankings[team][ranking] = float(tds[2].text)

	with open(f"{prefix}static/nba/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)

def writeSGP():
	outfile = "outnbaSGP"
	url = "https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/42648?format=json"
	os.system(f"curl {url} -o {outfile}")
	date = str(datetime.now())[:10]

	with open(outfile) as fh:
		lines = json.load(fh)

	with open("static/nba/sgp.json") as fh:
		res = json.load(fh)

	res = {}
	for row in lines["eventGroup"]["events"]:
		game = "-".join(row["name"].lower().split(" ")) + "/" + row["eventId"]
		if "eventStatus" in row and "state" in row["eventStatus"] and row["eventStatus"]["state"] == "STARTED":
			continue

		start = f"{row['startDate'].split('T')[0]}T{':'.join(row['startDate'].split('T')[1].split(':')[:2])}Z"
		startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=4)
		if startDt.day != int(date[-2:]):
			continue
			pass

		awayFull, homeFull = map(str, game.split("/")[0].replace("-", " ").split(" @ "))
		away, home = convertNBATeam(awayFull), convertNBATeam(homeFull)
		url = f"https://sportsbook.draftkings.com/event/{game}?sgpmode=true"
		os.system(f"curl {url} -o {outfile}")

		soup = BS(open(outfile, 'rb').read(), "lxml")

		data = "{}"
		for script in soup.find_all("script"):
			if not script.string:
				continue
			if "__INITIAL_STATE" in script.string:
				m = re.search(r"__INITIAL_STATE__ = {(.*?)};", script.string)
				if m:
					data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
					data = f"{{{data}}}"
					break

		data = eval(data)

		game = away+" @ "+home
		res[game] = {}

		for gameId in data["offers"]:
			for eventId in data["offers"][gameId]:
				offerRow = data["offers"][gameId][eventId]
				if type(offerRow) is list:
					offerRow = offerRow[0]

				prop = offerRow["label"].lower()
				player = ""
				alt = False
				if "alternate total points" in prop:
					if prop.startswith(awayFull):
						prop = "away_total"
					elif prop.startswith(homeFull):
						prop = "home_total"
					else:
						continue
				elif prop == "spread alternate":
					prop = "spread"
				elif prop == "total alternate":
					prop = "total"
				elif "playerNameIdentifier" in offerRow:
					if " - " in prop:
						continue
					participant = offerRow["outcomes"][0]["participant"].lower().strip()
					player = parsePlayer(participant)
					if " alt " in prop:
						alt = True
						prop = prop.replace("alt ", "")
					prop = prop.replace(participant+" ", "").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("turnovers", "to").replace("steals", "stl").replace("blocks", "blk").replace("three pointers made", "3ptm").replace(" o/u", "")
					prop = prop.replace(" ", "").replace("pts+ast+reb", "pts+reb+ast")
				else:
					continue

				if prop not in res[game]:
					res[game][prop] = {}
				if player and player not in res[game][prop]:
					res[game][prop][player] = {}

				for outcome in offerRow["outcomes"]:
					line = outcome.get("line", "")
					odds = outcome["oddsAmerican"].replace("\u2212", "-")

					if prop in ["away_total", "home_total", "total", "spread"]:
						over = outcome["label"].lower() == "over"
						if line in res[game][prop]:
							if over:
								res[game][prop][line] = f"{odds}/{res[game][prop][line]}"
							else:
								res[game][prop][line] += "/"+odds
						else:
							res[game][prop][line] = odds
					elif alt and not line:
						line = str(int(outcome["label"].replace("+", "")) - 0.5)
						if line not in res[game][prop][player]:
							res[game][prop][player][line] = odds
					elif player:
						line = str(line)
						over = outcome["label"].lower() == "over"
						if not line:
							res[game][prop][player] = odds
						elif line in res[game][prop][player]:
							if over:
								res[game][prop][player][line] = f"{odds}/{res[game][prop][player][line]}"
							else:
								res[game][prop][player][line] += "/"+odds
						else:
							res[game][prop][player][line] = odds

	with open("static/nba/sgp.json", "w") as fh:
		json.dump(res, fh, indent=4)

	#readSGP()

def readSGP(insurance=False):

	#game = "phx @ cle"

	with open("static/nba/sgp.json") as fh:
		res = json.load(fh)

	with open(f"static/basketballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	with open(f"static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"static/basketballreference/trades.json") as fh:
		trades = json.load(fh)

	with open(f"static/basketballreference/splits.json") as fh:
		splits = json.load(fh)

	with open(f"static/nba/minutes.json") as fh:
		minutes = json.load(fh)

	with open(f"{prefix}static/basketballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"{prefix}static/nba/matchups.json") as fh:
		matchups = json.load(fh)

	out = ""
	for game in res:
		output = []
		away, home = map(str, game.split(" @ "))
		for prop in res[game]:
			keys = res[game][prop].keys()
			for key in keys:
				lines = []
				# player has multiple lines
				if type(res[game][prop][key]) is dict:
					lines = res[game][prop][key].keys()
				else:
					lines = [key]
				for line in lines:
					#print(prop, key, line)
					player = ""
					if type(res[game][prop][key]) is dict:
						player = key
						oddsStr = res[game][prop][key][line].split("/")
					else:
						oddsStr = res[game][prop][line].split("/")
					for ouIdx, odds in enumerate(oddsStr):
						isOver = ouIdx == 0
						if insurance:
							if int(odds) < -300 or int(odds) >= -185:
								continue
						else:
							if int(odds) <= -360 or int(odds) >= -185:
								continue

						over = overL15 = overPerMin = 0
						lastArr = []
						if player:
							team = away
							opp = home
							if home in playerIds and player in playerIds[home]:
								opp = away
								team = home

							playerSplits = {}
							if player in trades:
								for hdr in splits[trades[player]][player]:
									playerSplits[hdr] = splits[trades[player]][player][hdr]
								for hdr in splits[team][player]:
									playerSplits[hdr] += ","+splits[team][player][hdr]
							else:
								playerSplits = splits[team][player]

							if prop not in playerSplits:
								continue

							minArr = playerSplits["min"].split(",")
							avgMin = minutes[team][player]

							arr = playerSplits[prop].split(",")
							lastArr = arr[-20:]
							overArr = [x for x in arr if int(x) > float(line)]
							overArrL15 = [x for x in arr[-15:] if int(x) > float(line)]
							overArrPerMin = [x for i, x in enumerate(arr) if int(x) * avgMin / int(minArr[i]) > float(line)]

							over = int(len(overArr) * 100 / len(arr))
							overL15 = int(len(overArrL15) * 100 / len(arr[-15:]))
							overPerMin = int(len(overArrPerMin) * 100 / len(arr))

							pos = ""
							if player in roster[team]:
								pos = roster[team][player].lower()
							if pos == "g":
								pos = "sg"
							elif pos == "f":
								pos = "sf"

							rank = posRank = ""
							try:
								rank = matchups[opp]["szn"]["all"][prop+"Rank"]
								posRank = matchups[opp]["szn"][pos][prop+"Rank"]
							except:
								pass

							txt = f"\n{player} o{line} {prop} ({avgMin}m) {odds}\n"
							txt += f"{over}%, {overL15}% L15, {overPerMin}% per min\n"
							txt += f"{','.join(lastArr)}\n"
							txt += f"Rank: {rank}, {pos.upper()} Pos Rank: {posRank}\n"

							output.append([overL15, txt])

		if game not in pnLines:
			continue
		out += f"\ngame: {game}\n"
		line = list(pnLines[game]['spread'].keys())[0]
		out += f"{line} {pnLines[game]['spread'][line]}\n"
		for L15, txt in sorted(output, reverse=True):
			out += txt

	with open("sgp.txt", "w") as fh:
		fh.write(out)


def writeThreesday():
	
	with open(f"{prefix}static/nba/rankings.json") as fh:
		rankings = json.load(fh)

	with open(f"{prefix}static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	output = "Game|away 3ptm|away opp 3ptm|home 3ptm|home opp 3ptm|avg\n"
	output += ":--|:--|:--|:--|:--|:--\n"
	data = []
	for game in pnLines:
		away, home = map(str, game.split(" @ "))
		avg = (rankings[away]["3ptm"] + rankings[away]["opp_3ptm"] + rankings[home]["3ptm"] + rankings[home]["opp_3ptm"]) / 4

		data.append({
			"game": game,
			"away_3ptm": rankings[away]["3ptm"],
			"away_opp_3ptm": rankings[away]["opp_3ptm"],
			"home_3ptm": rankings[home]["3ptm"],
			"home_opp_3ptm": rankings[home]["opp_3ptm"],
			"avg": round(avg, 3)
		})

	for row in sorted(data, key=lambda k: k["avg"], reverse=True):
		output += f"{row['game'].upper()}|{row['away_3ptm']}|{row['away_opp_3ptm']}|{row['home_3ptm']}|{row['home_opp_3ptm']}|{row['avg']}  \n"

	print(output)

def writeInjuries():
	with open(f"{prefix}static/nba/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/basketballreference/totals.json") as fh:
		totals = json.load(fh)

	output = "Injury Watch -- (3ptm-3pta)\n\n"
	for game in pnLines:
		output += f"{game.upper()}  \n"
		for status in ["out", "50/50", "likely", "unlikely"]:
			for team in game.split(" @ "):
				for player in lineups[team][status]:
					if player not in totals[team]:
						continue
					if not totals[team][player]["gamesPlayed"]:
						continue
					ptm = round(totals[team][player].get("3ptm", 0) / totals[team][player]["gamesPlayed"], 1)
					pta = round(totals[team][player].get("3pta", 0) / totals[team][player]["gamesPlayed"], 1)
					output += f"{status.upper()}: {player.title()} ({ptm}-{pta})  \n"
		output += "\n\n---\n\n"

	with open("static/nba/injuries.txt", "w") as fh:
		fh.write(output)

def writeLeaders():
	with open(f"{prefix}static/nba/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/nba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/basketballreference/totals.json") as fh:
		totals = json.load(fh)

	output = ""
	for game in dkLines:
		output += f"{game.upper()}  \n"
		for status in ["starters"]:
			for team in game.split(" @ "):
				for player in lineups[team][status]:
					if player not in totals[team]:
						continue
					odds = ""
					try:
						odds = dkLines[game]["first_3ptm"][player]
					except:
						pass
					ptm = round(totals[team][player].get("3ptm", 0) / totals[team][player]["gamesPlayed"], 1)
					pta = round(totals[team][player].get("3pta", 0) / totals[team][player]["gamesPlayed"], 1)
					output += f"{player.title()} ({ptm}-{pta}) {odds} \n"
		output += "\n\n---\n\n"

	print(output)


def bvParlay():
	with open(f"{prefix}static/nba/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/nba/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nba/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/nba/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/nba/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/nba/caesars.json") as fh:
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
			ev.append((evData[desc]["ev"], desc, fairValue, tdParlay['odds'], legs))

	for row in sorted(ev):
		print(f"{row[0]}, {row[1]}, fairval={row[2]}, bvOdds={row[3]} {row[4]}")
		pass

	output = "\t".join(["EV", "Parlay", "BV Odds", "Fair Value"])+"\n"
	for row in sorted(ev, reverse=True):
		arr = [row[0], row[1], row[3], row[2]]
		arr.extend(row[-1])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nba/bvParlays.csv", "w") as fh:
		fh.write(output)

def parseESPN(espnLines, noespn=None):
	with open("static/basketballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"static/nba/espn.json") as fh:
		espn = json.load(fh)

	players = {}
	for team in roster:
		players[team] = {}
		for player in roster[team]:
			first = player.split(" ")[0][0]
			last = player.split(" ")[-1]
			if team == "hou" and player == "jeff green":
				continue
			players[team][f"{first} {last}"] = player

	if not noespn:
		for game in espn:
			espnLines[game] = {}
			for prop in espn[game]:
				if prop == "ml":
					espnLines[game][prop] = espn[game][prop]
				elif prop in ["total", "spread"]:
					espnLines[game][prop] = espn[game][prop].copy()
				else:
					espnLines[game][prop] = {}
					away, home = map(str, game.split(" @ "))
					for p in espn[game][prop]:
						if len(p.split(" ")[0]) > 1:
							continue
						if p == "j jadeney":
							player = "jaden ivey"
						else:
							if p not in players[away] and p not in players[home]:
								continue
							if p in players[away]:
								player = players[away][p]
							else:
								player = players[home][p]
						
						if type(espn[game][prop][p]) is str:
							espnLines[game][prop][player] = espn[game][prop][p]
						else:
							espnLines[game][prop][player] = espn[game][prop][p].copy()

def writePlayer(player, propArg):
	with open(f"{prefix}static/nba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/nba/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nba/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/nba/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/nba/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nba/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/nba/caesars.json") as fh:
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

	for book in lines:
		for game in lines[book]:
			for prop in lines[book][game]:
				if propArg and propArg != prop:
					continue

				for p in lines[book][game][prop]:
					if player not in p:
						continue

					print(book, lines[book][game][prop][p])

def writeCirca(date, debug):

	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)
	teamGame = {}
	for game in schedule[date]:
		a,h = map(str, game.split(" @ "))
		teamGame[a] = teamGame[h] = game

	today = datetime.strptime(date, "%Y-%m-%d")
	dt = today.strftime("%Y-%-m-%-d")
	data = nested_dict()

	file = f"/mnt/c/Users/zhech/Downloads/NBA - {dt}.pdf"
	pages = convert_from_path(file)

	pages[1].save("outnbaprops.png", "PNG")
	img = Image.open("outnbaprops.png")
	left,top,right,bottom = 108,445,460,2185

	boxH, boxW = 93, 350

	props = [
		("pts", 12, top, left, 2185),
		("3ptm", 8, top, 866, 1190),
		("reb", 3, 1309, 866, 1690),
		("ast", 3, 1693, left, 1975)
	]
	for prop, rows, top, left, bottom in props:
		l = left
		for colIdx in range(2):
			t = top
			for rowIdx in range(rows):
				box_img = img.crop((l,t,l+boxW,t+boxH))
				box_text = pytesseract.image_to_string(box_img).split("\n")
				player = parsePlayer(box_text[0].split(" (")[0])
				team = convertNBATeam(box_text[0].split("(")[-1].replace(")", ""))

				line_img = img.crop((left+220,t+35,left+270,t+boxH))
				line_text = pytesseract.image_to_string(line_img).split("\n")
				line = line_text[0]
				if line == "%":
					line = "9.5"
				else:
					line = line.replace("%", ".5").replace("h", ".5")
				if "." not in line and line.endswith("4"):
					line = line[:-1]+".5"

				ou_img = img.crop((left+270,t+35,left+boxW,t+boxH))
				ou_text = pytesseract.image_to_string(ou_img).split("\n")
				ou = ou_text[0]+"/"+ou_text[1]
				ou = ou.replace("EVEN", "+100").replace("\u201c", "-")

				#print(team, player, line_text, line, ou)

				if "+" not in ou and ou.startswith("4"):
					ou = "+"+ou[1:]
				if "-" not in ou and ou.startswith("7"):
					ou = "-"+ou[1:]

				if "+" not in ou and "/4" in ou:
					ou = ou.replace("/4", "/+")
				if "-" not in ou and "/7" in ou:
					ou = ou.replace("/7", "/-")

				if not player or not team:
					continue
				data[teamGame.get(team, "")][prop][player][line] = ou

				#if debug and rowIdx == 0:
				if "harden" in player:
					box_img.save("out-box.png", "PNG")
					line_img.save("out.png", "PNG")
				t += boxH+3

			l += boxW

	with open("static/nba/circa.json", "w") as fh:
		json.dump(data, fh, indent=4)


def writeLineups(tmrw=None):
	url = "https://www.rotowire.com/basketball/nba-lineups.php"
	if tmrw:
		url += "?date=tomorrow"
	outfile = "outnba2"
	os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.rotowire.com/basketball/nba-lineups.php' -H 'Connection: keep-alive' -H 'Cookie: PHPSESSID=fa8217e19e4a32a38d5bd2e3e46e4487; g_uuid=8ccd1e2c-792c-4822-a45e-9b68d791c622; cohort_id=3; usprivacy=1NNN; g_sid=1729631249817.jm63rbi; g_device=macos%7Cdesktop; ktag_version=20241128; cookieyes-consent=consentid:dHRLVWZXcDZsYkVZazdGUFZwa2E4YU5acFNQQk5WMFI,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes' -H 'Upgrade-Insecure-Requests: 1' -H 'Sec-Fetch-Dest: document' -H 'Sec-Fetch-Mode: navigate' -H 'Sec-Fetch-Site: same-origin' -H 'Priority: u=0, i' -o {outfile}")
	soup = BS(open(outfile, 'rb').read(), "lxml")

	lineups = {}
	rotoTeams = []
	for game in soup.find_all("div", class_="lineup"):
		if "is-tools" in game.get("class"):
			continue
		teams = game.find_all("a", class_="lineup__team")
		lineupList = game.find_all("ul", class_="lineup__list")
		statusList = game.find_all("li", class_="lineup__status")
		for idx, teamLink in enumerate(teams):
			team = teamLink.get("href").split("-")[-1]
			rotoTeams.append(team)
			team = convertNBATeam(team)
			try:
				lineups[team] = {
					"confirmed": False if "is-expected" in statusList[idx].get("class") else True,
					"starters": [],
					"50/50": [],
					"likely": [],
					"unlikely": [],
					"out": []
				}
			except:
				continue
			for playerIdx, li in enumerate(lineupList[idx].find_all("li", class_="lineup__player")):
				player = " ".join(li.find("a").get("href").split("/")[-1].split("-")[:-1])
				player = parsePlayer(player)
				pos = li.find("div").text

				if playerIdx < 5:
					lineups[team]["starters"].append(player)
				elif "hide" in li.get("class"):
					continue
				elif "is-pct-play-0" in li.get("class"):
					lineups[team]["out"].append(player)
				elif "is-pct-play-25" in li.get("class"):
					lineups[team]["unlikely"].append(player)
				elif "is-pct-play-50" in li.get("class"):
					lineups[team]["50/50"].append(player)
				elif "is-pct-play-75" in li.get("class"):
					lineups[team]["likely"].append(player)

	with open(f"{prefix}static/nba/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)

	with open(f"{prefix}static/nba/rotoTeams.json", "w") as fh:
		json.dump(rotoTeams, fh, indent=4)

def writeMinutes():
	with open(f"{prefix}static/nba/rotoTeams.json") as fh:
		rotoTeams = json.load(fh)

	outfile = "outnbaMinutes"
	minutes = {}
	for team in rotoTeams:
		url = f"https://www.rotowire.com/basketball/ajax/get-projected-minutes.php?team={team.upper()}"
		time.sleep(0.3)
		os.system(f"curl {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' -H 'Referer: https://www.rotowire.com/basketball/nba-lineups.php' -H 'Cookie: PHPSESSID=fa8217e19e4a32a38d5bd2e3e46e4487; g_uuid=8ccd1e2c-792c-4822-a45e-9b68d791c622; cohort_id=3; usprivacy=1NNN; g_sid=1729631249817.jm63rbi; g_device=macos%7Cdesktop; ktag_version=20241128; cookieyes-consent=consentid:dHRLVWZXcDZsYkVZazdGUFZwa2E4YU5acFNQQk5WMFI,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'Priority: u=0' -H 'TE: trailers' -o {outfile}")
		team = convertNBATeam(team)
		minutes[team] = {}

		with open(outfile) as fh:
			data = json.load(fh)

		for row in data:
			player = parsePlayer(row["name"])
			minutes[team][player] = row["proj"]

	with open("static/nba/minutes.json", "w") as fh:
		json.dump(minutes, fh, indent=4)

def calcPoints(prop, val):
	pts = 0
	if prop == "pts":
		pts += val * 1
	elif prop in ["reb", "ast"]:
		pts += val * 1.5
	#elif prop == "reb":
	#	pts += val * 1.2
	elif prop == "ast":
		pts += val * 1.5
	elif prop in ["stl", "blk"]:
		pts += val * 3
	elif prop == "to":
		pts += val * -1
	return pts


#https://www.fantasypros.com/nba/projections/daily-overall.php

def writeRanks(teamArg=None):
	with open(f"{prefix}static/nba/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nba/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/nba/bet365.json") as fh:
		bet365 = json.load(fh)

	with open(f"{prefix}static/nba/espn.json") as fh:
		espn = json.load(fh)

	with open(f"{prefix}static/nba/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/nba/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/basketballreference/roster.json") as fh:
		roster = json.load(fh)

	espnLines = {}
	parseESPN(espnLines)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"espn": espnLines,
		"365": bet365,
		"dk": dkLines,
		"cz": czLines
	}

	#with open("static/nba/ranksData.json") as fh:
	#	data = json.load(fh)
	data = {}

	for book in lines:
		for game in lines[book]:
			if teamArg and teamArg not in game.split(" @ "):
				continue

			for prop in lines[book][game]:
				if prop not in ["pts", "reb", "ast", "stl", "blk", "to"]:
					continue

				for player in lines[book][game][prop]:
					away, home = map(str, game.split(" @ "))
					if player in roster[away]:
						t = away
					elif player in roster[home]:
						t = home
					else:
						continue
					pos = roster[t][player]
					if "G" in pos:
						pos = "G"
					elif "F" in pos:
						pos = "F"

					if t not in data:
						data[t] = {}
					if player not in data[t]:
						data[t][player] = {}
					if prop not in data[t][player]:
						data[t][player][prop] = {}

					for line in lines[book][game][prop][player]:
						odds = lines[book][game][prop][player][line]
						if not odds:
							continue
						implied = getFairValue(odds)
						if not implied:
							continue
						#ous.append((abs(.5-implied), odds, line, math.ceil(float(line)) * implied))
						if line not in data[t][player][prop]:
							data[t][player][prop][line] = []
						if player == "lebron james" and prop == "stl":
							print(book, line, odds)
						data[t][player][prop][line].append(odds)

	with open("static/nba/ranksData.json", "w") as fh:
		json.dump(data, fh, indent=4)

	sortedOutputs = {"ALL": []}
	for team in data:
		for player in data[team]:
			pos = roster[team][player]
			if "G" in pos:
				pos = "G"
			elif "F" in pos:
				pos = "F"
			if pos not in sortedOutputs:
				sortedOutputs[pos] = []
			j = {}
			inc = {}
			for prop in data[team][player]:
				arr = []
				for line in data[team][player][prop]:
					odds = data[team][player][prop][line]
					l = []
					for o in odds:
						implied = getFairValue(o)
						l.append(implied)
					l = sorted(l)
					avgOdds = averageOdds(odds)
					arr.append((math.ceil(float(line)), getFairValue(avgOdds, method="power"), avgOdds))

				if not arr:
					continue

				arr = sorted(arr, reverse=True)

				j[prop] = {}
				tot = last = 0
				for line, implied, avg in arr:
					if not implied:
						implied = .002
					tot += (implied - last)
					j[prop][line] = implied - last
					if player == "lebron james" and prop == "stl":
						print(line, implied, implied-last, avg)
					last = implied

				j[prop][0] = 1 - tot

			pts = 0
			propPts = {}
			for prop in j:
				propPts[prop] = 0
				for line in j[prop]:
					#p = calcPoints(prop, line * j[prop][line])
					p = line * j[prop][line]
					propPts[prop] += p
				pts += calcPoints(prop, propPts[prop])

			sortedOutputs[pos].append((pts, player, pos, team, propPts, inc, j))
			sortedOutputs["ALL"].append((pts, player, pos, team, propPts, inc, j))

	reddit = ""
	table = []
	for pos in ["ALL", "G", "F", "C"]:
		output = "\tFPTS\tTEAM\tPLAYER"
		reddit += "PTS|PLAYER"
		props = ["pts", "reb", "ast", "stl", "blk", "to"]
		for prop in props:
			output += f"\t{prop.upper()}"
		#output += "\tINC"
		output += "\n"
		reddit += "\n"

		posIdx = {}
		for pts, player, p, team, propPts, inc, j in sorted(sortedOutputs[pos], reverse=True):
			if p not in posIdx:
				posIdx[p] = 1
			x = f"{p}{posIdx[p]}"
			output += f"{x}"

			if player == "lebron james":
				print(player, propPts.get("stl"), j.get("stl"))

			j = {
				"player": player.title(),
				"pos": p,
				"rank": x,
				"pts": round(pts, 1),
				#"fpDiff": fpDiff.replace("'", ""),
			}

			output += f"\t{round(pts, 1)}\t{team.upper()}\t{player.title()}"
			for prop in props:
				x = 0
				if prop in propPts:
					x = round(propPts[prop], 2)
				output += f"\t{x or '-'}"
				j[prop] = x

			#j["inc"] = ",".join(inc.keys())

			# incomplete highlight
			#output += "\t,"+",".join(inc.keys())+","
			output += "\n"
			if pos == "ALL":
				table.append(j)
			posIdx[p] += 1

		with open(f"static/nba/rank_{pos}.csv", "w") as fh:
			fh.write(output)

	with open(f"static/nba/ranks.json", "w") as fh:
		json.dump(table, fh, indent=4)

def writeDaily():
	with open(f"{prefix}static/nba/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nba/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/nba/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/nba/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/nba/bet365.json") as fh:
		bet365Lines = json.load(fh)

	espnLines = {}
	parseESPN(espnLines)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"dk": dkLines,
		"cz": czLines,
		"espn": espnLines,
		"365": bet365Lines
	}

	date = str(datetime.now())[:10]
	with open(f"static/nba/lines/{date}.json", "w") as fh:
		json.dump(lines, fh)

def writeEV(propArg="", bookArg="fd", teamArg="", notd=None, boost=None):

	if not boost:
		boost = 1

	with open(f"updated.json") as fh:
		updated = json.load(fh)
	updated["nba"] = str(datetime.now())
	with open(f"updated.json", "w") as fh:
		json.dump(updated, fh, indent=4)

	with open(f"{prefix}static/nba/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/nba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nba/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/nba/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/nba/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/nba/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/nba/circa.json") as fh:
		circaLines = json.load(fh)

	with open(f"{prefix}static/nba/espn.json") as fh:
		espnLines = json.load(fh)

	with open(f"{prefix}static/nba/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/basketballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	with open(f"{prefix}static/basketballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	with open(f"{prefix}static/basketballreference/trades.json") as fh:
		trades = json.load(fh)

	with open(f"{prefix}static/basketballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"{prefix}static/basketballreference/scores.json") as fh:
		scores = json.load(fh)

	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/basketballreference/splits.json") as fh:
		splits = json.load(fh)

	with open(f"{prefix}static/nba/matchups.json") as fh:
		matchups = json.load(fh)

	with open(f"{prefix}static/nba/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/nba/minutes.json") as fh:
		minutes = json.load(fh)

	lines = {
		"pn": pnLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"dk": dkLines,
		"cz": czLines,
		"espn": espnLines,
		"365": bet365Lines,
		"circa": circaLines
	}

	with open(f"{prefix}static/nba/ev.json") as fh:
		evData = json.load(fh)

	evData = {}
	htmlData = []

	teamGame = {}
	for game in pnLines:
		away, home = map(str, game.split(" @ "))
		teamGame[away] = teamGame[home] = game

	for game in pnLines:
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

			if "live" in prop or "+ three" in prop or "+ ast" in prop or "+ reb" in prop or "+ pts" in prop:
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
							else:
								for h in lineData[game][prop][player]:
									handicaps[(handicap, " ")] = player

			for handicap, playerHandicap in handicaps:
				player = handicaps[(handicap, playerHandicap)]

				# last year stats
				lastTotalOverPerMin = 0
				lastTotalOver = lastTotalGames = 0
				last10TotalOver = last20TotalOver = last50TotalOver = 0
				totalGames = totalOver = totalOverPerMin = 0
				total15Over = total15OverPerMin = 0
				total10Over = total10OverPerMin = 0
				totalSplits = ""
				dtSplits = ""
				totalSplitsPerMin = []
				avgMin = []
				winLossSplits = [0,0]
				awayHomeSplits = [0,0]
				winLossSplitsPerMin = [0,0]
				awayHomeSplitsPerMin = [0,0]
				team = opp = gameLine = ""
				away, home = map(str, game.split(" @ "))
				if "away_total" in prop:
					team = away
					opp = home
				elif "home_total" in prop:
					team = home
					opp = away
				elif player:
					convertedProp = prop
					t = away
					if home in playerIds and player in playerIds[home]:
						t = home

					team = t
					playerSplits = {}
					if player in trades:
						for hdr in splits[trades[player]][player]:
							playerSplits[hdr] = splits[trades[player]][player][hdr]
						for hdr in splits[team].get(player, []):
							playerSplits[hdr] += ","+splits[team][player][hdr]
					elif team in splits and player in splits[team]:
						playerSplits = splits[team][player]

					projMin = 0
					if team in minutes:
						projMin = minutes[team].get(player, 0)
					minArr = playerSplits.get("min", "").split(",")
					winLossArr = playerSplits.get("winLoss", "").split(",")
					awayHomeArr = playerSplits.get("awayHome", "").split(",")
					dtSplits = playerSplits.get("dt", "")

					totalSplits = playerSplits.get(prop, "")
					if len(minArr) > 1 and prop in playerSplits:
						totalOver = round(len([x for x in playerSplits[prop].split(",") if int(x) > float(playerHandicap)]) * 100 / len(minArr))
						totalOverPerMin = round(len([x for i, x in enumerate(playerSplits[prop].split(",")) if int(x) * projMin / int(minArr[i]) > float(playerHandicap)]) * 100 / len(minArr))
						total15Over = round(len([x for x in playerSplits[prop].split(",")[-15:] if int(x) > float(playerHandicap)]) * 100 / len(minArr[-15:]))
						total15OverPerMin = round(len([x for x, m in zip(playerSplits[prop].split(",")[-15:], minArr[-15:]) if int(x) * projMin / int(m) > float(playerHandicap)]) * 100 / len(minArr[-15:]))
						total10Over = round(len([x for x in playerSplits[prop].split(",")[-10:] if int(x) > float(playerHandicap)]) * 100 / len(minArr[-10:]))
						total10OverPerMin = round(len([x for x, m in zip(playerSplits[prop].split(",")[-10:], minArr[-10:]) if int(x) * projMin / int(m) > float(playerHandicap)]) * 100 / len(minArr[-10:]))

					winArrLength = len([x for x in winLossArr if x == "W"])
					if winArrLength and prop in playerSplits:
						winLossSplits[0] = round(len([x for x, wl in zip(playerSplits[prop].split(","), winLossArr) if wl == "W" and int(x) > float(playerHandicap)]) * 100 / winArrLength)
						winLossSplitsPerMin[0] = round(len([x for x, wl, m in zip(playerSplits[prop].split(","), winLossArr, minArr) if wl == "W" and int(x) * projMin / int(m) > float(playerHandicap)]) * 100 / winArrLength)
					loseArrLength = len([x for x in winLossArr if x == "L"])
					if loseArrLength and prop in playerSplits:
						winLossSplits[1] = round(len([x for x, wl in zip(playerSplits[prop].split(","), winLossArr) if wl == "L" and int(x) > float(playerHandicap)]) * 100 / loseArrLength)
						winLossSplitsPerMin[1] = round(len([x for x, wl, m in zip(playerSplits[prop].split(","), winLossArr, minArr) if wl == "L" and int(x) * projMin / int(m) > float(playerHandicap)]) * 100 / loseArrLength)

					awayArrLength = len([x for x in awayHomeArr if x == "A"])
					if awayArrLength and prop in playerSplits:
						awayHomeSplits[0] = round(len([x for x, wl in zip(playerSplits[prop].split(","), awayHomeArr) if wl == "A" and int(x) > float(playerHandicap)]) * 100 / awayArrLength)
						awayHomeSplitsPerMin[0] = round(len([x for x, wl, m in zip(playerSplits[prop].split(","), awayHomeArr, minArr) if wl == "A" and int(x) * projMin / int(m) > float(playerHandicap)]) * 100 / awayArrLength)

					homeArrLength = len([x for x in awayHomeArr if x == "H"])						
					if homeArrLength and prop in playerSplits:
						awayHomeSplits[1] = round(len([x for x, wl in zip(playerSplits[prop].split(","), awayHomeArr) if wl == "H" and int(x) > float(playerHandicap)]) * 100 / homeArrLength)
					
						awayHomeSplitsPerMin[1] = round(len([x for x, wl, m in zip(playerSplits[prop].split(","), awayHomeArr, minArr) if wl == "H" and int(x) * projMin / int(m) > float(playerHandicap)]) * 100 / homeArrLength)

					if team in lastYearStats and player in lastYearStats[team] and lastYearStats[team][player]:
						for idx, d in enumerate(lastYearStats[team][player]):
							m = lastYearStats[team][player][d]["min"]
							if m > 0 and (convertedProp in lastYearStats[team][player][d] or "+" in convertedProp):
								lastTotalGames += 1
								val = 0
								for p in convertedProp.split("+"):
									val += lastYearStats[team][player][d][p]
								if val > float(playerHandicap):
									lastTotalOver += 1
									if idx < 10:
										last10TotalOver += 1
									if idx < 20:
										last20TotalOver += 1
									if idx < 50:
										last50TotalOver += 1
								if val * projMin / m > float(playerHandicap):
									lastTotalOverPerMin += 1
					if lastTotalGames:
						lastTotalOver = int(lastTotalOver * 100 / lastTotalGames)
						lastTotalOverPerMin = int(lastTotalOverPerMin * 100 / lastTotalGames)
						last10TotalOver = int(last10TotalOver * 100 / (10 if lastTotalGames >= 10 else lastTotalGames))
						last20TotalOver = int(last20TotalOver * 100 / (20 if lastTotalGames >= 20 else lastTotalGames))
						last50TotalOver = int(last50TotalOver * 100 / (50 if lastTotalGames >= 50 else lastTotalGames))

				for i in range(2):
					highestOdds = []
					books = []
					odds = []

					if lastTotalOver and i == 1:
						lastTotalOver = 100 - lastTotalOver
						lastTotalOverPerMin = 100 - lastTotalOverPerMin
						last50TotalOver = 100 - last50TotalOver
						last20TotalOver = 100 - last20TotalOver
					if totalOver and i == 1:
						totalOver = 100 - totalOver
						totalOverPerMin = 100 - totalOverPerMin
						total15Over = 100 - total15Over
						total15OverPerMin = 100 - total15OverPerMin
						total10Over = 100 - total10Over
						total10OverPerMin = 100 - total10OverPerMin

					for book in lines:
						lineData = lines[book]
						#if book == "dk" and "+" in prop:
						#	continue
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
									if prop != "first_3ptm" and playerHandicap != val.split(" ")[0]:
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

							try:
								highestOdds.append(int(o.replace("+", "")))
							except:
								continue
							odds.append(ou)
							books.append(book)

					if len(books) < 2:
						continue

					if len(books) < 3 and ("spread" in prop or "total" in prop):
						continue

					#print(game, prop, handicap, highestOdds, books, odds)

					removed = {}
					removedBooks = ["pn", "circa", "365"]
					for book in removedBooks:
						try:
							bookIdx = books.index(book)
							o = odds[bookIdx]
							del odds[bookIdx]
							books.remove(book)
							removed[book] = o
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
					
					for book in removed:
						books.append(book)
						l.append(removed[book])

					avgOver = []
					avgUnder = []
					for book in l:
						if book and book != "-":
							try:
								avgOver.append(convertDecOdds(int(book.split("/")[0])))
								if "/" in book:
									avgUnder.append(convertDecOdds(int(book.split("/")[1])))
							except:
								continue

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
						
					bookOdds = {b: o for o, b in zip(l, books)}
					key = f"{game} {handicap} {playerHandicap} {prop} {'over' if i == 0 else 'under'}"
					if key in evData:
						continue
					if True:
						pass
						#print(key, ou, line)
						devig(evData, key, ou, line, prop=prop)
						if bookOdds.get("pn"):
							o = bookOdds["pn"]
							if i == 1:
								o = f"{o.split('/')[1]}/{o.split('/')[0]}"
							devig(evData, key, o, line, prop=prop, sharp=True)
						#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
						if key not in evData:
							#print(key)
							continue
						if float(evData[key]["ev"]) > 0:
							#print(evData[key]["ev"], game, handicap, prop, int(line), ou, books)
							pass

						pos = oppRank = oppRankPos = rank = posRank = ""
						oppRankClass = oppRankPosClass = ""
						isAway = "A"
						if player:
							if player in roster[team]:
								pos = roster[team][player].lower()
							opp = home
							away, home = map(str, game.split(" @ "))
							if team == home:
								opp = away
								isAway = "H"
							try:
								rank = matchups[opp]["szn"]["all"][prop+"Rank"]
								oppRank = rank
								oppRankClass = matchups[opp]["szn"]["all"][prop+"RankClass"]
								posRank = matchups[opp]["szn"][pos][prop+"Rank"]
								oppRankPos = posRank
								oppRankPosClass = matchups[opp]["szn"][pos][prop+"RankClass"]
							except:
								pass

							if game in lines["fd"] and "ml" in lines["fd"][game]:
								if isAway == "A":
									gameLine = lines["fd"][game]["ml"].split('/')[0]
								else:
									gameLine = lines["fd"][game]["ml"].split('/')[1]

						implied = 0
						if line > 0:
							implied = 100 / (line + 100)
						else:
							implied = -1*line / (-1*line + 100)
						implied *= 100

						winLoss = f"{winLossSplits[0]}% - {winLossSplits[1]}%"
						winLossPerMin = f"{winLossSplitsPerMin[0]}% - {winLossSplitsPerMin[1]}%"
						awayHome = f"{awayHomeSplits[0]}% - {awayHomeSplits[1]}%"
						awayHomePerMin = f"{awayHomeSplitsPerMin[0]}% - {awayHomeSplitsPerMin[1]}%"
						if i == 1:
							winLoss = f"{100 - winLossSplits[0]}% - {100 - winLossSplits[1]}%"
							winLossPerMin = f"{100 - winLossSplitsPerMin[0]}% - {100 - winLossSplitsPerMin[1]}%"
							awayHome = f"{100 - awayHomeSplits[0]}% - {100 - awayHomeSplits[1]}%"
							awayHomePerMin = f"{100 - awayHomeSplitsPerMin[0]}% - {100 - awayHomeSplitsPerMin[1]}%"

						confirmed = False
						starting = False
						if team in lineups:
							confirmed = lineups[team]["confirmed"]

						evData[key]["imp"] = round(implied)
						evData[key]["rank"] = rank
						evData[key]["winLossSplits"] = winLoss
						evData[key]["awayHomeSplits"] = awayHome
						evData[key]["winLossSplitsPerMin"] = winLossPerMin
						evData[key]["awayHomeSplitsPerMin"] = awayHomePerMin
						evData[key]["oppRank"] = oppRank
						evData[key]["oppRankPos"] = oppRankPos
						evData[key]["oppRankClass"] = oppRankClass
						evData[key]["oppRankPosClass"] = oppRankPosClass
						evData[key]["posRank"] = posRank
						evData[key]["totalOver"] = totalOver
						evData[key]["totalOverPerMin"] = totalOverPerMin
						evData[key]["total15Over"] = total15Over
						evData[key]["total15OverPerMin"] = total15OverPerMin
						evData[key]["total10Over"] = total10Over
						evData[key]["total10OverPerMin"] = total10OverPerMin
						evData[key]["dtSplits"] = dtSplits
						evData[key]["totalSplits"] = totalSplits
						evData[key]["totalSplitsPerMin"] = ",".join(totalSplitsPerMin)
						evData[key]["lastYearTotal"] = lastTotalOver
						evData[key]["lastYearTotalPerMin"] = lastTotalOverPerMin
						evData[key]["last10YearTotal"] = last10TotalOver
						evData[key]["last20YearTotal"] = last20TotalOver
						evData[key]["last50YearTotal"] = last50TotalOver
						evData[key]["team"] = team
						evData[key]["opp"] = opp
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
						evData[key]["confirmed"] = confirmed
						bookOdds[evBook] = maxOU
						evData[key]["bookOdds"] = bookOdds
						

						if player:
							j = {
								"player": player.title(),
								"pos": pos.upper(),
								"rank": int(rank[:-2]) if rank else "",
								"posRank": int(posRank[:-2]) if posRank else "",
								"line": f"{'o' if i == 0 else 'u'}{playerHandicap}",
								"handicap": playerHandicap,
								"book": f"{line} {evBook.replace('kambi', 'br').upper()}",
								"evBook": evBook,
								"odds": line,
								"totalSplits": ",".join(totalSplits.split(",")[-10:]),
								"totalSplitsPerMin": ",".join(totalSplitsPerMin[-10:]),
								"avgMin": 0 if not projMin else round(projMin),
								"isAway": isAway,
								"gameLine": gameLine,
								"bookOdds": bookOdds
							}
							for x in ["prop", "team", "opp", "totalOver", "totalOverPerMin", "total10Over", "total10OverPerMin", "total15Over", "total15OverPerMin", "lastYearTotal", "ev", "imp", "awayHomeSplits", "winLossSplits", "awayHomeSplitsPerMin", "winLossSplitsPerMin", "confirmed"]:
								j[x] = evData[key][x]
							htmlData.append(j)

	with open(f"{prefix}static/nba/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	with open(f"{prefix}static/nba/html.json", "w") as fh:
		json.dump(htmlData, fh, indent=4)

	with open(f"{prefix}static/nba/evArr.json", "w") as fh:
		json.dump([value for key, value in evData.items()], fh)

def get_suffix(num):
	if num >= 11 and num <= 13:
		return "th"
	elif num % 10 == 1:
		return "st"
	elif num % 10 == 2:
		return "nd"
	elif num % 10 == 3:
		return "rd"
	return "th"

def printHistorical():
	with open("static/basketballreference/roster.json") as fh:
		roster = json.load(fh)

	date = "2024-05-18"

	bets = [("kyrie irving", "pts", 19.5, -115), ("jaylin williams", "pts+reb", 5.5, 100)]

	win = loss = profit = 0
	for player, prop, line, odds in bets:
		team = ""
		for t in roster:
			if player in roster[t]:
				team = t
				break

		if not team:
			print(player, "no team")
			continue
		
		with open(f"static/basketballreference/{team}/{date}.json") as fh:
			stats = json.load(fh)

		if player not in stats:
			print(f"{player} not in")
			continue

		minutes = stats[player].get("min", 0)
		if minutes == 0:
			continue

		val = 0
		for p in prop.split("+"):
			val += stats[player].get(p, 0)

		if val > line:
			win += 1
			if odds > 0:
				profit += (odds / 100)
			else:
				profit += (100 / (odds * -1))
		else:
			loss += 1
			profit -= 1

	print(f"{win}W-{loss}L profit={round(profit, 4)}")

def writeMatchups():
	url = "https://www.fantasypros.com/nba/defense-vs-position.php"
	outfile = "outnba"
	os.system(f"curl -s \"{url}\" -o {outfile}")
	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = {}
	rankings = {}
	for tr in soup.find("table", id="data-table").find_all("tr")[1:]:
		period = "szn"
		if "GC-7" in tr.get("class"):
			period = "L7"
		elif "GC-15" in tr.get("class"):
			period = "L15"
		elif "GC-30" in tr.get("class"):
			period = "L30"

		pos = "all"
		if "PG" in tr.get("class"):
			pos = "pg"
		elif "SG" in tr.get("class"):
			pos = "sg"
		elif "SF" in tr.get("class"):
			pos = "sf"
		elif "PF" in tr.get("class"):
			pos = "pf"
		elif "C" in tr.get("class"):
			pos = "c"
		elif "TM" in tr.get("class"):
			continue

		team = convertNBATeam(tr.find("td").text)
		if team not in data:
			data[team] = {}
		if period not in data[team]:
			data[team][period] = {}

		data[team][period][pos] = {}
		props = ["pts", "reb", "ast", "3ptm", "stl", "blk", "to", "fg%", "ft%"]
		for td, prop in zip(tr.find_all("td")[1:], props):
			key = f"{period}_{pos}_{prop}"
			if key not in rankings:
				rankings[key] = []
			rankings[key].append((float(td.text), team))
			data[team][period][pos][prop] = float(td.text)

		for prop in ["pts+reb", "pts+ast", "pts+reb+ast", "stl+blk", "reb+ast"]:
			key = f"{period}_{pos}_{prop}"
			if key not in rankings:
				rankings[key] = []
			val = 0
			for p in prop.split("+"):
				val += data[team][period][pos][p]
			rankings[key].append((val, team))
			data[team][period][pos][prop] = round(val, 2)

	rankingsKey = {}
	for key in rankings:
		rankings[key] = sorted(rankings[key])
		idx = 1
		for num, team in rankings[key]:
			rankingsKey[f"{team}_{key}"] = idx
			idx += 1

	for team in data:
		for period in data[team]:
			for pos in data[team][period]:
				for prop in data[team][period][pos].copy():
					rank = rankingsKey[f"{team}_{period}_{pos}_{prop}"]
					rankClass = ""
					if int(rank) <= 10:
						rankClass = "negative"
					elif int(rank) >= 20:
						rankClass = "positive"
					data[team][period][pos][f"{prop}Rank"] = f"{rank}{get_suffix(rank)}"
					data[team][period][pos][f"{prop}RankClass"] = rankClass

	with open("static/nba/matchups.json", "w") as fh:
		json.dump(data, fh, indent=4)

def sortEV(noDaily=False):
	if not noDaily:
		writeDaily()

	with open(f"{prefix}static/nba/ev.json") as fh:
		evData = json.load(fh)

	with open(f"{prefix}static/nba/matchups.json") as fh:
		matchups = json.load(fh)

	with open(f"{prefix}static/basketballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"{prefix}static/basketballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	#with open(f"static/nba/totals.json") as fh:
	#	totals = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], d["game"], player, d["playerHandicap"], d["line"], d["book"], j, d["lastYearTotal"], d))

	for row in sorted(data):
		if "total" in row[-1]["prop"] or "spread" in row[-1]["prop"] or "ml" in row[-1]["prop"] or row[-1]["prop"] == "first_3ptm":
			continue
		print(row[:-1])


	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Player", "DK", "CZ", "ESPN"]) + "\n"
	for row in sorted(data, reverse=True):
		player = row[-1]["player"]
		prop = row[-1]["prop"]
		if prop != "first_3ptm":
			continue
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper(), f"{round(row[-1]['imp'])}%", row[-1]["game"].upper(), player.title()]
		for book in ["dk", "cz", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nba/threesday.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Prop", "O/U", "FD", "DK", "MGM", "Bet365", "PN", "Kambi/BR", "CZ", "ESPN"]) + "\n"
	for row in sorted(data, reverse=True):
		player = row[-1]["player"]
		prop = row[-1]["prop"]
		if "total" not in prop and "spread" not in prop and "ml" not in prop:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "+row[-1]["handicap"]
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), f"{round(row[-1]['imp'])}%", row[-1]["game"].upper(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "365", "pn", "kambi", "cz", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nba/lines.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Team", "Player", "Prop", "O/U", "FD", "DK", "MGM", "Bet365", "PN", "Kambi/BR", "CZ", "ESPN", "LYR %", "L10 %", "SZN %", "Splits", "Def Rank", "Def Pos Rank", "IN"]) + "\n"
	for row in sorted(data, reverse=True):
		player = row[-1]["player"]
		prop = row[-1]["prop"]
		if "total" in prop or "spread" in prop or "ml" in prop or prop == "first_3ptm":
			continue
		
		ou = ("u" if row[-1]["under"] else "o")+" "
		if player:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR").replace("BET365", "365"), f"{round(row[-1]['imp'])}%", row[-1]["game"].upper(), row[-1]['team'].upper(), player.title(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "365", "pn", "kambi", "cz", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		arr.append(f"{row[-1]['lastYearTotal']}%")
		#arr.append(f"{row[-1]['last50YearTotal']}%")
		arr.append(f"{row[-1]['total10Over']}%")
		arr.append(f"{row[-1]['totalOver']}%")
		arr.append(",".join(row[-1]["totalSplits"].split(",")[-10:]))
		arr.extend([row[-1]["rank"], row[-1]["posRank"]])
		if row[-1]["confirmed"]:
			arr.append("🟢")
		else:
			arr.append("🟡")
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nba/props.csv", "w") as fh:
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
	parser.add_argument("--matchups", action="store_true", help="Matchups")
	parser.add_argument("--lineups", action="store_true", help="Lineups")
	parser.add_argument("--minutes", action="store_true", help="Minutes")
	parser.add_argument("--lineupsLoop", action="store_true", help="Lineups")
	parser.add_argument("--debug", action="store_true", help="Debug")
	parser.add_argument("--notd", action="store_true", help="Not ATTD FTD")
	parser.add_argument("--threesday", action="store_true", help="3sday")
	parser.add_argument("--injuries", action="store_true", help="injuries")
	parser.add_argument("--leaders", action="store_true", help="leaders")
	parser.add_argument("--no-daily", action="store_true")
	parser.add_argument("--sgp", action="store_true", help="SGP")
	parser.add_argument("--tmrw", action="store_true")
	parser.add_argument("--insurance", action="store_true")
	parser.add_argument("--historical", action="store_true")
	parser.add_argument("--writeSGP", action="store_true", help="Write SGP")
	parser.add_argument("--ranks", action="store_true")
	parser.add_argument("--commit", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--circa", action="store_true")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--token")
	parser.add_argument("--player", help="Player")

	args = parser.parse_args()

	if args.lineups:
		writeLineups(args.tmrw)

	if args.minutes:
		writeLineups(args.tmrw)
		writeMinutes()

	date = str(datetime.now())[:10]
	if args.date:
		data = args.date

	dinger = False
	if args.dinger:
		dinger = True

	if args.writeSGP:
		writeSGP()

	if args.sgp:
		readSGP()
	if args.insurance:
		readSGP(insurance=True)

	if args.injuries:
		writeInjuries()

	if args.leaders:
		writeLeaders()

	if args.threesday:
		writeRankings()
		writeLineups()
		writeThreesday()
		writeInjuries()
		writeLeaders()

	if args.action:
		writeActionNetwork(args.date)

	if args.fd:
		writeFanduel()

	if args.mgm:
		writeMGM(args.date)

	if args.pb:
		writePointsbet(args.date)

	if args.dk:
		writeDK(args.date, args.debug, args.keep)

	if args.kambi:
		writeKambi(args.date)

	if args.pn:
		writePinnacle(args.date, args.debug)

	if args.bv:
		writeBV(args.date)

	if args.bvParlay:
		bvParlay()

	if args.circa:
		writeCirca(date, args.debug)

	if args.cz:
		uc.loop().run_until_complete(writeCZToken())
		writeCZ(args.date)

	if args.matchups:
		writeMatchups()

	if args.update:
		#writeFanduel()
		writeMatchups()
		print("pn")
		writePinnacle(args.date, args.debug)
		#print("br")
		#writeKambi(args.date)
		#print("mgm")
		#writeMGM(args.date)
		#print("pb")
		#writePointsbet(args.date)
		print("dk")
		writeDK(args.date, args.debug, args.keep)
		print("cz")
		uc.loop().run_until_complete(writeCZToken())
		writeCZ(args.date)
		#print("bv")
		#writeBV(args.date)

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, teamArg=args.team, notd=args.notd, boost=args.boost)

	if args.print:
		sortEV(args.no_daily)

	if args.player:
		writePlayer(args.player, args.prop)

	if args.historical:
		printHistorical()

	if args.ranks:
		writeRanks()

	if args.commit:
		commitChanges()