
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

def writePinnacle(date):
	if not date:
		date = str(datetime.now())[:10]

	outfile = f"tennisoutPN"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/sports/33/markets/straight?primaryOnly=false&withSpecials=false" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile

	os.system(url)
	with open(outfile) as fh:
		data = json.load(fh)

	ids = []
	for row in data:
		if str(datetime.strptime(row["cutoffAt"][:-6].split(".")[0], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=4))[:10] != date:
			continue
		if row["matchupId"] not in ids:
			ids.append(row["matchupId"])

	res = {}
	for bid in ids:
		url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

		time.sleep(0.3)
		os.system(url)
		with open(outfile) as fh:
			related = json.load(fh)

		url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

		time.sleep(0.3)
		os.system(url)
		with open(outfile) as fh:
			data = json.load(fh)

		try:
			gamesMatchup = related[0]["id"] if related[0]["units"] == "Games" else related[1]["id"]
		except:
			gamesMatchup = ""
		try:
			player1 = related[0]["participants"][0]["name"].lower()
			player2 = related[0]["participants"][1]["name"].lower()
			if " / " in player1:
				player1 = player1.split(" / ")[0].split(" ")[0] + " / " + player1.split(" / ")[-1].split(" ")[0]
				player2 = player2.split(" / ")[0].split(" ")[0] + " / " + player2.split(" / ")[-1].split(" ")[0]
			else:
				player1 = player1.split(" ")[-1]
				player2 = player2.split(" ")[-1]
		except:
			continue

		game = strip_accents(f"{player1} @ {player2}")

		if game in res:
			continue
		res[game] = {}

		for row in data:
			try:
				prop = row["type"]
			except:
				continue
			keys = row["key"].split(";")

			prefix = ""
			if keys[1] == "1":
				prefix = "set1_"

			if prop == "moneyline":
				prop = f"{prefix}ml"
			elif prop == "spread":
				prop = f"{prefix}spread"
				if gamesMatchup != row["matchupId"] and not prefix:
					prop = f"set_spread"
			elif prop == "total":
				prop = f"{prefix}total"
				if gamesMatchup != row["matchupId"] and not prefix:
					prop = f"total_sets"
			elif prop == "team_total":
				awayHome = "away" if row['side'] == "home" else "home"
				prop = f"{prefix}{awayHome}_total"


			prices = row["prices"]
			ou = f"{prices[0]['price']}/{prices[1]['price']}"
			if "points" in prices[0]:
				handicap = str(prices[0]["points"])
				if prop not in res[game]:
					res[game][prop] = {}
				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

	with open("static/tennis/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)


def writeMGM(date=None):

	if not date:
		date = str(datetime.now())[:10]

	res = {}

	tourneys = {
		"atp": {
			"id": 6
		},
		"wta": {
			"id": 7
		},
		"itf women": {
			"id": 8
		},
		"itf men": {
			"id": 9
		}
	}

	for tourney in tourneys:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&offerCategories=Gridable&fixtureCategories=Gridable,NonGridable,Other&sportIds=5&tournamentIds={tourneys[tourney]['id']}&competitionIds=&conferenceIds=&isPriceBoost=false&statisticsModes=None"
		outfile = f"tennisoutMGM"

		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		ids = []
		for row in data["fixtures"]:
			if str(datetime.strptime(row["startDate"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
				continue
			ids.append(row["id"])

		for mgmid in ids:
			url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
			time.sleep(0.3)
			os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			data = data["fixture"]
			game = strip_accents(data["name"]["value"].lower())

			p1, p2 = map(str, game.split(" - "))
			p1 = p1.split(" (")[0]
			p2 = p2.split(" (")[0]

			if "/" in game:
				p1 = p1.split("/")[0].split(" ")[-1]+" / "+p1.split("/")[-1].split(" ")[-1]
				p2 = p2.split("/")[0].split(" ")[-1]+" / "+p2.split("/")[-1].split(" ")[-1]
			else:
				p1 = p1.split(" ")[-1]
				p2 = p2.split(" ")[-1]
			game = f"{p1} @ {p2}"

			res[game] = {}
			for row in data["games"]:
				prop = row["name"]["value"].lower()

				if prop == "match winner":
					prop = "ml"
				elif prop == "set 1 winner":
					prop = "set1_ml"
				elif prop == "set 2 winner":
					prop = "set2_ml"
				elif prop == "set betting":
					prop = "set"
				elif prop == "total games - set 1":
					prop = "set1_total"
				elif prop == "total games - match":
					prop = "total"
				elif "at least 1" in prop:
					p = "away_1_set"
					if "player 2" in prop:
						p = "home_1_set"
					prop = p
				elif "set spread" in prop:
					prop = "set_spread"
				elif "player spread" in prop:
					prop = "spread"
				elif prop.startswith("how many sets will be played") and "best of three" in prop:
					prop = "total_sets"
				else:
					continue

				results = row['results']
				ou = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
				if "ml" in prop or prop in ["away_1_set", "home_1_set"]:
					res[game][prop] = ou
				elif prop == "total_sets":
					if prop not in res[game]:
						res[game][prop] = {}
					ou = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
					if results[0]['name']['value'] == '2 sets':
						ou = f"{results[1]['americanOdds']}/{results[0]['americanOdds']}"

					res[game][prop]["2.5"] = ou
				elif len(results) >= 2:
					if prop not in res[game]:
						res[game][prop] = {}

					skip = 1 if prop == "set" else 2
					for idx in range(0, len(results), skip):
						val = results[idx]["name"]["value"].lower()
						if "over" not in val and "under" not in val and prop not in ["set_spread", "spread", "set"]:
							continue
						else:
							val = val.split(" ")[-1]
						ou = str(results[idx]["americanOdds"])
						if prop == "set":
							res[game][prop][val] = ou
						else:
							ou = f"{results[idx]['americanOdds']}/{results[idx+1]['americanOdds']}"
							res[game][prop][str(float(val))] = ou

	with open("static/tennis/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBovada():
	url = "https://www.bovada.lv/sports/tennis/"

	ids = []
	for which in ["wta", "wta-doubles", "wta-125k", "challenger", "itf-men", "itf-women", "atp", "atp-doubles"]:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description/tennis/{which}?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
		outfile = f"tennisoutBV"

		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			ids.extend([r["link"] for r in data[0]["events"]])
		except:
			continue

	res = {}
	#print(ids)
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			comp = data[0]['events'][0]['competitors']
		except:
			continue
		player1 = comp[0]['name'].lower()
		player2 = comp[1]['name'].lower()
		if "/" in player1:
			player1 = f"{player1.split(' / ')[0].split(' ')[-2]} / {player1.split(' / ')[1].split(' ')[-2]}"
			player2 = f"{player2.split(' / ')[0].split(' ')[-2]} / {player2.split(' / ')[1].split(' ')[-2]}"
		else:
			player1 = player1.split(" ")[-1]
			player2 = player2.split(" ")[-1]
		game = f"{player1} @ {player2}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "game spreads/totals", "match props", "set props"]:
				for market in row["markets"]:
					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "total" or prop == "alternate total games":
						prop = "total"
					elif prop == "game spread" or prop == "alternate game spread":
						prop = "spread"
					elif prop == f"total games o/u - {player1}":
						prop = "away_total"
					elif prop == f"total games o/u - {player2}":
						prop = "home_total"
					elif prop == "any set to nil":
						prop = "6-0"
					elif prop == "number of sets played" or prop == "total sets":
						prop = "total_sets"
					elif prop == "set spread" or prop == "alternate set spread":
						prop = "set_spread"
					elif prop == "set betting":
						prop = "set"
					else:
						continue

					if market["period"]["description"].lower() == "1st set":
						prop = f"set1_{prop}"
					elif market["period"]["description"].lower() == "2nd set":
						prop = f"set2_{prop}"

					if market["period"]["main"] == False:
						continue

					if not len(market["outcomes"]):
						continue

					if "ml" in prop or prop == "6-0":
						res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
					elif prop == "total_sets":
						if prop not in res[game]:
							res[game][prop] = {}
						ou = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}"
						if market['outcomes'][0]['description'] == '2 sets':
							ou = f"{market['outcomes'][1]['price']['american']}/{market['outcomes'][0]['price']['american']}"
						res[game][prop]["2.5"] = ou.replace("EVEN", "100")
					elif prop == "set":
						if prop not in res[game]:
							res[game][prop] = {}
						for outcome in market["outcomes"]:
							score1 = outcome["description"].split(" ")[-3]
							score2 = outcome["description"].split(" ")[-1]
							score = f"{score1}-{score2}"
							if outcome["type"] == "A":
								score = f"{score2}-{score1}"
							res[game][prop][score] = outcome["price"]["american"]
					elif "spread" in prop or prop in ["total", "set1_total", "set2_total", "away_total", "home_total"]:
						if prop not in res[game]:
							res[game][prop] = {}

						outcomes = market["outcomes"]
						for idx in range(0, len(outcomes), 2):
							handicap = str(float(outcomes[idx]["price"]["handicap"]))

							res[game][prop][handicap] = f"{market['outcomes'][idx]['price']['american']}/{market['outcomes'][idx+1]['price']['american']}".replace("EVEN", "100")
					else:
						handicap = market["outcomes"][0]["price"]["handicap"]
						res[game][prop] = f"{handicap} {market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")

	with open("static/tennis/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi(date=None):
	data = {}
	outfile = f"tennisout.json"

	if not date:
		date = str(datetime.now())[:10]

	for gender in [None]:
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/tennis/all/all/all/matches.json?lang=en_US&market=US"
		os.system(f"curl -k \"{url}\" -o {outfile}")
		
		with open(outfile) as fh:
			j = json.load(fh)

		eventIds = {}

		if "events" not in j:
			continue

		for event in j["events"]:
			game = event["event"]["name"].lower()
			player1, player2 = map(str, game.split(f" {event['event']['nameDelimiter']} "))
			game = []
			for player in [player1, player2]:
				if "/" in player:
					p1,p2 = map(str, player.split("/"))
					game.append(f"{p1.strip().split(', ')[0].split(' ')[0]} / {p2.strip().split(', ')[0].split(' ')[0]}")
				else:
					p = f"{player.split(', ')[-1]} {player.split(', ')[0]}"
					p = p.split(" ")[-1]
					game.append(p)
			game = strip_accents(" @ ".join(game))
			if game in eventIds:
				continue

			if event["event"]["state"] == "STARTED":
				continue
			eventIds[game] = event["event"]["id"]
			data[game] = {}

		for game in eventIds:
			eventId = eventIds[game]
			teamIds = {}

			player1, player2 = map(str, game.split(" @ "))
			
			time.sleep(0.3)
			url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
			os.system(f"curl -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				j = json.load(fh)

			if "closed" not in j["betOffers"][0]:
				continue

			if str(datetime.strptime(j["betOffers"][0]["closed"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=5))[:10] != date:
				continue

			i = 0
			for betOffer in j["betOffers"]:
				label = betOffer["criterion"]["label"].lower()
				if label == "set betting":
					label = "set"
				elif label == "match odds":
					label = "ml"
				elif label == "set handicap":
					label = "set_spread"
				elif label == "set 1":
					label = "set1_ml"
				elif label == "set 2":
					label = "set2_ml"
				elif label == "game handicap":
					label = "spread"
				elif label == "game handicap - set 1":
					label = "set1_spread"
				elif label == "total games":
					label = "total"
				elif label == "total sets":
					label = "total_sets"
				else:
					continue

				ou = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				if "ml" in label:
					data[game][label] = ou
				elif label == "set":
					data[game][label] = {}
					for outcome in betOffer["outcomes"]:
						data[game][label][outcome['label']] = outcome["oddsAmerican"]
				else:
					if label not in data[game]:
						data[game][label] = {}
					line = betOffer["outcomes"][0]["line"] / 1000
					data[game][label][line] = ou

		with open(f"{prefix}static/tennis/kambi.json", "w") as fh:
			json.dump(data, fh, indent=4)

def writeFanduelManual():
	js = """

	let data = {};
	{

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
			return player;
		}

		let game = document.querySelector("h1").innerText.toLowerCase().replace(" odds", "");
		let awayFull = game.split(" v ")[0];
		let homeFull = game.split(" v ")[1];
		game = away+" @ "+home;
		if (!data[game]) {
			data[game] = {};
		}

		const arrows = document.querySelectorAll("div[data-test-id='ArrowAction']");

		for (const arrow of arrows) {
			let li = arrow;
			let idx = 0;
			while (li.nodeName != "LI") {
				li = li.parentElement;
				idx += 1;
				if (idx > 10) {
					break;
				}
			}

			if (idx > 10) {
				break;
			}

			let prop = "";
			let line = "";
			let player = "";
			let label = arrow.innerText.toLowerCase();
			if (label.indexOf("game lines") >= 0) {
				prop = "lines";
			} else if (label.indexOf("any time goal scorer") >= 0) {
				prop = "atgs";
			} else if (label.indexOf("player to record") >= 0) {
				line = (parseFloat(label.split(" ")[3].replace("+", "")) - 0.5).toString();
				if (label.indexOf("shots on goal") > 0) {
					prop = "sog";
				} else if (label.indexOf("+ points") > 0) {
					prop = "pts";
				} else if (label.indexOf("+ powerplay points") > 0) {
					prop = "pp_pts";
				} else if (label.indexOf("+ assists") > 0) {
					prop = "ast";
				}
			} else if (label.indexOf("alternate puck line") >= 0) {
				prop = "spread";
			} else if (label.indexOf("alternate total goals") >= 0) {
				prop = "total";
			} else if (label.indexOf("total saves") >= 0) {
				player = parsePlayer(label.split(" -")[0]);
				prop = "saves";
			} else if (label.indexOf("shots on goal") >= 0) {
				player = parsePlayer(label.split(" shots")[0]);
				prop = "sog";
			} else if (label.indexOf(awayFull+" total goals") >= 0) {
				prop = "away_total";
			} else if (label.indexOf(homeFull+" total goals") >= 0) {
				prop = "home_total";
			}

			if (!prop) {
				continue;
			}

			if (arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
				arrow.click();
			}
			let el = arrow.parentElement.parentElement.querySelector("div[aria-label='Show more']");
			if (el) {
				el.click();
			}

			if (prop != "lines" && !data[game][prop]) {
				data[game][prop] = {};
			}

			let skip = 1;
			if (["saves", "away_total", "home_total"].indexOf(prop) >= 0) {
				skip = 2;
			} else if (prop == "sog" && player) {
				skip = 2;
			}
			let btns = Array.from(li.querySelectorAll("div[role=button]"));
			btns.shift();

			if (prop == "lines") {
				data[game]["ml"] = btns[1].getAttribute("aria-label").split(", ")[1].split(" ")[0]+"/"+btns[4].getAttribute("aria-label").split(", ")[1].split(" ")[0];
				line = btns[0].getAttribute("aria-label").split(", ")[1];
				data[game]["spread"] = {};
				data[game]["spread"][line.replace("+", "")] = btns[0].getAttribute("aria-label").split(", ")[2].split(" ")[0] + "/" + btns[3].getAttribute("aria-label").split(", ")[2].split(" ")[0];
				line = btns[2].getAttribute("aria-label").split(", ")[2].split(" ")[1];
				data[game]["total"] = {};
				data[game]["total"][line] = btns[2].getAttribute("aria-label").split(", ")[3].split(" ")[0] + "/" + btns[5].getAttribute("aria-label").split(", ")[3].split(" ")[0];
			}

			for (let i = 0; i < btns.length; i += skip) {
				const btn = btns[i];
				if (btn.getAttribute("data-test-id")) {
					continue;
				}
				const ariaLabel = btn.getAttribute("aria-label");
				if (ariaLabel == "Show more" || ariaLabel == "Show less") {
					continue;
				}
				let odds = ariaLabel.split(", ")[1];
				if (odds.indexOf("unavailable") >= 0) {
					continue;
				}
				if (prop == "lines") {

				} else if (["spread"].indexOf(prop) >= 0) {
					let arr = ariaLabel.split(", ")[0].split(" ");
					line = arr[arr.length - 1];
					arr.pop();
					let team = convertTeam(arr.join(" "));

					let isAway = true;
					if (team == game.split(" @ ")[1]) {
						line = (parseFloat(line) * -1).toString();
						isAway = false;
					}

					line = line.replace("+", "");

					if (isAway) {
						data[game][prop][line] = odds;
					} else if (!data[game][prop][line]) {
						data[game][prop][line] = "-/"+odds;
					} else {
						data[game][prop][line] += "/"+odds;
					}
				} else if (["total"].indexOf(prop) >= 0) {
					let arr = ariaLabel.split(", ")[0].split(" ");
					line = arr[arr.length - 1];

					let isAway = true;
					if (arr[0] == "Under") {
						isAway = false;
					}

					line = line.replace("+", "");

					if (isAway) {
						data[game][prop][line] = odds;
					} else if (!data[game][prop][line]) {
						data[game][prop][line] = "-/"+odds;
					} else {
						data[game][prop][line] += "/"+odds;
					}
				} else if (skip == 2 && player) {
					// 2 sides
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop][player][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
				} else if (skip == 2) {
					line = ariaLabel.split(", ")[2].split(" ")[1];
					odds = ariaLabel.split(", ")[3].split(" ")[0];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop] = {};
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
				} else {
					player = parsePlayer(ariaLabel.split(",")[0]);
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}

					if (["atgs"].indexOf(prop) >= 0) {
						data[game][prop][player] = odds;
					} else {
						data[game][prop][player][line] = odds;
					}
				}
			}
		}

		console.log(data);
	}
"""

def writeFanduel():
	url = "https://mi.sportsbook.fanduel.com/navigation/us-open?tab=men%27s-matches"

	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/tennis/") >= 0) {
				const time = a.parentElement.querySelector("time");
				//if (time && time.innerText.split(" ").length < 3) {
				//if (time && time.innerText.split(" ")[0] === "FRI") {
				if (time && (time.innerText.split(" ")[0] === "TUE" || time.innerText.split(" ").length < 3)) {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/tennis/wta-angers-2023/er-andreeva-v-burel-32860949",
  "https://mi.sportsbook.fanduel.com/tennis/wta-montevideo-2023/mar-carle-v-j-riera-32861638",
  "https://mi.sportsbook.fanduel.com/tennis/itf-chile-futures/j-v-couto-loureiro-l-midon-v-d-fernandez-flores-32861980",
  "https://mi.sportsbook.fanduel.com/tennis/wta-angers-2023/el-cocciaretto-v-paquet-32861781",
  "https://mi.sportsbook.fanduel.com/tennis/wta-montevideo-2023/christie-lizarazo-v-lechemia-lee-32862184",
  "https://mi.sportsbook.fanduel.com/tennis/wta-montevideo-2023/d-parry-v-so-sierra-32861929",
  "https://mi.sportsbook.fanduel.com/tennis/wta-montevideo-2023/carle-riera-v-lohoff-perrin-32861857",
  "https://mi.sportsbook.fanduel.com/tennis/wta-montevideo-2023/robi-montgomery-v-in-albon-32859637",
  "https://mi.sportsbook.fanduel.com/tennis/wta-angers-2023/bucsa-niculescu-v-dzalamidze-moratelli-32863111"
]

	lines = {}
	#games = ["https://mi.sportsbook.fanduel.com/tennis/women's-us-open-2023/boulter-putintseva-v-wu-zhu-32592168"]
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		if game in lines:
			continue

		outfile = "tennisout"

		for tab in ["", "total-games-props", "alternatives"]:
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
				
			# find name
			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				if marketName == "moneyline":
					player1 = data["attachments"]["markets"][market]["runners"][0]["runnerName"].lower()
					player2 = data["attachments"]["markets"][market]["runners"][1]["runnerName"].lower()
					game = []
					for player in [player1, player2]:
						if "/" in player:
							p1, p2 = map(str, player.split(" / "))
							p = p1.split(" ")[-1]+" / "+p2.split(" ")[-1]
						else:
							p = player.split(" ")[-1]
						game.append(p)
					game = " @ ".join(game)
					if game not in lines:
						lines[game] = {}

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				runners = data["attachments"]["markets"][market]["runners"]

				if marketName in ["moneyline", "alternative game spread", "game spread", "alternative set spread", "6-0 set in match", "set betting", "to win 1st set", "set 2 winner"] or marketName.startswith("total match games") or "total sets" in marketName or "set 1 game handicap" in marketName or marketName.startswith("both") or marketName.startswith("player a") or marketName.startswith("player b") or "total games" in marketName:
					prop = ""
					if marketName == "moneyline":
						prop = "ml"
					elif marketName == "game spread" or marketName == "alternative game spread":
						prop = "spread"
					elif marketName == "alternative set spread":
						prop = "set_spread"
					elif "total match" in marketName:
						if "3-way" in marketName:
							continue
						prop = "total"
					elif "total sets" in marketName:
						prop = "total_sets"
					elif marketName == "to win 1st set":
						prop = "set1_ml"
					elif marketName == "set 2 winner":
						prop = "set2_ml"
					elif "set 1 game handicap" in marketName:
						prop = "set1_spread"
					elif "6-0" in marketName:
						prop = "6-0"
					elif "both" in marketName:
						prop = "both"
					elif marketName == "set betting":
						prop = "set"
					elif marketName.startswith("player a") or marketName.startswith("player b"):
						prop = "away" if marketName.split(" ")[1] == "a" else "home"
						if "at least one set" in marketName:
							prop += "_1_set"
						elif "total games" in marketName:
							prop += "_total"
						else:
							continue
					elif "total games" in marketName and "3 way" not in marketName:
						prop = "total"
						if marketName.startswith("set 1"):
							prop = "set1_total"
						elif marketName.startswith("set 2"):
							prop = "set2_total"
					else:
						continue

					if prop in ["ml", "set1_ml", "set2_ml", "6-0", "both", "away_1_set", "home_1_set"]:
						lines[game][prop] = ""

						for idx, runner in enumerate(runners):
							if idx == 1:
								lines[game][prop] += "/"
							try:
								lines[game][prop] += str(runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							except:
								print(url, game, prop)
								continue
					elif prop == "set":
						lines[game][prop] = {}

						for idx, runner in enumerate(runners):
							s = runner["runnerName"].lower().split(" ")[-1]
							if game.endswith(runner["runnerName"].lower().split(" ")[-2]):
								s1, s2 = map(str, s.split("-"))
								s = f"{s2}-{s1}"
							lines[game][prop][s] = str(runner["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					else:
						if prop not in lines[game]:
							lines[game][prop] = {}

						handicap = str(float(runners[0]["runnerName"].split(" ")[-1].replace("(", "").replace(")", "")))
						try:
							lines[game][prop][handicap] = str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
						except:
							print(url, game, prop)
							continue
	
	with open(f"{prefix}static/tennis/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr", sharp=False):

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

def writeDK(date):
	url = "https://sportsbook.draftkings.com/leagues/tennis/us-open-men"

	url = "https://sportsbook.draftkings.com/leagues/tennis/us-open-women"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 488,
		"sets": 534,
		"player props": 633
	}

	subCats = {
		488: [6364, 10818, 6365],
		534: [12169, 12170, 11127, 6367, 9535, 5369, 4816],
		633: [0]
	}

	lines = {}
	for gender in [73112, 73118, 209022, 209024, 44044, 211362, 17019, 17021, 103606, 92024, 59457, 210505, 210469, 96898, 144342, 199314, 105008, 198156, 160764, 71985, 205210]:
		for mainCat in mainCats:
			for subCat in subCats[mainCats[mainCat]]:
				time.sleep(0.3)
				url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/{gender}/categories/{mainCats[mainCat]}"
				if subCat:
					url += f"/subcategories/{subCat}"
				url += "?format=json"
				outfile = "outtennis1"
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
					game = event["name"].lower().replace(" vs ", " @ ")
					player1, player2 = map(str, game.split(" @ "))
					if "/" in player1:
						game = f"{player1.split(' / ')[0].split(' ')[-1]} / {player1.split(' / ')[1].split(' ')[-1]} @ {player2.split(' / ')[0].split(' ')[-1]} / {player2.split(' / ')[1].split(' ')[-1]}"
					else:
						player1 = player1.split(" ")[-1]
						player2 = player2.split(" ")[-1]
						game = f"{player1} @ {player2}"
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
								label = row["label"].lower().split(" [")[0]

								if label == "moneyline":
									label = "ml"
								elif label == "spread games":
									label = "spread"
								elif label == "set spread":
									label = "set_spread"
								elif "player total games" in label:
									if game.startswith(label.split(":")[0]):
										label = "away_total"
									else:
										label = "home_total"
								elif label.startswith("total games"):
									if "1st set" in label:
										label = "set1_total"
									elif "2nd set" in label:
										label = "set2_total"
									else:
										label = "total"
								elif label == "total sets":
									label = "total_sets"
								elif label == "1st set":
									label = "set1_ml"
								elif label == "2nd set":
									label = "set2_ml"
								elif label == "correct score":
									label = "set"

								if "6:0" in label:
									label = "6-0"

								if "ml" in label or label == "6-0":
									if len(row['outcomes']) == 0:
										continue
									lines[game][label] = f"{row['outcomes'][0]['oddsAmerican']}"
									if len(row['outcomes']) != 1:
										lines[game][label] += f"/{row['outcomes'][1]['oddsAmerican']}"
								elif label == "set":
									lines[game][label] = {}

									for outcome in row["outcomes"]:
										p = outcome["participant"].lower().split(" ")[-1]
										score = outcome['label'].replace(':', '-')
										if game.endswith(p):
											s1, s2 = map(str, score.split("-"))
											score = f"{s2}-{s1}"
										lines[game][label][score] = outcome['oddsAmerican']
								else:
									if label not in lines[game]:
										lines[game][label] = {}

									outcomes = row["outcomes"]
									for i in range(0, len(outcomes), 2):
										line = str(outcomes[i]["line"])
										try:
											lines[game][label][line] = f"{outcomes[i]['oddsAmerican']}/{outcomes[i+1]['oddsAmerican']}"
											if outcomes[i]['label'] == 'Under':
												lines[game][label][line] = f"{outcomes[i+1]['oddsAmerican']}/{outcomes[i]['oddsAmerican']}"

										except:
											continue
								

	with open("static/tennis/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writePointsbet(date=None):
	url = "https://api.mi.pointsbet.com/api/v2/sports/tennis/events/nextup"
	outfile = f"tennisoutPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	if not date:
		date = str(datetime.now())[:10]

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	#games = ["337209"]
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"tennisoutPB"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		try:
			with open(outfile) as fh:
				data = json.load(fh)
		except:
			continue

		startDt = datetime.strptime(data["startsAt"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if startDt.day != int(date[-2:]):
			continue

		game = ""
		for market in data["fixedOddsMarkets"]:
			if market["eventName"] == "Match Result":
				away = market["outcomes"][0]["name"].lower().replace("/", " / ")
				home = market["outcomes"][1]["name"].lower().replace("/", " / ")
				game = []
				for player in [away, home]:
					p = player
					if "/" in player:
						p1, p2 = map(str, player.split(" / "))
						p1 = p1.split(", ")[0].split(" ")[-1]
						p2 = p2.split(", ")[0].split(" ")[-1]
						p = " / ".join([p1, p2])
					else:
						p = p.split(" ")[-1]
					game.append(p)
				game = " @ ".join(game)
				break

		res[game] = {}

		for market in data["fixedOddsMarkets"]:
			prop = market["name"].lower().split(" (")[0]

			prefix = ""
			if "1st set" in prop:
				prefix = "set1_"
			elif "2nd set" in prop:
				prefix = "set2_"

			if "games handicap" in prop:
				prop = f"{prefix}spread"
			elif prop.startswith("sets handicap"):
				prop = f"{prefix}set_spread"
			elif prop == "set betting":
				prop = "set"
			elif prop.startswith("match result") or "set winner" in prop:
				prop = f"{prefix}ml"
			elif "total games" in prop:
				if "odd/even" in market["name"].lower() or "3 way" in prop:
					continue
				prop = f"{prefix}total"
			elif prop == "total sets":
				prop = "total_sets"
			elif prop.startswith(f"to win a set"):
				prop = f"away_1_set"
			elif prop == "6-0 set in match":
				prop = "6-0"
			else:
				continue

			if "ml" not in prop and prop != "6-0":
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			skip = 1 if prop in ["set1_spread", "set2_spread", "set"] else 2
			for i in range(0, len(outcomes), skip):
				if outcomes[i]["price"] == 1:
					continue
				over = convertAmericanOdds(outcomes[i]["price"])
				under = ""
				try:
					if skip == 2:
						under = convertAmericanOdds(outcomes[i+1]["price"])
				except:
					pass
				ou = f"{over}"

				if under:
					ou += f"/{under}"

				if "ml" in prop or prop in ["6-0"]:
					res[game][prop] = ou
				elif prop == "set":
					s = outcomes[i]["name"].split(" ")[-1]
					if game.endswith(outcomes[i]["name"].split(" ")[-2].lower()):
						s1, s2 = map(str, s.split("-"))
						s = f"{s2}-{s1}"
					res[game][prop][s] = str(over)
				elif prop in ["set1_spread", "set2_spread"]:
					points = str(float(outcomes[i]["name"].split(" ")[-1].replace("Even", "100")))
					if game.endswith(outcomes[i]["name"].split(" ")[-2].lower()):
						points = str(float(points) * -1)

					if points not in res[game][prop]:
						res[game][prop][points] = ou
					else:
						res[game][prop][points] += f"/{ou}"
				elif prop == "total_sets":
					res[game][prop]["2.5"] = f"{under}/{over}"
				elif prop == "away_1_set":
					res[game][prop] = str(over)
					res[game]["home_1_set"] = str(under)
				else:
					points = str(float(outcomes[i]["name"].split(" ")[-1].replace("Even", "100")))
					res[game][prop][points] = ou

	with open("static/tennis/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B13/C20904590/D7/E83/F4/"

	js = """
	
	const data = {};

	// All Main other than, Set: set1_spread, Games: away_total

	{
		for (const main of document.querySelectorAll(".gl-MarketGroupContainer")) {
			let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
			let prop = title.replace("moneyline", "ml");

			if (prop == "spread - games won") {
				prop = "spread";
			} else if (prop === "total games") {
				prop = "total";
			} else if (prop == "first set money line") {
				prop = "set1_ml";
			} else if (prop == "first set spread") {
				prop = "set1_spread";
			} else if (prop === "set betting") {
				prop = "set";
			} else if (prop == "total sets") {
				prop = "total_sets";
			} else if (prop == "1st set total games") {
				prop = "set1_total";
			} else if (prop == "player games won") {
				prop = "away_total";
			} else {
				prop = "ml";
			}

			if (["set", "total_sets", "set1_total", "away_total"].indexOf(prop) >= 0) {
				for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
					let game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" vs ", " @ ").replaceAll(".", "").replaceAll("/", " / ");
					let away = game.split(" @ ")[0];
					let home = game.split(" @ ")[1];
					if (away.indexOf(" / ") >= 0) {
						let away1 = away.split(" / ")[0];
						let away2 = away.split(" / ")[1];
						let home1 = home.split(" / ")[0];
						let home2 = home.split(" / ")[1];
						game = away1.split(" ")[away1.split(" ").length - 1]+" / "+away2.split(" ")[away2.split(" ").length - 1]+" @ "+home1.split(" ")[home1.split(" ").length - 1]+" / "+home2.split(" ")[home2.split(" ").length - 1];
					} else {
						away = away.split(" ")[away.split(" ").length - 1];
						home = home.split(" ")[home.split(" ").length - 1];
						game = away+" @ "+home;
					}

					if (data[game] === undefined) {
						data[game] = {};
					}

					if (div.classList.contains("src-FixtureSubGroup_Closed")) {
						div.click();
					}

					if (prop == "away_total") {
						let ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[0].innerText.replace("Over ", "");
						
						data[game]["away_total"] = {};
						data[game]["away_total"][ou] = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[0].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[1].innerText;

						ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[2].innerText.replace("Over ", "");
						data[game]["home_total"] = {};
						data[game]["home_total"][ou] = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[2].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[3].innerText;
					} else if (prop == "total_sets") {
						data[game][prop] = {};

						let ou = div.querySelectorAll(".gl-Participant_General")[1].querySelector(".gl-ParticipantBorderless_Odds").innerText+"/"+div.querySelectorAll(".gl-Participant_General")[0].querySelector(".gl-ParticipantBorderless_Odds").innerText;
						data[game][prop]["2.5"] = ou;
					} else {
						data[game][prop] = {};
						let arr = [];
						for (const set of div.querySelector(".gl-Market").querySelectorAll(".gl-Market_General-cn1")) {
							arr.push(set.innerText);
						}

						let idx = 0;
						for (const playerDiv of div.querySelectorAll(".gl-Participant_General")) {
							let set = arr[idx % arr.length];
							const odds = playerDiv.querySelector(".gl-ParticipantOddsOnly_Odds").innerText;

							if (prop == "set") {
								if (idx >= arr.length) {
									let s1 = set.split("-")[0];
									let s2 = set.split("-")[1];
									set = s2+"-"+s1;
								}
								
								data[game][prop][set] = odds;
							} else {
								if (idx < arr.length) {
									data[game][prop][set] = odds;
								} else {
									data[game][prop][set] += "/"+odds;
								}
							}
							idx += 1;
						}
					}
				}
			} else {
				let games = [];
				let idx = 0;
				for (div of main.querySelector(".gl-Market_General").children) {
					if (idx === 0 || div.classList.contains("Hidden")) {
						idx += 1;
						continue;
					}
					if (div.classList.contains("rcl-MarketHeaderLabel-isdate")) {
						//break;
						continue;
					}
					let away = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[0].innerText.toLowerCase().replaceAll(".", "");
					let home = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[1].innerText.toLowerCase().replaceAll(".", "");
					let game = (away+" @ "+home).replaceAll("/", " / ");
					if (away.indexOf("/") >= 0) {
						let away1 = away.split("/")[0];
						let away2 = away.split("/")[1];
						let home1 = home.split("/")[0];
						let home2 = home.split("/")[1];
						game = away1.split(" ")[away1.split(" ").length - 1]+" / "+away2.split(" ")[away2.split(" ").length - 1]+" @ "+home1.split(" ")[home1.split(" ").length - 1]+" / "+home2.split(" ")[home2.split(" ").length - 1];
					} else {
						away = away.split(" ")[away.split(" ").length - 1];
						home = home.split(" ")[home.split(" ").length - 1];
						game = away+" @ "+home;
					}
					games.push(game);

					if (!data[game]) {
						data[game] = {};
					}
				}

				idx = 0;
				let divs = main.querySelectorAll(".gl-Market_General")[1].querySelectorAll(".gl-Participant_General");
				for (let i = 0; i < divs.length; i += 1) {
					let game = games[idx];

					if (!game) {
						break;
					}

					if (prop.indexOf("ml") >= 0) {
						let odds = divs[i].querySelector(".sgl-ParticipantOddsOnly80_Odds").innerText;
						data[game][prop] = odds;
					} else {
						let line = divs[i].querySelector(".src-ParticipantCenteredStacked80_Handicap").innerText;
						let odds = divs[i].querySelector(".src-ParticipantCenteredStacked80_Odds").innerText;
						if (!data[game][prop]) {
							data[game][prop] = {};
						}
						line = parseFloat(line).toString();
						data[game][prop][line] = odds;
					}
					idx += 1;
				}

				idx = 0;
				divs = main.querySelectorAll(".gl-Market_General")[2].querySelectorAll(".gl-Participant_General");
				for (let i = 0; i < divs.length; i += 1) {
					let game = games[idx];

					if (!game) {
						break;
					}

					if (prop.indexOf("ml") >= 0) {
						let odds = divs[i].querySelector(".sgl-ParticipantOddsOnly80_Odds").innerText;
						data[game][prop] += "/"+odds;
					} else {
						let line = divs[i].querySelector(".src-ParticipantCenteredStacked80_Handicap").innerText;
						let odds = divs[i].querySelector(".src-ParticipantCenteredStacked80_Odds").innerText;
						if (prop.indexOf("spread") >= 0) {
							line = (parseFloat(line) * -1).toString();
						} else {
							line = parseFloat(line).toString();
						}

						data[game][prop][line] += "/"+odds;
					}
					idx += 1;
				}
			}
		}
		console.log(data);
	}

	"""
	pass

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None, singles=None, doubles=None):
	if not boost:
		boost = 1

	with open(f"{prefix}static/tennis/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/tennis/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/tennis/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/tennis/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/tennis/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/tennis/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/tennis/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/tennis/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/tennis/ev.json") as fh:
		evData = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		"bet365": bet365Lines,
		#"cz": czLines
	}

	evData = {}
	for game in fdLines:
		if teamArg and teamArg not in game:
			continue

		if singles and "/" in game:
			continue
		if doubles and "/" not in game:
			continue
		team1, team2 = map(str, game.split(" @ "))

		props = {}
		for book in lines:
			if game not in lines[book]:
				continue
			for prop in lines[book][game]:
				props[prop] = 1

		for prop in props:

			if propArg and prop != propArg:
				continue

			if not propArg and prop in ["set"]:
				continue

			handicaps = {}
			for book in lines:
				lineData = lines[book]
				if game in lineData and prop in lineData[game]:
					if type(lineData[game][prop]) is not dict:
						handicaps[("", "")] = ""
						break
					for handicap in lineData[game][prop]:
						player = playerHandicap = ""
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

					for book in lines:
						lineData = lines[book]
						if game in lineData and prop in lineData[game]:

							if type(lineData[game][prop]) is not dict:
								val = lineData[game][prop]
							else:
								if handicap not in lineData[game][prop]:
									continue
								val = lineData[game][prop][handicap]

								if player:
									if type(val) is dict:
										if playerHandicap not in val:
											continue
										val = lineData[game][prop][handicap][playerHandicap]
									else:
										if prop not in ["set"] and playerHandicap != val.split(" ")[0]:
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

					bet365 = ""
					try:
						bookIdx = books.index("bet365")
						bet365 = odds[bookIdx]
						odds.remove(bet365)
						books.remove("bet365")
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
					if bet365:
						books.append("bet365")
						l.append(bet365)

					avgOver = []
					avgUnder = []

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

					if ou == "-/-" or ou.startswith("-/"):
						continue

					if ou.endswith("/-"):
						ou = ou.split("/")[0]

					if not line:
						continue

					key = f"{game} {prop} {handicap} {'over' if i == 0 else 'under'}"
					if key in evData:
						continue
					if True:
						pass
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
							print(evData[key]["ev"], game, prop, handicap, int(line), ou, evBook, "\n\t", l)
						evData[key]["game"] = game
						evData[key]["player"] = player
						evData[key]["book"] = evBook
						evData[key]["books"] = books
						evData[key]["ou"] = ou
						evData[key]["under"] = i == 1
						evData[key]["odds"] = l
						evData[key]["line"] = line
						evData[key]["fullLine"] = maxOU
						evData[key]["handicap"] = handicap
						evData[key]["playerHandicap"] = playerHandicap
						evData[key]["prop"] = prop
						j = {b: o for o, b in zip(l, books)}
						j[evBook] = maxOU
						evData[key]["bookOdds"] = j

	with open(f"{prefix}static/tennis/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def sortEV():

	with open(f"{prefix}static/tennis/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for game in evData:
		d = evData[game]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], game, d["line"], d["book"], j, d))

	for row in sorted(data):
		print(row[:-1])

	output = "\t".join(["EV", "PN EV", "EV Book", "Game", "Prop", "O/U", "FD", "DK", "MGM", "BV", "PB", "PN", "Kambi", "Bet365"]) + "\n"
	for row in sorted(data, reverse=True):
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], row[-1].get("pn_ev", "-"), str(row[-1]["line"])+" "+row[-1]["book"].upper(), row[-1]["game"], row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "bv", "pb", "pn", "kambi", "bet365"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/tennis/props.csv", "w") as fh:
		fh.write(output)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--avg", action="store_true", help="AVG")
	parser.add_argument("--all", action="store_true", help="ALL AVGs")
	parser.add_argument("--fd", action="store_true", help="Fanduel")
	parser.add_argument("--dk", action="store_true", help="Fanduel")
	parser.add_argument("--pb", action="store_true", help="Pointsbet")
	parser.add_argument("--writeBV", action="store_true", help="Bovada")
	parser.add_argument("--bv", action="store_true", help="Bovada")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("--mgm", action="store_true", help="MGM")
	parser.add_argument("--pn", action="store_true", help="Pinnacle")
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
	parser.add_argument("--singles", action="store_true", help="Singles")
	parser.add_argument("--doubles", action="store_true", help="Doubles")
	parser.add_argument("--lineupsLoop", action="store_true", help="Lineups")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--player", help="Player")

	args = parser.parse_args()

	if args.fd:
		writeFanduel()

	if args.dk:
		writeDK(args.date)

	if args.kambi:
		writeKambi(args.date)

	if args.bv:
		writeBovada()

	if args.mgm:
		writeMGM(args.date)

	if args.pn:
		writePinnacle(args.date)

	if args.pb:
		writePointsbet(args.date)

	if args.update:
		writeFanduel()
		writeDK(args.date)
		writeBovada()
		writeKambi(args.date)
		writeMGM(args.date)
		writePointsbet(args.date)
		writePinnacle(args.date)

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, boost=args.boost, doubles=args.doubles, singles=args.singles)

	if args.print:
		sortEV()

	if args.prop:
		#writeEV(dinger=dinger, date=args.date, avg=True, allArg=args.all, gameArg=args.game, teamArg=args.team, prop=args.prop, under=args.under, nocz=args.nocz, nobr=args.nobr, no365=args.no365, boost=args.boost, bookArg=args.book)
		#sortEV()
		pass

	if False:
		with open(f"{prefix}static/tennis/bet365.json") as fh:
			bet365Lines = json.load(fh)

		res = {}
		for game in bet365Lines:
			res[game] = {}
			for prop in bet365Lines[game]:
				if type(bet365Lines[game][prop]) is str and " " in bet365Lines[game][prop]:
					handicap, odds = map(str, bet365Lines[game][prop].split(" "))
					res[game][prop] = {
						handicap: odds
					}
				else:
					res[game][prop] = bet365Lines[game][prop]

		with open(f"{prefix}static/tennis/bet365.json", "w") as fh:
			json.dump(res, fh, indent=4)

	if args.player:
		with open(f"{prefix}static/tennis/draftkings.json") as fh:
			dkLines = json.load(fh)

		with open(f"{prefix}static/tennis/bet365.json") as fh:
			bet365Lines = json.load(fh)

		with open(f"{prefix}static/tennis/fanduelLines.json") as fh:
			fdLines = json.load(fh)

		with open(f"{prefix}static/tennis/bovada.json") as fh:
			bvLines = json.load(fh)

		with open(f"{prefix}static/tennis/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"{prefix}static/tennis/pinnacle.json") as fh:
			pnLines = json.load(fh)

		with open(f"{prefix}static/tennis/pointsbet.json") as fh:
			pbLines = json.load(fh)

		with open(f"{prefix}static/tennis/mgm.json") as fh:
			mgmLines = json.load(fh)


		lines = {
			"mgm": mgmLines,
			"pb": pbLines,
			"pn": pnLines,
			"kambi": kambiLines,
			"bv": bvLines,
			"bet365": bet365Lines,
			"dk": dkLines
		}
		for game in fdLines:
			arr = []
			if len([p for p in fdLines[game]]) < 2:
				continue
			for book in lines:
				if game not in lines[book]:
					arr.append(book)
			print(game, arr)
		exit()

	
		player = args.player

		for game in fdLines:
			if player not in game:
				continue

			for prop in fdLines[game]:
				if args.prop and args.prop != prop:
					continue

				fd = fdLines[game][prop]

				handicap = type(fd) is dict
				dk = bet365 = kambi = bv = pn = mgm = ""

				try:
					dk = dkLines[game][prop]
				except:
					pass
				try:
					bet365 = bet365Lines[game][prop]
				except:
					pass
				try:
					kambi = kambiLines[game][prop]
				except:
					pass
				try:
					bv = bvLines[game][prop]
				except:
					pass
				try:
					pn = pnLines[game][prop]
				except:
					pass
				try:
					mgm = mgmLines[game][prop]
				except:
					pass

				print(f"{prop} fd='{fd}'\ndk='{dk}'\n365='{bet365}'\nkambi='{kambi}'\nbv='{bv}'\nmgm={mgm}\npn={pn}")