from flask import *
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

march_blueprint = Blueprint('march', __name__, template_folder='views')

@march_blueprint.route('/getMarch')
def getmarch_route():
	with open(f"{prefix}static/ncaab/kenpom.json") as fh:
		kenpom = json.load(fh)

	with open(f"{prefix}static/ncaab/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/ncaab/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/ncaab/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/ncaab/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/ncaab/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaab/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/ncaab/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/ncaab/fdMarch.json") as fh:
		fdLines = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines,
		"fd": fdLines
	}

	matchups = {}
	mls = {}
	for book in lines:
		for game in lines[book]:
			if book != "fd" and "ml" not in lines[book][game]:
				continue
			away, home = map(str, game.split(" @ "))
			if book == "fd":
				ml = lines[book][game]
			else:
				ml = lines[book][game]["ml"]

			if away not in mls:
				mls[away] = {}
			if home not in mls:
				mls[home] = {}

			mls[away][book] = ml
			mls[home][book] = ml.split("/")[1]+"/"+ml.split("/")[0]
			matchups[away] = game
			matchups[home] = game

	res = []
	for team in kenpom:
		matchup = matchups.get(team, "")
		j = {"team": team.title(), "matchup": matchup}
		for book in lines:
			j[book] = ""
			if team in mls and book in mls[team]:
				j[book] = mls[team][book]
		for stat in kenpom[team]:
			j[stat] = kenpom[team][stat]
		res.append(j)

	return jsonify(res)

@march_blueprint.route('/march')
def march_route():
	return render_template("march.html")

def writeKenpom():
	url = "https://kenpom.com/"
	outfile = "outKP"
	#os.system(f"curl {url} -o {outfile}")

	data = {}
	soup = BS(open(outfile, 'rb').read(), "lxml")
	for tr in soup.find("table", id="ratings-table").findAll("tr")[2:]:
		tds = tr.findAll("td")
		if not tds:
			continue
		team = tds[1].find("a").text.lower().replace(".", "").replace("'", "")
		if team.endswith(" st"):
			team += "ate"
		team = convertTeam(team)
		seed = 0
		if tds[1].find("span"):
			seed = int(tds[1].find("span").text)
		data[team] = {
			"kpRank": int(tds[0].text),
			"seed": seed,
			"record": tr.find("td", class_="wl").text,
			"adjEM": float(tds[4].text)
		}

		idx = 5
		for hdr in ["adjO", "adjD", "adjT", "luck", "sos", "oppO", "oppD", "nonConfSOS"]:
			data[team][hdr] = f"{tds[idx].text} ({tds[idx+1].text})"
			idx += 2

	with open("static/ncaab/kenpom.json", "w") as fh:
		json.dump(data, fh, indent=4)

def convertTeam(team):
	team = strip_accents(team.lower().split(" (")[0])
	team = team.replace("'", "").replace(".", "").replace("- ", "").replace("-", " ").replace("a and m", "a&m")
	if team.endswith(" u"):
		team = team[:-2]
	trans = {
		"american university": "american",
		"alcorn": "alcorn state",
		"alabama am": "alabama a&m",
		"appalachian st": "appalachian state",
		"arkansas little rock": "little rock",
		"army west point": "army",
		"cal": "california",
		"cal baptist": "california baptist",
		"california san diego": "uc san diego",
		"coll charleston": "charleston",
		"college of charleston": "charleston",
		"st johns": "saint johns",
		"saint bonaventure": "st bonaventure",
		"ohio st": "ohio state",
		"unc greensboro": "nc greensboro",
		"albany ny": "albany",
		"southeastern louisiana": "se louisiana",
		"long island": "liu",
		"long island university": "liu",
		"siu edwardsville": "siue",
		"boston": "boston university",
		"central florida": "cfu",
		"cal irvine": "uc irvine",
		"cal poly slo": "cal poly", 
		"cal state fullerton": "csu fullerton",
		"cs fullerton": "csu fullerton",
		"cal state bakersfield": "csu bakersfield",
		"bakersfield": "csu bakersfield",
		"cs bakersfield": "csu bakersfield",
		"cs northridge": "csu northridge",
		"csun": "csu northridge",
		"cal state northridge": "csu northridge",
		"cal riverside": "uc riverside",
		"detroit mercy": "detroit",
		"detroitu": "detroit",
		"eastern carolina": "east carolina",
		"fau": "florida atlantic",
		"fiu": "florida international",
		"grambling": "grambling state",
		"illinois chicago": "uic",
		"kansas city": "umkc",
		"kennesaw st": "kennesaw state",
		"purdue fort wayne": "ipfw",
		"lamar cardinals": "lamar",
		"louisiana lafayette": "louisiana",
		"ul lafayette": "louisiana",
		"louisiana monroe": "ul monroe",
		"miami ohio": "miami oh",
		"middle tennessee state": "middle tennessee",
		"middle tenn state": "middle tennessee",
		"mississippi valley": "mississippi valley state",
		"mississippi valley st": "mississippi valley state",
		"mcneese state cowboys": "mcneese",
		"mcneese state": "mcneese",
		"miami fl": "miami",
		"miami florida": "miami",
		"mt st marys": "mount st marys",
		"mount saint marys": "mount st marys",
		"n carolina a and t": "north carolina a&t",
		"nc wilmington": "unc wilmington",
		"north carolina state": "nc state",
		"north carolina central": "nc central",
		"north carolina asheville": "unc asheville",
		"nc asheville": "unc asheville",
		"northwestern st": "northwestern state",
		"penn": "pennsylvania",
		"upenn": "pennsylvania",
		"prairie view": "prairie view a&m",
		"queens nc": "queens university",
		"queens charlotte": "queens university",
		"queens": "queens university",
		"sam houston": "sam houston state",
		"sam houston st": "sam houston state",
		"san jose st": "san jose",
		"san jose state": "san jose",
		"saint marys ca": "saint marys",
		"so illinois": "southern illinois",
		"southern mississippi": "southern miss",
		"st francis": "st francis pa",
		"saint francis pa": "st francis pa",
		"saint josephs": "st josephs",
		"st peters": "saint peters",
		"southern methodist": "smu",
		"st thomas mn": "st thomas",
		"saint thomas mn": "st thomas",
		"st thomas minnesota": "st thomas",
		"stephen f austin": "sfa",
		"stephen austin": "sfa",
		"texas san antonio": "utsa",
		"texas a&m corpus christi": "texas a&m cc",
		"a&m corpus christi": "texas a&m cc",
		"t a&m corpus christi": "texas a&m cc",
		"texas a&m corpus": "texas a&m cc",
		"tennessee martin": "ut martin",
		"uconn": "connecticut",
		"uiw": "incarnate word",
		"ulm": "ul monroe",
		"uncw": "unc wilmington",
		"uncg": "nc greensboro",
		"md baltimore county": "umbc",
		"md baltimore": "umbc",
		"utrgv": "ut rio grande valley",
		"wisc green bay": "green bay",
		"wisconsin green bay": "green bay",
		"wisconsin milwaukee": "milwaukee",
		"wisc milwaukee": "milwaukee"
	}
	return trans.get(team, team)

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

	with open(f"{prefix}static/ncaab/draftkings.json") as fh:
		fdLines = json.load(fh)

	teamGame = {}
	for game in fdLines:
		away, home = map(str, game.split(" @ "))
		if away not in teamGame:
			teamGame[away] = game
		if home not in teamGame:
			teamGame[home] = game

	props = ["56_first_touchdown_scorer", "62_anytime_touchdown_scorer", "60_longest_completion", "59_longest_reception", "58_longest_rush", "30_passing_attempts", "10_pass_completions", "11_passing_tds", "9_passing_yards", "17_receiving_tds", "16_receiving_yards", "15_receptions", "18_rushing_attempts", "13_rushing_tds", "12_rushing_yards", "70_tackles_assists"]
	#props = ["70_tackles_assists"]

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
		path = f"nbaout.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/1/props/core_bet_type_{actionProp}?bookIds=69,1541,283,348,351,355&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		prop = ""
		if "touchdown" in actionProp:
			prop = "ftd"
			if "anytime" in actionProp:
				prop = "attd"
		elif "tackles_assist" in actionProp:
			prop = "tackles+ast"
		else:
			prop = "_".join(actionProp.split("_")[1:]).replace("rushing", "rush").replace("passing", "pass").replace("receiving", "rec").replace("yards", "yd").replace("attempts", "att").replace("completion", "cmp").replace("reception", "rec")
			if prop == "longest_cmp":
				prop = "longest_pass"

		if prop not in ["longest_pass"] and prop.endswith("s"):
			prop = prop[:-1]

		with open(path) as fh:
			j = json.load(fh)

		if "markets" not in j or not j["markets"]:
			continue
		market = j["markets"][0]

		if "teams" not in market:
			continue

		for option in market["rules"]["options"]:
			optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

		teamIds = {}
		for row in market["teams"]:
			team = row["abbr"].lower()
			if team == "la":
				team = "lar"
			teamIds[row["id"]] = team

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
				try:
					player = playerIds[oddData["player_id"]]
					team = teamIds[oddData["team_id"]]
					game = teamGame[team]
				except:
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

	with open(f"{prefix}static/ncaab/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def writeCZ(date, march):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/basketball/events/schedule/?competitionIds=d246a1dd-72bf-45d1-bc86-efc519fa8e90"
	outfile = "outCZ"
	#os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")
	os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.9.0' -H 'x-aws-waf-token: d54677cb-c7bf-4b5c-add6-0de10122dfcd:EQoAfmx+iUwAAAAA:uVSQjRFAgmnBJtUQy+W3HaDJApw3BiyFT+Ye9AkEaIc1sI4h0td2RugiLK6UVqB9Sh3JcvjD8P94BCiuxh7iONcqWtAJ9dkbzAJ42JL4ZuWdIGZjqvPu0dttlqflf0+r+YxBxHHK98AGaJqtnqRAsytkmeLa3BNvemeWO38tasM7GZMSjM9IHEK78zk6ydrfN0nCW7Kb76HAGqb5419ROLXCJU3IGJHw/8euZjxKipOK9AKTs0PY9OM4XHrQ8gXN1FIKY01iFeqEXQ==' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"]:
		if not event["active"]:
			continue
		d = datetime.strptime(event["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=5)
		if not march and str(d)[:10] != date:
			continue
		if date == str(datetime.now())[:10] and d < datetime.now():
			continue
		games.append(event["id"])


	#games = ["9835ed03-b6bc-49c3-b274-5e6a32b56612"]
	res = {}
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/events/{gameId}"
		time.sleep(0.2)
		#os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")
		os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.9.0' -H 'x-aws-waf-token: d54677cb-c7bf-4b5c-add6-0de10122dfcd:EQoAfmx+iUwAAAAA:uVSQjRFAgmnBJtUQy+W3HaDJApw3BiyFT+Ye9AkEaIc1sI4h0td2RugiLK6UVqB9Sh3JcvjD8P94BCiuxh7iONcqWtAJ9dkbzAJ42JL4ZuWdIGZjqvPu0dttlqflf0+r+YxBxHHK98AGaJqtnqRAsytkmeLa3BNvemeWO38tasM7GZMSjM9IHEK78zk6ydrfN0nCW7Kb76HAGqb5419ROLXCJU3IGJHw/8euZjxKipOK9AKTs0PY9OM4XHrQ8gXN1FIKY01iFeqEXQ==' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		#game = data["name"].lower().replace("|at|", "@").replace("|", "")
		game = ""
		for market in data["markets"]:
			if market["selections"] and "teamData" in market["selections"][0] and "teamData" in market["selections"][1]:
				away = convertTeam(market["selections"][0]["teamData"]["teamCity"])
				home = convertTeam(market["selections"][1]["teamData"]["teamCity"])
				game = f"{away} @ {home}"
				res[game] = {}
				break

		if not game:
			continue

		for market in data["markets"]:
			if not market["display"]:
				continue
			if "name" not in market:
				continue
			prop = market["name"].lower().replace("|", "").split(" (")[0]
			name = market["templateName"].lower().replace("|", "")

			prefix = player = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "1st quarter" in prop:
				prefix = "1q_"
			elif "2nd half" in prop:
				prefix = "2h_"

			if "money line" in prop:
				prop = "ml"
			elif ("total points" in prop or "alternative points" in prop) and "player" not in name:
				if "away points" in name:
					prop = "away_total"
				elif "home points" in name:
					prop = "home_total"
				else:
					prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif "player total" in name:
				p = prop.split(" total")[0]
				player = parsePlayer(p)
				prop = prop.split(p+" ")[-1].replace("total ", "").replace("points + assists + rebounds", "pts+reb+ast").replace("points + assists", "pts+ast").replace("points + rebounds", "pts+reb").replace("rebounds + assists", "reb+ast").replace("blocks + steals", "blk+stl").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("steals", "stl").replace("blocks", "blk").replace("3pt field goals", "3ptm")
			else:
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			selections = market["selections"]
			skip = 2
			for i in range(0, len(selections), skip):
				ou = str(selections[i]["price"]["a"])
				if skip == 2:
					ou += f"/{selections[i+1]['price']['a']}"
					if selections[i]["name"].lower().replace("|", "") == "under":
						ou = f"{selections[i+1]['price']['a']}/{selections[i]['price']['a']}"

				if "ml" in prop:
					res[game][prop] = ou
				elif "spread" in prop:
					line = str(float(market["line"]) * -1)
					res[game][prop][line] = ou
				elif "total" in prop:
					try:
						line = str(float(market["line"]))
						res[game][prop][line] = ou
					except:
						continue
				else:
					line = str(float(market["line"]))
					res[game][prop][player] = {
						line: ou
					}

			if prop in ["spread", "total"]:
				try:
					linePrices = market["movingLines"]["linePrices"]
				except:
					continue
				for prices in linePrices:
					selections = prices["selections"]
					if prop == "spread":
						line = str(float(prices["line"]) * -1)
						ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"
					else:
						line = str(float(prices["line"]))
						ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
						if selections[0]["selectionType"] == "under":
							ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"

					
					res[game][prop][line] = ou


	with open("static/ncaab/caesars.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writePointsbet(date):
	if not date:
		date = str(datetime.now())[:10]

	url = "https://api.mi.pointsbet.com/api/v2/competitions/4/events/featured?includeLive=false&page=1"
	outfile = f"nbaoutPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	#games = ["340247"]
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"nbaoutPB"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		startDt = datetime.strptime(data["startsAt"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=5)
		if startDt.day != int(date[-2:]):
			continue
		elif startDt < datetime.now():
			continue

		game = data["name"].lower()
		fullAway, fullHome = map(str, game.split(" @ "))
		game = f"{convertTeam(fullAway)} @ {convertTeam(fullHome)}"
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

			prefix = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "2nd half" in prop:
				prefix = "2h_"
			elif "1st quarter" in prop:
				prefix = "1q_"
			elif "2nd quarter" in prop:
				prefix = "2q_"
			elif "3rd quarter" in prop:
				prefix = "3q_"
			elif "4th quarter" in prop:
				prefix = "4q_"

			if prop.startswith("point spread") or prop == "pick your own line":
				if "3 way" in prop:
					continue
				prop = f"{prefix}spread"
			elif prop.startswith("moneyline"):
				if "3 way" in prop:
					continue
				prop = f"{prefix}ml"
			elif prop.startswith("total") or prop == "alternate totals":
				if " and " in prop or "bands" in prop:
					continue
				prop = "total"
				prop = f"{prefix}total"
			elif prop.startswith(f"{fullAway} total"):
				prop = f"{prefix}away_total"
			elif prop.startswith(f"{fullHome} total"):
				prop = f"{prefix}home_total"
			elif prop.startswith("player points over/under"):
				prop = "pts"
			elif prop.startswith("player rebounds over/under"):
				prop = "reb"
			elif prop.startswith("player 3-pointers made"):
				prop = "3ptm"
			elif prop.startswith("player assists over/under"):
				prop = "ast"
			elif "over/under" in prop and "+" in prop:
				prop = prop.split(" over/under")[0].split("player ")[-1].replace(" + ", "+").replace("asts", "ast").replace("rebs", "reb").replace("assists", "ast").replace("points", "pts").replace("rebounds", "reb")
			else:
				continue

			if "ml" not in prop:
				if prop not in res[game]:
					res[game][prop] = {}

			outcomes = market["outcomes"]
			if market["hiddenOutcomes"] and prop in ["total"]:
				outcomes.extend(market["hiddenOutcomes"])
			skip = 2
			for i in range(0, len(outcomes), skip):
				points = str(outcomes[i]["points"])
				if outcomes[i]["price"] == 1:
					continue
				over = str(convertAmericanOdds(outcomes[i]["price"]))
				under = ""
				try:
					under = convertAmericanOdds(outcomes[i+1]["price"])
					ou = f"{over}/{under}"
					if ("spread" in prop or "ml" in prop) and outcomes[i]["side"] == "Home":
						ou = f"{under}/{over}"
				except:
					pass

				if "ml" in prop:
					res[game][prop] = ou
				elif prop in ["pts", "reb", "3ptm", "ast"] or "+" in prop:
					player = parsePlayer(outcomes[i]["name"].lower().split(" over")[0])
					res[game][prop][player] = {
						outcomes[i]['name'].split(' ')[-1]: ou
					}
				else:
					if "spread" in prop and outcomes[i]["side"] == "Home":
						points = str(outcomes[i+1]["points"])
						ou = f"{under}/{over}"
					res[game][prop][points] = ou

	with open("static/ncaab/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "nbaoutPN"
	game = games[gameId]

	#print(game)
	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 410040c0-e1fcf090-53cb2c91-be5a5dbd" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" --connect-timeout 60 -o nbaoutPN'

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
			prop = row["units"].lower().replace("points", "pts").replace("assists", "ast").replace("assist", "ast").replace("rebounds", "reb").replace("threepointfieldgoals", "3ptm").replace("ptsrebast", "pts+reb+ast")

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

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 410040c0-e1fcf090-53cb2c91-be5a5dbd" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" --connect-timeout 60 -o nbaoutPN'

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
		try:
			prop = row["type"]
			keys = row["key"].split(";")
		except:
			continue

		prefix = ""
		if keys[1] == "1":
			prefix = "1h_"
		elif keys[1] == "4":
			prefix = "2q_"
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
				res[game][prop][player] = {
					handicap: ou
				}
			else:
				res[game][prop][player] = ou
		else:
			ou = f"{prices[0]['price']}/{prices[1]['price']}"
			if prices[0]["designation"] in ["home", "under"]:
				ou = f"{prices[1]['price']}/{prices[0]['price']}"
				switched = 1

			if "points" in prices[0]:
				handicap = str(prices[switched]["points"])
				if prop not in res[game]:
					res[game][prop] = {}

				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

def writePinnacle(date, debug, march):

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/basketball/ncaa/matchups/#period:0"

	url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/493/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 410040c0-e1fcf090-53cb2c91-be5a5dbd" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -o nbaoutPN'

	os.system(url)
	outfile = f"nbaoutPN"
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	for row in data:
		d = datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=5)
		if str(d)[:10] != date and not march:
			continue
		if date == str(datetime.now())[:10] and d < datetime.now():
			continue
		if row["type"] == "matchup" and not row["parent"]:
			player1 = convertTeam(row["participants"][0]["name"].lower())
			player2 = convertTeam(row["participants"][1]["name"].lower())
			games[str(row["id"])] = f"{player2} @ {player1}"

	res = {}
	#games = {'1580434847': 'phx @ gs'}
	retry = []
	for gameId in games:
		parsePinnacle(res, games, gameId, retry, debug)

	for gameId in retry:
		parsePinnacle(res, games, gameId, retry, debug)

	with open("static/ncaab/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBV(date, march):

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.bovada.lv/sports/basketball/college-basketball"

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/basketball/college-basketball?marketFilterId=def&preMatchOnly=false&eventsLimit=5000&lang=en"
	outfile = f"nbaoutBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	ids = []
	for row in data[0]["events"]:
		if not march and str(datetime.fromtimestamp(row["startTime"] / 1000))[:10] != date:
			continue
		ids.append(row["link"])

	#ids = ["/football/ncaab/kansas-city-chiefs-jacksonville-jaguars-202309171300"]
	res = {}
	#print(ids)
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl \"{url}\" --connect-timeout 60 -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			comp = data[0]['events'][0]['competitors']
			game = data[0]['events'][0]['description'].lower()
		except:
			continue
		fullAway, fullHome = game.split(" @ ")
		game = f"{convertTeam(fullAway)} @ {convertTeam(fullHome)}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "player points", "player rebounds", "assists & threes", "blocks & steals", "player turnovers", "player combos"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["description"].lower() == "first half":
						prefix = "1h_"
					elif market["period"]["description"].lower() == "second half":
						prefix = "2h_"
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
					elif prop.startswith("total points -"):
						prop = "pts"
					elif prop.startswith("total assists -"):
						prop = "ast"
					elif prop.startswith("total blocks -"):
						prop = "blk"
					elif prop.startswith("total steals -"):
						prop = "stl"
					elif prop.startswith("total turnovers -"):
						prop = "to"
					elif prop.startswith("total made 3"):
						prop = "3ptm"
					elif prop.startswith("total points, rebounds"):
						prop = "pts+reb+ast"
					elif prop.startswith("total points and rebounds"):
						prop = "pts+reb"
					elif prop.startswith("total points and assists"):
						prop = "pts+ast"
					elif prop.startswith("total rebounds and assists"):
						prop = "reb+ast"
					else:
						continue

					prop = f"{prefix}{prop}"

					if not len(market["outcomes"]):
						continue

					if "ml" not in prop and prop not in res[game]:
						res[game][prop] = {}

					if "ml" in prop:
						try:
							res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
						except:
							continue
					elif "total" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							except:
								continue
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif "spread" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							except:
								continue
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					else:
						try:
							handicap = market["outcomes"][0]["price"]["handicap"]
							player = parsePlayer(market["description"].split(" - ")[-1].split(" (")[0])
							ou = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}"
							if market["outcomes"][0]["description"] == "Under":
								ou = f"{market['outcomes'][1]['price']['american']}/{market['outcomes'][0]['price']['american']}"
							res[game][prop][player] = {
								handicap: ou.replace("EVEN", "100")
							}
						except:
							continue


	with open("static/ncaab/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM(date, march):

	if not date:
		date = str(datetime.now())[:10]

	res = {}

	url = "https://sports.mi.betmgm.com/en/sports/basketball-7/betting/usa-9/college-264"

	url = f"https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=7&regionId=9&competitionId=264&compoundCompetitionId=1:264&widgetId=/mobilesports-v1.0/layout/layout_us/modules/competition/defaultcontainereventsfutures-redesign&shouldIncludePayload=true"
	outfile = f"nbaoutMGM"

	time.sleep(0.3)
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	rows = data["widgets"][0]["payload"]["items"][0]["activeChildren"][0]["payload"]["fixtures"]
	ids = []
	for row in rows:
		if row["stage"].lower() == "live":
			continue
		if "2023/2024" in row["name"]["value"] or "2023/24" in row["name"]["value"]:
			continue
		d = datetime.strptime(row["startDate"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if not march and str(d)[:10] != date:
			continue
		if date == str(datetime.now())[:10] and d < datetime.now():
			continue
		ids.append(row["id"])

	#ids = ["14627784"]
	for mgmid in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/109.0' \"{url}\" --connect-timeout 60 -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		if "fixture" not in data:
			continue
		data = data["fixture"]

		if " at " not in data["name"]["value"]:
			continue
		game = strip_accents(data["name"]["value"].lower()).replace(" at ", " @ ")
		fullTeam1, fullTeam2 = game.split(" @ ")
		game = f"{convertTeam(fullTeam1)} @ {convertTeam(fullTeam2)}"

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
			elif "totals" in prop:
				prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif "double-double in the game" in prop:
				player = parsePlayer(prop.split(" (")[0][5:])
				prop = "double-double"
			elif " over/under " in prop:
				player = parsePlayer(prop.split(" (")[0])
				prop = prop.split("over/under ")[-1].replace(" and ", "+").replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("three-pointers made", "3ptm").replace(", ", "+")
			elif "): " in prop:
				player = parsePlayer(prop.split(" (")[0])
				prop = prop.split(": ")[-1].replace(" and ", "+").replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("three-pointers made", "3ptm").replace(", ", "+")
			elif prop.startswith("how many "):
				if prop.startswith("how many points will be scored in the game") or "extra points" in prop:
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
					player = parsePlayer(prop.split(" (")[0].split(" will ")[-1])
					p = prop.split(" will ")[0].split(" total ")[-1].split(" many ")[-1]
					p = p.replace(" and ", "+").replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("three-pointers", "3ptm").replace(", ", "+")
					if p == "pts+reb s":
						p = "pts+reb"
					prop = p
			else:
				continue

			if prop == "three-pointers" or prop == "three-pts made":
				prop = "3ptm"

			prop = prefix+prop

			results = row['results']
			ou = f"{results[0]['americanOdds']}"
			if len(results) < 2:
				continue
			if "americanOdds" in results[1]:
				ou += f"/{results[1]['americanOdds']}"
			if "ml" in prop:
				res[game][prop] = ou
			elif len(results) >= 2:
				skip = 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop and prop not in ["double-double"]:
						continue
					else:
						val = val.split(" ")[-1]
					
					ou = f"{results[idx]['americanOdds']}"
					if "americanOdds" in results[idx+1]:
						ou += f"/{results[idx+1]['americanOdds']}"

					if prop in ["double-double"]:
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = ou
					elif player:
						player = parsePlayer(player)
						if prop not in res[game]:
							res[game][prop] = {}
						res[game][prop][player] = {
							val: ou
						}
					else:
						if prop not in res[game]:
							res[game][prop] = {}
						try:
							v = str(float(val))
							res[game][prop][v] = ou
						except:
							pass

	with open("static/ncaab/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi(date, march):

	if not date:
		date = str(datetime.now())[:10]

	data = {}
	outfile = f"outnba.json"
	url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/basketball/ncaab"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/basketball/ncaab/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl \"{url}\" --connect-timeout 60 -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	fullTeam = {}
	eventIds = {}
	swapped = {}
	for event in j["events"]:
		game = event["event"]["name"].lower()
		away, home = event["event"]["awayName"].lower(), event["event"]["homeName"].lower()
		games = []
		for team in [away, home]:
			t = convertTeam(team)
			fullTeam[t] = team
			games.append(t)
		game = " @ ".join(games)
		#print(game, away, home)
		if game in eventIds:
			continue
			#pass
		#swapped[game] = swap
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	#eventIds = {'arizona @ utah': 1020207806}
	#data['arizona @ utah'] = {}

	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl \"{url}\" --connect-timeout 60 -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		if not j["betOffers"] or "closed" not in j["betOffers"][0]:
			continue

		d = datetime.strptime(j["betOffers"][0]["closed"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=5)
		if not march and str(d)[:10] != date:
			continue
		if date == str(datetime.now())[:10] and d < datetime.now():
			continue

		awayFull, homeFull = j["events"][0]["awayName"].lower(), j["events"][0]["homeName"].lower()

		i = 0
		for betOffer in j["betOffers"]:
			playerProp = False
			label = betOffer["criterion"]["label"].lower()

			prefix = ""
			if "1st half" in label:
				prefix = "1h_"
			elif "2nd half" in label:
				prefix = "2h_"
			elif "quarter 1" in label:
				prefix = "1q_"
			elif "quarter 2" in label:
				prefix = "2q_"
			elif "quarter 3" in label:
				prefix = "3q_"
			elif "quarter 4" in label:
				prefix = "4q_"

			if label.split(" -")[0] == "total points":
				label = "total"
			elif label.split(" -")[0] == "handicap":
				label = "spread"
			elif "total points by" in label:
				team = convertTeam(label.split(" by ")[-1].split(" - ")[0])
				if team.startswith(awayFull):
					label = "away_total"
				else:
					label = "home_total"
			elif label == "including overtime":
				label = "ml"
			elif "double-double" in label:
				label = "double-double"
				playerProp = True
			elif label.endswith("by the player - including overtime"):
				playerProp = True
				label = label.replace(" - including overtime", "").split(" by the player")[0]
				label = label.replace("points scored", "pts").replace("points, rebounds & assists", "pts+reb+ast").replace("3-point field goals made", "3ptm").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk")

				if "&" in label:
					continue
			else:
				continue

			label = f"{prefix}{label}"

			if "oddsAmerican" not in betOffer["outcomes"][0]:
				continue

			try:
				ou = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
				#if swapped[game]:
				#	ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			except:
				ou = betOffer["outcomes"][0]["oddsAmerican"]
			player = ""
			if playerProp:
				player = parsePlayer(betOffer["outcomes"][0]["participant"])
				try:
					last, first = map(str, player.split(", "))
					player = f"{first} {last}"
				except:
					pass
			if "ml" in label:
				data[game][label] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
				t = betOffer["outcomes"][0].get("participant", betOffer["outcomes"][0]["label"])
				if t.lower().startswith(awayFull):
				 	data[game][label] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
			else:
				if label not in data[game]:
					data[game][label] = {}
				if not playerProp:
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer["outcomes"][0]["label"] == "Under" or betOffer["outcomes"][0]["label"].lower().startswith(homeFull):
						line = str(betOffer["outcomes"][1]["line"] / 1000)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					data[game][label][line] = ou
				elif label == "double-double":
					data[game][label][player] = ou
				else:
					if "line" not in betOffer["outcomes"][0]:
						line = float(betOffer["outcomes"][0]["label"].split(" ")[-1])
						if betOffer["outcomes"][0]["label"].split(" ")[0] == "Under":
							line = float(betOffer["outcomes"][1]["label"].split(" ")[-1])
							ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					else:
						line = betOffer["outcomes"][0]["line"] / 1000
						if betOffer["outcomes"][0]["label"] == "Under":
							line = betOffer["outcomes"][1]["line"] / 1000
							ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
					if player not in data[game][label]:
						data[game][label][player] = {}
					data[game][label][player][line] = ou


	with open(f"static/ncaab/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "").replace(" iv", "").replace("\t", "")
	if player == "nicholas boyd":
		player = "nick boyd"
	elif player == "alvaro cardenas torre":
		player = "alvaro cardenas"
	return player

def writeFanduelManual():
	js = """

	let data = {};
	{

		function convertTeam(team) {
			team = team.toLowerCase().replaceAll("'", "").replaceAll(".", "").replace("-", " ");
			if (team == "st johns") {
				return "saint johns";
			} else if (team == "nebraska cornhuskers") {
				return "nebraska";
			} else if (team == "siu edwardsville") {
				return "siue";
			} else if (team == "louisiana monroe") {
				return "ul monroe";
			} else if (team == "nicholls") {
				return "nicholls state";
			} else if (team == "san jose st") {
				return "san jose";
			} else if (team == "purdue fort wayne") {
				return "ipfw";
			} else if (team == "stephen f austin") {
				return "sfa";
			} else if (team == "citadel") {
				return "the citadel";
			} else if (team == "wv mountaineers") {
				return "west virginia";
			} else if (team == "gw colonials") {
				return "george washington";
			} else if (team == "long island university") {
				return "liu";
			} else if (team == "north carolina central") {
				return "nc central";
			} else if (team == "grambling") {
				return "grambling state";
			} else if (team == "mt st marys") {
				return "mount st marys";
			} else if (team == "detroit mercy") {
				return "detroit";
			} else if (team == "unc greensboro") {
				return "nc greensboro";
			} else if (team == "miami (oh)") {
				return "miami oh";
			} else if (team == "youngstown st") {
				return "youngstown state";
			}
			return team
		}

		function parsePlayer(player) {
			return player.toLowerCase().replaceAll(".", "").replaceAll("(", "").replaceAll(")", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
		}

		let game = document.querySelector("h1").innerText.toLowerCase().replace(" odds", "").split(" player")[0];
		let awayFull = game.split(" @ ")[0];
		let awayName = awayFull.split(" ")[awayFull.split(" ").length - 1];
		let homeFull = game.split(" @ ")[1];
		let homeName = homeFull.split(" ")[homeFull.split(" ").length - 1];
		let away = convertTeam(game.split(" @ ")[0]);
		let home = convertTeam(game.split(" @ ")[1]);
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
			} else if (label.indexOf(" made threes") >= 0) {
				line = (parseFloat(label.split("+ ")[0]) - 0.5).toString();
				prop = "3ptm";
			} else if (label.indexOf(" total rebounds") >= 0) {
				player = true;
				prop = "reb";
			} else if (label.indexOf(" total assists") >= 0) {
				player = true;
				prop = "ast";
			} else if (label.indexOf(" total points + rebounds + assists") >= 0) {
				player = true;
				prop = "pts+reb+ast";
			} else if (label.indexOf(" - total") >= 0) {
				player = true;

				if (label.indexOf("most") >= 0 || label.indexOf("of the game") >= 0 || label.indexOf(" and ") >= 0 || label.indexOf("first") >= 0) {
					continue;
				}

				if (label.indexOf("pts + reb + ast") >= 0) {
					prop = "pts+reb+ast";
				} else if (label.indexOf("reb + ast") >= 0) {
					prop = "reb+ast";
				} else if (label.indexOf("pts + reb") >= 0) {
					prop = "pts+reb";
				} else if (label.indexOf("pts + ast") >= 0) {
					prop = "pts+ast";
				} else if (label.indexOf("assists") >= 0) {
					prop = "ast";
				} else if (label.indexOf("rebounds") >= 0) {
					prop = "reb";
				} else if (label.indexOf("made threes") >= 0) {
					prop = "3ptm";
				} else if (label.indexOf("points") >= 0) {
					prop = "pts";
				} else if (label.indexOf("steals") >= 0) {
					prop = "stl";
				} else if (label.indexOf("blocks") >= 0) {
					prop = "blk";
				}
			} else if (label.indexOf(" - alternate") >= 0) {
				continue;
			} else if (label.indexOf("alternate spread") >= 0) {
				prop = "spread";
				if (label.indexOf("1st half") >= 0) {
					prop = "1h_spread";
				} else if (label.indexOf("2nd half") >= 0) {
					prop = "2h_spread";
				}
			} else if (label.indexOf("alternate total points") >= 0) {
				prop = "total";
			} else if (label.indexOf("1st half moneyline") >= 0) {
				prop = "1h_ml";
			} else if (label.indexOf("1st half spread") >= 0) {
				prop = "1h_spread";
			} else if (label.indexOf("1st half total") >= 0) {
				prop = "1h_total";
			} else if (label.indexOf(awayName+" total points") >= 0) {
				prop = "away_total";
			} else if (label.indexOf(homeName+" total points") >= 0) {
				prop = "home_total";
			}

			if (label.indexOf("odd even") >= 0 || label.indexOf("tie") >= 0) {
				continue;
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
			el = arrow.parentElement.parentElement.querySelector("div[aria-label='Show more correct score options']");
			if (el) {
				el.click();
			}

			if (prop != "lines" && !data[game][prop]) {
				data[game][prop] = {};
			}

			let skip = 1;
			if (["away_total", "home_total", "spread"].indexOf(prop) >= 0 || player || prop.indexOf("1h_") >= 0) {
				skip = 2;
			}
			let btns = Array.from(li.querySelectorAll("div[role=button]"));
			btns.shift();

			if (prop == "lines") {
				if (btns[1].getAttribute("aria-label").split(", ")[1].split(" ")[0].indexOf(".") < 0 && btns[4].getAttribute("aria-label").split(", ")[1].split(" ")[0].indexOf(".") < 0) {
					data[game]["ml"] = btns[1].getAttribute("aria-label").split(", ")[1].split(" ")[0]+"/"+btns[4].getAttribute("aria-label").split(", ")[1].split(" ")[0];
				}
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
				if (!ariaLabel || ariaLabel.indexOf("Show more") >= 0 || ariaLabel.indexOf("Show less") >= 0 || ariaLabel.indexOf("unavailable") >= 0) {
					continue;
				}
				let odds = ariaLabel.split(", ")[1];

				//console.log(btn, odds);

				if (odds.indexOf("unavailable") >= 0) {
					continue;
				}
				if (prop == "lines") {

				} else if (["spread"].indexOf(prop) >= 0) {
					line = ariaLabel.split(", ")[1];
					let team = convertTeam(ariaLabel.split(", ")[0]);

					let isAway = true;
					if (team == game.split(" @ ")[1]) {
						line = (parseFloat(line) * -1).toString();
						isAway = false;
					}

					odds = ariaLabel.split(", ")[2];
					if (isAway) {
						data[game][prop][line] = odds+"/"+btns[i+1].getAttribute("aria-label").split(", ")[2];
					} else {
						data[game][prop][line] = btns[i+1].getAttribute("aria-label").split(", ")[2]+"/"+odds;
					}
				} else if (["total"].indexOf(prop) >= 0) {
					let odds = ariaLabel.split(", ")[2].split(" ")[0];
					let line = ariaLabel.split(", ")[1].split(" ")[0];

					let isAway = true;
					if (ariaLabel.split(", ")[1].indexOf("Under") >= 0) {
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
					if (prop == "pts+reb+ast") {
						player = parsePlayer(label.split(" total")[0]);
					} else {
						player = parsePlayer(ariaLabel.split(", ")[0].replace(" Over", ""));
					}
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					try {
						data[game][prop][player][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2].split(" ")[0];
					} catch {
						data[game][prop][player][line] = odds;
					}
				} else if (prop == "1h_ml") {
					data[game][prop] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[1];
				} else if (prop == "1h_spread") {
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
				} else if (["home_total", "away_total"].indexOf(prop) >= 0) {
					line = ariaLabel.split(", ")[1];
					odds = ariaLabel.split(", ")[2];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop] = {};
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
				} else if (skip == 2) {
					line = ariaLabel.split(", ")[2].split(" ")[1];
					odds = ariaLabel.split(", ")[3].split(" ")[0];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					data[game][prop] = {};
					data[game][prop][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[3].split(" ")[0];
				} else {
					player = parsePlayer(ariaLabel.split(",")[0].replace(" Over", ""));
					if (!data[game][prop][player]) {
						data[game][prop][player] = {};
					}

					data[game][prop][player][line] = odds;
				}
			}
		}

		console.log(data);
	}

"""

def writeFDMoneylines():
	js = """

	let data = {};
	{

		function convertTeam(team) {
			team = team.toLowerCase().replaceAll("'", "").replaceAll(".", "").replace("-", " ");
			if (team == "st johns") {
				return "saint johns";
			} else if (team == "nebraska cornhuskers") {
				return "nebraska";
			} else if (team == "siu edwardsville") {
				return "siue";
			} else if (team == "louisiana monroe") {
				return "ul monroe";
			} else if (team == "nicholls") {
				return "nicholls state";
			} else if (team == "san jose st") {
				return "san jose";
			} else if (team == "purdue fort wayne") {
				return "ipfw";
			} else if (team == "stephen f austin") {
				return "sfa";
			} else if (team == "citadel") {
				return "the citadel";
			} else if (team == "wv mountaineers") {
				return "west virginia";
			} else if (team == "gw colonials") {
				return "george washington";
			} else if (team == "long island university") {
				return "liu";
			} else if (team == "north carolina central") {
				return "nc central";
			} else if (team == "grambling") {
				return "grambling state";
			} else if (team == "mt st marys") {
				return "mount st marys";
			} else if (team == "detroit mercy") {
				return "detroit";
			} else if (team == "unc greensboro") {
				return "nc greensboro";
			} else if (team == "miami (oh)") {
				return "miami oh";
			} else if (team == "youngstown st") {
				return "youngstown state";
			}
			return team
		}

		const ul = document.querySelectorAll("ul")[5];
		const lis = Array.from(ul.querySelectorAll("li"));
		for (const li of lis) {
			if (!li.querySelector("svg")) {
				continue;
			}

			let btns = Array.from(li.querySelectorAll("div[role=button]"));
			let game = convertTeam(btns[1].getAttribute("aria-label").split(", ")[0].toLowerCase())+" @ "+convertTeam(btns[4].getAttribute("aria-label").split(", ")[0].toLowerCase());
			data[game] = btns[1].innerText+"/"+btns[4].innerText;
		}

		console.log(data);
	}

"""

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/basketball") >= 0) {
				urls[a.href] = 1;
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
  "https://mi.sportsbook.fanduel.com/football/ncaab/jacksonville-jaguars-@-new-orleans-saints-32705962",
  "https://mi.sportsbook.fanduel.com/football/ncaab/cleveland-browns-@-indianapolis-colts-32705963",
  "https://mi.sportsbook.fanduel.com/football/ncaab/washington-commanders-@-new-york-giants-32705965",
  "https://mi.sportsbook.fanduel.com/football/ncaab/atlanta-falcons-@-tampa-bay-buccaneers-32705970",
  "https://mi.sportsbook.fanduel.com/football/ncaab/buffalo-bills-@-new-england-patriots-32705972",
  "https://mi.sportsbook.fanduel.com/football/ncaab/las-vegas-raiders-@-chicago-bears-32705973",
  "https://mi.sportsbook.fanduel.com/football/ncaab/detroit-lions-@-baltimore-ravens-32705979",
  "https://mi.sportsbook.fanduel.com/football/ncaab/pittsburgh-steelers-@-los-angeles-rams-32705967",
  "https://mi.sportsbook.fanduel.com/football/ncaab/arizona-cardinals-@-seattle-seahawks-32705974",
  "https://mi.sportsbook.fanduel.com/football/ncaab/los-angeles-chargers-@-kansas-city-chiefs-32705968",
  "https://mi.sportsbook.fanduel.com/football/ncaab/green-bay-packers-@-denver-broncos-32705969",
  "https://mi.sportsbook.fanduel.com/football/ncaab/miami-dolphins-@-philadelphia-eagles-32705975",
  "https://mi.sportsbook.fanduel.com/football/ncaab/san-francisco-49ers-@-minnesota-vikings-32705977"
]

	games = ["https://mi.sportsbook.fanduel.com/football/ncaab/jacksonville-jaguars-@-new-orleans-saints-32705962"]
	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away = convertTeam(game.split(" @ ")[0])
		home = convertTeam(game.split(" @ ")[1])
		game = f"{away} @ {home}"
		if game in lines:
			continue
		lines[game] = {}

		outfile = "outnba"

		for tab in ["", "passing-props", "receiving-props", "rushing-props", "defensive-props", "1st-half", "2nd-half", "1st-quarter"]:
		#for tab in ["1st-half"]:
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])
			time.sleep(2.1)

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue
			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				marketType = data["attachments"]["markets"][market]["marketType"]
				runners = data["attachments"]["markets"][market]["runners"]

				prefix = ""
				if "1st half" in marketName or "first half" in marketName:
					prefix = "1h_"
				elif "2nd half" in marketName or "second half" in marketName:
					prefix = "2h_"
				elif "1st quarter" in marketName or "1st quarter" in marketName:
					prefix = "1q_"


				if marketName in ["moneyline"] or "any time touchdown" in marketName or "first touchdown" in marketName or marketName.startswith("1st half") or marketName.startswith("1st quarter") or marketName.startswith("alternate") or "total points" in marketName or marketName == "player to record a sack" or marketName.split(" - ")[-1] in ["pass completions", "passing tds", "passing attempts", "passing yds", "receiving yds", "receiving tds", "total receptions", "longest pass", "longest rush", "longest reception", "rushing yds", "rushing attempts", "rushing + receiving yds"]:

					prop = ""
					if "moneyline" in marketName:
						prop = "ml"
					elif "total points" in marketName or marketName.startswith("alternate total points"):
						if "/" in marketName:
							continue
						if "AWAY_TOTAL_POINTS" in marketType or "AWAY_TEAM_TOTAL_POINTS" in marketType:
							prop = "away_total"
						elif "HOME_TOTAL_POINTS" in marketType or "HOME_TEAM_TOTAL_POINTS" in marketType:
							prop = "home_total"
						else:
							prop = "total"
					elif "spread" in marketName or marketName.startswith("alternate spread"):
						if "/" in marketName:
							continue
						prop = "spread"
					elif marketName == "any time touchdown scorer":
						prop = "attd"
					elif marketName == "first touchdown scorer":
						prop = "ftd"
					elif marketName == "player to record a sack":
						prop = "sacks"
					elif " - " in marketName:
						if "total touchdowns" in marketName:
							continue
						marketName = marketName.split(" - ")[-1]
						prop = "_".join(marketName.split(" ")).replace("completions", "cmp").replace("tds", "td").replace("passing", "pass").replace("attempts", "att").replace("yds", "yd").replace("receiving", "rec").replace("total_receptions", "rec").replace("reception", "rec").replace("rushing", "rush")
						if prop == "rush_+_rec_yd":
							prop = "rush+rec"
					else:
						continue

					prop = f"{prefix}{prop}"

					handicap = runners[0]["handicap"]
					skip = 1 if prop in ["spread", "total", "attd", "sacks", "ftd"] else 2
					try:
						ou = str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
						if skip == 2:
							ou += "/"+str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					except:
						continue

					if runners[0]["runnerName"] == "Under":
						ou = str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])

					if "ml" in prop:
						lines[game][prop] = ou
					else:
						if prop not in lines[game]:
							lines[game][prop] = {}

						for i in range(0, len(runners), skip):
							handicap = str(float(runners[i]["handicap"]))
							try:
								odds = str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							except:
								continue
							if prop in ["spread", "total"]:
								handicap = str(float(runners[i]["runnerName"].split(" ")[-1][1:-1]))
								runnerType = runners[i]["result"]["type"]
								if "spread" in prop and runnerType in ["HOME", "UNDER"]:
									handicap = str(float(handicap) * -1)
								
								if handicap not in lines[game][prop]:
									lines[game][prop][handicap] = ""
								if runners[i]["result"]["type"] == "OVER" or runners[i]["result"]["type"] == "AWAY":
									lines[game][prop][handicap] = str(odds)+lines[game][prop][handicap]
								else:
									lines[game][prop][handicap] += f"/{odds}"
							elif "spread" in prop or "total" in prop:
								lines[game][prop][handicap] = ou
							else:
								if prop in ["attd", "ftd"]:
									player = parsePlayer(runners[i]["runnerName"])
									lines[game][prop][player] = odds
								elif prop == "sacks":
									player = parsePlayer(runners[i]["runnerName"].split(" to ")[0])
									if player not in lines[game][prop]:
										lines[game][prop][player] = odds
									else:
										if "not" in runners[i]["runnerName"]:
											lines[game][prop][player] += f"/{odds}"
										else:
											lines[game][prop][player] = f"{odds}/{lines[game][prop][player]}"
										lines[game][prop][player] = "0.5 "+lines[game][prop][player]
								else:
									player = parsePlayer(" ".join(runners[i]["runnerName"].split(" ")[:-1]))
									lines[game][prop][player] = f"{handicap} {ou}"
	
	with open(f"static/ncaab/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

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

def writeDK(date, march):
	url = "https://sportsbook.draftkings.com/leagues/football/nba"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 487,
		"points": 1215,
		"rebounds": 1216,
		"assists": 1217,
		"threes": 1218,
		"team": 523,
		"combos": 583
	}
	
	subCats = {
		487: [4511, 13202, 13201],
		1215: [12488, 13769],
		1216: [12492, 13770],
		1217: [12495, 13771],
		1218: [12497],
		523: [4609],
		583: [5001, 9976, 9973, 9974]
	}

	propIds = {13202: "spread", 13201: "total", 12488: "pts", 13769: "pts", 12492: "reb", 13770: "reb", 12495: "ast", 13771: "ast", 12497: "3ptm", 5001: "pts+reb+ast", 9976: "pts+reb", 9973: "pts+ast", 9974: "reb+ast"}

	if False:
		mainCats = {
			"team": 530
		}
		subCats = {
			530: [10514],
		}

	lines = {}
	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/92483/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outnba"
			os.system(f"curl {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
				startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=5)
				if not march and startDt.day != int(date[-2:]):
					continue
					pass
				elif startDt < datetime.now():
					continue
				game = event["name"].lower()
				games = []
				for team in game.split(" @ "):
					t = convertTeam(team)
					games.append(t)
				game = " @ ".join(games)
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

							prefix = ""
							if subCat in propIds:
								prop = propIds[subCat]
							else:
								prop = row["label"].lower().split(" [")[0]
								
								if "1st half" in prop:
									prefix = "1h_"
								elif "2nd half" in prop:
									prefix = "2h_"
								elif "1st quarter" in prop:
									prefix = "1q_"

								if "moneyline" in prop:
									prop = "ml"
								elif "spread" in prop:
									prop = "spread"
								elif "team total points" in prop:
									team = prop.split(":")[0]
									t = team.split(" ")[0]
									if game.startswith(t):
										prop = "away_total"
									else:
										prop = "home_total"
								elif "total" in prop:
									prop = "total"
								else:
									continue


							prop = prop.replace(" alternate", "")
							prop = f"{prefix}{prop}"

							if prop == "halftime/fulltime":
								continue

							if "ml" not in prop:
								if prop not in lines[game]:
									lines[game][prop] = {}

							outcomes = row["outcomes"]
							ou = ""
							try:
								ou = f"{outcomes[0]['oddsAmerican']}/{outcomes[1]['oddsAmerican']}"
								if outcomes[0]["label"] == "Under":
									ou = f"{outcomes[1]['oddsAmerican']}/{outcomes[0]['oddsAmerican']}"
							except:
								continue

							if "ml" in prop:
								lines[game][prop] = ou
							elif "total" in prop or "spread" in prop:
								for i in range(0, len(outcomes), 2):
									line = str(float(outcomes[i]["line"]))
									ou = f"{outcomes[i]['oddsAmerican']}"
									try:
										ou += f"/{outcomes[i+1]['oddsAmerican']}"
										if outcomes[i]["label"] == "Under":
											ou = f"{outcomes[i+1]['oddsAmerican']}/{outcomes[i]['oddsAmerican']}"
									except:
										pass
									lines[game][prop][line] = ou
							elif len(outcomes) > 2:
								for i in range(0, len(outcomes), 2):
									player = parsePlayer(outcomes[i]["participant"].split(" (")[0])
									if player not in lines[game][prop]:
										lines[game][prop][player] = {}
									try:
										lines[game][prop][player][outcomes[i]['line']] = f"{outcomes[i]['oddsAmerican']}/{outcomes[i+1]['oddsAmerican']}"
									except:
										continue
									if outcomes[i]["label"] == "Under":
										lines[game][prop][player][outcomes[i]['line']] = f"{outcomes[i+1]['oddsAmerican']}/{outcomes[i]['oddsAmerican']}"
							else:
								player = parsePlayer(outcomes[0]["participant"].split(" (")[0])
								if player not in lines[game][prop]:
									lines[game][prop][player] = {}
								lines[game][prop][player][outcomes[0]['line']] = f"{outcomes[0]['oddsAmerican']}"
								if len(row["outcomes"]) > 1:
									lines[game][prop][player][outcomes[0]['line']] += f"/{outcomes[1]['oddsAmerican']}"

	with open("static/ncaab/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B18/C20902960/D43/E181378/F43/"

	js = """
	const data = {};

	{
		const main = document.querySelector(".gl-MarketGroupContainer");
		let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
		let prefix = "";
		if (title.indexOf("1st half") >= 0) {
			prefix = "1h_";
		} else if (title.indexOf("1st quarter") >= 0) {
			prefix = "1q_";
		}

		if (title == "game lines" || title == "1st half" || title == "1st quarter") {
			title = "lines";
		} else if (title == "player assists") {
			title = "ast";
		} else if (title === "player points") {
			title = "pts";
		} else if (title === "player rebounds") {
			title = "reb";
		} else if (title === "player steals") {
			title = "stl";
		} else if (title === "player turnovers") {
			title = "to";
		} else if (title === "player blocks") {
			title = "blk";
		} else if (title === "player threes made") {
			title = "3ptm";
		} else if (title === "alternative point spread" || title == "alternative spread" || title == "alternative 1st quarter point spread") {
			title = prefix+"spread";
		} else if (title === "alternative game total") {
			title = prefix+"total";
		}

		if (title.indexOf("spread") >= 0 || title.indexOf("total") >= 0) {
			for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
				const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" v ", " @ ");
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
		} else if (title != "lines") {
			for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
				const game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" v ", " @ ");
				if (div.classList.contains("src-FixtureSubGroup_Closed")) {
					div.click();
				}
				let playerList = [];
				for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
					let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(". ", "").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
					let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];
					
					if (!data[game]) {
						data[game] = {};
					}
					if (!data[game][title]) {
						data[game][title] = {};
					}
					data[game][title][player] = "";
					playerList.push([game, player]);
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
		} else {
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
				const game = away+" @ "+home;
				games.push(game);

				if (!data[game]) {
					data[game] = {};
				}
			}

			const props = ["spread", "total", "ml"];
			let p = 0;
			for (const prop of props) {
				idx = 0;
				let divs = main.querySelectorAll(".gl-Market_General")[p+1].querySelectorAll(".gl-Participant_General");
				p += 1;
				for (let i = 0; i < divs.length; i += 2) {
					let game = games[idx];

					if (!game) {
						break;
					}

					let over = divs[i].innerText;
					let under = divs[i+1].innerText;

					if (prop == "ml") {
						if (over !== "" && under !== "") {
							data[game][prefix+prop] = over+"/"+under;
						}
					} else {
						let over = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
						let under = divs[i+1].querySelector(".sac-ParticipantCenteredStacked50OTB_Odds").innerText;
						let line = divs[i].querySelector(".sac-ParticipantCenteredStacked50OTB_Handicap").innerText.replace("O ", "");
						if (!data[game][prefix+prop]) {
							data[game][prefix+prop] = {};
						}
						data[game][prefix+prop][line] = over+"/"+under;
					}
					idx += 1;
				}
			}
		}

		console.log(data);
	}

	"""
	pass

def bvParlay():
	with open(f"{prefix}static/ncaab/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/ncaab/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/ncaab/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/ncaab/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/ncaab/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/ncaab/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaab/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/ncaab/caesars.json") as fh:
		czLines = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		#"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines
	}

	ev = []
	evData = {}
	for game in bvLines:
		away, home = map(str, game.split(" @ "))
		if "td_parlay" not in bvLines[game]:
			continue
		abbr = {}
		shouldBreak = False
		for prop in ["rush_yd", "rec"]:
			try:
				for player in bvLines[game][prop]:
					abbr[player.split(" ")[0][0]+". "+player.split(" ")[-1]] = player
			except:
				shouldBreak = True

		if shouldBreak:
			continue

		for desc in bvLines[game]["td_parlay"]:
			tdParlay = bvLines[game]["td_parlay"][desc]
			if tdParlay["ml"] or (len(tdParlay["ftd"]) == 1 and len(tdParlay["attd"]) == 1):
				pass
			else:
				if tdParlay["ftd"] or "Anytime" not in desc or "1st" in desc:
					continue

			#if desc != "A.J. Brown & D'Andre Swift 1+ Anytime Touchdown Each":
			#	continue

			fairVals = []
			legs = []
			players = 0
			for prop in ["attd", "ftd"]:
				for player in tdParlay[prop]:
					players += 1
					if "." in player:
						try:
							player = abbr[player]
						except:
							continue
					maxOdds = []
					books = []
					for book in lines:
						if game in lines[book] and prop in lines[book][game] and player in lines[book][game][prop]:
								books.append(book)
								maxOdds.append(int(lines[book][game][prop][player].split("/")[0]))

					if not maxOdds:
						continue
					odds = max(maxOdds)
					idx = maxOdds.index(odds)
					book = books[idx]
					legs.append(f"{player.title()} {odds} {book.upper()}")
					if odds > 0:
						implied = 100 / (odds + 100)
					else:
						implied = -1*odds / (-1*odds + 100)

					fairVals.append(implied)

			if players != len(fairVals):
				continue

			if tdParlay["ml"]:
				maxOdds = []
				books = []
				for book in lines:
					if game in lines[book] and prop in lines[book][game]:
							i = 0
							if tdParlay["ml"] == home:
								i = 1
							books.append(book)
							maxOdds.append(int(lines[book][game]["ml"].split("/")[i]))

				if not maxOdds:
					continue
				odds = max(maxOdds)
				idx = maxOdds.index(odds)
				book = books[idx]
				legs.append(f"{tdParlay['ml'].upper()} ML {odds} {book.upper()}")
				if odds > 0:
					implied = 100 / (odds + 100)
				else:
					implied = -1*odds / (-1*odds + 100)
				fairVals.append(implied)

			odds = 1
			for o in fairVals:
				odds *= o
			
			fairValue = round((100 * (1 - odds)) / odds)

			evData[desc] = {}
			devig(evData, desc, str(fairValue), int(tdParlay["odds"]))
			ev.append((evData[desc]["ev"], desc, fairValue, tdParlay['odds'], legs))

	for row in sorted(ev):
		print(f"{row[0]}, {row[1]}, fairval={row[2]}, bvOdds={row[3]} {row[4]}")
		pass

	output = "\t".join(["EV", "Parlay", "BV Odds", "Fair Value"])+"\n"
	for row in sorted(ev, reverse=True):
		arr = [row[0], row[1], row[3], row[2]]
		arr.extend(row[-1])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/ncaab/bvParlays.csv", "w") as fh:
		fh.write(output)

def writePlayer(player, propArg):
	with open(f"{prefix}static/ncaab/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/ncaab/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaab/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/ncaab/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/ncaab/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/ncaab/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/ncaab/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/ncaab/caesars.json") as fh:
		czLines = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		#"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines
	}

	for book in lines:
		for game in lines[book]:
			for prop in lines[book][game]:
				if propArg and propArg != prop:
					continue

				for p in lines[book][game][prop]:
					if player not in p:
						continue

					print(book, lines[book][game][prop][p])

def writePlayers(keep=None):

	with open(f"{prefix}static/ncaab/playerIds.json") as fh:
		playerIds = json.load(fh)

	url = "https://www.espn.com/mens-college-basketball/scoreboard/_/seasontype/2/group/50"
	outfile = "outncaab2"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	soup = BS(open(outfile, 'rb').read(), "lxml")

	teamIds = {}
	for div in soup.findAll("section", class_="TeamLinks"):
		team = convertTeam(strip_accents(div.find("a").text.lower()))
		id = div.find("a").get("href").split("/")[-2]
		teamIds[team] = id


	for team in teamIds:
		if team in playerIds:
			continue

		print(team)
		playerIds[team] = {}
		url = f"https://www.espn.com/mens-college-basketball/team/roster/_/id/{teamIds[team]}"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")

		if not soup.find("table", class_="Table"):
			continue

		for row in soup.find("table", class_="Table").findAll("tr")[1:]:
			playerId = row.find("a").get("href").split("/")[-2]
			player = parsePlayer(row.findAll("td")[1].find("a").text)
			playerIds[team][player] = playerId


	with open(f"{prefix}static/ncaab/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/ncaab/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaab/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/ncaab/draftkings.json") as fh:
		dkLines = json.load(fh)

	players = {}
	for lines in [fdLines, dkLines, czLines]:
		for game in lines:
			away, home = map(str, game.split(" @ "))
			for team in [away, home]:
				if team not in players:
					players[team] = {}
				for prop in ["pts", "ast", "reb", "3ptm", "pts+reb+ast", "pts+ast", "pts+reb", "reb+ast"]:
					if prop in lines[game]:
						for player in lines[game][prop]:
							try:
								players[team][player] = playerIds[team][player]
							except:
								pass

	stats = {}
	if keep:
		with open(f"{prefix}static/ncaab/stats.json") as fh:
			stats = json.load(fh)

	for team in players:
		if team not in stats:
			stats[team] = {}
		for player in players[team]:
			if player not in stats[team]:
				stats[team][player] = {}
			elif keep:
				continue

			url = f"https://www.espn.com/mens-college-basketball/player/gamelog/_/id/{players[team][player]}"
			time.sleep(0.3)
			os.system(f"curl -k \"{url}\" -o {outfile}")
			soup = BS(open(outfile, 'rb').read(), "lxml")

			hdrs = []
			for td in soup.find("thead").findAll("th")[1:]:
				hdrs.append(td.text.lower())

			playerStats = {}
			for tbody in soup.find("div", class_="gamelog").findAll("tbody"):
				for row in tbody.findAll("tr"):
					if "note-row" in row.get("class") or "totals_row" in row.get("class"):
						continue
					for td, hdr in zip(row.findAll("td")[1:], hdrs):
						val = td.text
						if hdr == "opp":
							val = "A" if "@" in val else "H"
						elif hdr == "result":
							try:
								val = td.find("div", class_="ResultCell").text
							except:
								continue

						if hdr not in playerStats:
							playerStats[hdr] = []	
						playerStats[hdr].append(val)

			playerStats["pts+reb+ast"] = []
			playerStats["pts+reb"] = []
			playerStats["pts+ast"] = []
			playerStats["reb+ast"] = []
			for pts,reb,ast in zip(playerStats["pts"], playerStats["reb"], playerStats["ast"]):
				playerStats["pts+reb+ast"].append(str(int(pts)+int(reb)+int(ast)))
				playerStats["pts+reb"].append(str(int(pts)+int(reb)))
				playerStats["pts+ast"].append(str(int(pts)+int(ast)))
				playerStats["reb+ast"].append(str(int(reb)+int(ast)))

			for hdr in playerStats:
				stats[team][player][hdr] = ",".join(playerStats[hdr])
	
	with open(f"{prefix}static/ncaab/stats.json", "w") as fh:
		json.dump(stats, fh)


def writeEV(propArg="", bookArg="fd", teamArg="", notd=None, boost=None):

	if not boost:
		boost = 1

	#with open(f"{prefix}static/ncaab/bet365.json") as fh:
	#	bet365Lines = json.load(fh)

	#with open(f"{prefix}static/ncaab/actionnetwork.json") as fh:
	#	actionnetwork = json.load(fh)

	with open(f"{prefix}static/ncaab/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/ncaab/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/ncaab/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/ncaab/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/ncaab/pointsbet.json") as fh:
		pbLines = json.load(fh)

	with open(f"{prefix}static/ncaab/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaab/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/ncaab/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/ncaab/stats.json") as fh:
		stats = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		#"pb": pbLines,
		"bv": bvLines,
		"dk": dkLines,
		"cz": czLines
	}

	with open(f"{prefix}static/ncaab/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	teamGame = {}
	for game in pnLines:
		away, home = map(str, game.split(" @ "))
		teamGame[away] = teamGame[home] = game

	for game in fdLines:
		away, home = map(str, game.split(" @ "))
		if teamArg:
			if game.split(" @ ")[0] not in teamArg.split(",") and game.split(" @ ")[1] not in teamArg.split(","):
				continue

		props = {}
		for book in lines:
			if game not in lines[book]:
				continue
			for prop in lines[book][game]:
				props[prop] = 1

		for prop in props:
			if propArg and prop != propArg:
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

			for handicap, playerHandicap in handicaps:
				player = handicaps[(handicap, playerHandicap)]

				totalGames = totalOver = total5Over = total10Over = 0
				totalSplits = ""
				team = ""
				if player:
					try:
						if player in stats[away]:
							team = away
						elif player in stats[home]:
							team = home
					except:
						continue

					if team:
						arr = ""
						if prop == "3ptm":
							arr = ",".join([x.split("-")[0] for x in stats[team][player]["3pt"].split(",")])
						else:
							arr = stats[team][player].get(prop, "")

						if arr:
							totalGames = len(stats[team][player]["min"].split(","))
							#print(player, team, prop, arr)
							totalOver = [x for x in arr.split(",") if int(x) > float(playerHandicap)]
							totalOver = round(len(totalOver) * 100 / totalGames)
							total5Over = [x for x in arr.split(",")[:5] if int(x) > float(playerHandicap)]
							total5Over = round(len(total5Over) * 100 / min(totalGames, 5))
							total10Over = [x for x in arr.split(",")[:10] if int(x) > float(playerHandicap)]
							total10Over = round(len(total10Over) * 100 / min(totalGames, 10))
							totalSplits = ",".join(arr.split(",")[:10][::-1])

				for i in range(2):
					highestOdds = []
					books = []
					odds = []

					if totalOver and i == 1:
						totalOver = 100 - totalOver
						total5Over = 100 - total5Over
						total10Over = 100 - total10Over

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
									if playerHandicap != val.split(" ")[0]:
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

							if not o or o == "-":
								continue
							highestOdds.append(int(o))
							odds.append(ou)
							books.append(book)

					if len(books) < 2:
						if player:
							print(game, player, prop, playerHandicap)
						continue

					if prop in ["spread", "total"] and len(books) < 3:
						continue

					#print(game, prop, handicap, highestOdds, books, odds)

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
					#print(maxOU in l, maxOU, l)
					l.remove(maxOU)
					books.remove(evBook)
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
						
					key = f"{game} {handicap} {playerHandicap} {prop} {'over' if i == 0 else 'under'}"
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
						evData[key]["totalOver"] = totalOver
						evData[key]["total5Over"] = total5Over
						evData[key]["total10Over"] = total10Over
						evData[key]["totalSplits"] = totalSplits
						evData[key]["game"] = team if team else game
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

	with open(f"{prefix}static/ncaab/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def sortEV():
	with open(f"{prefix}static/ncaab/ev.json") as fh:
		evData = json.load(fh)

	#with open(f"static/ncaab/totals.json") as fh:
	#	totals = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], d["game"], player, d["playerHandicap"], d["line"], d["book"], j, d))

	for row in sorted(data):
		print(row[:-1])

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "BV", "PN", "Kambi/BR", "CZ", "L10%", "L5%", "SZN", "Splits"]) + "\n"
	for row in sorted(data, reverse=True):
		player = row[-1]["player"]
		prop = row[-1]["prop"]
		pos = rank = posRank = ""
		implied = 0
		if row[-1]["line"] > 0:
			implied = 100 / (row[-1]["line"] + 100)
		else:
			implied = -1*row[-1]["line"] / (-1*row[-1]["line"] + 100)
		implied *= 100
		ou = ("u" if row[-1]["under"] else "o")+" "
		if player:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), f"{round(implied)}%", row[-1]["game"], player.title(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "bv", "pn", "kambi", "cz"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		for x in ["total10Over", "total5Over", "totalOver"]:
			if not row[-1][x]:
				arr.append("-")
			else:
				arr.append(f"{row[-1][x]}%")
		arr.append(row[-1]["totalSplits"])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/ncaab/props.csv", "w") as fh:
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
	parser.add_argument("--bvParlay", action="store_true", help="Bovada TD Parlay")
	parser.add_argument("--pb", action="store_true", help="Pointsbet")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
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
	parser.add_argument("--under", action="store_true", help="Under")
	parser.add_argument("--nocz", action="store_true", help="No CZ Lines")
	parser.add_argument("--no365", action="store_true", help="No 365 Devig")
	parser.add_argument("--nobr", action="store_true", help="No BR/Kambi lines")
	parser.add_argument("--dinger", action="store_true", help="Dinger Tues")
	parser.add_argument("--plays", action="store_true", help="Plays")
	parser.add_argument("--players", action="store_true", help="Players")
	parser.add_argument("--keep", action="store_true", help="Keep")
	parser.add_argument("--summary", action="store_true", help="Summary")
	parser.add_argument("--text", action="store_true", help="Text")
	parser.add_argument("--matchups", action="store_true", help="Matchups")
	parser.add_argument("--lineups", action="store_true", help="Lineups")
	parser.add_argument("--lineupsLoop", action="store_true", help="Lineups")
	parser.add_argument("--debug", action="store_true", help="Debug")
	parser.add_argument("--notd", action="store_true", help="Not ATTD FTD")
	parser.add_argument("--kenpom", action="store_true")
	parser.add_argument("--march", action="store_true")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--player", help="Player")

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


	if args.action:
		writeActionNetwork(args.date)

	if args.fd:
		writeFanduel()

	if args.mgm:
		writeMGM(args.date, args.march)

	if args.pb:
		writePointsbet(args.date)

	if args.dk:
		writeDK(args.date, args.march)

	if args.kambi:
		writeKambi(args.date, args.march)

	if args.pn:
		writePinnacle(args.date, args.debug, args.march)

	if args.bv:
		writeBV(args.date, args.march)

	if args.bvParlay:
		bvParlay()

	if args.cz:
		writeCZ(args.date, args.march)

	if args.matchups:
		writeMatchups()

	if args.players:
		writePlayers(args.keep)

	if args.kenpom:
		writeKenpom()

	if args.update:
		#writeFanduel()
		print("pn")
		writePinnacle(args.date, args.debug, args.march)
		print("kambi")
		writeKambi(args.date, args.march)
		print("mgm")
		writeMGM(args.date, args.march)
		#print("pb")
		#writePointsbet(args.date)
		print("dk")
		writeDK(args.date, args.march)
		print("cz")
		writeCZ(args.date, args.march)
		print("bv")
		writeBV(args.date, args.march)

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, teamArg=args.team, notd=args.notd, boost=args.boost)

	if args.print:
		sortEV()

	if args.player:
		writePlayer(args.player, args.prop)