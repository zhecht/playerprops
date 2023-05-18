
from datetime import datetime
from subprocess import call
import json
import os
import time

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def writeActionNetwork():
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel",
		15: "betmgm",
		283: "betmgm",
		348: "betrivers",
		351: "pointsbet",
		355: "caesars"
	}

	props = ["35_doubles", "33_hr"]
	odds = {}
	optionTypes = {}

	date = datetime.now()
	date = str(date)[:10]

	for prop in props:
		path = f"out.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/8/props/core_bet_type_{prop}?bookIds=69,68,15,283,348,351,355&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		prop = prop.split("_")[-1]

		with open(path) as fh:
			j = json.load(fh)

		with open(path, "w") as fh:
			json.dump(j, fh, indent=4)

		if "markets" not in j:
			return
		market = j["markets"][0]

		for option in market["rules"]["options"]:
			optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

		teamIds = {}
		for row in market["teams"]:
			teamIds[row["id"]] = row["abbr"].lower()

		playerIds = {}
		for row in market["players"]:
			playerIds[row["id"]] = row["full_name"].lower().replace(".", "").replace("-", " ").replace("'", "")

		books = market["books"]
		for bookData in books:
			bookId = bookData["book_id"]
			if bookId not in actionNetworkBookIds:
				#continue
				pass
			for oddData in bookData["odds"]:
				player = playerIds[oddData["player_id"]]
				team = teamIds[oddData["team_id"]]
				overUnder = optionTypes[oddData["option_type_id"]]
				book = actionNetworkBookIds.get(bookId, "")

				if team not in odds:
					odds[team] = {}
				if player not in odds[team]:
					odds[team][player] = {}
				if prop not in odds[team][player]:
					odds[team][player][prop] = {}
				if book not in odds[team][player][prop]:
					odds[team][player][prop][book] = {}
				odds[team][player][prop][book][overUnder] = f"{overUnder[0]}{oddData['value']} ({oddData['money']})"

				if player == "yandy diaz":
					#print(bookId, player, team, f"{overUnder[0]}{oddData['value']} ({oddData['money']})")
					pass
				if "line" not in odds[team][player][prop]:
					odds[team][player][prop]["line"] = f"o{oddData['value']}"
				elif oddData['value'] < float(odds[team][player][prop]["line"][1:]):
					odds[team][player][prop]["line"] = f"o{oddData['value']}"

	with open(f"{prefix}static/freebets/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def convertFDTeam(team):
	team = team.replace("pittsburgh pirates", "pit").replace("detroit tigers", "det").replace("cincinnati reds", "cin").replace("colorado rockies", "col").replace("minnesota twins", "min").replace("los angeles dodgers", "lad").replace("arizona diamondbacks", "ari").replace("oakland athletics", "oak").replace("philadelphia phillies", "phi").replace("san francisco giants", "sf").replace("kansas city royals", "kc").replace("san diego padres", "sd").replace("los angeles angels", "laa").replace("baltimore orioles", "bal").replace("washington nationals", "wsh").replace("miami marlins", "mia").replace("new york yankees", "nyy").replace("toronto blue jays", "tor").replace("seattle mariners", "sea").replace("boston red sox", "bos").replace("tampa bay rays", "tb").replace("new york mets", "nym").replace("milwaukee brewers", "mil").replace("st. louis cardinals", "stl").replace("atlanta braves", "atl").replace("texas rangers", "tex").replace("cleveland guardians", "cle").replace("chicago white sox", "chw").replace("chicago cubs", "chc").replace("houston astros", "hou")
	return team

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	
	js = """
		const as = document.getElementsByTagName("a");
		const urls = {};
		for (a of as) {
			if (a.href.indexOf("/baseball/mlb") >= 0) {
				urls[a.href] = 1;
			}
		}
		console.log(Object.keys(urls));
	"""

	games = [
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/pittsburgh-pirates-@-detroit-tigers-32357990",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/cincinnati-reds-@-colorado-rockies-32357984",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/minnesota-twins-@-los-angeles-dodgers-32357991",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/arizona-diamondbacks-@-oakland-athletics-32357992",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/philadelphia-phillies-@-san-francisco-giants-32358829",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/kansas-city-royals-@-san-diego-padres-32358859",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/los-angeles-angels-@-baltimore-orioles-32357986",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/washington-nationals-@-miami-marlins-32357985",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/new-york-yankees-@-toronto-blue-jays-32357987",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/seattle-mariners-@-boston-red-sox-32357988",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/tampa-bay-rays-@-new-york-mets-32358670",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/milwaukee-brewers-@-st.-louis-cardinals-32357983",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/atlanta-braves-@-texas-rangers-32357993",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/cleveland-guardians-@-chicago-white-sox-32357989",
	  "https://mi.sportsbook.fanduel.com/baseball/mlb/chicago-cubs-@-houston-astros-32357994"
	]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = convertFDTeam(game.split("/")[-1][:-9].replace("-", " "))
		lines[game] = {}

		outfile = "out"
		time.sleep(0.2)
		url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}&tab=batter-props"
		call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		for market in data["attachments"]["markets"]:
			marketName = data["attachments"]["markets"][market]["marketName"].lower()

			if marketName in ["to hit a home run", "to hit a double"]:
				prop = "double" if "double" in marketName else "hr"
				for playerRow in data["attachments"]["markets"][market]["runners"]:
					player = playerRow["runnerName"].lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
					odds = playerRow["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]

					if player not in lines[game]:
						lines[game][player] = {}
					lines[game][player][prop] = odds
	
	with open(f"{prefix}static/baseballreference/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

if __name__ == '__main__':

	writeFanduel()
	#writeActionNetwork()

	freeBet = 170
