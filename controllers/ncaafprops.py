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
	teams = {
		"jax state": "jacksonville state",
		"n mexico state": "new mexico state",
		"umass": "massachusetts",
		"la tech": "louisiana tech",
		"fiu": "florida intl",
		"k state": "kansas state",
		"texas a m": "texas a&m",
		"unc": "north carolina",
		"app state": "appalachian state",
		"va tech": "virginia tech",
		"ole miss": "mississippi"
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
	outfile = f"outBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	ids = []
	for row in data[0]["events"]:
		ids.append((row["link"], row["id"]))


	res = {}
	#print(ids)
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

			if desc in ["game lines", "alternate lines", "touchdown scorers"]:
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
	outfile = "outPN"
	game = games[gameId]

	#print(game)
	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o outPN'

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

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o outPN'

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

def writePinnacle(date=None):
	debug = False

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/football/ncaa/matchups#period:0"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/880/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o outPN'

	os.system(url)
	outfile = f"outPN"
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

	outfile = f"outMGM"

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
  "14682653",
  "14420124",
  "14682658",
  "14682659",
  "14682656",
  "14682655",
  "14682657",
  "14682654",
  "14682660",
  "14682663",
  "14420127",
  "14420126",
  "14682664",
  "14682661",
  "14682662",
  "14682665",
  "14682666",
  "14682667",
  "14682668",
  "14682669",
  "14682939",
  "14682940",
  "14682941",
  "14682942",
  "14682943",
  "14682944",
  "14682945",
  "14420125",
  "14682951",
  "14682946",
  "14682949",
  "14682950",
  "14682947",
  "14682948",
  "14688932",
  "14682955",
  "14682957",
  "14682953",
  "14682956",
  "14682952",
  "14682954",
  "14688931",
  "14682958",
  "14682960",
  "14682959",
  "14682961"
]


	#ids = ["14682653"]
	for mgmid in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		data = data["fixture"]

		if " at " not in data["name"]["value"]:
			continue
		game = strip_accents(data["name"]["value"].lower()).replace(" at ", " @ ")
		fullTeam1, fullTeam2 = game.split(" @ ")
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
							try:
								over = outcome["oddsAmerican"]
							except:
								continue
							if player not in data[team]:
								data[team][player] = {}
							data[team][player][prop] = f"{over}"


	with open(f"{prefix}static/ncaafprops/kambi.json", "w") as fh:
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
				if player not in odds[game]:
					odds[game][player] = {}
				if prop not in odds[game][player]:
					odds[game][player][prop] = {}

				if book not in odds[game][player][prop]:
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[game][player][prop][book] = f"{v}{oddData['money']}"
				elif overUnder == "over":
					v = ""
					if prop not in ["attd", "ftd"]:
						v = value+" "
					odds[game][player][prop][book] = f"{v}{oddData['money']}/{odds[game][player][prop][book].replace(v, '')}"
				else:
					odds[game][player][prop][book] += f"/{oddData['money']}"
				sp = odds[game][player][prop][book].split("/")
				if odds[game][player][prop][book].count("/") == 3:
					odds[game][player][prop][book] = sp[1]+"/"+sp[2]
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
				if (time && time.innerText.split(" ").length === 2) {
					urls[a.href] = 1;
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/vanderbilt-@-wake-forest-32608897",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/nebraska-@-colorado-32607048",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/notre-dame-@-nc-state-32607255",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/utah-@-baylor-32607592",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/ball-state-@-georgia-32607591",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/youngstown-state-@-ohio-state-32617968",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/james-madison-@-virginia-32608981",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/purdue-@-virginia-tech-32608947",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/troy-@-kansas-state-32608951",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/unlv-@-michigan-32607325",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/mississippi-@-tulane-32607596",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/texas-a-m-@-miami-florida-32607595",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/iowa-@-iowa-state-32607168",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/texas-state-@-utsa-32609015",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/utep-@-northwestern-32609277",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/miami-(oh)-@-massachusetts-32609013",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/western-michigan-@-syracuse-32608945",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/marshall-@-east-carolina-32609031",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/kent-state-@-arkansas-32609030",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/tulsa-@-washington-32609036",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/appalachian-state-@-north-carolina-32609032",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/new-mexico-state-@-liberty-32609033",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/ohio-@-florida-atlantic-32609034",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/louisiana-lafayette-@-old-dominion-32609104",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/uab-@-georgia-southern-32609035",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/smu-@-oklahoma-32608529",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/north-texas-@-fiu-32609114",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/cincinnati-@-pittsburgh-32608950",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/oregon-@-texas-tech-32608569",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/texas-@-alabama-32607499",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/connecticut-@-georgia-state-32609115",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/jacksonville-state-@-coastal-carolina-32609113",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/memphis-@-arkansas-state-32609119",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/houston-@-rice-32609095",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/middle-tennessee-@-missouri-32609088",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/ucf-@-boise-state-32608965",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/wisconsin-@-washington-state-32608618",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/temple-@-rutgers-32610048",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/eastern-michigan-@-minnesota-32609077",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/ucla-@-san-diego-state-32609049",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/arizona-@-mississippi-state-32609096",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/charlotte-@-maryland-32609127",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/air-force-@-sam-houston-state-32609076",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-division-1/southern-miss-@-florida-state-32609128",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/oklahoma-state-@-arizona-state-32608730",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/auburn-@-california-32607351",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/stanford-@-usc-32608630"
]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away, home = map(str, game.split(" @ "))
		game = f"{convertActionTeam(away)} @ {convertActionTeam(home)}"
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

	with open(f"{prefix}static/ncaafprops/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/ncaafprops/ev.json") as fh:
		evData = json.load(fh)

	games = {}
	for game in fdLines:
		games[game.split(" @ ")[0]] = game
		games[game.split(" @ ")[1]] = game

	evData = {}

	for game in fdLines:
		if teamArg and teamArg not in game:
			continue
		if game not in actionnetwork:
			continue
		for player in actionnetwork[game]:
			if not player:
				continue

			for prop in actionnetwork[game][player]:
				handicap = ""

				if propArg and propArg != prop:
					continue
				if notd and prop in ["attd", "ftd"]:
					continue

				an = actionnetwork[game][player][prop]
				fd = "-"
				dk = an.get("draftkings", "-")
				br = an.get("betrivers", "-")
				#mgm = an.get("mgm", "-")
				cz = an.get("caesars", "-")

				if " " in dk:
					handicap = float(str(dk.split(" ")[0]))

				if prop in fdLines[game] and player in fdLines[game][prop]:
					fd = str(fdLines[game][prop][player])
					if " " in fd:
						handicap = float(str(fd.split(" ")[0]))
					if handicap:
						if float(fd.split(" ")[0]) == handicap:
							fd = fd.split(" ")[-1]
						else:
							fd = "-"

				mgm = "-"
				if game in mgmLines and prop in mgmLines[game] and player in mgmLines[game][prop]:
					mgm = mgmLines[game][prop][player]
					if handicap:
						if float(mgm.split(" ")[0]) == handicap:
							mgm = mgm.split(" ")[-1]
						else:
							mgm = "-"

				pn = "-"
				if game in pnLines and prop in pnLines[game] and player in pnLines[game][prop]:
					pn = pnLines[game][prop][player]
					if handicap:
						if float(pn.split(" ")[0]) == handicap:
							pn = pn.split(" ")[-1]
						else:
							pn = "-"

				bv = "-"
				if game in bvLines and prop in bvLines[game] and player in bvLines[game][prop]:
					bv = bvLines[game][prop][player]
					if handicap:
						if float(bv.split(" ")[0]) == handicap:
							bv = bv.split(" ")[-1]
						else:
							bv = "-"

				if handicap:
					if dk != "-" and float(dk.split(" ")[0]) == handicap:
						dk = dk.split(" ")[-1]
					else:
						dk = "-"
					if br != "-" and float(br.split(" ")[0]) == handicap:
						br = br.split(" ")[-1]
					else:
						br = "-"
					if cz != "-" and float(cz.split(" ")[0]) == handicap:
						cz = cz.split(" ")[-1]
					else:
						cz = "-"

				kambi = "-"
				if False:
					if team in kambiLines and player in kambiLines[team] and prop in kambiLines[team][player]:
						kambi = kambiLines[team][player][prop]
						if handicap:
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

					l = [dk, fd, mgm, pn, bv, cz]
					books = ["dk", "fd", "mgm", "pn", "bv", "cz"]
					evBook = ""
					if bookArg:
						if bookArg not in books:
							continue
						evBook = bookArg
						idx = books.index(bookArg)
						maxOU = l[idx]
						try:
							evLine = maxOU.split("/")[i]
						except:
							continue
					else:
						maxOdds = []
						for odds in l:
							try:
								maxOdds.append(int(odds.split("/")[i]))
							except:
								maxOdds.append(-10000)

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

					if not maxOU:
						continue

					evLine = convertAmericanOdds(1 + (convertDecOdds(int(line)) - 1) * boost)
					l.extend([kambi, bet365])
					l.remove(maxOU)

					print(l, books)
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
					evData[key]["game"] = game
					evData[key]["ou"] = ou
					evData[key]["line"] = evLine
					evData[key]["player"] = player
					evData[key]["prop"] = prop
					evData[key]["handicap"] = handicap

	with open(f"{prefix}static/ncaafprops/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	data = []
	for key in evData:
		data.append((evData[key]["ev"], key, evData[key]["book"], evData[key]["game"], evData[key]["line"], [k+' '+evData[key]["odds"][k] for k in evData[key]["odds"] if evData[key]["odds"][k] != "-" and k != evData[key]["book"]]))

	for row in sorted(data):
		print(row)

def printEV():

	with open(f"{prefix}static/ncaafprops/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for key in evData:
		data.append((evData[key]["ev"], evData[key]["player"], evData[key]["prop"], evData[key]["game"], evData[key]["line"], evData[key]["book"], evData[key]))

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