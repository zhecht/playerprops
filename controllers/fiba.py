
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


def writeKambi():
	data = {}
	outfile = f"out.json"
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
				label = "1st_half_spread"
			elif "handicap - 2nd half" in label:
				label = "2nd_half_spread"
			elif "total points - 1st half" in label:
				label = "1st_half_total"
			elif "total points - 2nd half" in label:
				label = "2nd_half_total"
			elif f"total points by {away} - 1st half" in label:
				label = "1st_half_away_total"
			elif f"total points by {home} - 1st half" in label:
				label = "1st_half_home_total"
			elif f"total points by {away} - including overtime" in label:
				label = "away_total"
			elif f"total points by {home} - including overtime" in label:
				label = "home_total"
			elif label == "including overtime":
				label = "ml"
			elif label == "draw no bet - 1st half":
				label = "1st_half_ml"
			elif label == "draw no bet - 2nd half":
				label = "2nd_half_ml"
			elif label.startswith("points scored"):
				label = "pts"
			elif label.startswith("rebounds"):
				label = "reb"
			elif label.startswith("assists"):
				label = "ast"
			elif label.startswith("3-point"):
				label = "3ptm"


			if label in ["ml", "1st_half_ml", "2nd_half_ml"]:
				team = betOffer["outcomes"][0]["label"].lower()
				if label != "ml":
					team = betOffer["outcomes"][0]["participant"].lower()
				if game.startswith(team):
					data[game][label] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				else:
					data[game][label] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label in ["1st_half_total", "2nd_half_total", "1st_half_away_total", "1st_half_home_total"]:
				line = betOffer["outcomes"][0]["line"] / 1000
				data[game][label] = str(line)+" "+betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
			elif label in ["spread", "1st_half_spread", "2nd_half_spread"]:
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
					last, first = map(str, player.split(", "))
					player = parsePlayer(f"{first} {last}")
					data[game][label][player] = str(line)+" "+betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]


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
				if (time && time.getAttribute("datetime").split("T")[0] === "2023-08-29") {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/germany-v-finland-32591218",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/angola-v-dominican-republic-32591220",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/egypt-v-mexico-32591226",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/lebanon-v-france-32591227",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/australia-v-japan-32591243",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/philippines-v-italy-32591235",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/montenegro-v-lithuania-32591236",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/canada-v-latvia-32591237"
]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		if game in lines:
			continue
		lines[game] = {}

		outfile = "out"

		for tab in ["", "player-points", "player-rebounds", "player-assists", "player-threes", "half"]:
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

				if marketName in ["moneyline", "total points", "spread"] or " - points" in marketName or " - rebounds" in marketName or " - assists" in marketName or " - made threes" in marketName or marketName.startswith("1st half"):
					prop = "ml"
					if marketName == "total points":
						prop = "total"
					elif marketName == "1st half total points":
						prop = "1st_half_total"
					elif marketName == "spread":
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
						prop = "1st_half_ml"
					elif marketName == "1st half spread":
						prop = "1st_half_spread"

					if prop in ["ml", "total", "spread", "1st_half_total", "1st_half_spread", "1st_half_ml"]:
						lines[game][prop] = ""

						for idx, runner in enumerate(runners):
							if idx == 0 and prop in ["total", "spread", "1st_half_total", "1st_half_spread"]:
								lines[game][prop] = f"{runner['handicap']} "
							elif idx == 1:
								lines[game][prop] += "/"	
							lines[game][prop] += str(runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					else:
						player = parsePlayer(marketName.split(" - ")[0])

						if prop not in lines[game]:
							lines[game][prop] = {}

						lines[game][prop][player] = ""

						for idx, runner in enumerate(runners):
							if idx == 0:
								lines[game][prop][player] = f"{runner['handicap']} "
							elif idx == 1:
								lines[game][prop][player] += "/"	
							lines[game][prop][player] += str(runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
	
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
		"halves": 520,
		"team props": 523
	}
	
	subCats = {
		520: [4598, 6230]
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
								label = "1st_half_spread"
							elif label == "total 1st half":
								label = "1st_half_total"
							elif label == "ml 1st half":
								label = "1st_half_ml"
							elif label.endswith("team total points - 1st half"):
								team = label.split(":")[0]
								if game.startswith(team):
									label = "1st_half_away_total"
								else:
									label = "1st_half_home_total"
							elif label.endswith("team total points"):
								team = label.split(":")[0]
								if game.startswith(team):
									label = "away_total"
								else:
									label = "home_total"

							if mainCat in ["pts", "reb", "ast"]:
								label = parsePlayer(label)
								if mainCat not in lines[game]:
									lines[game][mainCat] = {}
								lines[game][mainCat][label] = ""
							else:	
								lines[game][label] = ""

							if mainCat in ["pts", "reb", "ast"]:
								try:
									lines[game][mainCat][label] = f"{row['outcomes'][0]['line']} {row['outcomes'][0]['oddsAmerican']}/{row['outcomes'][1]['oddsAmerican']}"
								except:
									continue
							else:
								if "ml" not in label:
									lines[game][label] = f"{row['outcomes'][1]['line']} "
								if "total" in label:
									lines[game][label] += f"{row['outcomes'][0]['oddsAmerican']}/{row['outcomes'][1]['oddsAmerican']}"
								else:
									lines[game][label] += f"{row['outcomes'][1]['oddsAmerican']}/{row['outcomes'][0]['oddsAmerican']}"

	with open("static/fiba/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def write365Props():
	url = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B18/C20902960/D43/E181378/F43/"

	js = """

	let data = {};

	{
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase().replace("player ", "");
		if (title == "assists") {
			title = "ast";
		} else if (title === "points") {
			title = "pts";
		} else if (title === "rebounds") {
			title = "reb";
		}
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
		console.log(data)
	}
	"""
	pass

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B18/C20902960/D43/E181378/F43/"

	js = """
	const data = {};

	{
		const main = document.querySelector(".gl-MarketGroupContainer");

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
			const game = away+" @ "+home
			games.push(game);

			if (!data[game]) {
				data[game] = {};
			}
		}

		idx = 0;
		let divs = main.querySelectorAll(".gl-Market_General")[1].querySelectorAll(".gl-Participant_General");
		for (let i = 0; i < divs.length; i += 2) {
			let game = games[idx];

			if (!game) {
				break;
			}

			data[game]["spread"] = "";
			let line = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Handicap").innerText;
			data[game]["spread"] = line+" ";

			let odds = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
			data[game]["spread"] += odds+"/";

			odds = divs[i+1].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
			data[game]["spread"] += odds;
			idx += 1;
		}

		idx = 0;
		divs = main.querySelectorAll(".gl-Market_General")[2].querySelectorAll(".gl-Participant_General");
		for (let i = 0; i < divs.length; i += 2) {
			let game = games[idx];

			if (!game) {
				break;
			}

			data[game]["total"] = "";
			let line = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Handicap").innerText.replace("O ", "");
			data[game]["total"] = line+" ";

			let odds = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
			data[game]["total"] += odds+"/";

			odds = divs[i+1].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
			data[game]["total"] += odds;
			idx += 1;
		}

		idx = 0;
		divs = main.querySelectorAll(".gl-Market_General")[3].querySelectorAll(".gl-Participant_General");
		for (let i = 0; i < divs.length; i += 2) {
			let game = games[idx];

			if (!game) {
				break;
			}

			data[game]["ml"] = "";
			let odds = divs[i].querySelector(".sac-ParticipantOddsOnly50OTB_Odds").innerText;
			data[game]["ml"] += odds+"/";

			odds = divs[i+1].querySelector(".sac-ParticipantOddsOnly50OTB_Odds").innerText;
			data[game]["ml"] += odds;

			if (data[game]["ml"] === "/") {
				delete data[game]["ml"];
			}
			idx += 1;
		}

		console.log(data);

	}

	"""
	pass

def writeEV(prop="", bookArg="fd", teamArg=""):
	with open(f"{prefix}static/fiba/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/fiba/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/fiba/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/fiba/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/fiba/ev.json") as fh:
		evData = json.load(fh)

	if not teamArg:
		evData = {}
	elif teamArg:
		for player in evData.copy():
			if teamArg in evData[player]["game"]:
				del evData[player]

	for game in dkLines:
		if teamArg and teamArg not in game:
			continue
		team1, team2 = map(str, game.split(" @ "))
		switchGame = f"{team2} @ {team1}"
		for prop in dkLines[game]:
			a = dkLines[game][prop]
			if prop in ["ml", "total", "spread"]:
				a = [" "]
			for player in a:
				if prop in ["ml", "total", "spread"]:
					dk = dkLines[game][prop]
				else:
					dk = dkLines[game][prop][player]
				handicap = ""
				if prop != "ml":
					handicap = dk.split(" ")[0]
				dk = dk.split(" ")[-1]

				kambi = ""
				if game in kambiLines and prop in kambiLines[game]:

					if prop == "ml":
						kambi = kambiLines[game][prop]
					if prop in ["spread", "total"]:
						if handicap in kambiLines[game][prop]:
							kambi = kambiLines[game][prop][handicap]
					else:
						if player in kambiLines[game][prop] and kambiLines[game][prop][player].startswith(handicap):
							kambi = kambiLines[game][prop][player].split(" ")[-1]

				bet365 = ""
				if game in bet365Lines and prop in bet365Lines[game]:
					if prop == "ml":
						bet365 = bet365Lines[game][prop]
					if prop in ["spread", "total"]:
						if bet365Lines[game][prop].startswith(handicap):
							bet365 = bet365Lines[game][prop].split(" ")[-1]
					else:
						if player in bet365Lines[game][prop] and bet365Lines[game][prop][player].startswith(handicap):
							bet365 = bet365Lines[game][prop][player].split(" ")[-1]

				fd = ""
				if game in fdLines and prop in fdLines[game]:
					if prop == "ml":
						fd = fdLines[game][prop]
					if prop in ["spread", "total"]:
						if fdLines[game][prop].startswith(handicap):
							fd = fdLines[game][prop].split(" ")[-1]
					else:
						if player in fdLines[game][prop] and fdLines[game][prop][player].startswith(handicap):
							fd = fdLines[game][prop][player].split(" ")[-1]

				for i in range(2):
					#print(game, prop, player)
					line = dk.split("/")[i]
					l = [fd, bet365, kambi]

					avgOver = []
					avgUnder = []

					evBook = "dk"
					if bookArg == "fd" or not line or (fd and int(fd.split("/")[i]) > int(line)):
						evBook = "fd"
						line = fd.split("/")[i]
						l[0] = str(dk)

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

					line = convertAmericanOdds(1 + (convertDecOdds(int(line)) - 1))
					
					key = f"{game} {player} {prop} {'over' if i == 0 else 'under'}"
					if key in evData:
						continue
					if True:
						pass
						devig(evData, key, ou, int(line), prop=prop)
						#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
						if key not in evData:
							print(key)
							continue
						if float(evData[key]["ev"]) > 0:
							print(key, prop, evData[key]["ev"], game, int(line), ou, evBook)
						evData[key]["game"] = game
						evData[key]["book"] = evBook
						evData[key]["ou"] = ou
						evData[key]["under"] = i == 1
						evData[key]["odds"] = l
						evData[key]["line"] = line
						evData[key]["fanduel"] = str(fd).split(" ")[-1]
						evData[key]["dk"] = dk
						evData[key]["value"] = str(handicap)

	with open(f"{prefix}static/fiba/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def sortEV():
	with open(f"{prefix}static/fiba/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		data.append((d["ev"], player, d["value"], d["game"], d["line"], d["book"], d["odds"]))

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

	if args.update:
		writeFanduel()
		writeDK(args.date)
		#writeActionNetwork(args.date)
		writeKambi()

	if args.ev:
		writeEV(prop=args.prop, bookArg=args.book)

	if args.print:
		sortEV()

	if args.prop:
		#writeEV(dinger=dinger, date=args.date, avg=True, allArg=args.all, gameArg=args.game, teamArg=args.team, prop=args.prop, under=args.under, nocz=args.nocz, nobr=args.nobr, no365=args.no365, boost=args.boost, bookArg=args.book)
		sortEV()
	#write365()
	#writeActionNetwork()

	