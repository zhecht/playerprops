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

from shared import convertImpOdds, convertAmericanFromImplied, convertMLBTeam

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")

def convertTeam(team):
	team = team.lower().replace(".", "").replace(" ", "")
	t = team.split(" ")[0][:3]
	if t == "was":
		t = "wsh"
	elif t == "san":
		if "padres" in team:
			t = "sd"
		else:
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
	elif "whitesox" in team:
		t = "chw"
	return t

def convertMGMTeam(team):
	if team == "diamondbacks":
		return "ari"
	elif team == "braves":
		return "atl"
	elif team == "orioles":
		return "bal"
	elif team == "red sox":
		return "bos"
	elif team == "cubs":
		return "chc"
	elif team == "white sox":
		return "chw"
	elif team == "reds":
		return "cin"
	elif team == "guardians":
		return "cle"
	elif team == "rockies":
		return "col"
	elif team == "tigers":
		return "det"
	elif team == "astros":
		return "hou"
	elif team == "royals":
		return "kc"
	elif team == "angels":
		return "laa"
	elif team == "dodgers":
		return "lad"
	elif team == "marlins":
		return "mia"
	elif team == "brewers":
		return "mil"
	elif team == "twins":
		return "min"
	elif team == "mets":
		return "nym"
	elif team == "yankees":
		return "nyy"
	elif team == "athletics":
		return "ath"
	elif team == "phillies":
		return "phi"
	elif team == "pirates":
		return "pit"
	elif team == "padres":
		return "sd"
	elif team == "giants":
		return "sf"
	elif team == "mariners":
		return "sea"
	elif team == "cardinals":
		return "stl"
	elif team == "rays":
		return "tb"
	elif team == "rangers":
		return "tex"
	elif team == "blue jays":
		return "tor"
	elif team == "nationals":
		return "wsh"
	return team

def writeMGM():
	ids = ["14881765", "14944813"]
	for fixture in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={fixture}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&isBettingInsightsEnabled=true&useRegionalisedConfiguration=true&includeRelatedFixtures=false&statisticsModes=All"
		outfile = "outfuture"
		time.sleep(0.2)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		data = data["fixture"]
		res = {}
		for gameRow in data["games"]:
			prop = gameRow["name"]["value"].strip().lower()
			player = ""
			if prop == "world series winner":
				prop = "world_series"
			elif "league winner" in prop:
				prop = "league"
			elif prop.endswith(" leader"):
				prop = prop.split(" season ")[-1].replace("home run", "hr").replace("hits", "h").replace("strikeout", "k").replace("saves", "sv").replace("doubles", "double").replace("triples", "triple").replace("stolen base", "sb")
				prop = prop.replace(" ", "_")
			elif "must play 159 regular season" in prop:
				player = parsePlayer(prop.split(" (")[0].split(" will ")[-1])
				p = "hr"
				if "strikeouts" in prop:
					p = "k"
				prop = p
			else:
				#print(prop)
				continue

			if prop not in res:
				res[prop] = {}

			if player:
				res[prop][player] = {}
				line = gameRow["results"][0]["name"]["value"].split(" ")[-1]
				res[prop][player][line] = str(gameRow["results"][0]["americanOdds"])+"/"+str(gameRow["results"][1]["americanOdds"])
				continue

			for row in gameRow["results"]:
				if "leader" in prop:
					team = parsePlayer(row["name"]["value"])
				else:
					team = convertMGMTeam(row["name"]["value"].lower())
				odds = str(row["americanOdds"])

				res[prop][team] = odds


	with open("static/mlbfutures/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePN(debug):
	outfile = "outfuture"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/246/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile

	os.system(url)
	with open(outfile) as fh:
		data = json.load(fh)

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/246/markets/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile

	time.sleep(0.2)
	os.system(url)
	with open(outfile) as fh:
		markets = json.load(fh)

	if debug:
		with open("t", "w") as fh:
			json.dump(data, fh, indent=4)

		with open("t2", "w") as fh:
			json.dump(markets, fh, indent=4)

	res = {}
	propData = {}
	for row in data:
		prop = row["special"]["category"].lower()
		desc = row["special"]["description"].lower()
		extra = row["participants"]

		if prop == "regular season wins":
			prop = "team_wins"
		elif prop == "futures":
			if desc.split(" ")[-2] in ["west", "east", "central"]:
				prop = "division"
			elif desc.split(" ")[-2] == "pennant":
				prop = "league"
			elif "world series champion" in desc:
				prop = "world_series"
		elif prop.endswith("mvp"):
			prop = "mvp"
		elif prop.endswith("rookie of the year"):
			prop = "roty"
		elif "cy young" in prop:
			prop = "cy_young"
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
		if prop in ["division", "league", "world_series", "mvp", "roty", "cy_young"]:
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
				if prop in ["division", "league", "world_series"]:
					res[prop][convertTeam(teamData["name"])] = ou
				else:
					res[prop][parsePlayer(teamData["name"])] = ou

	with open("static/mlbfutures/pn.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi(keep = None):
	outfile = "outfuture"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/baseball/mlb/all/all/competitions.json?lang=en_US&market=US&client_id=2&channel_id=7&ncid=1710474292570"

	res = {}
	if keep:
		with open("static/mlbfutures/kambi.json") as fh:
			res = json.load(fh)

	os.system(f"curl \"{url}\" -o {outfile}")
	with open(outfile) as fh:
		j = json.load(fh)

	playerMarkets = False
	for event in j["events"]:
		prop = event["event"]["name"].lower()
		eventId = event["event"]["id"]

		player = team = ""
		if prop == "world series 2025":
			prop = "world_series"
		elif prop == "american league 2025" or prop == "national league 2025":
			prop = "league"
		elif " west " in  prop or " east " in prop or " central " in prop:
			prop = "division"
		elif "cy young" in prop:
			prop = "cy_young"
		elif "rookie of the year" in prop:
			prop = "roty"
		elif " mvp " in prop:
			prop = "mvp"
		elif " leader " in prop:
			prop = prop.split(" 2025")[0].replace("home run", "hr").replace("hits", "h").replace("runs", "r").replace("strikeout", "k").replace("saves", "sv").replace("doubles", "double").replace("triples", "triple").replace("stolen base", "sb")
			prop = prop.replace(" ", "_")
		elif " markets " in prop:
			if prop.startswith("general") or prop.startswith("world"):
				continue

			if prop == "aaron judge markets 2025":
				playerMarkets = True

			if playerMarkets:
				player = parsePlayer(prop.split(" markets")[0])
			else:
				team = convertTeam(prop.split(" markets")[0])
			prop = "market"
		elif prop.startswith("mlb milestones"):
			prop = "milestones"
		else:
			#print(prop)
			continue

		#continue
		if prop in ["milestones"]:
			#continue
			pass

		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json?includeParticipants=true"
		time.sleep(0.2)
		os.system(f"curl \"{url}\" -o {outfile}")
		with open(outfile) as fh:
			j = json.load(fh)

		#with open("out", "w") as fh:
		#	json.dump(j, fh, indent=4)
		skip = 1
		if prop in ["market"]:
			skip = 2

		for offerRow in j["betOffers"]:
			outcomes = offerRow["outcomes"]
			offerLabel = offerRow["criterion"]["label"].lower()
			mainLine = ""

			if "make the playoffs" in offerLabel:
				prop = "playoffs"
			elif "total matches won" in offerLabel:
				prop = "team_wins"
			elif offerLabel.startswith("total runs scored"):
				prop = "r"
			elif offerLabel.startswith("total rbis"):
				prop = "rbi"
			elif offerLabel.startswith("total home runs"):
				prop = "hr"
			elif offerLabel.startswith("total hits"):
				prop = "h"
			elif offerLabel.startswith("stolen bases"):
				prop = "sb"
			elif offerLabel.startswith("total strikeouts"):
				prop = "k"
			elif offerLabel.startswith("total wins by the pitcher"):
				prop = "w"
			elif offerLabel.startswith("team to win at least"):
				mainLine = str(float(offerLabel.split(" ")[5].replace("+", "")) - 0.5)
				prop =  "team_wins"
			elif offerLabel.startswith("player to record"):
				mainLine = str(float(offerLabel.split(" ")[3].replace("+", "")) - 0.5)
				if offerLabel.endswith("strikeouts"):
					prop = "k"
				elif offerLabel.endswith("stolen bases"):
					prop = "sb"
				elif offerLabel.endswith("hits"):
					prop = "h"
				elif offerLabel.endswith("home runs"):
					prop = "hr"

			if prop not in res:
				res[prop] = {}

			for i in range(0, len(outcomes), skip):
				outcome = outcomes[i]
				if prop == "playoffs":
					try:
						res[prop][team] = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
					except:
						continue
				elif prop == "team_wins":
					if "oddsAmerican" not in outcome:
						continue
					if mainLine:
						team = convertMLBTeam(outcome["participant"])
						ou = outcome["oddsAmerican"]
						line = mainLine
					else:
						ou = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
						line = str(outcome["line"] / 1000)

					if team not in res[prop]:
						res[prop][team] = {}
					res[prop][team][line] = ou
				elif not mainLine and prop in ["r", "rbi", "hr", "h", "sb", "k", "w"]:
					if "line" not in outcome:
						continue
					line = str(outcome["line"] / 1000)
					ou = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
					if player not in res[prop]:
						res[prop][player] = {}
					res[prop][player][line] = ou
				elif prop in ["world_series", "league", "division"]:
					team = convertTeam(outcome["participant"].lower())
					res[prop][team] = outcome["oddsAmerican"]
				else:
					if "participant" not in outcome or "oddsAmerican" not in outcome:
						continue
					try:
						last, first = outcome["participant"].lower().split(", ")
						player = parsePlayer(f"{first} {last}")
					except:
						player = parsePlayer(outcome["participant"])

					if player not in res[prop]:
						res[prop][player] = {}

					if mainLine:
						res[prop][player][mainLine] = outcome["oddsAmerican"]
					else:
						res[prop][player] = outcome["oddsAmerican"]

	with open("static/mlbfutures/kambi.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBV():

	res = {}
	for which in ["mlb-futures", "mlb-season-props"]:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description/baseball/{which}?marketFilterId=rank&preMatchOnly=true&eventsLimit=1000&lang=en"
		outfile = "outfuture"
		os.system(f"curl \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		for mainRow in data:
			for eventRow in mainRow["events"]:
				for marketRow in eventRow["displayGroups"][0]["markets"]:
					prop = marketRow["description"].lower()
					player = mainLine = ""
					if prop.split(" total ")[-1] in ["strikeouts", "wins", "hits", "home runs", "rbis", "stolen bases"]:
						player = parsePlayer(prop.split(" total ")[0])
						prop = prop.split(" total ")[-1].replace("strikeouts", "k").replace("wins", "w").replace("hits", "h").replace("home runs", "hr").replace("rbis", "rbi").replace("runs scored", "r").replace("stolen bases", "sb")
					elif "to record" in prop and "+ regular season" in prop:
						mainLine = str(float(prop.split(" ")[3].replace("+", "")) - 0.5)
						prop = prop.split(" season ")[-1].replace("strikeouts", "k").replace("wins", "w").replace("hits", "h").replace("home runs", "hr").replace("rbis", "rbi").replace("runs scored", "r").replace("stolen bases", "sb")
					elif prop.endswith(" era"):
						player = parsePlayer(prop.split(" - ")[-1].split(" era")[0])
						prop = "era"
					elif "regular season wins" in prop:
						player = convertTeam(eventRow["description"].lower().split(" wins")[0])
						prop = "team_wins" 
					elif "to make the playoffs" in prop:
						prop = "playoffs"
					elif "world series winner" in prop:
						prop = "world_series"
					elif "american league winner" in prop or "national league winner" in prop:
						prop = "league"
					elif prop.split(" ")[-1] in ["west", "east", "central"]:
						prop = "division"
					elif "cy young" in prop:
						prop = "cy_young"
					elif "mvp" in prop:
						prop = "mvp"
					elif prop.endswith(" roy"):
						prop = "roty"
					elif "player to hit the most" in prop:
						prop = prop.split(" most ")[-1].replace("doubles", "double").replace("home runs", "hr").replace("hits", "h").replace("rbis", "rbi").replace("regular season wins", "w").replace("saves", "sv").replace("stolen bases", "sb").replace("strikeouts", "k")
						if "dnu" in prop:
							continue
						prop += "_leader"
					else:
						#print(prop)
						continue

					if prop not in res:
						res[prop] = {}

					skip = 2
					if prop in ["world_series", "league", "division", "cy_young", "mvp", "roty"] or "leader" in prop or mainLine:
						skip = 1
					outcomes = marketRow["outcomes"]
					for i in range(0, len(outcomes), skip):
						outcome = outcomes[i]
						ou = outcome["price"]["american"]
						if skip == 2:
							ou = outcome["price"]["american"]+"/"+outcomes[i+1]["price"]["american"]
						ou = ou.replace("EVEN", "100")
						if player:
							line = outcome["description"].split(" ")[-1]
							res[prop][player] = {
								line: ou
							}
						elif skip == 1:
							if prop in ["cy_young", "mvp", "roty"] or "leader" in prop or mainLine:
								team = parsePlayer(outcome["description"].split(" (")[0])
							else:
								team = convertTeam(outcome["description"])
							if mainLine:
								if team not in res[prop]:
									res[prop][team] = {}
								res[prop][team][mainLine] = ou
							else:
								res[prop][team] = ou
						elif prop == "playoffs":
							team = convertTeam(eventRow["description"].split(" to ")[0])
							res[prop][team] = ou
						else:
							team = convertTeam(marketRow["description"])
							res[prop][team] = ou



	with open("static/mlbfutures/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)


def writeDK(date=None):
	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"futures": 517,
		"awards": 684,
		"player_totals": 1279,
		"leaders": 685
	}
	
	subCats = {
		517: [9916, 9917, 5628, 10988, 10821],
		684: [5946, 12562, 5982],
		685: [5884, 5885, 5886, 5888, 5889, 5892, 15114, 15115],
		1279: [13302, 13319, 14944, 15076, 15078, 15165]
	}

	propIds = {
		9916: "world_series", 9917: "league", 5628: "division", 10988: "team_wins", 10821: "playoffs", 5946: "mvp", 12562: "cy_young", 5982: "roty", 13302: "hr", 13319: "k",  14944: "sb", 15076: "rbi", 15078: "h", 15165: "30/30", 5884: "hr_leader", 5885: "rbi_leader", 5886: "h_leader", 5888: "r_leader", 5889: "sb_leader", 5892: "sv_leader", 15114: "double_leader", 15115: "triple_leader"
	}

	if False:
		mainCats = {
			"leaders": 685
		}

		subCats = {
			685: [5884]
		}

	lines = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/84240/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outmlb"
			os.system(f"curl \"{url}\" --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' -H 'Upgrade-Insecure-Requests: 1' -H 'Sec-Fetch-Dest: document' -H 'Sec-Fetch-Mode: navigate' -H 'Sec-Fetch-Site: none' -H 'Sec-Fetch-User: ?1' -H 'TE: trailers' -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			prop = propIds.get(subCat, "")

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				if event["name"].lower() in ["world series 2025"]:
					continue
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

							if prop not in lines:
								lines[prop] = {}

							outcomes = row["outcomes"]
							skip = 1
							if mainCat == "player_totals" or prop in ["team_wins", "playoffs"]:
								skip = 2

							for i in range(0, len(outcomes), skip):
								outcome = outcomes[i]
								if skip == 2:
									if mainCat == "player_totals":
										team = parsePlayer(row["label"].lower().split(" regular ")[0].split(" to record ")[0])
									else:
										if row["eventId"] not in events:
											continue
										team = events[row["eventId"]]
									line = outcome["label"].split(" ")[-1]
									#print(mainCat, subCat)
									ou = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
									if "under" in outcome["label"].lower() or outcome["label"].lower() == "no":
										ou = outcomes[i+1]["oddsAmerican"]+"/"+outcome["oddsAmerican"]

									if prop in ["playoffs", "30/30"]:
										lines[prop][team] = ou
									else:
										lines[prop][team] = {
											line: ou
										}
								else:
									if prop in ["mvp", "cy_young", "roty"]:
										team = parsePlayer(outcome["participant"])
									elif mainCat == "leaders":
										team = parsePlayer(outcome["label"])
									else:
										team = convertTeam(outcome["participant"])
									lines[prop][team] = outcome["oddsAmerican"]

	with open("static/mlbfutures/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writeFanduelManual():

	js = """

	{
		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.replace(". ", "").substring(0, 3);
			if (t == "los") {
				if (team.indexOf("angels") >= 0) {
					return "laa";
				}
				return "lad";
			} else if (t == "new") {
				if (team.indexOf("yankees") >= 0) {
					return "nyy";
				}
				return "nym";
			} else if (t == "tam") {
				return "tb";
			} else if (t == "chi") {
				if (team.indexOf("white sox") >= 0) {
					return "chw";
				}
				return "chc";
			} else if (t == "san") {
				if (team.indexOf("giants") >= 0) {
					return "sf";
				}
				return "sd";
			} else if (t == "kan") {
				return "kc";
			} else if (t == "was") {
				return "wsh";
			}
			return t;
		}

		function parsePlayer(player) {
			return player.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
		}


		let start = true;
		let team = "";
		for (const li of document.querySelectorAll("ul")[5].querySelectorAll("li")) {
			if (li.querySelector("svg")) {
				//break;
			}
			if (li.innerText.indexOf("Strikeouts") >= 0) {
				break;
			}
			if (li.innerText.indexOf("Home Runs") >= 0) {
				start = true;
			}
			if (start && li.querySelector("div[data-test-id='ArrowAction']")) {
				//li.querySelector("div[data-test-id='ArrowAction']").click();
			}
			if (li.querySelector("div[role=heading]")) {
				team = parsePlayer(li.querySelector("div[role=heading]").getAttribute("aria-label").split(" Regular")[0]);
			}
			const btns = Array.from(li.querySelectorAll("div[role=button]"));
			if (btns.length < 2) {
				continue;
			}
			const skip = 1;
			for (let i = 0; i < btns.length; i += skip) {
				const btn = btns[i];
				if (btn.getAttribute("data-test-id") == "ArrowAction") {
					continue;
				}
				if (start) {
					team = parsePlayer(btn.getAttribute("aria-label").split(", ")[0]);
					const odds = btn.getAttribute("aria-label").split(", ")[1];
					data[team] = odds;

					/*
					const line = btn.getAttribute("aria-label").split(" ")[1];
					const odds = btn.getAttribute("aria-label").split(", ")[1];
					data[team] = {};
					data[team][line] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[1];
					*/
				}
			}
		}

		console.log(data);
	}

"""

def write365():

	js = """
	{
		let data = {};
		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.split(" ")[0];
			if (t == "la") {
				if (team.indexOf("angels") >= 0) {
					return "laa";
				}
				return "lad";
			} else if (t == "ny") {
				if (team.indexOf("yankees") >= 0) {
					return "nyy";
				}
				return "nym";
			} else if (t == "chi") {
				if (team.indexOf("white sox") >= 0) {
					return "chw";
				}
				return "chc";
			} else if (t == "was") {
				return "wsh";
			}
			return t;
		}

		function parsePlayer(player) {
			return player.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
		}

		let prop = document.querySelector(".rcl-MarketGroupButton_MarketTitle").innerText.toLowerCase();

		let skip = 1;
		if (prop == "to win outright") {
			prop = "world_series";
		} else if (prop == "to join the 30-30 club") {
			prop = "30/30";
			skip = 2;
		} else if (prop == "to win league") {
			prop = "league";
		} else if (prop == "to win division") {
			prop = "division";
		} else if (prop == "regular season awards") {
			prop = "awards";
		} else if (prop == "regular season stat leaders") {
			prop = "leaders";
		} else if (prop == "regular season wins") {
			prop = "team_wins";
		} else if (prop == "to make the playoffs") {
			prop = "playoffs";
		} else if (prop.indexOf("player regular season") >= 0) {
			prop = prop.split(" season ")[1].replace("runs batted in", "rbi").replace("home runs", "hr").replace("stolen bases", "sb");
			skip = 2;
		} else if (prop.indexOf("pitcher regular season strikeouts") >= 0) {
			prop = "k";
			skip = 2;
		}

		if (prop == "team_wins" || prop == "playoffs") {
			data[prop] = {};
			let teams = [];
			for (let div of document.querySelectorAll(".srb-ParticipantLabel_Name")) {
				teams.push(convertTeam(div.innerText));
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
					data[prop][teams[idx]] = {};
					data[prop][teams[idx]][line] = overs[idx]+"/"+odds;
				}
				idx += 1;
			}
		} else if (prop) {
			let player = "";
			for (let row of document.querySelectorAll(".gl-MarketGroupPod")) {
				if (row.className.indexOf("src-FixtureSubGroupWithShowMore_Closed") >= 0) {
					row.click();
				}

				if (["hr", "k", "sb", "h", "rbi"].includes(prop)) {
					player = parsePlayer(row.querySelector(".src-FixtureSubGroupButton_Text").innerText.split(" - ")[1]);
				}

				if (["awards", "cy_young", "mvp", "roty"].includes(prop) || prop.indexOf("leader") >= 0) {
					if (!row.querySelector(".src-FixtureSubGroupButton_Text")) {
						continue;
					}
					let p = row.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase();
					if (p.indexOf("cy young") >= 0) {
						p = "cy_young";
					} else if (p.indexOf(" mvp ") > 0) {
						p = "mvp";
					} else if (p.indexOf("rookie") > 0) {
						p = "roty";
					} else if (p.indexOf("home runs") >= 0) {
						p = "hr_leader";
					} else if (p.indexOf("hits") >= 0) {
						p = "h_leader";
					} else if (p.indexOf("rbis") >= 0) {
						p = "rbi_leader";
					} else if (p.indexOf("strikeouts") >= 0) {
						p = "k_leader";
					} else if (p.indexOf("wins") >= 0) {
						p = "w_leader";
					} else if (p.indexOf("saves") >= 0) {
						p = "sv_leader";
					} else if (p.indexOf("stolen bases") >= 0) {
						p = "sb_leader";
					} else if (p.indexOf("doubles") >= 0) {
						p = "double_leader";
					} else if (p.indexOf("triples") >= 0) {
						p = "triple_leader";
					} else {
						continue;
					}
					prop = p;
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
						if (["roty", "cy_young", "mvp"].includes(prop) || prop.indexOf("leader") >= 0) {
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
						if (prop == "team_wins") {
							data[prop][convertTeam(team.split(" - ")[0])] = ou;
						} else if (["hr", "k", "sb", "h", "rbi"].includes(prop)) {
							data[prop][player] = {};
							data[prop][player][team.split(" ")[1]] = ou;
						} else {
							data[prop][parsePlayer(team.split(" - ")[0])] = ou;
						}
					}
				}
			}
		}

		if (["cy_young", "mvp", "roty"].indexOf(prop) >= 0 || prop.indexOf("_leader") >= 0) {
			console.log(data);
		} else {
			console.log(data[prop]);
		}
	}
"""

def writeCZ():

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v4/sports/baseball/events/futures?competitionIds=04f90892-3afa-4e84-acce-5b89f151063d"
	outfile = "outfuture"

	os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.9.0' -H 'x-aws-waf-token: 29e44a76-d37d-4f53-a078-7f3f5fd18f64:EgoAv+FwiS0KAwAA:lidCSh6DHS2jQXLHJhmXT7IxByX0tt7VUovBwB2Tleu6kfdc/kmOsxTHRYLeY/74ee43RWK5VakQ7kXnZD/0J8QclDR3T2OSpl/qm2SwucamQCDWddgeL5x9I2kEw+M8r6ogbJqAs3y5XOo8+TPEwwUcE9I+edVP2cPnkj40Zj2mmr4mTy7P0nX64WlV1jjuTIWgQGdDCdws7TUoWN10GzaihAP6Vo+tzAnL1+dpXyDsWP4bLe9VFl/BfOg=' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	res = {}
	for event in data["competitions"][0]["events"]:
		for market in event["markets"]:
			if not market["display"]:
				continue

			prop = market["name"].lower().replace("|", "")

			if prop == "world series winner":
				prop = "world_series"
			elif prop == "american league outright" or prop == "national league outright":
				prop = "league"
			elif prop == "division winner":
				prop = "division"
			elif prop == "regular season wins" or prop.startswith("alternate regular season wins"):
				prop = "team_wins"
			elif prop == "to make the playoffs":
				prop = "playoffs"
			elif prop == "mvp winner":
				prop = "mvp"
			elif prop == "cy young winner":
				prop = "cy_young"
			elif prop == "rookie of the year winner":
				prop = "roty"
			elif prop == "home run leader":
				prop = "hr_leader"
			elif prop == "hits leader":
				prop = "h_leader"
			elif prop == "rbi leader":
				prop = "rbi_leader"
			elif prop == "stolen base leader":
				prop = "sb_leader"
			elif prop == "runs scored leader":
				prop = "r_leader"
			elif prop == "wins leader":
				prop = "w_leader"
			elif prop == "strikeouts leader":
				prop = "k_leader"
			elif prop == "saves leader":
				prop = "sv_leader"
			elif prop == "doubles leader":
				prop = "double_leader"
			elif prop == "triples leader":
				prop = "triple_leader"
			elif prop == "total home runs":
				prop = "hr"
			elif prop == "total rbi":
				prop = "rbi"
			elif prop == "total stolen bases":
				prop = "sb"
			elif prop == "total wins":
				prop = "w"
			else:
				continue

			if prop not in res:
				res[prop] = {}

			selections = market["selections"]
			skip = 1
			if prop in ["team_wins", "playoffs", "hr", "rbi", "sb", "w"]:
				skip = 2
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
					if prop in ["division", "league", "world_series"]:
						team = convertTeam(selections[i]["name"].replace("|", ""))
					else:
						team = parsePlayer(selections[i]["name"].replace("|", ""))
					res[prop][team] = ou
				elif prop in ["hr", "sb", "w", "rbi"]:
					player = parsePlayer(event["name"].replace("|", "").split(" 2025")[0])
					line = str(market["line"])
					if player not in res[prop]:
						res[prop][player] = {}
					res[prop][player][line] = ou
				else:
					team = convertTeam(event["name"].replace("|", ""))

					if prop in ["team_wins", "hr"]:
						line = str(market["line"])
						if team not in res[prop]:
							res[prop][team] = {}
						res[prop][team][line] = ou
					else:
						res[prop][team] = ou


	with open("static/mlbfutures/cz.json", "w") as fh:
		json.dump(res, fh, indent=4)


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

	if False and prop == "hr_leader":
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
	#print(player, ou, finalOdds)
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

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None):
	if not boost:
		boost = 1

	with open(f"updated.json") as fh:
		updated = json.load(fh)
	updated["mlbfutures"] = str(datetime.now())
	with open(f"updated.json", "w") as fh:
		json.dump(updated, fh, indent=4)

	with open(f"static/mlbfutures/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"static/mlbfutures/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"static/mlbfutures/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"static/mlbfutures/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"static/mlbfutures/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"static/mlbfutures/pn.json") as fh:
		pnLines = json.load(fh)

	with open(f"static/mlbfutures/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"static/mlbfutures/cz.json") as fh:
		czLines = json.load(fh)

	with open(f"static/mlbfutures/circa.json") as fh:
		circaLines = json.load(fh)

	with open(f"static/mlbfutures/espn.json") as fh:
		espnLines = json.load(fh)

	lines = {
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"bv": bvLines,
		"dk": dkLines,
		"pn": pnLines,
		"cz": czLines,
		"365": bet365Lines,
		"circa": circaLines,
		"espn": espnLines
	}

	with open("static/mlbfutures/ev.json") as fh:
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

				if len(books) < 3:
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
						#avgOver.append(convertDecOdds(int(book.split("/")[0])))
						avgOver.append(convertImpOdds(int(book.split("/")[0])))
						if "/" in book:
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

	with open("static/mlbfutures/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	with open("static/mlbfutures/evArr.json", "w") as fh:
		json.dump([value for key, value in evData.items()], fh)

def printEV():
	with open(f"static/mlbfutures/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], player, d["playerHandicap"], d["line"], d["book"], j, d))

	for row in sorted(data):
		print(row[:-1])

	output = "\t".join(["EV", "EV Book", "Imp", "Player", "Prop", "O/U", "FD", "DK", "MGM", "BV", "CZ", "Kambi/BR", "PN", "bet365", "ESPN", "Circa"]) + "\n"
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
		for book in ["fd", "dk", "mgm", "bv", "cz", "kambi", "pn", "365", "espn", "circa"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/mlbfutures/props.csv", "w") as fh:
		fh.write(output)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--dk", action="store_true", help="Fanduel")
	parser.add_argument("--mgm", action="store_true", help="MGM")
	parser.add_argument("--kambi", action="store_true")
	parser.add_argument("--pn", action="store_true")
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("--bv", action="store_true")
	parser.add_argument("--cz", action="store_true")
	parser.add_argument("--ev", action="store_true")
	parser.add_argument("--summary", action="store_true")
	parser.add_argument("-u", "--update", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("-p", "--print", action="store_true", help="Print")

	args = parser.parse_args()
	if args.dk:
		writeDK()
	if args.mgm:
		writeMGM()
	if args.kambi:
		writeKambi(args.keep)
	if args.bv:
		writeBV()
	if args.cz:
		writeCZ()
	if args.pn:
		writePN(args.debug)
	if args.update:
		#writeDK()
		writeCZ()
		#writeMGM()
		writeKambi()
		writeBV()
		writePN(args.debug)
	if args.ev:
		writeEV(args.prop, args.book, args.team, args.boost)
	if args.print:
		printEV()

	if args.summary:
		with open(f"static/mlbfutures/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"static/mlbfutures/bovada.json") as fh:
			bvLines = json.load(fh)

		with open(f"static/mlbfutures/mgm.json") as fh:
			mgmLines = json.load(fh)

		with open(f"static/mlbfutures/fanduel.json") as fh:
			fdLines = json.load(fh)

		with open(f"static/mlbfutures/draftkings.json") as fh:
			dkLines = json.load(fh)

		with open(f"static/mlbfutures/pn.json") as fh:
			pnLines = json.load(fh)

		with open(f"static/mlbfutures/bet365.json") as fh:
			bet365Lines = json.load(fh)

		lines = {
			"kambi": kambiLines,
			"mgm": mgmLines,
			"fd": fdLines,
			"bv": bvLines,
			"dk": dkLines,
			"pn": pnLines,
			"365": bet365Lines,
			"circa": circaLines
		}

		for book in lines:
			for prop in lines[book]:
				if prop != args.prop:
					continue
				for team in lines[book][prop]:
					if team != args.team:
						continue

					print(book, prop, lines[book][prop][team])
