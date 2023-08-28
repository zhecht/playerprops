
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
	url = "https://bv2.digitalsportstech.com/api/game?sb=bovada&league=143"
	outfile = f"outBV"

	if True:
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		ids = []
		for row in data:
			ids.append([r for r in row["providers"] if r["name"] == "nix"][0]["id"])

	res = {}
	print(ids)
	for nixId in ids:
		for prop in ["tb", "hr"]:
			url = f"https://bv2.digitalsportstech.com/api/dfm/marketsBySs?sb=bovada&gameId={nixId}&statistic="
			if prop == "tb":
				url += "Total%2520bases"
			else:
				url += "Home%2520runs"
			outfile = f"outBV"

			time.sleep(0.31)
			os.system(f"curl -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			for playerRow in data[0]["players"]:
				player = strip_accents(playerRow["name"]).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
				team = playerRow["team"].lower()

				if team not in res:
					res[team] = {}

				if player not in res[team]:
					res[team][player] = {}

				res[team][player][prop] = {}
				for market in playerRow["markets"]:
					tb = market["value"]
					odds = convertAmericanOdds(market["odds"])
					res[team][player][prop][tb] = odds

	
	with open("static/freebets/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def checkBovada():
	with open("static/freebets/bovada.json") as fh:
		bv = json.load(fh)

	with open("static/baseballreference/fanduelLines.json") as fh:
		fd = json.load(fh)

	for game in fd:
		team1, team2 = map(str, game.split(" @ "))
		for player in fd[game]:
			if "hr" not in fd[game][player]:
				continue

			hr = fd[game][player]["hr"]
			team = ""
			if team1 in bv and player in bv[team1]:
				team = team1
			elif team2 in bv and player in bv[team2]:
				team = team2
			else:
				continue

			if "4" not in bv[team][player]["tb"]:
				continue

			if bv[team][player]["tb"]["4"] > hr:
				print(team, player, hr, bv[team][player]["tb"]["4"])

def writeBallparkpal():
	js = """
		for (btn of document.getElementsByTagName("button")) {
			if (btn.innerText === "Expanded Book View") {
				btn.click();
			}
		}

		const data = {};
		for (row of document.getElementsByTagName("tr")) {
			tds = row.getElementsByTagName("td");
			if (tds.length === 0) {
				continue;
			}
			let team = tds[0].innerText.toLowerCase();
			if (team === "was") {
				team = "wsh";
			}

			if (data[team] === undefined) {
				data[team] = {};
			}

			let player = tds[1].innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "").replace("michael a taylor", "michael taylor");

			if (data[team][player] === undefined) {
				data[team][player] = {};
			}

			let prop = tds[2].innerText.toLowerCase().split(" ")[1];
			let line = tds[2].innerText.split(" ")[2];
			if (prop === "ks") {
				prop = "k";
			} else if (prop === "bases") {
				prop = "tb";
			} else if (prop === "hits") {
				prop = "h";
			}

			let max = 0;
			let maxBooks = [];
			let books = ["fd", "dk", "mgm", "cz", "pn", "bs"];
			let idx = 4;
			while (idx < 10) {
				if (tds[idx].innerText) {
					const odds = parseInt(tds[idx].innerText);
					if (odds == max) {
						maxBooks.push(books[idx-4]);
					} else if (odds > max) {
						maxBooks = [books[idx-4]];
						max = odds;
					}
				}
				idx++;
			}

			if (data[team][player][prop] === undefined) {
				data[team][player][prop] = {};
			}

			data[team][player][prop][line] = {
				bpp: tds[3].innerText,
				fd: tds[4].innerText,
				dk: tds[5].innerText,
				mgm: tds[6].innerText,
				cz: tds[7].innerText,
				pn: tds[8].innerText,
				bs: tds[9].innerText,
				max: max,
				maxBooks: maxBooks
			}
		}
		console.log(data);

	"""

def convertBPPTeam(team):
	return team.replace("nationals", "wsh").replace("phillies", "phi").replace("twins", "min").replace("tigers", "det").replace("marlins", "mia").replace("reds", "cin").replace("cardinals", "stl").replace("rays", "tb").replace("braves", "atl").replace("pirates", "pit").replace("astros", "hou").replace("orioles", "bal").replace("blue jays", "tor").replace("guardians", "cle").replace("royals", "kc").replace("red sox", "bos").replace("cubs", "chc").replace("mets", "nym").replace("yankees", "nyy").replace("white sox", "chw").replace("rockies", "col").replace("brewers", "mil").replace("giants", "sf").replace("angels", "laa").replace("rangers", "tex").replace("athletics", "oak").replace("padres", "sd").replace("mariners", "sea").replace("dodgers", "lad").replace("dbacks", "ari")

def writeBPPHomers():
	url = "https://ballparkpal.com/index.php"
	outfile = f"outBpp"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	soup = BS(open(outfile, 'rb').read(), "lxml")

	links = []
	for a in soup.findAll("a"):
		if a.text == "Details":
			links.append(a.get("href"))

	data = {}
	for url in links:
		outfile = f"outBpp"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		soup = BS(open(outfile, 'rb').read(), "lxml")

		for table in soup.findAll("table", class_="runMarginTable"):
			if "Home Runs" not in table.text:
				continue
			game = convertBPPTeam(table.findAll("th")[1].text.lower()) + " @ " + convertBPPTeam(table.findAll("th")[3].text.lower())
			if game not in data:
				tds = table.findAll("tr")[3].findAll("td")
				data[game] = round(float(tds[1].text) + float(tds[3].text), 2)
			break

	with open(f"{prefix}static/freebets/bppExpectedHomers.json", "w") as fh:
		json.dump(data, fh, indent=4)


def checkBPP():
	with open(f"{prefix}static/mlbprops/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/mlbprops/bpp.json") as fh:
		bppLines = json.load(fh)

	data = []
	for team in bppLines:
		for player in bppLines[team]:
			try:
				bet365Underdog = int(bet365Lines[team][player].split("/")[0])
			except:
				continue

			maxBpp = bppLines[team][player]["max"]
			maxBooks = bppLines[team][player]["maxBooks"]
			fd = bppLines[team][player]["fd"]
			if maxBpp > bet365Underdog and maxBooks != ["fd"]:
				summary = f"{player} bet={bet365Lines[team][player]}; max={maxBpp}; maxBooks={maxBooks}; fd={fd}"
				diff = (maxBpp - bet365Underdog) / bet365Underdog
				data.append((diff, summary))

	for row in sorted(data, reverse=True):
		print(row[1])

def sendText(body=""):
	accountSid = os.environ["TWILIO_ACCOUNT_SID"]
	authToken = os.environ["TWILIO_AUTH_TOKEN"]

	client = Client(accountSid, authToken)

	message = client.messages.create(
		body=body,
		from_="+18334181767",
		to=os.environ["TWILIO_TO"]
	)

def writeLineups(plays = []):
	url = "https://www.mlb.com/starting-lineups/"
	outfile = f"outlineups"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = {}
	for table in soup.findAll("div", class_="starting-lineups__matchup"):
		for which in ["away", "home"]:
			team = table.find("div", class_=f"starting-lineups__teams--{which}-head").text.strip().split(" ")[0].lower().replace("az", "ari")

			if team in data:
				continue
			data[team] = []
			for player in table.find("ol", class_=f"starting-lineups__team--{which}").findAll("li"):
				try:
					player = player.find("a").text.strip().lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
				except:
					player = player.text

				data[team].append(player)

	with open(f"{prefix}static/freebets/lineupsSent.json") as fh:
		lineupsSent = json.load(fh)

	date = datetime.now()
	date = str(date)[:10]

	if True or datetime.now().hour > 21 or datetime.now().hour < 10:
		pass
	else:
		if date != lineupsSent["updated"]:
			lineupsSent = {
				"updated": date,
				"teams": []
			}
		for team in data:
			if team not in lineupsSent["teams"] and data[team][0] != "TBD":

				for row in plays:
					if row[-1] == team:
						if row[0] not in data[row[-1]]:
							pass
							sendText(f"\n\n{team}\n\n{row[0]} SITTING")
				#sendText(f"\n\n{team}\n\n"+"\n".join(data[team]))
				lineupsSent["teams"].append(team)

	for row in plays:
		if row[-1] in data and len(data[row[-1]]) > 1:
			if row[0] not in data[row[-1]]:
				print(row[0], "SITTING!!")


	with open(f"{prefix}static/freebets/lineups.json", "w") as fh:
		json.dump(data, fh, indent=4)

	with open(f"{prefix}static/freebets/lineupsSent.json", "w") as fh:
		json.dump(lineupsSent, fh, indent=4)


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
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		i = 0
		for betOffer in j["betOffers"]:
			label = betOffer["criterion"]["label"]
			if label == "Total Points - Including Overtime":
				label = "total"
			elif "Handicap - Including Overtime" in label:
				label = "spread"
			elif label == "Including Overtime":
				label = "ml"


			if label == "ml":
				team = betOffer["outcomes"][0]["label"].lower()
				if game.startswith(team):
					data[game]["ml"] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				else:
					data[game]["ml"] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label == "spread":
				if "spread" not in data[game]:
					data[game]["spread"] = {}
				line = betOffer["outcomes"][0]["line"] / 1000
				line2 = betOffer["outcomes"][1]["line"] / 1000
				team = betOffer["outcomes"][0]["label"].lower()
				if game.startswith(team):
					data[game]["spread"][line] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				else:
					data[game]["spread"][line2] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label in ["total"]:
				if "total" not in data[game]:
					data[game]["total"] = {}
				line = betOffer["outcomes"][0]["line"] / 1000
				data[game]["total"][str(line)] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]


	with open(f"{prefix}static/fiba/kambi.json", "w") as fh:
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

def writeActionNetworkML():
	date = datetime.now()
	date = str(date)[:10]

	if datetime.now().hour > 21:
		date = str(datetime.now() + timedelta(days=1))[:10]

	time.sleep(0.2)
	path = f"out.json"
	url = f"https://api.actionnetwork.com/web/v1/scoreboard/mlb?period=game&bookIds=15,30,283,366,68,351,348,355,76,75,123,69&date={date.replace('-', '')}"
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

	with open(path) as fh:
		j = json.load(fh)

	#with open("j.json", "w") as fh:
	#	json.dump(j, fh, indent=4)

	if "games" not in j:
		return

	data = {}
	
	for game in j["games"]:
		if game["status"] == "complete":
			continue
		start = game["start_time"].split(".")[0].split("T")[1]
		inning = ""
		if game["status"] == "inprogress":
			inning = game["status_display"]
		away = game["teams"][0]["abbr"].lower()
		home = game["teams"][1]["abbr"].lower()
		awayScore = game["boxscore"]["stats"]["away"]["runs"]
		homeScore = game["boxscore"]["stats"]["home"]["runs"]
		score = f"{awayScore}-{homeScore}"
		if inning:
			score += f" {inning}"

		g = f"{away} @ {home}"
		data[g] = {
			"start": start,
			"score": score,
			"ou": {},
			"ml": {},
			"spread": {},
			"away_ou": {},
			"home_ou": {}
		}

		for odd in game["odds"]:
			book = actionNetworkBookIds.get(odd["book_id"], "")
			if not book:
				#print(odd["book_id"])
				continue

			if odd["total"] not in data[g]["ou"]:
				data[g]["ou"][odd["total"]] = {}

			spread = odd["spread_away"]
			if spread not in data[g]["spread"]:
				data[g]["spread"][spread] = {}

			for which in ["away", "home"]:
				ou = odd[f"{which}_total"]
				if not ou:
					continue
				if ou not in data[g][f"{which}_ou"]:
					data[g][f"{which}_ou"][ou] = {}
				data[g][f"{which}_ou"][ou][book] = str(odd[f"{which}_over"])+"/"+str(odd[f"{which}_under"])

			if odd['over']:
				data[g]["ou"][odd["total"]][book] = f"{odd['over']}/{odd['under']}"
			if odd['ml_away']:
				data[g]["ml"][book] = f"{odd['ml_away']}/{odd['ml_home']}"
			if odd['spread_away_line']:
				data[g]["spread"][spread][book] = f"{odd['spread_away_line']}/{odd['spread_home_line']}"

	#with open("t.json", "w") as fh:
	#	json.dump(data, fh, indent=4)

	for game in data:

		for which in ["ou", "away_ou", "home_ou"]:
			ou = ""
			ouLen = 0
			for ouNum in data[game][which]:
				if not ou:
					ou = ouNum
				if len(data[game][which].keys()) > ouLen:
					ou = ouNum
					ouLen = len(data[game][which].keys())
			avgOU = [[], []]
			maxOU = [[], []]
			if not ou:
				continue
			for book in data[game][which][ou]:
				awayOdds, homeOdds = map(int, data[game][which][ou][book].split("/"))
				odds = [convertDecOdds(awayOdds), convertDecOdds(homeOdds)]
				if not maxOU[0]:
					maxOU[0] = maxOU[1] = [book]
				else:
					if odds[0] > max(avgOU[0]):
						maxOU[0] = [book]
					elif odds[0] == max(avgOU[0]):
						maxOU[0].append(book)
					if odds[1] > max(avgOU[1]):
						maxOU[1] = [book]
					elif odds[1] == max(avgOU[1]):
						maxOU[1].append(book)

				avgOU[0].append(odds[0])
				avgOU[1].append(odds[1])

			over = convertDecOdds(int(data[game][which][ou][maxOU[0][0]].split("/")[0]))
			under = convertDecOdds(int(data[game][which][ou][maxOU[1][0]].split("/")[1]))
			if False and len(avgOU[0]) > 1:
				avgOU[0].remove(over)
				avgOU[1].remove(under)
			avgOU[0], avgOU[1] = str(convertAmericanOdds(float(sum(avgOU[0]) / len(avgOU[0])))), str(convertAmericanOdds(float(sum(avgOU[1]) / len(avgOU[1]))))
			data[game][f"{which}_num"] = ou
			data[game][f"{which}_avg"] = "/".join(avgOU)
			data[game][f"{which}_away"] = f"{','.join(maxOU[0])} {data[game][which][ou][maxOU[0][0]].split('/')[0]}"
			data[game][f"{which}_home"] = f"{','.join(maxOU[1])} {data[game][which][ou][maxOU[1][0]].split('/')[1]}"

		avgML = [[], []]
		maxML = [[], []]
		for book in data[game]["ml"]:
			awayOdds, homeOdds = map(int, data[game]["ml"][book].split("/"))
			odds = [convertDecOdds(awayOdds), convertDecOdds(homeOdds)]
			if not maxML[0]:
				maxML[0] = maxML[1] = [book]
			else:
				if odds[0] > max(avgML[0]):
					maxML[0] = [book]
				elif odds[0] == max(avgML[0]):
					maxML[0].append(book)
				if odds[1] > max(avgML[1]):
					maxML[1] = [book]
				elif odds[1] == max(avgML[1]):
					maxML[1].append(book)
			avgML[0].append(odds[0])
			avgML[1].append(odds[1])

		if not data[game]["ml"]:
			continue
		over = convertDecOdds(int(data[game]["ml"][maxML[0][0]].split("/")[0]))
		under = convertDecOdds(int(data[game]["ml"][maxML[1][0]].split("/")[1]))
		if False:
			avgML[0].remove(over)
			avgML[1].remove(under)
		avgML[0], avgML[1] = str(convertAmericanOdds(float(sum(avgML[0]) / len(avgML[0])))), str(convertAmericanOdds(float(sum(avgML[1]) / len(avgML[1]))))
		data[game]["ml_avg"] = "/".join(avgML)
		data[game]["ml_away"] = f"{','.join(maxML[0])} {data[game]['ml'][maxML[0][0]].split('/')[0]}"
		data[game]["ml_home"] = f"{','.join(maxML[1])} {data[game]['ml'][maxML[1][0]].split('/')[1]}"



	with open(f"{prefix}static/freebets/actionnetworkML.json", "w") as fh:
		json.dump(data, fh, indent=4)



def writeActionNetwork(dateArg = None):
	props = ["35_doubles", "33_hr", "37_strikeouts", "32_singles", "77_total_bases"]
	#props = ["32_singles"]

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
		path = f"out.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/8/props/core_bet_type_{actionProp}?bookIds=69,68,283,348,351,355&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		prop = actionProp.split("_")[-1].replace("strikeouts", "k").replace("base", "tb")
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
			teamIds[row["id"]] = row["abbr"].lower().replace("cws", "chw")

		playerIds = {}
		for row in market["players"]:
			playerIds[row["id"]] = row["full_name"].lower().replace(".", "").replace("-", " ").replace("'", "").replace(" jr", "").replace(" ii", "")

		books = market["books"]
		for bookData in books:
			bookId = bookData["book_id"]
			if bookId not in actionNetworkBookIds or not actionNetworkBookIds[bookId]:
				continue
				pass
			for oddData in bookData["odds"]:
				player = playerIds[oddData["player_id"]]
				if player == "michael a taylor":
					player = "michael taylor"
				team = teamIds[oddData["team_id"]]
				overUnder = optionTypes[oddData["option_type_id"]]
				book = actionNetworkBookIds.get(bookId, "")
				value = oddData["value"]

				if team not in odds:
					odds[team] = {}
				if player not in odds[team]:
					odds[team][player] = {}
				if prop not in odds[team][player]:
					odds[team][player][prop] = {}

				if prop in ["k", "tb"]:
					if value not in odds[team][player][prop]:
						odds[team][player][prop][value] = {}

					if book not in odds[team][player][prop][value]:
						odds[team][player][prop][value][book] = f"{oddData['money']}"
					elif overUnder == "over":
						odds[team][player][prop][value][book] = f"{oddData['money']}/{odds[team][player][prop][value][book]}"
					else:
						odds[team][player][prop][value][book] += f"/{oddData['money']}"
				else:
					if book not in odds[team][player][prop]:
						odds[team][player][prop][book] = f"{oddData['money']}"
					elif overUnder == "over":
						odds[team][player][prop][book] = f"{oddData['money']}/{odds[team][player][prop][book]}"
					else:
						odds[team][player][prop][book] += f"/{oddData['money']}"
					sp = odds[team][player][prop][book].split("/")
					if odds[team][player][prop][book].count("/") == 3:
						odds[team][player][prop][book] = sp[1]+"/"+sp[2]

					if prop == "hr":
						sp = odds[team][player][prop][book].split("/")
						if len(sp) == 2 and int(sp[0]) < 0:
							del odds[team][player][prop][book]

	with open(f"{prefix}static/freebets/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def convertFDTeam(team):
	team = team.replace("pittsburgh pirates", "pit").replace("detroit tigers", "det").replace("cincinnati reds", "cin").replace("colorado rockies", "col").replace("minnesota twins", "min").replace("los angeles dodgers", "lad").replace("arizona diamondbacks", "ari").replace("oakland athletics", "oak").replace("philadelphia phillies", "phi").replace("san francisco giants", "sf").replace("kansas city royals", "kc").replace("san diego padres", "sd").replace("los angeles angels", "laa").replace("baltimore orioles", "bal").replace("washington nationals", "wsh").replace("miami marlins", "mia").replace("new york yankees", "nyy").replace("toronto blue jays", "tor").replace("seattle mariners", "sea").replace("boston red sox", "bos").replace("tampa bay rays", "tb").replace("new york mets", "nym").replace("milwaukee brewers", "mil").replace("st. louis cardinals", "stl").replace("atlanta braves", "atl").replace("texas rangers", "tex").replace("cleveland guardians", "cle").replace("chicago white sox", "chw").replace("chicago cubs", "chc").replace("houston astros", "hou")
	return team

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("basketball/international") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && time.getAttribute("datetime").split("T")[0] === "2023-08-28") {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/venezuela-v-cape-verde-32588636",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/china-v-south-sudan-32588635",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/new-zealand-v-jordan-32588637",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/ivory-coast-v-iran-32588638",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/georgia-v-slovenia-32588589",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/puerto-rico-v-serbia-32588588",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/greece-v-usa-32588623",
  "https://mi.sportsbook.fanduel.com/basketball/international---fiba-world-cup---men/brazil-v-spain-32588621"
]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		if game in lines:
			continue
		lines[game] = {}

		outfile = "out"

		for tab in ["", "player-points", "player-rebounds", "player-assists"]:
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

				if marketName in ["moneyline", "total points", "spread"] or " - points" in marketName or " - rebounds" in marketName or " - assists" in marketName:
					prop = "ml"
					if marketName == "total points":
						prop = "total"
					elif marketName == "spread":
						prop = "spread"
					elif "points" in marketName:
						prop = "pts"
					elif "rebounds" in marketName:
						prop = "reb"
					elif "ast" in marketName:
						prop = "ast"

					if prop in ["ml", "total", "spread"]:
						lines[game][prop] = ""

						for idx, runner in enumerate(runners):
							if idx == 0 and prop in ["total", "spread"]:
								lines[game][prop] = f"{runner['handicap']} "
							elif idx == 1:
								lines[game][prop] += "/"	
							lines[game][prop] += str(runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					else:
						player = strip_accents(marketName.split(" - ")[0]).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")

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
		"ast": 1217
	}

	lines = {}
	for mainCat in mainCats:
		time.sleep(0.3)
		url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/12550/categories/{mainCats[mainCat]}?format=json"
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

						if mainCat in ["pts", "reb", "ast"]:
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
							if label != "ml":
								lines[game][label] = f"{row['outcomes'][1]['line']} "
							if label == "total":
								lines[game][label] += f"{row['outcomes'][0]['oddsAmerican']}/{row['outcomes'][1]['oddsAmerican']}"
							else:
								lines[game][label] += f"{row['outcomes'][1]['oddsAmerican']}/{row['outcomes'][0]['oddsAmerican']}"

	with open("static/fiba/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def write365Props():
	url = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B18/C20902960/D43/E181378/F43/"

	js = """
	{
		let data = {};
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
		for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
			const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" v ", " @ ");
			if (div.classList.contains("src-FixtureSubGroup_Closed")) {
				div.click();
			}
			let playerList = [];
			for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
				let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(". ", "").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
				let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];
				
				if (data[game] === undefined) {
					data[game] = {};
				}
				data[game][player] = "";
				playerList.push([game, player]);
			}

			let idx = 0;
			for (playerDiv of div.getElementsByClassName("gl-Market")[1].getElementsByClassName("gl-ParticipantCenteredStacked")) {
				let team = playerList[idx][0];
				let player = playerList[idx][1];

				let line = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Handicap")[0].innerText;
				let odds = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
				data[team][player] = line+" "+odds;
				idx += 1;
			}

			idx = 0;
			for (playerDiv of div.getElementsByClassName("gl-Market")[2].getElementsByClassName("gl-ParticipantCenteredStacked")) {
				let team = playerList[idx][0];
				let player = playerList[idx][1];

				data[team][player] += "/" + playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
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
	{
		let data = {};
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
			data[game] = {};
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

	for p in ["pts", "reb", "ast"]:
		with open(f"{prefix}static/fiba/bet365_{p}.json") as fh:
			out = json.load(fh)
		for game in out:
			if game not in bet365Lines:
				bet365Lines[game] = {}
			bet365Lines[game][p] = out[game].copy()

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

			if prop not in ["pts", "reb", "ast"]:
				continue

			for player in dkLines[game][prop]:
				dk = dkLines[game][prop][player]
				handicap = ""
				if prop != "ml":
					handicap = dk.split(" ")[0]
				dk = dk.split(" ")[-1]

				kambi = ""
				if game in kambiLines and prop in kambiLines[game] and player in kambiLines[game][prop]:
					if prop != "ml" and handicap in kambiLines[game][prop]:
						kambi = kambiLines[game][prop][handicap]
					else:
						kambi = kambiLines[game][prop]

				bet365 = ""
				if game in bet365Lines and prop in bet365Lines[game] and player in bet365Lines[game][prop] and bet365Lines[game][prop][player].startswith(handicap):
					bet365 = bet365Lines[game][prop][player].split(" ")[-1]

				fd = ""
				if game in fdLines and prop in fdLines[game] and player in fdLines[game][prop] and fdLines[game][prop][player].startswith(handicap):
					fd = dkLines[game][prop][player].split(" ")[-1]


				for i in range(2):

					line = dk.split("/")[i]
					l = [fd, bet365, kambi]

					avgOver = []
					avgUnder = []

					evBook = "dk"
					if bookArg == "fd" or (fd and int(fd.split("/")[i]) > int(line)):
						evBook = "fd"
						line = fd.split("/")[i]
						l[0] = str(dkLines[game][prop][player])

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
					#player = f"{game} {prop}"
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
							print(player, prop, evData[player]["ev"], game, int(line), ou, evBook)
						evData[player]["game"] = game
						evData[player]["book"] = evBook
						evData[player]["ou"] = ou
						evData[player]["under"] = i == 1
						evData[player]["odds"] = l
						evData[player]["line"] = line
						evData[player]["fanduel"] = str(fd).split(" ")[-1]
						evData[player]["dk"] = dk
						evData[player]["value"] = str(handicap)

	with open(f"{prefix}static/fiba/ev.json", "w") as fh:
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

	with open("static/freebets/passing_boost.json", "w") as fh:
		json.dump(ev, fh, indent=4)


def sortEV(dinger=False):

	with open(f"{prefix}static/mlbprops/bpp.json") as fh:
		bppLines = json.load(fh)

	with open(f"{prefix}static/freebets/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/freebets/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/freebets/bovada.json") as fh:
		bovada = json.load(fh)

	with open(f"{prefix}static/freebets/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/freebets/bppExpectedHomers.json") as fh:
		bppExpectedHomers = json.load(fh)

	for prop in ["hr", "k", "single", "double", "tb"]:
		with open(f"{prefix}static/mlbprops/ev_{prop}.json") as fh:
			evData = json.load(fh)

		data = []
		bet365data = []
		for player in evData:
			try:
				ev = float(evData[player]["ev"])
			except:
				continue
			if "bet365ev" not in evData[player]:
				bet365ev = 0
			else:
				bet365ev = float(evData[player]["bet365ev"])
			bpp = dk = mgm = pb = cz = br = kambi = ""
			line = evData[player].get("line", 0)
			game = evData[player]["game"]
			team = evData[player].get("team", "")
			dk = evData[player]["dk"]
			value = evData[player].get("value", 0)
			if "/" in dk and int(dk.split("/")[0]) > 0:
				if dk.startswith("+"):
					dk = str(dk)[1:]
				else:
					dk = str(dk)
			if team and team in actionnetwork and player in actionnetwork[team] and prop in actionnetwork[team][player]:
				an = actionnetwork[team][player][prop]
				if prop == "k":
					if value not in actionnetwork[team][player][prop]:
						continue
					an = actionnetwork[team][player][prop][value]
				mgm = an.get("mgm", "-")
				br = an.get("betrivers", "-")
				cz = an.get("caesars", "-")
				pb = an.get("pointsbet", "-")

			pn = bs = "-"
			if team in bppLines and player in bppLines[team] and prop in bppLines[team][player]:
				if prop == "k":
					if value in bppLines[team][player]["k"]:
						pn = bppLines[team][player]["k"][value].get("pn", "-")
						bs = bppLines[team][player]["k"][value].get("bs", "-")
				else:
					pn = bppLines[team][player][prop]["0.5"].get("pn", "-")
					bs = bppLines[team][player][prop]["0.5"].get("bs", "-")

			bv = ""
			if prop == "hr" and team in bovada and player in bovada[team]:
				bv = bovada[team][player]["hr"]["1"]

			if prop == "hr" and team and team in kambiLines and player in kambiLines[team]:
				kambi = kambiLines[team][player]

			bet365 = evData[player]['bet365']
			if "/" in bet365 and int(bet365.split("/")[0]) > 0:
				bet365 = str(bet365)[1:]
			avg = evData[player]['ou']

			expectedHR = 2
			if dinger and game in bppExpectedHomers:
				expectedHR = bppExpectedHomers[game]

			starting = ""
			if team in lineups and player in lineups[team]:
				starting = "*"

			l = [ev, team.upper(), player.title(), starting, evData[player]["fanduel"], avg, bet365, dk, mgm, cz]
			if prop not in ["single", "double", "tb"]:
				l.extend([pb, br, pn, bs])
			if prop == "hr":
				l.insert(1, bet365ev)
			elif prop == "k":
				l.insert(1, value)
			if dinger:
				l.append(expectedHR)
			tab = "\t".join([str(x) for x in l])
			data.append((ev, player, tab, evData[player]))
			bet365data.append((bet365ev, player, tab, evData[player]))

		dt = datetime.strftime(datetime.now(), "%I:%M %p")
		output = f"\t\t\tUPD: {dt}\n\n"
		l = ["EV (AVG)", "Team", "Player", "IN", "FD", "AVG", "bet365", "DK", "MGM", "CZ"]
		if prop not in ["single", "double", "tb"]:
			l.extend(["PB", "BR", "PN", "BS"])
		if prop == "hr":
			l.insert(1, "EV (365)")
		elif prop == "k":
			l.insert(1, "Line")
		if dinger:
			l.append("xHR")
		output += "\t".join(l) + "\n"
		bet365output = output
		reddit = bet365reddit = ""
		for row in sorted(data, reverse=True):
			playerData = row[-1]
			line = f"{playerData['fanduel']} FD"
			if not playerData["fanduel"]:
				line = f"{playerData['other']} {playerData['otherBook']}"
			output += f"{row[-2]}\n"
			reddit += f"{playerData['ev']}% EV: {playerData.get('team', '').upper()} {row[1].title()} +{line} vs AVG {playerData['ou']}  \n"

		for row in sorted(bet365data, reverse=True):
			playerData = row[-1]
			line = f"{playerData['fanduel']} FD"
			if not playerData["fanduel"]:
				line = f"{playerData['other']} {playerData['otherBook']}"
			bet365output += f"{row[-2]}\n"
			bet365reddit += f"{playerData.get('bet365ev', '-')}% EV: {playerData.get('team', '').upper()} {row[1].title()} +{line} vs bet365 {playerData['bet365']}  \n"

		if prop == "hr":
			with open(f"{prefix}static/freebets/reddit_{prop}", "w") as fh:
				fh.write(reddit)

			with open(f"{prefix}static/freebets/reddit365_{prop}", "w") as fh:
				fh.write(bet365reddit)

			with open(f"{prefix}static/freebets/ev365_{prop}.csv", "w") as fh:
				fh.write(bet365output)

		with open(f"{prefix}static/freebets/ev_{prop}.csv", "w") as fh:
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

	if args.writeBV:
		writeBovada()

	if args.bv:
		checkBovada()

	if args.text:
		sendText("test")

	if args.update:
		writeFanduel()
		writeDK(args.date)
		#writeActionNetwork(args.date)
		writeKambi()

	if args.ml:
		writeActionNetworkML()

	if args.ev:
		writeEV(prop=args.prop, bookArg=args.book)

	if args.bpp:
		writeBPPHomers()

	if args.action:
		writeActionNetwork(args.date)

	if args.print:
		sortEV(args.dinger)

	if args.prop:
		#writeEV(dinger=dinger, date=args.date, avg=True, allArg=args.all, gameArg=args.game, teamArg=args.team, prop=args.prop, under=args.under, nocz=args.nocz, nobr=args.nobr, no365=args.no365, boost=args.boost, bookArg=args.book)
		sortEV(args.dinger)
	#write365()
	#writeActionNetwork()

	