
from datetime import datetime
import json
import os

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


def writeFanduel():
	pass

if __name__ == '__main__':

	writeFanduel()
	#writeActionNetwork()

	freeBet = 170
