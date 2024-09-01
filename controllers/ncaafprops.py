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
		"north carolina state": "nc state",
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
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" ii", "").replace(" iii", "").replace(" iv", "")
	if player == "joquavious marks":
		return "woody marks"
	return player

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

	{

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			return player;
		}

		let data = {};

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
					let player = parsePlayer(playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText);
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
					let player = parsePlayer(playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText);
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

def writeCZ(date=None, token=None):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/americanfootball/events/schedule?competitionIds=b7eda1b3-0170-4510-9616-1bce561d7aa7"
	outfile = "ncaafoutCZ"
	cookie = "18397176-0983-4317-84cb-816fa1699cf4:EgoAu4pmpDdmAQAA:jtQ2KxjmXN9kQhHqkpnHqzd1zBoF3DKDubbI4xuyAZCbIyOgei4n4qJJ+W7Qpf+elQyz5v0SEMUmgoxuS+ZRqG+GAINIGUpIrP8V/DnMAuId9K/0PGwOdTKmavypIq+/+IM4KOgo42W+OKlj8D35WYeu0FiGuYzfrbP7UiF6FhgJzi4wadr4Z/15gL6fyKMdMWokPTa++BCLUHiNo2LWnoXt/Qf5EoK7b/yYbGVYElxJa3HOaWzu/JK7UX0PjznHkdGm9XIhUCLRjg=="
	if token:
		cookie = token
	
	os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"]:
		if str(datetime.strptime(event["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
		games.append(event["id"])

	#games = ["9008305d-4519-434f-8362-9af8b5167e2d"]

	res = {}
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/events/{gameId}"
		time.sleep(0.2)
		os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			awayTeam = data["markets"][0]["selections"][0]["teamData"]["teamCity"]
			homeTeam = data["markets"][0]["selections"][1]["teamData"]["teamCity"]
		except:
			continue
		game = f"{awayTeam} @ {homeTeam}".lower()
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
			if "1st half" in prop:
				prefix = "1h_"
			elif "1st quarter" in prop:
				prefix = "1q_"

			if prop in ["money line"]:
				prop = "ml"
			elif prop == "player to score a touchdown":
				prop = "attd"
			elif market["templateName"].lower().split(" ")[0] == "|player":
				player = parsePlayer(market["name"].split("|")[1])
				prop = market["name"].lower().split("|")[-2].replace("total ", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("interceptions", "int").replace("touchdowns", "td").replace("yards", "yd").replace(" ", "_")
			elif "total points" in prop:
				prop = "total"
			elif "spread" in prop:
				prop = "spread"
			else:
				#print(prop)
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			selections = market["selections"]
			skip = 1 if prop in ["attd"] else 2
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

				if "ml" in prop:
					res[game][prop] = ou
				elif prop == "attd":
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
						line = float(prices["line"])
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


	with open("static/ncaafprops/cz.json", "w") as fh:
		json.dump(res, fh, indent=4)


def writeESPN():
	js = """

	{
		function convertTeam(team) {
			team = team.toLowerCase();
			if (team[0] == "(") {
				team = team.split(") ")[1];
			}
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
			for (detail of document.querySelectorAll("details")) {
				let prop = detail.querySelector("h2").innerText.toLowerCase();

				if (prop == "moneyline") {
					prop = "ml";
				} else if (prop == "match spread") {
					prop = "spread";
				} else if (prop == "total points") {
					prop = "total";
				}

				data[game][prop] = {};

				let btns = detail.querySelectorAll("button");
				for (i = 0; i < btns.length; i += 2) {
					if (btns[i].innerText == "See All Lines") {
						continue;
					}
					let ou = btns[i].querySelectorAll("span")[1].innerText+"/"+btns[i+1].querySelectorAll("span")[1].innerText;

					if (prop == "ml") {
						data[game][prop] = ou;
					} else {
						let line = btns[i].querySelector("span").innerText.split(" ");
						line = line[line.length - 1];
						data[game][prop][line] = ou;
					}
				}
			}

			for (tab of document.querySelectorAll("button[data-testid='tablist-carousel-tab']")) {
				if (tab.innerText == "Player Props") {
					tab.click();
					break;
				}
			}
			while (!document.querySelectorAll("h2")[2].innerText.includes("Touchdown")) {
				await new Promise(resolve => setTimeout(resolve, 500));
			}

			let players = {};
			for (detail of document.querySelectorAll("details")) {
				let prop = detail.querySelector("h2").innerText.toLowerCase();

				let open = detail.getAttribute("open");
				if (open == null) {
					detail.querySelector("summary").click();
					while (detail.querySelectorAll("button").length == 0) {
						await new Promise(resolve => setTimeout(resolve, 500));
					}
				}

				if (prop == "to score a touchdown") {
					prop = "attd";
				} else if (prop == "first touchdown scorer") {
					prop = "ftd";
				} else if (prop.split(" ")[0] == "player") {
					if (prop.includes("+") || prop.includes("kicking") || prop.includes("extra")) {
						continue;
					}
					prop = prop.replace("player ", "").replace("total ", "").replace("passing", "pass").replace("rushing", "rush").replace("receptions", "rec").replace("reception", "rec").replace("receiving", "rec").replace("attempts", "att").replace("completions", "cmp").replace("completion", "cmp").replace("yards", "yd").replace("tds", "td").replace(" ", "_");
				} else {
					continue;
				}

				data[game][prop] = {};

				let btns = detail.querySelectorAll("button");
				let seeAll = false;
				if (btns[btns.length - 1].innerText == "See All Lines") {
					seeAll = true;
					btns[btns.length - 1].click();
				}

				if (seeAll) {
					let modal = document.querySelector(".modal--see-all-lines");
					while (!modal) {
						await new Promise(resolve => setTimeout(resolve, 500));
						modal = document.querySelector(".modal--see-all-lines");
					}

					let btns = Array.from(modal.querySelectorAll("button"));
					btns.shift();
					for (i = 0; i < btns.length; i += 3) {
						let ou = btns[i+1].querySelectorAll("span")[1].innerText+"/"+btns[i+2].querySelectorAll("span")[1].innerText;
						let player = parsePlayer(btns[i].innerText.toLowerCase().split(" to score ")[0].split(" first ")[0]);
						let last = player.split(" ");
						last.shift();
						last = last.join(" ");
						players[player.split(" ")[0][0]+" "+last] = player;
						data[game][prop][player] = ou;
					}
					modal.querySelector("button").click();
					while (document.querySelector(".modal--see-all-lines")) {
						await new Promise(resolve => setTimeout(resolve, 500));
					}
				} else if (["attd", "ftd"].includes(prop)) {
					let btns = detail.querySelectorAll("button");
					for (i = 0; i < btns.length; i += 3) {
						let ou = btns[i+1].querySelectorAll("span")[1].innerText+"/"+btns[i+2].querySelectorAll("span")[1].innerText;
						let player = parsePlayer(btns[i].innerText.toLowerCase().split(" to score ")[0].split(" first ")[0]);
						let last = player.split(" ");
						last.shift();
						last = last.join(" ");
						players[player.split(" ")[0][0]+" "+last] = player;
						data[game][prop][player] = ou;
					}
				} else {
					let btns = detail.querySelectorAll("button");
					for (i = 0; i < btns.length; i += 2) {
						let player = parsePlayer(btns[i].parentElement.parentElement.previousSibling.innerText.toLowerCase());
						if (players[player]) {
							player = players[player];
						}
						let ou = btns[i].querySelectorAll("span")[1].innerText+"/"+btns[i+1].querySelectorAll("span")[1].innerText;
						let line = btns[i].querySelector("span").innerText.split(" ");
						line = line[line.length - 1];
						data[game][prop][player] = {};
						data[game][prop][player][line] = ou;
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
					let awayTeam = convertTeam(btns[0].querySelector(".text-primary").innerText);
					let homeTeam = convertTeam(btns[1].querySelector(".text-primary").innerText);
					let game = awayTeam + " @ " + homeTeam;

					if (data[game]) {
						continue;
					}
					
					console.log(game);
					data[game] = {};

					btns[0].click();

					while (!window.location.href.includes("event")) {
						await new Promise(resolve => setTimeout(resolve, 500));
					}

					await new Promise(resolve => setTimeout(resolve, 2000));

					status = "";
					readPage(game);

					while (status != "done") {
						await new Promise(resolve => setTimeout(resolve, 2000));
					}

					document.querySelector("a[aria-labelledby=NCAAF-8]").click();

					/*
					while (window.location.href.includes("event")) {
						await new Promise(resolve => setTimeout(resolve, 1000));
					}
					*/

					await new Promise(resolve => setTimeout(resolve, 5000));

					//testing
					//break;
					console.log(data);
				}
				break;
			}
			console.log(data);
		}

		main();
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
					try:
						ou = f"{convertAmericanOdds(markets[0]['odds'])}/{convertAmericanOdds(markets[1]['odds'])}"
					except:
						continue
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
			url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/87637/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outncaaf"
			cookie = "-H 'Cookie: hgg=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWQiOiIxODU4ODA5NTUwIiwiZGtzLTYwIjoiMjg1IiwiZGtlLTEyNiI6IjM3NCIsImRrcy0xNzkiOiI1NjkiLCJka2UtMjA0IjoiNzA5IiwiZGtlLTI4OCI6IjExMjgiLCJka2UtMzE4IjoiMTI2MSIsImRrZS0zNDUiOiIxMzUzIiwiZGtlLTM0NiI6IjEzNTYiLCJka2UtNDI5IjoiMTcwNSIsImRrZS03MDAiOiIyOTkyIiwiZGtlLTczOSI6IjMxNDAiLCJka2UtNzU3IjoiMzIxMiIsImRraC03NjgiOiJxU2NDRWNxaSIsImRrZS03NjgiOiIwIiwiZGtlLTgwNiI6IjM0MjYiLCJka2UtODA3IjoiMzQzNyIsImRrZS04MjQiOiIzNTExIiwiZGtlLTgyNSI6IjM1MTQiLCJka3MtODM0IjoiMzU1NyIsImRrZS04MzYiOiIzNTcwIiwiZGtoLTg5NSI6IjhlU3ZaRG8wIiwiZGtlLTg5NSI6IjAiLCJka2UtOTAzIjoiMzg0OCIsImRrZS05MTciOiIzOTEzIiwiZGtlLTk0NyI6IjQwNDIiLCJka2UtOTc2IjoiNDE3MSIsImRrcy0xMTcyIjoiNDk2NCIsImRrcy0xMTc0IjoiNDk3MCIsImRrcy0xMjU1IjoiNTMyNiIsImRrcy0xMjU5IjoiNTMzOSIsImRrZS0xMjc3IjoiNTQxMSIsImRrZS0xMzI4IjoiNTY1MyIsImRraC0xNDYxIjoiTjZYQmZ6S1EiLCJka3MtMTQ2MSI6IjAiLCJka2UtMTU2MSI6IjY3MzMiLCJka2UtMTY1MyI6IjcxMzEiLCJka2UtMTY1NiI6IjcxNTEiLCJka2UtMTY4NiI6IjcyNzEiLCJka2UtMTcwOSI6IjczODMiLCJka3MtMTcxMSI6IjczOTUiLCJka2UtMTc0MCI6Ijc1MjciLCJka2UtMTc1NCI6Ijc2MDUiLCJka3MtMTc1NiI6Ijc2MTkiLCJka3MtMTc1OSI6Ijc2MzYiLCJka2UtMTc2MCI6Ijc2NDkiLCJka2UtMTc2NiI6Ijc2NzUiLCJka2gtMTc3NCI6IjJTY3BrTWF1IiwiZGtlLTE3NzQiOiIwIiwiZGtlLTE3NzAiOiI3NjkyIiwiZGtlLTE3ODAiOiI3NzMxIiwiZGtlLTE2ODkiOiI3Mjg3IiwiZGtlLTE2OTUiOiI3MzI5IiwiZGtlLTE3OTQiOiI3ODAxIiwiZGtlLTE4MDEiOiI3ODM4IiwiZGtoLTE4MDUiOiJPR2tibGtIeCIsImRrZS0xODA1IjoiMCIsImRrcy0xODE0IjoiNzkwMSIsImRraC0xNjQxIjoiUjBrX2xta0ciLCJka2UtMTY0MSI6IjAiLCJka2UtMTgyOCI6Ijc5NTYiLCJka2gtMTgzMiI6ImFfdEFzODZmIiwiZGtlLTE4MzIiOiIwIiwiZGtzLTE4NDciOiI4MDU0IiwiZGtzLTE3ODYiOiI3NzU4IiwiZGtlLTE4NTEiOiI4MDk3IiwiZGtlLTE4NTgiOiI4MTQ3IiwiZGtlLTE4NjEiOiI4MTU3IiwiZGtlLTE4NjAiOiI4MTUyIiwiZGtlLTE4NjgiOiI4MTg4IiwiZGtoLTE4NzUiOiJZRFJaX3NoSiIsImRrcy0xODc1IjoiMCIsImRrcy0xODc2IjoiODIxMSIsImRraC0xODc5IjoidmI5WWl6bE4iLCJka2UtMTg3OSI6IjAiLCJka2UtMTg0MSI6IjgwMjQiLCJka3MtMTg4MiI6IjgyMzkiLCJka2UtMTg4MSI6IjgyMzYiLCJka2UtMTg4MyI6IjgyNDMiLCJka2UtMTg4MCI6IjgyMzIiLCJka2UtMTg4NyI6IjgyNjQiLCJka2UtMTg5MCI6IjgyNzYiLCJka2UtMTkwMSI6IjgzMjYiLCJka2UtMTg5NSI6IjgzMDAiLCJka2gtMTg2NCI6IlNWbjFNRjc5IiwiZGtlLTE4NjQiOiIwIiwibmJmIjoxNzIyNDQyMjc0LCJleHAiOjE3MjI0NDI1NzQsImlhdCI6MTcyMjQ0MjI3NCwiaXNzIjoiZGsifQ.jA0OxjKzxkyuAktWmqFbJHkI6SWik-T-DyZuLjL9ZKM; STE=\"2024-07-31T16:43:12.166175Z\"; STIDN=eyJDIjoxMjIzNTQ4NTIzLCJTIjo3MTU0NjgxMTM5NCwiU1MiOjc1Mjc3OTAxMDAyLCJWIjoxODU4ODA5NTUwLCJMIjoxLCJFIjoiMjAyNC0wNy0zMVQxNjo0MToxNC42ODc5Mzk4WiIsIlNFIjoiVVMtREsiLCJVQSI6IngxcVNUYXJVNVFRRlo3TDNxcUlCbWpxWFozazhKVmt2OGFvaCttT1ZpWFE9IiwiREsiOiIzMTQyYjRkMy0yNjU2LTRhNDMtYTBjNi00MTEyM2Y5OTEyNmUiLCJESSI6IjEzNTBmMGM0LWQ3MDItNDUwZC1hOWVmLTJlZjRjZjcxOTY3NyIsIkREIjo0NDg3NTQ0MDk4OH0=; STH=3a3368e54afc8e4c0a5c91094077f5cd1ce31d692aaaf5432b67972b5c3eb6fc; _abck=56D0C7A07377CFD1419CD432549CD1DB~0~YAAQJdbOF6Bzr+SQAQAAsmCPCQykOCRLV67pZ3Dd/613rD8UDsL5x/r+Q6G6jXCECjlRwzW7ESOMYaoy0fhStB3jiEPLialxs/UD9kkWAWPhuOq/RRxzYkX+QY0wZ/Uf8WSSap57OIQdRC3k3jlI6z2G8PKs4IyyQ/bRZfS2Wo6yO0x/icRKUAUeESKrgv6XrNaZCr14SjDVxBBt3Qk4aqJPKbWIbaj+1PewAcP+y/bFEVCmbcrAruJ4TiyqMTEHbRtM9y2O0WsTg79IZu52bpOI2jFjEUXZNRlz2WVhxbApaKY09QQbbZ3euFMffJ25/bXgiFpt7YFwfYh1v+4jrIvbwBwoCDiHn+xy17v6CXq5hIEyO4Bra6QT1sDzil+lQZPgqrPBE0xwoHxSWnhVr60EK1X5IVfypMHUcTvLKFcEP2eqwSZ67Luc/ompWuxooaOVNYrgvH/Vvs5UbyVOEsDcAXoyGt0BW3ZVMVPHXS/30dP3Rw==~-1~-1~1722445877; PRV=3P=0&V=1858809550&E=1720639388; ss-pid=4CNl0TGg6ki1ygGONs5g; ab.storage.deviceId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%22fe7382ec-2564-85bf-d7c4-3eea92cb7c3e%22%2C%22c%22%3A1709950180242%2C%22l%22%3A1709950180242%7D; ab.storage.userId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%2228afffab-27db-4805-85ca-bc8af84ecb98%22%2C%22c%22%3A1712278087074%2C%22l%22%3A1712278087074%7D; ab.storage.sessionId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%223eff9525-6179-dc9c-ce88-9e51fca24c58%22%2C%22e%22%3A1722444192818%2C%22c%22%3A1722442278923%2C%22l%22%3A1722442392818%7D; _gcl_au=1.1.386764008.1720096930; _ga_QG8WHJSQMJ=GS1.1.1722442278.7.1.1722442393.19.0.0; _ga=GA1.2.2079166597.1720096930; _dpm_id.16f4=b3163c2a-8640-4fb7-8d66-2162123e163e.1720096930.7.1722442393.1722178863.1f3bf842-66c7-446c-95e3-d3d5049471a9; _tgpc=78b6db99-db5f-5ce5-848f-0d7e4938d8f2; _tglksd=eyJzIjoiYjRkNjE4MWYtMTJjZS01ZDJkLTgwNTYtZWQ2NzIxM2MzMzM2Iiwic3QiOjE3MjI0NDIyNzgyNzEsInNvZCI6IihkaXJlY3QpIiwic29kdCI6MTcyMTg3ODUxOTY5OCwic29kcyI6Im8iLCJzb2RzdCI6MTcyMTg3ODUxOTY5OH0=; _sp_srt_id.16f4=55c32e85-f32f-42ac-a0e8-b1e37c9d3bc6.1720096930.6.1722442279.1722178650.6d45df5a-aea8-4a66-a4ba-0ef841197d1d.cdc2d898-fa3f-4430-a4e4-b34e1909bb05...0; _scid=e6437688-491e-4800-b4b2-e46e81b2816c; _ga_M8T3LWXCC5=GS1.2.1722442279.7.1.1722442288.51.0.0; _svsid=9d0929120b67695ad6ee074ccfd583b7; _sctr=1%7C1722398400000; _hjSessionUser_2150570=eyJpZCI6ImNmMDA3YTA2LTFiNmMtNTFkYS05Y2M4LWNmNTAyY2RjMWM0ZCIsImNyZWF0ZWQiOjE3MjA1NTMwMDE4OTMsImV4aXN0aW5nIjp0cnVlfQ==; _csrf=ba945d1a-57c4-4b50-a4b2-1edea5014b72; ss-id=x8zwcqe0hExjZeHXAKPK; ak_bmsc=F8F9B7ED0366DC4EB63B2DD6D078134C~000000000000000000000000000000~YAAQJdbOF3hzr+SQAQAAp1uPCRjLBiubHwSBX74Dd/8hmIdve4Tnb++KpwPtaGp+NN2ZcEf+LtxC0PWwzhZQ1one2MxGFFw1J6BXg+qiFAoQ6+I3JExoHz4r+gqodWq7y5Iri7+3aBFQRDtn17JMd1PTEEuN8EckzKIidL3ggrEPS+h1qtof3aHJUdx/jkCUjkaN/phWSvohlUGscny8dJvRz76e3F20koI5UsjJ/rQV7dUn6HNw1b5H1tDeL7UR1mbBrCLz6YPDx4XCjybvteRQpyLGI0o9L6xhXqv12exVAbZ15vpuNJalhR6eB4/PVwCmfVniFcr/xc8hivkuBBMOj1lN7ADykNA60jFaIRAY2BD2yj27Aedr7ETAFnvac0L0ITfH20LkA2cFhGUxmzOJN0JQ6iTU7VGgk19FzV+oeUxNmMPX; bm_sz=D7ABF43D4A5671594F842F6C403AB281~YAAQJdbOF3lzr+SQAQAAp1uPCRgFgps3gN3zvxvZ+vbm5t9IRWYlb7as+myjQOyHzYhriG6n+oxyoRdQbE6wLz996sfM/6r99tfwOLP2K8ULgA2nXfOPvqk6BwofdTsUd7KP7EnKhcCjhADO18uKB/QvIJgyS3IFBROxP2XFzS15m/DrRbF7lQDRscWtVo8oOITxNTBlwg0g4fI3gzjG6A4uHYxjeCegxSrHFHGFr4KZXgOnsJhmZe0lqIRWUFcIKC/gfsDd+jfyUnprMso1Flsv9blGlvycOoWTHPdEQvUudpOZlZ3JYz9H5y+dU94wBD9ejxIlRKP26giQISjun829Kt7CuKxJXYAcSJeiomZFh5Abj+Mkv0wi6ZcRcmOVFt49eywPazFHpGM8DVcUkVEFMcpNCeiJ/CtC60U9SoJy+ermF1hTqiAq~3622209~4408134; bm_sv=6618DE86472CB31D7B7F16DAE6689651~YAAQJdbOF96Lr+SQAQAA4iSRCRjfwGUmEhVBbE3y/2VDAAvuPyI2gX7io7CQCPfcdMOnBnNhxHIKYt9PFr7Y1TADQHFUC9kqXu7Nbj9d1BrLlfi1rPbv/YKPqhqSTLkbNSWbeKhKM4HfOu7C+RLV383VzGeyDhc2zOuBKBVNivHMTF9njS3vK6RKeSPFCfxOJdDHgNlIYykf0Ke2WJvflHflTUykwWUaYIlqoB52Ixb9opHQVTptWjetGdYjuOO2S2ZPkw==~1; _dpm_ses.16f4=*; _tgidts=eyJzaCI6ImQ0MWQ4Y2Q5OGYwMGIyMDRlOTgwMDk5OGVjZjg0MjdlIiwiY2kiOiIxZDMxOGRlZC0yOWYwLTUzYjItYjFkNy0yMDlmODEwNDdlZGYiLCJzaSI6ImI0ZDYxODFmLTEyY2UtNWQyZC04MDU2LWVkNjcyMTNjMzMzNiJ9; _tguatd=eyJzYyI6IihkaXJlY3QpIn0=; _tgsid=eyJscGQiOiJ7XCJscHVcIjpcImh0dHBzOi8vc3BvcnRzYm9vay5kcmFmdGtpbmdzLmNvbSUyRmxlYWd1ZXMlMkZiYXNlYmFsbCUyRm1sYlwiLFwibHB0XCI6XCJNTEIlMjBCZXR0aW5nJTIwT2RkcyUyMCUyNiUyMExpbmVzJTIwJTdDJTIwRHJhZnRLaW5ncyUyMFNwb3J0c2Jvb2tcIixcImxwclwiOlwiXCJ9IiwicHMiOiJkOTY4OTkxNy03ZTAxLTQ2NTktYmUyOS1mZThlNmI4ODY3MzgiLCJwdmMiOiIxIiwic2MiOiJiNGQ2MTgxZi0xMmNlLTVkMmQtODA1Ni1lZDY3MjEzYzMzMzY6LTEiLCJlYyI6IjUiLCJwdiI6IjEiLCJ0aW0iOiJiNGQ2MTgxZi0xMmNlLTVkMmQtODA1Ni1lZDY3MjEzYzMzMzY6MTcyMjQ0MjI4MjA3NDotMSJ9; _sp_srt_ses.16f4=*; _gid=GA1.2.150403708.1722442279; _scid_r=e6437688-491e-4800-b4b2-e46e81b2816c; _uetsid=85e6d8504f5711efbe6337917e0e834a; _uetvid=d50156603a0211efbb275bc348d5d48b; _hjSession_2150570=eyJpZCI6ImQxMTAyZTZjLTkyYzItNGMwNy1hNzMzLTcxNDhiODBhOTI4MyIsImMiOjE3MjI0NDIyODE2NDUsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _rdt_uuid=1720096930967.9d40f035-a394-4136-b9ce-2cf3bb298115'"
			os.system(f"curl {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' {cookie} -o {outfile}")

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
								lines[game][label][player] = {
									outcomes[0]['line']: f"{outcomes[0]['oddsAmerican']}"
								}
								if len(row["outcomes"]) > 1:
									lines[game][label][player][outcomes[0]['line']] += f"/{outcomes[1]['oddsAmerican']}"

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
			//console.log(a.parentElement.parentElement.innerText.includes("Today"), a.parentElement.parentElement, );
			if (a.parentElement.parentElement.querySelector("ms-prematch-timer") && a.parentElement.parentElement.querySelector("ms-prematch-timer").innerText.includes("Today")) {
				ids.push(href[href.length - 1]);
			}
		}
		console.log(ids);
	}
"""

	ids = [
    "15860764"
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
			if "1st half" in prop or "first half" in prop:
				prefix = "1h_"
			elif "1st quarter" in prop or "first quarter" in prop:
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
					ou = f"{betOffer['outcomes'][0]['oddsAmerican']}/{betOffer['outcomes'][1]['oddsAmerican']}"
					if betOffer["outcomes"][0]["label"] == "Under":
						ou = f"{betOffer['outcomes'][1]['oddsAmerican']}/{betOffer['outcomes'][0]['oddsAmerican']}"
					data[game][prop][player][line] = ou
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

		try:
			with open(path) as fh:
				j = json.load(fh)
		except:
			continue

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



def writeFanduelManual():
	js = """

	{

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			return player;
		}
		
		const data = {};
		let status = "";

		async function readPage(game) {

			for (arrow of document.querySelectorAll("div[data-test-id=ArrowAction]")) {
				let div = arrow.parentElement.parentElement.parentElement;
				let prop = arrow.getAttribute("aria-label").toLowerCase();

				let skip = 2;
				if (prop == "game lines") {
					prop = "lines";
				} else if (prop == "touchdown scorers") {
					prop = "attd";
					data[game]["ftd"] = {};
				} else if (prop.indexOf("player") == 0) {
					prop = prop.replace("player ", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("total receptions", "rec").replace("yds", "yd").replace("tds", "td").replace(" ", "_");
				} else if (prop == "1st half winner") {
					prop = "1h_ml";
				} else if (prop == "1st half spread") {
					prop = "1h_spread";
				} else if (prop == "1st half total") {
					prop = "1h_total";
				} else if (prop.includes("total points")) {
					if (prop.includes("parlay") || prop.includes("alternate")) {
						continue;
					}
					prop = "team_total";
				} else {
					continue;
				}

				if (prop != "lines" && arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
					arrow.click();
					while (arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
						await new Promise(resolve => setTimeout(resolve, 1000));
					}
				}

				let el = div.querySelector("div[aria-label='Show more']");
				if (el) {
					el.click();
					while (!div.querySelector("div[aria-label='Show less']")) {
						await new Promise(resolve => setTimeout(resolve, 1000));	
					}
				}

				await new Promise(resolve => setTimeout(resolve, 500));

				if (prop != "lines" && prop != "team_total" && !data[game][prop]) {
					data[game][prop] = {};
				}

				while (div.querySelectorAll("div[role=button]").length == 0) {
					await new Promise(resolve => setTimeout(resolve, 1000));
				}

				let btns = Array.from(div.querySelectorAll("div[role=button]"));
				btns.shift();

				if (btns[0].innerText.includes("Read more")) {
					btns.shift();
				}

				if (prop == "lines") {
					if (!btns[1].getAttribute("aria-label").includes("unavailable")) {
						data[game]["ml"] = btns[1].getAttribute("aria-label").split(", ")[2].split(" ")[0]+"/"+btns[4].getAttribute("aria-label").split(", ")[2].split(" ")[0];
					}
					if (!btns[0].getAttribute("aria-label").includes("unavailable")) {
						line = btns[0].getAttribute("aria-label").split(", ")[2];
						data[game]["spread"] = {};
						data[game]["spread"][line.replace("+", "")] = btns[0].getAttribute("aria-label").split(", ")[3].split(" ")[0] + "/" + btns[3].getAttribute("aria-label").split(", ")[3].split(" ")[0];
					}
					line = btns[2].getAttribute("aria-label").split(", ")[3].split(" ")[1];
					data[game]["total"] = {};
					data[game]["total"][line] = btns[2].getAttribute("aria-label").split(", ")[4].split(" ")[0] + "/" + btns[5].getAttribute("aria-label").split(", ")[4].split(" ")[0];
					continue;
				}

				for (let i = 0; i < btns.length; i += skip) {
					const btn = btns[i];
					if (btn.getAttribute("data-test-id")) {
						continue;
					}
					const label = btn.getAttribute("aria-label");
					if (!label) {
						continue;
					}
					if (label == "Show more" || label == "Show less") {
						continue;
					}
					const fields = label.split(", ");
					let line = fields[1].split(" ")[1];
					let odds = fields[fields.length - 1].split(" ")[0];

					if (prop == "attd") {
						const player = parsePlayer(fields[1].split(" (")[0]);
						data[game][prop][player] = odds;
						data[game]["ftd"][player] = btns[i+1].getAttribute("aria-label").split(", ")[2];
					} else if (prop == "1h_ml") {
						if (label.includes("unavailable")) {
							delete data[game][prop];
							continue;
						}
						data[game][prop] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[2];
					} else if (prop == "1h_spread") {
						data[game][prop][fields[2]] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[3];
					} else if (prop == "1h_total") {
						data[game][prop][fields[2].split(" ")[1]] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
					} else if (prop == "team_total") {
						let p = "home_total";
						if (data[game][p]) {
							p = "away_total";
						}
						data[game][p] = {};
						data[game][p][fields[2]] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[3];
					} else {
						const player = parsePlayer(fields[0].split(" (")[0]);
						if (!data[game][prop][player]) {
							data[game][prop][player] = {};
						}
						data[game][prop][player][line] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[2].split(" ")[0];
					}
				}
			}
			status = "done";
		}

		function openDialog() {
			let dialog = document.querySelector("div[role=dialog]");
			if (!dialog) {
				document.querySelector("div[role=button]").click();
			}
		}

		async function chooseGame() {
			openDialog();
			let dialog = document.querySelector("div[role=dialog]");
			while (!dialog) {
				dialog = document.querySelector("div[role=dialog]");
				await new Promise(resolve => setTimeout(resolve, 100));
			}
			
			for (li of dialog.querySelectorAll("li")) {
				const game = li.querySelector("a").getAttribute("title").toLowerCase();
				if (li.querySelector("title")) {
					continue;
				}
				if (li.querySelectorAll("span")[2].innerText == "Sunday") {
					gameStatus = "break";
					return;
				}
				if (data[game]) {
					continue;
				}
				data[game] = {};

				li.querySelector("a").click();

				/*
				while (!document.querySelector("h1") || document.querySelector("h1").innerText.toLowerCase().replace(" odds", "") != game) {
					await new Promise(resolve => setTimeout(resolve, 1000));
				}
				*/

				await new Promise(resolve => setTimeout(resolve, 5000));

				status = "";
				readPage(game);
				while (status != "done") {
					await new Promise(resolve => setTimeout(resolve, 1000));
				}
				gameStatus = "good";
				return;
			}
			gameStatus = "break";
			return;
		}

		async function main() {
			let idx = 0;
			while (true) {
				if (idx > 1) {
					//break;
				}

				gameStatus = "";
				chooseGame();
				while (gameStatus == "") {
					await new Promise(resolve => setTimeout(resolve, 1000));
				}
				if (gameStatus == "break") {
					break;
				}
				idx += 1;
			}

			console.log(data);
		}

		main();
	}
"""

def writeFanduelGame():
	js = """

	{

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			return player;
		}
		
		const data = {};
		let status = "";

		async function readPage(game) {

			for (arrow of document.querySelectorAll("div[data-test-id=ArrowAction]")) {
				let div = arrow.parentElement.parentElement.parentElement;
				let prop = arrow.getAttribute("aria-label").toLowerCase();

				let skip = 2;
				if (prop == "game lines") {
					prop = "lines";
				} else if (prop == "touchdown scorers") {
					prop = "attd";
					data[game]["ftd"] = {};
				} else if (prop.indexOf("player") == 0) {
					prop = prop.replace("player ", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("total receptions", "rec").replace("yds", "yd").replace("tds", "td").replace(" ", "_");
				} else if (prop == "1st half winner") {
					prop = "1h_ml";
				} else if (prop == "1st half spread") {
					prop = "1h_spread";
				} else if (prop == "1st half total") {
					prop = "1h_total";
				} else if (prop.includes("total points")) {
					if (prop.includes("parlay") || prop.includes("alternate")) {
						continue;
					}
					prop = "team_total";
				} else {
					continue;
				}

				if (prop != "lines" && arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
					arrow.click();
					while (arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
						await new Promise(resolve => setTimeout(resolve, 1000));
					}
				}

				let el = div.querySelector("div[aria-label='Show more']");
				if (el) {
					el.click();
					while (!div.querySelector("div[aria-label='Show less']")) {
						await new Promise(resolve => setTimeout(resolve, 1000));	
					}
				}

				await new Promise(resolve => setTimeout(resolve, 500));

				if (prop != "lines" && prop != "team_total" && !data[game][prop]) {
					data[game][prop] = {};
				}

				while (div.querySelectorAll("div[role=button]").length == 0) {
					await new Promise(resolve => setTimeout(resolve, 1000));
				}

				let btns = Array.from(div.querySelectorAll("div[role=button]"));
				btns.shift();

				if (btns[0].innerText.includes("Read more")) {
					btns.shift();
				}

				if (prop == "lines") {
					if (!btns[1].getAttribute("aria-label").includes("unavailable")) {
						data[game]["ml"] = btns[1].getAttribute("aria-label").split(", ")[2].split(" ")[0]+"/"+btns[4].getAttribute("aria-label").split(", ")[2].split(" ")[0];
					}
					if (!btns[0].getAttribute("aria-label").includes("unavailable")) {
						line = btns[0].getAttribute("aria-label").split(", ")[2];
						data[game]["spread"] = {};
						data[game]["spread"][line.replace("+", "")] = btns[0].getAttribute("aria-label").split(", ")[3].split(" ")[0] + "/" + btns[3].getAttribute("aria-label").split(", ")[3].split(" ")[0];
					}
					line = btns[2].getAttribute("aria-label").split(", ")[3].split(" ")[1];
					data[game]["total"] = {};
					data[game]["total"][line] = btns[2].getAttribute("aria-label").split(", ")[4].split(" ")[0] + "/" + btns[5].getAttribute("aria-label").split(", ")[4].split(" ")[0];
					continue;
				}

				for (let i = 0; i < btns.length; i += skip) {
					const btn = btns[i];
					if (btn.getAttribute("data-test-id")) {
						continue;
					}
					const label = btn.getAttribute("aria-label");
					if (!label) {
						continue;
					}
					if (label == "Show more" || label == "Show less") {
						continue;
					}
					const fields = label.split(", ");
					let line = fields[1].split(" ")[1];
					let odds = fields[fields.length - 1].split(" ")[0];

					if (prop == "attd") {
						const player = parsePlayer(fields[1].split(" (")[0]);
						data[game][prop][player] = odds;
						data[game]["ftd"][player] = btns[i+1].getAttribute("aria-label").split(", ")[2];
					} else if (prop == "1h_ml") {
						if (label.includes("unavailable")) {
							delete data[game][prop];
							continue;
						}
						data[game][prop] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[2];
					} else if (prop == "1h_spread") {
						data[game][prop][fields[2]] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[3];
					} else if (prop == "1h_total") {
						data[game][prop][fields[2].split(" ")[1]] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
					} else if (prop == "team_total") {
						let p = "home_total";
						if (data[game][p]) {
							p = "away_total";
						}
						data[game][p] = {};
						data[game][p][fields[2]] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[3];
					} else {
						const player = parsePlayer(fields[0].split(" (")[0]);
						if (!data[game][prop][player]) {
							data[game][prop][player] = {};
						}
						data[game][prop][player][line] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[2].split(" ")[0];
					}
				}
			}
			status = "done";
		}

		async function main() {
			let game = document.querySelector("h1").innerText.toLowerCase().replace(" odds", "");

			data[game] = {};
			readPage(game);
			while (status != "done") {
				await new Promise(resolve => setTimeout(resolve, 1000));
			}

			console.log(data);
		}

		main();
	}
"""

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	
	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/football/ncaa-football") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && (time.innerText.split(" ")[0] === "FRI" || time.innerText.split(" ").length < 3)) {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/tulane-@-memphis-32701487",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/fresno-state-@-utah-state-32701498",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/stanford-@-colorado-32700294"
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
						player = parsePlayer(runners[i]["runnerName"].lower().replace(" over", "").replace(" under", "")).split(" (")[0]
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

	with open(f"{prefix}static/ncaafprops/espn.json") as fh:
		espnLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/ncaafprops/cz.json") as fh:
		cz = json.load(fh)

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
		#"bv": bvLines,
		"cz": cz,
		"dk": dkLines,
		"espn": espnLines
	}

	for game in fdLines:
		if teamArg and teamArg not in game:
			continue
		#if game not in actionnetwork:
		#	continue

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
									continue
								o = val
								ou = val

							if not o or o == ".":
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

	output = "\t".join(["EV", "EV Book", "Game", "Player", "Prop", "O/U", "FD", "DK", "ESPN", "MGM", "Kambi", "PN", "CZ", "BV"]) + "\n"
	for row in sorted(data, reverse=True):
		d = evData[row[-1]]
		ou = ("u" if d["under"] else "o")+" "
		if d["player"]:
			ou += d["playerHandicap"]
		else:
			ou += d["handicap"]
		arr = [row[0], str(d["line"])+" "+d["book"].upper(), d["game"], d["player"].title(), d["prop"], ou]
		for book in ["fd", "dk", "espn", "mgm", "kambi", "pn", "cz", "bv"]:
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
	parser.add_argument("--cz", action="store_true", help="CZR")
	parser.add_argument("--pn", action="store_true", help="Pinnacle")
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("-g", "--game", help="Game")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("--book", help="Book")
	parser.add_argument("--token", help="Token")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--fd", action="store_true", help="FD")
	parser.add_argument("--dk", action="store_true", help="DK")
	parser.add_argument("-p", "--print", action="store_true", help="Print")
	parser.add_argument("--notd", action="store_true", help="Not ATTD FTD")

	args = parser.parse_args()

	if args.update:
		#writeFanduel()
		writeActionNetwork(args.date)
		writeKambi(args.date)
		writeMGM()
		writePinnacle()
		#writeBovada()
		writeDK()
		writeCZ(args.date, args.token)

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

	if args.cz:
		writeCZ(args.date, args.token)

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