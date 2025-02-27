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

def write_schedule(date):
	url = f"https://www.espn.com/soccer/scoreboard/_/league/FIFA.WORLD/date/{date.replace('-','')}"
	outfile = "out"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/soccerreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/soccerreference/scores.json") as fh:
		scores = json.load(fh)

	schedule[date] = []
	if date not in scores:
		scores[date] = {}

	data = "{}"
	for script in soup.find_all("script"):
		if script.text.strip().startswith("window.espn.scoreboard"):
			m = re.search(r"window\.espn\.scoreboardData\s+=? (.*?)};", script.text)
			if m:
				data = m.group(1).replace("false", "False").replace("true", "True") + "}"
				break

	data = eval(data)

	for event in data["events"]:
		teams = ["",""]
		for teamData in event["competitions"][0]["competitors"]:
			idx = 0
			if teamData["homeAway"] == "home":
				idx = 1
			team = teamData["team"]["shortDisplayName"].lower()
			score = int(teamData["score"])
			scores[date][team] = score
			teams[idx] = team
		schedule[date].append(" @ ".join(teams))
	with open(f"{prefix}static/soccerreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/soccerreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

def writeCSV():
	date = datetime.datetime.now()
	date = str(date)[:10]

	with open(f"{prefix}static/soccerreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/soccerreference/scores.json") as fh:
		scores = json.load(fh)

	with open(f"{prefix}static/soccerreference/teams.json") as fh:
		teams = json.load(fh)

	year,mon,day = map(int, date.split("-"))

	totals = {}
	for date in schedule:
		year,mon,day = map(int, date.split("-"))
		for game in schedule[date]:
			gameSp = game.split(" @ ")
			for idx, team in enumerate(gameSp):
				oppScore = scores[date][gameSp[0]] if idx == 1 else scores[date][gameSp[1]]
				score = scores[date][team]
				if team not in totals:
					totals[team] = {"goals": 0, "w": 0, "l":0, "t": 0, "pts": 0, "games": 0, "r16w": 0}
				totals[team]["goals"] += score
				totals[team]["games"] += 1

				if date == "2022-12-05":
					if team == "croatia":
						score = 3
					elif team == "japan":
						oppScore = 3
				elif date == "2022-12-06":
					if team == "morocco":
						score = 3
					elif team == "spain":
						oppScore = 3
				elif date == "2022-12-09":
					if team == "croatia":
						score = 4
					elif team == "brazil":
						oppScore = 4
					elif team == "netherlands":
						oppScore = 4
					elif team == "argentina":
						score = 4

				if score == oppScore:
					totals[team]["t"] += 1
					totals[team]["pts"] += 1
				elif score > oppScore:
					totals[team]["w"] += 1
					totals[team]["pts"] += 2
					if mon == 12 and day >= 3:
						totals[team]["pts"] += 1
						totals[team]["r16w"] += 1
					if mon == 12 and day == 18:
						totals[team]["pts"] += 1
				else:
					totals[team]["l"] += 1

	res = []
	for duder in teams:
		totPts = totr16 = totTies = totWins = totGames = totGoals = 0
		for team in teams[duder]:
			totPts += totals[team]["pts"]
			totTies += totals[team]["t"]
			totWins += totals[team]["w"]
			totr16 += totals[team]["r16w"]
			totGames += totals[team]["games"]
			totGoals += totals[team]["goals"]

		res.append({
			"duder": duder,
			"teams": ",".join(teams[duder]),
			"pts": totPts,
			"ties": totTies,
			"wins": totWins,
			"r16wins": totr16,
			"games": totGames,
			"goals": totGoals
		})

	res = sorted(res, key=lambda k: (k["pts"], k["wins"], k["goals"]), reverse=True)
	out = "\t".join(["", "TEAMS","PTS","GAMES","WINS","R16 WINS","TIES","GOALS"]) + "\n"
	for row in res:
		out += "\t".join([str(x) for x in [
			row["duder"].upper(), row["teams"], row["pts"], row["games"], row["wins"], row["r16wins"], row["ties"], row["goals"]
		]]) + "\n"

	with open(f"{prefix}static/soccerreference/out.csv", "w") as fh:
		fh.write(out)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--rankings", help="Rankings", action="store_true")
	parser.add_argument("--roster", help="Roster", action="store_true")
	parser.add_argument("--averages", help="averages", action="store_true")
	parser.add_argument("--schedule", help="Schedule", action="store_true")
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.datetime.now()
		date = str(date)[:10]

	if args.schedule:
		write_schedule(date)
	elif args.cron:
		pass
		write_schedule(date)
		#write_stats(date)
	else:
		writeCSV()
