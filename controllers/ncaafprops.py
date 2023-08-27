from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time
from twilio.rest import Client

def convertActionTeam(team):
	if team.endswith(" st"):
		team = team.replace(" st", " state")
	if "international" in team:
		team = team.replace("international", "intl")
	teams = {
		"jax state": "jacksonville state",
		"n mexico state": "new mexico state",
		"umass": "massachusetts",
		"la tech": "louisiana tech",
		"fiu": "florida intl"
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
	return player.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")

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
	return int(avg)

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
	let data = {};
	let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
	for (div of document.querySelectorAll(".src-FixtureSubGroupWithShowMore")) {
		const showMore = div.querySelector(".msl-ShowMore_Link");
		let playerList = [];
		for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
			let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(". ", "").replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
			let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];
			
			if (data[team] === undefined) {
				data[team] = {};
			}
			data[team][player] = {
				ftd: "",
				ltd: "",
				attd: ""
			};
			playerList.push([team, player]);
		}

		let idx = 0;
		for (playerDiv of div.querySelectorAll(".gl-Market")[1].querySelectorAll(".gl-ParticipantOddsOnly_Odds")) {
			let team = playerList[idx][0];
			let player = playerList[idx][1];

			let odds = playerDiv.innerText;
			data[team][player]["ftd"] = odds;
			idx += 1;
		}

		idx = 0;
		for (playerDiv of div.querySelectorAll(".gl-Market")[2].querySelectorAll(".gl-ParticipantOddsOnly_Odds")) {
			let team = playerList[idx][0];
			let player = playerList[idx][1];

			let odds = playerDiv.innerText;
			data[team][player]["ltd"] = odds;
			idx += 1;
		}

		idx = 0;
		for (playerDiv of div.querySelectorAll(".gl-Market")[3].querySelectorAll(".gl-ParticipantOddsOnly_Odds")) {
			let team = playerList[idx][0];
			let player = playerList[idx][1];

			let odds = playerDiv.innerText;
			data[team][player]["attd"] = odds;
			idx += 1;
		}
	}
	console.log(data)
	}

"""

def writeKambi(date):

	if not date:
		date = datetime.now()
		date = str(date)[:10]

	data = {}
	outfile = f"out.json"
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
			label = betOffer["criterion"]["label"]
			if not teamIds and "Handicap" in label:
				for row in betOffer["outcomes"]:
					team = home
					if away in row["label"].lower():
						team = away
					teamIds[row["participantId"]] = team
					data[team] = {}

			elif label.startswith("Touchdown Scorer") or label.startswith("First Touchdown Scorer"):
				prop = "attd"
				if label.startswith("First"):
					prop = "ftd"

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
						over = outcome["oddsAmerican"]
						if player not in data[team]:
							data[team][player] = {}
						data[team][player][prop] = f"{over}"


	with open(f"{prefix}static/ncaafprops/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)

actionNetworkBookIds = {
	68: "draftkings",
	69: "fanduel",
	#15: "betmgm",
	283: "mgm",
	348: "betrivers",
	351: "pointsbet",
	355: "caesars"
}

def writeActionNetwork(dateArg = None):
	props = ["56_first_touchdown_scorer", "62_anytime_touchdown_scorer"]

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
		url = f"https://api.actionnetwork.com/web/v1/leagues/2/props/core_bet_type_{actionProp}?bookIds=69,68,283,348,351,355&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		prop = actionProp.split("_")[-1]
		if "touchdown" in actionProp:
			prop = "ftd"
			if "anytime" in actionProp:
				prop = "attd"
		elif prop.endswith("s"):
			prop = prop[:-1]

		with open(path) as fh:
			j = json.load(fh)

		if "markets" not in j:
			return
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
				overUnder = "over"
				try:
					optionTypes[oddData["option_type_id"]]
				except:
					pass
				book = actionNetworkBookIds.get(bookId, "")
				value = oddData["value"]

				if team not in odds:
					odds[team] = {}
				if player not in odds[team]:
					odds[team][player] = {}
				if prop not in odds[team][player]:
					odds[team][player][prop] = {}

				if book not in odds[team][player][prop]:
					odds[team][player][prop][book] = f"{oddData['money']}"
				elif overUnder == "over":
					odds[team][player][prop][book] = f"{oddData['money']}/{odds[team][player][prop][book]}"
				else:
					odds[team][player][prop][book] += f"/{oddData['money']}"
				sp = odds[team][player][prop][book].split("/")
				if odds[team][player][prop][book].count("/") == 3:
					odds[team][player][prop][book] = sp[1]+"/"+sp[2]

	with open(f"{prefix}static/ncaafprops/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	
	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText == "More wagers" && a.href.indexOf("/football/ncaa-football-games") >= 0) {
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
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/utep-@-jacksonville-state-32562512",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/ohio-@-san-diego-state-32562518",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/massachusetts-@-new-mexico-state-32562515",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/hawaii-@-vanderbilt-32562519",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/san-jose-state-@-usc-32562537",
  "https://mi.sportsbook.fanduel.com/football/ncaa-football-games/florida-international-@-louisiana-tech-32562538"
]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-", " ")
		#away, home = map(str, game.split(" @ "))
		#game = f"{convertCollege(away)} @ {convertCollege(home)}"
		if game in lines:
			continue
		lines[game] = {}

		outfile = "out"

		for tab in ["td-scorer"]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}&tab={tab}-props"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue
			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()

				if marketName in ["any time touchdown scorer", "first touchdown scorer"]:
					prop = "attd"
					if "first" in marketName:
						prop = "ftd"

					for playerRow in data["attachments"]["markets"][market]["runners"]:
						player = parsePlayer(playerRow["runnerName"].lower().replace(" over", "").replace(" under", ""))
						handicap = ""
						try:
							odds = playerRow["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
						except:
							continue

						if player not in lines[game]:
							lines[game][player] = {}

						lines[game][player][prop] = odds


	
	with open(f"{prefix}static/ncaafprops/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devigger(evData, player="", bet365Odds="575/-900", finalOdds=630, prop="hr"):

	outfile = f"out_{prop}"
	post = ["curl", 'https://crazyninjaodds.com/Public/sportsbooks/sportsbook_devigger.aspx', "-X", "POST", "-H", 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0', "-H", 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', "-H",'Accept-Language: en-US,en;q=0.5', "-H",'Accept-Encoding: gzip, deflate', "-H",'Content-Type: application/x-www-form-urlencoded', "-H",'Origin: https://crazyninjaodds.com', "-H",'Connection: keep-alive', "-H",'Referer: https://crazyninjaodds.com/Public/sportsbooks/sportsbook_devigger.aspx', "-H",'Cookie: ASP.NET_SessionId=ytnh3dbruzkf32qaweb3wio3; General=KellyMultiplier=.25&KellyBankRoll=1000&DevigMethodIndex=4&WorstCaseDevigMethod_Multiplicative=True&WorstCaseDevigMethod_Additive=True&WorstCaseDevigMethod_Power=True&WorstCaseDevigMethod_Shin=True&MultiplicativeWeight=0&AdditiveWeight=0&PowerWeight=0&ShinWeight=0&ShowEVColorIndicator=False&ShowDetailedDevigInfo=False&CopyToClipboard_Reddit=False&CopyToClipboard_DevigURL=True&CopyToClipboard_Reddit_IncludeDevigURL=False&ShowHedgeDevigMethod=False&UseMultilineTextbox=False', "-H",'Upgrade-Insecure-Requests: 1', "-H",'Pragma: no-cache', "-H",'Cache-Control: no-cache', "--data-raw", '__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=mmD0Dl1C6EgV%2BDqOi7tbA%2BnOlOxGkYdG1DQ0Dv9Don%2FcQnhqZ977VWb3vTBqmdT3S%2Fng2DngDHu87Smxc5GuAeDG%2FPE8ol%2FtlxKl3NuULU42P3Y7PwndnRpvWouYQTQBejSCEBuxZDYcBxxi5lVFeP0EPAhUqWsNj0TpzBsd2w9qU7GPmdrYtts8bFB9SPbdWnU33UQOrXf%2FP2PsekX%2FtNLaqtv0EQCef%2F11tDhlGestDGZNSzI4H962zIGo6aIThiN7O6l%2BJsymp2Bowj%2BYrhbDAZz90Fi0tMxzPaFMKwnsTV2GTc58vxJ8MwN75qvEl7aWbao34JBR2BNtixrALDbrpzfuqZsQafZCxqeFpxsv6i343etGvHHjFdA2B%2F%2BldeU2hLuslsKR98VxHHUNpIZdXW%2FBPxcBGvKiah9iaglqHRNJbO9%2FgZRFLH4Jlz42uPBjEeKOMRMHqLOVFk8Alt7ZvDa%2BYAVKj3ke7sFTXiLqCSP9GFcrhsdFh3%2FlyMK1KQa2uO9rs3y1bb6PamvzPY78KK4MvA6Wppvxw65ICHypxw5feEqIpv0WbVPHzlyohKf1Bomt40NH6dlVnMK5D0LHDWRT49k5%2FB4NojdQYxcAibx2h%2BdO46udYv%2FAFF53kxSeQMtKqDwkSqqSgYBJT6Q1qO7cyU61qfVtX1IkxylJws%2BRDL818HSeUL5sUqpS1YO1BN5YYZPlwtGvOnUopGBdBZ3lPcOJKarZI5b4oj2ukSbbR1NAVgio0Fx9fZlkst6Zp4JszRup%2BxQipCBpjclBHCeuQc0xQf9bpeAU7jj%2BpS2lrK%2FfGp6doUd1psrdhWuuXZn2H96wlKpOtJQFjXNmDV1e7yQ4Xg1N9IKsVyZsL9aIZbx91qHjbW5p5bYLfV6WgTGl748OFWYYQXRgLv9p7gLI6zIkpOW%2FfC1YZP%2FRAmFXeXdT1REmgMR1A6I%2Bwu4w3Gt6VVDDVlkXhB2gF6ibfrWKRtjWCmbo8rI%2F2oSBOTBhpcMQ2ZxYJyHuRFQUSP63pyeRVw25jQZG2o%2FuAwHAKZuCR6i4DMylsVmd3eDzdLXzU4FdSQLs41xuS51F%2B0%2BbOhTyLhACABpOgn%2FpFdiA9yAVh9g7eMcYWrWDrwuHDCUbCvcWmdWGdlYlRcOGtd5SYegC06AiIRGzQNmYmhMFtdssQ8MThQI7EJNf9INitgKG0j%2F0ucxSCBZ%2BhwyzstbTPjvZKeFKr%2FSwWlqOkGAmFpMUeQjaGd9mRBeKNSlQql2cEs5UmHN8asvDPZJ%2BIHBg1Bgz5Uvj9v%2B7D14ujxugjATPgJXLBO9nUcS3UM1AJBf8FpRFHhTljZNKjTZdOPam%2FaZeV2hQU%2FQuCASAN5SgD2dFlTr4xFU6XkzKTRtRN%2FrFc21LqJHBe1V4AGuQ5sA%2B4ClPpVyKzjZkImOoqeLs1RFNfEBF1du2mx08iSQZQR%2F8IHEkcIIJnB%2BJO8doPyIDYlTs0D5TcuEV19y6%2Fuz%2BhGopH3VWyXZF3995CdXYXoaXeQnjCYU3LohkMWEMKYzFmI6u2dN0ZC6hBRgmOlAMLRHAB9Tv%2BuozseQYeuAxK%2BFpcGy73FpDKbIeoOkkm8xMBNNUWLwdP9tm8XQ7yGUgJEABRkZLC8cbe5z8Jt1202t3YO4%2BUFxusPMu4L1s1lX%2B%2F%2F2mJhpboAi9QHZrtGHV0luWzBfFe0PV51KhmWN56NtbLqo2MHVTSb0wlf%2B1gVB9tAkNG31ioJIjUfhtdLK6nbjW6GKBiwGAIsYcYl8by0uLeN2%2BaeSru8WRyVle%2BqXv83Cap35tdZg89vNnHqEbBba950MpN6cEmwHUViyP88XO6VctlhyhKpjEL%2BYI0NG1IoU1Mz%2BFmQcRck1fc2DYJdoUbGoOAIYiFlpKXwUMoeIlQNX5KEEKo50CshCUlwO0TFGCmaPlvuIPuVkR8cCxzdouuC6Tr5JHuENmRNbvkTcVwCSDPue04tjFPz83&__VIEWSTATEGENERATOR=75A63123&__EVENTVALIDATION=Zr5waX29KFtDx%2B%2BTw51Tt8HB5B0GTcdcqlawxLCwmhEYuz7ZzMAfiq2Rax%2FjuEFCG8QtUbvGvUNRuKP%2Fzh5HI%2FlUqyw0KbImM%2FIYe%2FsBbhqvqP3Jm6SmAo6buwGM51cAvXCGtI5DEO%2FLEiPuQyvg9nPgJI4WbaoK8%2B%2BXxqVcC8nM%2BiZkP6ny9CpojqCqCXwtRZa87knXf6wGnTJJ3fmLZoWSXHqaSQfU0a2j0hXL%2B7G4IFUkenNSxacAhym7pIBIbkX2OSWDpPWY242nH1mnKjQCekp3fUJaWPiTf%2F9vZlI3CHez7M%2B1L7q9ltWhynNHCZXkV5BX5UAzxL0W%2FFo6QiPTi0EPu7ckqmYYaQVey0K%2FWde5nDU%2FgiMBjD9u9VFxNslbqytjT4Xn8H5659GVxHOZCGke3N2U1%2FEasCInKUrq5pURmsTIlmqpgXpaJKW1JI1edPzr4JsVosHsYC7iTyoHNNX2lVLtwxnOWCmxsMuBUbW2T%2BfGd62SQovw0rDpBe8wvZkG1075LdVuzcOI2%2B8b%2BrEqan2bTJacf%2BQWcXB1Wba9v%2Bha4ekXUflA%2FT9uQofbNGLO3%2Fk%2FYbN2P8miLiDflzT55LvqRJ0b4m8L51kKoPcubP4sAtAZiSTgJ7XZCWpL14PQCvh%2FLA0QyGhlPvRFkUhqrc90HLjlZAeYIuNAKQ306Q0gXT5CbP8xNtxzSzORR3gtjDBHQ46YfO5VG0XOT9un%2BA0kfmCun43YrozvVcpILbJwOjbFtA4EbiIbvAoDn09Swo3D%2BtKyIbveoDyM%2FWDpTmFb2UYD4dSvooDffp%2FeSljH89b2L3MSSBP3sS7xDLj2rGP1GeXJr2%2F%2BVyt%2B8Xm5BGt%2FgJiu9T1ND0jAlILHuG%2FyLZxWkPlpiPO0R6GnLS%2B7aztX2T1sBxmqr874atOJKg77T4NMcSC%2FClMoNnFI2YS%2FEbK92IadQNpFulWIcRYKwMPN7RBmi1kV2oUpmCdD%2F7Mv95Uy%2BlhI05jSt2sICSlZvHz5D9QaFvPHnhH%2FL%2BjZpEIl09JPgyeFX5h2Gb5iR%2F6TMmx94zGblnRV4x2iMNmnm7T98Ve3sRcd3LXLxXO92tW9kXvxtCD7rSnZ5du1SmJnWwE1qwfsTEeE671V%2BxAIrAhTUWBpNHSF8W4iEvN2swA22wM2SemIzsmLXYJUCXIwHZ3bo3Kgm2Qm93nJSP%2BpvfFQC5W%2BAsQuaxxgIh7FH2yIUXWUzokKwHcrsAhmGMkJM64o6OFFRFKJwVoXKThwERuuU7u2Bi2x86%2FwKEkvdMLa6cemCqieEWRzTR9WT0qIUaPn%2BhLunuW5%2FnSernkf7Qhn51ukrRK0pdZv6kZESHyx4BsxoA8L5oWGNCvZJajHI304I4kFIM0sKP3CHpPZ3iq79qEGo%2FUl5JnuXHN9HF23INR2HrEjR%2BUgMdJfoehGly3KNtQw%2F1NOnJG7TRC8Sj5NE%2FTrbjzH3cLqL1grHOI2PS45hoRD1Q%3D%3D&TextBoxKellyMultiplier=.25&TextBoxBankRoll=1000&RadioButtonListDevigMethod=worstcase&TextBoxLegOdds='+str(bet365Odds)+'&TextBoxFinalOdds='+str(finalOdds)+'&TextBoxCorrelation=0&TextBoxBoost=0%25&Boost=RadioButtonBoostProfit&DropDownListDailyFantasy=0&ButtonCalculate=Calculate&Text1=https%3A%2F%2Fcrazyninjaodds.com%2FPublic%2Fsportsbooks%2Fsportsbook_devigger.aspx%3Fautofill%3D1%26LegOdds%3DAVG%28350%252c275%252c300%252c350%252c400%29%26FinalOdds%3D312&CheckBoxListWorstCaseMethodSettings%240=The+Multiplicative%2FNormalization%2FTraditional+Method&CheckBoxListWorstCaseMethodSettings%241=The+Additive+Method&CheckBoxListWorstCaseMethodSettings%242=The+Power+Method&CheckBoxListWorstCaseMethodSettings%243=The+Shin+Method&TextBoxMultiplicativeWeight=0%25&TextBoxAdditiveWeight=0%25&TextBoxPowerWeight=0%25&TextBoxShinWeight=0%25&CheckBoxListCopyToClipboardSettings%240=devigurl', "-o", outfile]

	time.sleep(0.3)
	call(post)

	soup = BS(open(outfile, 'rb').read(), "lxml")
	try:
		output = soup.find("span", id="LabelOutput").text
	except:
		return

	m = re.search(r".* Fair Value = (.*?) \((.*?)\)Summary\; EV% = (.*?)%", output)
	if m:
		fairVal = m.group(1)
		implied = m.group(2)
		ev = m.group(3)
		if player not in evData:
			evData[player] = {}
		evData[player]["fairVal"] = fairVal
		evData[player]["implied"] = implied
		evData[player]["ev"] = ev

def writeEV(date=None, gameArg="", teamArg="", prop="attd", book="", boost=None):
	if not date:
		date = str(datetime.now())[:10]

	if not boost:
		boost = 1

	with open(f"{prefix}static/ncaafprops/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/ncaafprops/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/ncaafprops/ev_{prop}.json") as fh:
		evData = json.load(fh)

	if not teamArg and not gameArg:
		evData = {}
	elif teamArg:
		for player in evData.copy():
			if teamArg in evData[player]["game"]:
				del evData[player]

	for team in bet365Lines:
		if not team:
			continue
		if teamArg and teamArg not in game:
			continue
		for player in bet365Lines[team]:
			if not player:
				continue
			if prop not in bet365Lines[team][player]:
				continue
			
			bet365 = bet365Lines[team][player][prop]

			fd = dk = br = mgm = "-"
			if team in actionnetwork and player in actionnetwork[team] and prop in actionnetwork[team][player]:
				fd = actionnetwork[team][player][prop].get("fanduel", "-")
				dk = actionnetwork[team][player][prop].get("draftkings", "-")
				#br = actionnetwork[team][player][prop].get("betrivers", "-")
				mgm = actionnetwork[team][player][prop].get("mgm", "-")

			kambi = "-"
			if team in kambiLines and player in kambiLines[team] and prop in kambiLines[team][player]:
				kambi = kambiLines[team][player][prop]

			evBook = "dk"
			evLine = dk
			l = [fd, br, mgm, kambi, bet365]

			if book == "fd" or (not book and (dk == "-" or (fd != "-" and dk != "-" and int(fd) > int(dk)))):
				evBook = "fd"
				evLine = fd
				l[0] = dk

			if evLine == "-":
				continue

			avgOver = []
			for line in l:
				if line and line != "-":
					avgOver.append(line)

			evLine = convertAmericanOdds(1 + (convertDecOdds(int(evLine)) - 1) * boost)

			ou = f"avg({','.join(avgOver)})"
			devigger(evData, player, ou, evLine, prop=prop)
			if player not in evData:
				print(player)
				continue

			evData[player]["odds"] = {
				"fd": fd,
				"dk": dk,
				"mgm": mgm,
				"bet365": bet365,
				"kambi": kambi
			}
			evData[player]["book"] = evBook
			evData[player]["team"] = team
			evData[player]["ou"] = ou
			evData[player]["line"] = evLine

	with open(f"{prefix}static/ncaafprops/ev_{prop}.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def printEV():

	for prop in ["ftd", "attd"]:
		with open(f"{prefix}static/ncaafprops/ev_{prop}.json") as fh:
			evData = json.load(fh)

		data = []
		for player in evData:
			data.append((float(evData[player]["ev"]), evData[player]["line"], player, evData[player]["team"], evData[player]["ou"], evData[player]))

		output = "\t".join(["EV", "Player", "Team", "Line", "FD", "DK", "Bet365", "MGM", "Kambi"]) + "\n"
		for row in sorted(data, reverse=True):
			arr = [row[0], row[2], row[3], f"{row[1]} ({row[-1]['book']})"]
			for book in ["fd", "dk", "bet365", "mgm", "kambi"]:
				arr.append(row[-1]["odds"][book])
			output += "\t".join([str(x) for x in arr])+"\n"

		with open(f"static/ncaafprops/ev_{prop}.csv","w") as fh:
			fh.write(output)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("-g", "--game", help="Game")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("--book", help="Book")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--fd", action="store_true", help="FD")
	parser.add_argument("-p", "--print", action="store_true", help="Print")

	args = parser.parse_args()

	if args.update:
		writeFanduel()
		writeActionNetwork(args.date)
		writeKambi(args.date)

	if args.fd:
		writeFanduel()

	if args.action:
		writeActionNetwork(args.date)

	if args.kambi:
		writeKambi(args.date)

	if args.print:
		printEV()

	if args.prop:
		writeEV(date=args.date, gameArg=args.game, teamArg=args.team, prop=args.prop, book=args.book, boost=args.boost)


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