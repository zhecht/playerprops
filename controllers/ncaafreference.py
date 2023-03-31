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

SPORT_PREFIX = f"{prefix}static/ncaafreference"

def write_stats(date, teamArg=""):
	with open(f"{SPORT_PREFIX}/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{SPORT_PREFIX}/teams.json") as fh:
		teams = json.load(fh)

	playerIds = {}
	if os.path.exists(f"{SPORT_PREFIX}/playerIds.json"):
		with open(f"{SPORT_PREFIX}/playerIds.json") as fh:
			playerIds = json.load(fh)

	roster = {}
	if os.path.exists(f"{SPORT_PREFIX}/roster.json"):
		with open(f"{SPORT_PREFIX}/roster.json") as fh:
			roster = json.load(fh)

	if date not in boxscores:
		print("No games found for this date")
		exit()

	allStats = {}
	for date in boxscores:
		allStats[date] = {}
		for game in boxscores[date]:
			away, home = map(str, game.split(" @ "))

			if teamArg and teamArg not in game.split(" @ "):
				continue

			if away not in allStats[date]:
				allStats[date][away] = {}
			if home not in allStats[date]:
				allStats[date][home] = {}

			gameId = boxscores[date][game].split("/")[-1]
			time.sleep(0.25)
			url = f"https://site.web.api.espn.com/apis/site/v2/sports/football/college-football/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
			outfile = "out"
			call(["curl", "-k", url, "-o", outfile])

			with open("out") as fh:
				data = json.load(fh)

			#with open("out2", "w") as fh:
			#	json.dump(data, fh, indent=4)

			if "code" in data and data["code"] == 400:
				continue

			if "players" not in data["boxscore"]:
				continue
			for teamRow in data["boxscore"]["players"]:
				team = teamRow["team"]["abbreviation"].lower()
				if team not in playerIds:
					playerIds[team] = {}
				if team not in roster:
					roster[team] = {}

				for statRow in teamRow["statistics"]:
					title = statRow["name"]
					shortHeader = ""
					if title == "receiving":
						shortHeader = "rec"
					elif title == "defensive":
						shortHeader = "def"
					elif title == "interceptions":
						shortHeader = "def_int"
					elif title in ["puntReturns", "kickReturns", "punting", "fumbles"]:
						shortHeader = title
					else:
						shortHeader = title[:4]

					headers = [h.lower() for h in statRow["labels"]]
					for playerRow in statRow["athletes"]:
						player = playerRow["athlete"]["displayName"].lower().replace("'", "").replace(".", "")
						playerId = int(playerRow["athlete"]["id"])

						playerIds[team][player] = playerId
						if player not in allStats[date][team]:
							allStats[date][team][player] = {}

						for header, stat in zip(headers, playerRow["stats"]):
							if header == "car":
								header = "rush_att"
							elif header == "rec":
								if shortHeader == "fumbles":
									header = "fumbles_recovered"
								else:
									header = "rec"
							elif header == "fum":
								header = "fumbles"
							elif header == "lost":
								header = "fumbles_lost"
							elif header == "tot":
								header = "tackles_combined"
							elif header == "solo":
								header = "tackles_solo"
							elif shortHeader == "def" and header == "td":
								header = "def_td"
							elif shortHeader == "def_int" and header == "int":
								header = "def_int"
							elif shortHeader in ["pass", "rush", "rec", "def_int", "returns"]:
								header = f"{shortHeader}_{header}"

							if header == "pass_c/att":
								made, att = map(int, stat.split("/"))
								allStats[date][team][player]["pass_cmp"] = made
								allStats[date][team][player]["pass_att"] = att
							elif header in ["xp", "fg"]:
								made, att = map(int, stat.split("/"))
								allStats[date][team][player][header+"m"] = made
								allStats[date][team][player][header+"a"] = att
							elif header == "pass_sacks":
								made, att = map(int, stat.split("-"))
								allStats[date][team][player]["pass_sacks"] = made
							else:
								val = stat
								try:
									val = float(val)
								except:
									val = 0.0
								allStats[date][team][player][header] = val

	for date in allStats:
		for team in allStats[date]:
			if not os.path.isdir(f"{prefix}static/ncaafreference/{team}"):
				os.mkdir(f"{prefix}static/ncaafreference/{team}")
			with open(f"{prefix}static/ncaafreference/{team}/{date}.json", "w") as fh:
				json.dump(allStats[date][team], fh, indent=4)

	write_totals()

	with open(f"{prefix}static/ncaafreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/ncaafreference/"):
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/ncaafreference/{team}/*-*-*.json"):
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
				totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/ncaafreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def write_averages():
	with open(f"{prefix}static/ncaafreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/ncaafreference/averages.json") as fh:
		averages = json.load(fh)

	lastYearStats = {}
	headers = ["min", "fg", "fg%", "3pt", "3p%", "ft", "ft%", "reb", "ast", "blk", "stl", "pf", "to", "pts"]
	for team in ids:
		if team not in averages:
			averages[team] = {}

		lastYearStats[team] = {}
		if os.path.exists(f"{prefix}static/ncaafreference/{team}/lastYearStats.json"):
			with open(f"{prefix}static/ncaafreference/{team}/lastYearStats.json") as fh:
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
			url = f"https://www.espn.com/college-football/player/gamelog/_/id/{pId}/type/college-football/year/2022"
			outfile = "out3"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			for row in soup.findAll("tr"):
				if row.text.lower().startswith("total"):
					for idx, td in enumerate(row.findAll("td")[1:]):
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
					tds = row.findAll("td")
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

		with open(f"{prefix}static/ncaafreference/averages.json", "w") as fh:
			json.dump(averages, fh, indent=4)

		with open(f"{prefix}static/ncaafreference/{team}/lastYearStats.json", "w") as fh:
			json.dump(lastYearStats[team], fh, indent=4)

def writeTeamId(teams, team):
	time.sleep(0.3)
	url = f"https://site.web.api.espn.com/apis/site/v2/sports/football/college-football/teams?region=us&lang=en&contentorigin=espn&limit=400"
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
	with open(f"{prefix}static/ncaafreference/teams.json") as fh:
		teams = json.load(fh)
	with open(f"{prefix}static/ncaafreference/playerIds.json") as fh:
		playerIds = json.load(fh)
	with open(f"{prefix}static/ncaafreference/roster.json") as fh:
		roster = json.load(fh)

	for team in os.listdir(f"{prefix}static/ncaafreference/"):
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
		url = f"https://www.espn.com/college-football/team/roster/_/id/{teamId}/"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		if not soup.find("table"):
			continue

		for row in soup.find("table").findAll("tr")[1:]:
			nameLink = row.findAll("td")[1].find("a").get("href").split("/")
			fullName = nameLink[-1].replace("-", " ")
			playerId = int(nameLink[-2])
			playerIds[team][fullName] = playerId
			roster[team][fullName] = row.findAll("td")[2].text.strip()

	with open(f"{prefix}static/ncaafreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/teams.json", "w") as fh:
		json.dump(teams, fh, indent=4)

def writeMissingTeamStats(teamArg):
	date = datetime.datetime.now()
	year = str(date)[:4]

	with open(f"{prefix}static/ncaafreference/teams.json") as fh:
		teams = json.load(fh)

	with open(f"{prefix}static/ncaafreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/ncaafreference/scores.json") as fh:
		scores = json.load(fh)

	with open(f"{prefix}static/ncaafreference/schedule.json") as fh:
		schedule = json.load(fh)
	
	for team in teamArg.lower().split(","):
		if team not in teams:
			writeTeamId(teams, team)
		teamId = teams[team]["id"]

		time.sleep(0.3)
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/football/college-football/teams/{teamId}/schedule?region=us&lang=en&seasontype=2"
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
					scores[date][t] = {
						"quarters": 0,
						"score": teamRow["score"]["value"]
					}

	with open(f"{prefix}static/ncaafreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/teams.json", "w") as fh:
		json.dump(teams, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

	for team in teamArg.lower().split(","):
		for date in schedule:
			for game in schedule[date]:
				if team in game.split(" @ ") and not os.path.exists(f"{prefix}static/ncaafreference/{team}/{date}.json"):
					write_stats(date, teamArg=team)

def write_schedule(date):
	#url = f"https://www.espn.com/college-football/schedule/_/date/{date.replace('-','')}"
	boxscores = {}
	schedule = {}
	teams = {}
	scores = {}

	try:
		with open(f"{prefix}static/ncaafreference/boxscores.json") as fh:
			boxscores = json.load(fh)
	except:
		pass

	try:
		with open(f"{prefix}static/ncaafreference/schedule.json") as fh:
			schedule = json.load(fh)
	except:
		pass

	try:
		with open(f"{prefix}static/ncaafreference/teams.json") as fh:
			teams = json.load(fh)
	except:
		pass

	try:
		with open(f"{prefix}static/ncaafreference/scores.json") as fh:
			scores = json.load(fh)
	except:
		pass

	today = datetime.datetime.now()
	today = str(today)[:10]

	for week in range(1,16):
		for group in [80]:
			time.sleep(0.3)
			url = f"https://www.espn.com/college-football/scoreboard/_/date/{today.replace('-', '')}/week/{week}/year/{today[:4]}/seasontype/2/group/{group}?_xhr=pageContent"
			outfile = "out"
			call(["curl", "-k", url, "-o", outfile])

			with open("out") as fh:
				data = json.load(fh)

			#with open("out2", "w") as fh:
			#	json.dump(data, fh, indent=4)

			for gameRow in data["scoreboard"]["evts"]:
				dt = datetime.datetime.strptime(gameRow["date"], "%Y-%m-%dT%H:%MZ") - datetime.timedelta(hours=5)
				dt = str(dt)[:10]

				if dt not in boxscores:
					boxscores[dt] = {}
				if dt not in scores:
					scores[dt] = {}
				if dt not in schedule:
					schedule[dt] = []

				game = ["", ""]
				for teamRow in gameRow["competitors"]:
					team = teamRow["abbrev"].lower()
					isHome = teamRow["isHome"]
					teams[team] = {
						"display": teamRow["displayName"],
						"id": teamRow["id"]
					}
					if isHome:
						game[1] = team
					else:
						game[0] = team


				quarterScoring = [[], []]
				if "lnescrs" in gameRow:
					for awayHome in gameRow["lnescrs"]:
						if awayHome == "lbls":
							continue
						idx = 0
						if awayHome == "hme":
							idx = 1
						scored = [x for x in gameRow["lnescrs"][awayHome]]

						scores[dt][game[idx]] = {
							"quarters": ",".join([str(x) for x in scored]),
							"score": sum(scored)
						}

				game = " @ ".join(game)

				boxscores[dt][game] = gameRow["link"].split("/")[-1]
				if game not in schedule[dt]:
					schedule[dt].append(game)

	with open(f"{prefix}static/ncaafreference/teams.json", "w") as fh:
		json.dump(teams, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/ncaafreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

def writePlayerIds():
	with open(f"{prefix}static/ncaafreference/teams.json") as fh:
		teams = json.load(fh)

	with open(f"{prefix}static/ncaafreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	for team in teams:
		teamId = teams[team]
		playerIds[team] = {}
		url = f"https://www.espn.com/college-football/team/roster/_/id/{teamId}"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for tr in soup.find("div", class_="ResponsiveTable").findAll("tr")[1:]:
			td = tr.findAll("td")[1].find("a")
			playerIds[team][td.text.strip()] = int(td.get("href").split("/")[-2])

		with open(f"{prefix}static/ncaafreference/playerIds.json", "w") as fh:
			json.dump(playerIds, fh, indent=4)

def writeColors():

	with open(f"{prefix}static/ncaafreference/teams.json") as fh:
		teams = json.load(fh)

	displayTeams = {teams[team]["display"].lower(): team for team in teams}

	url = "https://teamcolorcodes.com/ncaa-color-codes/"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	colors = {}
	css = ""
	for link in [a.get("href") for a in soup.findAll("a", class_="team-button")]:
		time.sleep(0.3)
		outfile = "out"
		call(["curl", "-k", link, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for teamLink in soup.findAll("a", class_="team-button"):
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

	with open(f"{prefix}static/ncaafreference/colors.json", "w") as fh:
		json.dump(colors, fh, indent=4)

	with open(f"{prefix}static/css/ncaafteams.css", "w") as fh:
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
		write_averages()
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
		#write_schedule(date)
		write_stats(date)