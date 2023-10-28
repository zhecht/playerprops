
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

def writePointsbet():
	url = "https://api.mi.pointsbet.com/api/v2/competitions/12864/events/featured?includeLive=false&page=1"
	outfile = f"outPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"outPB"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		game = data["name"].lower().replace(" v ", " @ ")
		away, home = map(str, game.split(" @ "))
		res[game] = {}

		for market in data["fixedOddsMarkets"]:
			prop = market["name"].lower().split(" (")[0]

			if prop == "point spread":
				prop = "spread"
			elif prop == "spread 1st half":
				prop = "1h_spread"
			elif prop == "spread 1st quarter":
				prop = "1q_spread"
			elif prop == "moneyline":
				prop = "ml"
			elif prop == "moneyline 1st half":
				prop = "1h_ml"
			elif prop == "moneyline 1st quarter":
				prop = "1q_ml"
			elif prop == "total":
				prop = "total"
			elif prop == "total 1st half":
				prop = "1h_total"
			elif prop == "total 1st quarter":
				prop = "1q_total"
			elif prop == f"{away} total":
				prop = "away_total"
			elif prop == f"{home} total":
				prop = "home_total"
			elif prop == f"{away} total 1st quarter":
				prop = "1q_away_total"
			elif prop == f"{home} total 1st quarter":
				prop = "1q_home_total"
			elif prop.startswith("player"):
				if " + " in prop:
					continue
				else:
					prop = prop.split(" ")[1].replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb")
			else:
				continue

			if "ml" not in prop:
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			for i in range(0, len(outcomes), 2):
				points = str(outcomes[i]["points"])
				over = convertAmericanOdds(outcomes[i]["price"])
				under = convertAmericanOdds(outcomes[i+1]["price"])
				ou = f"{over}/{under}"

				if "ml" in prop:
					res[game][prop] = ou
				elif prop in ["pts", "reb", "ast"]:
					player = outcomes[i]["name"].lower().split(" over")[0]
					res[game][prop][player] = f"{outcomes[i]['name'].split(' ')[-1]} {ou}"
				else:
					res[game][prop][points] = ou

	with open("static/fiba/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePinnacle(date):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/basketball/fiba-world-cup/matchups#period:0"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/9585/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o outPN'

	os.system(url)
	outfile = f"outPN"
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	for row in data:
		if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
		player1 = row["participants"][0]["name"].lower()
		player2 = row["participants"][1]["name"].lower()
		games[str(row["id"])] = f"{player1} @ {player2}"

	
	res = {}
	for gameId in games:
		game = games[gameId]
		url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o outPN'

		time.sleep(0.3)
		os.system(url)
		with open(outfile) as fh:
			data = json.load(fh)

		res[game] = {}

		for row in data:
			prop = row["type"]
			keys = row["key"].split(";")

			prefix = ""
			if keys[1] == "1":
				prefix = "1h_"

			if prop == "moneyline":
				prop = f"{prefix}ml"
			elif prop == "spread":
				prop = f"{prefix}spread"
			elif prop == "total":
				prop = f"{prefix}total"
			elif prop == "team_total":
				awayHome = "away" if row['side'] == "home" else "home"
				prop = f"{prefix}{awayHome}_total"


			prices = row["prices"]
			ou = f"{prices[0]['price']}/{prices[1]['price']}"
			if "points" in prices[0]:
				handicap = str(prices[0]["points"])
				if prop not in res[game]:
					res[game][prop] = {}
				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

	with open("static/fiba/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBV():
	url = "https://www.bovada.lv/sports/basketball/fiba-world-cup"
	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/fiba-world-cup?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
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
		game = f"{comp[0]['name'].lower()} @ {comp[1]['name'].lower()}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "player points", "player rebounds", "assists & threes", "blocks & steals", "player turnovers"]:
				for market in row["markets"]:
					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "total":
						prop = "total"
					elif prop == "point spread":
						prop = "spread"
					elif prop.startswith("total points"):
						prop = "pts"
					elif prop.startswith("total rebounds"):
						prop = "reb"
					elif prop.startswith("total made 3 points"):
						prop = "3ptm"
					elif prop.startswith("total assists"):
						prop = "ast"
					elif prop.startswith("total blocks"):
						prop = "blk"
					elif prop.startswith("total steals"):
						prop = "stl"
					elif prop.startswith("total turnovers"):
						prop = "to"
					else:
						continue

					if market["period"]["description"].lower() == "first half":
						prop = f"1h_{prop}"
					elif market["period"]["description"].lower() == "1st quarter":
						prop = f"1q_{prop}"

					if not len(market["outcomes"]):
						continue

					if "ml" in prop:
						res[game][prop] = f"{market['outcomes'][1]['price']['american']}/{market['outcomes'][0]['price']['american']}".replace("EVEN", "100")
					elif "total" in prop or prop in ["pts", "reb", "ast", "3ptm", "blk", "stl", "to"]:
						handicap = market["outcomes"][0]["price"]["handicap"]
						if prop not in res[game]:
							res[game][prop] = {}

						if "total" in prop:
							res[game][prop][handicap] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
						else:
							player = parsePlayer(market["descriptionKey"].split(" - ")[-1])
							try:
								res[game][prop][player] = f"{handicap} {market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
							except:
								pass
					else:
						if prop not in res[game]:
							res[game][prop] = {}
						handicap = market["outcomes"][1]["price"]["handicap"]
						res[game][prop][handicap] = f"{market['outcomes'][1]['price']['american']}/{market['outcomes'][0]['price']['american']}".replace("EVEN", "100")


	with open("static/fiba/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM():

	res = {}

	url = "https://sports.mi.betmgm.com/en/sports/basketball-7/betting/world-6/fiba-world-cup-men-9029"

	url = f"https://sports.mi.betmgm.com/en/sports/api/widget?layoutSize=Large&page=CompetitionLobby&sportId=7&regionId=6&competitionId=9029&compoundCompetitionId=1:9029&forceFresh=1&shouldIncludePayload=true"
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
		ids.append(row["id"])

	for mgmid in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		data = data["fixture"]
		if " - " not in data["name"]["value"]:
			continue
		game = strip_accents(data["name"]["value"].lower()).replace(" - ", " @ ")
		team1, team2 = game.split(" @ ")

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
			elif prop.startswith("how many "):
				if prop.startswith("how many points will be scored in the game"):
					continue
				if team1 in prop or team2 in prop:
					p = "away_total"
					team = prop.split(" will ")[-1].split(" score")[0]
					if game.endswith(team):
						p = "home_total"
					prop = p
				else:
					player = parsePlayer(prop.split(" (")[0].split(" will ")[-1])
					prop = prop.split(" ")[2].replace("assists", "ast").replace("points", "pts").replace("rebounds", "reb").replace("blocks", "blk").replace("steals", "stl").replace("three-pointers", "3ptm")
					if prop == "total":
						continue
			else:
				continue

			prop = prefix+prop

			results = row['results']
			ou = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
			if "ml" in prop:
				res[game][prop] = ou
			elif len(results) >= 2:
				if prop not in res[game]:
					res[game][prop] = {}

				skip = 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop:
						continue
					else:
						val = val.split(" ")[-1]
					#print(game, prop, player)
					ou = f"{results[idx]['americanOdds']}/{results[idx+1]['americanOdds']}"

					if player:
						res[game][prop][player] = val+" "+ou
					else:
						res[game][prop][val] = ou

	with open("static/fiba/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi():
	data = {}
	outfile = f"outfiba.json"
	url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/basketball/fiba_world_cup"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/basketball/fiba_world_cup/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	eventIds = {}
	for event in j["events"]:
		game = event["event"]["name"].lower()
		team1, team2 = map(str, game.split(" @ "))
		game = f"{team2} @ {team1}"
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		i = 0
		for betOffer in j["betOffers"]:
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
			elif label.startswith("points scored"):
				label = "pts"
			elif label.startswith("rebounds"):
				label = "reb"
			elif label.startswith("assists"):
				label = "ast"
			elif label.startswith("3-point"):
				label = "3ptm"

			if label in ["ml", "1h_ml", "2h_ml", "1q_ml"]:
				team = betOffer["outcomes"][0]["label"].lower()
				if label != "ml":
					team = betOffer["outcomes"][0]["participant"].lower()
				if game.startswith(team):
					data[game][label] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				else:
					data[game][label] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label in ["1h_total", "2h_total", "1q_total", "1h_away_total", "1h_home_total", "1q_away_total", "1q_home_total"]:
				if label not in data[game]:
					data[game][label] = {}
				line = betOffer["outcomes"][0]["line"] / 1000
				data[game][label][str(line)] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
			elif label in ["spread", "1h_spread", "2h_spread", "1q_spread"]:
				if label not in data[game]:
					data[game][label] = {}
				line = betOffer["outcomes"][0]["line"] / 1000
				line2 = betOffer["outcomes"][1]["line"] / 1000
				team = betOffer["outcomes"][0]["label"].lower()
				if game.startswith(team):
					data[game][label][line] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				else:
					data[game][label][line2] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label in ["total", "pts", "reb", "ast", "3ptm", "away_total", "home_total"]:
				if label not in data[game]:
					data[game][label] = {}
				line = betOffer["outcomes"][0]["line"] / 1000
				if "total" in label:
					data[game][label][str(line)] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				else:
					player = betOffer["outcomes"][0]["participant"].split(" (")[0].lower()
					if "," in player:
						last, first = map(str, player.split(", ")
							)
					else:
						last, first = map(str, player.split(" "))
					ou = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
					if betOffer["outcomes"][0]["label"] == "Under":
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					player = parsePlayer(f"{first} {last}")
					data[game][label][player] = str(line)+" "+ou


	with open(f"{prefix}static/fiba/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

def parsePlayer(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("basketball/international") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && time.getAttribute("datetime").split("T")[0] === "2023-09-10") {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/usa-v-canada-32620584",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/germany-v-serbia-32620587"
]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		if game in lines:
			continue
		lines[game] = {}

		outfile = "out"

		for tab in ["", "player-points", "player-rebounds", "player-assists", "player-threes", "half", "alternates", "1st-quarter"]:
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

				if marketName in ["moneyline", "total points", "spread"] or " - points" in marketName or " - rebounds" in marketName or " - assists" in marketName or " - made threes" in marketName or marketName.startswith("1st half") or marketName.startswith("1st quarter") or marketName.startswith("alternative"):
					prop = ""
					if marketName == "moneyline":
						prop = "ml"
					elif marketName == "total points" or marketName.startswith("alternative total points"):
						prop = "total"
					elif marketName == "1st half total points":
						prop = "1h_total"
					elif marketName == "1st quarter total points":
						prop = "1q_total"
					elif marketName == "spread" or marketName.startswith("alternative handicap"):
						prop = "spread"
					elif "points" in marketName:
						prop = "pts"
					elif "rebounds" in marketName:
						prop = "reb"
					elif "assists" in marketName:
						prop = "ast"
					elif "threes" in marketName:
						prop = "3ptm"
					elif marketName == "1st half moneyline":
						prop = "1h_ml"
					elif marketName == "1st half spread":
						prop = "1h_spread"
					elif marketName == "1st quarter moneyline":
						prop = "1q_ml"
					elif marketName == "1st quarter spread":
						prop = "1q_spread"
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

						if "spread" in prop or "total" in prop:
							lines[game][prop][str(handicap)] = ou
						else:

							player = parsePlayer(marketName.split(" - ")[0])
							lines[game][prop][player] = f"{handicap} {ou}"
	
	with open(f"{prefix}static/fiba/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr"):

	over,under = map(int, ou.split("/"))
	impliedOver = impliedUnder = 0

	if over > 0:
		impliedOver = 100 / (over+100)
	else:
		impliedOver = -1*over / (-1*over+100)

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

	bet = 100
	profit = finalOdds / 100 * bet
	if finalOdds < 0:
		profit = 100 * bet / (finalOdds * -1)

	evs = []
	for method in [x, mult, add]:
		ev = method * profit + (1-method) * -1 * bet
		ev = round(ev, 1)
		evs.append(ev)

	ev = min(evs)

	if player not in evData:
		evData[player] = {}
	evData[player]["fairVal"] = fairVal
	evData[player]["implied"] = implied
	evData[player]["ev"] = ev

def writeDK(date):
	url = "https://sportsbook.draftkings.com/leagues/basketball/fiba-world-cup"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 487,
		"pts": 1215,
		"reb": 1216,
		"ast": 1217,
		"3ptm": 1218,
		"blk": 1263,
		"stl": 1294,
		"halves": 520,
		"quarters": 522,
		"team props": 523
	}
	
	subCats = {
		487: [4511, 13202, 13201, 12188],
		520: [4598, 6230],
		#522: [4600]
	}

	lines = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCat, [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/12550/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outfiba"
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
				game = event["name"].lower()
				team1, team2 = map(str, game.split(" @ "))
				game = f"{team2} @ {team1}"
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

							if "label" not in row:
								continue
							label = row["label"].lower().replace("moneyline", "ml").split(" [")[0]
							if label == "spread 1st half":
								label = "1h_spread"
							elif label == "total 1st half":
								label = "1h_total"
							elif label == "ml 1st half":
								label = "1h_ml"
							elif label == "spread 1st quarter":
								label = "1q_spread"
							elif label == "total 1st quarter":
								label = "1q_total"
							elif label == "ml 1st quarter":
								label = "1q_ml"
							elif label.endswith("team total points - 1st half"):
								team = label.split(":")[0]
								if game.startswith(team):
									label = "1h_away_total"
								else:
									label = "1h_home_total"
							elif label.endswith("team total points"):
								team = label.split(":")[0]
								if game.startswith(team):
									label = "away_total"
								else:
									label = "home_total"

							label = label.replace(" alternate", "")

							if label == "halftime/fulltime":
								continue

							if "ml" in label:
								lines[game][label] = ""
							elif "total" in label or "spread" in label:
								if label not in lines[game]:
									lines[game][label] = {}
							else:
								label = parsePlayer(label)
								if mainCat not in lines[game]:
									lines[game][mainCat] = {}

							outcomes = row["outcomes"]
							ou = ""
							try:
								ou = f"{outcomes[0]['oddsAmerican']}/{outcomes[1]['oddsAmerican']}"
								switchedOU = ou = f"{outcomes[1]['oddsAmerican']}/{outcomes[0]['oddsAmerican']}"
							except:
								continue

							if "ml" in label:
								lines[game][label] = switchedOU
							elif "total" in label or "spread" in label:
								for i in range(0, len(outcomes), 2):
									if "total" in label:
										line = outcomes[i]["line"]
										lines[game][label][str(line)] = f"{outcomes[i]['oddsAmerican']}/{outcomes[i+1]['oddsAmerican']}"
									else:
										line = outcomes[i+1]["line"]
										lines[game][label][str(line)] = f"{outcomes[i+1]['oddsAmerican']}/{outcomes[i]['oddsAmerican']}"
							else:
								lines[game][mainCat][label] = f"{outcomes[0]['line']} {outcomes[0]['oddsAmerican']}"
								if len(row["outcomes"]) > 1:
									lines[game][mainCat][label] += f"/{outcomes[1]['oddsAmerican']}"

	with open("static/fiba/draftkings.json", "w") as fh:
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

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None):

	if not boost:
		boost = 1

	with open(f"{prefix}static/fiba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/fiba/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/fiba/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/fiba/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/fiba/bovada.json") as fh:
		bovadaLines = json.load(fh)

	with open(f"{prefix}static/fiba/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/fiba/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/fiba/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/fiba/ev.json") as fh:
		evData = json.load(fh)

	evData = {}
	for game in dkLines:
		if teamArg and teamArg not in game:
			continue
		team1, team2 = map(str, game.split(" @ "))
		switchGame = f"{team2} @ {team1}"
		for prop in dkLines[game]:

			if propArg and prop != propArg:
				continue

			if type(dkLines[game][prop]) is dict:
				arr = dkLines[game][prop]
			else:
				arr = [None]

			for key in arr:
				dk = dkLines[game][prop]
				handicap = propHandicap = ""

				if " " in dk:
					handicap = str(float(dk.split(" ")[0]))

				if key:
					dk = dkLines[game][prop][key]
					handicap = key
					if " " in dk:
						propHandicap = str(float(dkLines[game][prop][key].split(" ")[0]))
				
				dk = dk.split(" ")[-1]

				kambi = ""
				if game in kambiLines and prop in kambiLines[game]:

					if handicap:
						if type(kambiLines[game][prop]) is dict:
							if handicap in kambiLines[game][prop]:
								kambi = kambiLines[game][prop][handicap]
								if " " in kambi:
									if float(kambi.split(" ")[0]) == float(propHandicap):
										kambi = kambi.split(" ")[-1]
									else:
										kambi = ""
						elif float(handicap) == float(kambiLines[game][prop].split(" ")[0]):
							kambi = kambiLines[game][prop].split(" ")[-1]
					else:
						kambi = kambiLines[game][prop]

				pn = ""
				if game in pnLines and prop in pnLines[game]:
					if type(pnLines[game][prop]) is dict:
						if handicap in pnLines[game][prop]:
							pn = pnLines[game][prop][handicap]
					else:
						pn = pnLines[game][prop]

				mgm = ""
				if game in mgmLines and prop in mgmLines[game]:
					if type(mgmLines[game][prop]) is dict:
						if handicap in mgmLines[game][prop]:
							mgm = mgmLines[game][prop][handicap]
							if " " in mgm:
								if float(mgm.split(" ")[0]) == float(propHandicap):
									mgm = mgm.split(" ")[-1]
								else:
									mgm = ""

					else:
						mgm = mgmLines[game][prop]

				bet365 = ""
				if game in bet365Lines and prop in bet365Lines[game]:
					if handicap:
						if type(bet365Lines[game][prop]) is dict:
							if handicap in bet365Lines[game][prop]:
								bet365 = bet365Lines[game][prop][handicap]
								if " " in bet365:
									if float(bet365.split(" ")[0]) == float(propHandicap):
										bet365 = bet365.split(" ")[-1]
									else:
										bet365 = ""
						elif float(handicap) == float(bet365Lines[game][prop].split(" ")[0]):
							bet365 = bet365Lines[game][prop].split(" ")[-1]
					else:
						bet365 = bet365Lines[game][prop]

					if "undefined" in bet365:
						bet365 = ""

				bv = ""
				if game in bovadaLines and prop in bovadaLines[game]:
					if handicap:
						if type(bovadaLines[game][prop]) is dict:
							if handicap in bovadaLines[game][prop]:
								bv = bovadaLines[game][prop][handicap]
								if " " in bv:
									if float(bv.split(" ")[0]) == float(propHandicap):
										bv = bv.split(" ")[-1]
									else:
										bv = ""
						elif float(handicap) == float(bovadaLines[game][prop].split(" ")[0]):
							bv = bovadaLines[game][prop].split(" ")[-1]
					else:
						bv = bovadaLines[game][prop]

				pb = ""
				if game in pbLines and prop in pbLines[game]:
					if handicap:
						if type(pbLines[game][prop]) is dict:
							if handicap in pbLines[game][prop]:
								pb = pbLines[game][prop][handicap]
								if " " in pb:
									if float(pb.split(" ")[0]) == float(propHandicap):
										pb = pb.split(" ")[-1]
									else:
										pb = ""
						elif float(handicap) == float(pbLines[game][prop].split(" ")[0]):
							pb = pbLines[game][prop].split(" ")[-1]
					else:
						fd = fdLines[game][prop]

				fd = ""
				if game in fdLines and prop in fdLines[game]:
					if handicap:
						if type(fdLines[game][prop]) is dict:
							if handicap in fdLines[game][prop]:
								fd = fdLines[game][prop][handicap]
								if " " in fd:
									if float(fd.split(" ")[0]) == float(propHandicap):
										fd = fd.split(" ")[-1]
									else:
										fd = ""
						elif float(handicap) == float(fdLines[game][prop].split(" ")[0]):
							fd = fdLines[game][prop].split(" ")[-1]
					else:
						fd = fdLines[game][prop]

				for i in range(2):
					if "/" not in dk:
						continue
					line = dk.split("/")[i]
					l = [dk, fd, bv, mgm, pn, pb]
					books = ["dk", "fd", "bv", "mgm", "pn", "pb"]
					evBook = ""
					if bookArg:
						if bookArg not in books:
							continue
						evBook = bookArg
						idx = books.index(bookArg)
						maxOU = l[idx]
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

						maxOdds = max(maxOdds)
						maxOU = ""
						for odds, book in zip(l, books):
							try:
								if odds.split("/")[i] == str(maxOdds):
									evBook = book
									maxOU = odds
									break
							except:
								pass

						line = maxOdds

					l.remove(maxOU)
					l.extend([bet365, kambi])

					avgOver = []
					avgUnder = []

					#print(game, prop, key, l)
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

					if ou == "-/-":
						continue

					if not line:
						continue

					line = convertAmericanOdds(1 + (convertDecOdds(int(line)) - 1) * boost)
					
					player = f"{game} {handicap} {prop} {'over' if i == 0 else 'under'}"
					if player in evData:
						continue
					if True:
						pass
						devig(evData, player, ou, int(line), prop=prop)
						#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
						if player not in evData:
							print(player)
							continue
						if float(evData[player]["ev"]) > 0:
							print(evData[player]["ev"], player, prop, game, int(line), ou, evBook)
						evData[player]["game"] = game
						evData[player]["book"] = evBook
						evData[player]["ou"] = ou
						evData[player]["under"] = i == 1
						evData[player]["odds"] = l
						evData[player]["line"] = line
						evData[player]["fanduel"] = str(fd).split(" ")[-1]
						evData[player]["dk"] = dk
						evData[player]["value"] = str(handicap)+" "+str(propHandicap)

	with open(f"{prefix}static/fiba/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def sortEV():
	with open(f"{prefix}static/fiba/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		data.append((d["ev"], player, d["value"], d["line"], d["book"], d["odds"]))

	for row in sorted(data):
		print(row)


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

	if args.fd:
		writeFanduel()

	if args.mgm:
		writeMGM()

	if args.pb:
		writePointsbet()

	if args.dk:
		writeDK(args.date)

	if args.kambi:
		writeKambi()

	if args.pn:
		writePinnacle(args.date)

	if args.bv:
		writeBV()

	if args.update:
		writeFanduel()
		writeDK(args.date)
		writePinnacle(args.date)
		writeKambi()
		writeBV()
		writeMGM()
		writePointsbet()

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, boost=args.boost, teamArg=args.team)

	if args.print:
		sortEV()

	if args.player:
		with open(f"{prefix}static/fiba/draftkings.json") as fh:
			dkLines = json.load(fh)

		with open(f"{prefix}static/fiba/bet365.json") as fh:
			bet365Lines = json.load(fh)

		with open(f"{prefix}static/fiba/fanduelLines.json") as fh:
			fdLines = json.load(fh)

		with open(f"{prefix}static/fiba/bovada.json") as fh:
			bvLines = json.load(fh)

		with open(f"{prefix}static/fiba/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"{prefix}static/fiba/mgm.json") as fh:
			mgmLines = json.load(fh)

		with open(f"{prefix}static/fiba/pinnacle.json") as fh:
			pnLines = json.load(fh)
	
		player = args.player

		for game in dkLines:
			for prop in dkLines[game]:
				if args.prop and args.prop != prop:
					continue

				if player not in dkLines[game][prop]:
					continue

				dk = dkLines[game][prop][player]
				fd = bet365 = kambi = bv = mgm = pn = ""
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
				try:
					mgm = mgmLines[game][prop][player]
				except:
					pass

				print(f"{prop} fd='{fd}'\ndk='{dk}'\n365='{bet365}'\nkambi='{kambi}'\nbv='{bv}'\npn={pn}\nmgm={mgm}")

	