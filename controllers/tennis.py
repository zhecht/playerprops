
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

def writePinnacle(date):
	if not date:
		date = str(datetime.now())[:10]

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/sports/33/markets/straight?primaryOnly=false&withSpecials=false" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o outPN'

	os.system(url)
	outfile = f"outPN"
	with open(outfile) as fh:
		data = json.load(fh)

	ids = []
	for row in data:
		if str(datetime.strptime(row["cutoffAt"][:-6].split(".")[0], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=4))[:10] != date:
			continue
		if row["matchupId"] not in ids:
			ids.append(row["matchupId"])

	res = {}
	for bid in ids:
		url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o outPN'

		time.sleep(0.3)
		os.system(url)
		with open(outfile) as fh:
			related = json.load(fh)

		url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o outPN'

		time.sleep(0.3)
		os.system(url)
		with open(outfile) as fh:
			data = json.load(fh)

		try:
			gamesMatchup = related[0]["id"] if related[0]["units"] == "Games" else related[1]["id"]
		except:
			gamesMatchup = ""
		try:
			player1 = related[0]["participants"][0]["name"].lower()
			player2 = related[0]["participants"][1]["name"].lower()
			if " / " in player1:
				player1 = player1.split(" / ")[0].split(" ")[0] + " / " + player1.split(" / ")[-1].split(" ")[0] 
				player2 = player2.split(" / ")[0].split(" ")[0] + " / " + player2.split(" / ")[-1].split(" ")[0] 
		except:
			continue

		game = strip_accents(f"{player1} @ {player2}")

		if game in res:
			continue
		res[game] = {}

		for row in data:
			prop = row["type"]
			keys = row["key"].split(";")

			prefix = ""
			if keys[1] == "1":
				prefix = "set1_"

			if prop == "moneyline":
				prop = f"{prefix}ml"
			elif prop == "spread":
				prop = f"{prefix}spread"
				if gamesMatchup != row["matchupId"] and not prefix:
					prop = f"set_spread"
			elif prop == "total":
				prop = f"{prefix}total"
				if gamesMatchup != row["matchupId"] and not prefix:
					prop = f"total_sets"
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

	with open("static/tennis/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)


def writeMGM():

	res = {}

	tourneys = {
		"mens": {
			"virtual": 6,
			"real": 4628
		},
		"womens": {
			"virtual": 7,
			"real": 4630
		},
		"mens doubles": {
			"virtual": 8,
			"real": 6622
		},
		"womens": {
			"virtual": 9,
			"real": 6625
		},
		"mixed": {
			"virtual": 10,
			"real": 6688
		}
	}

	for tourney in tourneys:
		url = f"https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=5&tournamentId=5&virtualCompetitionId=2&virtualCompetitionGroupId={tourneys[tourney]['virtual']}&realCompetitionId={tourneys[tourney]['real']}&widgetId=/mobilesports-v1.0/layout/layout_standards/modules/competition/defaultcontainer&shouldIncludePayload=true"
		outfile = f"outMGM"

		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			rows = data["widgets"][0]["payload"]["items"][0]["activeChildren"][0]["payload"]["fixtures"]
		except:
			print(tourney)
			continue
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
			game = strip_accents(data["name"]["value"].lower())

			p1, p2 = map(str, game.split(" - "))
			p1 = p1.split(" (")[0]
			p2 = p2.split(" (")[0]

			if "/" in game:
				p1 = p1.split("/")[0].split(" ")[-1]+" / "+p1.split("/")[-1].split(" ")[-1]
				p2 = p2.split("/")[0].split(" ")[-1]+" / "+p2.split("/")[-1].split(" ")[-1]
			game = f"{p1} @ {p2}"

			res[game] = {}
			for row in data["games"]:
				prop = row["name"]["value"].lower()

				if prop == "match winner":
					prop = "ml"
				elif prop == "set 1 winner":
					prop = "set1_ml"
				elif prop == "set 2 winner":
					prop = "set2_ml"
				elif prop == "set betting":
					prop = "set"
				elif prop == "total games - set 1":
					prop = "set1_total"
				elif prop == "total games - match":
					prop = "total"
				elif "at least 1" in prop:
					p = "away_1_set"
					if "player 2" in prop:
						p = "home_1_set"
					prop = p
				elif "set spread" in prop:
					prop = "set_spread"
				elif "player spread" in prop:
					prop = "spread"
				else:
					continue

				results = row['results']
				ou = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
				if "ml" in prop or prop in ["away_1_set", "home_1_set"]:
					res[game][prop] = ou
				elif len(results) >= 2:
					if prop not in res[game]:
						res[game][prop] = {}

					skip = 1 if prop == "set" else 2
					for idx in range(0, len(results), skip):
						val = results[idx]["name"]["value"].lower()
						if "over" not in val and "under" not in val and prop not in ["set_spread", "player_spread"]:
							continue
						else:
							val = val.split(" ")[-1]
						ou = str(results[idx]["americanOdds"])
						if prop != "set":
							ou = f"{results[idx]['americanOdds']}/{results[idx+1]['americanOdds']}"
						res[game][prop][val] = ou

	with open("static/tennis/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBovada():
	url = "https://www.bovada.lv/sports/tennis/"

	ids = []
	for gender in ["men", "women"]:
		for which in ["singles", "doubles"]:
			url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description/tennis/us-open/{gender}-s-{which}?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
			outfile = f"outBV"

			time.sleep(0.3)
			os.system(f"curl -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			ids.extend([r["link"] for r in data[0]["events"]])

	res = {}
	#print(ids)
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		comp = data[0]['events'][0]['competitors']
		player1 = comp[0]['name'].lower()
		player2 = comp[1]['name'].lower()
		if "/" in player1:
			player1 = f"{player1.split(' / ')[0].split(' ')[-2]} / {player1.split(' / ')[1].split(' ')[-2]}"
			player2 = f"{player2.split(' / ')[0].split(' ')[-2]} / {player2.split(' / ')[1].split(' ')[-2]}"
		game = f"{player1} @ {player2}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "game spreads/totals", "match props", "set props"]:
				for market in row["markets"]:
					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "total" or prop == "alternate total games":
						prop = "total"
					elif prop == "game spread" or prop == "alternate game spread":
						prop = "spread"
					elif prop == "total sets":
						prop = "total_sets"
					elif prop == f"total games o/u - {player1}":
						prop = "away_total"
					elif prop == f"total games o/u - {player2}":
						prop = "home_total"
					elif prop == "any set to nil":
						prop = "6-0"
					else:
						continue

					if market["period"]["description"].lower() == "1st set":
						prop = f"set1_{prop}"
					elif market["period"]["description"].lower() == "2nd set":
						prop = f"set2_{prop}"

					if not len(market["outcomes"]):
						continue

					if "ml" in prop or prop == "6-0":
						res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
					elif "spread" in prop or prop in ["total", "set1_total", "set2_total", "away_total", "home_total"]:
						if prop not in res[game]:
							res[game][prop] = {}

						outcomes = market["outcomes"]
						for idx in range(0, len(outcomes), 2):
							handicap = outcomes[idx]["price"]["handicap"]
							res[game][prop][handicap] = f"{market['outcomes'][idx]['price']['american']}/{market['outcomes'][idx+1]['price']['american']}".replace("EVEN", "100")
					else:
						handicap = market["outcomes"][0]["price"]["handicap"]
						res[game][prop] = f"{handicap} {market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")

	with open("static/tennis/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi():
	data = {}
	outfile = f"tennisout.json"

	for gender in ["", "_doubles", "_women", "_women_doubles"]:
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/tennis/grand_slam/us_open{gender}/all/matches.json?lang=en_US&market=US"
		os.system(f"curl -k \"{url}\" -o {outfile}")
		
		with open(outfile) as fh:
			j = json.load(fh)

		eventIds = {}
		for event in j["events"]:
			game = event["event"]["name"].lower()
			player1, player2 = map(str, game.split(f" {event['event']['nameDelimiter']} "))
			game = []
			for player in [player1, player2]:
				if "/" in player:
					p1,p2 = map(str, player.split("/"))
					game.append(f"{p1.split(', ')[0]} / {p2.split(', ')[0]}")
				else:
					game.append(f"{player.split(', ')[-1]} {player.split(', ')[0]}")
			game = strip_accents(" @ ".join(game))
			if game in eventIds:
				continue

			if event["event"]["state"] == "STARTED":
				continue
			eventIds[game] = event["event"]["id"]
			data[game] = {}

		for game in eventIds:
			eventId = eventIds[game]
			teamIds = {}

			player1, player2 = map(str, game.split(" @ "))
			
			time.sleep(0.3)
			url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
			os.system(f"curl -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				j = json.load(fh)

			i = 0
			for betOffer in j["betOffers"]:
				label = betOffer["criterion"]["label"].lower()
				if label == "set betting":
					label = "set"
				elif label == "match odds":
					label = "ml"
				elif label == "set handicap":
					label = "set_spread"
				elif label == "set 1":
					label = "set1_ml"
				elif label == "set 2":
					label = "set2_ml"
				elif label == "game handicap":
					label = "spread"
				elif label == "game handicap - set 1":
					label = "set1_spread"
				elif label == "total games":
					label = "total"
				elif label == "total sets":
					label = "total_sets"
				else:
					continue

				ou = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				if "ml" in label:
					data[game][label] = ou
				elif label == "set":
					#print(game, url, label)
					data[game][label] = {}
					for outcome in betOffer["outcomes"]:
						key = f"{player1} {outcome['label']}"
						if int(outcome['awayScore']) > int(outcome['homeScore']):
							key = f"{player2} {outcome['awayScore']}-{outcome['homeScore']}"
						data[game][label][key] = outcome["oddsAmerican"]
				else:
					if label not in data[game]:
						data[game][label] = {}
					line = betOffer["outcomes"][0]["line"] / 1000
					data[game][label][line] = ou

		with open(f"{prefix}static/tennis/kambi.json", "w") as fh:
			json.dump(data, fh, indent=4)

def writeFanduel():
	url = "https://mi.sportsbook.fanduel.com/navigation/us-open?tab=men%27s-matches"

	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/tennis/") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && time.innerText.split(" ").length < 3) {
				//if (time && time.innerText.split(" ")[0] === "TUE") {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	mens = [
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/nys-zielinski-v-dodig-krajicek-32611369",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/fritz-v-djokovic-32609445",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/lammons-withrow-v-bopanna-ebden-32611457",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/tiafoe-v-be-shelton-32609209",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/linette-pera-v-brady-stefani-32611125",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/dabrowski-routliffe-v-fernandez-townsend-32611324",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/s-cirstea-v-muchova-32609025"
]

	url = "https://mi.sportsbook.fanduel.com/navigation/us-open?tab=women%27s-matches"

	womens = []
	games = []
	games.extend(mens)
	games.extend(womens)

	lines = {}
	#games = ["https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/boulter-putintseva-v-wu-zhu-32592168"]
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		if game in lines:
			continue

		outfile = "tennisout"

		for tab in ["", "total-games-props", "alternatives"]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue
				
			# find name
			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				if marketName == "moneyline":
					player1 = data["attachments"]["markets"][market]["runners"][0]["runnerName"].lower()
					player2 = data["attachments"]["markets"][market]["runners"][1]["runnerName"].lower()
					game = f"{player1} @ {player2}"
					if game not in lines:
						lines[game] = {}

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				runners = data["attachments"]["markets"][market]["runners"]

				if marketName in ["moneyline", "alternative game spread", "game spread", "alternative set spread", "6-0 set in match", "set betting", "to win 1st set", "set 2 winner"] or marketName.startswith("total match games") or "total sets" in marketName or "set 1 game handicap" in marketName or marketName.startswith("both") or marketName.startswith("player a") or marketName.startswith("player b") or "total games" in marketName:
					prop = ""
					if marketName == "moneyline":
						prop = "ml"
					elif marketName == "game spread" or marketName == "alternative game spread":
						prop = "spread"
					elif marketName == "alternative set spread":
						prop = "set_spread"
					elif "total match" in marketName:
						prop = "total"
					elif "total sets" in marketName:
						prop = "total_sets"
					elif marketName == "to win 1st set":
						prop = "set1_ml"
					elif marketName == "set 2 winner":
						prop = "set2_ml"
					elif "set 1 game handicap" in marketName:
						prop = "set1_spread"
					elif "6-0" in marketName:
						prop = "6-0"
					elif "both" in marketName:
						prop = "both"
					elif marketName == "set betting":
						prop = "set"
					elif marketName.startswith("player a") or marketName.startswith("player b"):
						prop = "away" if marketName.split(" ")[1] == "a" else "home"
						if "at least one set" in marketName:
							prop += "_1_set"
						elif "total games" in marketName:
							prop += "_total"
						else:
							continue
					elif "total games" in marketName and "3 way" not in marketName:
						prop = "total"
						if marketName.startswith("set 1"):
							prop = "set1_total"
						elif marketName.startswith("set 2"):
							prop = "set2_total"
					else:
						continue

					if prop in ["ml", "set1_ml", "set2_ml", "6-0", "both", "away_1_set", "home_1_set"]:
						lines[game][prop] = ""

						for idx, runner in enumerate(runners):
							if idx == 1:
								lines[game][prop] += "/"
							try:
								lines[game][prop] += str(runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							except:
								print(url, game, prop)
								continue
					elif prop == "set":
						lines[game][prop] = {}

						for idx, runner in enumerate(runners):
							lines[game][prop][runner["runnerName"].lower()] = str(runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					else:
						if prop not in lines[game]:
							lines[game][prop] = {}

						handicap = runners[0]["runnerName"].split(" ")[-1].replace("(", "").replace(")", "")
						try:
							lines[game][prop][handicap] = str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
						except:
							print(url, game, prop)
							continue
	
	with open(f"{prefix}static/tennis/fanduelLines.json", "w") as fh:
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

def writeDK(date):
	url = "https://sportsbook.draftkings.com/leagues/tennis/us-open-men"

	url = "https://sportsbook.draftkings.com/leagues/tennis/us-open-women"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 488,
		"sets": 534,
		"player props": 633
	}

	subCats = {
		488: [6364, 10818, 6365],
		534: [12169, 12170, 11127, 6367, 9535, 5369, 4816],
		633: [0]
	}

	lines = {}
	for gender in [72778, 72779, 101899, 101901]:
		for mainCat in mainCats:
			for subCat in subCats[mainCats[mainCat]]:
				time.sleep(0.3)
				url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/{gender}/categories/{mainCats[mainCat]}"
				if subCat:
					url += f"/subcategories/{subCat}"
				url += "?format=json"
				outfile = "outtennis"
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
					player1, player2 = map(str, game.split(" @ "))
					if "/" in player1:
						game = f"{player1.split(' / ')[0].split(' ')[-1]} / {player1.split(' / ')[1].split(' ')[-1]} @ {player2.split(' / ')[0].split(' ')[-1]} / {player2.split(' / ')[1].split(' ')[-1]}"
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
								label = row["label"].lower().split(" [")[0]

								if label == "moneyline":
									label = "ml"
								elif label == "spread games":
									label = "spread"
								elif label == "set spread":
									label = "set_spread"
								elif "player total games" in label:
									if game.startswith(label.split(":")[0]):
										label = "away_total"
									else:
										label = "home_total"
								elif label.startswith("total games"):
									if "1st set" in label:
										label = "set1_total"
									elif "2nd set" in label:
										label = "set2_total"
									else:
										label = "total"
								elif label == "total sets":
									label = "total_sets"
								elif label == "1st set":
									label = "set1_ml"
								elif label == "2nd set":
									label = "set2_ml"
								elif label == "correct score":
									label = "set"

								if "6:0" in label:
									label = "6-0"

								if "ml" in label or label == "6-0":
									if len(row['outcomes']) == 0:
										continue
									lines[game][label] = f"{row['outcomes'][0]['oddsAmerican']}"
									if len(row['outcomes']) != 1:
										lines[game][label] += f"/{row['outcomes'][1]['oddsAmerican']}"
								elif label in ["set"]:
									lines[game][label] = {}

									for outcome in row["outcomes"]:
										lines[game][label][f"{outcome['participant'].lower()} {outcome['label'].replace(':', '-')}"] = outcome['oddsAmerican']
								else:
									if label not in lines[game]:
										lines[game][label] = {}

									outcomes = row["outcomes"]
									for i in range(0, len(outcomes), 2):
										line = str(outcomes[i]["line"])
										try:
											lines[game][label][line] = f"{outcomes[i]['oddsAmerican']}/{outcomes[i+1]['oddsAmerican']}"
										except:
											continue
								

	with open("static/tennis/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B13/C20904590/D7/E83/F4/"

	js = """
	
	const data = {};

	// All Main other than, Set: set1_spread, Games: away_total

	{
		const main = document.querySelectorAll(".gl-MarketGroupContainer")[0];
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
		let prop = title.replace("moneyline", "ml");

		if (prop == "spread - games won") {
			prop = "spread";
		} else if (prop === "total games") {
			prop = "total";
		} else if (prop == "first set money line") {
			prop = "set1_ml";
		} else if (prop == "first set spread") {
			prop = "set1_spread";
		} else if (prop === "set betting") {
			prop = "set";
		} else if (prop == "total sets") {
			prop = "total_sets";
		} else if (prop == "1st set total games") {
			prop = "set1_total";
		} else if (prop == "player games won") {
			prop = "away_total";
		} else {
			prop = "ml";
		}

		if (["set", "total_sets", "set1_total", "away_total"].indexOf(prop) >= 0) {
			for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
				const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" vs ", " @ ").replaceAll(".", "").replace("/", " / ");

				if (data[game] === undefined) {
					data[game] = {};
				}

				if (div.classList.contains("src-FixtureSubGroup_Closed")) {
					div.click();
				}

				if (prop == "away_total") {
					let ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[0].innerText.replace("Over ", "");
					
					data[game]["away_total"] = ou+" "+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[0].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[1].innerText;

					ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[2].innerText.replace("Over ", "");
					data[game]["home_total"] = ou+" "+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[2].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[3].innerText;
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
							let player = game.split(" @ ")[0];
							if (idx >= arr.length) {
								player = game.split(" @ ")[1];
							}
							
							data[game][prop][player+" "+set] = odds;
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
					break;
				}
				const away = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[0].innerText.toLowerCase().replaceAll(".", "");
				const home = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[1].innerText.toLowerCase().replaceAll(".", "");
				const game = (away+" @ "+home).replaceAll("/", " / ");
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
					data[game][prop] = line+" "+odds;
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
					data[game][prop] += "/"+odds;
				}
				idx += 1;
			}
		}
		console.log(data);
	}

	"""
	pass

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None, singles=None, doubles=None):
	if not boost:
		boost = 1

	with open(f"{prefix}static/tennis/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/tennis/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/tennis/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/tennis/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/tennis/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/tennis/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/tennis/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/tennis/ev.json") as fh:
		evData = json.load(fh)

	if not teamArg:
		evData = {}
	elif teamArg:
		for player in evData.copy():
			if teamArg in evData[player]["game"]:
				del evData[player]

	for game in fdLines:
		if teamArg and teamArg not in game:
			continue

		if singles and "/" in game:
			continue
		if doubles and "/" not in game:
			continue
		team1, team2 = map(str, game.split(" @ "))
		for prop in fdLines[game]:

			if prop == "set":
				continue

			if propArg and prop != propArg:
				continue

			if type(fdLines[game][prop]) is dict:
				arr = fdLines[game][prop]
			else:
				arr = [None]

			for key in arr:
				fd = fdLines[game][prop]
				handicap = 0
				if " " in fd:
					handicap = str(float(fd.split(" ")[0]))

				if key:
					fd = fdLines[game][prop][key]
					handicap = key

				fd = fd.split(" ")[-1]

				kambi = ""
				if game in kambiLines and prop in kambiLines[game]:
					if handicap:
						if " " in kambiLines[game][prop]:
							if str(handicap) == float(kambiLines[game][prop].split(" ")[0]):
								kambi = kambiLines[game][prop].split(" ")[-1]
						elif handicap in kambiLines[game][prop]:
							kambi = kambiLines[game][prop][handicap]

					elif prop in ["set"]:
						kambi = kambiLines[game][prop][handicap]
					else:
						kambi = kambiLines[game][prop]

				bv = ""
				if game in bvLines and prop in bvLines[game]:
					if handicap:
						if type(bvLines[game][prop]) is dict:
							if handicap in bvLines[game][prop]:
								bv = bvLines[game][prop][handicap]
						elif float(handicap) == float(bvLines[game][prop].split(" ")[0]):
							bv = bvLines[game][prop].split(" ")[-1]
					else:
						bv = bvLines[game][prop]

				mgm = ""
				if game in mgmLines and prop in mgmLines[game]:
					if handicap:
						if type(mgmLines[game][prop]) is dict:
							if handicap in mgmLines[game][prop]:
								mgm = mgmLines[game][prop][handicap]
						elif float(handicap) == float(mgmLines[game][prop].split(" ")[0]):
							mgm = mgmLines[game][prop].split(" ")[-1]
					else:
						mgm = mgmLines[game][prop]

				pn = ""
				if game in pnLines and prop in pnLines[game]:
					if handicap:
						if type(pnLines[game][prop]) is dict:
							if handicap in pnLines[game][prop]:
								pn = pnLines[game][prop][handicap]
						elif float(handicap) == float(pnLines[game][prop].split(" ")[0]):
							pn = pnLines[game][prop].split(" ")[-1]
					else:
						pn = pnLines[game][prop]

				bet365 = ""
				if game in bet365Lines and prop in bet365Lines[game]:
					if handicap:
						if type(bet365Lines[game][prop]) is dict:
							if handicap in bet365Lines[game][prop]:
								bet365 = bet365Lines[game][prop][handicap]
						elif float(handicap) == float(bet365Lines[game][prop].split(" ")[0]):
							bet365 = bet365Lines[game][prop].split(" ")[-1]
					else:
						bet365 = bet365Lines[game][prop]

				dk = ""
				if game in dkLines and prop in dkLines[game]:
					if handicap:
						if type(dkLines[game][prop]) is dict:
							if handicap in dkLines[game][prop]:
								dk = dkLines[game][prop][handicap]
						elif float(handicap) == float(dkLines[game][prop].split(" ")[0]):
							dk = dkLines[game][prop].split(" ")[-1]
					else:
						dk = dkLines[game][prop]


				for i in range(2):

					if "/" not in fd and i == 1:
						continue

					line = fd.split("/")[i]
					l = [dk, bv, mgm, pn, bet365, kambi]

					avgOver = []
					avgUnder = []

					evBook = "fd"
					try:
						if bookArg == "dk" or (bookArg != "fd" and dk and int(dk.split("/")[i]) > int(line)):
							evBook = "dk"
							line = dk.split("/")[i]
							l[0] = str(fd)
					except:
						if bookArg == "dk":
							continue
						pass

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

					line = convertAmericanOdds(1 + (convertDecOdds(int(line)) - 1) * boost)
					player = f"{game} {prop} {handicap} {'over' if i == 0 else 'under'}"
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
							print(evData[player]["ev"], game, prop, handicap, int(line), ou, evBook, "\n\t", l)
						evData[player]["game"] = game
						evData[player]["book"] = evBook
						evData[player]["ou"] = ou
						evData[player]["under"] = i == 1
						evData[player]["odds"] = l
						evData[player]["line"] = line
						evData[player]["fanduel"] = str(fd).split(" ")[-1]
						evData[player]["dk"] = dk
						evData[player]["value"] = str(handicap)

	with open(f"{prefix}static/tennis/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)


def writeBoostTMP():

	with open("passing_boost.json") as fh:
		boost = json.load(fh)

	ev = {}
	for player in boost:
	#for player in ["patrick mahomes"]:
		for prop in ["pass_yd", "pass_td", "int"]:
			if prop not in boost[player]["fanduel"]:
				continue
			overs = []
			fdBoost = boost[player]["fanduel"][prop] * 1.25

			for book in ["bet365", "draftkings", "mgm", "kambi", "caesars"]:
				if book not in boost[player] or prop not in boost[player][book]:
					continue
				overs.append(int(boost[player][book][prop]))

			ou = f"AVG({','.join([str(x) for x in overs])})"
			playerProp = player+"_"+prop
			devigger(ev, player=playerProp, bet365Odds=ou, finalOdds=int(fdBoost))
			if playerProp not in ev:
				continue
			ev[playerProp]["prop"] = prop
			ev[playerProp]["overs"] = overs
			ev[playerProp]["fd"] = boost[player]["fanduel"][prop]

	with open("static/tennis/passing_boost.json", "w") as fh:
		json.dump(ev, fh, indent=4)


def sortEV():

	with open(f"{prefix}static/tennis/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/tennis/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for game in evData:
		d = evData[game]
		data.append((d["ev"], game, d["line"], d["book"], d["odds"]))

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
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--player", help="Player")

	args = parser.parse_args()

	if args.fd:
		writeFanduel()

	if args.dk:
		writeDK(args.date)

	if args.kambi:
		writeKambi()

	if args.bv:
		writeBovada()

	if args.mgm:
		writeMGM()

	if args.pn:
		writePinnacle(args.date)

	if args.update:
		writeFanduel()
		writeDK(args.date)
		writeBovada()
		writeKambi()
		writeMGM()
		writePinnacle(args.date)

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, boost=args.boost, doubles=args.doubles, singles=args.singles)

	if args.print:
		sortEV()

	if args.prop:
		#writeEV(dinger=dinger, date=args.date, avg=True, allArg=args.all, gameArg=args.game, teamArg=args.team, prop=args.prop, under=args.under, nocz=args.nocz, nobr=args.nobr, no365=args.no365, boost=args.boost, bookArg=args.book)
		#sortEV()
		pass

	if args.player:
		with open(f"{prefix}static/tennis/draftkings.json") as fh:
			dkLines = json.load(fh)

		with open(f"{prefix}static/tennis/bet365.json") as fh:
			bet365Lines = json.load(fh)

		with open(f"{prefix}static/tennis/fanduelLines.json") as fh:
			fdLines = json.load(fh)

		with open(f"{prefix}static/tennis/bovada.json") as fh:
			bvLines = json.load(fh)

		with open(f"{prefix}static/tennis/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"{prefix}static/tennis/pinnacle.json") as fh:
			pnines = json.load(fh)

		with open(f"{prefix}static/tennis/mgm.json") as fh:
			mgmines = json.load(fh)
	
		player = args.player

		for game in fdLines:
			if player not in game:
				continue

			for prop in fdLines[game]:
				if args.prop and args.prop != prop:
					continue

				fd = fdLines[game][prop]

				handicap = type(fd) is dict
				dk = bet365 = kambi = bv = pn = mgm = ""

				try:
					dk = dkLines[game][prop]
				except:
					pass
				try:
					bet365 = bet365Lines[game][prop]
				except:
					pass
				try:
					kambi = kambiLines[game][prop]
				except:
					pass
				try:
					bv = bvLines[game][prop]
				except:
					pass
				try:
					pn = pnLines[game][prop]
				except:
					pass
				try:
					mgm = mgmLines[game][prop]
				except:
					pass

				print(f"{prop} fd='{fd}'\ndk='{dk}'\n365='{bet365}'\nkambi='{kambi}'\nbv='{bv}'\nmgm={mgm}\npn={pn}")