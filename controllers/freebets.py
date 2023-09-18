
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
	{
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
	}
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
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/baseball/mlb/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	eventIds = {}
	for event in j["events"]:
		game = event["event"]["name"]
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]


	for game in eventIds:
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		for betOffer in j["betOffers"]:
			label = betOffer["criterion"]["label"]
			if not teamIds and "Handicap" in label:
				for row in betOffer["outcomes"]:
					team = convertFDTeam(row["label"].lower())
					teamIds[row["participantId"]] = team
					data[team] = {}

			elif "to hit a Home Run" in label:
				player = strip_accents(betOffer["outcomes"][0]["participant"])
				try:
					last, first = map(str, player.lower().split(", "))
					player = f"{first} {last}"
				except:
					player = player.lower()
				player = player.replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
				over = betOffer["outcomes"][0]["oddsAmerican"]
				under = betOffer["outcomes"][1]["oddsAmerican"]
				team = teamIds[betOffer["outcomes"][0]["eventParticipantId"]]
				data[team][player] = f"{over}/{under}"


	with open(f"{prefix}static/freebets/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

actionNetworkBookIds = {
	#68: "draftkings",
	1541: "draftkings",
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

def parsePlayer(player):
    return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "").replace("\u00a0", " ")

def writeActionNetwork(dateArg = None):
	#props = ["35_doubles", "33_hr", "37_strikeouts", "32_singles", "77_total_bases", "34_rbi"]
	props = ["33_hr", "37_strikeouts", "34_rbi"]

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
		url = f"https://api.actionnetwork.com/web/v1/leagues/8/props/core_bet_type_{actionProp}?bookIds=69,283,348,351,355,1541&date={date.replace('-', '')}"
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
			playerIds[row["id"]] = parsePlayer(row["full_name"])

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

				if book == "pointsbet" and oddData["grade"] == None:
					continue

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
					if prop == "hr" and book == "caesars" and odds[team][player][prop][book].count("/") == 1:
						odds[team][player][prop][book] = sp[0]


					if prop == "hr":
						sp = odds[team][player][prop][book].split("/")
						if len(sp) == 2 and int(sp[0]) < 0:
							del odds[team][player][prop][book]

	with open(f"{prefix}static/freebets/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def convertFDTeam(team):
	team = team.replace("pittsburgh pirates", "pit").replace("detroit tigers", "det").replace("cincinnati reds", "cin").replace("colorado rockies", "col").replace("minnesota twins", "min").replace("los angeles dodgers", "lad").replace("arizona diamondbacks", "ari").replace("oakland athletics", "oak").replace("philadelphia phillies", "phi").replace("san francisco giants", "sf").replace("kansas city royals", "kc").replace("san diego padres", "sd").replace("los angeles angels", "laa").replace("baltimore orioles", "bal").replace("washington nationals", "wsh").replace("miami marlins", "mia").replace("new york yankees", "nyy").replace("toronto blue jays", "tor").replace("seattle mariners", "sea").replace("boston red sox", "bos").replace("tampa bay rays", "tb").replace("new york mets", "nym").replace("milwaukee brewers", "mil").replace("st. louis cardinals", "stl").replace("atlanta braves", "atl").replace("texas rangers", "tex").replace("cleveland guardians", "cle").replace("chicago white sox", "chw").replace("chicago cubs", "chc").replace("houston astros", "hou")
	return team

def writeFanduel(team=None):
	apiKey = "FhMFpcPWXMeyZxOx"

	
	js = """
		const as = document.getElementsByTagName("a");
		const urls = {};
		for (a of as) {
			if (a.href.indexOf("/baseball/mlb") >= 0) {
				urls[a.href] = 1;
			}
		}
		console.log(Object.keys(urls));
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/baseball/mlb/tampa-bay-rays-@-baltimore-orioles-32640190",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/new-york-yankees-@-pittsburgh-pirates-32640199",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/boston-red-sox-@-toronto-blue-jays-32640191",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/cincinnati-reds-@-new-york-mets-32640184",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/atlanta-braves-@-miami-marlins-32640187",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/texas-rangers-@-cleveland-guardians-32640192",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/washington-nationals-@-milwaukee-brewers-32640188",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/houston-astros-@-kansas-city-royals-32640193",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/minnesota-twins-@-chicago-white-sox-32640194",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/philadelphia-phillies-@-st.-louis-cardinals-32640185",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/san-francisco-giants-@-colorado-rockies-32640189",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/detroit-tigers-@-los-angeles-angels-32640195",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/san-diego-padres-@-oakland-athletics-32640196",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/los-angeles-dodgers-@-seattle-mariners-32640198",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/chicago-cubs-@-arizona-diamondbacks-32640186"
]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = convertFDTeam(game.split("/")[-1][:-9].replace("-", " "))
		if game in lines:
			continue
		lines[game] = {}

		outfile = "out"

		for tab in ["pitcher", "hitter"]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}&tab={tab}-props"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue

			if data["attachments"]["events"][str(gameId)]["inPlay"]:
				continue

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()

				if marketName in ["to hit a home run", "to hit a double", "to hit a triple", "to hit a single", "to record a hit", "to record 2+ total bases", "to record an rbi", "to record a run"] or "- strikeouts" in marketName:
					prop = "hr"
					if "single" in marketName:
						prop = "single"
					elif "double" in marketName:
						prop = "double"
					elif "triple" in marketName:
						prop = "triple"
					elif "rbi" in marketName:
						prop = "rbi"
					elif "record a hit" in marketName:
						prop = "h"
					elif "strikeouts" in marketName:
						prop = "k"
					elif "total bases" in marketName:
						prop = "tb"
					elif "record a run" in marketName:
						prop = "r"

					for playerRow in data["attachments"]["markets"][market]["runners"]:
						player = playerRow["runnerName"].lower().replace(" over", "").replace(" under", "").replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
						handicap = ""
						try:
							odds = playerRow["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
							if prop == "k":
								t = playerRow['result']['type'][0].lower()
								if t == "o":
									handicap = f"{t}{playerRow['handicap']}"
						except:
							continue

						if player not in lines[game]:
							lines[game][player] = {}

						if prop != "k":
							lines[game][player][prop] = odds
						else:
							if handicap:
								lines[game][player][prop] = f"{handicap} {odds}"
							else:
								lines[game][player][prop] += f"/{odds}"


	
	with open(f"{prefix}static/baseballreference/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, avg=False, prop="hr"):

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
	if avg:
		evData[player]["ev"] = ev
	else:
		evData[player]["bet365ev"] = ev
		evData[player]["bet365Implied"] = implied

def devigger(evData, player="", bet365Odds="575/-900", finalOdds=630, dinger=False, avg=False, prop="hr", expectedHR=0):

	if dinger:
		# assuming 2hr/g = 40% FB @ 70% conversion
		if expectedHR:
			finalOdds = f"1={finalOdds};n={round(expectedHR, 4)}x"
		else:
			finalOdds = f"1={finalOdds};n=0.28x"

	outfile = f"out_{prop}"
	post = ["curl", 'https://crazyninjaodds.com/Public/sportsbooks/sportsbook_devigger.aspx', "-X", "POST", "-H", 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0', "-H", 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', "-H",'Accept-Language: en-US,en;q=0.5', "-H",'Accept-Encoding: gzip, deflate', "-H",'Content-Type: application/x-www-form-urlencoded', "-H",'Origin: https://crazyninjaodds.com', "-H",'Connection: keep-alive', "-H",'Referer: https://crazyninjaodds.com/Public/sportsbooks/sportsbook_devigger.aspx', "-H",'Cookie: ASP.NET_SessionId=ytnh3dbruzkf32qaweb3wio3; General=KellyMultiplier=.25&KellyBankRoll=1000&DevigMethodIndex=4&WorstCaseDevigMethod_Multiplicative=True&WorstCaseDevigMethod_Additive=True&WorstCaseDevigMethod_Power=True&WorstCaseDevigMethod_Shin=True&MultiplicativeWeight=0&AdditiveWeight=0&PowerWeight=0&ShinWeight=0&ShowEVColorIndicator=False&ShowDetailedDevigInfo=False&CopyToClipboard_Reddit=False&CopyToClipboard_DevigURL=True&CopyToClipboard_Reddit_IncludeDevigURL=False&ShowHedgeDevigMethod=False&UseMultilineTextbox=False', "-H",'Upgrade-Insecure-Requests: 1', "-H",'Pragma: no-cache', "-H",'Cache-Control: no-cache', "--data-raw", '__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=mmD0Dl1C6EgV%2BDqOi7tbA%2BnOlOxGkYdG1DQ0Dv9Don%2FcQnhqZ977VWb3vTBqmdT3S%2Fng2DngDHu87Smxc5GuAeDG%2FPE8ol%2FtlxKl3NuULU42P3Y7PwndnRpvWouYQTQBejSCEBuxZDYcBxxi5lVFeP0EPAhUqWsNj0TpzBsd2w9qU7GPmdrYtts8bFB9SPbdWnU33UQOrXf%2FP2PsekX%2FtNLaqtv0EQCef%2F11tDhlGestDGZNSzI4H962zIGo6aIThiN7O6l%2BJsymp2Bowj%2BYrhbDAZz90Fi0tMxzPaFMKwnsTV2GTc58vxJ8MwN75qvEl7aWbao34JBR2BNtixrALDbrpzfuqZsQafZCxqeFpxsv6i343etGvHHjFdA2B%2F%2BldeU2hLuslsKR98VxHHUNpIZdXW%2FBPxcBGvKiah9iaglqHRNJbO9%2FgZRFLH4Jlz42uPBjEeKOMRMHqLOVFk8Alt7ZvDa%2BYAVKj3ke7sFTXiLqCSP9GFcrhsdFh3%2FlyMK1KQa2uO9rs3y1bb6PamvzPY78KK4MvA6Wppvxw65ICHypxw5feEqIpv0WbVPHzlyohKf1Bomt40NH6dlVnMK5D0LHDWRT49k5%2FB4NojdQYxcAibx2h%2BdO46udYv%2FAFF53kxSeQMtKqDwkSqqSgYBJT6Q1qO7cyU61qfVtX1IkxylJws%2BRDL818HSeUL5sUqpS1YO1BN5YYZPlwtGvOnUopGBdBZ3lPcOJKarZI5b4oj2ukSbbR1NAVgio0Fx9fZlkst6Zp4JszRup%2BxQipCBpjclBHCeuQc0xQf9bpeAU7jj%2BpS2lrK%2FfGp6doUd1psrdhWuuXZn2H96wlKpOtJQFjXNmDV1e7yQ4Xg1N9IKsVyZsL9aIZbx91qHjbW5p5bYLfV6WgTGl748OFWYYQXRgLv9p7gLI6zIkpOW%2FfC1YZP%2FRAmFXeXdT1REmgMR1A6I%2Bwu4w3Gt6VVDDVlkXhB2gF6ibfrWKRtjWCmbo8rI%2F2oSBOTBhpcMQ2ZxYJyHuRFQUSP63pyeRVw25jQZG2o%2FuAwHAKZuCR6i4DMylsVmd3eDzdLXzU4FdSQLs41xuS51F%2B0%2BbOhTyLhACABpOgn%2FpFdiA9yAVh9g7eMcYWrWDrwuHDCUbCvcWmdWGdlYlRcOGtd5SYegC06AiIRGzQNmYmhMFtdssQ8MThQI7EJNf9INitgKG0j%2F0ucxSCBZ%2BhwyzstbTPjvZKeFKr%2FSwWlqOkGAmFpMUeQjaGd9mRBeKNSlQql2cEs5UmHN8asvDPZJ%2BIHBg1Bgz5Uvj9v%2B7D14ujxugjATPgJXLBO9nUcS3UM1AJBf8FpRFHhTljZNKjTZdOPam%2FaZeV2hQU%2FQuCASAN5SgD2dFlTr4xFU6XkzKTRtRN%2FrFc21LqJHBe1V4AGuQ5sA%2B4ClPpVyKzjZkImOoqeLs1RFNfEBF1du2mx08iSQZQR%2F8IHEkcIIJnB%2BJO8doPyIDYlTs0D5TcuEV19y6%2Fuz%2BhGopH3VWyXZF3995CdXYXoaXeQnjCYU3LohkMWEMKYzFmI6u2dN0ZC6hBRgmOlAMLRHAB9Tv%2BuozseQYeuAxK%2BFpcGy73FpDKbIeoOkkm8xMBNNUWLwdP9tm8XQ7yGUgJEABRkZLC8cbe5z8Jt1202t3YO4%2BUFxusPMu4L1s1lX%2B%2F%2F2mJhpboAi9QHZrtGHV0luWzBfFe0PV51KhmWN56NtbLqo2MHVTSb0wlf%2B1gVB9tAkNG31ioJIjUfhtdLK6nbjW6GKBiwGAIsYcYl8by0uLeN2%2BaeSru8WRyVle%2BqXv83Cap35tdZg89vNnHqEbBba950MpN6cEmwHUViyP88XO6VctlhyhKpjEL%2BYI0NG1IoU1Mz%2BFmQcRck1fc2DYJdoUbGoOAIYiFlpKXwUMoeIlQNX5KEEKo50CshCUlwO0TFGCmaPlvuIPuVkR8cCxzdouuC6Tr5JHuENmRNbvkTcVwCSDPue04tjFPz83&__VIEWSTATEGENERATOR=75A63123&__EVENTVALIDATION=Zr5waX29KFtDx%2B%2BTw51Tt8HB5B0GTcdcqlawxLCwmhEYuz7ZzMAfiq2Rax%2FjuEFCG8QtUbvGvUNRuKP%2Fzh5HI%2FlUqyw0KbImM%2FIYe%2FsBbhqvqP3Jm6SmAo6buwGM51cAvXCGtI5DEO%2FLEiPuQyvg9nPgJI4WbaoK8%2B%2BXxqVcC8nM%2BiZkP6ny9CpojqCqCXwtRZa87knXf6wGnTJJ3fmLZoWSXHqaSQfU0a2j0hXL%2B7G4IFUkenNSxacAhym7pIBIbkX2OSWDpPWY242nH1mnKjQCekp3fUJaWPiTf%2F9vZlI3CHez7M%2B1L7q9ltWhynNHCZXkV5BX5UAzxL0W%2FFo6QiPTi0EPu7ckqmYYaQVey0K%2FWde5nDU%2FgiMBjD9u9VFxNslbqytjT4Xn8H5659GVxHOZCGke3N2U1%2FEasCInKUrq5pURmsTIlmqpgXpaJKW1JI1edPzr4JsVosHsYC7iTyoHNNX2lVLtwxnOWCmxsMuBUbW2T%2BfGd62SQovw0rDpBe8wvZkG1075LdVuzcOI2%2B8b%2BrEqan2bTJacf%2BQWcXB1Wba9v%2Bha4ekXUflA%2FT9uQofbNGLO3%2Fk%2FYbN2P8miLiDflzT55LvqRJ0b4m8L51kKoPcubP4sAtAZiSTgJ7XZCWpL14PQCvh%2FLA0QyGhlPvRFkUhqrc90HLjlZAeYIuNAKQ306Q0gXT5CbP8xNtxzSzORR3gtjDBHQ46YfO5VG0XOT9un%2BA0kfmCun43YrozvVcpILbJwOjbFtA4EbiIbvAoDn09Swo3D%2BtKyIbveoDyM%2FWDpTmFb2UYD4dSvooDffp%2FeSljH89b2L3MSSBP3sS7xDLj2rGP1GeXJr2%2F%2BVyt%2B8Xm5BGt%2FgJiu9T1ND0jAlILHuG%2FyLZxWkPlpiPO0R6GnLS%2B7aztX2T1sBxmqr874atOJKg77T4NMcSC%2FClMoNnFI2YS%2FEbK92IadQNpFulWIcRYKwMPN7RBmi1kV2oUpmCdD%2F7Mv95Uy%2BlhI05jSt2sICSlZvHz5D9QaFvPHnhH%2FL%2BjZpEIl09JPgyeFX5h2Gb5iR%2F6TMmx94zGblnRV4x2iMNmnm7T98Ve3sRcd3LXLxXO92tW9kXvxtCD7rSnZ5du1SmJnWwE1qwfsTEeE671V%2BxAIrAhTUWBpNHSF8W4iEvN2swA22wM2SemIzsmLXYJUCXIwHZ3bo3Kgm2Qm93nJSP%2BpvfFQC5W%2BAsQuaxxgIh7FH2yIUXWUzokKwHcrsAhmGMkJM64o6OFFRFKJwVoXKThwERuuU7u2Bi2x86%2FwKEkvdMLa6cemCqieEWRzTR9WT0qIUaPn%2BhLunuW5%2FnSernkf7Qhn51ukrRK0pdZv6kZESHyx4BsxoA8L5oWGNCvZJajHI304I4kFIM0sKP3CHpPZ3iq79qEGo%2FUl5JnuXHN9HF23INR2HrEjR%2BUgMdJfoehGly3KNtQw%2F1NOnJG7TRC8Sj5NE%2FTrbjzH3cLqL1grHOI2PS45hoRD1Q%3D%3D&TextBoxKellyMultiplier=.25&TextBoxBankRoll=1000&RadioButtonListDevigMethod=worstcase&TextBoxLegOdds='+str(bet365Odds)+'&TextBoxFinalOdds='+str(finalOdds)+'&TextBoxCorrelation=0&TextBoxBoost=0%25&Boost=RadioButtonBoostProfit&DropDownListDailyFantasy=0&ButtonCalculate=Calculate&Text1=https%3A%2F%2Fcrazyninjaodds.com%2FPublic%2Fsportsbooks%2Fsportsbook_devigger.aspx%3Fautofill%3D1%26LegOdds%3DAVG%28350%252c275%252c300%252c350%252c400%29%26FinalOdds%3D312&CheckBoxListWorstCaseMethodSettings%240=The+Multiplicative%2FNormalization%2FTraditional+Method&CheckBoxListWorstCaseMethodSettings%241=The+Additive+Method&CheckBoxListWorstCaseMethodSettings%242=The+Power+Method&CheckBoxListWorstCaseMethodSettings%243=The+Shin+Method&TextBoxMultiplicativeWeight=0%25&TextBoxAdditiveWeight=0%25&TextBoxPowerWeight=0%25&TextBoxShinWeight=0%25&CheckBoxListCopyToClipboardSettings%240=devigurl', "-o", outfile]

	time.sleep(0.3)
	call(post)

	soup = BS(open(outfile, 'rb').read(), "lxml")
	try:
		output = soup.find("span", id="LabelOutput").text
	except:
		return

	m = re.search(r".* Fair Value = (.*?) \((.*?)\)Summary\; EV% = (.*?)%", output)
	if m:
		fairVal = m.group(1)
		implied = m.group(2)
		ev = m.group(3)
		if player not in evData:
			evData[player] = {}
		evData[player]["fairVal"] = fairVal
		evData[player]["implied"] = implied
		if avg:
			evData[player]["ev"] = ev
		else:
			evData[player]["bet365ev"] = ev
			evData[player]["bet365Implied"] = implied

def write365():
	js = """
	{
		let data = {};
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
		for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
			if (div.classList.contains("src-FixtureSubGroup_Closed")) {
				div.click();
			}
			let playerList = [];
			for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
				let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(". ", "").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
				let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];

				if (team === "la angels") {
					team = "laa";
				} else if (team === "la dodgers") {
					team = "lad";
				} else if (team === "chi white sox") {
					team = "chw";
				} else if (team === "chi cubs") {
					team = "chc";
				} else if (team === "was nationals") {
					team = "wsh";
				} else if (team === "ny mets") {
					team = "nym";
				} else if (team === "ny yankees") {
					team = "nyy";
				} else {
					team = team.split(" ")[0];
				}
				
				if (data[team] === undefined) {
					data[team] = {};
				}
				data[team][player] = "";
				playerList.push([team, player]);
			}

			let idx = 0;
			for (playerDiv of div.getElementsByClassName("gl-Market")[1].getElementsByClassName("gl-ParticipantCenteredStacked")) {
				let team = playerList[idx][0];
				let player = playerList[idx][1];

				let line = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Handicap")[0].innerText;
				let odds = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
				if (title === "pitcher strikeouts") {
					data[team][player] = line+" "+odds;
				} else {
					data[team][player] = odds;
				}
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

def writeEV(dinger=False, date=None, useDK=False, avg=False, allArg=False, gameArg="", teamArg="", strikeouts=False, prop="hr", under=False, nocz=False, nobr=False, no365=False, boost=None, bookArg="fd"):

	if not date:
		date = str(datetime.now())[:10]

	if not boost:
		boost = 1

	if prop != "hr":
		with open(f"{prefix}static/mlbprops/bet365_{prop}s.json") as fh:
			bet365Lines = json.load(fh)
	else:
		with open(f"{prefix}static/mlbprops/bet365.json") as fh:
			bet365Lines = json.load(fh)


	with open(f"{prefix}static/baseballreference/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/freebets/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/freebets/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/freebets/bovada.json") as fh:
		bovada = json.load(fh)

	with open(f"{prefix}static/mlb/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/mlb/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/mlb/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/mlb/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/mlb/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/mlb/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/freebets/bppExpectedHomers.json") as fh:
		bppExpectedHomers = json.load(fh)

	with open(f"{prefix}static/mlbprops/ev_{prop}.json") as fh:
		evData = json.load(fh)

	with open(f"{prefix}static/mlbprops/bpp.json") as fh:
		bpp = json.load(fh)

	if not teamArg and not gameArg:
		evData = {}
	elif teamArg:
		for player in evData.copy():
			if teamArg in evData[player]["game"]:
				del evData[player]
	elif gameArg:
		for player in evData.copy():
			if evData[player]["game"] == gameArg:
				del evData[player]

	for game in fdLines:
		if gameArg and game != gameArg:
			continue
		if teamArg and teamArg not in game:
			continue
		for player in fdLines[game]:
			if prop not in fdLines[game][player]:
				continue
			team1, team2 = map(str, game.split(" @ "))
			team = ""
			if not useDK:
				if team1 in bet365Lines and player in bet365Lines[team1]:
					team = team1
				elif team2 in bet365Lines and player in bet365Lines[team2]:
					team = team2
				else:
					if team1 in actionnetwork and player in actionnetwork[team1]:
						team = team1
					elif team2 in actionnetwork and player in actionnetwork[team2]:
						team = team2
					else:
						continue

			fdLine = fdLines[game][player][prop]
			handicap = ""
			if prop in "k":
				handicap = float(fdLine.split(" ")[0][1:])
				if under:
					fdLine = int(fdLine.split(" ")[1].split("/")[1])
				else:
					fdLine = int(fdLine.split(" ")[1].split("/")[0])

			dk = ""
			dkLine = 0
			dkProp = prop.replace("single", "1b").replace("double", "2b")
			if game in dkLines and prop in dkLines[game] and player in dkLines[game][prop]:
				dk = dkLines[game][prop][player].split(" ")[-1]
			elif useDK:
				continue

			mgm = pb = cz = br = kambi = ""
			if team in actionnetwork and player in actionnetwork[team] and prop in actionnetwork[team][player]:
				data = actionnetwork[team][player][prop]
				if prop == "k":
					data = actionnetwork[team][player][prop].get(str(handicap), {})
				mgm = data.get("mgm", "-")
				br = data.get("betrivers", "-")
				cz = data.get("caesars", "-")
				pb = data.get("pointsbet", "-")

				if dk == "":
					dk = data.get("draftkings", "-")

			pn = bs = ""
			if prop == "k" and team in bpp and player in bpp[team] and "k" in bpp[team][player] and str(handicap) in bpp[team][player]["k"]:
				pn = bpp[team][player]["k"][str(handicap)].get("pn", "-")
				bs = bpp[team][player]["k"][str(handicap)].get("bs", "-")
			elif prop == "hr" and team in bpp and player in bpp[team] and "hr" in bpp[team][player]:
				pn = bpp[team][player]["hr"]["0.5"].get("pn", "-")
				bs = bpp[team][player]["hr"]["0.5"].get("bs", "-")

			if prop == "hr" and game in pnLines and "hr" in pnLines[game] and player in pnLines[game]["hr"]:
				pn = pnLines[game]["hr"][player].split(" ")[-1]

			if prop == "hr" and game in pbLines and "hr" in pbLines[game] and player in pbLines[game]["hr"]:
				pb = pbLines[game]["hr"][player].split(" ")[-1]

			if prop == "hr" and game in czLines and "hr" in czLines[game] and player in czLines[game]["hr"]:
				cz = czLines[game]["hr"][player].split(" ")[-1]

			if prop == "hr" and game in mgmLines and "hr" in mgmLines[game] and player in mgmLines[game]["hr"]:
				mgm = mgmLines[game]["hr"][player].split(" ")[-1]

			bv = ""
			if prop == "hr" and game in bvLines and "hr" in bvLines[game] and player in bvLines[game]["hr"]:
				bv = bvLines[game]["hr"][player].split(" ")[-1]

			if team not in bet365Lines or player not in bet365Lines[team]:
				bet365ou = ""
			else:
				bet365ou = bet365Lines[team][player]
				if prop == "k":
					if bet365ou.split(" ")[0] != str(handicap):
						bet365ou = ""
					else:
						bet365ou = bet365ou.split(" ")[-1]

			if team and team in kambiLines and player in kambiLines[team]:
				kambi = kambiLines[team][player]

			line = fdLine
			l = [dk, bet365ou, mgm, pb]

			avgOver = []
			avgUnder = []
			if prop in ["single", "double"]:
				l = [dk, bet365ou, mgm, pb]
				if not nocz:
					l.append(cz)
				if not nobr:
					l.append(br.split("/")[0])
			elif prop == "k":
				l = [dk, bet365ou, mgm, pb, pn, bs]
				if not nocz:
					l.append(cz)
				if not nobr:
					l.append(br.split("/")[0])
			if allArg:
				l = [dk, bet365ou, mgm, pb, pn.split("/")[0], bs, bv]
				if not nocz:
					l.append(cz)
				if not nobr:
					l.append(br.split("/")[0])

			evBook = "fd"
			if bookArg == "dk":
				evBook = "dk"
				line = dk.split("/")[0]
				l[0] = str(fdLine)

				if line == "-":
					continue
			elif bookArg == "cz":
				evBook = "cz"
				line = cz
				l[7] = str(fdLine)

				if line == "-":
					continue

			for book in l:
				if book and book != "-":
					avgOver.append(convertDecOdds(int(book.split("/")[0])))
					if "/" in book and book.split("/")[1] != "0":
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

			if under:
				ou = f"{avgUnder}/{avgOver}"
			else:
				ou = f"{avgOver}/{avgUnder}"

			if ou.startswith("-/") or ou.endswith("/-"):
				continue


			if not line:
				continue

			line = convertAmericanOdds(1 + (convertDecOdds(int(line)) - 1) * boost)

			if player in evData:
				continue
			if True or dinger or prop == "k" or line > sharpUnderdog:
				pass
				if useDK:
					bet365ou = ou = f"{sharpUnderdog}/{dkLines[game][player][prop]['under']}"

				expectedHR = 0.28
				if game in bppExpectedHomers and dinger:
					expectedHR = .70 * (bppExpectedHomers[game] / 5)

				if prop == "hr" and bet365ou and not no365:
					devig(evData, player, bet365ou, int(line))
					#devigger(evData, player, bet365ou, line, dinger)
				devig(evData, player, ou, int(line), avg=True, prop=prop)
				#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
				if player not in evData:
					print(player)
					continue
				if float(evData[player]["ev"]) > 0:
					print(player, evData[player]["ev"], int(line), ou)
				evData[player]["pitcher"] = strikeouts
				evData[player]["game"] = game
				evData[player]["book"] = bookArg
				evData[player]["team"] = team
				evData[player]["ou"] = ou
				evData[player]["odds"] = l
				evData[player]["line"] = line
				evData[player]["under"] = under
				evData[player]["bet365"] = bet365ou
				evData[player]["fanduel"] = str(fdLines[game][player][prop]).split(" ")[-1]
				evData[player]["dk"] = dk
				evData[player]["value"] = str(handicap)

		with open(f"{prefix}static/mlbprops/ev_{prop}.json", "w") as fh:
			json.dump(evData, fh, indent=4)

	with open(f"{prefix}static/mlbprops/ev_{prop}.json", "w") as fh:
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

	with open(f"{prefix}static/mlb/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/mlb/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/mlb/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/mlb/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/mlb/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/freebets/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/freebets/bovada.json") as fh:
		bovada = json.load(fh)

	with open(f"{prefix}static/freebets/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/freebets/bppExpectedHomers.json") as fh:
		bppExpectedHomers = json.load(fh)

	for prop in ["hr", "k", "single", "double", "tb", "rbi"]:
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

			if prop == "hr":
				if game in pnLines and "hr" in pnLines[game] and player in pnLines[game]["hr"]:
					pn = pnLines[game]["hr"][player].split(" ")[-1]

				if game in pbLines and "hr" in pbLines[game] and player in pbLines[game]["hr"]:
					pb = pbLines[game]["hr"][player].split(" ")[-1]

				if game in mgmLines and "hr" in mgmLines[game] and player in mgmLines[game]["hr"]:
					mgm = mgmLines[game]["hr"][player].split(" ")[-1]

				if game in bvLines and "hr" in bvLines[game] and player in bvLines[game]["hr"]:
					bv = bvLines[game]["hr"][player].split(" ")[-1].replace("+", "")

				if team and team in kambiLines and player in kambiLines[team]:
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
				l.extend([pb, br, pn, bs, bv])
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
			l.extend(["PB", "BR", "PN", "BS", "BV"])
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
	parser.add_argument("--dk", action="store_true", help="Draftkings")
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

	plays = [("matt wallner", 390, "min"), ("mj melendez", 520, "kc"), ("aaron judge", 320, "nyy"), ("jordan lawlar", 900, "ari"), ("ketel marte", 680, "ari")]

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

	if args.kambi:
		writeKambi()

	if args.writeBV:
		writeBovada()

	if args.bv:
		checkBovada()

	if args.text:
		sendText("test")

	if args.update:
		writeFanduel(args.team)
		writeActionNetwork(args.date)
		#writeKambi()

	if args.ml:
		writeActionNetworkML()

	if args.ev:
		writeEV(dinger=dinger, date=args.date, useDK=args.dk, avg=args.avg, allArg=args.all, gameArg=args.game, strikeouts=args.k, prop=args.prop, nocz=args.nocz, boost=args.boost, bookArg=args.book)

	if args.bpp:
		writeBPPHomers()

	if args.action:
		writeActionNetwork(args.date)

	if args.print:
		sortEV(args.dinger)

	if args.prop:
		writeEV(dinger=dinger, date=args.date, avg=True, allArg=args.all, gameArg=args.game, teamArg=args.team, prop=args.prop, under=args.under, nocz=args.nocz, nobr=args.nobr, no365=args.no365, boost=args.boost, bookArg=args.book)
		sortEV(args.dinger)
	#write365()
	#writeActionNetwork()

	data = {}
	#devigger(data, player="dean kremer", bet365Odds="-115/-115", finalOdds="-128")
	devig(data, player="judge", ou="-110/-120", finalOdds=-105, avg=True)
	#print(data)

	with open("static/freebets/passing_boost.json") as fh:
		boost = json.load(fh)

	with open("passing_boost.json") as fh:
		boostOdds = json.load(fh)

	data = []
	for player in boost:
		data.append((float(boost[player]["bet365ev"]), player, boost[player]))

	output = "\t".join(["EV%", "Player", "Prop", "FD", "Bet365", "DK", "MGM", "Kambi", "CZ"])+"\n"
	for row in sorted(data, reverse=True):
		player = row[1].replace("_"+row[-1]["prop"], "")
		prop = row[-1]["prop"]
		arr = [str(row[0]), player.title(), prop, str(row[-1]['fd']*1.25)]
		for book in ["bet365", "draftkings", "mgm", "kambi", "caesars"]:
			if book in boostOdds[player] and prop in boostOdds[player][book]:
				arr.append(boostOdds[player][book][prop])
			else:
				arr.append("-")
		output += "\t".join(arr)+"\n"

	with open("static/freebets/passing_boost.csv", "w") as fh:
		fh.write(output)

	summaryOutput = {}
	if args.plays:
		with open(f"static/mlbprops/ev_hr.json") as fh:
			ev = json.load(fh)

		with open(f"static/freebets/bppExpectedHomers.json") as fh:
			bppExpectedHomers = json.load(fh)
		
		output = []
		for player, odds, team in plays:
			if player not in ev:
				output.append(f"{player} taken={odds}")
				continue
			currOdds = int(ev[player]["fanduel"])
			game = ev[player]["game"]
			ou = ev[player]["ou"]
			currEv = ev[player]["ev"]

			if currOdds != odds:
				data = {}
				expectedHR = 0.28
				if game in bppExpectedHomers and args.dinger:
					expectedHR = .70 * (bppExpectedHomers[game] / 5)

				devig(data, player, ou, odds, avg=True)
				if data:
					currEv = data[player]["ev"]

			output.append(f"{player} taken={odds} curr={currOdds} ev={currEv}")

			if game not in output:
				summaryOutput[game] = []
			summaryOutput[game].append((float(currEv), player, odds))
		print("\n".join(output))

	if args.summary:
		with open(f"static/mlbprops/ev_hr.json") as fh:
			ev = json.load(fh)
		for player in ev:
			if player in [p[0] for p in plays]:
				continue
			if ev[player]["game"] not in summaryOutput:
				summaryOutput[ev[player]["game"]] = []
			summaryOutput[ev[player]["game"]].append((float(ev[player]["ev"]), player, ev[player]["fanduel"]))
		for game in summaryOutput:
			summaryOutput[game] = sorted(summaryOutput[game], reverse=True)
			out = game
			for o in summaryOutput[game][:3]:
				out += " "
				if o[1] in [p[0] for p in plays]:
					out += "**"
				out += f"+{o[-1]} {o[1].title()} ({o[0]}%)"
				if o[1] in [p[0] for p in plays]:
					out += "**"
				out += "."
			print(out+"\n")
