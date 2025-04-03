
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
import csv
from glob import glob
import nodriver as uc
from twilio.rest import Client

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

def convertFDTeam(team):
	team = team.lower().replace("pittsburgh pirates", "pit").replace("detroit tigers", "det").replace("cincinnati reds", "cin").replace("colorado rockies", "col").replace("minnesota twins", "min").replace("los angeles dodgers", "lad").replace("arizona diamondbacks", "ari").replace("oakland athletics", "ath").replace("philadelphia phillies", "phi").replace("san francisco giants", "sf").replace("kansas city royals", "kc").replace("san diego padres", "sd").replace("los angeles angels", "laa").replace("baltimore orioles", "bal").replace("washington nationals", "wsh").replace("miami marlins", "mia").replace("new york yankees", "nyy").replace("toronto blue jays", "tor").replace("seattle mariners", "sea").replace("boston red sox", "bos").replace("tampa bay rays", "tb").replace("new york mets", "nym").replace("milwaukee brewers", "mil").replace("st. louis cardinals", "stl").replace("atlanta braves", "atl").replace("texas rangers", "tex").replace("cleveland guardians", "cle").replace("chicago white sox", "chw").replace("chicago cubs", "chc").replace("houston astros", "hou").replace("athletics", "ath")
	return team

def convertTeam(team):
	team = team.lower().replace(".", "")
	t = team.split(" ")[0][:3]
	if t == "was":
		t = "wsh"
	elif t == "san":
		t = "sf"
	elif t == "tam":
		t = "tb"
	elif t == "kan":
		t = "kc"
	elif "yankees" in team:
		t = "nyy"
	elif "mets" in team:
		t = "nym"
	elif "angels" in team:
		t = "laa"
	elif "dodgers" in team:
		t = "lad"
	elif "cubs" in team:
		t = "chc"
	elif "whitesox" in team or "white sox" in team:
		t = "chw"
	return t

def getSuffix(num):
	if num >= 11 and num <= 13:
		return "th"
	elif num % 10 == 1:
		return "st"
	elif num % 10 == 2:
		return "nd"
	elif num % 10 == 3:
		return "rd"
	return "th"

def convertRankingsProp(prop):
	if prop in ["r"]:
		return "er"
	elif prop == "rbi":
		return "opp_rbi"
	elif prop == "er":
		return "r"
	elif prop == "single":
		return "opp_1b"
	elif prop == "double":
		return "opp_2b"
	elif prop == "sb":
		return "opp_sb"
	elif prop == "tb":
		return "opp_tb"
	elif prop == "k":
		return "so"
	elif prop == "bb":
		return "bb_allowed"
	elif prop == "bb_allowed":
		return "bb"
	elif prop == "hr_allowed":
		return "hr"
	elif prop == "hr":
		return "hr_allowed"
	elif prop == "h_allowed":
		return "h"
	elif prop == "h":
		return "h_allowed"
	elif prop == "h+r+rbi_allowed":
		return "h+r+rbi"
	elif prop == "h+r+rbi":
		return "h+r+rbi_allowed"
	return prop

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

def writeDaily():
	with open(f"{prefix}static/mlb/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/mlb/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/mlb/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/mlb/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/mlb/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/mlb/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/mlb/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/mlb/espn.json") as fh:
		espnLines = json.load(fh)

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
	with open(f"static/mlb/lines/{date}.json", "w") as fh:
		json.dump(lines, fh)


async def writeLeftRight(year):
	if not year:
		year = datetime.now().year - 1

	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	playerTeams = nested_dict()
	for team in roster:
		for player in roster[team]:
			if player not in playerTeams:
				playerTeams[player] = []
			playerTeams[player].append(team)

	url = f"https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=1&startDate=2024-03-01&endDate=2024-11-01&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=1&players=&filter=PA%7Cgt%7C10&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pg=0"

	leftRightSplits = nested_dict()

	for throws in ["LHP", "RHP"]:
		with open(f"Splits Leaderboard Data vs {throws}.csv", newline="") as fh:
			reader = csv.reader(fh)

			headers = []
			for idx, row in enumerate(reader):
				if idx == 0:
					headers = [x.lower() for x in row]
				else:
					player = parsePlayer(row[1])
					if "Tm" in row[2]:
						teams = playerTeams.get(player)
						if not teams:
							team = row[2].lower()
						else:
							team = teams[0]
					else:
						team = convertMLBTeam(row[2])

					for hdr, col in zip(headers, row):
						try:
							leftRightSplits[team][player][year][throws][f"{hdr}"] = int(col)
						except:
							try:
								leftRightSplits[team][player][year][throws][f"{hdr}"] = float(col)
							except:
								leftRightSplits[team][player][year][throws][f"{hdr}"] = col

	with open(f"static/mlb/leftRightSplits.json") as fh:
		data = json.load(fh)
	merge_dicts(data, leftRightSplits, forceReplace=True)

	for team in data:
		for player in data[team]:
			data[team][player]["total"] = {}

			for year in data[team][player]:
				if year == "total":
					continue
				for LR in data[team][player][year]:
					for key in data[team][player][year][LR]:
						if key in ["season", "name", "tm", "playerId", "avg"]:
							continue
						val = data[team][player][year][LR][key]
						if key in data[team][player]["total"]:
							data[team][player]["total"][key] += val
						else:
							data[team][player]["total"][key] = val

	with open(f"static/mlb/leftRightSplits.json", "w") as fh:
		json.dump(data, fh, indent=4)

def writeLeftRightSplits():

	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	playerTeams = nested_dict()
	for team in roster:
		for player in roster[team]:
			if player not in playerTeams:
				playerTeams[player] = []
			playerTeams[player].append(team)

	url = "https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=1&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=1&startDate=2024-03-01&endDate=2024-11-01&players=&filter=PA%7Cgt%7C10&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pg=0"

	leftRightSplits = nested_dict()

	for throws in ["LHP", "RHP"]:
		with open(f"Splits Leaderboard Data vs {throws}.csv", newline="") as fh:
			reader = csv.reader(fh)

			headers = []
			for idx, row in enumerate(reader):
				if idx == 0:
					headers = [x.lower() for x in row]
				else:
					player = parsePlayer(row[1])
					if "Tm" in row[2]:
						teams = playerTeams.get(player)
						if not teams:
							continue
						team = teams[0]
					else:
						team = convertMLBTeam(row[2])

					for hdr, col in zip(headers, row):
						try:
							leftRightSplits[team][player][throws][f"{hdr}"] = float(col)
						except:
							leftRightSplits[team][player][throws][f"{hdr}"] = col

	with open(f"static/mlb/leftRightSplits.json", "w") as fh:
		json.dump(leftRightSplits, fh, indent=4)

def writeESPN():
	js = """

	{
		function convertTeam(team) {
			team = team.toLowerCase();
			return team;
		}

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			if (player == "joquavious marks") {
				return "woody marks";
			}
			return player;
		}

		const data = {};
		let status = "";

		async function readPage(game) {
			for (tab of document.querySelectorAll("button[data-testid='tablist-carousel-tab']")) {
				if (tab.innerText == "Player Props") {
					tab.click();
					break;
				}
			}
			while (!window.location.href.includes("player_props")) {
				await new Promise(resolve => setTimeout(resolve, 500));
			}

			await new Promise(resolve => setTimeout(resolve, 3000));

			let players = {};
			for (detail of document.querySelectorAll("details")) {
				let prop = detail.querySelector("h2").innerText.toLowerCase();

				if (prop == "player total home runs hit") {
					prop = "hr";
				} else if (prop == "first batter to record a hit") {
					prop = "";
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

				data[game]["hr"] = {};

				let btns = detail.querySelectorAll("button");
				if (prop == "hr") {
					for (i = 0; i < btns.length; i += 2) {
						let player = parsePlayer(btns[i].parentElement.parentElement.previousSibling.innerText.toLowerCase());
						let sp = player.split(" ");
						player = sp[0][0];
						sp.shift();
						player += " "+sp.join(" ");
						let ou = btns[i].querySelectorAll("span")[1].innerText+"/"+btns[i+1].querySelectorAll("span")[1].innerText;
						players[player] = ou;
					}
				} else {
					for (btn of btns) {
						let player = parsePlayer(btn.querySelector("span").innerText);
						let sp = player.split(" ");
						let p = sp[0][0];
						sp.shift();
						p += " "+sp.join(" ");
						if (players[p]) {
							data[game]["hr"][player] = players[p];
						}
					}
				}
			}
			status = "done";
		}

		async function main() {
			while (true) {
				for (div of document.querySelector("section").querySelectorAll("article")) {
					if (!div.innerText.includes("Today")) {
						continue;
					}
					let btns = div.querySelectorAll("button[data-testid=team-name]");
					let awayTeam = convertTeam(btns[0].querySelector(".text-primary").innerText.split(" ")[0]);
					let homeTeam = convertTeam(btns[1].querySelector(".text-primary").innerText.split(" ")[0]);
					let game = awayTeam + " @ " + homeTeam;

					if (data[game]) {
						continue;
					}
					
					data[game] = {};

					btns[0].click();

					while (!window.location.href.includes("event")) {
						await new Promise(resolve => setTimeout(resolve, 500));
					}

					await new Promise(resolve => setTimeout(resolve, 5000));

					status = "";
					readPage(game);

					while (status != "done") {
						await new Promise(resolve => setTimeout(resolve, 2000));
					}

					document.querySelector("a[aria-labelledby=MLB-9]").click();

					await new Promise(resolve => setTimeout(resolve, 5000));

					console.log(data);
					//testing
					//break;
				}
				break;
			}
			console.log(data);
		}

		main();
	}
"""

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

	#props = ["33_hr", "37_strikeouts", "34_rbi"]
	props = ["33_hr"]

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

		try:
			with open(path) as fh:
				j = json.load(fh)
		except:
			continue

		if "markets" not in j:
			return
		try:
			market = j["markets"][0]
		except:
			continue

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

	with open(f"{prefix}static/mlb/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)


def writeCZ(date=None):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/baseball/events/schedule?competitionIds=04f90892-3afa-4e84-acce-5b89f151063d"
	outfile = "mlboutCZ"
	cookie = ""
	with open("token") as fh:
		cookie = fh.read()
	os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"]:
		if str(datetime.strptime(event["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			#continue
			pass
		games.append(event["id"])

	#games = ["a81f213e-e391-4c9a-bd6f-60cc198174aa"]

	res = {}
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/events/{gameId}"
		time.sleep(0.2)
		os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		#print(data["name"], data["startTime"])

		if str(datetime.strptime(data["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			#continue
			pass

		game = convertFDTeam(data["name"].lower().replace("|", "").replace(" at ", " @ "))
		if game in res:
			continue
		res[game] = {}

		for market in data["markets"]:
			if "name" not in market:
				continue

			if market["active"] == False:
				continue
			prop = market["name"].lower().replace("|", "").split(" (")[0]

			prefix = player = ""
			if "1st 3 innings" in prop:
				prefix = "f3_"
			elif "1st 5 innings" in prop:
				prefix = "f5_"
			elif "1st 7 innings" in prop:
				prefix = "f7_"

			if prop in ["money line", "1st 3 innings money line", "1st 5 innings money line"]:
				prop = "ml"
			elif prop == "any run in 1st inning?":
				prop = "rfi"
			elif prop == "player to hit a home run":
				prop = "hr"
			elif market["templateName"].lower().split(" ")[0] in ["|batter|", "|pitcher|"]:
				player = parsePlayer(market["name"].replace("|", "").split(" - ")[0])
				if "total runs scored" in prop:
					prop = "r"
				elif "total bases" in prop:
					prop = "tb"
				elif "hits allowed" in prop:
					prop = "h_allowed"
				elif "walks allowed" in prop:
					prop = "bb_allowed"
				elif "total hits" in prop:
					prop = "h"
				elif "total singles" in prop:
					prop = "single"
				elif "total doubles" in prop:
					prop = "double"
				elif "total triples" in prop:
					prop = "triple"
				elif "total rbis" in prop:
					prop = "rbi"
				elif "strikeouts" in prop:
					prop = "k"
				elif "outs" in prop:
					prop = "outs"
				elif "win" in prop:
					prop = "w"
				elif "earned runs" in prop:
					prop = "er"
				else:
					continue
			elif "total runs" in prop:
				if "odd/even" in prop:
					continue
				if prop.startswith("away"):
					prop = "away_total"
				elif prop.startswith("home"):
					prop = "home_total"
				else:
					prop = "total"
			elif "run line" in prop:
				prop = "spread"
			else:
				#print(prop)
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			selections = market["selections"]
			skip = 1 if prop in ["away_total", "home_total", "hr"] else 2
			if "total doubles" in market["name"].lower() or "total singles" in market["name"].lower():
				skip = 2
			mainLine = ""
			for i in range(0, len(selections), skip):
				try:
					ou = str(selections[i]["price"]["a"])
				except:
					continue
				if skip == 2:
					ou += f"/{selections[i+1]['price']['a']}"
					if selections[i]["name"].lower().replace("|", "") in ["under", "home"]:
						ou = f"{selections[i+1]['price']['a']}/{selections[i]['price']['a']}"

				if "ml" in prop or prop == "rfi":
					res[game][prop] = ou
				elif prop == "hr":
					player = parsePlayer(selections[i]["name"].replace("|", ""))
					res[game][prop][player] = ou
				elif "spread" in prop:
					line = str(float(market["line"]) * -1)
					mainLine = line
					res[game][prop][line] = ou
				elif "total" in prop:
					if "line" in market:
						line = str(float(market["line"]))
						if prop == "total":
							mainLine = line
						if line not in res[game][prop]:
							res[game][prop][line] = ou
						elif "over" in selections[i]["name"].lower():
							res[game][prop][line] = f"{ou}/{res[game][prop][line]}"
						else:
							res[game][prop][line] += "/"+ou
					else:
						line = str(float(selections[i]["name"].split(" ")[-1]))
						if prop == "total":
							mainLine = line
						if line not in res[game][prop]:
							res[game][prop][line] = ou
						elif "over" in selections[i]["name"].lower():
							res[game][prop][line] = f"{ou}/{res[game][prop][line]}"
						else:
							res[game][prop][line] += "/"+ou
				else:
					try:
						line = str(float(market["line"]))
						if player not in res[game][prop]:
							res[game][prop][player] = {}
						if prop in ["single", "double"]:
							if line != "0.5":
								continue
							res[game][prop][player] = ou
						else:
							res[game][prop][player][line] = ou
					except:
						res[game][prop][player] = ou

			#print(market["name"], prop, mainLine)
			if prop in ["spread", "total"]:
				try:
					linePrices = market["movingLines"]["linePrices"]
				except:
					continue
				for prices in linePrices:
					selections = prices["selections"]
					if prop == "spread":
						line = float(prices["line"]) * -1
						ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
						if selections[0]["selectionType"] == "home":
							line *= -1
							ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"

						line = str(line)
					else:
						line = str(float(prices["line"]))
						ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
						if selections[0]["selectionType"] == "under":
							ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"
					if line == mainLine:
						continue
					res[game][prop][line] = ou


	with open("static/mlb/caesars.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePointsbet(date=None):
	url = "https://api.mi.pointsbet.com/api/v2/competitions/5284/events/featured?includeLive=false&page=1"
	outfile = f"mlboutPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for row in data["events"]:
		games.append(row["key"])

	if not date:
		date = str(datetime.now())[:10]

	#games = ["336956"]
	res = {}
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"mlboutPB"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		startDt = datetime.strptime(data["startsAt"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if startDt.day != int(date[-2:]):
			continue

		game = data["name"].lower()
		fullAway, fullHome = map(str, game.split(" @ "))
		game = convertFDTeam(f"{fullAway} @ {fullHome}")
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
			playerProps = False
			prefix = ""
			if "first 5 innings" in prop:
				prefix = "f5_"
			elif "first 3 innings" in prop:
				prefix = "f3_"
			elif "first 7 innings" in prop:
				prefix = "f7_"
			elif "1st inning" in prop:
				prefix = "f1_"

			if prop.startswith("run line") or prop.startswith("alternate run line"):
				if "3-way" in prop or "bands" in prop or "exact" in prop or "odd/even" in prop:
					continue
				prop = f"{prefix}spread"
			elif prop.startswith("moneyline"):
				if "3-way" in prop or "pitchers" in market["eventClass"].lower():
					continue
				prop = f"{prefix}ml"
			elif prop.startswith("total runs") or prop.startswith("alternate total runs"):
				if "3-way" in prop or "bands" in prop or "exact" in prop or "odd/even" in prop:
					continue
				prop = "total"
				prop = f"{prefix}total"
			elif prop == f"{fullAway} total runs" or prop == f"{fullAway} alternate total runs":
				prop = f"{prefix}away_total"
			elif prop == f"{fullHome} total runs" or prop == f"{fullHome} alternate total runs":
				prop = f"{prefix}home_total"
			elif prop.startswith("player") or prop.startswith("pitcher"):
				playerProps = True
				p = prop.split(" ")[1]
				if "to get" in prop:
					continue
				if p == "home":
					prop = "hr"
				elif p == "hits":
					prop = "h"
				elif "runs batted in" in prop:
					prop = "rbi"
				elif p == "stolen":
					prop = "sb"
				elif p == "total":
					prop = "tb"
				elif p == "strikeouts":
					prop = "k"
				elif "win" in prop:
					prop = "w"
			else:
				continue

			if "ml" not in prop:
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			skip = 1 if False else 2
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

					if "ml" in prop and game.startswith(convertFDTeam(outcomes[i+1]["name"])):
						ou = f"{under}/{over}"

				if "ml" in prop:
					res[game][prop] = ou
				elif playerProps:
					#player = parsePlayer(outcomes[i]["name"].lower().split(" over")[0].split(" to ")[0])
					try:
						player = parsePlayer(playerIds[outcomes[i]["playerId"]])
					except:
						continue
					if prop == "w":
						res[game][prop][player] = f"{ou}"
					else:
						res[game][prop][player] = f"{outcomes[i]['name'].split(' ')[-1]} {ou}"
				else:
					if "spread" in prop and outcomes[i]["side"] == "Home":
						points = str(outcomes[i+1]["points"])
						ou = f"{under}/{over}"
					res[game][prop][points] = ou

	with open("static/mlb/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "mlboutPN"
	game = games[gameId]

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o mlboutPN'

	time.sleep(0.3)
	os.system(url)
	try:
		with open(outfile) as fh:
			related = json.load(fh)
	except:
		retry.append(gameId)
		return

	relatedData = {}
	for row in related:
		if row.get("periods") and row["periods"][0]["status"] == "closed":
			continue
		if "special" in row:
			prop = row["units"].lower()

			if prop == "totalbases":
				prop = "tb"
			elif prop == "pitchingouts":
				prop = "outs"
			elif prop == "strikeouts":
				prop = "k"
			elif prop == "hitsallowed":
				prop = "h_allowed"
			elif prop == "earnedruns":
				prop = "er"
			elif prop == "homeruns":
				prop = "hr"
			else:
				continue

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

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o mlboutPN'

	time.sleep(0.3)
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

		overId = underId = 0
		player = ""
		if keys[1] == "1":
			prefix = "f5_"
		elif keys[1] == "3" and row["key"] != "s;3;ou;0.5":
			continue

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
			elif prop == "total" and row["key"] == "s;3;ou;0.5":
				prop = "rfi"
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
			if player not in res[game][prop]:
				res[game][prop][player] = {}

			if "points" in prices[0] and prop not in []:
				handicap = str(float(prices[switched]["points"]))
				res[game][prop][player][handicap] = ou
			else:
				res[game][prop][player] = ou
		else:
			ou = f"{prices[0]['price']}/{prices[1]['price']}"
			if prices[0]["designation"] in ["home", "under"]:
				ou = f"{prices[1]['price']}/{prices[0]['price']}"
				switched = 1

			if "points" in prices[0] and prop != "rfi":
				handicap = str(float(prices[switched]["points"]))
				if prop not in res[game]:
					res[game][prop] = {}

				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

def writePinnacle(date, debug=False):

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/baseball/mlb/matchups#period:0"

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/leagues/246/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o mlboutPN'

	os.system(url)
	outfile = f"mlboutPN"
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	seenGames = {}
	for row in data:
		if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			#continue
			pass
		if row["type"] == "matchup" and not row["parent"]:
			player1 = row["participants"][0]["name"].lower()
			player2 = row["participants"][1]["name"].lower()
			game = f"{player2} @ {player1}".replace("g1 ", "").replace("g2 ", "")
			if "home runs" in game:
				continue

			if convertFDTeam(game) in seenGames:
				continue
			seenGames[convertFDTeam(game)] = True
			games[str(row["id"])] = convertFDTeam(game)

	res = {}
	#games = {'1606945742': 'nym @ mia'}	
	retry = []
	for gameId in games:
		parsePinnacle(res, games, gameId, retry, debug)

	for gameId in retry:
		parsePinnacle(res, games, gameId, retry, debug)

	with open("static/mlb/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

	with open("static/dailyev/odds.json") as fh:
		dingers = json.load(fh)

	for game in res:
		if "hr" in res[game]:
			for player in res[game]["hr"]:
				dingers[game].setdefault(player, {})
				dingers[game][player]["pn"] = res[game]["hr"][player]["0.5"]

	with open("static/dailyev/odds.json", "w") as fh:
		json.dump(dingers, fh, indent=4)

def writeBV():
	url = "https://www.bovada.lv/sports/baseball/mlb"

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/baseball/mlb?marketFilterId=def&liveOnly=False&eventsLimit=5000&lang=en"
	outfile = f"mlboutBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	ids = [r["link"] for r in data[0]["events"]]

	res = {}
	#ids = ["/baseball/mlb/washington-nationals-pittsburgh-pirates-202309121835"]
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		comp = data[0]['events'][0]['competitors']
		game = data[0]['events'][0]['description'].lower()
		fullAway, fullHome = game.split(" @ ")
		game = convertFDTeam(f"{fullAway} @ {fullHome}")

		if game in res:
			continue
		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "player props", "pitcher props"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["description"].lower() == "first 5 innings":
						prefix = "f5_"
					elif market["period"]["description"].lower() == "1st inning":
						prefix = "f1_"

					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "total" or prop == "total runs o/u":
						prop = "total"
					elif prop == "spread":
						prop = "spread"
					elif prop == f"total runs o/u - {fullAway}":
						prop = "away_total"
					elif prop == f"total runs o/u - {fullHome}":
						prop = "home_total"
					elif prop.startswith("total strikeouts"):
						prop = "k"
					elif prop.startswith("total walks"):
						prop = "bb_allowed"
					elif prop.startswith("total hits allowed"):
						prop = "h_allowed"
					elif prop.startswith("total pitcher outs"):
						prop = "outs"
					elif "record a win" in prop:
						prop = "w"
					elif prop.startswith("player") or prop.startswith("total hits, runs") or prop.startswith("total bases") or prop in ["to steal a base", "to record a hit", "to record a run", "to record an rbi"]:
						if "first home run" in prop or "/" in prop or "2+" in prop:
							continue
						if "home run" in prop:
							prop = "hr"
						elif prop == "player to record a double":
							prop = "double"
						elif prop == "player to record a single":
							prop = "single"
						elif prop == "to steal a base":
							prop = "sb"
						elif prop == "to record a hit":
							prop = "h"
						elif prop == "to record a run":
							prop = "r"
						elif prop == "player to record an rbi":
							prop = "rbi"
						elif prop.startswith("total hits, runs"):
							prop = "h+r+rbi"
						elif prop.startswith("total bases"):
							prop = "tb"
					elif prop.startswith("total tackles and assists"):
						prop = "tackles+ast"
					elif prop.startswith("total kicking points"):
						prop = "kicking_pts"
					elif prop == "player sacks":
						prop = "sacks"
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
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
								handicap = market["outcomes"][i]["price"]["handicap"]
							except:
								continue
							res[game][prop][handicap] = ou
					elif "spread" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif prop in ["h+r+rbi", "tb", "k", "bb_allowed", "h_allowed", "w", "outs"]:
						try:
							handicap = market["outcomes"][0]["price"]["handicap"]
							player = parsePlayer(market["description"].split(" - ")[-1].split(" (")[0])
							ou = f"{market['outcomes'][0]['price']['american']}"
							if len(market["outcomes"]) > 1:
								ou += f"/{market['outcomes'][1]['price']['american']}"
							if player not in res[game][prop]:
								res[game][prop][player] = {}
							res[game][prop][player][handicap] = f"{ou}".replace("EVEN", "100")
						except:
							continue
					else:
						for i in range(0, len(market["outcomes"]), 1):
							player = parsePlayer(market['outcomes'][i]["description"].split(" - ")[-1].split(" (")[0])
							try:
								ou = f"{market['outcomes'][i]['price']['american']}".replace("EVEN", "100")
								if prop == "r":
									res[game][prop][player] = {"0.5": ou}
								else:
									res[game][prop][player] = ou
							except:
								pass


	with open("static/mlb/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)


def arb(bookArg="fd"):
	freebets = 100
	res = []
	for sport in ["nba", "nhl", "mlb"]:
		with open(f"static/{sport}/fanduel.json") as fh:
			fdLines = json.load(fh)

		with open(f"static/{sport}/draftkings.json") as fh:
			dkLines = json.load(fh)

		with open(f"static/{sport}/caesars.json") as fh:
			czLines = json.load(fh)

		lines = {
			"dk": dkLines,
			"cz": czLines
		}

		if sport == "nhl":
			with open("static/nhl/mgm.json") as fh:
				lines["mgm"] = json.load(fh)

		for game in fdLines:
			for prop in fdLines[game]:
				over = fdLines[game][prop]
				keys = [over]

				if type(over) is dict:
					keys = fdLines[game][prop].keys()

				for key in keys:
					if type(fdLines[game][prop]) is str:
						over = fdLines[game][prop]
					else:
						over = fdLines[game][prop][key]

					if type(over) is dict:
						continue
					if over.startswith("-/"):
						continue

					odds = over.split("/")
					for ouIdx, odd in enumerate(odds):
						over = int(odd)

						for book in lines:
							if game not in lines[book]:
								continue
							if prop not in lines[book][game]:
								continue
							if key not in lines[book][game][prop]:
								continue

							if type(lines[book][game][prop]) is str:
								under = lines[book][game][prop]
							else:
								under = lines[book][game][prop][key]

							if "/" not in under:
								continue

							if ouIdx == 0:
								under = int(under.split("/")[-1])
							else:
								under = int(under.split("/")[0])

							fdValue = (over / 100) * freebets
							if over < 0:
								fdValue = -1*(100/over) * freebets

							bookValue = under / 100
							if under < 0:
								bookValue = -1*(100/under)
							
							minIdx = hedge = 0
							for i in range(100):
								profit = i / 100 * freebets
								hedge = profit / bookValue
								diff = fdValue - hedge - hedge*bookValue
								#print(i, diff)
								if diff < 0:
									minIdx = i-1
									break

							res.append((minIdx, sport, game, key, prop, over, book, under, f"hedge={round(hedge, 2)}"))

	for row in sorted(res, reverse=True)[:20]:
		print(row)

def writeDK(date, propArg, keep):
	url = "https://sportsbook.draftkings.com/leagues/football/nfl"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		#"game lines": 493,
		"batter": 743,
		"pitcher": 1031,
		#"game props": 724,
		#"innings": 729,
		"1st inning": 1024,
		#"1st x innings": 1626
	}
	
	subCats = {
		493: [4519, 13168, 13169],
		743: [
			# HR, H, TB, RBI
			17319, 17320, 17321, 17322,
			# HRR-ou, h-ou, tb-ou, rbi-ou, r-ou, sb-ou
			17406, 6719, 6607, 8025, 17407, 17408,
			# single, double, bb
			17409, 17410, 17411
		],
		729: [6821],
		1024: [11024],
		1031: [17323, 15221, 9884, 17324, 9886, 17325, 15219, 17412, 17413],
		1626: [15629]
	}

	propIds = {
		11024: "rfi",
		17319: "hr",
		17320: "h", 6719: "h-o/u",
		17321: "tb", 6607: "tb-o/u",
		17322: "rbi", 8025: "rbi-o/u",
		17406: "h+r+rbi-o/u",
		17407: "r-o/u", 17408: "sb-o/u",
		17409: "single-o/u", 17410: "double-o/u", 17411: "bb-o/u",
		17323: "k", 15221: "k-o/u", 9884: "win",
		17324: "h_allowed", 9886: "h_allowed-o/u",
		17325: "bb_allowed", 15219: "bb_allowed-o/u",
		17412: "er-o/u", 17413: "outs-o/u",
	}

	if False:
		mainCats = {
			#"batter": 743,
			#"pitchers": 1031,
			#"game lines": 493,
			#"game props": 724,
			#"innings": 729,
			"1st inning": 1024,
			#"1st x innings": 1626
		}

		subCats = {
			#743: [17319, 17320, 17321, 17322, 17406, 6719, 6607, 8025, 17407, 17408, 17409, 17410, 17411],
			743: [17406],
			#1031: [17323, 15221, 9884, 17324, 9886, 17325, 15219, 17412, 17413],
			1024: [11024],
			#1626: [15629]
		}

	lines = nested_dict()
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			if propArg and "hr" in propArg and subCat not in [6606, 15520]:
				continue
			elif propArg and "k" in propArg and subCat != 15221:
				continue
			elif propArg and "single" in propArg and subCat != 11031:
				continue
			elif propArg and "double" in propArg and subCat != 11032:
				continue
			time.sleep(0.3)
			url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/84240/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outmlbdk"
			cookie = "-H 'Cookie: hgg=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWQiOiIxODU4ODA5NTUwIiwiZGtzLTYwIjoiMjg1IiwiZGtlLTEyNiI6IjM3NCIsImRrcy0xNzkiOiI1NjkiLCJka2UtMjA0IjoiNzA5IiwiZGtlLTI4OCI6IjExMjgiLCJka2UtMzE4IjoiMTI2MSIsImRrZS0zNDUiOiIxMzUzIiwiZGtlLTM0NiI6IjEzNTYiLCJka2UtNDI5IjoiMTcwNSIsImRrZS03MDAiOiIyOTkyIiwiZGtlLTczOSI6IjMxNDAiLCJka2UtNzU3IjoiMzIxMiIsImRraC03NjgiOiJxU2NDRWNxaSIsImRrZS03NjgiOiIwIiwiZGtlLTgwNiI6IjM0MjYiLCJka2UtODA3IjoiMzQzNyIsImRrZS04MjQiOiIzNTExIiwiZGtlLTgyNSI6IjM1MTQiLCJka3MtODM0IjoiMzU1NyIsImRrZS04MzYiOiIzNTcwIiwiZGtoLTg5NSI6IjhlU3ZaRG8wIiwiZGtlLTg5NSI6IjAiLCJka2UtOTAzIjoiMzg0OCIsImRrZS05MTciOiIzOTEzIiwiZGtlLTk0NyI6IjQwNDIiLCJka2UtOTc2IjoiNDE3MSIsImRrcy0xMTcyIjoiNDk2NCIsImRrcy0xMTc0IjoiNDk3MCIsImRrcy0xMjU1IjoiNTMyNiIsImRrcy0xMjU5IjoiNTMzOSIsImRrZS0xMjc3IjoiNTQxMSIsImRrZS0xMzI4IjoiNTY1MyIsImRraC0xNDYxIjoiTjZYQmZ6S1EiLCJka3MtMTQ2MSI6IjAiLCJka2UtMTU2MSI6IjY3MzMiLCJka2UtMTY1MyI6IjcxMzEiLCJka2UtMTY1NiI6IjcxNTEiLCJka2UtMTY4NiI6IjcyNzEiLCJka2UtMTcwOSI6IjczODMiLCJka3MtMTcxMSI6IjczOTUiLCJka2UtMTc0MCI6Ijc1MjciLCJka2UtMTc1NCI6Ijc2MDUiLCJka3MtMTc1NiI6Ijc2MTkiLCJka3MtMTc1OSI6Ijc2MzYiLCJka2UtMTc2MCI6Ijc2NDkiLCJka2UtMTc2NiI6Ijc2NzUiLCJka2gtMTc3NCI6IjJTY3BrTWF1IiwiZGtlLTE3NzQiOiIwIiwiZGtlLTE3NzAiOiI3NjkyIiwiZGtlLTE3ODAiOiI3NzMxIiwiZGtlLTE2ODkiOiI3Mjg3IiwiZGtlLTE2OTUiOiI3MzI5IiwiZGtlLTE3OTQiOiI3ODAxIiwiZGtlLTE4MDEiOiI3ODM4IiwiZGtoLTE4MDUiOiJPR2tibGtIeCIsImRrZS0xODA1IjoiMCIsImRrcy0xODE0IjoiNzkwMSIsImRraC0xNjQxIjoiUjBrX2xta0ciLCJka2UtMTY0MSI6IjAiLCJka2UtMTgyOCI6Ijc5NTYiLCJka2gtMTgzMiI6ImFfdEFzODZmIiwiZGtlLTE4MzIiOiIwIiwiZGtzLTE4NDciOiI4MDU0IiwiZGtzLTE3ODYiOiI3NzU4IiwiZGtlLTE4NTEiOiI4MDk3IiwiZGtlLTE4NTgiOiI4MTQ3IiwiZGtlLTE4NjEiOiI4MTU3IiwiZGtlLTE4NjAiOiI4MTUyIiwiZGtlLTE4NjgiOiI4MTg4IiwiZGtoLTE4NzUiOiJZRFJaX3NoSiIsImRrcy0xODc1IjoiMCIsImRrcy0xODc2IjoiODIxMSIsImRraC0xODc5IjoidmI5WWl6bE4iLCJka2UtMTg3OSI6IjAiLCJka2UtMTg0MSI6IjgwMjQiLCJka3MtMTg4MiI6IjgyMzkiLCJka2UtMTg4MSI6IjgyMzYiLCJka2UtMTg4MyI6IjgyNDMiLCJka2UtMTg4MCI6IjgyMzIiLCJka2UtMTg4NyI6IjgyNjQiLCJka2UtMTg5MCI6IjgyNzYiLCJka2UtMTkwMSI6IjgzMjYiLCJka2UtMTg5NSI6IjgzMDAiLCJka2gtMTg2NCI6IlNWbjFNRjc5IiwiZGtlLTE4NjQiOiIwIiwibmJmIjoxNzIyNDQyMjc0LCJleHAiOjE3MjI0NDI1NzQsImlhdCI6MTcyMjQ0MjI3NCwiaXNzIjoiZGsifQ.jA0OxjKzxkyuAktWmqFbJHkI6SWik-T-DyZuLjL9ZKM; STE=\"2024-07-31T16:43:12.166175Z\"; STIDN=eyJDIjoxMjIzNTQ4NTIzLCJTIjo3MTU0NjgxMTM5NCwiU1MiOjc1Mjc3OTAxMDAyLCJWIjoxODU4ODA5NTUwLCJMIjoxLCJFIjoiMjAyNC0wNy0zMVQxNjo0MToxNC42ODc5Mzk4WiIsIlNFIjoiVVMtREsiLCJVQSI6IngxcVNUYXJVNVFRRlo3TDNxcUlCbWpxWFozazhKVmt2OGFvaCttT1ZpWFE9IiwiREsiOiIzMTQyYjRkMy0yNjU2LTRhNDMtYTBjNi00MTEyM2Y5OTEyNmUiLCJESSI6IjEzNTBmMGM0LWQ3MDItNDUwZC1hOWVmLTJlZjRjZjcxOTY3NyIsIkREIjo0NDg3NTQ0MDk4OH0=; STH=3a3368e54afc8e4c0a5c91094077f5cd1ce31d692aaaf5432b67972b5c3eb6fc; _abck=56D0C7A07377CFD1419CD432549CD1DB~0~YAAQJdbOF6Bzr+SQAQAAsmCPCQykOCRLV67pZ3Dd/613rD8UDsL5x/r+Q6G6jXCECjlRwzW7ESOMYaoy0fhStB3jiEPLialxs/UD9kkWAWPhuOq/RRxzYkX+QY0wZ/Uf8WSSap57OIQdRC3k3jlI6z2G8PKs4IyyQ/bRZfS2Wo6yO0x/icRKUAUeESKrgv6XrNaZCr14SjDVxBBt3Qk4aqJPKbWIbaj+1PewAcP+y/bFEVCmbcrAruJ4TiyqMTEHbRtM9y2O0WsTg79IZu52bpOI2jFjEUXZNRlz2WVhxbApaKY09QQbbZ3euFMffJ25/bXgiFpt7YFwfYh1v+4jrIvbwBwoCDiHn+xy17v6CXq5hIEyO4Bra6QT1sDzil+lQZPgqrPBE0xwoHxSWnhVr60EK1X5IVfypMHUcTvLKFcEP2eqwSZ67Luc/ompWuxooaOVNYrgvH/Vvs5UbyVOEsDcAXoyGt0BW3ZVMVPHXS/30dP3Rw==~-1~-1~1722445877; PRV=3P=0&V=1858809550&E=1720639388; ss-pid=4CNl0TGg6ki1ygGONs5g; ab.storage.deviceId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%22fe7382ec-2564-85bf-d7c4-3eea92cb7c3e%22%2C%22c%22%3A1709950180242%2C%22l%22%3A1709950180242%7D; ab.storage.userId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%2228afffab-27db-4805-85ca-bc8af84ecb98%22%2C%22c%22%3A1712278087074%2C%22l%22%3A1712278087074%7D; ab.storage.sessionId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%223eff9525-6179-dc9c-ce88-9e51fca24c58%22%2C%22e%22%3A1722444192818%2C%22c%22%3A1722442278923%2C%22l%22%3A1722442392818%7D; _gcl_au=1.1.386764008.1720096930; _ga_QG8WHJSQMJ=GS1.1.1722442278.7.1.1722442393.19.0.0; _ga=GA1.2.2079166597.1720096930; _dpm_id.16f4=b3163c2a-8640-4fb7-8d66-2162123e163e.1720096930.7.1722442393.1722178863.1f3bf842-66c7-446c-95e3-d3d5049471a9; _tgpc=78b6db99-db5f-5ce5-848f-0d7e4938d8f2; _tglksd=eyJzIjoiYjRkNjE4MWYtMTJjZS01ZDJkLTgwNTYtZWQ2NzIxM2MzMzM2Iiwic3QiOjE3MjI0NDIyNzgyNzEsInNvZCI6IihkaXJlY3QpIiwic29kdCI6MTcyMTg3ODUxOTY5OCwic29kcyI6Im8iLCJzb2RzdCI6MTcyMTg3ODUxOTY5OH0=; _sp_srt_id.16f4=55c32e85-f32f-42ac-a0e8-b1e37c9d3bc6.1720096930.6.1722442279.1722178650.6d45df5a-aea8-4a66-a4ba-0ef841197d1d.cdc2d898-fa3f-4430-a4e4-b34e1909bb05...0; _scid=e6437688-491e-4800-b4b2-e46e81b2816c; _ga_M8T3LWXCC5=GS1.2.1722442279.7.1.1722442288.51.0.0; _svsid=9d0929120b67695ad6ee074ccfd583b7; _sctr=1%7C1722398400000; _hjSessionUser_2150570=eyJpZCI6ImNmMDA3YTA2LTFiNmMtNTFkYS05Y2M4LWNmNTAyY2RjMWM0ZCIsImNyZWF0ZWQiOjE3MjA1NTMwMDE4OTMsImV4aXN0aW5nIjp0cnVlfQ==; _csrf=ba945d1a-57c4-4b50-a4b2-1edea5014b72; ss-id=x8zwcqe0hExjZeHXAKPK; ak_bmsc=F8F9B7ED0366DC4EB63B2DD6D078134C~000000000000000000000000000000~YAAQJdbOF3hzr+SQAQAAp1uPCRjLBiubHwSBX74Dd/8hmIdve4Tnb++KpwPtaGp+NN2ZcEf+LtxC0PWwzhZQ1one2MxGFFw1J6BXg+qiFAoQ6+I3JExoHz4r+gqodWq7y5Iri7+3aBFQRDtn17JMd1PTEEuN8EckzKIidL3ggrEPS+h1qtof3aHJUdx/jkCUjkaN/phWSvohlUGscny8dJvRz76e3F20koI5UsjJ/rQV7dUn6HNw1b5H1tDeL7UR1mbBrCLz6YPDx4XCjybvteRQpyLGI0o9L6xhXqv12exVAbZ15vpuNJalhR6eB4/PVwCmfVniFcr/xc8hivkuBBMOj1lN7ADykNA60jFaIRAY2BD2yj27Aedr7ETAFnvac0L0ITfH20LkA2cFhGUxmzOJN0JQ6iTU7VGgk19FzV+oeUxNmMPX; bm_sz=D7ABF43D4A5671594F842F6C403AB281~YAAQJdbOF3lzr+SQAQAAp1uPCRgFgps3gN3zvxvZ+vbm5t9IRWYlb7as+myjQOyHzYhriG6n+oxyoRdQbE6wLz996sfM/6r99tfwOLP2K8ULgA2nXfOPvqk6BwofdTsUd7KP7EnKhcCjhADO18uKB/QvIJgyS3IFBROxP2XFzS15m/DrRbF7lQDRscWtVo8oOITxNTBlwg0g4fI3gzjG6A4uHYxjeCegxSrHFHGFr4KZXgOnsJhmZe0lqIRWUFcIKC/gfsDd+jfyUnprMso1Flsv9blGlvycOoWTHPdEQvUudpOZlZ3JYz9H5y+dU94wBD9ejxIlRKP26giQISjun829Kt7CuKxJXYAcSJeiomZFh5Abj+Mkv0wi6ZcRcmOVFt49eywPazFHpGM8DVcUkVEFMcpNCeiJ/CtC60U9SoJy+ermF1hTqiAq~3622209~4408134; bm_sv=6618DE86472CB31D7B7F16DAE6689651~YAAQJdbOF96Lr+SQAQAA4iSRCRjfwGUmEhVBbE3y/2VDAAvuPyI2gX7io7CQCPfcdMOnBnNhxHIKYt9PFr7Y1TADQHFUC9kqXu7Nbj9d1BrLlfi1rPbv/YKPqhqSTLkbNSWbeKhKM4HfOu7C+RLV383VzGeyDhc2zOuBKBVNivHMTF9njS3vK6RKeSPFCfxOJdDHgNlIYykf0Ke2WJvflHflTUykwWUaYIlqoB52Ixb9opHQVTptWjetGdYjuOO2S2ZPkw==~1; _dpm_ses.16f4=*; _tgidts=eyJzaCI6ImQ0MWQ4Y2Q5OGYwMGIyMDRlOTgwMDk5OGVjZjg0MjdlIiwiY2kiOiIxZDMxOGRlZC0yOWYwLTUzYjItYjFkNy0yMDlmODEwNDdlZGYiLCJzaSI6ImI0ZDYxODFmLTEyY2UtNWQyZC04MDU2LWVkNjcyMTNjMzMzNiJ9; _tguatd=eyJzYyI6IihkaXJlY3QpIn0=; _tgsid=eyJscGQiOiJ7XCJscHVcIjpcImh0dHBzOi8vc3BvcnRzYm9vay5kcmFmdGtpbmdzLmNvbSUyRmxlYWd1ZXMlMkZiYXNlYmFsbCUyRm1sYlwiLFwibHB0XCI6XCJNTEIlMjBCZXR0aW5nJTIwT2RkcyUyMCUyNiUyMExpbmVzJTIwJTdDJTIwRHJhZnRLaW5ncyUyMFNwb3J0c2Jvb2tcIixcImxwclwiOlwiXCJ9IiwicHMiOiJkOTY4OTkxNy03ZTAxLTQ2NTktYmUyOS1mZThlNmI4ODY3MzgiLCJwdmMiOiIxIiwic2MiOiJiNGQ2MTgxZi0xMmNlLTVkMmQtODA1Ni1lZDY3MjEzYzMzMzY6LTEiLCJlYyI6IjUiLCJwdiI6IjEiLCJ0aW0iOiJiNGQ2MTgxZi0xMmNlLTVkMmQtODA1Ni1lZDY3MjEzYzMzMzY6MTcyMjQ0MjI4MjA3NDotMSJ9; _sp_srt_ses.16f4=*; _gid=GA1.2.150403708.1722442279; _scid_r=e6437688-491e-4800-b4b2-e46e81b2816c; _uetsid=85e6d8504f5711efbe6337917e0e834a; _uetvid=d50156603a0211efbb275bc348d5d48b; _hjSession_2150570=eyJpZCI6ImQxMTAyZTZjLTkyYzItNGMwNy1hNzMzLTcxNDhiODBhOTI4MyIsImMiOjE3MjI0NDIyODE2NDUsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _rdt_uuid=1720096930967.9d40f035-a394-4136-b9ce-2cf3bb298115'"
			os.system(f"curl -s {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' {cookie} -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			#with open("out", "w") as fh:
			#	json.dump(data, fh, indent=4)

			prop = propIds.get(subCat, "")

			print(prop)

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
				startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=4)
				if startDt.day != int(date[-2:]):
					#continue
					pass
				game = event["name"].lower()
				games = []
				for team in game.split(" @ "):
					t = convertTeam(team)
					games.append(t)
				game = " @ ".join(games)
				if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
					continue

				events[event["eventId"]] = game

			for catRow in data["eventGroup"]["offerCategories"]:
				if catRow["offerCategoryId"] != mainCats[mainCat]:
					continue
				if "offerSubcategoryDescriptors" not in catRow:
					continue
				for cRow in catRow["offerSubcategoryDescriptors"]:
					if "offerSubcategory" not in cRow:
						continue
					topProp = cRow["name"].lower()
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

							alt = True
							if subCat in propIds:
								prop = propIds[subCat]

								if "o/u" in prop:
									alt = False
									prop = prop.replace("-o/u", "")
							else:
								alt = False
								prop = row["label"].lower().split(" [")[0]
							
								prefix = ""
								if "1st 5" in prop:
									prefix = "f5_"
								elif "1st 3" in prop:
									prefix = "f3_"
								elif "1st 7" in prop:
									prefix = "f7_"

								if "moneyline" in prop or prop in ["1st 5 innings", "1st 3 innings", "1st 7 innings"]:
									prop = "ml"
								elif "run line" in prop:
									prop = "spread"
								elif "team total runs" in topProp:
									team = convertTeam(prop.split(": ")[0].replace(" total runs", "").replace("alternate ", ""))
									if game.startswith(team):
										prop = "away_total"
									else:
										prop = "home_total"
								elif "total" in prop:
									prop = "total"
								else:
									continue


								prop = prop.replace(" alternate", "")
								prop = f"{prefix}{prop}"

							outcomes = row["outcomes"]
							if "ml" in prop:
								lines[game][prop] = f"{outcomes[0]['oddsAmerican']}/{outcomes[1]['oddsAmerican']}"
							elif prop == "rfi":
								outcomes = [x for x in outcomes if x["line"] == 0.5]
								lines[game][prop] = outcomes[0]["oddsAmerican"]+"/"+outcomes[1]["oddsAmerican"]
								continue

							skip = 1
							if not alt:
								skip = 2
							for i in range(0, len(outcomes), skip):
								outcome = outcomes[i]
								if "spread" in prop or "total" in prop:
									player = convertMLBTeam(outcome["participant"])
								else:
									player = parsePlayer(outcome["participant"].split(" (")[0].strip())

								ou = outcome["oddsAmerican"]

								if prop == "win":
									if i+1 >= len(outcomes):
										continue
									lines[game][prop][player] = ou+"/"+outcomes[i+1]["oddsAmerican"]
								elif alt:
									line = outcome.get("label", "")

									if line:
										line = str(float(line.replace("+", "")) - 0.5)
										if line in lines[game][prop][player]:
											o,u = map(str, lines[game][prop][player][line].split("/"))
											if int(ou) > int(o):
												o = ou
											lines[game][prop][player][line] = o+"/"+u
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
										if line in lines[game][prop][player]:
											if "under" in outcome.get("label", "").lower():
												lines[game][prop][player][line] += "/"+ou
										else:
											lines[game][prop][player][line] = ou
										"""

	if keep:
		with open("static/mlb/draftkings.json") as fh:
			d = json.load(fh)
		merge_dicts(d, lines, forceReplace=True)
		with open("static/mlb/draftkings.json", "w") as fh:
			json.dump(d, fh, indent=4)
	else:
		with open("static/mlb/draftkings.json", "w") as fh:
			json.dump(lines, fh, indent=4)

def writeKambi(date):
	if not date:
		date = str(datetime.now())[:10]

	data = {}
	outfile = f"outmlb.json"
	url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/baseball/nfl"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/baseball/mlb/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -s \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	fullTeam = {}
	eventIds = {}
	events = []
	if "events" in j:
		events = j["events"]

	for event in events:
		if "event" not in event:
			continue
		if str(datetime.strptime(event["event"]["start"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			#continue
			pass
		game = f"{event['event']['awayName']} @ {event['event']['homeName']}"
		away, home = map(str, game.split(" @ "))
		homeFull, awayFull = map(str, event["event"]["englishName"].lower().split(" - "))
		games = []
		for team, full in zip([away, home], [awayFull, homeFull]):
			t = convertTeam(team)
			fullTeam[t] = full
			games.append(t)
		game = " @ ".join(games)
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	#eventIds = {'kc @ mil': 1022035215}
	#data['kc @ mil'] = {}
	#print(eventIds)
	#exit()
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

		i = 0
		for betOffer in j["betOffers"]:
			playerProp = False
			label = betOffer["criterion"]["label"].lower()
			prefix = ""
			if "first 3 inn" in label:
				prefix = "f3_"
			elif "first 5 inn" in label:
				prefix = "f5_"
			elif "inning 1" in label:
				prefix = "f1_"


			if "handicap" in label:
				label = "spread"
			elif f"total runs by {awayFull}" in label:
				label = "away_total"
			elif f"total runs by {homeFull}" in label:
				label = "home_total"
			elif "by the player" in label:
				playerProp = True
				label = "_".join(label.replace("total ", "").split(" by the player")[0].split(" "))

				if label == "strikeouts_thrown":
					label = "k"
				elif label == "runs_scored":
					label = "r"
				elif label == "hits":
					label = "h"
				elif label == "bases_recorded":
					label = "tb"
				elif label == "stolen_bases":
					label = "sb"
				elif label in ["doubles", "rbis"]:
					label = label[:-1]
			elif "total runs" in label:
				if "odd/even" in label:
					continue
				label = "total"
			elif label == "match odds":
				label = "ml"
			elif label == "first team to score":
				label = "first_score"
			elif "player to hit a home run" in label:
				label = "hr"
				playerProp = True
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
				player = parsePlayer(betOffer["outcomes"][0]["participant"].split(") ")[-1])
				try:
					last, first = map(str, player.split(", "))
					player = f"{first} {last}"
				except:
					pass
			if "ml" in label or label in ["first_score"]:
				data[game][label] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			else:
				if label not in data[game]:
					data[game][label] = {}
				if not playerProp:
					#print(betOffer["criterion"]["label"], label)
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer["outcomes"][0]["label"] == "Under" or convertTeam(betOffer["outcomes"][0]["label"].lower()) == home:
						line = str(float(line) * -1)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					data[game][label][line] = ou
					if label == "f1_total" and line == "0.5":
						data[game]["rfi"] = ou
				elif label == "hr":
					if betOffer["outcomes"][0]["label"] == "Under":
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]

					data[game][label][player] = ou
				else:
					if "line" not in betOffer["outcomes"][0]:
						continue
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer["outcomes"][0]["label"] == "Under":
						line = str(betOffer["outcomes"][1]["line"] / 1000)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]

					if player not in data[game][label]:
						data[game][label][player] = {}

					if label in ["single", "double", "sb"]:
						if line != "0.5":
							continue
						data[game][label][player] = ou
					else:
						data[game][label][player][line] = ou


	with open(f"static/mlb/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

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

def convertRetroTeam(team):
	team = team.lower()
	if team == "chn":
		return "chc"
	elif team == "cha":
		return "chw"
	elif team == "lan":
		return "lad"
	elif team == "nyn":
		return "nym"
	elif team == "nya":
		return "nyy"
	elif team == "sln":
		return "stl"
	elif team == "was":
		return "wsh"
	elif team == "ana":
		return "laa"
	elif team in ["kca", "sdn", "sfn", "tba"]:
		return team[:2]
	return team

def writeGamelogs():
	data = {}
	# headers https://www.retrosheet.org/gamelogs/glfields.txt
	for file in glob(f"static/mlbprops/gamelogs/*"):
		with open(file) as fh:
			reader = csv.reader(fh)
			rows = [x for x in reader]
		for idx, row in enumerate(rows):
			# 21-37 AB,H,2B,3B,HR,...
			date = row[0]
			dh = row[1]
			year = date[:4]
			date = f"{date[4:6]}-{date[-2:]}"
			away = convertRetroTeam(row[3])
			home = convertRetroTeam(row[6])
			if dh == "2":
				away += " gm2"
				home += " gm2"
			elif dh == "3":
				away += " gm3"
				home += " gm3"
			game = f"{away} @ {home}"

			awayHR = int(row[21+4])
			homeHR = int(row[49+4])

			if year not in data:
				data[year] = {}
			if date not in data[year]:
				data[year][date] = {}
			data[year][date][game] = awayHR + homeHR

	with open("static/baseballreference/gamelogs.json", "w") as fh:
		json.dump(data, fh, indent=4)

def readGamelogHomers():
	with open("static/baseballreference/gamelogs.json") as fh:
		gamelogs = json.load(fh)

	monthTxt = ["Jan", "Feb", "Mar", "Apr", "May", "June", "Jul", "Aug", "Sep", "Oct"]
	for year in gamelogs:
		hrs = games = 0
		months = {}
		for date in gamelogs[year]:
			month = date.split("-")[0]
			if month not in months:
				months[month] = []
			for game in gamelogs[year][date]:
				games += 1
				hrs += gamelogs[year][date][game]

				months[month].append(gamelogs[year][date][game])

		hrPerGame = round(hrs / games, 2)
		out = ""
		for month in months:
			if month in ["09", "10", "11"]:
				continue
			hr = round(sum(months[month]) / len(months[month]), 2)
			out += f"{monthTxt[int(month)-1]}: {hr}, "
		print(year, hrPerGame, "HR/G")
		print("\t"+out)

def parseESPN(espnLines, noespn=None):
	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"static/mlb/espn.json") as fh:
		espn = json.load(fh)

	players = {}
	for team in roster:
		players[team] = {}
		for player in roster[team]:
			first = player.split(" ")[0][0]
			last = player.split(" ")[-1]
			#if team == "hou" and player == "jeff green":
			#	continue
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

def clear():
	with open(f"{prefix}static/mlb/bet365.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/kambi.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/bovada.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/pinnacle.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/mgm.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/fanduel.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/draftkings.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/caesars.json", "w") as fh:
		json.dump({}, fh)

	with open(f"{prefix}static/mlb/espn.json", "w") as fh:
		json.dump({}, fh)

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None, overArg=None, underArg=None):
	if not boost:
		boost = 1

	with open(f"updated.json") as fh:
		updated = json.load(fh)
	updated["mlb"] = str(datetime.now())
	with open(f"updated.json", "w") as fh:
		json.dump(updated, fh, indent=4)

	with open(f"{prefix}static/mlb/actionnetwork.json") as fh:
		action = json.load(fh)

	with open(f"{prefix}static/mlb/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/mlb/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/mlb/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/mlb/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/mlb/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/mlb/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/mlb/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/mlb/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/mlb/espn.json") as fh:
		espnLines = json.load(fh)

	with open(f"{prefix}static/mlb/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"static/baseballreference/bvp.json") as fh:
		bvpData = json.load(fh)

	with open(f"static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)

	with open(f"static/mlb/leftRightSplits.json") as fh:
		leftRightSplits = json.load(fh)

	with open(f"static/dailyev/weather.json") as fh:
		weather = json.load(fh)

	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"{prefix}static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)

	year = datetime.now().year
	lastYear = year - 1
	with open(f"{prefix}static/mlbprops/stats/{lastYear}.json") as fh:
		lastYearStats = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines,
		"espn": espnLines,
		"365": bet365Lines
	}

	with open(f"{prefix}static/mlb/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	teamGame = {}
	for game in fdLines:
		away, home = map(str, game.split(" @ "))
		teamGame[away] = teamGame[home] = game

	for game in fdLines:
		if "gm2" in game:
			continue
		if teamArg:
			if game.split(" @ ")[0] not in teamArg.split(",") and game.split(" @ ")[1] not in teamArg.split(","):
				continue

		away, home = map(str, game.split(" @ "))
		gameWeather = weather.get(game, {})
		with open(f"static/splits/mlb/{away}.json") as fh:
			awayStats = json.load(fh)
		with open(f"static/splits/mlb_historical/{away}.json") as fh:
			awayHistStats = json.load(fh)

		with open(f"static/splits/mlb/{home}.json") as fh:
			homeStats = json.load(fh)
		with open(f"static/splits/mlb_historical/{home}.json") as fh:
			homeHistStats = json.load(fh)
		props = {}
		for book in lines:
			if game not in lines[book]:
				continue
			for prop in lines[book][game]:
				props[prop] = 1

		for prop in props:
			if propArg and prop != propArg:
				continue

			if not propArg and prop in ["triple", "double", "spread"]:
				pass
				#continue

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
				for i in range(2):

					if overArg and i == 1:
						continue
					elif underArg and i == 0:
						continue
					highestOdds = []
					books = []
					odds = []

					for book in lines:
						lineData = lines[book]
						if game in lineData and prop in lineData[game]:
							#print(book, game, prop, handicap)
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
									if " " in val and playerHandicap != val.split(" ")[0]:
										continue
									val = lineData[game][prop][handicap].split(" ")[-1]

							try:
								o = val.split(" ")[-1].split("/")[i]
								ou = val.split(" ")[-1]
							except:
								if i == 1:
									pass
								o = "-"
								ou = val

							if not o:
								continue

							if "unavailable" in o:
								continue

							if o != "-":
								highestOdds.append(int(o.replace("+", "")))
							odds.append(ou)
							books.append(book)

					if len(books) < 2:
						continue

					unders = [s.split("/")[-1] for s in odds if "/" in s]
					if i == 1:
						if not unders:
							continue

					team = opp = dtSplits = dtSplitsLYR = totalSplits = awayHomeSplits = ""
					logsLYR = ""
					hitRateLYR = 0
					totalOver = total10Over = totalOverLastYear = 0
					playerYears = []
					convertedProp = prop.replace("single", "1b").replace("double", "2b")
					if prop == "away_total":
						team = away
						opp = home
					elif prop == "home_total":
						team = home
						opp = away
					elif player:
						away, home = map(str, game.split(" @ "))
						team = away
						opp = home
						if player in roster[home]:
							team = home
							opp = away
							stats = homeStats.get(player, {})
							statsHist = homeHistStats.get(player, {})
						elif player in roster[away]:
							stats = awayStats.get(player, {})
							statsHist = awayHistStats.get(player, {})
						else:
							stats = {}
							statsHist = {}

						ou = playerHandicap
						if not ou.strip():
							ou = "0.5"

						dtSplits = ",".join(stats.get("dt", []))
						totalSplits = ",".join([str(x) for x in stats.get(convertedProp, [])])
						awayHomeSplits = ",".join([str(x) for x in stats.get("awayHome", [])])
						playerYears = sorted(list(statsHist.keys()), reverse=True)
						logsLYR = statsHist.get(str(lastYear), {}).get(convertedProp, [])[::-1]
						dtSplitsLYR = ",".join(statsHist.get(str(lastYear), {}).get("date", [])[::-1])
						if logsLYR:
							hitRateLYR = round(len([x for x in logsLYR if x > float(ou)]) * 100 / len(logsLYR))

						if convertedProp in stats:
							arr = stats.get(convertedProp, [])
							totalOver = round(len([x for x in arr if int(x) > float(ou)]) * 100 / len(arr))
							total10Over = round(len([x for x in arr[-10:] if int(x) > float(ou)]) * 100 / len(arr[-10:]))

						logsLYR = ",".join([str(x) for x in logsLYR])

						if i == 1:
							#if total10Over:
							total10Over = 100 - total10Over
							#if totalOver:
							totalOver = 100 - totalOver
							#if totalOverLastYear:
							totalOverLastYear = 100 - totalOverLastYear

					bvp = pitcher = ""
					try:
						pitcher = lineups[opp]["pitcher"]
						pitcherLR = leftOrRight[opp].get(pitcher, "")
						bvpStats = bvpData[team][player+' v '+pitcher]
						bvp = f"{bvpStats['h']}-{bvpStats['ab']}, {bvpStats['hr']} HR, {bvpStats['rbi']} RBI, {bvpStats['so']} SO"
					except:
						pass

					# LeftRightSplits Last Year
					try:
						x = leftRightSplits[team][player]["2024"][pitcherLR+"HP"]
						other = "L" if pitcherLR == "R" else "R"
						x2 = leftRightSplits[team][player]["2024"][pitcherLR+"HP"]
						leftRightHTML = f"<></>"
					except:
						pass

					oppRank = oppRankLastYear = 0
					rankingsProp = convertRankingsProp(prop)
					if opp and rankingsProp in rankings[opp]:
						oppRank = rankings[opp][rankingsProp]['rank']
						oppRank = f"{oppRank}{getSuffix(oppRank)}"
						oppRankLastYear = rankings[opp][rankingsProp].get('lastYearRank', 0)
						if oppRankLastYear and "opp" in rankingsProp:
							oppRankLastYear = 30 - oppRankLastYear
						oppRankLastYear = f"{oppRankLastYear}{getSuffix(oppRankLastYear)}"

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
								#maxOdds.append(-10000)
								pass

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

					implied = 0
					if line > 0:
						implied = 100 / (line + 100)
					else:
						implied = -1*line / (-1*line + 100)
					implied *= 100

					# if no unders other than ev book, use that
					if len(unders) == 1 and "/" in maxOU and unders[0] == maxOU.split("/")[1]:
						bookIdx = l.index(maxOU)
						l[bookIdx] = "-/"+maxOU.split("/")[-1]
					else:
						l.remove(maxOU)
						books.remove(evBook)

					if pn:
						books.append("pn")
						l.append(pn)

					avgOver = []
					avgUnder = []
					for book in l:
						if book.split("/")[0] != "-":
							avgOver.append(convertImpOdds(int(book.split("/")[0])))
						if "/" in book and book.split("/")[1] != "-":
							avgUnder.append(convertImpOdds(int(book.split("/")[1])))

					if avgOver:
						avgOver = float(sum(avgOver) / len(avgOver))
						avgOver = convertAmericanFromImplied(avgOver)
					else:
						avgOver = "-"
					if avgUnder:
						avgUnder = float(sum(avgUnder) / len(avgUnder))
						avgUnder = convertAmericanFromImplied(avgUnder)
					else:
						avgUnder = "-"

					if i == 1:
						ou = f"{avgUnder}/{avgOver}"
					else:
						ou = f"{avgOver}/{avgUnder}"

					if ou == "-/-" or ou.startswith("-/") or ou.startswith("0/"):
						continue

					if ou.endswith("/-") or ou.endswith("/0"):
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


						evData[key]["weather"] = gameWeather
						evData[key]["implied"] = implied
						evData[key]["team"] = team
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
						evData[key]["playerYears"] = playerYears
						evData[key]["odds"] = l
						evData[key]["player"] = player
						evData[key]["pitcher"] = "" if not pitcher else f"{pitcher.title()} ({pitcherLR})"
						evData[key]["bvp"] = bvp
						j = {b: o for o, b in zip(l, books)}
						j[evBook] = maxOU
						evData[key]["bookOdds"] = j
						evData[key]["logsLYR"] = logsLYR
						evData[key]["hitRateLYR"] = hitRateLYR
						evData[key]["dtSplitsLYR"] = dtSplitsLYR
						evData[key]["dtSplits"] = dtSplits
						evData[key]["totalSplits"] = totalSplits
						evData[key]["awayHomeSplits"] = awayHomeSplits
						evData[key]["totalOver"] = totalOver
						evData[key]["total10Over"] = total10Over
						evData[key]["totalOverLastYear"] = totalOverLastYear
						evData[key]["oppRank"] = oppRank
						evData[key]["oppRankLastYear"] = oppRankLastYear

	with open(f"{prefix}static/mlb/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	with open(f"{prefix}static/mlb/evArr.json", "w") as fh:
		json.dump([value for key, value in evData.items()], fh)

def sortEV(propArg=""):
	with open(f"{prefix}static/mlb/ev.json") as fh:
		evData = json.load(fh)

	writeDaily()

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], d["game"], player, d["playerHandicap"], d["line"], d["book"], j, d))

	for row in sorted(data):
		print(row[:-1])

	hdrs = ["EV", "EV Book", "Imp", "Game", "Player", "Prop", "O/U", "FD", "Bet365", "DK", "MGM"]
	if propArg not in ["single", "double", "sb", "h"]:
		hdrs.insert(1, "PN EV")
		hdrs.extend(["PN"])
	if propArg != "single":
		hdrs.append("Kambi")
	if propArg in ["k", "single", "double", "sb", "h"]:
		hdrs.insert(hdrs.index("FD")+1, "bet365")
	hdrs.append("CZ")
	hdrs.extend(["SZN", "LYR", "Splits", "Opp Rank", "LYR Opp Rank"])
	output = "\t".join(hdrs) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["book"] in ["kambi"]:
			#continue
			pass
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("BET365", "365").replace("KAMBI", "BR"), f"{round(row[-1]['implied'])}%", row[1].upper(), row[-1]["player"].title(), row[-1]["prop"], ou]
		if propArg not in ["single", "double", "sb", "h"]:
			arr.insert(1, row[-1].get("pn_ev", "-"))

		for book in ["fd", "bet365", "dk", "mgm", "pn", "kambi", "cz"]:
			if book == "mgm":
				pass
				#continue
			if propArg == "single" and book in ["pn", "kambi"]:
				continue
			elif propArg in ["double", "sb", "h"] and book in ["pn"]:
				continue
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		arr.extend([f"{row[-1]['totalOver']}%", f"{row[-1]['totalOverLastYear']}%", row[-1]["totalSplits"]])
		arr.extend([row[-1]["oppRank"], row[-1]["oppRankLastYear"]])
		if propArg in ["k", "single", "double", "sb", "h"]:
			arr.insert(hdrs.index("FD")+1, row[-1]["bookOdds"].get("bet365", "-").replace("+", ""))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/mlb/props.csv", "w") as fh:
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
	parser.add_argument("--clear", action="store_true", help="Clear")
	parser.add_argument("--under", action="store_true", help="Under")
	parser.add_argument("--over", action="store_true", help="Over")
	parser.add_argument("--nocz", action="store_true", help="No CZ Lines")
	parser.add_argument("--no365", action="store_true", help="No 365 Devig")
	parser.add_argument("--nobr", action="store_true", help="No BR/Kambi lines")
	parser.add_argument("--dinger", action="store_true", help="Dinger Tues")
	parser.add_argument("--plays", action="store_true", help="Plays")
	parser.add_argument("--summary", action="store_true", help="Summary")
	parser.add_argument("--text", action="store_true", help="Text")
	parser.add_argument("--lineups", action="store_true", help="Lineups")
	parser.add_argument("--lineupsLoop", action="store_true", help="Lineups")
	parser.add_argument("--token", help="Token")
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("--skipdk", action="store_true")
	parser.add_argument("--bpp", action="store_true")
	parser.add_argument("--gamelogs", action="store_true")
	parser.add_argument("--arb", action="store_true")
	parser.add_argument("--writeGamelogs", action="store_true")
	parser.add_argument("--commit", action="store_true")
	parser.add_argument("--leftRight", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--year", type=int)
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

	if args.writeGamelogs:
		writeGamelogs()

	if args.gamelogs:
		readGamelogHomers()

	if args.arb:
		arb()

	if args.action:
		writeActionNetwork(args.date)

	if args.fd:
		writeFanduel()

	if args.mgm:
		writeMGM(args.date)

	if args.pb:
		writePointsbet(args.date)

	if args.dk:
		writeDK(args.date, args.prop, args.keep)

	if args.kambi:
		writeKambi(args.date)

	if args.pn:
		writePinnacle(args.date, args.debug)

	if args.bv:
		writeBV()

	if args.cz:
		uc.loop().run_until_complete(writeCZToken())
		writeCZ(args.date)

	if args.clear:
		clear()

	if args.update:
		#writeFanduel()
		print("pn")
		writePinnacle(args.date)
		print("kambi")
		writeKambi(args.date)
		#print("mgm")
		#writeMGM(args.date)
		#if not args.skipdk:
		print("dk")
		writeDK(args.date, args.prop, args.keep)
		#writeBPP(args.date)
		#writeActionNetwork(args.date)
		print("cz")
		uc.loop().run_until_complete(writeCZToken())
		writeCZ(args.date)
		#print("bv")
		#writeBV()

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, teamArg=args.team, boost=args.boost, overArg=args.over, underArg=args.under)

	if args.print:
		sortEV(args.prop)

	if args.commit:
		commitChanges()

	if args.leftRight:
		#writeLeftRightSplits()
		uc.loop().run_until_complete(writeLeftRight(args.year))

	if args.player:
		#with open(f"{prefix}static/mlb/draftkings.json") as fh:
		#	dkLines = json.load(fh)

		#with open(f"{prefix}static/mlb/bet365.json") as fh:
		#	bet365Lines = json.load(fh)

		with open(f"{prefix}static/mlb/fanduel.json") as fh:
			fdLines = json.load(fh)

		#with open(f"{prefix}static/mlb/bovada.json") as fh:
		#	bvLines = json.load(fh)

		with open(f"{prefix}static/mlb/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"{prefix}static/mlb/mgm.json") as fh:
			mgmLines = json.load(fh)

		with open(f"{prefix}static/mlb/pinnacle.json") as fh:
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

	