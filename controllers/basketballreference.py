import argparse
import datetime
import glob
import json
import math
import os
import operator
import unicodedata
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
	with open(f"{prefix}static/basketballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/basketballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	if date not in boxscores:
		print("No games found for this date")
		exit()

	allStats = {}
	for game in boxscores[date]:
		away, home = map(str, game.split(" @ "))

		if away not in allStats:
			allStats[away] = {}
		if home not in allStats:
			allStats[home] = {}

		gameId = boxscores[date][game].split("/")[-2]
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/basketball/nba/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
		outfile = "outnba"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		if "boxscore" not in data or "players" not in data["boxscore"]:
			continue
		
		teamIds = {}
		for teamIdx, teamRow in enumerate(data["boxscore"]["players"]):
			team = away if teamIdx == 0 else home
			teamIds[teamRow["team"]["id"]] = team
			if team not in playerIds:
				playerIds[team] = {}	
			for statRow in teamRow["statistics"]:
				headers = []
				for hdr in statRow["labels"]:
					headers.append(hdr.lower())

				for playerRow in statRow["athletes"]:
					player = parsePlayer(playerRow["athlete"]["displayName"])
					playerIds[team][player] = playerRow["athlete"]["id"]
					if player not in allStats[team]:
						allStats[team][player] = {}
					for stat, hdr in zip(playerRow["stats"], headers):
						if hdr in ["fg", "3pt", "ft"]:
							s1,s2 = map(int, stat.split("-"))
							allStats[team][player][f"{hdr}m"] = s1
							allStats[team][player][f"{hdr}a"] = s2
						else:
							allStats[team][player][hdr] = int(stat)

		"""
		{"atl": {
			"teamThree": "curry,thompson",
			"three": "1,0,1",
			"point": "0,1,1",
			"teamPoint": "curry,kuminga",
			"teamPointFT"
		}}
		"""
		gameFirsts = {}
		for play in data["plays"]:
			if "team" not in play:
				continue
			team = teamIds[play["team"]["id"]]
			if play["scoringPlay"]:
				isThree = play["scoreValue"] == 3
				#gameFirsts[team]

	for team in allStats:
		if not os.path.isdir(f"{prefix}static/basketballreference/{team}"):
			os.mkdir(f"{prefix}static/basketballreference/{team}")
		with open(f"{prefix}static/basketballreference/{team}/{date}.json", "w") as fh:
			json.dump(allStats[team], fh, indent=4)

	write_totals()
	writeSplits()

	with open(f"{prefix}static/basketballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/basketballreference/"):
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/basketballreference/{team}/*.json"):
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
				if stats[player].get("min", 0) > 0:
					totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/basketballreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def writeSplits():
	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/basketballreference/scores.json") as fh:
		scores = json.load(fh)

	splits = {}
	for team in os.listdir(f"{prefix}static/basketballreference/"):
		if team not in splits:
			splits[team] = {}

		for file in sorted(glob(f"{prefix}static/basketballreference/{team}/*.json")):
			with open(file) as fh:
				stats = json.load(fh)

			if not stats:
				continue
				
			date = file.split("/")[-1][:-5]
			game = opp = awayHome = ""
			for g in schedule[date]:
				teams = g.split(" @ ")
				if team in teams:
					game = g
					opp = teams[0]
					awayHome = "H"
					if teams[0] == team:
						opp = teams[1]
						awayHome = "A"
					break
			score = scores[date][team]
			oppScore = scores[date][opp]
			winLoss = "W"
			if oppScore > score:
				winLoss = "L"

			for player in stats:
				if stats[player].get("min", 0) == 0:
					continue
				if player not in splits[team]:
					splits[team][player] = {"dt": []}

				if "winLoss" not in splits[team][player]:
					splits[team][player]["winLoss"] = []
				if "awayHome" not in splits[team][player]:
					splits[team][player]["awayHome"] = []
				splits[team][player]["awayHome"].append(awayHome)
				splits[team][player]["winLoss"].append(winLoss)
				splits[team][player]["dt"].append(date)

				for header in stats[player]:
					if header not in splits[team][player]:
						splits[team][player][header] = []
					splits[team][player][header].append(str(stats[player][header]))

				for prop in ["pts+ast", "pts+reb", "pts+reb+ast", "reb+ast", "stl+blk"]:
					if stats[player].get("min", 0) == 0:
						continue
					val = 0
					for p in prop.split("+"):
						val += int(stats[player][p])
					if prop not in splits[team][player]:
						splits[team][player][prop] = []
					splits[team][player][prop].append(str(val))

		for player in splits[team]:
			for hdr in splits[team][player]:
				splits[team][player][hdr] = ",".join(splits[team][player][hdr])

	with open(f"{prefix}static/basketballreference/splits.json", "w") as fh:
		json.dump(splits, fh, indent=4)

def write_averages():
	with open(f"{prefix}static/basketballreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/basketballreference/averages.json") as fh:
		averages = json.load(fh)

	with open(f"{prefix}static/basketballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	if 0:
		ids = {
			"mil": {
				"khris middleton": 6609
			}
		}

	headers = ["min", "fg", "fg%", "3pt", "3p%", "ft", "ft%", "reb", "ast", "blk", "stl", "pf", "to", "pts"]
	for team in ids:
		if team not in averages:
			averages[team] = {}
		if team not in lastYearStats:
			lastYearStats[team] = {}

		for player in ids[team]:
			pId = ids[team][player]
			if player in averages[team]:
				pass
				#continue
			
			gamesPlayed = 0
			averages[team][player] = {}
			lastYearStats[team][player] = {}

			time.sleep(0.175)
			url = f"https://www.espn.com/nba/player/gamelog/_/id/{pId}/type/nba/year/2023"
			outfile = "outnba"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			for row in soup.find_all("tr"):
				try:
					if "Regular Season" not in row.findPrevious("div", class_="Table__Title").text:
						continue
				except:
					continue
				if row.text.startswith("Averages"):
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

	with open(f"{prefix}static/basketballreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	with open(f"{prefix}static/basketballreference/lastYearStats.json", "w") as fh:
		json.dump(lastYearStats, fh, indent=4)


def write_schedule(date):
	url = f"https://www.espn.com/nba/schedule/_/date/{date.replace('-','')}"
	outfile = "outnba"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/basketballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/basketballreference/scores.json") as fh:
		scores = json.load(fh)

	for table in soup.find_all("div", class_="ResponsiveTable"):
		try:
			date = table.find("div", class_="Table__Title").text.strip()
		except:
			continue
		date = str(datetime.datetime.strptime(date, "%A, %B %d, %Y"))[:10]
		if date not in boxscores:
			boxscores[date] = {}
		if date not in scores:
			scores[date] = {}

		schedule[date] = []
		for row in table.find_all("tr")[1:]:
			tds = row.find_all("td")
			if not tds[0].find("a"):
				continue
			awayTeam = tds[0].find_all("a")[-1].get("href").split("/")[-2]
			if "TBD" in tds[1].text:
				continue
			homeTeam = tds[1].find_all("a")[-1].get("href").split("/")[-2]
			score = tds[2].find("a").text.strip()
			if "Postponed" in score or "Suspended" in score:
				continue
			if ", " in score:
				scoreSp = score.replace(" (2OT)", "").replace(" (OT)", "").split(", ")
				if f"{awayTeam.upper()} " in scoreSp[0]:
					scores[date][awayTeam] = int(scoreSp[0].replace(awayTeam.upper()+" ", ""))
					scores[date][homeTeam] = int(scoreSp[1].replace(homeTeam.upper()+" ", ""))
				else:
					scores[date][awayTeam] = int(scoreSp[1].replace(awayTeam.upper()+" ", ""))
					scores[date][homeTeam] = int(scoreSp[0].replace(homeTeam.upper()+" ", ""))
			boxscore = tds[2].find("a").get("href")
			boxscores[date][f"{awayTeam} @ {homeTeam}"] = boxscore
			schedule[date].append(f"{awayTeam} @ {homeTeam}")

	with open(f"{prefix}static/basketballreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/basketballreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/basketballreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

def convertTeamRankingsTeam(team):
	if team == "new orleans":
		return "no"
	elif team == "washington":
		return "wsh"
	elif team == "okla city":
		return "okc"
	elif team == "phoenix":
		return "phx"
	elif team == "san antonio":
		return "sa"
	elif team == "utah":
		return "utah"
	elif team == "brooklyn":
		return "bkn"
	elif team == "new york":
		return "ny"
	elif team == "golden state":
		return "gs"
	return team.replace(" ", "")[:3]

def convertFProsTeam(team):
	if team.startswith("uth"):
		return "utah"
	elif team.startswith("sas"):
		return "sa"
	elif team.startswith("pho"):
		return "phx"
	elif team.startswith("nyk"):
		return "ny"
	elif team.startswith("gsw"):
		return "gs"
	elif team.startswith("nor"):
		return "no"
	elif team.startswith("was"):
		return "wsh"
	return team.replace(" ", "")[:3]

def writeTotalsPerGame():
	pass

def write_rankings():
	url = "https://www.fantasypros.com/daily-fantasy/nba/fanduel-defense-vs-position.php"
	outfile = "outnba"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	allPos = ["PG", "SG", "SF", "PF", "C"]
	headers = ["pts","reb","ast","3ptm","stl","blk","to"]
	rankings = {}
	sortedRankings = {}
	for row in soup.find("table").find_all("tr")[1:]:
		pos = row.get("class")[-1]
		if pos not in allPos:
			continue
		if row.get("class")[0] != "GC-0":
			continue
		tds = row.find_all("td")
		team = convertFProsTeam(tds[0].text.lower().strip())
		if team not in rankings:
			rankings[team] = {}
		if pos not in rankings[team]:
			rankings[team][pos] = {}
		if pos not in sortedRankings:
			sortedRankings[pos] = []

		pts = float(tds[1].text.strip())
		reb = float(tds[2].text.strip())
		ast = float(tds[3].text.strip())
		j = {
			"pts": pts,
			"reb": reb,
			"ast": ast,
			"pts+ast": pts+ast,
			"pts+reb": pts+reb,
			"pts+reb+ast": pts+reb+ast,
			"reb+ast": reb+ast,
			"3ptm": float(tds[4].text.strip()),
			"stl": float(tds[5].text.strip()),
			"blk": float(tds[6].text.strip()),
			"stl+blk": float(tds[5].text.strip()) + float(tds[6].text.strip()),
			"to": float(tds[7].text.strip()),
		}
		rankings[team][pos] = j
		j["team"] = team
		sortedRankings[pos].append(j)

	allHeaders = ["pts", "reb", "ast", "pts+ast", "pts+reb", "pts+reb+ast", "reb+ast", "3ptm", "stl", "blk", "stl+blk", "to"]
	for header in allHeaders:
		for pos in allPos:
			sortedRanks = sorted(sortedRankings[pos], key=lambda k: (k[header]))
			for idx, rank in enumerate(sortedRanks):
				rankings[rank["team"]][pos][header+"_rank"] = idx+1

	with open(f"{prefix}static/basketballreference/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" sr", "").replace(" jr", "").replace(" iii", "").replace(" ii", "").replace(" iv", "")
	if player == "k caldwell pope":
		player = "kentavious caldwell pope"
	elif player == "cameron thomas":
		player = "cam thomas"
	elif player == "jadeney":
		player = "jaden ivey"
	elif player == "nicolas claxton":
		player = "nic claxton"
	elif player == "alex sarr":
		return "alexandre sarr"
	return player

def writePlayerIds():

	playerIds = {}
	roster = {}
	for team in ["bos", "bkn", "ny", "phi", "tor", "gs", "lac", "lal", "phx", "sac", "chi", "cle", "det", "ind", "mil", "atl", "cha", "mia", "orl", "wsh", "den", "min", "okc", "por", "utah", "dal", "hou", "mem", "no", "sa"]:
		time.sleep(0.175)
		url = f"https://www.espn.com/nba/team/roster/_/name/{team}"
		outfile = "outnba"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		playerIds[team] = {}
		roster[team] = {}
		for table in soup.find_all("table"):
			for row in table.find("tbody").find_all("tr"):
				pid = row.find_all("td")[1].find("a").get("href").split("/")[-2]
				player = parsePlayer(row.find_all("td")[1].find("a").text.lower())
				playerIds[team][player] = pid
				roster[team][player] = row.find_all("td")[2].text.strip()

	with open(f"{prefix}static/basketballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/basketballreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--ids", help="IDs", action="store_true")
	parser.add_argument("--totals", help="Tot", action="store_true")
	parser.add_argument("--rankings", help="Rankings", action="store_true")
	parser.add_argument("--roster", help="Roster", action="store_true")
	parser.add_argument("--averages", help="averages", action="store_true")
	parser.add_argument("--schedule", help="Schedule", action="store_true")
	parser.add_argument("--splits", help="Splits", action="store_true")
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
	elif args.averages:
		write_averages()
	elif args.rankings:
		write_rankings()
	elif args.ids:
		writePlayerIds()
	elif args.totals:
		write_totals()
	elif args.splits:
		writeSplits()
	elif args.cron:
		pass
		write_schedule(date)
		write_rankings()
		write_stats(date)
		#write_averages()
		
