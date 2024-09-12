
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

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr"):

	prefix = ""

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

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "").replace(" iv", "")
	if player.endswith(" v"):
		player = player[:-2]
	return player

def convertTeam(team):
	team = team.lower().replace(".", "").replace(" ", "")
	t = team.split(" ")[0][:3]
	if t in ["gre", "gbp"]:
		return "gb"
	elif t == "jac":
		return "jax"
	elif t == "nep":
		return "ne"
	elif t == "nos":
		return "no"
	elif t in ["kan", "kcc"]:
		return "kc"
	elif t in ["tam", "tbb"]:
		return "tb"
	elif t in ["san", "sf4"]:
		return "sf"
	elif t in ["las", "lvr"]:
		return "lv"
	elif t == "los":
		if "rams" in team:
			return "lar"
		return "lac"
	elif t == "new":
		if "giants" in team:
			return "nyg"
		elif "jets" in team:
			return "nyj"
		elif "saints" in team:
			return "no"
		return "ne"
	return t

def writeESPN():
	js = """

	{
		function convertTeam(team) {
			team = team.toLowerCase();
			t = team.split(" ")[0];
			if (t == "ny") {
				if (team.includes("giants")) {
					return "nyg";
				}
				return "nyj";
			} else if (t == "la") {
				if (team.includes("rams")) {
					return "lar";
				}
				return "lac";
			}
			return t;
		}

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			return player;
		}

		let status = "";

		async function readPage() {
			for (detail of document.querySelectorAll("details")) {
				let prop = detail.querySelector("h2").innerText.toLowerCase();

				let skip = 2;
				let player = "";
				if (prop.indexOf("player") == 0) {
					prop = prop.replace("player total ", "").replace("player ", "").replace(" + ", "+").replace("points", "pts").replace("field goals made", "fgm").replace("extra pts made", "xp").replace("passing", "pass").replace("rushing", "rush").replace("receptions", "rec").replace("reception", "rec").replace("receiving", "rec").replace("attempts", "att").replace("interceptions thrown", "int").replace("completions", "cmp").replace("completion", "cmp").replace("yards", "yd").replace("touchdowns", "td").replace("assists", "ast").replaceAll(" ", "_");
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

				if (!data[prop]) {
					data[prop] = {};
				}

				let btns = detail.querySelectorAll("button");
				let seeAll = false;
				if (btns[btns.length - 1].innerText == "See All Lines") {
					seeAll = true;
					btns[btns.length - 1].click();
				}

				if (seeAll) {
					let modal = document.querySelector(".modal--see-all-lines");
					while (!modal) {
						await new Promise(resolve => setTimeout(resolve, 700));
						modal = document.querySelector(".modal--see-all-lines");
					}

					while (modal.querySelectorAll("button").length == 0) {
						await new Promise(resolve => setTimeout(resolve, 700));
					}

					let btns = Array.from(modal.querySelectorAll("button"));
					btns.shift();

					for (i = 0; i < btns.length; i += 3) {
						let ou = btns[i+1].querySelectorAll("span")[1].innerText+"/"+btns[i+2].querySelectorAll("span")[1].innerText;
						let player = parsePlayer(btns[i].innerText.toLowerCase().split(" total ")[0]);
						let line = btns[i+1].querySelector("span").innerText.split(" ")[1];
						data[prop][player] = {};
						data[prop][player][line] = ou.replace("Even", "+100");
					}
					modal.querySelector("button").click();
					while (document.querySelector(".modal--see-all-lines")) {
						await new Promise(resolve => setTimeout(resolve, 500));
					}
				}
			}
			console.log(data);
		}

		readPage();
	}

"""

def writeMGM():
	url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35"

	url = "https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=11&regionId=9&competitionId=35&compoundCompetitionId=1:35&widgetId=/mobilesports-v1.0/layout/layout_us/modules/competition/defaultcontainer-futures-specials-events-no-header&shouldIncludePayload=true"
	outfile = "outfuture"
	time.sleep(0.2)
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	data = data["widgets"][0]["payload"]["items"][0]["activeChildren"][0]["payload"]["fixtures"]

	#with open("t", "w") as fh:
	#	json.dump(data, fh, indent=4)

	res = {}
	for propRow in data:
		for row in propRow["games"]:
			prop = row["name"]["value"].lower().split(": ")[-1]
			player = parsePlayer(row["name"]["value"].split(":")[0].split(" (")[0])

			isLine = True
			if prop == "regular season passing yards":
				prop = "pass_yd"
			elif prop == "regular season passing touchdowns":
				prop = "pass_td"
			elif prop == "regular season receiving yards":
				prop = "rec_yd"
			elif prop == "regular season receiving touchdowns":
				prop = "rec_td"
			elif prop == "regular season rushing yards":
				prop = "rush_yd"
			elif prop == "regular season rushing touchdowns":
				prop = "rush_td"
			elif prop == "regular season sacks":
				prop = "sacks"
			elif prop.split(" ")[0] == "most":
				isLine = False
				prop = "most_"+prop.split(" season ")[-1].replace(" ", "_").replace("passing", "pass").replace("receiving", "rec").replace("rushing", "rush").replace("touchdowns", "td").replace("yards", "yd")
			elif prop.endswith("to make the playoffs"):
				prop = "playoffs"
			#elif prop == "regular season wins":
			#	prop = "wins"
			else:
				continue

			if prop not in res:
				res[prop] = {}

			if prop == "playoffs":
				team = convertTeam(row["name"]["value"].lower().split(" to make ")[0])
				res[prop][team] = f"{row['results'][0]['americanOdds']}/{row['results'][1]['americanOdds']}"
			elif prop == "wins":
				team = convertTeam(row["name"]["value"].lower().split(":")[0])
				line = row["results"][0]["name"]["value"].split(" ")[-1]
				odds = str(row["results"][0]["americanOdds"])
				
				if team not in res[prop]:
					res[prop][team] = {}

				if line not in res[prop][team]:
					res[prop][team][line] = odds
				else:
					if row["results"][0]["name"]["value"].split(" ")[0] == "Under":
						res[prop][team][line] += f"/{odds}"
					else:
						res[prop][team][line] += f"{odds}/{res[prop][team][line]}"
			elif isLine:
				line = row["results"][0]["name"]["value"].split(" ")[-1]
				res[prop][player] = {
					line: f"{row['results'][0]['americanOdds']}/{row['results'][1]['americanOdds']}"
				}
			else:
				for result in row["results"]:
					player = parsePlayer(result["name"]["value"])
					res[prop][player] = str(result["americanOdds"])

	with open("static/nflfutures/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeDK():

	mainCats = {
		"player_stats": 782,
		"wins": 1286,
		"awards": 787,
		"futures": 529
	}
	
	subCats = {
		782: [7200, 14770, 7276, 7239, 7694, 7277, 13405, 13352, 13350, 13351],
		1286: [13354],
		787: [13342, 13343, 13339, 13340, 13341, 13344, 13345],
		529: [10500, 4652, 4651, 5629]
	}

	propIds = {
		7200: "pass_yd", 14770: "pass_td", 7276: "rec_yd", 7239: "rec_td", 7694: "rush_td", 7277: "rush_yd", 13352: "sacks", 13350: "int", 13351: "def_int", 13354: "wins", 13342: "oroy", 13343: "droy", 13339: "mvp", 13340: "opoy", 13341: "dpoy", 13344: "coach", 13345: "comeback", 10500: "superbowl", 4652: "playoffs", 4651: "conference", 5629: "division", 13405: "rec"
	}

	if False:
		mainCats = {
			"futures": 529
		}

		subCats = {
			529: [10500, 4652, 4651, 5629]
		}

	res = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/88808/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outfuture"
			os.system(f"curl \"{url}\" --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' -H 'Upgrade-Insecure-Requests: 1' -H 'Sec-Fetch-Dest: document' -H 'Sec-Fetch-Mode: navigate' -H 'Sec-Fetch-Site: none' -H 'Sec-Fetch-User: ?1' -H 'TE: trailers' -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			prop = propIds.get(subCat, "")

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				if mainCat == "player_stats":
					team = parsePlayer(event["name"].replace(" 2024/25", ""))
				else:
					team = convertTeam(event["name"])
				events[event["eventId"]] = team

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
							if "label" not in row:
								continue

							if subCat in propIds:
								prop = propIds[subCat]

							if prop not in res:
								res[prop] = {}

							outcomes = row["outcomes"]
							skip = 1
							if mainCat == "player_stats" or prop in ["wins", "playoffs"]:
								skip = 2

							for i in range(0, len(outcomes), skip):
								outcome = outcomes[i]
								if skip == 2:
									if row["eventId"] not in events:
										continue
									team = events[row["eventId"]]

									if team not in res[prop]:
										res[prop][team] = {}

									line = outcome["label"].split(" ")[-1]
									if prop in ["wins"]:
										line = str(outcome["line"])

									ou = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
									if "under" in outcome["label"].lower() or outcome["label"].lower() == "no":
										ou = outcomes[i+1]["oddsAmerican"]+"/"+outcome["oddsAmerican"]

									if prop in ["playoffs"]:
										res[prop][team] = ou
									else:
										res[prop][team][line] = ou
								else:
									#if prop in ["mvp", "cy_young", "roty"]:
									if mainCat == "awards":
										team = parsePlayer(outcome["participant"])
									elif mainCat == "leaders":
										team = parsePlayer(outcome["label"])
									else:
										team = convertTeam(outcome["participant"])
									res[prop][team] = outcome["oddsAmerican"]

	with open("static/nflfutures/draftkings.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePN(debug):
	outfile = "outfuture"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/889/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile

	os.system(url)
	with open(outfile) as fh:
		data = json.load(fh)

	outfile2 = "outfuture2"
	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/889/markets/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile2

	time.sleep(0.2)
	os.system(url)
	with open(outfile2) as fh:
		markets = json.load(fh)

	if debug:
		with open("t", "w") as fh:
			json.dump(data, fh, indent=4)

		with open("t2", "w") as fh:
			json.dump(markets, fh, indent=4)

	res = {}
	propData = {}
	for row in data:
		if "special" not in row:
			continue
		prop = row["special"]["category"].lower()
		desc = row["special"]["description"].lower()
		extra = row["participants"]

		if prop == "regular season wins":
			prop = "wins"
		elif prop == "futures":
			if desc.split(" ")[-2] in ["west", "east", "south", "north"]:
				prop = "division"
			elif desc.split(" ")[-1] == "winner":
				prop = "conference"
			elif "super bowl champion" in desc:
				prop = "superbowl"
		elif "most valuable player" in prop:
			prop = "mvp"
		elif "coach of the year" in prop:
			prop = "coach"
		elif "rookie of the year" in prop:
			if "offensive" in prop:
				prop = "oroy"
			else:
				prop = "droy"
		elif "player of the year" in prop:
			if "offensive" in prop:
				prop = "opoy"
			elif "comeback" in prop:
				prop = "comeback"
			else:
				prop = "dpoy"
		else:
			continue

		propData[row["id"]] = [prop, desc, extra]

	for row in markets:
		if row["matchupId"] not in propData:
			continue
		marketData = propData[row["matchupId"]]
		prop = marketData[0]
		desc = marketData[1]
		extra = marketData[2]
		outcomes = row["prices"]

		if prop not in res:
			res[prop] = {}

		skip = 2
		if prop in ["division", "conference", "superbowl", "mvp", "oroy", "droy", "opoy", "dpoy", "comeback", "coach"]:
			skip = 1

		for i in range(0, len(outcomes), skip):

			ou = str(outcomes[i]["price"])
			line = outcomes[i].get("points", 0)
			if skip == 2:
				ou += f"/{outcomes[i+1]['price']}"
				if (outcomes[i]['participantId'] == extra[0]['id'] and extra[0]['name'] == 'Under') or (outcomes[i]['participantId'] != extra[0]['id'] and extra[0]['name'] == 'Over'):
					ou = f"{outcomes[i+1]['price']}/{outcomes[i]['price']}"

				if line:
					res[prop][convertTeam(desc)] = {
						str(line): ou
					}
			else:
				teamData = [x for x in extra if x["id"] == outcomes[i]["participantId"]][0]
				if prop in ["division", "conference", "superbowl"]:
					res[prop][convertTeam(teamData["name"])] = ou
				else:
					res[prop][parsePlayer(teamData["name"].split(" (")[0])] = ou

	with open("static/nflfutures/pn.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi():
	outfile = "outfuture"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/american_football/nfl/all/all/competitions.json?lang=en_US&market=US&client_id=2&channel_id=7&ncid=1722267596039"

	os.system(f"curl \"{url}\" -o {outfile}")
	with open(outfile) as fh:
		j = json.load(fh)

	res = {}
	playerMarkets = False
	for event in j["events"]:
		prop = event["event"]["name"].lower()
		eventId = event["event"]["id"]

		player = team = mainProp = ""
		if prop == "super bowl 2024/2025":
			prop = "superbowl"
		elif prop.startswith("afc championship") or prop.startswith("nfc championship"):
			prop = "conference"
		elif prop.startswith("afc") or prop.startswith("nfc"):
			prop = "division"
		elif "mvp" in prop:
			prop = "mvp"
		elif "rookie of the year" in prop:
			if prop.startswith("defensive"):
				prop = "droy"
			else:
				prop = "oroy"
		elif "player of the year" in prop:
			if prop.startswith("defensive"):
				prop = "dpoy"
			elif prop.startswith("comeback"):
				prop = "comeback"
			else:
				prop = "opoy"
		elif prop.startswith("most "):
			prop = prop.split(" 2024")[0].replace("most ", "").replace("points", "pts").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yd").replace("touchdowns", "td").replace("interceptions", "int").replace("receptions", "rec")
			prop = prop.replace(" ", "_")
			if prop == "int":
				prop = "def_int"
			elif prop == "int_thrown":
				prop = "int"
			prop = f"most_{prop}"
		elif " markets " in prop:
			if prop.startswith("general") or prop.startswith("world"):
				continue

			if prop.startswith("derrick henry") or prop.startswith("lamar jackson") or prop.startswith("isiah pacheco"):
				playerMarkets = True

			if playerMarkets:
				player = parsePlayer(prop.split(" markets")[0])
			else:
				team = convertTeam(prop.split(" markets")[0])
			mainProp = prop = "market"
		else:
			continue

		#if prop not in ["market"]:
		#	continue

		if prop in ["market"]:
			url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json?includeParticipants=true"
			time.sleep(0.2)
			os.system(f"curl \"{url}\" -o {outfile}")
			with open(outfile) as fh:
				j = json.load(fh)
		else:
			j = event.copy()

		#with open("out", "w") as fh:
		#	json.dump(j, fh, indent=4)
		skip = 1
		if prop in ["market"]:
			skip = 2

		for offerRow in j["betOffers"]:
			outcomes = offerRow["outcomes"]
			offerLabel = offerRow["criterion"]["label"].lower()
			if "games won" in offerLabel:
				prop = "wins"
			elif offerLabel == "to reach the playoffs":
				prop = "playoffs"
			elif offerLabel.startswith("player's total"):
				prop = offerLabel.split(" total ")[-1].split(" - ")[0].replace("points", "pts").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yd").replace("touchdowns", "td").replace("interceptions", "int").replace("receptions", "rec")
				prop = prop.replace(" ", "_")
			elif mainProp == "market" and not playerMarkets:
				continue

			if prop not in res:
				res[prop] = {}

			for i in range(0, len(outcomes), skip):
				outcome = outcomes[i]
				if prop == "playoffs":
					res[prop][team] = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
				elif prop == "wins":
					if "line" not in outcome:
						continue
					line = str(outcome["line"] / 1000)
					if team not in res[prop]:
						res[prop][team] = {}
					res[prop][team][line] = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
				elif offerLabel.startswith("player's total"):
					line = str(outcome["line"] / 1000)
					res[prop][player] = {
						line: outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
					}
				elif prop in ["superbowl", "conference", "division"]:
					team = convertTeam(outcome["participant"].lower())
					res[prop][team] = outcome["oddsAmerican"]
				else:
					try:
						last, first = outcome["participant"].lower().split(", ")
						player = parsePlayer(f"{first} {last}")
					except:
						player = parsePlayer(outcome["participant"])
					res[prop][player] = outcome["oddsAmerican"]

	with open("static/nflfutures/kambi.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeCZ(token=None):
	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/americanfootball/events/futures?competitionIds=007d7c61-07a7-4e18-bb40-15104b6eac92"
	outfile = "outfuture"

	cookie = "3d6dfd09-53ab-4872-89e0-136b34b8ceb8:EgoAqiZbtq4OAQAA:gAM/7bhmyH8VcVkjz2ZWivdEKdsePcPuklrVAFVUoK8xD9sbFmdqGXTBGJd7n7ScwgMv/p44y86rmUJLTtPpWGheExuRGUQRIpwswg4kXE5BqMwL4JNWA6JYzeHCzJPNYA07+83ejN5SK0iqZicpevcePdfZobPWBFYye1sO2rtCJpDhNYTMUZrI9na7y9tSp8t+prK1H0wEpe1iJ9AUWZ7F4nxmw+k4ZKi88Zy/Fyzeh9u4H83e3WvbVLh12uoA7PZIllih21QcYy6lUQ=="
	if token:
		cookie = token
	os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	res = {}
	for event in data["competitions"][0]["events"]:
		for market in event["markets"]:
			if not market["display"]:
				continue

			prop = market["name"].lower().replace("|", "")
			if prop == "division winner":
				prop = "division"
			elif prop == "regular season mvp":
				prop = "mvp"
			elif "regular season wins" in prop:
				prop = "wins"
			elif prop == "to make the playoffs":
				prop = "playoffs"
			elif prop == "super bowl winner":
				prop = "superbowl"
			elif "player of the year" in prop:
				if "comeback" in prop:
					prop = "comeback"
				else:
					prop = prop.split(" ")[0][0]+"poy"
			elif "rookie of the year" in prop:
				prop = prop.split(" ")[0][0]+"roy"
			elif prop.startswith("most"):
				if "Rookie" in event["name"]:
					continue
				prop = "most_"+prop.split(" season ")[-1].replace("passing", "pass").replace("yards", "yd").replace("touchdowns", "td").replace("rushing", "rush").replace("receiving", "rec").replace(" ", "_")
			elif prop.startswith("total regular season"):
				if "Leader" in event["name"]:
					continue
				prop = prop.split(" season ")[-1].replace("passing", "pass").replace("yards", "yd").replace("touchdowns", "td").replace("rushing", "rush").replace("receiving", "rec").replace(" ", "_")
				if prop == "touchdown_passes":
					prop = "pass_td"
			else:
				#print(event["name"], prop)
				continue

			if prop not in res:
				res[prop] = {}

			selections = market["selections"]
			skip = 2

			if prop in ["superbowl", "conference", "division", "mvp", "opoy", "dpoy", "oroy", "droy", "comeback"] or "most" in prop:
				skip = 1

			for i in range(0, len(selections), skip):
				try:
					ou = str(selections[i]["price"]["a"])
				except:
					continue
				if skip == 2:
					ou += f"/{selections[i+1]['price']['a']}"
					if selections[i]["name"].lower().replace("|", "") == "under":
						ou = f"{selections[i+1]['price']['a']}/{selections[i]['price']['a']}"

				if skip == 1:
					if prop in ["division", "conference", "superbowl"]:
						team = convertTeam(selections[i]["name"].replace("|", ""))
					else:
						team = parsePlayer(selections[i]["name"].replace("|", ""))
					res[prop][team] = ou
				elif "td" in prop or "yd" in prop or prop in ["sacks"]:
					player = parsePlayer(event["name"].replace("|", "").split(" 2024")[0]).strip()
					line = str(market["line"])
					if player not in res[prop]:
						res[prop][player] = {}
					res[prop][player][line] = ou
				else:
					team = convertTeam(event["name"].replace("|", ""))

					if prop in ["wins"]:
						line = str(market["line"])
						if team not in res[prop]:
							res[prop][team] = {}
						res[prop][team][line] = ou
					else:
						res[prop][team] = ou


	with open("static/nflfutures/cz.json", "w") as fh:
		json.dump(res, fh, indent=4)

def write365():

	js = """
	{
		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.replace(". ", "");
			if (team.split(" ")[0].length == 2) {
				t = team.split(" ")[0];
				if (["la", "ny"].includes(t)) {
					t = team.replace(" ", "").substring(0, 3);
				}
			} else {
				t = t.substring(0, 3);
			}
			if (t == "los") {
				if (team.includes("chargers")) {
					return "lac";
				}
				return "lar";
			} else if (t == "new") {
				if (team.includes("jets")) {
					return "nyj";
				} else if (team.includes("patriots")) {
					return "ne";
				} else if (team.includes("saints")) {
					return "no";
				}
				return "nyg";
			} else if (t == "tam") {
				return "tb";
			} else if (t == "kan") {
				return "kc";
			} else if (t == "jac") {
				return "jax";
			} else if (t == "gre") {
				return "gb";
			} else if (t == "san") {
				return "sf";
			} else if (t == "las") {
				return "lv";
			} else if (t == "arz") {
				return "ari";
			}
			return t;
		}

		function parsePlayer(player) {
			let p = player.toLowerCase().replaceAll(". ", " ").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			if (p == "amon ra stbrown") {
				return "amon ra st brown"
			}
			return p;
		}

		async function main() {
			let data = {};
			for (el of document.querySelectorAll(".src-FixtureSubGroupWithShowMore_Closed")) {
				el.click();
				await new Promise(resolve => setTimeout(resolve, 10));
			}

			for (el of document.querySelectorAll(".msl-ShowMore_Link")) {
				if (el.innerText == "Show more") {
					el.click();
					await new Promise(resolve => setTimeout(resolve, 500));
				}
			}

			let prop = document.querySelector(".rcl-MarketGroupButton_MarketTitle").innerText.toLowerCase();

			let skip = 1;
			let isPlayer = false;
			if (prop == "to win outright") {
				prop = "superbowl";
			} else if (prop == "to win conference") {
				prop = "conference";
			} else if (prop == "to win division") {
				prop = "division";
			} else if (prop == "mvp") {
				prop = "mvp";
			} else if (prop == "regular season awards") {
				prop = "awards";

			} else if (prop == "regular season stat leaders") {
				prop = "leaders";
			} else if (prop == "regular season wins") {
				prop = "wins";
			} else if (prop == "to make the playoffs") {
				prop = "playoffs";
			} else if (prop.includes("player")) {
				prop = prop.split("player ")[1].split(" regular")[0].replace(" ", "_").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yd").replace("touchdowns", "td").replace("receptions", "rec").replace("defensive", "def").replace("interceptions", "int");
				if (prop == "regular_season int") {
					prop = "int";
				} else if (prop == "regular_season rec") {
					prop = "rec";
				}
				skip = 2;
				isPlayer = true;
			} else if (prop.includes("leaders")) {
				prop = "leaders";
			}

			let mainProp = prop;

			if (prop.includes("_yd") || prop == "wins" || prop == "playoffs") {
				data[prop] = {};
				let teams = [];
				for (let div of document.querySelectorAll(".srb-ParticipantLabel_Name")) {
					if (isPlayer) {
						teams.push(parsePlayer(div.innerText));
					} else {
						teams.push(convertTeam(div.innerText));
					}
				}
				let overs = [];
				let div = document.querySelectorAll(".gl-Market")[1];
				for (let overDiv of div.querySelectorAll(".gl-Participant_General")) {
					let spans = overDiv.querySelectorAll("span"); 
					if (spans.length == 1) {
						overs.push(spans[0].innerText);
					} else {
						overs.push(spans[1].innerText);
					}
				}
				div = document.querySelectorAll(".gl-Market")[2];
				let idx = 0;
				for (let underDiv of div.querySelectorAll(".gl-Participant_General")) {
					let spans = underDiv.querySelectorAll("span"); 
					if (spans.length == 1) {
						let odds = spans[0].innerText;
						data[prop][teams[idx]] = overs[idx]+"/"+odds;
					} else {
						let line = spans[0].innerText;
						let odds = spans[1].innerText;
						if (!data[prop][teams[idx]]) {
							data[prop][teams[idx]] = {};
						}
						data[prop][teams[idx]][line] = overs[idx]+"/"+odds;
					}
					idx += 1;
				}
			} else if (prop) {
				let player = "";
				for (let row of document.querySelectorAll(".gl-MarketGroupPod")) {

					if (row.innerText.includes("Others on Request")) {
						continue;
					}
					if (prop.includes("_td") || prop == "sacks" || prop == "int" || prop == "rec") {
						player = parsePlayer(row.querySelector(".src-FixtureSubGroupButton_Text").innerText);
					}

					if (mainProp == "leaders") {
						prop = row.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase();
						if (prop.includes("scrimmage") || prop.includes("&") || prop.includes("qb with")) {
							continue;
						}
						prop = prop.split("season ")[1].split(" - ")[0].replace(" ", "_").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yd").replace("touchdowns", "td").replace("td's", "td").replace("receptions", "rec").replace("defensive", "def").replace("interceptions", "int").replace("_thrown", "");
						prop = "most_"+prop;
					} else if (mainProp == "awards") {
						prop = row.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase();
						if (prop.includes("rookie of the year")) {
							if (prop.includes("offensive")) {
								prop = "oroy";
							} else {
								prop = "droy";
							}
						} else if (prop.includes("comeback")) {
							prop = "comeback";
						} else if (prop.includes("player of the year")) {
							if (prop.includes("offensive")) {
								prop = "opoy";
							} else {
								prop = "dpoy";
							}
						}
					}

					if (!data[prop]) {
						data[prop] = {};
					}

					let btns = row.querySelectorAll(".gl-Participant_General");
					for (let i = 0; i < btns.length; i += skip) {
						if (!btns[i].querySelector("span")) {
							continue;
						}
						let team = btns[i].querySelector("span").innerText;
						let odds = btns[i].querySelectorAll("span")[1].innerText;

						if (skip == 1) {
							if (["roty", "cy_young", "mvp"].includes(prop) || ["leaders", "awards"].includes(mainProp)) {
								data[prop][parsePlayer(team)] = odds;
							} else {
								data[prop][convertTeam(team)] = odds;
							}
						} else {
							let ou = odds;
							ou += "/"+btns[i+1].querySelectorAll("span")[1].innerText;
							if (team.indexOf("- No") >= 0) {
								ou = btns[i+1].querySelectorAll("span")[1].innerText+"/"+odds;
							}
							if (prop.includes("_td") || prop == "sacks" || prop == "int" || prop == "rec") {
								data[prop][player] = {};
								data[prop][player][team.split(" ")[1]] = ou;
							} else if (prop == "playoffs") {
								team = row.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().split(" to ")[0];
								data[prop][convertTeam(team)] = ou;
							} else {
								data[prop][parsePlayer(team.split(" - ")[0])] = ou;
							}
						}
					}
				}
			}
			console.log(data);
		}

		main();
	}
"""

def writeFanduelManual():

	js = """

	{
		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.replace(". ", "").substring(0, 3);
			if (t == "los") {
				if (team.includes("chargers")) {
					return "lac";
				}
				return "lar";
			} else if (t == "new") {
				if (team.includes("jets")) {
					return "nyj";
				} else if (team.includes("patriots")) {
					return "ne";
				} else if (team.includes("saints")) {
					return "no";
				}
				return "nyg";
			} else if (t == "tam") {
				return "tb";
			} else if (t == "kan") {
				return "kc";
			} else if (t == "jac") {
				return "jax";
			} else if (t == "gre") {
				return "gb";
			} else if (t == "san") {
				return "sf";
			} else if (t == "las") {
				return "lv";
			}
			return t;
		}

		function parsePlayer(player) {
			return player.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
		}


		async function main() {
			const arrows = document.querySelectorAll("div[data-test-id='ArrowAction']");

			for (const arrow of arrows) {
				if (arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
					arrow.click();
				}

				await new Promise(resolve => setTimeout(resolve, 0.1));
			}

			for (let el of document.querySelectorAll("div[aria-label='Show more']")) {
				if (el) {
					el.click();
					await new Promise(resolve => setTimeout(resolve, 0.1));
				}
			}

			let tab = document.querySelectorAll("div[aria-selected=true]")[0].innerText.toLowerCase();
			let btns = Array.from(document.querySelectorAll("ul")[5].querySelectorAll("div[role=button]"));
			for (let i = 0; i < btns.length; i += 1) {
				player = "";
				const btn = btns[i];
				let label = btn.getAttribute("aria-label");
				if (!label) {
					continue;
				}
				label = label.toLowerCase();
				if (label.includes("unavailable") || label[0] == ",") {
					continue;
				}

				let prop = "";

				if (["rookies", "conferences", "divisions", "season awards", "super bowl"].includes(tab) || (tab == "defensive props" && label.split(", ").length <= 2)) {
					let parent = btn.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement.parentElement;
					if (parent.nodeName != "LI") {
						continue;
					}
					while (parent.querySelector("h3[role=heading]") == null) {
						parent = parent.previousSibling;
					}
					prop = parent.querySelector("h3[role=heading]").innerText.toLowerCase();
					if (prop.includes("comeback")) {
						prop = "comeback";
					} else if (prop.includes("coach")) {
						if (prop.includes("assistant")) {
							continue;
						}
						prop = "coach";
					} else if (prop.includes("rookie of the year")) {
						if (prop.includes("offensive")) {
							prop = "oroy";
						} else {
							prop = "droy";
						}
					} else if (prop.includes("player of the year")) {
						if (prop.includes("offensive")) {
							prop = "opoy";
						} else {
							prop = "dpoy";
						}
					} else if (tab == "season awards" && prop.includes("mvp")) {
						if (prop.includes("parlay")) {
							continue;
						}
						prop = "mvp";
					} else if (prop.includes("championship winner")) {
						prop = "conference";
					} else if (tab == "divisions" && prop.includes("winner")) {
						prop = "division";
					} else if (prop.includes("most regular season sacks")) {
						prop = "most_sacks";
					} else if (tab == "super bowl" && prop.includes("outright")) {
						prop = "superbowl";
					} else {
						continue;
					}
				} else {
					prop = label.split(", ")[0];
					if (prop.includes("regular season total ")) {
						prop = label.split(", ")[0].split(" total ")[1].split(" 2024")[0].replace(" ", "_").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yd").replace("tds", "td").replace("receptions", "rec").replace("defensive", "def").replace("interceptions", "int");
						player = parsePlayer(label.split(" regular")[0].split(" 2024")[0]);
						i += 1;
					} else if (prop.includes("most regular season")) {
						prop = label.split(", ")[0].split(" season ")[1].split(" 2024")[0].replace(" ", "_").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yd").replace("tds", "td").replace("receptions", "rec").replace("defensive", "def").replace("interceptions", "int");
						prop = "most_"+prop;
						if (prop.includes("return")) {
							continue;
						}
					} else if (prop.includes(" - to make the playoffs")) {
						prop = "playoffs";
						i += 1;
					} else if (prop.includes("regular season wins")) {
						prop = "wins";
						i += 1;
					} else {
						continue;
					}
				}

				if (!data[prop]) {
					data[prop] = {};
				}

				if (player) {
					line = label.split(", ")[1].split(" ")[1];
					if (!data[prop][player]) {
						data[prop][player] = {};
					}
					data[prop][player][line] = label.split(", ")[2]+"/"+btns[i].getAttribute("aria-label").split(", ")[2];
				} else if (prop != "most_sacks" && prop.includes("most")) {
					player = parsePlayer(label.split(", ")[1]);
					data[prop][player] = label.split(", ")[2];
				} else if (prop == "playoffs") {
					team = convertTeam(label.split(" - ")[0]);
					data[prop][team] = label.split(", ")[2]+"/"+btns[i].getAttribute("aria-label").split(", ")[2];
				} else if (prop == "wins") {
					team = convertTeam(label.split(" regular ")[0].split(" - ")[0]);
					line = label.split(", ")[1].split(" ")[1];
					if (!data[prop][team]) {
						data[prop][team] = {};
					}
					data[prop][team][line] = label.split(", ")[2]+"/"+btns[i].getAttribute("aria-label").split(", ")[2];
				} else if (prop == "superbowl") {
					team = convertTeam(label.split(", ")[0]);
					data[prop][team] = label.split(", ")[1];
				} else if (["conference", "division"].includes(prop)) {
					player = convertTeam(label.split(", ")[0]);
					data[prop][player] = label.split(", ")[1];
				} else {
					player = parsePlayer(label.split(", ")[0]);
					data[prop][player] = label.split(", ")[1];
				}
			}

			console.log(data);
		}

		main();
	}

"""

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None):
	if not boost:
		boost = 1

	with open(f"static/nflfutures/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"static/nflfutures/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"static/nflfutures/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"static/nflfutures/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"static/nflfutures/pn.json") as fh:
		pnLines = json.load(fh)

	with open(f"static/nflfutures/cz.json") as fh:
		czLines = json.load(fh)

	with open(f"static/nflfutures/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"static/nflfutures/espn.json") as fh:
		espnLines = json.load(fh)

	lines = {
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"dk": dkLines,
		"pn": pnLines,
		"cz": czLines,
		"bet365": bet365Lines,
		"espn": espnLines
	}

	with open("static/nflfutures/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	props = {}
	for book in lines:
		for prop in lines[book]:
			props[prop] = 1

	for prop in props:
		if propArg and prop != propArg:
			continue
		handicaps = {}
		for book in lines:
			lineData = lines[book]
			if prop in lineData:
				if type(lineData[prop]) is not dict:
					handicaps[(" ", " ")] = ""
					break
				for handicap in lineData[prop]:
					player = playerHandicap = ""
					try:
						player = float(handicap)
						player = ""
						handicaps[(handicap, playerHandicap)] = player
					except:
						player = handicap
						playerHandicap = ""
						if type(lineData[prop][player]) is dict:
							for h in lineData[prop][player]:
								handicaps[(handicap, h)] = player
						elif type(lineData[prop][player]) is str:
							handicaps[(handicap, " ")] = player
						else:
							for h in lineData[prop][player]:
								handicaps[(handicap, " ")] = player

		for handicap, playerHandicap in handicaps:
			player = handicaps[(handicap, playerHandicap)]
			for i in range(2):
				highestOdds = []
				books = []
				odds = []

				for book in lines:
					lineData = lines[book]
					if prop in lineData:
						if type(lineData[prop]) is str:
							val = lineData[prop]
						else:
							if handicap not in lineData[prop]:
								continue
							val = lineData[prop][handicap]

						if player.strip():
							if type(val) is dict:
								if playerHandicap not in val:
									continue
								val = lineData[prop][handicap][playerHandicap]
							else:
								val = lineData[prop][handicap].split(" ")[-1]

						#if player == "ronald acuna":
						#	print(book, prop, player, val)
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
					#print(player, prop, books, odds)
					continue

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
				l.remove(maxOU)
				books.remove(evBook)

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
					
				key = f"{handicap} {playerHandicap} {prop} {'over' if i == 0 else 'under'}"
				if key in evData:
					continue

				devig(evData, key, ou, line, prop=prop)
				if key not in evData:
					continue
				implied = 0
				if line > 0:
					implied = 100 / (line + 100)
				else:
					implied = -1*line / (-1*line + 100)
				implied *= 100

				evData[key]["imp"] = round(implied)
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

	with open("static/nflfutures/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def printEV():
	with open(f"static/nflfutures/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], player, d["playerHandicap"], d["line"], d["book"], j, d))

	for row in sorted(data):
		print(row[:-1])

	output = "\t".join(["EV", "EV Book", "Imp", "Player", "Prop", "O/U", "FD", "DK", "MGM", "CZ", "Kambi/BR", "PN", "Bet365", "ESPN"]) + "\n"
	for row in sorted(data, reverse=True):
		player = row[-1]["player"].title()
		if len(player) < 4:
			player = player.upper()
		prop = row[-1]["prop"]
		
		ou = ("u" if row[-1]["under"] else "o")+" "
		if player:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR").replace("BET", ""), f"{round(row[-1]['imp'])}%", player, row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "cz", "kambi", "pn", "bet365", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nflfutures/props.csv", "w") as fh:
		fh.write(output)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--dk", action="store_true", help="Fanduel")
	parser.add_argument("--mgm", action="store_true", help="MGM")
	parser.add_argument("--kambi", action="store_true")
	parser.add_argument("--pn", action="store_true")
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("--cz", action="store_true")
	parser.add_argument("--ev", action="store_true")
	parser.add_argument("--summary", action="store_true")
	parser.add_argument("-u", "--update", action="store_true")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--token")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("-p", "--print", action="store_true", help="Print")

	args = parser.parse_args()

	if args.mgm:
		writeMGM()

	if args.dk:
		writeDK()

	if args.cz:
		writeCZ(args.token)

	if args.kambi:
		writeKambi()

	if args.pn:
		writePN(args.debug)

	if args.ev:
		writeEV(args.prop, args.book, args.team, args.boost)
	if args.print:
		printEV()

	if args.update:
		writeMGM()
		writeDK()
		writeCZ(args.token)
		writeKambi()
		writePN(args.debug)

	if args.summary:
		with open(f"static/nflfutures/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"static/nflfutures/mgm.json") as fh:
			mgmLines = json.load(fh)

		with open(f"static/nflfutures/fanduel.json") as fh:
			fdLines = json.load(fh)

		with open(f"static/nflfutures/draftkings.json") as fh:
			dkLines = json.load(fh)

		with open(f"static/nflfutures/pn.json") as fh:
			pnLines = json.load(fh)

		with open(f"static/nflfutures/cz.json") as fh:
			czLines = json.load(fh)

		with open(f"static/nflfutures/bet365.json") as fh:
			bet365Lines = json.load(fh)

		lines = {
			"kambi": kambiLines,
			"mgm": mgmLines,
			"fd": fdLines,
			"cz": czLines,
			"dk": dkLines,
			"pn": pnLines,
			"bet365": bet365Lines
		}

		for book in lines:
			for prop in lines[book]:
				if prop != args.prop:
					continue
				for team in lines[book][prop]:
					if team != args.team:
						continue

					print(book, prop, lines[book][prop][team])