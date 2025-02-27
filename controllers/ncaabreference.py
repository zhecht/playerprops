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

def write_stats(date, teamArg=""):
	with open(f"{prefix}static/ncaabreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/ncaabreference/teams.json") as fh:
		teams = json.load(fh)

	with open(f"{prefix}static/ncaabreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	with open(f"{prefix}static/ncaabreference/roster.json") as fh:
		roster = json.load(fh)

	if date not in boxscores:
		print("No games found for this date")
		exit()

	allStats = {}
	for game in boxscores[date]:
		away, home = map(str, game.split(" @ "))

		if teamArg and teamArg not in game.split(" @ "):
			continue

		if away not in allStats:
			allStats[away] = {}
		if home not in allStats:
			allStats[home] = {}

		gameId = boxscores[date][game].split("/")[-1]
		time.sleep(0.2)
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		#with open("out2", "w") as fh:
		#	json.dump(data, fh, indent=4)

		if "code" in data and data["code"] == 400:
			continue

		if "boxscore" not in data:
			continue
		if "players" not in data["boxscore"]:
			continue
		for teamRow in data["boxscore"]["players"]:
			team = teamRow["team"]["abbreviation"].lower()
			if team not in playerIds:
				playerIds[team] = {}
			if team not in roster:
				roster[team] = {}
			headers = [h.lower() for h in teamRow["statistics"][0]["names"]]

			for playerRow in teamRow["statistics"][0]["athletes"]:
				if playerRow["didNotPlay"]:
					continue
				player = playerRow["athlete"]["displayName"].lower().replace(".", "").replace("'", "").replace("-", " ")
				playerId = int(playerRow["athlete"]["id"])
				pos = playerRow["athlete"]["position"]["abbreviation"]

				playerIds[team][player] = playerId
				allStats[team][player] = {}
				roster[team][player] = pos

				for header, stat in zip(headers, playerRow["stats"]):
					if "-" in stat:
						try:
							made, att = map(int, stat.split("-"))
						except:
							made = att = 0
						allStats[team][player][header+"m"] = made
						allStats[team][player][header+"a"] = att
					else:
						allStats[team][player][header] = int(stat)

	for team in allStats:
		if not os.path.isdir(f"{prefix}static/ncaabreference/{team}"):
			os.mkdir(f"{prefix}static/ncaabreference/{team}")
		with open(f"{prefix}static/ncaabreference/{team}/{date}.json", "w") as fh:
			json.dump(allStats[team], fh, indent=4)

	write_totals()

	with open(f"{prefix}static/ncaabreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/ncaabreference/"):
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/ncaabreference/{team}/*-*-*.json"):
			with open(file) as fh:
				stats = json.load(fh)
			for player in stats:
				if player not in totals[team]:
					totals[team][player] = stats[player]
				else:
					for header in stats[player]:
						if header not in totals[team][player]:
							totals[team][player][header] = 0
						try:
							totals[team][player][header] += stats[player][header]
						except:
							pass

				if "gamesPlayed" not in totals[team][player]:
					totals[team][player]["gamesPlayed"] = 0
				if stats[player].get("min", 0) > 0:
					totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/ncaabreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def write_averages(teams = []):
	with open(f"{prefix}static/ncaabreference/playerIds.json") as fh:
		ids = json.load(fh)

	if not teams:
		teams = ids.keys()

	with open(f"{prefix}static/ncaabreference/averages.json") as fh:
		averages = json.load(fh)

	lastYearStats = {}
	headers = ["min", "fg", "fg%", "3pt", "3p%", "ft", "ft%", "reb", "ast", "blk", "stl", "pf", "to", "pts"]
	for team in teams:
		if team not in averages:
			averages[team] = {}

		lastYearStats[team] = {}
		if os.path.exists(f"{prefix}static/ncaabreference/{team}/lastYearStats.json"):
			with open(f"{prefix}static/ncaabreference/{team}/lastYearStats.json") as fh:
				lastYearStats[team] = json.load(fh)

		for player in ids[team]:
			pId = ids[team][player]
			if player in averages[team]:
				pass
				continue
			
			gamesPlayed = 0
			averages[team][player] = {}
			lastYearStats[team][player] = {}

			time.sleep(0.25)
			url = f"https://www.espn.com/mens-college-basketball/player/gamelog/_/id/{pId}/type/mens-college-basketball/year/2022"
			outfile = "out3"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			for row in soup.find_all("tr"):
				if row.text.lower().startswith("total"):
					for idx, td in enumerate(row.find_all("td")[1:]):
						header = headers[idx]
						if header in ["fg", "3pt", "ft"]:
							made, att = map(float, td.text.strip().split("-"))
							averages[team][player][header+"a"] = att
							averages[team][player][header+"m"] = made
						else:
							val = float(td.text.strip())
							averages[team][player][header] = val
					averages[team][player]["gamesPlayed"] = gamesPlayed
				else:
					tds = row.find_all("td")
					if len(tds) > 1 and ("@" in tds[1].text or "vs" in tds[1].text):
						date = str(datetime.datetime.strptime(tds[0].text.strip(), "%a %m/%d")).split(" ")[0][6:]
						lastYearStats[team][player][date] = {}
						for idx, td in enumerate(tds[3:]):
							header = headers[idx]
							if header == "min" and int(td.text.strip()) > 0:
								gamesPlayed += 1

							if header in ["fg", "3pt", "ft"]:
								made, att = map(int, td.text.strip().split("-"))
								lastYearStats[team][player][date][header+"a"] = att
								lastYearStats[team][player][date][header+"m"] = made
							else:
								val = float(td.text.strip())
								lastYearStats[team][player][date][header] = val

		with open(f"{prefix}static/ncaabreference/averages.json", "w") as fh:
			json.dump(averages, fh, indent=4)

		with open(f"{prefix}static/ncaabreference/{team}/lastYearStats.json", "w") as fh:
			json.dump(lastYearStats[team], fh, indent=4)

def writeTeamId(teams, team):
	time.sleep(0.3)
	url = f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams?region=us&lang=en&contentorigin=espn&limit=400"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	for t in data["sports"][0]["leagues"][0]["teams"]:
		if t["team"]["abbreviation"].lower() == team:
			teams[team] = {
				"display": t["team"]["displayName"],
				"id": t["team"]["id"]
			}
			break

def writeRosters():
	with open(f"{prefix}static/ncaabreference/teams.json") as fh:
		teams = json.load(fh)
	with open(f"{prefix}static/ncaabreference/playerIds.json") as fh:
		playerIds = json.load(fh)
	with open(f"{prefix}static/ncaabreference/roster.json") as fh:
		roster = json.load(fh)

	for team in os.listdir(f"{prefix}static/ncaabreference/"):
		if team.endswith(".json"):
			continue

		if team in roster:
			#pass
			continue

		roster[team] = {}
		if team not in teams:
			writeTeamId(teams, team)
		if team not in teams:
			continue
		teamId = teams[team]["id"]

		if team not in playerIds:
			playerIds[team] = {}

		time.sleep(0.3)
		url = f"https://www.espn.com/mens-college-basketball/team/roster/_/id/{teamId}/"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		if not soup.find("table"):
			continue

		for row in soup.find("table").find_all("tr")[1:]:
			nameLink = row.find_all("td")[1].find("a").get("href").split("/")
			fullName = nameLink[-1].replace("-", " ")
			playerId = int(nameLink[-2])
			playerIds[team][fullName] = playerId
			roster[team][fullName] = row.find_all("td")[2].text.strip()

	with open(f"{prefix}static/ncaabreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/teams.json", "w") as fh:
		json.dump(teams, fh, indent=4)

def writeMissingTeamStats(teamArg):
	date = datetime.datetime.now()
	year = str(date)[:4]

	with open(f"{prefix}static/ncaabreference/teams.json") as fh:
		teams = json.load(fh)

	with open(f"{prefix}static/ncaabreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/ncaabreference/scores.json") as fh:
		scores = json.load(fh)

	with open(f"{prefix}static/ncaabreference/schedule.json") as fh:
		schedule = json.load(fh)
	
	for team in teamArg.lower().split(","):
		if team not in teams:
			writeTeamId(teams, team)
		teamId = teams[team]["id"]

		time.sleep(0.2)
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{teamId}/schedule?region=us&lang=en&seasontype=2"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		for row in data["events"]:
			dt = datetime.datetime.strptime(row["date"],"%Y-%m-%dT%H:%MZ") - datetime.timedelta(hours=5)
			date = str(dt)[:10]
			if datetime.datetime.strptime(date, "%Y-%m-%d") > datetime.datetime.strptime(str(datetime.datetime.now())[:10], "%Y-%m-%d"):
				continue
			game = row["shortName"].lower()

			if date not in schedule:
				schedule[date] = []
			if date not in boxscores:
				boxscores[date] = {}
			if date not in scores:
				scores[date] = {}
			if game not in schedule[date]:
				schedule[date].append(game)
				boxscores[date][game] = row["id"]
				for teamRow in row["competitions"][0]["competitors"]:
					t = teamRow["team"]["abbreviation"].lower()
					if "score" not in teamRow:
						continue
					scores[date][t] = teamRow["score"]["value"]
			else:
				for teamRow in row["competitions"][0]["competitors"]:
					t = teamRow["team"]["abbreviation"].lower()
					if "score" not in teamRow:
						continue
					scores[date][t] = teamRow["score"]["value"]

	with open(f"{prefix}static/ncaabreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/teams.json", "w") as fh:
		json.dump(teams, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

	for team in teamArg.lower().split(","):
		for date in schedule:
			for game in schedule[date]:
				if team in game.split(" @ "):
					if not os.path.exists(f"{prefix}static/ncaabreference/{team}/{date}.json"):
						write_stats(date, teamArg=team)
					else:
						with open(f"{prefix}static/ncaabreference/{team}/{date}.json") as fh:
							data = json.load(fh)
						if len(data.keys()) == 0:
							write_stats(date, teamArg=team)


def write_schedule(date):
	#url = f"https://www.espn.com/mens-college-basketball/schedule/_/date/{date.replace('-','')}"
	with open(f"{prefix}static/ncaabreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/ncaabreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/ncaabreference/teams.json") as fh:
		teams = json.load(fh)

	with open(f"{prefix}static/ncaabreference/scores.json") as fh:
		scores = json.load(fh)

	#time.sleep(0.4)
	url = f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?region=us&lang=en&contentorigin=espn&limit=300&dates={date.replace('-','')}&seasontype=2&groups=50&tz=America/New_York"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	#with open("out2", "w") as fh:
	#	json.dump(data, fh, indent=4)

	boxscores[date] = {}
	scores[date] = {}
	schedule[date] = []

	for gameRow in data["events"]:
		game = gameRow["shortName"].lower()

		for teamData in gameRow["competitions"][0]["competitors"]:
			team = game.split(" @ ")[0] if teamData["homeAway"] == "away" else game.split(" @ ")[1]
			teams[team] = {
				"display": teamData["team"]["displayName"],
				"id": teamData["team"]["id"]
			}
			scores[date][team] = int(teamData["score"])

		boxscores[date][game] = gameRow["links"][0]["href"].split("/")[-1]
		schedule[date].append(game)
		#dt = dt + datetime.timedelta(days=1)

	with open(f"{prefix}static/ncaabreference/teams.json", "w") as fh:
		json.dump(teams, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/ncaabreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

def writePlayerIds():
	with open(f"{prefix}static/ncaabreference/teams.json") as fh:
		teams = json.load(fh)

	with open(f"{prefix}static/ncaabreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	for team in teams:
		teamId = teams[team]
		playerIds[team] = {}
		url = f"https://www.espn.com/mens-college-basketball/team/roster/_/id/{teamId}"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for tr in soup.find("div", class_="ResponsiveTable").find_all("tr")[1:]:
			td = tr.find_all("td")[1].find("a")
			playerIds[team][td.text.strip()] = int(td.get("href").split("/")[-2])

		with open(f"{prefix}static/ncaabreference/playerIds.json", "w") as fh:
			json.dump(playerIds, fh, indent=4)

def writeColors():

	with open(f"{prefix}static/ncaabreference/teams.json") as fh:
		teams = json.load(fh)

	displayTeams = {teams[team]["display"].lower(): team for team in teams}

	url = "https://teamcolorcodes.com/ncaa-color-codes/"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	colors = {}
	css = ""
	for link in [a.get("href") for a in soup.find_all("a", class_="team-button")]:
		time.sleep(0.3)
		outfile = "out"
		call(["curl", "-k", link, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for teamLink in soup.find_all("a", class_="team-button"):
			team = teamLink.text.lower().replace("'", "").replace(".", "").replace(")", "").replace("(", "").replace("&", "")
			styles = {}
			for style in teamLink.get("style").split(";"):
				k,v = style.strip().split(":")
				styles[k] = v

			if "color" not in styles:
				styles["color"] = "#fff"

			if team in displayTeams:
				team = displayTeams[team]
			elif team[:4] in teams:
				team = team[:4]
			colors[team] = {
				"color": styles["color"],
				"background-color": styles["background-color"]
			}
			css += f".{team.replace(' ', '-')} {{\n"
			css += f"\tcolor: {styles['color']};\n"
			css += f"\tbackground-color: {styles['background-color']};\n"
			css += f"}}\n\n"

	with open(f"{prefix}static/ncaabreference/colors.json", "w") as fh:
		json.dump(colors, fh, indent=4)

	with open(f"{prefix}static/css/ncaabteams.css", "w") as fh:
		fh.write(css)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--averages", help="Last Yr Averages", action="store_true")
	parser.add_argument("--colors", help="Colors", action="store_true")
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-t", "--teams", help="Teams")
	parser.add_argument("--roster", help="Roster", action="store_true")
	parser.add_argument("--totals", help="Totals", action="store_true")
	parser.add_argument("--schedule", help="Schedule", action="store_true")
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	if args.start:
		curr_week = args.start

	date = args.date
	if not date:
		date = datetime.datetime.now()
		date = str(date)[:10]

	#writePlayerIds()
	if args.averages:
		teams = []
		if args.teams:
			teams = args.teams.split(",")
		write_averages(teams)
	elif args.colors:
		writeColors()
	elif args.roster:
		writeRosters()
	elif args.schedule:
		write_schedule(date)
	elif args.teams:
		writeMissingTeamStats(args.teams)
	elif args.totals:
		write_totals()
	elif args.cron:
		write_schedule(date)
		write_stats(date)