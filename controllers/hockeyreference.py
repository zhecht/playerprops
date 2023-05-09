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

def write_stats(date):
	with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/hockeyreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	dates = [date]
	#dates = ["2022-10-11", "2022-10-12", "2022-10-13", "2022-10-14", "2022-10-15", "2022-10-17", "2022-10-18", "2022-10-19", "2022-10-20", "2022-10-21", "2022-10-22", "2022-10-23"]
	for date in dates:

		if date not in boxscores:
			print("No games found for this date, grabbing schedule")
			write_schedule(date)
			with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
				boxscores = json.load(fh)

		allStats = {}
		for game in boxscores[date]:
			away, home = map(str, game.split(" @ "))

			if away not in allStats:
				allStats[away] = {}
			if home not in allStats:
				allStats[home] = {}

			time.sleep(0.4)
			link = boxscores[date][game].replace("game?gameId=", "boxscore/_/gameId/")
			url = f"https://www.espn.com{link}"
			outfile = "outnhl"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			chkPre = soup.find("div", class_="ScoreCell__NotesWrapper")
			if chkPre and "preseason" in chkPre.text.strip().lower():
				continue

			# tables are split with players then stats, players -> stats
			headers = []
			playerList = []
			team = away
			for idx, table in enumerate(soup.findAll("table")[1:9]):
				if idx in [2,4,6]:
					playerList = []
				if idx == 4:
					team = home

				if team not in playerIds:
					playerIds[team] = {}

				playerIdx = 0
				for row in table.findAll("tr"):
					if idx in [0,2,4,6]:
						# PLAYERS
						if row.text.strip().lower() in ["skaters", "defensemen", "goalies"]:
							continue
						if not row.find("a"):
							continue
						nameLink = row.find("a").get("href").split("/")
						fullName = row.find("a").text.lower().title().replace("-", " ")
						if fullName.startswith("J.T."):
							fullName = fullName.replace("J.T.", "J.")
						elif fullName.startswith("J.J."):
							fullName = fullName.replace("J.J.", "J.")
						elif fullName.startswith("T.J."):
							fullName = fullName.replace("T.J.", "T.")
						elif fullName.startswith("A.J."):
							fullName = fullName.replace("A.J.", "A.")
						playerId = int(nameLink[-1])
						playerIds[team][fullName] = playerId
						playerList.append(fullName)
					else:
						# idx==1 or 3. STATS
						if not row.find("td"):
							continue
						firstTd = row.find("td").text.strip().lower()
						if firstTd in ["g", "sa"]:
							headers = []
							for td in row.findAll("td"):
								headers.append(td.text.strip().lower())
							continue

						try:
							player = playerList[playerIdx]
						except:
							continue
						playerIdx += 1
						playerStats = {}
						for tdIdx, td in enumerate(row.findAll("td")):
							header = headers[tdIdx]
							val = 0
							if header in ["toi", "pptoi", "shtoi", "estoi"]:
								valSp = td.text.strip().split(":")
								val = int(valSp[0])+round(int(valSp[1]) / 60, 2)
							else:
								val = float(td.text.strip())
							playerStats[header] = val

						allStats[team][player] = playerStats

		for team in allStats:
			if not os.path.isdir(f"{prefix}static/hockeyreference/{team}"):
				os.mkdir(f"{prefix}static/hockeyreference/{team}")
			if allStats[team]:
				with open(f"{prefix}static/hockeyreference/{team}/{date}.json", "w") as fh:
					json.dump(allStats[team], fh, indent=4)

	write_totals()

	with open(f"{prefix}static/hockeyreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/hockeyreference/"):
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/hockeyreference/{team}/*.json"):
			with open(file) as fh:
				stats = json.load(fh)
			for player in stats:
				if player not in totals[team]:
					totals[team][player] = stats[player]
				else:
					for header in stats[player]:
						if header not in totals[team][player]:
							totals[team][player][header] = 0
						totals[team][player][header] += stats[player][header]

				if "gamesPlayed" not in totals[team][player]:
					totals[team][player]["gamesPlayed"] = 0
				#print(team,player)
				if float(stats[player]["toi"]) > 0:
					totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/hockeyreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def convertStatMuseTeam(team):
	team = team.lower()
	if team.startswith("montreal"):
		return "mtl"
	elif team.endswith("islanders"):
		return "nyi"
	elif team.endswith("rangers"):
		return "nyr"
	elif team.endswith("devils"):
		return "nj"
	elif team.endswith("kings"):
		return "la"
	elif team.endswith("blues"):
		return "stl"
	elif team.endswith("flames"):
		return "cgy"
	elif team.endswith("capitals"):
		return "wsh"
	elif team.endswith("knights"):
		return "vgk"
	elif team.endswith("jackets"):
		return "cbj"
	elif team.endswith("jets"):
		return "wpg"
	elif team.endswith("panthers"):
		return "fla"
	elif team.endswith("lightning"):
		return "tb"
	elif team.endswith("sharks"):
		return "sj"
	elif team.endswith("predators"):
		return "nsh"
	return team[:3]

def writeRankings():
	baseurl = f"https://www.statmuse.com/nhl/ask/"

	rankings = {}
	shortIds = ["tot", "last1", "last3", "last5", "tot", "last1", "last3", "last5"]
	urls = ["nhl-team-saves-per-game-this-season", "nhl-team-saves-per-game-last-1-games", "nhl-team-saves-per-game-last-3-games", "nhl-team-saves-per-game-last-5-games", "nhl-team-saves-allowed-per-game-this-season", "nhl-team-saves-allowed-per-game-last-1-games", "nhl-team-saves-allowed-per-game-last-3-games", "nhl-team-saves-allowed-per-game-last-5-games"]
	for timePeriod, url in zip(shortIds, urls):
		outfile = "outnhl"
		time.sleep(0.3)
		call(["curl", "-k", baseurl+url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		ans = eval(soup.find("visual-answer").get("answer").replace("true", "True").replace("false", "False"))

		for row in ans["visual"]["detail"][0]["grids"][0]["rows"]:
			team = convertStatMuseTeam(row["TEAM"]["value"])
			if team not in rankings:
				rankings[team] = {}
			if timePeriod not in rankings[team]:
				rankings[team][timePeriod] = {}
			for stat in row:
				if stat in ["TEAM", "SEASON"]:
					continue
				try:
					rankings[team][timePeriod][stat] = row[stat]["value"]
				except:
					pass

	with open(f"{prefix}static/hockeyreference/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)

def writeTeamTTOI():
	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	teamTTOI = {}
	for team in os.listdir(f"{prefix}static/hockeyreference/"):
		if team.endswith(".json"):
			continue

		if team not in teamTTOI:
			teamTTOI[team] = {"ttoi": [], "oppTTOI": []}

		files = sorted(glob(f"{prefix}static/hockeyreference/{team}/*-*-*.json"), key=lambda k: datetime.datetime.strptime(k.split("/")[-1][:-5], "%Y-%m-%d"), reverse=True)
		for file in files:
			date = file.split("/")[-1][:-5]
			games = schedule[date]
			try:
				gameSp = [g.split(" @ ") for g in games if team in g.split(" @ ")][0]
			except:
				continue
			opp = gameSp[0] if team == gameSp[1] else gameSp[1]
			if opp not in teamTTOI:
				teamTTOI[opp] = {"ttoi": [], "oppTTOI": []}
			with open(file) as fh:
				stats = json.load(fh)
			toi = 0
			for player in stats:
				if stats[player].get("sv", 0) > 0:
					toi += stats[player]["toi"]
			teamTTOI[opp]["oppTTOI"].append(toi)
			teamTTOI[team]["ttoi"].append(toi)

	res = {}
	for team in teamTTOI:
		res[team] = {
			"ttoi": sum(teamTTOI[team]["ttoi"]),
			"ttoiL10": sum(teamTTOI[team]["ttoi"][:10]),
			"ttoiL5": sum(teamTTOI[team]["ttoi"][:5]),
			"ttoiL3": sum(teamTTOI[team]["ttoi"][:3]),
			"ttoiL1": sum(teamTTOI[team]["ttoi"][:1]),
			"oppTTOI": sum(teamTTOI[team]["oppTTOI"]),
			"oppTTOIL10": sum(teamTTOI[team]["oppTTOI"][:10]),
			"oppTTOIL5": sum(teamTTOI[team]["oppTTOI"][:5]),
			"oppTTOIL3": sum(teamTTOI[team]["oppTTOI"][:3]),
			"oppTTOIL1": sum(teamTTOI[team]["oppTTOI"][:1]),
		}

	with open(f"{prefix}static/hockeyreference/ttoi.json", "w") as fh:
		json.dump(res, fh, indent=4)


def write_averages():
	with open(f"{prefix}static/hockeyreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/hockeyreference/averages.json") as fh:
		averages = json.load(fh)

	with open(f"{prefix}static/hockeyreference/lastYearStats.json") as fh:
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
			url = f"https://www.espn.com/nhl/player/gamelog/_/id/{pId}/type/nhl/year/2022"
			outfile = "outnhl"
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
						if header in ["toi/g", "prod"]:
							valSp = td.text.strip().split(":")
							val = int(valSp[0])+round(int(valSp[1]) / 60, 2)
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
							if header == "toi/g" and float(td.text.strip().replace(":", ".")) > 0:
								gamesPlayed += 1

							val = 0.0
							if header in ["toi/g", "prod"]:
								valSp = td.text.strip().split(":")
								if len(valSp) > 1:
									val = int(valSp[0])+round(int(valSp[1]) / 60, 2)
							else:
								val = float(td.text.strip())
							lastYearStats[team][player][date][header] = val

	with open(f"{prefix}static/hockeyreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	if lastYearStats:
		with open(f"{prefix}static/hockeyreference/lastYearStats.json", "w") as fh:
			json.dump(lastYearStats, fh, indent=4)


def write_schedule(date):
	url = f"https://www.espn.com/nhl/schedule/_/date/{date.replace('-', '')}"
	outfile = "outnhl"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/hockeyreference/scores.json") as fh:
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
			if ", " in score and os.path.exists(f"{prefix}static/hockeyreference/{awayTeam}/{date}.json"):
				scoreSp = score.replace(" (SO)", "").replace(" (OT)", "").split(", ")
				if awayTeam == scoreSp[0].split(" ")[0].lower():
					scores[date][awayTeam] = int(scoreSp[0].split(" ")[1])
					scores[date][homeTeam] = int(scoreSp[1].split(" ")[1])
				else:
					scores[date][awayTeam] = int(scoreSp[1].split(" ")[1])
					scores[date][homeTeam] = int(scoreSp[0].split(" ")[1])
			boxscores[date][f"{awayTeam} @ {homeTeam}"] = boxscore
			schedule[date].append(f"{awayTeam} @ {homeTeam}")

	with open(f"{prefix}static/hockeyreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/hockeyreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/hockeyreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--averages", help="Last Yr Averages", action="store_true")
	parser.add_argument("--rankings", help="Rankings", action="store_true")
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

	if args.schedule:
		write_schedule(date)
	elif args.totals:
		write_totals()
	elif args.rankings:
		writeRankings()
	elif args.ttoi:
		writeTeamTTOI()
	elif args.averages:
		write_averages()
	elif args.stats:
		write_stats(date)
	elif args.cron:
		write_schedule(date)
		write_stats(date)
		write_schedule(date)
		writeRankings()
		writeTeamTTOI()