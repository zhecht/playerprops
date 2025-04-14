from flask import *
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
try:
	from shared import *
except:
	from controllers.shared import *
import math
import json
import os
import re
import argparse
import unicodedata
import time
from twilio.rest import Client
import nodriver as uc
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

nhl_blueprint = Blueprint('nhl', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def convertFDTeam(team):
	team = team.lower()
	if team.endswith("predators"):
		team = "nsh"
	elif team.endswith("lightning"):
		team = "tb"
	elif team.endswith("blackhawks"):
		team = "chi"
	elif team.endswith("penguins"):
		team = "pit"
	elif team.endswith("kraken"):
		team = "sea"
	elif team.endswith("knights"):
		team = "vgk"
	elif team.endswith("senators"):
		team = "ott"
	elif team.endswith("hurricanes"):
		team = "car"
	elif team.endswith("canadiens"):
		team = "mtl"
	elif team.endswith("leafs"):
		team = "tor"
	elif team.endswith("jets"):
		team = "wpg"
	elif team.endswith("flames"):
		team = "cgy"
	elif team.endswith("oilers"):
		team = "edm"
	elif team.endswith("canucks"):
		team = "van"
	elif team.endswith("avalanche"):
		team = "col"
	elif team.endswith("kings"):
		team = "la"
	elif team.endswith("wings"):
		team = "det"
	elif team.endswith("devils"):
		team = "nj"
	elif team.endswith("flyers"):
		team = "phi"
	elif team.endswith("jackets"):
		team = "cbj"
	elif team.endswith("rangers"):
		team = "nyr"
	elif team.endswith("sabres"):
		team = "buf"
	elif team.endswith("bruins"):
		team = "bos"
	elif team.endswith("panthers"):
		team = "fla"
	elif team.endswith("sharks"):
		team = "sj"
	elif "utah" in team:
		team = "utah"
	elif team.endswith("capitals"):
		team = "wsh"
	elif team.endswith("islanders"):
		team = "nyi"
	elif team.endswith("wild"):
		team = "min"
	elif team.endswith("blues"):
		team = "stl"
	elif team.endswith("stars"):
		team = "dal"
	elif team.endswith("ducks"):
		team = "ana"
	elif team == "sweden":
		return "swe"
	elif team == "canada":
		return "can"
	return team

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

def getPropData(date=None, teams=""):
	if not date:
		date = str(datetime.now())[:10]

	with open(f"static/hockeyreference/totals.json") as fh:
		stats = json.load(fh)

	with open(f"static/hockeyreference/scores.json") as fh:
		scores = json.load(fh)

	with open(f"static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	with open(f"static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open("static/nhl/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open("static/nhl/draftkings.json") as fh:
		dkLines = json.load(fh)



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

	with open(f"{prefix}static/nhl/fanduel.json") as fh:
		fdLines = json.load(fh)

	teamGame = {}
	for game in fdLines:
		away, home = map(str, game.split(" @ "))
		if away not in teamGame:
			teamGame[away] = game
		if home not in teamGame:
			teamGame[home] = game

	props = ["56_first_touchdown_scorer", "62_anytime_touchdown_scorer", "60_longest_completion", "59_longest_reception", "58_longest_rush", "30_passing_attempts", "10_pass_completions", "11_passing_tds", "9_passing_yards", "17_receiving_tds", "16_receiving_yards", "15_receptions", "18_rushing_attempts", "13_rushing_tds", "12_rushing_yards", "70_tackles_assists"]
	props = ["70_tackles_assists"]

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
		path = f"nflout.json"
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
			prop = "_".join(actionProp.split("_")[1:]).replace("rushing", "rush").replace("passing", "pass").replace("receiving", "rec").replace("yards", "yd").replace("attempts", "att").replace("reception", "rec")
			if prop == "longest_completion":
				prop = "longest_pass"

		if prop.endswith("s"):
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
				player = playerIds[oddData["player_id"]]
				team = teamIds[oddData["team_id"]]
				game = teamGame[team]
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

	with open(f"{prefix}static/nhl/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)


def writeCZ(date):
	if not date:
		date = str(datetime.now())[:10]

	league = "b7b715a9-c7e8-4c47-af0a-77385b525e09"
	url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/icehockey/events/schedule?competitionIds={league}"

	outfile = "nhloutCZ"
	cookie = ""
	with open("token") as fh:
		cookie = fh.read()
	
	os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: b51ee484-42d9-40de-81ed-5c6df2f3122a' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.15.1' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'Priority: u=4' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"][:20]:
		games.append(event["id"])

	#games = ["7e06c1b1-0be9-404e-b81d-665bc8088ada"]

	res = {}
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/events/{gameId}"
		time.sleep(0.2)
		os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		#print(data["name"], data["startTime"])

		if str(datetime.strptime(data["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue

		game = data["name"].lower().replace("|", "").replace(" at ", " @ ").replace(" 4n", "")
		away, home = map(str, game.split(" @ "))
		game = f"{convertFDTeam(away)} @ {convertFDTeam(home)}"
		res[game] = {}

		for market in data["markets"]:
			if "name" not in market:
				continue

			if market["active"] == False:
				continue
			prop = market["name"].lower().replace("|", "").split(" (")[0]
			template = market["templateName"].lower().replace("|", "")

			prefix = player = ""
			playerProp = False
			if "1st period" in prop:
				prefix = "1p_"
			elif "2nd period" in prop:
				prefix = "2p_"
			elif "3rd period" in prop:
				prefix = "3p_"

			if "money line" in prop:
				prop = "ml"
			elif "both teams to score" in prop:
				prop = "btts"
			elif prop == "60 minutes betting":
				prop = "3-way"
			elif prop == "player to score a goal" or prop == "anytime goal scorer":
				prop = "atgs"
			elif prop == "first goalscorer" or prop == "first goal scorer":
				prop = "fgs"
			elif "total saves" in prop:
				player = parsePlayer(prop.split(" total saves")[0])
				prop = "saves"
			elif "total shots" in prop:
				player = parsePlayer(prop.split(" total shots")[0])
				prop = "sog"
			elif "total assists" in prop:
				player = parsePlayer(prop.split(" total assists")[0])
				prop = "ast"
			elif "blocked shots" in prop:
				player = parsePlayer(prop.split(" blocked shots")[0])
				prop = "bs"
			elif prop.startswith("player to be credited"):
				if "power play" in prop:
					prop = "pp_pts"
				elif "assists" in prop:
					prop = "ast"
				elif "point" in prop:
					prop = "pts"
			elif "total goals" in prop or "total goals" in template:
				if "odd/even" in template:
					continue
				if template == "x team goals":
					if game.startswith(convertFDTeam(prop.split(" total")[0])):
						prop = "away_total"
					elif game.endswith(convertFDTeam(prop.split(" total")[0])):
						prop = "home_total"
				else:
					prop = "total"
			elif "puck line" in prop:
				prop = "spread"
			else:
				#print(prop)
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			selections = market["selections"]
			skip = 1 if prop in ["fgs", "atgs", "pts", "pp_pts"] else 2
			if prop == "3-way":
				skip = 3
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

				if "ml" in prop or "btts" in prop:
					res[game][prop] = ou
				elif "3-way" in prop:
					res[game][prop] = f"{selections[0]['price']['a']}/{selections[-1]['price']['a']}"
				elif prop in ["atgs", "fgs"]:
					player = parsePlayer(selections[i]["name"].replace("|", "").strip())
					res[game][prop][player] = ou
				elif prop in ["pts", "pp_pts"]:
					line = str(float(market["name"].split(" ")[5][1:]) - 0.5)
					player = parsePlayer(selections[i]["name"].replace("|", "").strip())
					if player not in res[game][prop]:
						res[game][prop][player] = {}
					res[game][prop][player][line] = ou
				elif "spread" in prop:
					line = str(float(market["line"]) * -1)
					mainLine = line
					res[game][prop][line] = ou
				elif "total" in prop:
					if "line" in market:
						line = str(float(market["line"]))
						if prop == "total":
							mainLine = line
						res[game][prop][line] = ou
					else:
						line = str(float(selections[i]["name"].split(" ")[-1]))
						if prop == "total":
							mainLine = line
						if line not in res[game][prop]:
							res[game][prop][line] = ou
						else:
							res[game][prop][line] += "/"+ou
				else:
					try:
						line = str(float(market["line"]))
					except:
						line = "0.5"
					res[game][prop][player.strip()] = {
						line: ou
					}

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


	with open("static/nhl/caesars.json", "w") as fh:
		json.dump(res, fh, indent=4)

def mergeCirca():
	date = str(datetime.now())[:10]
	with open("static/nhl/circa.json") as fh:
		circa = json.load(fh)

	with open("static/nhl/circa-main.json") as fh:
		circaMain = json.load(fh)

	with open("static/nhl/circa-props.json") as fh:
		circaProps = json.load(fh)

	with open(f"static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"static/hockeyreference/roster.json") as fh:
		roster = json.load(fh)

	games = schedule[date]
	teamGame = {}
	for game in games:
		a,h = map(str, game.split(" @ "))
		teamGame[a] = game
		teamGame[h] = game

	data = nested_dict()
	data.update(circaMain)
	for game in circaProps:
		data[game]["atgs"] = circaProps[game]["atgs"]
		
	with open("static/nhl/circa.json", "w") as fh:
		json.dump(data, fh, indent=4)

def writeCircaProps(page, data, teamGame):
	page.save("outnhlprops.png", "PNG")
	img = Image.open("outnhlprops.png")
	bottom, top = 2250, 495
	left,right = 295, 1575

	player_img = img.crop((90,415,470,bottom)) # l,t,r,b
	#player_img.save("outnhl-players.png", "PNG")
	player_text = pytesseract.image_to_string(player_img).split("\n")
	player_text = [x for x in player_text if x.strip()]

	over_img = img.crop((600,415,660,bottom))
	over_text = pytesseract.image_to_string(over_img).split("\n")
	over_text = [x for x in over_text if x.strip()]

	under_img = img.crop((775,415,835,bottom))
	under_text = pytesseract.image_to_string(under_img).split("\n")
	under_text = [x for x in under_text if x.strip()]

	for playerIdx, player in enumerate(player_text):
		team = convertNHLTeam(player.split(")")[0].split("(")[-1])
		game = teamGame.get(team, "")
		player = parsePlayer(player.lower().split(" (")[0])
		data[game][player]["atgs"] = over_text[playerIdx]+"/"+under_text[playerIdx]

def writeCircaMain(page, data):
	page.save("outnhlmain.png", "PNG")
	img = Image.open("outnhlmain.png")
	bottom, top = 2250, 495
	left,right = 295, 1575

	game_top = top
	game_img = img.crop((left,game_top,right,game_top+75)) # l,t,r,b
	game_img.save("outnhlgame.png", "PNG")

	game_w, game_h = game_img.size
	ml_img = game_img.crop((0,0,300,game_h))
	ml_img.save("outnhlml.png", "PNG")
	ml_text = pytesseract.image_to_string(ml_img).split("\n")

	away = convertFDTeam(ml_text[0].split(" ")[0])
	home = convertFDTeam(ml_text[1].split(" ")[0])
	game = f"{away} @ {home}"
	data[game]["ml"] = ml_text[0].split(" ")[-1]+"/"+ml_text[1].split(" ")[-1]

	tot_img = game_img.crop((300,0,400,game_h))
	tot_text = pytesseract.image_to_string(tot_img).split("\n")
	line = tot_text[1].split(" ")[0].replace("%", ".5")
	data[game]["total"][line] = tot_text[0]+"/"+tot_text[1].split(" ")[-1]

	sp_img = game_img.crop((420,0,420+125,game_h))
	sp_img.save("outnhlsp.png", "PNG")
	sp_text = pytesseract.image_to_string(sp_img).split("\n")
	line = sp_text[0].split(" ")[0]
	if len(line) == 3 and line.endswith("4"):
		line = line.replace("4", ".5")
	line = str(float(line))
	data[game]["spread"][line] = sp_text[0].split(" ")[-1]+"/"+sp_text[1].split(" ")[-1]

	ml_1p_img = game_img.crop((610,0,675,game_h))
	ml_1p_text = pytesseract.image_to_string(ml_1p_img).split("\n")
	ml_1p_text = [x for x in ml_1p_text if x.strip()]
	data[game]["1p_ml"] = ml_1p_text[0]+"/"+ml_1p_text[1]

	sp_1p_img = game_img.crop((780,0,890,game_h))
	sp_1p_text = pytesseract.image_to_string(sp_1p_img).split("\n")
	line = "0.5" if sp_1p_text[0].startswith("+") else "-0.5"
	data[game]["1p_spread"][line] = sp_1p_text[0].split(" ")[-1]+"/"+sp_1p_text[1].split(" ")[-1]

	alt_sp_img = game_img.crop((980,0,1095,game_h))
	alt_sp_text = pytesseract.image_to_string(alt_sp_img).split("\n")
	line = alt_sp_text[0].split(" ")[0].replace("%", ".5")
	line = str(float(line))
	data[game]["spread"][line] = alt_sp_text[0].split(" ")[-1]+"/"+alt_sp_text[1].split(" ")[-1]

	gift_img = game_img.crop((1220,0,game_w,game_h))
	gift_text = pytesseract.image_to_string(gift_img).split("\n")
	gift_text = [x for x in gift_text if x.strip()]
	data[game]["gift"] = gift_text[0]+"/"+gift_text[1]

def writeCirca(date):
	if not date:
		date = str(datetime.now())[:10]
	with open("static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	games = schedule[date]
	teamGame = {}
	for game in games:
		a,h = map(str, game.split(" @ "))
		teamGame[a] = game
		teamGame[h] = game

	today = datetime.strptime(date, "%Y-%m-%d")
	dt = today.strftime("%Y-%-m-%-d")

	file = f"/mnt/c/Users/zhech/Downloads/NHL - {dt}.pdf"
	pages = convert_from_path(file)
	data = nested_dict()
	props = nested_dict()


	#pages = [pages[1]]
	#writeCircaMain(pages[0], data)
	writeCircaProps(pages[1], data, teamGame)

	with open("static/nhl/circa.json", "w") as fh:
		json.dump(data, fh, indent=4)
	exit()
	
	for pageIdx, page in enumerate(pages):
		page.save("outnhl.png", "PNG")
		img = Image.open("outnhl.png")

		bottom = 2200
		top = 400
		playersImg = img.crop((0,top,400,bottom))
		text = pytesseract.image_to_string(playersImg).split("\n")

		players = []
		for player in text:
			if "(" not in player:
				continue
			team = convertNHLTeam(player.split(")")[0].split("(")[-1])
			if team == "nyt":
				team = "nyi"
			elif team == "vgi":
				team = "vgk"
			elif team in ["co!", "ct"]:
				team = "col"
			game = teamGame.get(team, "")
			player = parsePlayer(player.lower().split(" (")[0])
			players.append((player, game))

		oversImg = img.crop((600,top,685,bottom))
		undersImg = img.crop((770,top,845,bottom))
		oversArr = pytesseract.image_to_string(oversImg).split("\n")
		undersArr = pytesseract.image_to_string(undersImg).split("\n")
		overs = []
		for over in oversArr:
			o = re.search(r"\d{3,4}", over)
			if not o:
				continue
			overs.append(over)
		unders = []
		for under in undersArr:
			o = re.search(r"\d{3,4}", under)
			if not o:
				continue
			unders.append(under)
		
		for p,o,u in zip(players, overs, unders):
			data[p[-1]]["atgs"][p[0]] = f"{o}/{u}".replace("\u201c", "-")

		bottom = 2060

		# l,t,r,b
		# pts -> 545,625,545+230,bottom

		w,h = img.size
		boxTop = 915

		boxW = 355 if pageIdx == 0 else 335
		boxH = 135 if pageIdx == 0 else 125

		#continue

		props = ["pts", "sog"]
		#props = ["pts"]
		for propIdx, prop in enumerate(props):
			tot = 8 if pageIdx == 0 else 10
			boxLeft = 855 if propIdx == 0 else (1230 if pageIdx == 0 else 1210)
			boxTop = 980 if pageIdx == 0 else (915 if pageIdx == 0 else 925)
			for boxIdx in range(tot):
				props_img = img.crop((boxLeft,boxTop,boxLeft+boxW,boxTop+boxH))
				props_img.save(f"outnhl-{pageIdx}-{propIdx}-{boxIdx}.png", "PNG")
				propsW,propsH = props_img.size
				player_img = props_img.crop((0,0,propsW,40))
				#player_img.save("out.png", "PNG")
				text = pytesseract.image_to_string(player_img).split("\n")

				ou_img = props_img.crop((propsW-65,propsH-100,propsW,propsH)) #l,t,r,b
				ous = pytesseract.image_to_string(ou_img).split("\n")
				#print(ous)
				o = ous[0]
				u = ous[1]

				if len(o) == 4 and o.startswith("4"):
					o = "-"+o[1:]
				if len(u) == 4 and u.startswith("7"):
					u = "-"+u[1:]
				ou = o+"/"+u
				ou = ou.replace("~", "-").replace("EVEN", "+100")

				#ho = 100 if pageIdx == 0 else 50
				to,bo,ri,le = 100,20,75,100
				if propIdx != 0:
					to,bo,ri,le = 100,20,60,105

				line_img = props_img.crop((propsW-le,propsH-to,propsW-ri,propsH-bo)) #l,t,r,b
				line_img.save(f"outnhl-{pageIdx}-{propIdx}-{boxIdx}-line.png", "PNG")
				lines = pytesseract.image_to_string(line_img, config="digits").split("\n")

				player = parsePlayer(text[0].split(" (")[0])
				team = convertNHLTeam(text[0].split(" (")[-1].split(")")[0])
				if team == "nyt":
					team = "nyi"
				elif team == "vgi":
					team = "vgk"
				elif team in ["co!", "ct"]:
					team = "col"
				game = teamGame.get(team, "")

				if pageIdx == 1 and propIdx == 1:
					print(player, lines, ous)
				line = "0.5"
				if lines[0] in ["1", "2", "3"]:
					line = lines[0]+".5"
				data[game][prop][player][line] = ou.replace("\u201c", "-")
				boxTop += boxH + 5
				#text = pytesseract.image_to_string(props_img).split("\n")

	with open("static/nhl/circa-props.json", "w") as fh:
		json.dump(data, fh, indent=4)

	if False:
		file = f"/mnt/c/Users/zhech/Downloads/NHL - {dt}.pdf"
		pages = convert_from_path(file)
		data = nested_dict()
		for page in pages:
			text = pytesseract.image_to_string(page).split("\n")

			for row in text:
				#print(row)
				pass

		with open("static/nhl/circa-main.json", "w") as fh:
			json.dump(data, fh, indent=4)

def writePointsbet(date=None):
	url = "https://api.mi.pointsbet.com/api/v2/competitions/1/events/featured?includeLive=false&page=1"
	outfile = f"nhloutPB"
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
		outfile = f"nhloutPB"
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
				prefix = "1p_"
			elif "first 3 innings" in prop:
				prefix = "2p_"
			elif "first 7 innings" in prop:
				prefix = "3p_"

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

	with open("static/nhl/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def parsePinnacle(res, games, gameId, retry, debug):
	outfile = "outnhlPN"
	game = games[gameId]

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" --connect-timeout 60 -o outnhlPN'

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
		if "special" in row:
			prop = row["units"].lower()

			if prop == "goals":
				prop = "atgs"
			elif prop == "shotsongoal":
				prop = "sog"
			elif prop == "assists":
				prop = "ast"
			elif prop == "points":
				prop = "pts"
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

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(gameId)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" --connect-timeout 60 -o outnhlPN'

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
		try:
			keys = row["key"].split(";")
		except:
			continue

		prefix = ""

		overId = underId = 0
		player = ""
		if keys[1] == "1":
			prefix = "1p_"
		if keys[1] == "2":
			prefix = "2p_"
		elif keys[1] == "3":
			prefix = "3p_"
		elif keys[1] == "6":
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
				if keys[1] == "6":
					prop = f"3-way"
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

			if "points" in prices[0] and prop not in []:
				handicap = str(float(prices[switched]["points"]))
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
				handicap = str(float(prices[switched]["points"]))
				#if game == "tor @ tb" and prop == "spread" and handicap == "1.0":
				#	print(row)
				if prop not in res[game]:
					res[game][prop] = {}

				res[game][prop][handicap] = ou
			else:
				res[game][prop] = ou

def writePinnacle(date, debug):

	if not date:
		date = str(datetime.now())[:10]

	url = "https://www.pinnacle.com/en/hockey/nhl/matchups#period:0"

	league ="1456"

	url = 'curl -s "https://guest.api.arcadia.pinnacle.com/0.1/leagues/'+league+'/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" --connect-timeout 60 -o outnhlPN'

	os.system(url)
	outfile = f"outnhlPN"
	with open(outfile) as fh:
		data = json.load(fh)

	games = {}
	for row in data:
		if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
		if row["type"] == "matchup" and not row["parent"]:
			player1 = row["participants"][0]["name"].lower()
			player2 = row["participants"][1]["name"].lower()
			games[str(row["id"])] = f"{convertFDTeam(player2)} @ {convertFDTeam(player1)}"

	#games = {'1607444353': 'tor @ tb'}

	res = {}
	retry = []
	for gameId in games:
		parsePinnacle(res, games, gameId, retry, debug)

	for gameId in retry:
		parsePinnacle(res, games, gameId, retry, debug)

	with open("static/nhl/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBV():
	url = "https://www.bovada.lv/sports/hockey/nhl"

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/hockey/nhl?marketFilterId=def&liveOnly=False&eventsLimit=5000&lang=en"
	outfile = f"nhloutBV"

	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	ids = [r["link"] for r in data[0]["events"]]

	#ids = ["/hockey/nhl/dallas-stars-detroit-red-wings-202401231900"]

	res = {}
	for link in ids:
		if "goals" in link:
			continue
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)

		os.system(f"curl \"{url}\" --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0' -H 'Accept: application/json, text/plain, */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://www.bovada.lv/' -H 'X-CHANNEL: desktop' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' -H 'X-SPORT-CONTEXT: ' -H 'Connection: keep-alive' -H 'Cookie: Device-Type=Desktop|false; LANG=en; AB=variant; VISITED=true; affid=14995; JOINED=true; url-prefix=/; ln_grp=1; odds_format=AMERICAN; TSD4E5KQ1M=T5mCLsoZdxfxCbEQD4qVATcG0sKVJAEQ; variant=v:0|lgn:0|dt:d|os:w|cntry:US|cur:USD|jn:1|rt:o|pb:0; JSESSIONID=79EAD6CF313245D69DB5B4BAFE4325BF; TS01ed9118=014b5d5d077747c6c55fa8f9f0eed7c4ffb9827efa99f5edf3213c3de6b0106b0501b972a707dab0397a11c3f2813e791df962eca970ba71e00ace4d692d2fb3aee5d1cc0c7696d376fab4329dbde7037083ba5f81342b1138c2b7fc149c52438ad4a4c5cc' -H 'TE: trailers' -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		#print(url)

		comp = data[0]['events'][0]['competitors']
		game = data[0]['events'][0]['description'].lower()
		if "@" not in game:
			continue
		fullAway, fullHome = game.split(" @ ")
		game = f"{convertFDTeam(fullAway)} @ {convertFDTeam(fullHome)}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "player props", "goalscorers", "shots on goal", "period props"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["description"].lower() == "1st period":
						prefix = "1p_"
					elif market["period"]["description"].lower() == "2nd period":
						prefix = "2p_"
					elif market["period"]["description"].lower() == "3rd period":
						prefix = "3p_"

					prop = market["description"].lower()
					if prop == "moneyline":
						prop = "ml"
					elif prop == "3-way moneyline":
						prop = "3-way"
					elif prop == "total":
						prop = "total"
						if market["period"]["abbreviation"] == "RT":
							continue
					elif prop == "spread":
						prop = "spread"
						if market["period"]["abbreviation"] == "RT":
							continue
					elif prop == f"total goals o/u - {fullAway}":
						prop = "away_total"
					elif prop == f"total goals o/u - {fullHome}":
						prop = "home_total"
					elif prop == "anytime goalscorer":
						prop = "atgs"
					elif prop == "player to score 1st goal":
						prop = "fgs"
					elif prop.startswith("total saves"):
						prop = "saves"
					elif prop.startswith("total shots on goal"):
						prop = "sog"
					elif prop.startswith("player to record"):
						if "powerplay" in prop:
							prop = "pp_pts"
						elif "points" in prop:
							prop = "pts"
						elif "assists" in prop:
							prop = "ast"
					elif "9m 59s" in prop:
						prop = "gift"
					elif "4m 59s" in prop:
						prop = "giff"
					else:
						continue

					prop = f"{prefix}{prop}"

					if prop.startswith("1p_gif"):
						prop = prop[3:]

					if not len(market["outcomes"]):
						continue

					if "ml" not in prop and prop not in res[game]:
						res[game][prop] = {}

					if "ml" in prop or "3-way" in prop or "giff" in prop or "gift" in prop:
						res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
					elif "total" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
								if market["outcomes"][i]["description"] == "Under":
									ou = f"{market['outcomes'][i+1]['price']['american']}/{market['outcomes'][i]['price']['american']}".replace("EVEN", "100")
								handicap = market["outcomes"][i]["price"]["handicap"]
							except:
								continue
							#print(handicap, ou)
							res[game][prop][handicap] = ou
					elif "spread" in prop:
						for i in range(0, len(market["outcomes"]), 2):
							try:
								ou = f"{market['outcomes'][i]['price']['american']}/{market['outcomes'][i+1]['price']['american']}".replace("EVEN", "100")
							except:
								continue
							handicap = market["outcomes"][i]["price"]["handicap"]
							res[game][prop][handicap] = ou
					elif prop in ["saves", "sog"]:
						try:
							handicap = market["outcomes"][0]["price"]["handicap"]
							player = parsePlayer(market["description"].split(" - ")[-1].split(" (")[0])
							ou = f"{market['outcomes'][0]['price']['american']}"
							if len(market["outcomes"]) > 1:
								ou += f"/{market['outcomes'][1]['price']['american']}"
							res[game][prop][player] = {
								handicap: f"{ou}".replace("EVEN", "100")
							}
						except:
							continue
					else:
						for i in range(0, len(market["outcomes"]), 1):
							player = parsePlayer(market['outcomes'][i]["description"].split(" - ")[-1].split(" (")[0])
							player = " ".join([x for x in player.split(" ") if x])
							if not player:
								continue

							ou = f"{market['outcomes'][i]['price']['american']}".replace("EVEN", "100")
							if prop in ["atgs", "fgs"]:
								res[game][prop][player] = ou
							else:
								handicap = str(float(market["description"].split(" ")[3].replace("+", "")) - 0.5)
								if player not in res[game][prop]:
									res[game][prop][player] = {}
								res[game][prop][player][handicap] = ou


	with open("static/nhl/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeMGM(date=None):

	res = {}

	if not date:
		date = str(datetime.now())[:10]

	url = "https://sports.mi.betmgm.com/en/sports/hockey-12/betting/usa-9/nhl-34"

	url = f"https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata?layoutSize=Large&page=CompetitionLobby&sportId=12&regionId=9&competitionId=34&compoundCompetitionId=1:34&widgetId=/mobilesports-v1.0/layout/layout_us/modules/competition/defaultcontainereventsfutures-redesign&shouldIncludePayload=true"
	outfile = f"outMGM"

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

		if str(datetime.strptime(row["startDate"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
		ids.append(row["id"])

	#ids = ["14476196"]
	for mgmid in ids:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=true"
		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' \"{url}\" --connect-timeout 30 -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		data = data["fixture"]

		if " at " not in data["name"]["value"]:
			continue
		game = strip_accents(data["name"]["value"].lower()).replace(" at ", " @ ")
		fullTeam1, fullTeam2 = game.split(" @ ")
		game = f"{convertFDTeam(fullTeam1)} @ {convertFDTeam(fullTeam2)}"

		res[game] = {}
		for row in data["games"]:
			prop = row["name"]["value"].lower()

			prefix = player = ""
			if "1st period" in prop:
				prefix = "1p_"
			elif "2nd period" in prop:
				prefix = "2p_"
			elif "3rd period" in prop:
				prefix = "3p_"

			if prop.endswith("money line"):
				prop = "ml"
			elif "totals" in prop:
				prop = "total"
			elif "spread" in prop:
				prop = "spread"
			elif "3-way" in prop:
				prop = "3-way"
			elif prop == "goalscorer (including overtime)":
				prop = "atgs"
			elif prop == "first goalscorer in match (including overtime)":
				prop = "fgs"
			elif "how many saves" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "saves"
			elif "how many shots" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "sog"
			elif "how many points" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "pts"
			elif "how many powerplay points" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "pp_pts"
			elif "how many assists" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "ast"
			elif "how many blocked shots" in prop:
				player = prop.split(" will ")[-1].split(" (")[0]
				prop = "bs"
			else:
				continue

			prop = prefix+prop

			results = row['results']
			if "ml" in prop:
				res[game][prop] = f"{results[0]['americanOdds']}/{results[1]['americanOdds']}"
			elif "3-way" in prop:
				res[game][prop] = f"{results[0]['americanOdds']}/{results[-1]['americanOdds']}"
			elif len(results) >= 2:
				if prop not in res[game]:
					res[game][prop] = {}
				skip = 1 if prop in ["atgs", "fgs"] else 2
				for idx in range(0, len(results), skip):
					val = results[idx]["name"]["value"].lower()
					if "over" not in val and "under" not in val and "spread" not in prop and prop not in ["atgs", "fgs"]:
						continue
					elif prop not in ["atgs", "fgs"]:
						val = val.split(" ")[-1]
					
					#print(game, prop, player)
					ou = f"{results[idx]['americanOdds']}"

					try:
						if skip == 2:
							ou += f"/{results[idx+1]['americanOdds']}"
					except:
						pass

					if player:
						player = parsePlayer(player)
						res[game][prop][player] = {
							val: ou
						}
					elif prop in ["atgs", "fgs"]:
						res[game][prop][parsePlayer(val)] = ou
					else:
						try:
							v = str(float(val))
							res[game][prop][v] = ou
						except:
							pass

	with open("static/nhl/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi(date=None):
	if not date:
		date = str(datetime.now())[:10]
	data = {}
	outfile = f"outnhl.json"

	url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/ice_hockey/nhl"

	league = "nhl"
	url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/ice_hockey/{league}/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -s \"{url}\" --connect-timeout 30 -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	fullTeam = {}
	eventIds = {}
	for event in j["events"]:
		if event["event"]["state"] == "STARTED":
			continue
		game = event["event"]["name"].lower()
		away, home = map(str, game.split(" @ "))
		homeFull, awayFull = map(str, event["event"]["englishName"].lower().split(" - "))
		games = []
		for team, full in zip([away, home], [awayFull, homeFull]):
			t = team.split(" ")[0]
			if t == "vgs":
				t = "vgk"
			elif "rangers" in team:
				t = "nyr"
			elif "islanders" in team:
				t = "nyi"
			fullTeam[t] = full
			games.append(t)
		game = " @ ".join(games)
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]
		data[game] = {}

	#eventIds = {'dal @ det': 1019881390}
	#data['dal @ det'] = {}
	#print(eventIds)
	#exit()

	for game in eventIds:
		away, home = map(str, game.split(" @ "))
		awayFull, homeFull = fullTeam[away], fullTeam[home]
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -s \"{url}\" --connect-timeout 30 -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		if not j["betOffers"] or "closed" not in j["betOffers"][0]:
			continue

		if str(datetime.strptime(j["betOffers"][0]["closed"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=5))[:10] != date:
			continue

		i = 0
		for betOffer in j["betOffers"]:
			playerProp = False
			label = betOffer["criterion"]["label"].lower()
			prefix = ""
			if "period 1" in label:
				prefix = "1p_"
			elif "period 2" in label:
				prefix = "2p_"
			elif "period 3" in label:
				prefix = "3p_"

			if "handicap" in label:
				if "regular time" in label:
					continue
				label = "spread"
			elif f"total goals by {awayFull}" in label:
				label = "away_total"
			elif f"total goals by {homeFull}" in label:
				label = "home_total"
			elif "total goals" in label:
				if "odd/even" in label or "regular time" in label:
					continue
				if "4:59" in label:
					label = "giff"
				elif "9:59" in label:
					label = "gift"
				else:
					label = "total"
			elif label == "match":
				label = "ml"
			elif label == "match odds":
				label = "3-way"
			elif label == "first team to score":
				label = "first_score"
			elif label == "to score - including overtime":
				label = "atgs"
				playerProp = True
			elif label == "first goal scorer - including overtime":
				label = "fgs"
				playerProp = True
			elif "points - " in label:
				label = "pts"
				playerProp = True
			elif "power play point - " in label:
				label = "pp_pts"
				playerProp = True
			elif "by the player" in label:
				playerProp = True
				label = "_".join(label.split(" by the player")[0].split(" "))

				if label == "shots_on_goal":
					label = "sog"
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
				player = parsePlayer(betOffer["outcomes"][0]["participant"])
				try:
					last, first = map(str, player.split(", "))
					player = parsePlayer(f"{first} {last}")
				except:
					pass
			if "ml" in label:
				data[game][label] = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label == "3-way":
				data[game][label] = betOffer["outcomes"][-1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
			elif label in ["gift", "giff"]:
				if str(betOffer["outcomes"][0]["line"] / 1000) == "0.5":
					data[game][label] = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][-1]["oddsAmerican"]
			else:
				if label not in data[game]:
					data[game][label] = {}
				if not playerProp:
					#print(betOffer["criterion"]["label"], label)
					line = str(betOffer["outcomes"][0]["line"] / 1000)
					if betOffer["outcomes"][0]["label"] == "Under" or convertFDTeam(betOffer["outcomes"][0]["label"].lower()) == home:
						line = str(float(line) * -1)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]

					data[game][label][line] = ou
				elif label == "fgs":
					for outcome in betOffer["outcomes"]:
						player = parsePlayer(outcome["participant"])
						try:
							last, first = map(str, player.split(", "))
							player = parsePlayer(f"{first} {last}")
							data[game][label][player] = outcome["oddsAmerican"]
						except:
							continue
				else:
					if label in ["sog"]:
						line = betOffer["outcomes"][0]["label"].split(" ")[-1]
					else:
						try:
							line = str(betOffer["outcomes"][0]["line"] / 1000)
						except:
							line = "0.5"
					if betOffer["outcomes"][0]["label"].split(" ")[0] in ["Under", "No"]:
						if label not in ["sog"]:
							line = str(betOffer["outcomes"][1]["line"] / 1000)
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]

					if player not in data[game][label]:
						data[game][label][player] = {}

					if label in ["atgs"]:
						line = "0.5"
					elif label in ["pts"]:
						line = str(float(line) - 0.5)
					data[game][label][player][line] = ou


	with open(f"static/nhl/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

def writeOnlyGoals2():

	goals = {}

	date = "2024-10-10"

	with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/hockeyreference/parsed.json") as fh:
		parsed = json.load(fh)

	for game in boxscores[date]:
		gameId = boxscores[date][game].split("/")[5]
		if gameId in parsed:
			continue
		url = f"https://www.espn.com/nhl/boxscore/_/gameId/{gameId}"
		if gameId != "401687618":
			continue
			pass
		outfile = "outnhl"
		time.sleep(0.2)
		os.system(f"curl \"{url}\" -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")

		js = "{}"
		for script in soup.find_all("script"):
			if "window['__CONFIG__']=" in script.text:
				m = re.search(r"window['__CONFIG__']={(.*?)};", script.text)
				if m:
					js = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
					js = f"{{{js}}}"
					break

		js = eval(js)

		with open("out", "w") as fh:
			json.dump(js, fh, indent=4)
		exit()

		gameOver = "Final" in soup.find("div", class_="pageContent").find("div", class_="ScoreCell__Time").text
		if gameOver:
			parsed[gameId] = True

		for table in soup.find("div", class_="tabs__content").find_all("table"):
			period = table.find("tbody").find("th").text.split(" ")[0]
			for tr in table.find("tbody").find_all("tr"):
				ast = ""
				if "assists" in tr.find_all("td")[2].text.lower():
					ast = [parsePlayer(p.split(" (")[0]) for p in tr.find_all("td")[2].text.split(": ")[-1].split(", ")]
				goals.append({
					"time": tr.find("td").text,
					"goal": parsePlayer(tr.find_all("td")[2].text.split(" (")[0]),
					"ast": ",".join(ast),
					"score": tr.find_all("td")[-2].text+"-"+tr.find_all("td")[-1].text,
					"game": game,
					"period": period
				})

	with open(f"{prefix}static/nhl/goals/{date}.json", "w") as fh:
		json.dump(goals, fh, indent=4)

	with open(f"{prefix}static/hockeyreference/parsed.json", "w") as fh:
		json.dump(parsed, fh, indent=4)

@nhl_blueprint.route('/goals')
def goals_route():
	date = request.args.get("date")
	if not date:
		date = str(datetime.now())[:10]

	with open(f"{prefix}static/nhl/goals/{date}.json") as fh:
		data = json.load(fh)
	res = []
	for rowId in data:
		row = data[rowId]
		row["game"] = row["game"].upper()
		row["goal"] = row["goal"].title()
		row["ast"] = row["ast"].title()
		if row['period'] == "OT":
			row["time"] = f"OT {row['time']}"
		else:
			row["time"] = f"{row['period'][0]}p {row['time']}"
		res.append(row)
	return render_template("goals.html", data=res)

def writeOnlyGoals(date=None):
	if not date:
		date = str(datetime.now())[:10]

	goals = {}

	with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/hockeyreference/parsed.json") as fh:
		parsed = json.load(fh)

	for game in boxscores[date]:
		gameId = boxscores[date][game].split("/")[5]
		if gameId in parsed:
			continue
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
		outfile = "outnhl"
		time.sleep(0.2)
		os.system(f"curl \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		for play in data["plays"]:
			if play["type"]["id"] == "522":
				parsed[gameId] = True
			elif play["type"]["id"] == "505":
				players = play["participants"]
				player = parsePlayer(players[0]["athlete"]["displayName"])
				goals[play["id"]] = {
					"goal": player,
					"ast": ",".join([parsePlayer(p["athlete"]["displayName"]) for p in players[1:]]),
					"dt": str(datetime.strptime(play["wallclock"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=7)),
					"period": play["period"]["displayValue"],
					"time": play["clock"]["displayValue"],
					"score": f"{play['awayScore']}-{play['homeScore']}",
					"game": game
				}

	with open(f"{prefix}static/nhl/goals/{date}.json", "w") as fh:
		json.dump(goals, fh, indent=4)

	with open(f"{prefix}static/hockeyreference/parsed.json", "w") as fh:
		json.dump(parsed, fh, indent=4)

def writeFanduelManual():
	js = """

	let data = {};
	{

		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.toLowerCase().substring(0, 3);
			if (t == "was") {
				t = "wsh";
			} else if (t == "cal") {
				t = "cgy";
			} else if (t == "col" && team.indexOf("columbus") >= 0) {
				t = "cbj";
			} else if (t == "flo") {
				t = "fla";
			} else if (t == "los") {
				t = "la";
			} else if (t == "nas") {
				t = "nsh";
			} else if (t == "mon") {
				t = "mtl";
			} else if (t == "new") {
				t = "nj";
				if (team.indexOf("rangers") > 0) {
					t = "nyr";
				} else if (team.indexOf("island") > 0) {
					t = "nyi";
				}
			} else if (t == "san") {
				t = "sj";
			} else if (t == "tam") {
				t = "tb";
			} else if (t == "st.") {
				t = "stl";
			} else if (t == "veg") {
				t = "vgk";
			} else if (t == "win") {
				t = "wpg";
			}
			return t;
		}

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
			if (player == "michael eyssimont") {
				return "mikey eyssimont";
			}
			return player;
		}

		let game = document.querySelector("h1").innerText.toLowerCase().replace(" odds", "").replace(" at ", " @ ");
		let awayFull = game.split(" @ ")[0];
		let homeFull = game.split(" @ ")[1];
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
			} else if (label.indexOf("any time goal scorer") >= 0) {
				if (label.indexOf("period") >= 0) {
					continue;
				}
				prop = "atgs";
			} else if (document.querySelector("h1").innerText.indexOf("Goal Scorer") >= 0) {
				if (label.indexOf("total goals") >= 0) {
					prop = "atgs";
				}
				player = parsePlayer(label.split(" total goals")[0]);
			} else if (label.indexOf("first goal scorer") >= 0) {
				prop = "fgs";
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
				//prop = "total";
			} else if (label.indexOf("total saves") >= 0) {
				player = parsePlayer(label.split(" -")[0]);
				prop = "saves";
			} else if (label.indexOf("shots on goal") >= 0) {
				if (label.indexOf("period") >= 0 || label.indexOf("combined") >= 0 || label.indexOf("first to 5") >= 0) {
					continue;
				}
				player = parsePlayer(label.split(" shots")[0]);
				prop = "sog";
			} else if (label.indexOf(awayFull+" total goals") >= 0) {
				prop = "away_total";
			} else if (label.indexOf(homeFull+" total goals") >= 0) {
				prop = "home_total";
			} else if (label == "1st period goal in first five minutes") {
				prop = "giff";
			} else if (label == "1st period goal in first ten minutes") {
				prop = "gift";
			} else if (label == "1st period total goals") {
				prop = "1p_total";
			}

			if (!prop) {
				continue;
			}

			if (arrow.querySelector("svg[data-test-id=ArrowActionIcon]").querySelector("path").getAttribute("d").split(" ")[0] != "M.147") {
				arrow.click();
			}
			let el = arrow.parentElement.parentElement.parentElement.querySelector("div[aria-label='Show more']");
			if (el) {
				el.click();
			}

			if (prop != "lines" && !data[game][prop]) {
				data[game][prop] = {};
			}

			let skip = 1;
			if (["saves", "away_total", "home_total", "gift", "giff", "1p_total"].indexOf(prop) >= 0) {
				skip = 2;
			} else if (prop == "sog" && player) {
				skip = 2;
			} else if (prop == "atgs" && player) {
				skip = 2;
			}
			let btns = Array.from(li.querySelectorAll("div[role=button]"));
			btns.shift();

			if (prop == "lines") {
				if (btns[1].getAttribute("aria-label").split(", ")[1]) {
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
				if (ariaLabel == "Show more" || ariaLabel == "Show less") {
					continue;
				}
				let odds = ariaLabel.split(", ")[1];
				if (!odds || odds.indexOf("unavailable") >= 0) {
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
					line = ariaLabel.split(", ")[2];
					odds = ariaLabel.split(", ")[3];
					if (odds.indexOf("unavailable") >= 0) {
						continue;
					}
					if (prop == "atgs") {
						if (line == "0.5") {
							data[game][prop][player] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[3];
						}
					} else {
						data[game][prop][player][line] = odds + "/" + btns[i+1].getAttribute("aria-label").split(", ")[3];
					}
				} else if (["giff", "gift"].indexOf(prop) >= 0) {
					data[game][prop] = btns[i].getAttribute("aria-label").split(", ")[2] + "/" + btns[i+1].getAttribute("aria-label").split(", ")[2];
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

					if (["atgs", "fgs"].indexOf(prop) >= 0) {
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
	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.getElementsByTagName("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/ice-hockey/nhl") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && (time.innerText.split(" ")[0] === "MON" || time.innerText.split(" ").length < 3)) {
					urls[a.href] = 1;
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/new-york-rangers-@-boston-bruins-33125260",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/new-york-islanders-@-detroit-red-wings-33125403",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/philadelphia-flyers-@-carolina-hurricanes-33125395",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/winnipeg-jets-@-new-jersey-devils-33125407",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/st.-louis-blues-@-ottawa-senators-33125413",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/nashville-predators-@-florida-panthers-33125419",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/buffalo-sabres-@-edmonton-oilers-33125439",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/chicago-blackhawks-@-anaheim-ducks-33125801",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/montreal-canadiens-@-vancouver-canucks-33125800",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/seattle-kraken-@-vegas-golden-knights-33125847",
    "https://sportsbook.fanduel.com/ice-hockey/nhl---matches/tampa-bay-lightning-@-san-jose-sharks-33125845"
]

	#games = ["https://sportsbook.fanduel.com/ice-hockey/nhl---matches/new-york-rangers-@-boston-bruins-33125260"]
	lines = {}
	for game in games:	
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		away, home = map(str, game.split(" @ "))
		game = f"{convertFDTeam(away)} @ {convertFDTeam(home)}"
		lines[game] = {}

		outfile = "outnhlfd"

		#for tab in ["", "points-assists", "shots"]:
		for tab in ["goal-scorer"]:
			time.sleep(0.6)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			#url = f"https://boapi.sportsbook.fanduel.com/popular/events/{gameId}?_ak=FhMFpcPWXMeyZxOx"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			with open("out", "w") as fh:
				json.dump(data, fh, indent=4)

			if "markets" not in data["attachments"]:
				continue

			if data["attachments"]["events"][str(gameId)]["inPlay"]:
				if game in lines:
					del lines[game]
				continue

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				runners = data["attachments"]["markets"][market]["runners"]

				if marketName in ["moneyline", "any time goal scorer"] or "3 way" in marketName or "total goals" in marketName or "puck line" in marketName or marketName.startswith("alternate") or marketName.startswith("player to record") or marketName.endswith("saves") or "shots on goal" in marketName:

					if "parlay" in marketName:
						continue

					prefix = ""
					if "1st period" in marketName:
						prefix = "1p_"
					elif "2nd period" in marketName:
						prefix = "2p_"
					elif "3rd period" in marketName:
						prefix = "3p_"

					alt = False
					prop = ""
					playerHandicap = ""
					if "moneyline" in marketName or "money line" in marketName:
						if "/" in marketName:
							continue
						prop = "ml"
					elif "3 way" in marketName:
						prop = "3-way"
					elif "alternate" in marketName:
						alt = True
						prop = "total"
						if "puck line" in marketName:
							prop = "spread"
					elif "total goals" in marketName:
						if "flat line" in marketName:
							continue
						if marketName == f"{away} total goals":
							prop = "away_total"
						elif marketName == f"{home} total goals":
							prop = "home_total"
						else:
							prop = "total"
					elif "puck line" in marketName:
						prop = "spread"
					elif marketName.endswith("saves"):
						prop = "saves"
					elif marketName == "any time goal scorer":
						prop = "atgs"
						alt = True
					elif "shots on goal" in marketName:
						prop = "sog"
						if marketName.startswith("player to"):
							alt = True
							playerHandicap = str(float(marketName.split(" ")[-4][:-1]) - 0.5)
					elif marketName.endswith("assists"):
						prop = "ast"
						playerHandicap = str(float(marketName.split(" ")[-2][:-1]) - 0.5)
						alt = True
					elif marketName.endswith("points"):
						prop = "pts"
						alt = True
						if "power" in marketName:
							prop = "pp_pts"
							playerHandicap = "0.5"
						else:
							playerHandicap = str(float(marketName.split(" ")[-2][:-1]) - 0.5)
					elif " - " in marketName:
						marketName = marketName.split(" - ")[-1]
						prop = "_".join(marketName.split(" "))
					else:
						continue

					prop = f"{prefix}{prop}"

					handicap = runners[0]["handicap"]
					skip = 1 if alt else 2
					try:
						ou = str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
						if skip == 2:
							ou += "/"+str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
					except:
						continue

					if runners[0]["runnerName"] == "Under":
						ou = str(runners[1]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])+"/"+str(runners[0]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])

					if "ml" not in prop:
						if prop not in lines[game]:
							lines[game][prop] = {}

					if "ml" in prop:
						lines[game][prop] = ou
					elif "3-way" in prop:
						lines[game][prop] = f"{runners[0]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[-1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"
					elif prop in ["saves"]:
						player = parsePlayer(marketName.split(" - ")[0])
						lines[game][prop][player] = {
							handicap: ou
						}
					elif prop in ["sog", "pts", "ast", "pp_pts"]:
						for i in range(0, len(runners), skip):
							player = parsePlayer(runners[i]["runnerName"].split(" - ")[0])
							if player not in lines[game][prop]:
								lines[game][prop][player] = {}
							if playerHandicap:
								lines[game][prop][player][playerHandicap] = str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							else:
								handicap = runners[i]["handicap"]
								lines[game][prop][player][handicap] = f"{runners[i]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"
					else:
						for i in range(0, len(runners), skip):
							handicap = str(runners[i]["handicap"])
							try:
								odds = str(runners[i]["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"])
							except:
								continue
							if alt:
								if "spread" in prop or "total" in prop:
									handicap = float(runners[i]["runnerName"].split(" ")[-1].replace("(", "").replace(")", ""))
									if "spread" in prop and runners[i]["result"].get("type", "") == "HOME" or " ".join(runners[i]["runnerName"].lower().split(" ")[:-1]) == home:
										handicap *= -1
									handicap = str(handicap)
								else:
									handicap = parsePlayer(runners[i]["runnerName"])

								if handicap not in lines[game][prop]:
									lines[game][prop][handicap] = odds
									if "total" not in prop and "spread" not in prop:
										lines[game][prop][handicap] = odds
								else:
									if runners[i]["runnerName"].startswith("Under") or runners[i]["result"].get("type", "") == "HOME" or " ".join(runners[i]["runnerName"].lower().split(" ")[:-1]) == home:
										if len(lines[game][prop][handicap].split("/")) == 2:
											if int(odds) > int(lines[game][prop][handicap].split("/")[-1]):
												lines[game][prop][handicap] = f"{lines[game][prop][handicap].split('/')[0]}/{odds}"

										else:
											lines[game][prop][handicap] += f"/{odds}"
									else:
										if len(lines[game][prop][handicap].split("/")) == 2:
											if int(odds) > int(lines[game][prop][handicap].split("/")[0]):
												lines[game][prop][handicap] = f"{odds}/{lines[game][prop][handicap].split('/')[-1]}"
										else:
											lines[game][prop][handicap] = f"{odds}/{lines[game][prop][handicap]}"
							elif "spread" in prop or "total" in prop:
								lines[game][prop][handicap] = ou
							else:
								if "over" in runners[i]["runnerName"].lower() or "under" in runners[i]["runnerName"].lower():
									player = parsePlayer(runners[i]["runnerName"].replace(" Over", "").replace(" Under", ""))
								else:
									player = parsePlayer(runners[i]["runnerName"].lower())
								lines[game][prop][player] = {
									handicap: ou
								}
	
	with open(f"static/nhl/fanduel.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr", sharp=False, book=""):

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

	if prop == "fgs":
		fairVal = impliedOver
		x = 0.4354
		ev = ((100 * (finalOdds / 100 + 1)) * fairVal - 100 + (100 * x))
		ev = round(ev, 1)


		#mult = impliedOver
		#ev = mult * profit + (1-mult) * -1 * bet
		#ev = round(ev, 1)
		if player not in evData:
			evData[player] = {}
		evData[player][f"{prefix}fairVal"] = 0
		evData[player][f"{prefix}implied"] = 0
		
		evData[player][f"{prefix}ev"] = ev
		return

	if "/" not in ou:
		u = 1.07 - impliedOver
		if u >= 1:
			#print(player, ou, finalOdds, impliedOver)
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

	if book:
		prefix = book+"_"

	if player not in evData:
		evData[player] = {}
	evData[player][f"{prefix}fairVal"] = fairVal
	evData[player][f"{prefix}implied"] = implied
	evData[player][f"{prefix}ev"] = ev

def writeDK(date=None, keep=False):
	url = "https://sportsbook.draftkings.com/leagues/hockey/nfl"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 496,
		"goalscorer": 1190,
		"sog": 1189,
		"player": 550,
		"goalie": 1064,
		"team totals": 1193,
		"quick hits": 1259,
		"points": 1675,
		"assists": 1676,
		"bs": 1679,
		"1st period": 548
	}
	
	subCats = {
		496: [4525, 4999, 13192, 13189],
		1064: [16550],
		1190: [13808],
		1189: [16544, 12040],
		548: [4761],
		550: [14305],
		1193: [12055],
		1259: [13750],
		1675: [16545, 16213],
		1676: [16546, 16215],
	}

	propIds = {
		4999: "3-way", 13808: "atgs", 14496: "fgs", 16544: "sog-alt", 12040: "sog", 13189: "spread", 13192: "total", 10284: "goals_against", 12436: "shutout", 14305: "bs", 13750: "gift", 16545: "pts-alt", 16213: "pts", 16546: "ast-alt", 16215: "ast", 16550: "saves"
	}

	if False:
		mainCats = {
			"goalscorer": 1190,
		}

		subCats = {
			1190: [13808],
		}

	cookie = """-H 'Cookie: hgg=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWQiOiI0ODg5Mjc3MDkxOCIsImRraC0xMjYiOiI4MzNUZF9ZSiIsImRrZS0xMjYiOiIwIiwiZGtlLTIwNCI6IjcxMCIsImRrZS0yODgiOiIxMTI4IiwiZGtlLTMxOCI6IjEyNjAiLCJka2UtMzQ1IjoiMTM1MyIsImRrZS0zNDYiOiIxMzU2IiwiZGtlLTQyOSI6IjE3MDUiLCJka2UtNzAwIjoiMjk5MiIsImRrZS03MzkiOiIzMTQwIiwiZGtlLTc1NyI6IjMyMTIiLCJka2UtODA2IjoiMzQyNiIsImRrZS04MDciOiIzNDM3IiwiZGtlLTgyNCI6IjM1MTEiLCJka2UtODI1IjoiMzUxNCIsImRrZS04MzYiOiIzNTcwIiwiZGtoLTg5NSI6IjhlU3ZaRG8wIiwiZGtlLTg5NSI6IjAiLCJka2UtOTAzIjoiMzg0OCIsImRrZS05MTciOiIzOTEzIiwiZGtlLTk0NyI6IjQwNDIiLCJka2UtOTc2IjoiNDE3MSIsImRraC0xNjQxIjoiUjBrX2xta0ciLCJka2UtMTY0MSI6IjAiLCJka2UtMTY1MyI6IjcxMzEiLCJka2UtMTY4NiI6IjcyNzEiLCJka2UtMTY4OSI6IjcyODciLCJka2UtMTc1NCI6Ijc2MDUiLCJka2UtMTc2MCI6Ijc2NDkiLCJka2UtMTc3NCI6Ijc3MTAiLCJka2UtMTc4MCI6Ijc3MzAiLCJka2UtMTc5NCI6Ijc4MDEiLCJka2gtMTgwNSI6Ik9Ha2Jsa0h4IiwiZGtlLTE4MDUiOiIwIiwiZGtlLTE4MjgiOiI3OTU2IiwiZGtlLTE4NjEiOiI4MTU3IiwiZGtlLTE4NjgiOiI4MTg4IiwiZGtlLTE4ODMiOiI4MjQyIiwiZGtlLTE4OTgiOiI4MzE0IiwiZGtoLTE5NTIiOiJhVWdlRFhiUSIsImRrZS0xOTUyIjoiMCIsImRrZS0yMDYyIjoiOTA0OCIsImRrZS0yMDk3IjoiOTIwNSIsImRrZS0yMTAwIjoiOTIyMyIsImRrZS0yMTAzIjoiOTI0MiIsImRrZS0yMTM1IjoiOTM5MyIsImRrZS0yMTM4IjoiOTQyMCIsImRrZS0yMTQxIjoiOTQzNSIsImRraC0yMTUwIjoiTmtiYVNGOGYiLCJka2UtMjE1MCI6IjAiLCJka2UtMjE2MSI6Ijk1MTUiLCJka2UtMjE2NSI6Ijk1MzUiLCJka2UtMjE4NyI6Ijk2MjQiLCJka2UtMjE5MiI6Ijk2NTIiLCJka2UtMjE5NSI6Ijk2NjUiLCJka2UtMjIwNyI6Ijk3MDkiLCJka2UtMjIxMSI6Ijk3MjciLCJka2UtMjIxNiI6Ijk3NDUiLCJka2UtMjIxNyI6Ijk3NTEiLCJka2UtMjIyMCI6Ijk3NjkiLCJka2UtMjIyMiI6Ijk3NzQiLCJka2UtMjIyNCI6Ijk3ODQiLCJka2gtMjIyNiI6IktlZE1ybUZPIiwiZGtlLTIyMjYiOiIwIiwiZGtlLTIyMzciOiI5ODM1IiwiZGtlLTIyMzgiOiI5ODM3IiwiZGtlLTIyNDAiOiI5ODU3IiwiZGtlLTIyNDEiOiI5ODY1IiwiZGtlLTIyNDMiOiI5ODcyIiwiZGtlLTIyNDQiOiI5ODc3IiwiZGtlLTIyNDYiOiI5ODg3IiwiZGtoLTIyNTgiOiJRd1BaT0tVNiIsImRrZS0yMjU4IjoiMCIsImRraC0yMjU5IjoibzFoSnN1Z1MiLCJka2UtMjI1OSI6IjAiLCJka2UtMjI2NCI6Ijk5NzAiLCJka2UtMjI2OSI6Ijk5ODkiLCJka2UtMjI3MCI6Ijk5OTIiLCJka2UtMjI3NyI6IjEwMDE5IiwiZGtlLTIyNzkiOiIxMDAzMyIsImRrZS0yMjgwIjoiMTAwMzUiLCJka2UtMjI4MSI6IjEwMDQyIiwiZGtlLTIyODgiOiIxMDA5MiIsImRrZS0yMjg5IjoiMTAwOTciLCJka2UtMjI5MSI6IjEwMTAzIiwiZGtoLTIyOTIiOiJNbHdDUVFVTSIsImRrZS0yMjkyIjoiMCIsImRrZS0yMjkzIjoiMTAxMjQiLCJka2UtMjI5NCI6IjEwMTI2IiwiZGtlLTIzMDAiOiIxMDE3NSIsImRrZS0yMzAzIjoiMTAyMDAiLCJka2UtMjMwNCI6IjEwMjAyIiwiZGtlLTIzMDkiOiIxMDI0NCIsImRraC0yMzEwIjoieFlJMXlMSmgiLCJka2UtMjMxMCI6IjAiLCJka2gtMjMxMSI6InhDem1LVThKIiwiZGtlLTIzMTEiOiIwIiwiZGtlLTIzMTIiOiIxMDI1NyIsImRrZS0yMzE0IjoiMTAyNjQiLCJka2gtMjMxNiI6ImZEa1ZMY1FfIiwiZGtlLTIzMTYiOiIwIiwiZGtlLTIzMTgiOiIxMDI3OSIsImRrZS0yMzIyIjoiMTAzMDciLCJka2UtMjMyMyI6IjEwMzE3IiwiZGtlLTIzMjQiOiIxMDMyMyIsImRraC0yMzI3IjoiQVN2UU5Ydy0iLCJka2UtMjMyNyI6IjAiLCJka2UtMjMyOCI6IjEwMzM4IiwiZGtlLTIzMzAiOiIxMDM0NSIsImRrZS0yMzMxIjoiMTAzNTIiLCJka2UtMjMzMyI6IjEwMzcxIiwiZGtoLTIzMzciOiJTa0JFeTdBUCIsImRrZS0yMzM3IjoiMCIsImRrZS0yMzM4IjoiMTAzOTIiLCJka2UtMjMzOSI6IjEwMzk2IiwibmJmIjoxNzQ0MzIyNzY4LCJleHAiOjE3NDQzMjMwNjgsImlhdCI6MTc0NDMyMjc2OCwiaXNzIjoiZGsifQ.idHI-mBiV9NBlx_1ESkYOKXFf1NFlg1IABywdvDjjaI; STE="2025-04-10T22:36:16.0424308Z"; STIDN=eyJDIjoxMjIzNTQ4NTIzLCJTIjo4OTY3OTI3NzI3MSwiU1MiOjkzNjM1MTIyNTY4LCJWIjo0ODg5Mjc3MDkxOCwiTCI6MSwiRSI6IjIwMjUtMDQtMTBUMjI6MzY6MDguMzY3ODk1N1oiLCJTRSI6IkNBLURLIiwiVUEiOiJJbjBMbWpMaFNUL3Y5UzRPay9iZXhuZnNUbDlIbEowUFZIRUl2RFZcdTAwMkI1UlU9IiwiREsiOiJjOWY1MzNlNC05YjMzLTQwN2YtYWJlOC0yZTA4MzNlNWY0YTkiLCJESSI6ImE4MGU3NDc1LWU0MmMtNDJjZC1hZjJmLTU4ZjI3ZTlmYjkwMyIsIkREIjo1ODc0Njk4NjIzNH0=; STH=c37a2427851040dc9c95d0202aef49b391cea8570a10bffeec35399ac1b64493; _abck=0A03A8670683A50F659B4083ABEBD8BC~0~YAAQ7xghFw2e9ByWAQAAnC+9IQ24npuFkdR7RYi01n0o3sV7bfpqhq+qCvrdy28KdGnH+dH5GiAJhWX14627AfN/ijaXra3F66dkmbsJ/hBh49yGzJ80PMU3V+mhoFm/Y73NKnmI9N+TI1CD4EBY2ajdo0gIKh50c6NAo6y9BYzqTfryEyCI7wc8u7B2iqB0Wez3wS35+EZkBBig4MUMz+1n0LxqP0BapxjQouRVEls179w8cINP/tJ1MHnjLl1SF/BsIAnrkaM4b201Hm+JjQ/e9J8cme1QDeSgY+P2ytqjz2tWTB9eFI/ZhyTh8y+U3rEOztp+NcFitoaDuwcSCGUwaCO2QDIwBDxyfj3OzXPJbbqIsNlSNnpA/zg1HtlC4OQp1E1mKBBTCMkcpazL7Xrwe8Raf/YauLAfCFWVFqdB2rFz6VJ5yKVwcqnv/krk1851Phlv1TLy//X+7FNvNBmfIyf7GjXQ2xAUJMmFSDhqDKj+bYmwqY1mewgtFsjkoE0UpjBW8YHXjKO67LxUpIKS2Eu6Q96o+TdzxAINwjGMHw==~-1~-1~-1; _csrf=0ef83b11-147a-46b1-a9e8-35d32690c104; _csrf=4e5ed430-17ae-45fc-8d4a-e1822a90d696; ak_bmsc=B9B2B3FE6EA54A3ECBD5CB0827FA9A23~000000000000000000000000000000~YAAQ7xghF52d9ByWAQAAGC+9IRuuhmFruMrUHxAWLmWENZlgr2XqFY1RgZUqQYYLFwIMcozj7JNw3nFKGcuc3E6OmM8uDvdH/rD8qyefUh2UmleZZS4DYmq4hncv+Qzw1H134jsTAB9DAYjdvVrSEuT/WuguAbWUexTthH8ECgFj+8BXfHI/J0H4rRo+jmK002powolFgEZ93tU5eIQQU11odf/ZGudb5SR8DuIpYPEgixvbfuVKC5xvpbas/Dls2YpPX+YpT2P0dek2RPDJhUQiFD0NmO78R1BuaJ6ZmN3nwzlT8qtomf9I1ZniPDYIefLwXPcbi/gu5jP6m8dz1N0XqYDr7HmWmhlc7Dmwrh5fHh791wm/0YYNZc6GTNyed6mJ4AXtDwJQ/aI4eA==; bm_sz=6461CBC0853B600B4F00F2AB25CDFB8B~YAAQ7xghF56d9ByWAQAAGC+9IRtIZxvi05iK+3c6bYF3we07w1XV4MEqECzCGUfHqwzN3zByR5iCTuazh8o7IoSowTUxzGcGNdLx+YxvIEJR2grHO60x+7tNaip3LzNIRvuuItQ8U7ne0FwElyAkhTPxkl/Li015KLRBq22w3NhwL1mdcgZ1q/AUDlaA8eIH9zXZJceQXJAEyebT3284oNvov1LB99vPZwiDEdJXVhyV5StKQBTR9vyLxYcgEokYLmRQtug1HMw3+pICl5wIzg9/sTXRdkMF5sIkoT1rboOtRy+3IlwdQnmxa+eL9XJBqRzzr0AeX5AOnkn0YBK9x6H1EvI0GXyzsPev+Nw9YNvCrYAkvWmDCeO3VHO2QkHNL9fKnPPnuJGVoiL8ZsTHlw==~3551553~4339001; bm_sv=56C64208EF0F3068896879855BED5B65~YAAQ5BghF5wRFh2WAQAA/ku9IRuVprl7JqohG9T0KvwpMPMZBJTtJepFzuB6lZjBX6nhLWD3VS+PW2MOpWJwmyPJZ90Uqa6C8A0BVOx5+qe5nT+bIw918B+s1Hq9MaVMJ2FzHvlHkd1mEAUjUMseFyU1zzmjl3wXjfemkOyC4c80e9oIiQQcBMuaoo12rmLDPFy9u1+1ACVRVC9FazLklMZ358yf1WI6fJwPLh/hSYztIqSDXiRYh20D43VDw9awNKR7XA==~1'"""

	lines = nested_dict()
	if keep:
		with open("static/nhl/draftkings.json") as fh:
			lines = json.load(fh)

	for mainCat in mainCats:
		for subCat in subCats.get(mainCats[mainCat], [0]):
			time.sleep(0.3)
			url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/42133/categories/{mainCats[mainCat]}"
			if subCat:
				url += f"/subcategories/{subCat}"
			url += "?format=json"
			outfile = "outnhlDK"
			os.system(f"curl -s {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' {cookie} -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			prop = propIds.get(subCat, "")

			print(prop)

			events = {}
			if "eventGroup" not in data:
				continue

			for event in data["eventGroup"]["events"]:
				start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
				startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=4)
				if startDt.day != int(date[-2:]):
					continue
					pass
				game = event["name"].lower()
				games = []
				for team in game.split(" @ "):
					t = team.split(" ")[0]
					if t == "was":
						t = "wsh"
					elif "rangers" in team:
						t = "nyr"
					elif "islanders" in team:
						t = "nyi"
					elif "uta" in team:
						t = "utah"
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

							alt = False
							if subCat in propIds:
								prop = propIds[subCat]
								if "-alt" in prop:
									alt = True
									prop = prop.replace("-alt", "")
							else:
								prop = row["label"].lower().split(" [")[0]
							
								prefix = ""
								if "1st period" in prop:
									prefix = "1p_"
								elif "2nd period" in prop:
									prefix = "2p_"
								elif "3rd period" in prop:
									prefix = "3p_"

								if "moneyline" in prop or prop.startswith("tie no bet"):
									prop = "ml"
								elif "puck line" in prop:
									prop = "spread"
								elif prop.endswith("team total goals"):
									team = prop.split(" ")[0]
									if team == "was":
										team = "wsh"
									elif "rangers" in prop:
										team = "nyr"
									elif "islanders" in prop:
										team = "nyi"
									elif "utah" in prop:
										team = "utah"
									if game.startswith(team.split(" ")[0]):
										prop = "away_total"
									else:
										prop = "home_total"
								elif "total" in prop:
									prop = "total"
								elif prop.endswith("blocks"):
									prop = "bs"
								else:
									print(prop)
									continue


								prop = prop.replace(" alternate", "")
								prop = f"{prefix}{prop}"

							outcomes = row["outcomes"]
							if alt:
								for outcome in outcomes:
									player = parsePlayer(outcome["participant"].strip())
									ou = outcome["oddsAmerican"]
									line = outcome.get("label", "")
									line = str(float(line.replace("+", "")) - 0.5)
									lines[game][prop][player][line] = ou
								continue

							ou = ""
							try:
								ou = f"{outcomes[0]['oddsAmerican']}/{outcomes[1]['oddsAmerican']}"
							except:
								continue

							if "ml" in prop:
								lines[game][prop] = ou
							elif prop == "3-way":
								lines[game][prop] = f"{outcomes[0]['oddsAmerican']}/{outcomes[-1]['oddsAmerican']}"
							elif prop == "gift":
								lines[game][prop] = ""
								for outcome in outcomes:
									if outcome["line"] != 0.5:
										continue
									if lines[game][prop]:
										lines[game][prop] += "/"+outcome["oddsAmerican"]
									else:
										lines[game][prop] = outcome["oddsAmerican"]
							elif "total" in prop or "spread" in prop:
								for i in range(0, len(outcomes), 1):
									line = str(float(outcomes[i]["line"]))
									odds = str(outcomes[i]['oddsAmerican'])
									team = outcomes[i]["label"].lower().split(" ")[0]
									if team == "was":
										team = "wsh"
									elif "rangers" in outcomes[i]["label"].lower():
										team = "nyr"
									elif "islanders" in outcomes[i]["label"].lower():
										team = "nyi"
									elif "utah" in outcomes[i]["label"].lower():
										team = "utah"

									if game.endswith(team):
										line = str(float(line) * -1)
									if line not in lines[game][prop]:
										lines[game][prop][line] = odds
									else:
										if team == "under" or game.endswith(team):

											if len(lines[game][prop][line].split("/")) == 2:
												if int(odds) > int(lines[game][prop][line].split("/")[-1]):
													lines[game][prop][line] = f"{lines[game][prop][line].split('/')[0]}/{odds}"
											else:
												lines[game][prop][line] += "/"+odds
										else:
											if len(lines[game][prop][line].split("/")) == 2:
												if int(odds) > int(lines[game][prop][line].split("/")[0]):
													lines[game][prop][line] = f"{odds}/{lines[game][prop][line].split('/')[-1]}"
											else:
												lines[game][prop][line] = odds+"/"+lines[game][prop][line]
							elif prop in ["atgs", "fgs"]:
								for outcome in outcomes:
									if outcome.get("hidden", False):
										continue
									player = parsePlayer(outcome["label"])
									try:
										if outcome['criterionName'] == "Anytime Scorer":
											p = "atgs"
										else:
											p = "fgs"
										if p not in lines[game]:
											lines[game][p] = {}
										lines[game][p][player] = outcome['oddsAmerican']
									except:
										continue
							else:
								player = parsePlayer(outcomes[0]["participant"].split(" (")[0])

								handicap = ""
								if prop == "shutout":
									pass
								else:
									handicap = f"{outcomes[0]['line']}"

								if not handicap:
									lines[game][prop][player] = f"{outcomes[0]['oddsAmerican']}"
									if len(row["outcomes"]) > 1:
										lines[game][prop][player] += f"/{outcomes[1]['oddsAmerican']}"
								else:
									lines[game][prop][player][handicap] = f"{outcomes[0]['oddsAmerican']}"
									if len(row["outcomes"]) > 1:
										lines[game][prop][player][handicap] += f"/{outcomes[1]['oddsAmerican']}"
										if "under" in outcomes[0]["label"].lower():
											lines[game][prop][player][handicap] = f"{outcomes[1]['oddsAmerican']}/{outcomes[0]['oddsAmerican']}"

	with open("static/nhl/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writeESPN():
	js = """

	{
		function convertTeam(team) {
			team = team.toLowerCase();
			let t = team.split(" ")[0];
			if (t == "ny") {
				if (team.includes("rangers")) {
					return "nyr";
				}
				return "nyi";
			} else if (t == "vgs") {
				return "vgk";
			}
			return t;
		}

		function parsePlayer(player) {
			player = player.toLowerCase().split(" (")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" sr", "").replaceAll(" iii", "").replaceAll(" ii", "").replaceAll(" iv", "");
			return player;
		}

		let status = "";

		async function readPage(game) {

			//for (tab of ["lines", "player props"]) {
			for (tab of ["player props"]) {
				for (let t of document.querySelectorAll("button[data-testid='tablist-carousel-tab']")) {
					if (t.innerText.toLowerCase() == tab && t.getAttribute("data-selected") == null) {
						t.click();
						break;
					}
				}
				if (tab != "lines") {
					while (!window.location.href.includes(tab.replace(" ", "_"))) {
						await new Promise(resolve => setTimeout(resolve, 500));
					}
				}
				await new Promise(resolve => setTimeout(resolve, 3000));

				for (detail of document.querySelectorAll("details")) {
					let prop = detail.querySelector("h2").innerText.toLowerCase();
					let isOU = false;

					if (prop.includes("o/u")) {
						isOU = true;
					}

					let skip = 2;
					let player = "";
					if (prop == "moneyline") {
						prop = "ml";
					} else if (prop == "game spread") {
						prop = "spread";
					} else if (prop == "total goals") {
						prop = "total";
					} else if (prop == "player total goals") {
						skip = 3;
						prop = "atgs";
					} else if (prop == "player total shots") {
						prop = "sog";
					} else if (prop == "player total assists") {
						prop = "ast";
						skip = 3;
					} else if (prop == "player total blocked shots") {
						prop = "bs";
						skip = 3;
					} else if (prop == "player saves") {
						prop = "saves";
						skip = 3;
					} else if (prop == "player points") {
						prop = "pts";
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

					if (!data[game][prop]) {
						data[game][prop] = {};
					}

					let sections = [detail];
					if (skip == 2) {
						sections = detail.querySelectorAll("div[aria-label='']");
					}

					for (section of sections) {
						let btns = section.querySelectorAll("button");

						if (skip == 2) {
							player = parsePlayer(btns[0].parentElement.parentElement.previousSibling.innerText);
						}
						for (i = 0; i < btns.length; i += skip) {
							if (btns[i].innerText == "See All Lines") {
								continue;
							}
							if (skip != 3 && btns[i].getAttribute("disabled") != null) {
								continue;
							}

							let idx = i;
							if (skip == 3) {
								idx += 1;
							}

							let ou = btns[idx].querySelectorAll("span")[1].innerText;
							if (skip != 1 && btns[idx+1].getAttribute("disabled") == null) {
								ou += "/"+btns[idx+1].querySelectorAll("span")[1].innerText;
							}

							if (skip == 3) {
								player = parsePlayer(btns[i].innerText.toLowerCase().split(" total")[0].split(" to record")[0]);
							}

							if (prop == "ml") {
								data[game][prop] = ou.replace("Even", "+100");
							} else if (prop == "double_double" || prop == "triple_double") {
								data[game][prop][player] = ou;
							} else if (prop == "atgs") {
								data[game][prop][player] = ou.replace("Even", "+100");
							} else {
								let line = btns[idx].querySelector("span").innerText;
								if (line.includes("+")) {
									line = (parseFloat(line.replace("+", "")) - 0.5).toFixed(1);
								} else {
									line = line.split(" ")[1];
								}

								if (!data[game][prop][player]) {
									data[game][prop][player] = {};
								}
								data[game][prop][player][line] = ou.replace("Even", "+100");
							}
						}
					}
				}
			}
			status = "done";
		}

		async function main() {

			let awayTeam = convertTeam(document.querySelector("div[data-testid=away-team-card] h2").innerText);
			let homeTeam = convertTeam(document.querySelector("div[data-testid=home-team-card] h2").innerText);
			let game = awayTeam + " @ " + homeTeam;
			
			data[game] = {};

			status = "";
			readPage(game);

			while (status != "done") {
				await new Promise(resolve => setTimeout(resolve, 2000));
			}

			console.log(data);
		}

		main();
	}
	"""

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

def writeEV(propArg="", bookArg="fd", teamArg="", notd=None, boost=None, overArg=None, underArg=None, nocz=None, addArg=None):

	if not boost:
		boost = 1
	if not addArg:
		addArg = 0

	with open(f"updated.json") as fh:
		updated = json.load(fh)
	updated["nhl"] = str(datetime.now())
	with open(f"updated.json", "w") as fh:
		json.dump(updated, fh, indent=4)

	#with open(f"{prefix}static/nhl/actionnetwork.json") as fh:
	#	actionnetwork = json.load(fh)

	with open(f"{prefix}static/nhl/kambi.json") as fh:
		kambiLines = json.load(fh)

	#with open(f"{prefix}static/nhl/bovada.json") as fh:
	#	bvLines = json.load(fh)

	with open(f"{prefix}static/nhl/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/nhl/mgm.json") as fh:
		mgmLines = json.load(fh)

	#with open(f"{prefix}static/nhl/pointsbet.json") as fh:
	#	pbLines = json.load(fh)

	with open(f"{prefix}static/nhl/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/nhl/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	with open(f"{prefix}static/hockeyreference/totals.json") as fh:
		totals = json.load(fh)

	with open(f"{prefix}static/hockeyreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	with open(f"{prefix}static/hockeyreference/splits.json") as fh:
		splits = json.load(fh)

	with open(f"{prefix}static/nhl/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/nhl/circa.json") as fh:
		circa = json.load(fh)

	with open(f"{prefix}static/nhl/espn.json") as fh:
		espnLines = json.load(fh)

	with open(f"{prefix}static/nhl/bet365.json") as fh:
		bet365Lines = json.load(fh)

	#espnLines = {"min @ buf": {"atgs": {"matt boldy": "160/-225", "jj peterka": "200/-300", "tage thompson": "155/-220"}}}

	lines = {
		"pn": pnLines,
		#"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"espn": espnLines,
		"365": bet365Lines,
		"dk": dkLines,
		"cz": czLines,
		"circa": circa,
	}

	with open(f"{prefix}static/nhl/ev.json") as fh:
		evData = json.load(fh)

	with open(f"{prefix}static/hockeyreference/trades.json") as fh:
		trades = json.load(fh)

	evData = {}

	teamGame = {}
	for game in pnLines:
		away, home = map(str, game.split(" @ "))
		teamGame[away] = teamGame[home] = game

	games = []
	for book in lines:
		for game in lines[book]:
			if game not in games:
				games.append(game)

	for game in games:
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

			if not propArg and (prop in ["pp_pts", "3-way"]):
				#pass
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
								handicaps[(handicap, "0.5")] = player

			for handicap, playerHandicap in handicaps:
				player = handicaps[(handicap, playerHandicap)]

				# last year stats
				lastTotalOver = lastTotalGames = 0
				totalOver = total10Over = totalGames = 0
				totalSplits = dtSplits = winLossSplits = awayHomeSplits = ""
				team = opp = ""
				if prop == "away_total":
					team = away
					opp = home
				elif prop == "home_total":
					team = home
					opp = away
				elif player:
					convertedProp = prop.replace("sog", "s").replace("ast", "a").replace("saves", "sv").replace("atgs", "g")
					#print(prop, game)
					away, home = map(str, game.split(" @ "))
					team = away
					name = player

					if home in playerIds and name in playerIds[home]:
						team = home
					if team in lastYearStats and name in lastYearStats[team] and lastYearStats[team][name]:
						for d in lastYearStats[team][name]:
							minutes = lastYearStats[team][name][d]["toi/g"]
							if minutes > 0 and (convertedProp == "pp_pts" or convertedProp in lastYearStats[team][name][d]):
								lastTotalGames += 1
								val = 0
								if convertedProp == "pp_pts":
									val = lastYearStats[team][name][d].get("ppg", 0) + lastYearStats[team][name][d].get("ppa", 0)
								else:
									val = lastYearStats[team][name][d][convertedProp]
								if val > float(playerHandicap):
									lastTotalOver += 1
					if lastTotalGames:
						lastTotalOver = int(lastTotalOver * 100 / lastTotalGames)

					if team in splits and name in splits[team]:
						playerSplits = {}
						if player in trades:
							for hdr in splits[trades[player]][name]:
								playerSplits[hdr] = splits[trades[player]][name][hdr]
							for hdr in splits[team][name]:
								playerSplits[hdr] += ","+splits[team][name][hdr]
						else:
							playerSplits = splits[team][name]

						dtSplits = playerSplits["dt"]
						winLossSplits = playerSplits["winLoss"]
						awayHomeSplits = playerSplits["awayHome"]

						if convertedProp in playerSplits:
							minArr = playerSplits["toi"].split(",")
							totalSplits = ",".join([str(int(float(x))) for x in playerSplits[convertedProp].split(",")])
							totalOver = round(len([x for x in playerSplits[convertedProp].split(",") if float(x) > float(playerHandicap)]) * 100 / len(minArr))
							total10Over = round(len([x for x in playerSplits[convertedProp].split(",")[-10:] if float(x) > float(playerHandicap)]) * 100 / len(minArr[-10:]))

				for i in range(2):

					if overArg and i == 1:
						continue
					elif underArg and i == 0:
						continue

					if lastTotalOver and i == 1:
						lastTotalOver = 100 - lastTotalOver
					if totalOver and i == 1:
						totalOver = 100 - totalOver
						total10Over = 100 - total10Over
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
									#continue
								o = "-"
								ou = f"{val}"

							o = str(o or '')
							if not o or "odds" in o.lower() or "." in o:
								continue

							#print(prop, player, book, o)
							if o != "-":
								highestOdds.append(int(o.replace("+", "")))
							odds.append(ou)
							books.append(book)

					if len(books) < 2:
						continue

					# if under but 
					unders = [s.split("/")[-1] for s in odds if "/" in s]
					if i == 1:
						if not unders:
							continue

					#print(game, prop, handicap, highestOdds, books, odds)

					removed = {}
					removedBooks = ["pn", "circa", "365"]
					for book in removedBooks:
						#removed[book] = ""
						try:
							bookIdx = books.index(book)
							o = odds[bookIdx]
							del odds[bookIdx]
							#odds.remove(o)
							books.remove(book)
							removed[book] = o
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
								#maxOdds.append(-100000)
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
					line += addArg

					# if no unders other than ev book, use that
					if len(unders) == 1 and "/" in maxOU and unders[0] == maxOU.split("/")[1]:
						bookIdx = l.index(maxOU)
						l[bookIdx] = "-/"+maxOU.split("/")[-1]
					else:
						l.remove(maxOU)
						books.remove(evBook)
					
					for book in removed:
						books.append(book)
						l.append(removed[book])

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
						j = {b: o for o, b in zip(l, books)}
						devig(evData, key, ou, line, prop=prop)
						if j.get("pn"):
							o = j["pn"]
							if i == 1:
								o = f"{o.split('/')[1]}/{o.split('/')[0]}"
							devig(evData, key, o, line, prop=prop, sharp=True)

						if "circa" in books and not j["circa"].startswith("-/"):
							o = j["circa"]
							if i == 1:
								o,u = map(str, j["circa"].split("/"))
								o = f"{u}/{o}"
							devig(evData, key, o, line, prop=prop, book="vs-circa")

						if "mgm" in books:
							try:
								l = int(j["mgm"].split("/")[0])
								if i == 1:
									if "/" in j["mgm"] and j["mgm"].split("/")[-1] != "-":
										l = int(j["mgm"].split("/")[-1])
										devig(evData, key, ou, l, prop=prop, book="mgm")
								else:
									devig(evData, key, ou, l, prop=prop, book="mgm")

								if i == 0:
									l = convertAmericanOdds(1 + (convertDecOdds(l) - 1) * 1.20)
									devig(evData, key, ou, l, prop=prop, book="mgm-20")

									if "circa" in books:
										devig(evData, key, j["circa"], l, prop=prop, book="mgm-20-vs-circa")
							except:
								pass
						#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
						if key not in evData:
							#print(key)
							continue
						if float(evData[key]["ev"]) > 0:
							#print(evData[key]["ev"], game, handicap, prop, int(line), ou, books)
							pass
						evData[key]["lastYearTotal"] = lastTotalOver
						evData[key]["totalOver"] = totalOver
						evData[key]["total10Over"] = total10Over
						evData[key]["totalSplits"] = totalSplits
						evData[key]["dtSplits"] = dtSplits
						evData[key]["winLossSplits"] = winLossSplits
						evData[key]["awayHomeSplits"] = awayHomeSplits
						evData[key]["team"] = team
						evData[key]["opp"] = opp
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
						evData[key]["odds"] = l
						evData[key]["player"] = player
						j[evBook] = maxOU
						evData[key]["bookOdds"] = j

	with open(f"{prefix}static/nhl/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	with open(f"{prefix}static/nhl/evArr.json", "w") as fh:
		json.dump([value for key, value in evData.items()], fh)

def sortEV(propArg):
	with open(f"{prefix}static/nhl/ev.json") as fh:
		evData = json.load(fh)

	data = []
	for player in evData:
		d = evData[player]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], d["game"], player, d["playerHandicap"], d["line"], d["book"], j, d["lastYearTotal"], d["totalOver"], d))

	for row in sorted(data):
		if propArg != "atgs" and row[-1]["prop"] in ["atgs"]:
			continue
		if propArg != "fgs" and row[-1]["prop"] in ["fgs"]:
			continue
		if propArg != "3-way" and row[-1]["prop"] in ["3-way"]:
			continue
		print(row[:-1])

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "Bet365", "CZ", "PN", "Kambi/BR", "ESPN", "LYR", "L10", "SZN", "Splits"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] in ["3-way", "atgs", "fgs"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		
		implied = 0
		if row[-1]["line"] > 0:
			implied = 100 / (row[-1]["line"] + 100)
		else:
			implied = -1*row[-1]["line"] / (-1*row[-1]["line"] + 100)
		implied *= 100
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), f"{round(implied)}%", row[1].upper(), row[-1]["player"].title(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "365", "cz", "pn", "kambi", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))

		for h in ["lastYearTotal", "total10Over", "totalOver"]:
			if not row[-1][h]:
				arr.append("-")
			else:
				arr.append(f"{row[-1][h]}%")
		try:
			arr.append(",".join(row[-1]["totalSplits"].split(",")[-10:]))
		except:
			arr.append("-")
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nhl/props.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "PN_EV", "EV Book", "Imp", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "Bet365", "CZ", "PN", "Kambi/BR", "ESPN", "LYR", "L10", "SZN"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] != "atgs":
			continue
		ou = ("u" if row[-1]["under"] else "o")
		implied = 0
		if row[-1]["line"] > 0:
			implied = 100 / (row[-1]["line"] + 100)
		else:
			implied = -1*row[-1]["line"] / (-1*row[-1]["line"] + 100)
		implied *= 100
		arr = [row[0], row[-1].get("pn_ev", "-"), str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), f"{round(implied)}%", row[1].upper(), row[-1]["player"].title(), row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "365", "cz", "pn", "kambi", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		for h in ["lastYearTotal", "total10Over", "totalOver"]:
			if not row[-1][h]:
				arr.append("-")
			else:
				arr.append(f"{row[-1][h]}%")
		arr.append(",".join(row[-1]["totalSplits"].split(",")[-10:]))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nhl/atgs.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Player", "Prop", "FD", "DK", "MGM", "Bet365", "Kambi/BR", "ESPN"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] != "fgs":
			continue
		implied = 0
		if row[-1]["line"] > 0:
			implied = 100 / (row[-1]["line"] + 100)
		else:
			implied = -1*row[-1]["line"] / (-1*row[-1]["line"] + 100)
		implied *= 100
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].upper().replace("KAMBI", "BR"), f"{round(implied)}%", row[1].upper(), row[-1]["player"].title(), row[-1]["prop"]]
		for book in ["fd", "dk", "mgm", "365", "kambi", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/nhl/fgs.csv", "w") as fh:
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
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("--espn", action="store_true", help="ESPN")
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
	parser.add_argument("--notd", action="store_true", help="Not ATTD FTD")
	parser.add_argument("--onlygoals", action="store_true")
	parser.add_argument("--commit", action="store_true")
	parser.add_argument("--circa", action="store_true")
	parser.add_argument("--merge-circa", action="store_true")
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--add", type=int)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--token")
	parser.add_argument("--player", help="Book")

	args = parser.parse_args()

	if args.onlygoals:
		writeOnlyGoals(args.date)

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
		writeMGM(args.date)

	if args.circa:
		writeCirca(args.date)

	if args.merge_circa:
		mergeCirca()

	if args.pb:
		writePointsbet(args.date)

	if args.dk:
		writeDK(args.date, args.keep)

	if args.kambi:
		writeKambi(args.date)

	if args.pn:
		writePinnacle(args.date, args.debug)

	if args.bv:
		writeBV()

	if args.cz:
		uc.loop().run_until_complete(writeCZToken())
		writeCZ(args.date)

	if args.update:
		#writeFanduel()
		print("pn")
		writePinnacle(args.date, args.debug)
		print("kambi")
		writeKambi(args.date)
		print("dk")
		writeDK(args.date, args.keep)
		print("cz")
		uc.loop().run_until_complete(writeCZToken())
		writeCZ(args.date)
		#print("bv")
		#writeBV()

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, teamArg=args.team, notd=args.notd, boost=args.boost, overArg=args.over, underArg=args.under, nocz=args.nocz, addArg=args.add)

	if args.print:
		sortEV(args.prop)

	if args.commit:
		commitChanges()