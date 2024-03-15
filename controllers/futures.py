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
	team = team.lower()
	t = team.split(" ")[0]
	if t == "was":
		t = "wsh"
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
	elif "white sox" in team:
		t = "chw"
	return t

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
		9916: "world_series", 9917: "league_winner", 5628: "division_winner", 10988: "team_wins", 10821: "make_playoffs", 5946: "mvp", 12562: "cy_young", 5982: "roty", 13302: "hr", 13319: "k",  14944: "sb", 15076: "rbi", 15078: "h", 15165: "30/30", 5884: "hr_leader", 5885: "rbi_leader", 5886: "h_leader", 5888: "r_leader", 5889: "sb_leader", 5892: "sv_leader", 15114: "double_leader", 15115: "triple_leader"
	}

	if False:
		mainCats = {
			"player_totals": 1279
		}

		subCats = {
			1279: [15165]
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
				if event["name"].lower() in ["world series 2024"]:
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
							if mainCat == "player_totals" or prop in ["team_wins", "make_playoffs"]:
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
									ou = outcome["oddsAmerican"]+"/"+outcomes[i+1]["oddsAmerican"]
									if "under" in outcome["label"].lower() or outcome["label"].lower() == "no":
										ou = outcomes[i+1]["oddsAmerican"]+"/"+outcome["oddsAmerican"]

									if prop in ["make_playoffs", "30/30"]:
										lines[prop][team] = ou
									else:
										lines[prop][team] = {
											line: ou
										}
								else:
									if prop in ["mvp", "cy_young", "roty"]:
										team = parsePlayer(outcome["participant"])
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
			if (li.innerText.indexOf("fewjio") >= 0) {
				break;
			}
			if (li.innerText.indexOf("Strikeouts") >= 0) {
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

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--dk", action="store_true", help="Fanduel")

	args = parser.parse_args()
	if args.dk:
		writeDK(args.date)