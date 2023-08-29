
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

def writeBovada():
	url = "https://www.bovada.lv/sports/tennis/"

	ids = []
	for gender in ["men", "women"]:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description/tennis/us-open/{gender}-s-singles?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
		outfile = f"outBV"

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
		game = f"{comp[0]['name'].lower()} @ {comp[1]['name'].lower()}"

		player1 = comp[0]['name'].lower()
		player2 = comp[1]['name'].lower()
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
	outfile = f"out.json"

	for gender in ["", "_women"]:
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

				if label in ["ml", "set1_ml", "set2_ml", "set_spread", "total_sets", "set1_spread"]:
					data[game][label] = ""
					if "ml" not in label:
						line = betOffer["outcomes"][0]["line"] / 1000
						data[game][label] = f"{line} "

					data[game][label] += betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				elif label in ["spread", "total"]:
					if label not in data[game]:
						data[game][label] = {}
					line = betOffer["outcomes"][0]["line"] / 1000
					line2 = betOffer["outcomes"][1]["line"] / 1000
					data[game][label][line] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				else:
					#print(game, url, label)
					data[game][label] = {}
					for outcome in betOffer["outcomes"]:
						key = f"{player1} {outcome['label']}"
						if int(outcome['awayScore']) > int(outcome['homeScore']):
							key = f"{player2} {outcome['awayScore']}-{outcome['homeScore']}"
						data[game][label][key] = outcome["oddsAmerican"]

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
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	mens = [
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/to-etcheverry-v-ot-virtanen-32590426",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/y-wu-v-lajovic-32584250",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/wawrinka-v-nishioka-32584224",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/nic-moreno-de-alboran-v-sonego-32590412",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/huesler-v-hurkacz-32584171",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/daniel-v-monfils-32590440",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/l-harris-v-pella-32584427",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/hanfmann-v-sinner-32584274",
  "https://mi.sportsbook.fanduel.com/tennis/men's-us-open-2023/carlos-alcaraz-v-koepfer-32584468",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/vickery-v-vekic-32590313",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/a-bogdan-v-kenin-32584154",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/pavlyuchenkova-v-crawley-32590318",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/strycova-v-k-kanepi-32584245",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/blinkova-v-burrage-32584506",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/q-zheng-v-podoroska-32583943",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/minnen-v-v-williams-32590257",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/l-bronzetti-v-b-krejcikova-32584016",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/ro-montgomery-v-e-lys-32590323",
  "https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/zanevska-v-a-sabalenka-32584195",
  "https://mi.sportsbook.fanduel.com/tennis/itf-thailand-futures/y-kawahashi-v-i-eqbal-32597142",
  "https://mi.sportsbook.fanduel.com/tennis/itf-thailand-futures/n-kunsuwan-v-s-banthia-32597143"
]

	url = "https://mi.sportsbook.fanduel.com/navigation/us-open?tab=women%27s-matches"

	womens = []
	games = []
	games.extend(mens)
	games.extend(womens)

	lines = {}
	#games = ["https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/strycova-v-k-kanepi-32584245"]
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		if game in lines:
			continue

		outfile = "out"

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

					if prop in ["ml", "set1_ml", "set2_ml", "total_sets", "set1_spread", "6-0", "both", "away_1_set", "home_1_set", "away_total", "home_total"]:
						lines[game][prop] = ""

						for idx, runner in enumerate(runners):
							if idx == 0 and prop in ["total", "total_sets", "set1_spread", "away_total", "home_total"]:
								lines[game][prop] = runner["runnerName"].split(" ")[-1].replace("(", "").replace(")", "")+" "
							elif idx == 1:
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
					elif prop in ["total", "set1_total", "set2_total", "spread", "set_spread"]:
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
	for gender in [72778, 72779]:
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

								if label in ["ml", "set1_ml", "set2_ml", "spread", "total", "total_sets", "6-0", "away_total", "home_total"]:
									lines[game][label] = ""

									if "ml" not in label and label not in ["6-0"]:
										lines[game][label] = f"{row['outcomes'][0]['line']} "
									
									lines[game][label] += f"{row['outcomes'][0]['oddsAmerican']}"
									if len(row['outcomes']) != 1:
										lines[game][label] += f"/{row['outcomes'][1]['oddsAmerican']}"
								elif label in ["set_spread", "set1_total", "set2_total"]:
									if label not in lines[game]:
										lines[game][label] = {}

									outcomes = row["outcomes"]
									for i in range(0, len(outcomes), 2):
										line = str(outcomes[i]["line"])
										lines[game][label][line] = f"{outcomes[i]['oddsAmerican']}/{outcomes[i+1]['oddsAmerican']}"
								elif label in ["set"]:
									lines[game][label] = {}

									for outcome in row["outcomes"]:
										lines[game][label][f"{outcome['participant'].lower()} {outcome['label'].replace(':', '-')}"] = outcome['oddsAmerican']

	with open("static/tennis/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def write365Props():
	url = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B18/C20902960/D43/E181378/F43/"

	js = """

	const data = {};

	{
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
		let prop = title;

		if (prop === "set betting") {
			prop = "set";
		} else if (prop == "total sets") {
			prop = "total_sets";
		} else if (prop == "1st set total games") {
			prop = "set1_total";
		} else if (prop == "player games won") {
			prop = "away_total";
		}

		for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
			const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" vs ", " @ ").replaceAll(".", "");
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
		console.log(data)
	}
	"""
	pass

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B13/C20904590/D7/E83/F4/"

	js = """
	
	const data = {};

	{
		const main = document.querySelector(".gl-MarketGroupContainer");
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
		} else {
			prop = "ml";
		}

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
			const game = away+" @ "+home;
			games.push(game);

			if (data[game] === undefined) {
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

		console.log(data);

	}

	"""
	pass

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None):
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
		team1, team2 = map(str, game.split(" @ "))
		switchGame = f"{team2} @ {team1}"
		for prop in fdLines[game]:

			if propArg and prop != propArg:
				continue

			if prop in ["set"]:
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

				if game == "barbora strycova @ kaia kanepi" and prop == "set1_total":
					print(handicap, fd)

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

					line = fd.split("/")[i]
					l = [dk, bv, bet365, kambi]

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

					if ou == "-/-" or ou.endswith("/-") or ou.startswith("-/"):
						continue

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

	args = parser.parse_args()

	plays = [("trea turner", 430, "phi"), ("christian bethancourt", 800, "tb"), ("randy arozarena", 500, "tb"), ("aaron judge", 235, "nyy"), ("jorge soler", 480, "mia"), ("jack suwinski", 540, "pit"), ("mark vientos", 680, "nym")]

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

	if args.dk:
		writeDK(args.date)

	if args.kambi:
		writeKambi()

	if args.bv:
		writeBovada()

	if args.text:
		sendText("test")

	if args.update:
		writeFanduel()
		writeDK(args.date)
		writeBovada()
		writeKambi()

	if args.ml:
		writeActionNetworkML()

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, boost=args.boost)

	if args.bpp:
		writeBPPHomers()

	if args.action:
		writeActionNetwork(args.date)

	if args.print:
		sortEV()

	if args.prop:
		#writeEV(dinger=dinger, date=args.date, avg=True, allArg=args.all, gameArg=args.game, teamArg=args.team, prop=args.prop, under=args.under, nocz=args.nocz, nobr=args.nobr, no365=args.no365, boost=args.boost, bookArg=args.book)
		sortEV()
	#write365()
	#writeActionNetwork()

	