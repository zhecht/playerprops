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
	if "(fl)" in team:
		team = team.replace("(fl)", "florida")
	if "(oh)" in team:
		team = team.replace("(oh)", "ohio")
	if team.endswith(" u"):
		team = team[:-2]
	teams = {
		"jax state": "jacksonville state",
		"n mexico state": "new mexico state",
		"umass": "massachusetts",
		"la tech": "louisiana tech",
		"fiu": "florida intl",
		"k state": "kansas state",
		"texas a m": "texas a&m",
		"ulm": "ul monroe",
		"unc": "north carolina",
		"app state": "appalachian state",
		"va tech": "virginia tech",
		"ole miss": "mississippi",
		"n.c central": "north carolina central",
		"miami oh": "miami ohio",
		"wv mountaineers": "west virginia"
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
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")

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

def writeBovada():
	url = "https://www.bovada.lv/sports/football/college-football"

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/football/college-football?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
	outfile = f"ncaafoutBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	ids = []
	for row in data[0]["events"]:
		ids.append((row["link"], row["id"]))


	res = {}
	#print(ids)
	#ids = [("/football/college-football/penn-state-7-illinois-202309161200", "202309161200")]
	for link, gameId in ids:
		#if "iowa-state" not in link:
		#	continue
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		comp = data[0]['events'][0]['competitors']
		game = data[0]['events'][0]['description'].lower()
		fullAway, fullHome = game.split(" @ ")
		game = f"{fullAway.split(' (')[0]} @ {fullHome.split(' (')[0]}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "touchdown scorers", "qb props", "rushing props", "receiving props"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["description"].lower() == "first half":
						prefix = "1h_"
					elif market["period"]["description"].lower() == "1st quarter":
						prefix = "1q_"
					elif market["period"]["description"].lower() == "2nd quarter":
						prefix = "2q_"
					elif market["period"]["description"].lower() == "3rd quarter":
						prefix = "3q_"
					elif market["period"]["description"].lower() == "4th quarter":
						prefix = "4q_"

					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "total" or prop == "total points":
						prop = "total"
					elif prop == "point spread" or prop == "spread":
						prop = "spread"
					elif prop == f"total points - {fullAway}":
						prop = "away_total"
					elif prop == f"total points - {fullHome}":
						prop = "home_total"
					elif prop == "anytime touchdown scorer":
						prop = "attd"
					elif "passing yards" in prop:
						prop = "pass_yd"
					elif "passing touch" in prop:
						prop = "pass_td"
					elif "rush yards" in prop:
						prop = "rush_yd"
					elif "receiving yards" in prop:
						prop = "rec_yd"
					elif "interceptions" in prop:
						prop = "int"
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
							ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif "spread" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							handicap = market["outcomes"][i]["price"]["handicap"]
							if handicap[0] != "-":
								handicap = "+"+handicap
							res[game][prop][handicap] = ou
					elif prop == "attd":
						for i in range(0, len(market["outcomes"]), 1):
							player = parsePlayer(market["outcomes"][i]["description"])
							res[game][prop][player] = market["outcomes"][i]["price"]["american"].replace("EVEN", "100")
					else:
						handicap = market["outcomes"][0]["price"]["handicap"]
						player = parsePlayer(market["description"].split(" - ")[-1])
						res[game][prop][player] = f"{handicap} {market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")


		url = f"https://bv2.digitalsportstech.com/api/game?sb=bovada&event={gameId}"
		time.sleep(0.2)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		if not data:
			continue

		nixId = 0
		for row in data[0]["providers"]:
			if row["name"] == "nix":
				nixId = row["id"]
				break

		for stat in ["Passing TDs", "Passing Yards", "Receiving Yards", "Rushing Yards", "Touchdowns"]:
		#for stat in ["Passing TDs"]:
			if stat == "Touchdowns":
				url = f"https://bv2.digitalsportstech.com/api/dfm/marketsBySs?sb=bovada&gameId={nixId}&statistic={stat}"
			else:
				url = f"https://bv2.digitalsportstech.com/api/dfm/marketsByOu?sb=bovada&gameId={nixId}&statistic={stat.replace(' ', '%20')}"
			time.sleep(0.2)
			os.system(f"curl -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			if not data:
				continue

			prop = stat.lower().replace(" ", "_").replace("touchdowns", "attd").replace("tds", "td").replace("passing", "pass").replace("receiving", "rec").replace("rushing", "rush")

			res[game][prop] = {}

			for playerRow in data[0]["players"]:
				player = parsePlayer(playerRow["name"])
				markets = playerRow["markets"]
				if prop == "attd":
					for row in markets:
						if row["value"] == 1:
							res[game][prop][player] = f"{convertAmericanOdds(row['odds'])}"
				else:
					ou = f"{convertAmericanOdds(markets[0]['odds'])}/{convertAmericanOdds(markets[1]['odds'])}"
					if markets[0]["statistic"]["id"] > markets[1]["statistic"]["id"]:
						ou = f"{convertAmericanOdds(markets[1]['odds'])}/{convertAmericanOdds(markets[0]['odds'])}"
					res[game][prop][player] = f"{markets[0]['value']} {ou}"

	with open("static/ncaafprops/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "ncaafoutPN"
	game = games[gameId]

	#print(game)
	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

	time.sleep(0.5)
	os.system(url)
	try:
		with open(outfile) as fh:
			related = json.load(fh)
	except:
		retry.append(gameId)
		return

	relatedData = {}
	for row in related:
		if "special" in row:
			prop = row["units"].lower().replace("yards", "_yd").replace("receiving", "rec").replace("passing", "pass").replace("rushing", "rush").replace("interceptions", "int")
			if prop == "touchdownpasses":
				prop = "pass_td"
			elif prop == "1st touchdown":
				prop = "ftd"
			elif prop == "touchdowns":
				prop = "attd"
			elif prop == "longestreception":
				prop = "longest_rec"
			elif prop == "longestpasscomplete":
				prop = "longest_pass"
			elif prop == "passreceptions":
				prop = "rec"

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

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

	time.sleep(0.5)
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
		if keys[1] == "1":
			prefix = "1h_"
		elif keys[1] == "3":
			prefix = "1q_"

		overId = underId = 0
		player = ""

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

			if "points" in prices[0] and prop not in ["ftd", "attd", "last touchdown"]:
				handicap = str(prices[switched]["points"])
				res[game][prop][player] = handicap+" "+ou
			else:
				res[game][prop][player] = ou
		else:
			ou = f"{prices[0]['price']}/{prices[1]['price']}"
			if prices[0]["designation"] in ["home", "under"]:
				ou = f"{prices[1]['price']}/{prices[0]['price']}"
				switched = 1

			if "points" in prices[0]:
				handicap = str(prices[switched]["points"])
				if "spread" in prop and handicap[0] != "-":
					handicap = "+"+handicap
				if prop not in res[game]:
					res[game][prop] = {}

				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou


def writeDK():
	url = "https://sportsbook.draftkings.com/leagues/football/ncaaf"

	mainCats = {
		"game lines": 492,
		"attd": 1003,
		"passing": 1000,
		"rush/rec": 1001,
		"quarters": 527,
		"halves": 526,
		"team": 530
	}
	
	subCats = {
		492: [4518, 13195, 13196, 9712],
		1000: [9525, 9524],
		1001: [9514, 9512],
		530: [4653, 10514]
	}

	lines = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/87637/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outncaaf"
			call(["curl", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				game = event["name"].lower()
				if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
					continue

				away, home = game.split(" @ ")
				away = convertActionTeam(away)
				home = convertActionTeam(home)
				game = f"{away} @ {home}"

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
					prop = cRow["name"].lower()
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

							label = row["label"].lower().split(" [")[0]
							
							prefix = ""
							if "1st half" in label:
								prefix = "1h_"
							elif "2nd half" in label:
								prefix = "2h_"
							elif "1st quarter" in label:
								prefix = "1q_"

							if "moneyline" in label:
								label = "ml"
							elif "spread" in label:
								label = "spread"
							elif "team total points" in label:
								team = label.split(":")[0]
								if game.startswith(team):
									label = "away_total"
								else:
									label = "home_total"
							elif "total" in label:
								if "touchdowns" in label:
									continue
								label = "total"
							elif label == "first td scorer":
								label = "ftd"
							elif label == "anytime td scorer":
								label = "attd"
							elif prop in ["pass tds", "pass yds", "rec tds", "rec yds", "rush tds", "rush yds"]:
								label = prop.replace(" ", "_").replace("tds", "td").replace("yds", "yd")
							else:
								continue


							label = label.replace(" alternate", "")
							label = f"{prefix}{label}"

							if label == "halftime/fulltime":
								continue

							if "ml" not in label:
								if label not in lines[game]:
									lines[game][label] = {}

							outcomes = row["outcomes"]
							ou = ""
							try:
								ou = f"{outcomes[0]['oddsAmerican']}/{outcomes[1]['oddsAmerican']}"
							except:
								continue

							if "ml" in label:
								lines[game][label] = ou
							elif "total" in label or "spread" in label:
								for i in range(0, len(outcomes), 2):
									line = str(float(outcomes[i]["line"]))
									try:
										lines[game][label][line] = f"{outcomes[i]['oddsAmerican']}/{outcomes[i+1]['oddsAmerican']}"
									except:
										continue
							elif label in ["ftd", "attd"]:
								for outcome in outcomes:
									player = parsePlayer(outcome["participant"].split(" (")[0])
									try:
										lines[game][label][player] = f"{outcome['oddsAmerican']}"
									except:
										continue
							else:
								player = parsePlayer(outcomes[0]["participant"])
								lines[game][label][player] = f"{outcomes[0]['line']} {outcomes[0]['oddsAmerican']}"
								if len(row["outcomes"]) > 1:
									lines[game][label][player] += f"/{outcomes[1]['oddsAmerican']}"

	with open("static/ncaafprops/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writePinnacle(date=None):
	debug = False

	outfile = f"ncaafoutPN"

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/football/ncaa/matchups#period:0"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/880/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile

	os.system(url)
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	for row in data:
		#if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
		#	continue
		if row["type"] == "matchup" and not row["parent"]:
			player1 = row["participants"][0]["name"].lower()
			player2 = row["participants"][1]["name"].lower()
			games[str(row["id"])] = f"{player2} @ {player1}"

	res = {}
	#games = {'1578086769': 'vanderbilt @ wake forest'}
	retry = []
	for gameId in games:
		parsePinnacle(res, games, gameId, retry, debug)

	for gameId in retry:
		parsePinnacle(res, games, gameId, retry, debug)

	with open("static/ncaafprops/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM():

	res = {}

	url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/college-football-211"

	outfile = f"ncaafoutMGM"

	js = """
	{
		const ids = [];
		for (const a of document.querySelectorAll("a.grid-info-wrapper")) {
			const href = a.href.split("-");
			ids.push(href[href.length - 1]);
		}
		console.log(ids);
	}
"""

	ids = [
  "14707819",
  "14707813",
  "14707814",
  "14707818",
  "14707815",
  "14707817",
  "14707812",
  "14707811",
  "14707816",
  "14707820",
  "14707821",
  "14707830",
  "14707824",
  "14707823",
  "14707829",
  "14707822",
  "14707826",
  "14707825",
  "14707828",
  "14707831",
  "14707827",
  "14707833",
  "14707834",
  "14707832",
  "14420129",
  "14707731",
  "14707735",
  "14707732",
  "14707738",
  "14707734",
  "14707739",
  "14707733",
  "14707736",
  "14707737",
  "14707740",
  "14707744",
  "14707743",
  "14707741",
  "14707742",
  "14707745",
  "14707746",
  "14707748",
  "14707750",
  "14707751",
  "14707747",
  "14707749",
  "14707752",
  "14707754",
  "14707753",
  "14707755",
  "14420129"
]


	#ids = ["14682653"]
	for mgmid in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		if "fixture" not in data:
			continue

		data = data["fixture"]

		if " at " not in data["name"]["value"]:
			continue
		game = strip_accents(data["name"]["value"].lower()).replace(" at ", " @ ").replace(" (neutral venue)", "")
		fullTeam1, fullTeam2 = game.split(" @ ")
		fullTeam1 = convertActionTeam(fullTeam1)
		fullTeam2 = convertActionTeam(fullTeam2)
		game = f"{fullTeam1} @ {fullTeam2}"

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
			elif prop == "which player will score a touchdown in the game?":
				prop = "attd"
			elif prop.startswith("how many ") or "over/under" in prop:
				if prop.startswith("how many points will be scored in the game") or "field goals" in prop or "kicking" in prop or "extra points" in prop:
					continue
				if fullTeam1 in prop or fullTeam2 in prop:
					p = "away_total"
					team = prop.split(" will ")[-1].split(" score")[0]
					if fullTeam2 in prop:
						p = "home_total"
					prop = p
				else:
					if "his 1st" in prop:
						continue
					player = prop.split(" (")[0].split(" will ")[-1]
					propIdx = 3
					if "over/under" in prop:
						p = prop.split(" ")[-2]
						propIdx = -1
					else:
						p = prop.split(" ")[2].replace("interceptions", "int")
					if "longest" in prop:
						end = prop.split(" ")[-1][:-1].replace("completion", "pass").replace("reception", "rec")
						if end not in ["rush", "pass", "rec"]:
							continue
						p = "longest_"+end
					elif "tackles" in prop:
						if "tackles and assists" in prop:
							p = "tackles_assists"
						else:
							continue
					elif p == "passing":
						p = "pass_"+prop.split(" ")[propIdx].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "rushing":
						p = "rush_"+prop.split(" ")[propIdx].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "receiving":
						p = "rec_"+prop.split(" ")[propIdx].replace("yards", "yd").replace("attempts", "att").replace("touchdowns", "td")
					elif p == "receptions":
						p = "rec"
					prop = p
			else:
				continue

			prop = prefix+prop

			results = row['results']
			ou = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
			if "ml" in prop:
				res[game][prop] = ou
			elif len(results) >= 2:
				skip = 1 if prop == "attd" else 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop and prop not in ["attd"]:
						continue
					else:
						val = val.split(" ")[-1]
					#print(game, prop, player)
					if prop == "attd":
						ou = str(results[idx]['americanOdds'])
					else:
						ou = f"{results[idx]['americanOdds']}/{results[idx+1]['americanOdds']}"

					if prop == "attd":
						player = results[idx]["name"]["value"].lower()
						player = parsePlayer(player)
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = ou
					elif player:
						player = parsePlayer(player)
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = val+" "+ou
					else:
						if prop not in res[game]:
							res[game][prop] = {}
						try:
							v = str(float(val))
							if "spread" in prop and v[0] != "-":
								v = "+"+v
							res[game][prop][v] = ou
						except:
							pass

	with open("static/ncaafprops/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)


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
		game = strip_accents(f"{away} @ {home}")
		dt = datetime.strptime(event["event"]["start"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if game in eventIds or str(dt)[:10] != date:
			continue
			#pass
		eventIds[game] = event["event"]["id"]

	#eventIds = {"penn state @ illinois": 1020039408}
	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		eventId = eventIds[game]
		teamIds = {}
		data[game] = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		if "events" not in j:
			continue
		fullAway, fullHome = map(str, j["events"][0]["name"].lower().replace("vs", "@").split(" @ "))

		for betOffer in j["betOffers"]:
			label = betOffer["criterion"]["label"].lower()

			if label.startswith("touchdown scorer") or label.startswith("first touchdown scorer") or "by the player" in label or "total points" in label or label == "including overtime" or "draw no bet" in label or "handicap" in label:

				prefix = ""
				if "1st half" in label:
					prefix = "1h_"
				elif "quarter 1" in label:
					prefix = "1q_"

				prop = "attd"
				if label.startswith("first"):
					prop = "ftd"
				elif label == "including overtime" or "draw no bet" in label:
					prop = "ml"
				elif "handicap" in label:
					prop = "spread"
				elif "total points" in label:
					prop = "total"
					if fullAway in label:
						prop = "away_total"
					elif fullHome in label:
						prop = "home_total"
				elif "by the player" in label:
					label = label.split(" by the player")[0].split("total ")[-1]
					prop = label.replace(" ", "_").replace("passing", "pass").replace("rushing", "rush").replace("yards", "yd").replace("receiving", "rec")
					if prop == "touchdown_passes_thrown":
						prop = "pass_td"
					elif "interceptions thrown" in label:
						prop = "int"

				prop = f"{prefix}{prop}"

				if prop not in data[game]:
					data[game][prop] = {}

				if "ml" in prop:
					ou = f"{betOffer['outcomes'][0]['oddsAmerican']}/{betOffer['outcomes'][1]['oddsAmerican']}"
					if betOffer['outcomes'][0]['participant'].lower() == fullHome:
						ou = f"{betOffer['outcomes'][1]['oddsAmerican']}/{betOffer['outcomes'][0]['oddsAmerican']}"
					data[game][prop] = ou
				elif "total" in prop:
					ou = f"{betOffer['outcomes'][0]['oddsAmerican']}/{betOffer['outcomes'][1]['oddsAmerican']}"
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer['outcomes'][0]['label'] == "Under":
						ou = f"{betOffer['outcomes'][1]['oddsAmerican']}/{betOffer['outcomes'][0]['oddsAmerican']}"
					data[game][prop][line] = ou
				elif "spread" in prop:
					ou = f"{betOffer['outcomes'][0]['oddsAmerican']}/{betOffer['outcomes'][1]['oddsAmerican']}"
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer['outcomes'][0]['participant'].lower() == fullHome:
						line = str(betOffer["outcomes"][1]["line"] / 1000)
						ou = f"{betOffer['outcomes'][1]['oddsAmerican']}/{betOffer['outcomes'][0]['oddsAmerican']}"
					data[game][prop][line] = ou
				elif prop not in ["attd", "ftd"]:
					player = strip_accents(betOffer["outcomes"][0]["participant"])
					try:
						last, first = map(str, player.split(" (")[0].lower().split(", "))
						player = f"{first} {last}"
					except:
						player = player.lower()
					player = parsePlayer(player)

					if player not in data[game][prop]:
						data[game][prop][player] = {}
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					data[game][prop][player][line] = f"{betOffer['outcomes'][0]['oddsAmerican']}/{betOffer['outcomes'][1]['oddsAmerican']}"
				else:
					if prop == "attd":
						player = strip_accents(betOffer["outcomes"][0]["participant"])
						try:
							last, first = map(str, player.split(" (")[0].lower().split(", "))
							player = f"{first} {last}"
						except:
							player = player.lower()
						player = parsePlayer(player)
						over = betOffer["outcomes"][0]["oddsAmerican"]
						data[game][prop][player] = f"{over}"
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
							try:
								over = outcome["oddsAmerican"]
							except:
								continue
							data[game][prop][player] = f"{over}"


	with open(f"static/ncaafprops/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

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

	with open("static/ncaafprops/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	games = {}
	for game in fdLines:
		games[game.split(" @ ")[0]] = game
		games[game.split(" @ ")[1]] = game

	#props = ["11_passing_tds"]
	for actionProp in props:
		time.sleep(0.2)
		path = f"ncaafout.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/2/props/core_bet_type_{actionProp}?bookIds=69,1541,283,348,351,355&date={date.replace('-', '')}"
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

		if "markets" not in j or not j["markets"]:
			print(actionProp)
			continue
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
				game = games.get(team, "")
				if not game:
					#print(team)
					continue
				overUnder = "over"
				try:
					overUnder = optionTypes[oddData["option_type_id"]]
				except:
					pass
				book = actionNetworkBookIds.get(bookId, "")
				value = str(oddData["value"])

				if game not in odds:
					odds[game] = {}
				if prop not in odds[game]:
					odds[game][prop] = {}
				if player not in odds[game][prop]:
					odds[game][prop][player] = {}

				if book not in odds[game][prop][player]:
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[game][prop][player][book] = f"{v}{oddData['money']}"
				elif overUnder == "over":
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[game][prop][player][book] = f"{v}{oddData['money']}/{odds[game][prop][player][book].replace(v, '')}"
				else:
					odds[game][prop][player][book] += f"/{oddData['money']}"
				sp = odds[game][prop][player][book].split("/")
				if odds[game][prop][player][book].count("/") == 3:
					odds[game][prop][player][book] = sp[1]+"/"+sp[2]
		#print(odds[game][player][prop])

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
				if (time && (time.innerText.split(" ")[0] === "SAT" || time.innerText.split(" ").length < 3)) {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/louisiana-monroe-@-texas-a-m-32626235",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/washington-@-michigan-state-32624502",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/northern-colorado-@-washington-state-32640522",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/n.c.-central-@-ucla-32640524",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/tennessee-@-florida-32624509",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/miami-ohio-@-cincinnati-32626228",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/south-alabama-@-oklahoma-state-32626247",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/bowling-green-@-michigan-32638557",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/georgia-tech-@-mississippi-32626072",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/byu-@-arkansas-32624517",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/akron-@-kentucky-32626254",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/pittsburgh-@-wv-mountaineers-32624511",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/syracuse-@-purdue-32625857",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/florida-atlantic-@-clemson-32626278",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/tcu-@-houston-32624528",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/wyoming-@-texas-32625781",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/hawaii-@-oregon-32626217",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/colorado-state-@-colorado-32623902",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/fresno-state-@-arizona-state-32625772",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/kansas-@-nevada-32626289",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/utep-@-arizona-32626293"
]

	lines = {}
	#games = ["https://mi.sportsbook.fanduel.com/football/ncaa-football-games/penn-state-@-illinois-32624485"]
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away, home = map(str, game.split(" @ "))
		game = f"{convertActionTeam(away)} @ {convertActionTeam(home)}"

		if game != "texas @ alabama":
			pass
			#continue

		if game in lines:
			continue
		lines[game] = {}

		outfile = "ncaafout"

		for tab in ["", "td-scorer-props", "passing-props", "receiving-props", "rushing-props", "1st-half", "1st-quarter", "totals"]:
		#for tab in [""]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue

			if data["attachments"]["events"][str(gameId)]["inPlay"]:
				continue

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()

				if marketName in ["any time touchdown scorer", "first touchdown scorer", "moneyline", "1st half winner"] or " - passing yds" in marketName or " - receiving yds" in marketName or " - rushing yds" in marketName or " - passing tds" in marketName or " - rushing tds" in marketName or "spread" in marketName or "total" in marketName:

					prefix = ""
					if "1st half" in marketName:
						prefix = "1h_"
					elif "1st quarter" in marketName:
						prefix = "1q_"

					prop = ""
					if "any time" in marketName:
						prop = "attd"
					elif "first" in marketName:
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
					elif "spread" in marketName and "/" not in marketName:
						prop = f"{prefix}spread"
					elif "total" in marketName and "/" not in marketName:
						if marketName.startswith("away"):
							prop = f"{prefix}away_total"
						elif marketName.startswith("home"):
							prop = f"{prefix}home_total"
						else:
							prop = f"{prefix}total"
					elif marketName in ["1st half winner", "moneyline", "1st quarter winner"]:
						prop = f"{prefix}ml"
					else:
						continue

					if "ml" not in prop:
						if prop not in lines[game]:
							lines[game][prop] = {}

					runners = data["attachments"]["markets"][market]["runners"]
					skip = 1 if prop in ["ftd", "attd"] or "spread" in prop or "total" in prop else 2
					for i in range(0, len(runners), skip):
						player = parsePlayer(runners[i]["runnerName"].lower().replace(" over", "").replace(" under", ""))
						handicap = ""
						try:
							odds = runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
						except:
							continue

						if "ml" in prop:
							lines[game][prop] = f"{odds}"

							try:
								lines[game][prop] += f"/{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"
							except:
								continue
						elif "total" in prop or "spread" in prop:
							handicap = str(runners[i]['handicap'])
							if handicap == "0":
								handicap = runners[i]["runnerName"].split(" ")[-1][1:-1]
							if runners[i]["result"] and runners[i]["result"]["type"] == "HOME":
								handicap = str(float(handicap) * -1)
							if "spread" in prop and handicap[0] != "-" and handicap[0] != "+":
								handicap = "+"+handicap
							try:
								if handicap in lines[game][prop]:
									if "/" in lines[game][prop][handicap]:
										continue
									lines[game][prop][handicap] += f"/{odds}"
								else:
									lines[game][prop][handicap] = f"{odds}"
							except:
								pass
						elif prop in ["ftd", "attd"]:
							lines[game][prop][player] = str(odds)
						else:
							lines[game][prop][player] = f"{runners[i]['handicap']} {odds}/{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"

		with open(f"static/ncaafprops/fanduelLines.json", "w") as fh:
			json.dump(lines, fh, indent=4)

	with open(f"static/ncaafprops/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="attd", sharp=False):

	prefix = ""
	if sharp:
		prefix = "pn_"
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

		evData[player][f"{prefix}fairVal"] = fairVal
		evData[player][f"{prefix}implied"] = implied
	
	evData[player][f"{prefix}ev"] = ev

def writeEV(date=None, gameArg="", teamArg="", propArg="attd", bookArg="", boost=None, notd=None):
	if not date:
		date = str(datetime.now())[:10]

	if not boost:
		boost = 1

	with open(f"{prefix}static/ncaafprops/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/ncaafprops/ev.json") as fh:
		evData = json.load(fh)

	games = {}
	for game in fdLines:
		games[game.split(" @ ")[0]] = game
		games[game.split(" @ ")[1]] = game

	evData = {}

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"bv": bvLines,
		"dk": dkLines
	}

	for game in fdLines:
		if teamArg and teamArg not in game:
			continue
		if game not in actionnetwork:
			continue

		props = {}
		for book in lines:
			if game not in lines[book]:
				continue
			for prop in lines[book][game]:
				props[prop] = 1

		for prop in props:
			if propArg and propArg != prop:
				continue
			if notd and prop in ["attd", "ftd"]:
				continue

			handicaps = {}
			for book in lines:
				lineData = lines[book]
				if game in lineData and prop in lineData[game]:
					if type(lineData[game][prop]) is not dict:
						handicaps[(" ", " ")] = ""
						break
					for handicap in lineData[game][prop]:
						player = playerHandicap = ""
						#print(book, game, handicap)
						try:
							player = float(handicap)
							player = ""
						except:
							player = handicap
							playerHandicap = ""
							if " " in lineData[game][prop][player]:
								playerHandicap = lineData[game][prop][player].split(" ")[0]
						handicaps[(handicap, playerHandicap)] = player

			for handicap, playerHandicap in handicaps:
				player = handicaps[(handicap, playerHandicap)]

				for i in range(2):
					highestOdds = []
					books = []
					odds = []

					if False and game in actionnetwork and prop in actionnetwork[game] and handicap in actionnetwork[game][prop]:
						for book in actionnetwork[game][prop][handicap]:
							if book in ["mgm", "fanduel", "draftkings", "betrivers"]:
								continue
							val = actionnetwork[game][prop][handicap][book]
							
							if player.strip():
								if type(val) is dict:
									if playerHandicap not in val:
										continue
									val = actionnetwork[game][prop][handicap][book][playerHandicap]
								else:
									if prop != "attd" and playerHandicap != val.split(" ")[0]:
										continue
									val = val.split(" ")[-1]

							try:
								o = val.split(" ")[-1].split("/")[i]
								ou = val.split(" ")[-1]
							except:
								if i == 1:
									continue
								o = val
								ou = val

							highestOdds.append(int(o))
							odds.append(ou)
							books.append(book)

					for book in lines:
						lineData = lines[book]
						if game in lineData and prop in lineData[game]:
							if type(lineData[game][prop]) is not dict:
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
										if prop != "attd" and playerHandicap != val.split(" ")[0]:
											continue
										val = lineData[game][prop][handicap].split(" ")[-1]


							try:
								o = val.split(" ")[-1].split("/")[i]
								ou = val.split(" ")[-1]
							except:
								if i == 1:
									continue
								o = val
								ou = val

							if not o:
								continue
							highestOdds.append(int(o))
							odds.append(ou)
							books.append(book)

					if len(books) < 2:
						continue

					kambi = ""
					try:
						bookIdx = books.index("kambi")
						kambi = odds[bookIdx]
						odds.remove(kambi)
						books.remove("kambi")
					except:
						pass

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
					if kambi:
						books.append("kambi")
						l.append(kambi)
					if pn:
						books.append("pn")
						l.append(pn)

					avgOver = []
					avgUnder = []
					for book in l:
						if book and book != "-":
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
						
					key = f"{game} {handicap} {prop} {'over' if i == 0 else 'under'}"
					devig(evData, key, ou, int(line), prop=prop)
					if pn:
						if i == 1:
							pn = f"{pn.split('/')[1]}/{pn.split('/')[0]}"
						devig(evData, key, pn, line, prop=prop, sharp=True)
					if key not in evData:
						print(key)
						continue

					evData[key]["odds"] = l
					evData[key]["under"] = i == 1
					evData[key]["book"] = evBook
					evData[key]["books"] = books
					evData[key]["game"] = game
					evData[key]["ou"] = ou
					evData[key]["line"] = line
					evData[key]["player"] = player
					evData[key]["fullLine"] = maxOU
					evData[key]["handicap"] = handicap
					evData[key]["playerHandicap"] = playerHandicap
					evData[key]["prop"] = prop
					j = {b: o for o, b in zip(l, books)}
					j[evBook] = maxOU
					evData[key]["bookOdds"] = j

	with open(f"static/ncaafprops/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def printEV():

	with open(f"static/ncaafprops/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for key in evData:
		d = evData[key]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], key, d["playerHandicap"], d["line"], d["book"], j, key))

	for row in sorted(data):
		print(row[:-1])

	output = "\t".join(["EV", "PN EV", "EV Book", "Game", "Player", "Prop", "O/U", "FD", "DK", "Bet365", "MGM", "Kambi", "PN", "CZ", "BV"]) + "\n"
	for row in sorted(data, reverse=True):
		d = evData[row[-1]]
		ou = ("u" if d["under"] else "o")+" "
		if d["player"]:
			ou += d["playerHandicap"]
		else:
			ou += d["handicap"]
		arr = [row[0], d.get("pn_ev", "-"), str(d["line"])+" "+d["book"].replace("caesars", "cz").upper(), d["game"], d["player"], d["prop"], ou]
		for book in ["fd", "dk", "bet365", "mgm", "kambi", "pn", "caesars", "bv"]:
			o = str(d["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open(f"static/ncaafprops/ev.csv","w") as fh:
		fh.write(output)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("--mgm", action="store_true", help="MGM")
	parser.add_argument("--pb", action="store_true", help="Pointsbet")
	parser.add_argument("--bv", action="store_true", help="Bovada")
	parser.add_argument("--pn", action="store_true", help="Pinnacle")
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("-g", "--game", help="Game")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("--book", help="Book")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--fd", action="store_true", help="FD")
	parser.add_argument("--dk", action="store_true", help="DK")
	parser.add_argument("-p", "--print", action="store_true", help="Print")
	parser.add_argument("--notd", action="store_true", help="Not ATTD FTD")

	args = parser.parse_args()

	if args.update:
		writeFanduel()
		writeActionNetwork(args.date)
		writeKambi(args.date)
		writeMGM()
		writePinnacle()
		writeBovada()
		writeDK()

	if args.fd:
		writeFanduel()

	if args.mgm:
		writeMGM()

	if args.action:
		writeActionNetwork(args.date)

	if args.kambi:
		writeKambi(args.date)

	if args.pb:
		writePointsbet()

	if args.pn:
		writePinnacle()

	if args.bv:
		writeBovada()

	if args.dk:
		writeDK()

	if args.ev or args.prop:
		writeEV(date=args.date, gameArg=args.game, teamArg=args.team, propArg=args.prop, bookArg=args.book, boost=args.boost, notd=args.notd)

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