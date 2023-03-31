import argparse
import datetime
import glob
import json
import math
import os
import operator
import re
import time

from bs4 import BeautifulSoup as BS
from bs4 import Comment
import datetime
from sys import platform
from subprocess import call
from glob import glob

try:
	from controllers.functions import *
except:
	from functions import *

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def write_schedule(date):
	url = f"https://www.espn.com/mlb/schedule/_/date/{date.replace('-', '')}"
	outfile = "out2"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/baseballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)

	schedule[date] = []

	date = ""

	for table in soup.findAll("div", class_="ResponsiveTable"):
		if table.find("div", class_="Table__Title"):
			date = table.find("div", class_="Table__Title").text.strip()
			date = str(datetime.datetime.strptime(date, "%A, %B %d, %Y"))[:10]
		schedule[date] = []
		if date not in boxscores:
			boxscores[date] = {}
		if date not in scores:
			scores[date] = {}

		for row in table.findAll("tr")[1:]:
			tds = row.findAll("td")
			try:
				awayTeam = tds[0].findAll("a")[-1].get("href").split("/")[-2]
				homeTeam = tds[1].findAll("a")[-1].get("href").split("/")[-2]
			except:
				continue
			boxscore = tds[2].find("a").get("href")
			score = tds[2].find("a").text.strip()
			if score.lower() == "postponed":
				continue
			if ", " in score and os.path.exists(f"{prefix}static/baseballreference/{awayTeam}/{date}.json"):
				scoreSp = score.split(", ")
				if awayTeam == scoreSp[0].split(" ")[0].lower():
					scores[date][awayTeam] = int(scoreSp[0].split(" ")[1])
					scores[date][homeTeam] = int(scoreSp[1].split(" ")[1])
				else:
					scores[date][awayTeam] = int(scoreSp[1].split(" ")[1])
					scores[date][homeTeam] = int(scoreSp[0].split(" ")[1])
			boxscores[date][f"{awayTeam} @ {homeTeam}"] = boxscore
			schedule[date].append(f"{awayTeam} @ {homeTeam}")

	with open(f"{prefix}static/baseballreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/baseballreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/baseballreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

def write_averages():
	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/baseballreference/averages.json") as fh:
		averages = json.load(fh)

	with open(f"{prefix}static/baseballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	for team in ids:
		if team not in averages:
			averages[team] = {}
		if team not in lastYearStats:
			lastYearStats[team] = {}

		for player in ids[team]:
			pId = ids[team][player]
			if player in averages[team]:
				pass
				continue
			
			gamesPlayed = 0
			averages[team][player] = {}
			lastYearStats[team][player] = {}

			time.sleep(0.175)
			url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}/type/mlb/year/2022"
			outfile = "out2"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			headers = []
			for row in soup.findAll("tr"):
				if not headers and row.text.lower().startswith("date"):
					tds = row.findAll("td")[3:]
					if not tds:
						tds = row.findAll("th")[3:]
					for td in tds:
						headers.append(td.text.strip().lower())
				elif row.text.startswith("Totals"):
					for idx, td in enumerate(row.findAll("td")[1:]):
						header = headers[idx]
						try:
							val = float(td.text.strip())
						except:
							val = "-"
						averages[team][player][header] = val
					averages[team][player]["gamesPlayed"] = gamesPlayed
				else:
					tds = row.findAll("td")
					if len(tds) > 1 and ("@" in tds[1].text or "vs" in tds[1].text):
						date = str(datetime.datetime.strptime(tds[0].text.strip(), "%a %m/%d")).split(" ")[0][6:]
						gamesPlayed += 1
						try:
							vs = tds[1].findAll("a")[-1].get("href").split("/")[-2]
						except:
							continue
						lastYearStats[team][player][date] = {
							"vs": vs
						}
						for idx, td in enumerate(tds[3:]):
							header = headers[idx]

							val = 0.0
							if header in ["dec", "rel"]:
								val = td.text.strip()
							else:
								try:
									val = float(td.text.strip())
								except:
									val = "-"
							lastYearStats[team][player][date][header] = val

	with open(f"{prefix}static/baseballreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	if lastYearStats:
		with open(f"{prefix}static/baseballreference/lastYearStats.json", "w") as fh:
			json.dump(lastYearStats, fh, indent=4)

def write_roster():

	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	roster = {}
	for team in os.listdir(f"{prefix}static/baseballreference/"):

		if team not in playerIds:
			playerIds[team] = {}

		if team.endswith(".json"):
			continue

		roster[team] = {}
		time.sleep(0.2)
		url = f"https://www.espn.com/mlb/team/roster/_/name/{team}/"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for table in soup.findAll("table"):
			for row in table.findAll("tr")[1:]:
				nameLink = row.findAll("td")[1].find("a").get("href").split("/")
				fullName = row.findAll("td")[1].find("a").text.lower().replace("'", "").replace("-", " ").replace(".", "")
				playerId = int(nameLink[-1])
				playerIds[team][fullName] = playerId
				roster[team][fullName] = row.findAll("td")[2].text.strip()

	with open(f"{prefix}static/baseballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/baseballreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

def convertTeamRankingsTeam(team):
	if team == "washington":
		return "wsh"
	elif team == "chi sox":
		return "chw"
	elif team == "chi cubs":
		return "chc"
	elif team == "sf giants":
		return "sf"
	elif team == "kansas city":
		return "kc"
	elif team == "san diego":
		return "sd"
	elif team == "tampa bay":
		return "tb"
	return team.replace(".", "").replace(" ", "")[:3]

def write_rankings():
	baseUrl = "https://www.teamrankings.com/mlb/stat/"
	pages = ["strikeouts-per-game", "walks-per-game", "runs-per-game", "hits-per-game", "home-runs-per-game", "singles-per-game", "doubles-per-game", "rbis-per-game", "total-bases-per-game", "earned-run-average", "earned-runs-against-per-game", "strikeouts-per-9", "home-runs-per-9", "hits-per-9", "walks-per-9"]
	ids = ["so", "bb", "r", "h", "hr", "1b", "2b", "rbi", "tb", "era", "er", "k", "hr_allowed", "hits_allowed", "bb_allowed"]

	rankings = {}
	for idx, page in enumerate(pages):
		url = baseUrl+page+"?date=2022-11-06"
		outfile = "out"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for row in soup.find("table").findAll("tr")[1:]:
			tds = row.findAll("td")
			team = convertTeamRankingsTeam(row.find("a").text.lower())
			if team not in rankings:
				rankings[team] = {}
			if ids[idx] not in rankings[team]:
				rankings[team][ids[idx]] = {}

			rankings[team][ids[idx]] = {
				"rank": int(tds[0].text),
				"season": float(tds[2].text.replace("--", "0").replace("%", "")),
				"last3": float(tds[3].text.replace("--", "0").replace("%", ""))
			}

	combined = []
	for team in rankings:
		combined.append({
			"team": team,
			"val": rankings[team]["h"]["season"]+rankings[team]["r"]["season"]+rankings[team]["rbi"]["season"]
		})

	for idx, x in enumerate(sorted(combined, key=lambda k: k["val"], reverse=True)):
		rankings[x["team"]]["h+r+rbi"] = {
			"rank": idx+1,
			"season": x["val"]
		}

	combined = []
	for team in rankings:
		combined.append({
			"team": team,
			"val": rankings[team]["hits_allowed"]["season"]+rankings[team]["er"]["season"]
		})

	for idx, x in enumerate(sorted(combined, key=lambda k: k["val"], reverse=True)):
		rankings[x["team"]]["h+r+rbi_allowed"] = {
			"rank": idx+1,
			"season": x["val"]
		}

	with open(f"{prefix}static/baseballreference/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--averages", help="Last Yr Averages", action="store_true")
	parser.add_argument("--rankings", help="Rankings", action="store_true")
	parser.add_argument("--roster", help="Roster", action="store_true")
	parser.add_argument("--schedule", help="Schedule", action="store_true")
	parser.add_argument("--totals", help="Totals", action="store_true")
	parser.add_argument("--stats", help="Stats", action="store_true")
	parser.add_argument("--ttoi", help="Team TTOI", action="store_true")
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	if args.start:
		curr_week = args.start

	date = args.date
	if not date:
		date = datetime.datetime.now()
		date = str(date)[:10]

	if args.averages:
		write_averages()
	elif args.rankings:
		write_rankings()
	elif args.roster:
		write_roster()
	elif args.cron:
		write_rankings()
		write_schedule(date)