from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time
import math
from twilio.rest import Client

def convertActionTeam(team):
	if team.endswith(" st"):
		team = team.replace(" st", " state")
	if "international" in team:
		team = team.replace("international", "intl")
	teams = {
		"jax state": "jacksonville state",
		"n mexico state": "new mexico state",
		"umass": "massachusetts",
		"la tech": "louisiana tech",
		"fiu": "florida intl"
	}
	return teams.get(team, team)

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	return player.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")

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

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"


def writeBet365():

	url = "https://www.oh.bet365.com/?_h=7KkQ9oD5Yw8_sBdGSlEFeA%3D%3D#/AC/B12/C20437885/D47/E120591/F47/"

	js = """

	let data = {};

	{
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();

		if (title == "touchdown scorers") {
			title = "td";
		} else if (title.split(" ")[0] == "player") {
			title = title.slice(7).replace("touchdowns", "td").replace("passing", "pass").replace("receiving", "rec").replace("rushing", "rush").replace("yards", "yd").replace(" ", "_");
		} else if (title == "alternative spread") {
			title = "spread";
		}

		if (title.indexOf("spread") >= 0 || title.indexOf("total") >= 0) {
			for (div of document.getElementsByClassName("src-FixtureSubGroupWithShowMore")) {
				const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase();

				console.log(game)
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
					let line = "";

					if (title == "total") {
						line = lineOdds.innerText;
					} else {
						line = lineOdds.querySelector(".gl-ParticipantCentered_Name").innerText;
					}

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
		} else if (title == "td") {
			for (div of document.querySelectorAll(".src-FixtureSubGroupWithShowMore")) {
				const showMore = div.querySelector(".msl-ShowMore_Link");

				if (div.classList.contains("src-FixtureSubGroupWithShowMore_Closed")) {
					div.click();
				}
				let playerList = [];
				for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
					let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(". ", "").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
					let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];
					
					if (!data[team]) {
						data[team] = {};
					}

					if (!data[team]["ftd"]) {
						data[team]["ftd"] = {};
					}
					if (!data[team]["attd"]) {
						data[team]["attd"] = {};
					}
					playerList.push([team, player]);
				}

				let idx = 0;
				for (playerDiv of div.querySelectorAll(".gl-Market")[1].querySelectorAll(".gl-ParticipantOddsOnly_Odds")) {
					let team = playerList[idx][0];
					let player = playerList[idx][1];

					let odds = playerDiv.innerText;
					data[team]["ftd"][player] = odds;
					idx += 1;
				}

				idx = 0;
				for (playerDiv of div.querySelectorAll(".gl-Market")[3].querySelectorAll(".gl-ParticipantOddsOnly_Odds")) {
					let team = playerList[idx][0];
					let player = playerList[idx][1];

					let odds = playerDiv.innerText;
					data[team]["attd"][player] = odds;
					idx += 1;
				}
			}
		} else {
			for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
				const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" v ", " @ ");
				if (div.classList.contains("src-FixtureSubGroup_Closed")) {
					div.click();
				}
				let playerList = [];
				for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
					let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(". ", "").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
					let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];
					
					if (!data[team]) {
						data[team] = {};
					}
					if (!data[team][title]) {
						data[team][title] = {};
					}

					data[team][title][player] = "";
					playerList.push([team, player]);
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
		}
		console.log(data)
	}

"""

def writeKambi(date):

	if not date:
		date = datetime.now()
		date = str(date)[:10]

	data = {}
	outfile = f"ncaafout.json"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/american_football/ncaaf/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	eventIds = {}
	for event in j["events"]:
		home = convertActionTeam(event["event"]["homeName"].lower())
		away = convertActionTeam(event["event"]["awayName"].lower())
		game = strip_accents(f"{home} @ {away}")
		dt = datetime.strptime(event["event"]["start"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if game in eventIds or str(dt)[:10] != date:
			continue
			#pass
		eventIds[game] = event["event"]["id"]


	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		for betOffer in j["betOffers"]:
			label = betOffer["criterion"]["label"].lower()
			if not teamIds and "handicap" in label:
				for row in betOffer["outcomes"]:
					team = home
					if away in row["label"].lower():
						team = away
					teamIds[row["participantId"]] = team
					data[team] = {}

			elif label.startswith("touchdown scorer") or label.startswith("first touchdown scorer") or "by the player" in label:
				prop = "attd"
				if label.startswith("first"):
					prop = "ftd"
				elif "by the player" in label:
					label = label.split(" by the player")[0].split("total ")[-1]
					prop = label.replace(" ", "_").replace("passing", "pass").replace("rushing", "rush").replace("yards", "yd").replace("receiving", "rec")
					if prop == "touchdown_passes_thrown":
						prop = "pass_td"

				if prop not in ["attd", "ftd"]:
					player = strip_accents(betOffer["outcomes"][0]["participant"])
					try:
						last, first = map(str, player.split(" (")[0].lower().split(", "))
						player = f"{first} {last}"
					except:
						player = player.lower()
					player = parsePlayer(player)

					if player not in data[team]:
						data[team][player] = {}
					if prop not in data[team][player]:
						data[team][player][prop] = {}
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					data[team][player][prop][line] = f"{betOffer['outcomes'][0]['oddsAmerican']}/{betOffer['outcomes'][1]['oddsAmerican']}"
				else:
					if prop == "attd":
						player = strip_accents(betOffer["outcomes"][0]["participant"])
						try:
							last, first = map(str, player.split(" (")[0].lower().split(", "))
							player = f"{first} {last}"
						except:
							player = player.lower()
						player = parsePlayer(player)
						team = teamIds[betOffer["outcomes"][0]["eventParticipantId"]]
						over = betOffer["outcomes"][0]["oddsAmerican"]
						if player not in data[team]:
							data[team][player] = {}
						data[team][player][prop] = f"{over}"
					else:
						for outcome in betOffer["outcomes"]:
							if "participant" not in outcome:
								continue
							player = strip_accents(outcome["participant"])
							try:
								last, first = map(str, player.split(" (")[0].lower().split(", "))
								player = f"{first} {last}"
							except:
								player = player.lower()
							player = parsePlayer(player)
							team = teamIds[outcome["eventParticipantId"]]
							over = outcome["oddsAmerican"]
							if player not in data[team]:
								data[team][player] = {}
							data[team][player][prop] = f"{over}"


	with open(f"{prefix}static/ncaafprops/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

actionNetworkBookIds = {
	68: "draftkings",
	69: "fanduel",
	#15: "betmgm",
	283: "mgm",
	348: "betrivers",
	351: "pointsbet",
	355: "caesars"
}

def writeActionNetwork(dateArg = None):
	props = ["56_first_touchdown_scorer", "62_anytime_touchdown_scorer", "9_passing_yards", "11_passing_tds", "17_receiving_tds", "16_receiving_yards", "13_rushing_tds", "12_rushing_yards"]

	odds = {}
	optionTypes = {}

	if not dateArg:
		date = datetime.now()
		date = str(date)[:10]
	else:
		date = dateArg

	if datetime.now().hour > 21:
		date = str(datetime.now() + timedelta(days=1))[:10]

	#props = ["11_passing_tds"]
	for actionProp in props:
		time.sleep(0.2)
		path = f"ncaafout.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/2/props/core_bet_type_{actionProp}?bookIds=69,68,283,348,351,355&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		prop = ""
		if "touchdown" in actionProp:
			prop = "ftd"
			if "anytime" in actionProp:
				prop = "attd"
		else:
			prop = "_".join(actionProp.split("_")[1:]).replace("rushing", "rush").replace("passing", "pass").replace("receiving", "rec").replace("yards", "yd")

		if prop.endswith("s"):
			prop = prop[:-1]

		with open(path) as fh:
			j = json.load(fh)

		if "markets" not in j:
			return
		market = j["markets"][0]

		for option in market["rules"]["options"]:
			optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

		teamIds = {}
		for row in market["teams"]:
			#teamIds[row["id"]] = row["abbr"].lower()
			teamIds[row["id"]] = convertActionTeam(row["display_name"].lower().replace(".", ""))

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
				overUnder = "over"
				try:
					overUnder = optionTypes[oddData["option_type_id"]]
				except:
					pass
				book = actionNetworkBookIds.get(bookId, "")
				value = str(oddData["value"])

				if team not in odds:
					odds[team] = {}
				if player not in odds[team]:
					odds[team][player] = {}
				if prop not in odds[team][player]:
					odds[team][player][prop] = {}

				if book not in odds[team][player][prop]:
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[team][player][prop][book] = f"{v}{oddData['money']}"
				elif overUnder == "over":
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[team][player][prop][book] = f"{v}{oddData['money']}/{odds[team][player][prop][book].replace(v, '')}"
				else:
					odds[team][player][prop][book] += f"/{oddData['money']}"
				sp = odds[team][player][prop][book].split("/")
				if odds[team][player][prop][book].count("/") == 3:
					odds[team][player][prop][book] = sp[1]+"/"+sp[2]

	with open(f"{prefix}static/ncaafprops/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	
	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/football/ncaa-football") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && time.innerText.split(" ").length === 2) {
					urls[a.href] = 1;
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/elon-@-wake-forest-32601835",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/kent-state-@-ucf-32527489",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/north-carolina-state-@-connecticut-32527921",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/north-carolina-a-t-@-uab-32601831",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/arkansas-pine-bluff-@-tulsa-32601836",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/south-dakota-@-missouri-32601814",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/nebraska-@-minnesota-32563890",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/florida-@-utah-32563892",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/southern-utah-@-arizona-state-32601837"
]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		#away, home = map(str, game.split(" @ "))
		#game = f"{convertCollege(away)} @ {convertCollege(home)}"
		if game in lines:
			continue
		lines[game] = {}

		outfile = "ncaafout"

		for tab in ["td-scorer", "passing", "receiving", "rushing"]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}&tab={tab}-props"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue
			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()

				if marketName in ["any time touchdown scorer", "first touchdown scorer"] or " - passing yds" in marketName or " - rushing yds" in marketName or " - passing tds" in marketName or " - rushing tds" in marketName:

					prop = "attd"
					if "first" in marketName:
						prop = "ftd"
					elif " - passing yds" in marketName:
						prop = "pass_yd"
					elif " - passing tds" in marketName:
						prop = "pass_td"
					elif " - receiving yds" in marketName:
						prop = "rec_yd"
					elif " - receiving tds" in marketName:
						prop = "rec_td"
					elif " - rushing yds" in marketName:
						prop = "rush_yd"
					elif " - rushing tds" in marketName:
						prop = "rush_td"

					runners = data["attachments"]["markets"][market]["runners"]
					skip = 1 if prop in ["ftd", "attd"] else 2
					for i in range(0, len(runners), skip):
						player = parsePlayer(runners[i]["runnerName"].lower().replace(" over", "").replace(" under", ""))
						handicap = ""
						try:
							odds = runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
						except:
							continue

						if prop not in lines[game]:
							lines[game][prop] = {}

						if prop in ["ftd", "attd"]:
							lines[game][prop][player] = odds
						else:
							lines[game][prop][player] = str(runners[i]["handicap"])+" "+str(odds)+"/"+str(runners[i+1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])


	
	with open(f"{prefix}static/ncaafprops/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="attd"):

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

def writeEV(date=None, gameArg="", teamArg="", propArg="attd", book="", boost=None):
	if not date:
		date = str(datetime.now())[:10]

	if not boost:
		boost = 1

	with open(f"{prefix}static/ncaafprops/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/ncaafprops/ev.json") as fh:
		evData = json.load(fh)

	fdGames = {}
	for game in fdLines:
		fdGames[game.split(" @ ")[0]] = game
		fdGames[game.split(" @ ")[1]] = game

	evData = {}

	for team in fdGames:
		if not team:
			continue
		if teamArg and teamArg not in team:
			continue
		if team not in actionnetwork:
			continue
		for player in actionnetwork[team]:
			if not player:
				continue

			for prop in actionnetwork[team][player]:
				handicap = ""

				if propArg and propArg != prop:
					continue

				an = actionnetwork[team][player][prop]
				fd = "-"
				dk = an.get("draftkings", "-")
				br = an.get("betrivers", "-")
				mgm = an.get("mgm", "-")
				cz = an.get("caesars", "-")

				if " " in dk:
					handicap = float(str(dk.split(" ")[0]))

				fdGame = fdGames.get(team, "")
				if fdGame and fd == "-" and prop in fdLines[fdGame] and player in fdLines[fdGame][prop]:
					fd = str(fdLines[fdGame][prop][player])
					if handicap:
						if float(fd.split(" ")[0]) == handicap:
							fd = fd.split(" ")[-1]
						else:
							fd = "-"

				if fd == "-" and dk == "-":
					continue

				if handicap:
					if dk != "-" and float(dk.split(" ")[0]) == handicap:
						dk = dk.split(" ")[-1]
					else:
						dk = "-"
					if br != "-" and float(br.split(" ")[0]) == handicap:
						br = br.split(" ")[-1]
					else:
						br = "-"
					if mgm != "-" and float(mgm.split(" ")[0]) == handicap:
						mgm = mgm.split(" ")[-1]
					else:
						mgm = "-"
					if cz != "-" and float(cz.split(" ")[0]) == handicap:
						cz = cz.split(" ")[-1]
					else:
						cz = "-"

				kambi = "-"
				if team in kambiLines and player in kambiLines[team] and prop in kambiLines[team][player]:
					kambi = kambiLines[team][player][prop]
					if handicap:
						if "autman bell" in player:
							print(kambi, handicap)
						if str(handicap) in kambiLines[team][player][prop]:
							kambi = kambiLines[team][player][prop][str(handicap)]
						else:
							kambi = "-"


				bet365 = "-"
				try:
					bet365 = bet365Lines[team][prop][player]
					if handicap:
						if float(bet365.split(" ")[0]) == handicap:
							bet365 = bet365.split(" ")[-1]
						else:
							bet365 = "-"
				except:
					pass

				for i in range(2):

					if "/" not in fd and i == 1:
						continue

					l = [fd, br, mgm, cz, kambi, bet365]
					evBook = "dk"
					evLine = dk

					if book == "fd" or (dk == "-" or (fd and fd != "-" and int(fd.split("/")[0]) > int(dk.split("/")[0]))):
						evLine = fd
						evBook = "fd"
						l[0] = dk

					evLine = evLine.split("/")[i]

					if evLine == "-":
						continue

					avgOver = []
					avgUnder = []
					for line in l:
						if line and line != "-":
							avgOver.append(convertDecOdds(int(line.split("/")[0])))
							if "/" in line:
								avgUnder.append(convertDecOdds(int(line.split("/")[1])))

					#print(avgOver)
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

					evLine = convertAmericanOdds(1 + (convertDecOdds(int(evLine)) - 1) * boost)

					key = f"{player} {prop} {'over' if i == 0 else 'under'} {handicap}"
					#print(l, key, ou, evLine)
					devig(evData, key, ou, int(evLine), prop=prop)
					if key not in evData:
						print(key)
						continue

					evData[key]["odds"] = {
						"fd": fd,
						"dk": dk,
						"mgm": mgm,
						"bet365": bet365,
						"kambi": kambi,
						"br": br,
						"cz": cz
					}
					evData[key]["book"] = evBook
					evData[key]["team"] = team
					evData[key]["ou"] = ou
					evData[key]["line"] = evLine
					evData[key]["player"] = player
					evData[key]["prop"] = prop
					evData[key]["handicap"] = handicap

	with open(f"{prefix}static/ncaafprops/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	data = []
	for key in evData:
		data.append((evData[key]["ev"], key, evData[key]["book"], evData[key]["team"], evData[key]["line"], [k+' '+evData[key]["odds"][k] for k in evData[key]["odds"] if evData[key]["odds"][k] != "-" and k != evData[key]["book"]]))

	for row in sorted(data):
		print(row)

def printEV():

	with open(f"{prefix}static/ncaafprops/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for key in evData:
		data.append((evData[key]["ev"], evData[key]["player"], evData[key]["prop"], evData[key]["team"], evData[key]["line"], evData[key]["book"], evData[key]))

	output = "\t".join(["EV", "Player", "Prop", "Team", "FD", "DK", "Bet365", "MGM", "Kambi", "CZ", "BR"]) + "\n"
	for row in sorted(data, reverse=True):
		arr = [row[0], row[1], row[2], row[3]]
		for book in ["fd", "dk", "bet365", "mgm", "kambi", "cz", "br"]:
			arr.append(row[-1]["odds"][book])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open(f"static/ncaafprops/ev.csv","w") as fh:
		fh.write(output)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("-g", "--game", help="Game")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("--book", help="Book")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--fd", action="store_true", help="FD")
	parser.add_argument("-p", "--print", action="store_true", help="Print")

	args = parser.parse_args()

	if args.update:
		writeFanduel()
		writeActionNetwork(args.date)
		writeKambi(args.date)

	if args.fd:
		writeFanduel()

	if args.action:
		writeActionNetwork(args.date)

	if args.kambi:
		writeKambi(args.date)

	if args.ev or args.prop:
		writeEV(date=args.date, gameArg=args.game, teamArg=args.team, propArg=args.prop, book=args.book, boost=args.boost)

	if args.print:
		printEV()

	if False:
		o = 100
		u = -200

		impliedOver = 100 / (o + 100)
		impliedUnder = u*-1 / (-1*u + 100)

		print("mult", impliedOver / (impliedOver + impliedUnder))
		print("additive", impliedOver - (impliedOver+impliedUnder-1) / 2)
		#power
		import math
		x = impliedOver
		y = impliedUnder
		while round(x+y, 6) != 1.0:
			k = math.log(2) / math.log(2 / (x+y))
			x = x**k
			y = y**k

		print(x)