import argparse
import datetime
import glob
import json
import math
import os
import operator
import re
import time
import csv
import unicodedata

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
	with open(f"{prefix}static/baseballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)

	if date not in boxscores:
		print("No games found for this date")
		exit()

	dates = [date]
	#dates = ["2023-03-30", "2023-03-31", "2023-04-01", "2023-04-02", "2023-04-03", "2023-04-04", "2023-04-05", "2023-04-06", "2023-04-07", "2023-04-08", "2023-04-09", "2023-04-10", "2023-04-11", "2023-04-12"]
	for date in dates:
		allStats = {}
		for game in boxscores[date]:
			if game not in schedule[date]:
				print("Game not in schedule")
				continue
			away, home = map(str, game.split(" @ "))

			gameId = boxscores[date][game].split("/")[-2]
			url = f"https://site.web.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
			outfile = "outmlb2"
			time.sleep(0.3)
			call(["curl", "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "code" in data and data["code"] == 400:
				continue

			if "boxscore" not in data or "players" not in data["boxscore"] or "plays" not in data:
				continue

			if away not in allStats:
				allStats[away] = {}
			if home not in allStats:
				allStats[home] = {}

			#scores[away][date]["innings"] = []
			for row in data["plays"]:
				txt = row.get("text", "").lower()
				if "inning" in txt and txt.startswith("end"):
					inning = txt.split(" ")[3][:-2]

					#print(txt, row["awayScore"], row["homeScore"])

			lastNames = {}
			for teamRow in data["boxscore"]["players"]:
				team = teamRow["team"]["abbreviation"].lower()
				t = team+" gm2" if "gm2" in away else team

				if team not in playerIds:
					playerIds[team] = {}
				if team not in lastNames:
					lastNames[team] = {}

				for statRow in teamRow["statistics"]:
					title = statRow["type"]

					headers = [h.lower() for h in statRow["labels"]]

					for playerRow in statRow["athletes"]:
						player = parsePlayer(playerRow["athlete"]["displayName"])
						playerId = int(playerRow["athlete"]["id"])
						lastNames[team][player.split(" ")[-1]] = player

						playerIds[team][player] = playerId
						if player not in allStats[t]:
							allStats[t][player] = {}

						pitchingDecision = ""
						if "notes" in playerRow and playerRow["notes"][0]["type"] == "pitchingDecision":
							pitchingDecision = playerRow["notes"][0]["text"][0].lower()
							if pitchingDecision == "h":
								pitchingDecision = "hold"
							elif pitchingDecision == "s":
								pitchingDecision = "sv"
							try:
								allStats[t][player][pitchingDecision] += 1
							except:
								allStats[t][player][pitchingDecision] = 1

						for header, stat in zip(headers, playerRow["stats"]):
							if header == "h-ab":
								continue
							if header == "k" and title == "batting":
								header = "so"
							if header in ["pc-st"]:
								pc, st = map(int, stat.split("-"))
								allStats[t][player]["pc"] = pc
								allStats[t][player]["st"] = st
							elif header in ["bb", "hr", "h"] and title == "pitching":
								try:
									allStats[t][player][header+"_allowed"] = int(stat)
								except:
									allStats[t][player][header+"_allowed"] = 0
							else:
								val = stat
								try:
									val = int(val)
								except:
									try:
										val = float(val)
									except:
										val = 0
								allStats[t][player][header] = val

			for teamRow in data["boxscore"]["teams"]:
				team = teamRow["team"]["abbreviation"].lower()
				t = team+" gm2" if "gm2" in away else team
				if not teamRow["details"]:
					continue
				for detailRow in teamRow["details"][0]["stats"]:
					stat = detailRow["abbreviation"].lower()

					if stat not in ["sf", "2b", "3b"]:
						continue

					for playerVal in detailRow["displayValue"].split("; "):
						name = parsePlayer(playerVal.split(" (")[0])
						try:
							val = int(name.split(" ")[-1])
							name = " ".join(name.split(" ")[:-1])
						except:
							val = 1

						if team == "tb" and name.endswith("lowe"):
							player = name.replace("j ", "josh ").replace("b ", "brandon ")
						elif team == "hou" and name.endswith("abreu"):
							player = name.replace("j ", "jose ").replace("b ", "bryan ")
						elif team == "nyy" and name.endswith("cordero"):
							player = name.replace("f ", "franchy ").replace("j ", "jimmy ")
						else:
							try:
								player = lastNames[team][name.split(" ")[-1]]
							except:
								print(team, name)
								continue
						if player not in allStats[t]:
							continue
						allStats[t][player][stat] = val

			for rosterRow in data["rosters"]:
				team = rosterRow["team"]["abbreviation"].lower()
				t = team+" gm2" if "gm2" in away else team
				if "roster" not in rosterRow:
					continue
				for playerRow in rosterRow["roster"]:
					player = parsePlayer(playerRow["athlete"]["displayName"])
					for statRow in playerRow.get("stats", []):
						hdr = statRow["shortDisplayName"].lower()
						if hdr not in allStats[t][player]:
							val = statRow["value"]
							try:
								val = int(val)
							except:
								pass
							allStats[t][player][hdr] = val

			for team in allStats:
				for player in allStats[team]:
					if "ip" in allStats[team][player]:
						ip = allStats[team][player]["ip"]
						outs = int(ip)*3 + int(str(ip).split(".")[-1])
						allStats[team][player]["outs"] = outs
					elif "ab" in allStats[team][player]:
						_3b = allStats[team][player].get("3b", 0)
						_2b = allStats[team][player].get("2b", 0)
						hr = allStats[team][player]["hr"]
						h = allStats[team][player]["h"]
						_1b = h - (_3b+_2b+hr)
						allStats[team][player]["1b"] = _1b
						allStats[team][player]["tb"] = 4*hr + 3*_3b + 2*_2b + _1b

						r = allStats[team][player]["r"]
						rbi = allStats[team][player]["rbi"]
						allStats[team][player]["h+r+rbi"] = h + r + rbi

		for team in allStats:
			realTeam = team.replace(" gm2", "")
			if not os.path.isdir(f"{prefix}static/baseballreference/{realTeam}"):
				os.mkdir(f"{prefix}static/baseballreference/{realTeam}")

			d = date+"-gm2" if "gm2" in team else date
			with open(f"{prefix}static/baseballreference/{realTeam}/{d}.json", "w") as fh:
				json.dump(allStats[team], fh, indent=4)

	write_totals()
	writeSplits()

	with open(f"{prefix}static/baseballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def parsePlayer(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "").replace(" iv", "")

def writeSplits():
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)

	splits = {}
	for team in os.listdir(f"{prefix}static/baseballreference/"):
		if "json" in team:
			continue
		if team not in splits:
			splits[team] = {}

		for file in sorted(glob(f"{prefix}static/baseballreference/{team}/*.json")):
			with open(file) as fh:
				stats = json.load(fh)

			if not stats:
				continue

			date = file.split("/")[-1][:-5]
			gm2 = False
			if "gm2" in date:
				gm2 = True
				date = date.replace("-gm2", "")
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
			if gm2:
				score = scores[date][team+" gm2"]
				oppScore = scores[date][opp+" gm2"]

			winLoss = "W"
			if oppScore > score:
				winLoss = "L"

			for player in stats:
				if player not in splits[team]:
					splits[team][player] = {}

				if "winLoss" not in splits[team][player]:
					splits[team][player]["winLoss"] = []
				if "awayHome" not in splits[team][player]:
					splits[team][player]["awayHome"] = []
				if "opp" not in splits[team][player]:
					splits[team][player]["opp"] = []
				splits[team][player]["opp"].append(opp)
				splits[team][player]["awayHome"].append(awayHome)
				splits[team][player]["winLoss"].append(winLoss)

				for header in stats[player]:
					if header not in splits[team][player]:
						splits[team][player][header] = []
					splits[team][player][header].append(str(stats[player][header]))

				if "ab" in stats[player]:
					for header in ["2b", "3b", "sf"]:
						if header not in stats[player]:
							if header not in splits[team][player]:
								splits[team][player][header] = []
							splits[team][player][header].append("0")

		for player in splits[team]:
			for hdr in splits[team][player]:
				splits[team][player][hdr] = ",".join(splits[team][player][hdr])

	with open(f"{prefix}static/baseballreference/splits.json", "w") as fh:
		json.dump(splits, fh, indent=4)

def sumStat(header, target, source):
	if header not in target:
		target[header] = 0

	if header == "ip":
		ip = target["ip"]+source["ip"]
		remainder = int(str(round(ip, 1)).split(".")[-1])

		if remainder >= 3:
			ip += remainder // 3
			ip = int(ip) + (remainder%3)*0.1
		target["ip"] = ip
	else:
		try:
			target[header] += source[header]
		except:
			pass


def write_curr_year_averages():
	year = datetime.datetime.now().year
	with open(f"{prefix}static/baseballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	statsVsTeam = {}
	for team in os.listdir(f"{prefix}static/baseballreference/"):
		if team.endswith("json"):
			continue

		if team not in statsVsTeam:
			statsVsTeam[team] = {}
		
		copy = True
		for file in glob(f"{prefix}static/baseballreference/{team}/*.json"):
			with open(file) as fh:
				stats = json.load(fh)

			date = file.split("/")[-1][:-5]
			doubleHeader = False
			if "-gm2" in date:
				doubleHeader = True
			date = date.replace("-gm2", "")
			opp = ""
			for game in schedule[date]:
				if game.startswith(team):
					opp = game.split(" @ ")[1]
					break
				elif game.endswith(team):
					opp = game.split(" @ ")[0]
					break

			if opp not in statsVsTeam[team]:
				statsVsTeam[team][opp] = {}

			for player in stats:
				if player not in averages[team]:
					averages[team][player] = {}
				if year not in averages[team][player]:
					averages[team][player][year] = {}
				if player not in statsVsTeam[team][opp]:
					statsVsTeam[team][opp][player] = {"gamesPlayed": 0}
				if copy:
					averages[team][player][year] = stats[player].copy()
					statsVsTeam[team][opp][player] = stats[player].copy()
				else:
					for hdr in stats[player]:
						sumStat(hdr, averages[team][player][year], stats[player])
						sumStat(hdr, statsVsTeam[team][opp][player], stats[player])

				if "gamesPlayed" not in statsVsTeam[team][opp][player]:
					statsVsTeam[team][opp][player]["gamesPlayed"] = 0
				statsVsTeam[team][opp][player]["gamesPlayed"] += 1

				for hdr in stats[player]:
					val = stats[player][hdr]
					if hdr in ["h", "1b", "tb", "r", "rbi", "outs", "h+r+rbi", "bb", "hr", "sb", "so", "k", "er"]:
						if hdr+"Overs" not in averages[team][player][year]:
							averages[team][player][year][hdr+"Overs"] = {}
						if hdr+"Overs" not in statsVsTeam[team][opp][player]:
							statsVsTeam[team][opp][player][hdr+"Overs"] = {}

						for i in range(1, int(val)+1):
							if i not in averages[team][player][year][hdr+"Overs"]:
								averages[team][player][year][hdr+"Overs"][i] = 0
							averages[team][player][year][hdr+"Overs"][i] += 1

							if i not in statsVsTeam[team][opp][player][hdr+"Overs"]:
								statsVsTeam[team][opp][player][hdr+"Overs"][i] = 0
							statsVsTeam[team][opp][player][hdr+"Overs"][i] += 1

			#only copy first time we see team stats
			copy = False

	with open(f"{prefix}static/baseballreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	with open(f"{prefix}static/baseballreference/statsVsTeamCurrYear.json", "w") as fh:
		json.dump(statsVsTeam, fh, indent=4)

def write_totals():
	totals = {}
	teamTotals = {}
	for team in os.listdir(f"{prefix}static/baseballreference/"):
		if team.endswith("json"):
			continue
		if team not in totals:
			totals[team] = {}
		if team not in teamTotals:
			teamTotals[team] = {}

		for file in glob(f"{prefix}static/baseballreference/{team}/*.json"):
			with open(file) as fh:
				stats = json.load(fh)
			for player in stats:
				if player not in totals[team]:
					totals[team][player] = stats[player]
				else:
					for header in stats[player]:
						sumStat(header, totals[team][player], stats[player])

				for header in stats[player]:
					if header == "r" and "ip" in stats[player]:
						continue
					sumStat(header, teamTotals[team], stats[player])

				if "gamesPlayed" not in totals[team][player]:
					totals[team][player]["gamesPlayed"] = 0
				totals[team][player]["gamesPlayed"] += 1

			if "gamesPlayed" not in teamTotals[team]:
				teamTotals[team]["gamesPlayed"] = 0
			teamTotals[team]["gamesPlayed"] += 1

	with open(f"{prefix}static/baseballreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

	with open(f"{prefix}static/baseballreference/teamTotals.json", "w") as fh:
		json.dump(teamTotals, fh, indent=4)

	write_curr_year_averages()

def write_schedule(date):
	url = f"https://www.espn.com/mlb/schedule/_/date/{date.replace('-', '')}"
	outfile = "outmlb"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/baseballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)

	#schedule[date] = []

	date = ""

	for table in soup.findAll("div", class_="ResponsiveTable"):
		if table.find("div", class_="Table__Title") and "spring training" not in table.find("div", class_="Table__Title").text.lower():
			date = table.find("div", class_="Table__Title").text.strip()
			date = str(datetime.datetime.strptime(date, "%A, %B %d, %Y"))[:10]
			date = date.split(" ")[-1]
		else:
			continue

		if table.find("a", class_="Schedule__liveLink"):
			continue

		schedule[date] = []
		if date not in boxscores:
			boxscores[date] = {}
		if date not in scores:
			scores[date] = {}

		seen = {}
		for row in table.findAll("tr")[1:]:
			tds = row.findAll("td")
			try:
				awayTeam = tds[0].findAll("a")[-1].get("href").split("/")[-2]
				homeTeam = tds[1].findAll("a")[-1].get("href").split("/")[-2]
			except:
				continue

			game = awayTeam + " @ " + homeTeam
			if (awayTeam, homeTeam) in seen:
				awayTeam += " gm2"
				homeTeam += " gm2"
			seen[(awayTeam, homeTeam)] = True
			boxscore = tds[2].find("a").get("href")
			score = tds[2].find("a").text.strip()
			if score.lower() == "postponed" or score.lower() == "canceled":
				continue

			if date in ["2024-03-20", "2024-03-21"] and "lad" not in game:
				continue

			#if ", " in score and os.path.exists(f"{prefix}static/baseballreference/{awayTeam.split(' ')[0]}/{date}.json"):
			if ", " in score:
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

	with open(f"{prefix}static/baseballreference/statsVsTeam.json") as fh:
		statsVsTeam = json.load(fh)

	currYear = str(datetime.datetime.now())[:4]

	#year = "2022"
	yearStats = {}
	for year in os.listdir(f"{prefix}static/mlbprops/stats/"):
		year = year[:4]
		if os.path.exists(f"{prefix}static/mlbprops/stats/{year}.json"):
			with open(f"{prefix}static/mlbprops/stats/{year}.json") as fh:
				stats = json.load(fh)
			yearStats[year] = stats.copy()

	#yearStats = {}

	if False:
		ids = {
			"ari": {
				"ketel marte": 32512
			},
			"det": {
				"tarik skubal": 42409
			}
		}

	for team in ids:
		for player in ids[team]:
			pId = ids[team][player]

			time.sleep(0.2)
			url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}"
			outfile = "outmlb3"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")
			#print(url)
			if not soup.find("div", class_="gamelog"):
				continue
			select = soup.find("div", class_="gamelog").find("select", class_="dropdown__select")
			if not select:
				continue
			years = [y.text for y in select.findAll("option")]

			if team not in averages:
				averages[team] = {}
			if player not in averages[team]:
				averages[team][player] = {"tot": {}}

			if team not in statsVsTeam:
				statsVsTeam[team] = {}

			averages[team][player] = {"tot": {}}
			statsVsTeam[team][player] = {}

			for year in years:
				if year == currYear:
					continue
				if year != "2023":
					#continue
					pass
				if len(year) != 4:
					for title in soup.find("div", class_="gamelog").findAll("div", class_="Table__Title"):
						if "regular" in title.text.lower():
							year = title.text.lower()[:4]
					if len(year) != 4:
						continue
				if year not in yearStats:
					yearStats[year] = {}
				if team not in yearStats[year]:
					yearStats[year][team] = {}

				if player in yearStats[year][team]:
					continue
					pass
				if player not in yearStats[year][team]:
					yearStats[year][team][player] = {}
				
				if year not in averages[team][player]:
					averages[team][player][year] = {}

				yearStats[year][team][player] = {"tot": {}, "splits": {}}
				gamesPlayed = 0

				time.sleep(0.2)
				url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}/type/mlb/year/{year}"
				outfile = "outmlb3"
				call(["curl", url, "-o", outfile])
				soup = BS(open(outfile, 'rb').read(), "lxml")

				headers = []
				for row in soup.findAll("tr"):
					try:
						title = row.findPrevious("div", class_="Table__Title").text.lower()
					except:
						title = ""
					if "regular season" not in title:
						continue
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
							yearStats[year][team][player]["tot"][header] = val
						yearStats[year][team][player]["tot"]["gamesPlayed"] = len(yearStats[year][team][player]["splits"]["opp"])
						
						if "outs" in yearStats[year][team][player]["splits"]:
							yearStats[year][team][player]["tot"]["outs"] = sum(yearStats[year][team][player]["splits"]["outs"])
							for p in ["w", "l"]:
								yearStats[year][team][player]["tot"][p] = len([x for x in yearStats[year][team][player]["splits"]["dec"] if x == p.upper()])
							for p in ["sv", "hld", "blsv"]:
								yearStats[year][team][player]["tot"][p] = len([x for x in yearStats[year][team][player]["splits"]["rel"] if x == p.upper()])
						if "tb" in yearStats[year][team][player]["splits"]:
							yearStats[year][team][player]["tot"]["tb"] = sum(yearStats[year][team][player]["splits"]["tb"])
							yearStats[year][team][player]["tot"]["1b"] = sum(yearStats[year][team][player]["splits"]["1b"])
							yearStats[year][team][player]["tot"]["h+r+rbi"] = sum(yearStats[year][team][player]["splits"]["h+r+rbi"])
					else:
						tds = row.findAll("td")
						if len(tds) > 1 and ("@" in tds[1].text or "vs" in tds[1].text):
							date = str(datetime.datetime.strptime(tds[0].text.strip()+"/"+year, "%a %m/%d/%Y")).split(" ")[0]
							awayHome = "A" if "@" in tds[1].text else "H"
							try:
								opp = tds[1].findAll("a")[-1].get("href").split("/")[-2]
							except:
								continue

							if opp not in statsVsTeam[team][player]:
								statsVsTeam[team][player][opp] = {"gamesPlayed": 0}
							statsVsTeam[team][player][opp]["gamesPlayed"] += 1

							result = "L" if tds[2].find("div", class_="loss-stat") else "W"
							if "splits" not in yearStats[year][team][player]:
								yearStats[year][team][player]["splits"] = {}

							for prop, val in [("awayHome", awayHome), ("opp", opp), ("winLoss", result)]:
								if prop not in yearStats[year][team][player]["splits"]:
									yearStats[year][team][player]["splits"][prop] = []
								yearStats[year][team][player]["splits"][prop].append(val)

							for idx, td in enumerate(tds[3:]):
								header = headers[idx]

								if header in ["era", "avg", "obp", "slg", "ops"]:
									continue
								val = 0.0
								if header in ["dec", "rel"]:
									val = td.text.strip()
									if "(" in val:
										val = val.split("(")[0]
									else:
										val = "-"
								else:
									try:
										val = int(td.text.strip())
									except:
										try:
											val = float(td.text.strip())
										except:
											val = "-"

								if header not in yearStats[year][team][player]["splits"]:
									yearStats[year][team][player]["splits"][header] = []

								yearStats[year][team][player]["splits"][header].append(val)

								if header == "ip":
									if "outs" not in yearStats[year][team][player]["splits"]:
										yearStats[year][team][player]["splits"]["outs"] = []
									outs = int(val)*3 + int(str(val).split(".")[-1])
									yearStats[year][team][player]["splits"]["outs"].append(outs)

							if "ab" in yearStats[year][team][player]["splits"]:
								_3b = yearStats[year][team][player]["splits"]["3b"][-1]
								_2b = yearStats[year][team][player]["splits"]["2b"][-1]
								hr = yearStats[year][team][player]["splits"]["hr"][-1]
								h = yearStats[year][team][player]["splits"]["h"][-1]
								_1b = h - (_3b+_2b+hr)
								# 1B
								if "1b" not in yearStats[year][team][player]["splits"]:
									yearStats[year][team][player]["splits"]["1b"] = []
								yearStats[year][team][player]["splits"]["1b"].append(_1b)

								# TB
								if "tb" not in yearStats[year][team][player]["splits"]:
									yearStats[year][team][player]["splits"]["tb"] = []
								yearStats[year][team][player]["splits"]["tb"].append(4*hr + 3*_3b + 2*_2b + _1b)

								# HRR
								r = yearStats[year][team][player]["splits"]["r"][-1]
								rbi = yearStats[year][team][player]["splits"]["rbi"][-1]
								hrr = h + r + rbi
								if "h+r+rbi" not in yearStats[year][team][player]["splits"]:
									yearStats[year][team][player]["splits"]["h+r+rbi"] = []
								yearStats[year][team][player]["splits"]["h+r+rbi"].append(hrr)

							# Overs
							for header in ["h", "1b", "2b", "3b", "tb", "r", "rbi", "h+r+rbi", "bb", "hr", "sb", "so", "k", "er", "outs"]:
								if header not in yearStats[year][team][player]["splits"]:
									continue

								opp = yearStats[year][team][player]["splits"]["opp"][-1]
								val = yearStats[year][team][player]["splits"][header][-1]
								hdrOver = header+"Overs"
								if hdrOver not in yearStats[year][team][player]["tot"]:
									yearStats[year][team][player]["tot"][hdrOver] = {}
								if hdrOver not in statsVsTeam[team][player][opp]:
									statsVsTeam[team][player][opp][hdrOver] = {}
								for i in range(1, int(val)+1):
									if i not in yearStats[year][team][player]["tot"][hdrOver]:
										yearStats[year][team][player]["tot"][hdrOver][i] = 0
									if i not in statsVsTeam[team][player][opp][hdrOver]:
										statsVsTeam[team][player][opp][hdrOver][i] = 0
									yearStats[year][team][player]["tot"][hdrOver][i] += 1
									statsVsTeam[team][player][opp][hdrOver][i] += 1

							# statsVsTeam
							for hdr in yearStats[year][team][player]["splits"]:
								if hdr in ["awayHome", "opp", "winLoss"] or "Overs" in hdr:
									continue
								if hdr in ["dec", "rel"]:
									val = yearStats[year][team][player]["splits"][hdr][-1]
									if val in ["W", "L", "SV", "HLD", "BLSV"]:
										hdr = val
									else:
										continue
									if hdr not in statsVsTeam[team][player][opp]:
										statsVsTeam[team][player][opp][hdr] = 0
									statsVsTeam[team][player][opp][hdr] += 1
								else:
									if hdr not in statsVsTeam[team][player][opp]:
										statsVsTeam[team][player][opp][hdr] = 0

									#print(year,hdr, yearStats[year][team][player]["splits"][hdr])
									statsVsTeam[team][player][opp][hdr] += yearStats[year][team][player]["splits"][hdr][-1]



				for hdr in yearStats[year][team][player]["splits"]:
					arr = ",".join([str(x) for x in yearStats[year][team][player]["splits"][hdr]][::-1])
					yearStats[year][team][player]["splits"][hdr] = arr

				#print(year, player in averages[team])
				averages[team][player][year] = yearStats[year][team][player]["tot"].copy()
				for hdr in averages[team][player][year]:
					if "Overs" in hdr:
						if hdr not in averages[team][player]["tot"]:
							averages[team][player]["tot"][hdr] = {}
						for val in averages[team][player][year][hdr]:
							if val not in averages[team][player]["tot"][hdr]:
								averages[team][player]["tot"][hdr][val] = 0
							averages[team][player]["tot"][hdr][val] += averages[team][player][year][hdr][val]
					else:
						if hdr in ["rel", "dec"]:
							continue
						if hdr not in averages[team][player]["tot"]:
							averages[team][player]["tot"][hdr] = 0
						averages[team][player]["tot"][hdr] += averages[team][player][year][hdr]


				with open(f"{prefix}static/mlbprops/stats/{year}.json", "w") as fh:
					#print(year)
					json.dump(yearStats[year], fh, indent=4)

				with open(f"{prefix}static/baseballreference/statsVsTeam.json", "w") as fh:
					json.dump(statsVsTeam, fh)

				with open(f"{prefix}static/baseballreference/averages.json", "w") as fh:
					json.dump(averages, fh, indent=4)

def writeStatsVsTeam():
	statsVsTeam = {}
	#statsVsTeam[team][player][opp][hdr]
	for year in os.listdir(f"{prefix}static/mlbprops/stats/"):
		year = year[:4]
		if not os.path.exists(f"{prefix}static/mlbprops/stats/{year}.json"):
			continue
		with open(f"{prefix}static/mlbprops/stats/{year}.json") as fh:
			stats = json.load(fh)

		for team in stats:
			if team not in statsVsTeam:
				statsVsTeam[team] = {}
			for player in stats[team]:
				if player not in statsVsTeam[team]:
					statsVsTeam[team][player] = {}
				splits = stats[team][player]["splits"]
				if not splits:
					continue
				opps = splits["opp"].split(",")
				for idx, opp in enumerate(opps):
					if opp not in statsVsTeam[team][player]:
						statsVsTeam[team][player][opp] = {"gamesPlayed": 0}
					statsVsTeam[team][player][opp]["gamesPlayed"] += 1
					for stat in splits:
						if stat in ["awayHome", "opp", "winLoss"]:
							continue

						val = splits[stat].split(",")[idx]
						try:
							val = int(val)
						except:
							try:
								val = float(val)
							except:
								pass

						try:
							statsVsTeam[team][player][opp][stat] += val
						except:
							statsVsTeam[team][player][opp][stat] = val


	with open(f"{prefix}static/baseballreference/statsVsTeam.json", "w") as fh:
		json.dump(statsVsTeam, fh)


def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def writeRoster():

	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	roster = {}
	for team in os.listdir(f"{prefix}static/baseballreference/"):

		if team.endswith(".json"):
			continue

		if team not in playerIds:
			playerIds[team] = {}

		roster[team] = {}
		time.sleep(0.2)
		url = f"https://www.espn.com/mlb/team/roster/_/name/{team}/"
		outfile = "outmlb"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for table in soup.findAll("table"):
			for row in table.findAll("tr")[1:]:
				nameLink = row.findAll("td")[1].find("a").get("href").split("/")
				fullName = parsePlayer(row.findAll("td")[1].find("a").text)
				playerId = int(nameLink[-1])
				playerIds[team][fullName] = playerId
				roster[team][fullName] = row.findAll("td")[2].text.strip()

	with open(f"{prefix}static/baseballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/baseballreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

def convertTeamRankingsTeam(team):
	if team.startswith("wash"):
		return "wsh"
	elif team.endswith("white sox") or team == "chi sox":
		return "chw"
	elif team.endswith("cubs"):
		return "chc"
	elif team.endswith("giants"):
		return "sf"
	elif team.endswith("dodgers"):
		return "lad"
	elif team.endswith("angels"):
		return "laa"
	elif team.startswith("kansas city"):
		return "kc"
	elif team.startswith("san diego"):
		return "sd"
	elif team.startswith("tampa bay"):
		return "tb"
	elif team.endswith("yankees"):
		return "nyy"
	elif team.endswith("mets"):
		return "nym"
	return team.replace(".", "").replace(" ", "")[:3]

def addNumSuffix(val):
	if not val:
		return "-"
	a = val % 10;
	b = val % 100;
	if val == 0:
		return ""
	if a == 1 and b != 11:
		return f"{val}st"
	elif a == 2 and b != 12:
		return f"{val}nd"
	elif a == 3 and b != 13:
		return f"{val}rd"
	else:
		return f"{val}th"

def write_player_rankings():
	baseUrl = "https://www.teamrankings.com/mlb/player-stat/"
	pages = ["pitches-per-plate-appearance", "strikeouts-per-walk"]
	ids = ["pitchesPerPlate", "k/bb"]

	rankings = {}
	for idx, page in enumerate(pages):
		url = baseUrl+page
		outfile = "outmlb2"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")
		ranking = ids[idx]

		for row in soup.find("table").findAll("tr")[1:]:
			tds = row.findAll("td")
			player = row.find("a").text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "").split(" (")[0]
			team = convertTeamRankingsTeam(row.findAll("a")[1].text.lower())

			if team not in rankings:
				rankings[team] = {}

			if player not in rankings[team]:
				rankings[team][player] = {}
			
			if ranking not in rankings[team][player]:
				rankings[team][player][ranking] = {}

			rankClass = ""
			if int(tds[0].text) <= 10:
				rankClass = "positive"
			elif int(tds[0].text) >= 20:
				rankClass = "negative"
			rankings[team][player][ranking] = {
				"rank": int(tds[0].text),
				"rankSuffix": addNumSuffix(int(tds[0].text)),
				"rankClass": rankClass,
				"val": float(tds[-1].text.replace("--", "0")),
			}

	with open(f"{prefix}static/baseballreference/playerRankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)


def write_rankings():
	baseUrl = "https://www.teamrankings.com/mlb/stat/"
	pages = ["at-bats-per-game", "strikeouts-per-game", "walks-per-game", "runs-per-game", "hits-per-game", "home-runs-per-game", "singles-per-game", "doubles-per-game", "rbis-per-game", "total-bases-per-game", "earned-run-average", "earned-runs-against-per-game", "strikeouts-per-9", "home-runs-per-9", "hits-per-9", "walks-per-9", "opponent-runs-per-game", "opponent-stolen-bases-per-game", "opponent-total-bases-per-game", "opponent-rbis-per-game", "opponent-at-bats-per-game"]
	ids = ["ab", "so", "bb", "r", "h", "hr", "1b", "2b", "rbi", "tb", "era", "er", "k", "hr_allowed", "h_allowed", "bb_allowed", "r_allowed", "opp_sb", "opp_tb", "opp_rbi", "opp_ab"]

	rankings = {}
	for idx, page in enumerate(pages):
		url = baseUrl+page
		outfile = "outmlb2"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")
		ranking = ids[idx]
		lastYearRanks = []

		for row in soup.find("table").findAll("tr")[1:]:
			tds = row.findAll("td")
			team = convertTeamRankingsTeam(row.find("a").text.lower())
			if team not in rankings:
				rankings[team] = {}
			
			if ranking not in rankings[team]:
				rankings[team][ranking] = {}

			rankClass = ""
			if int(tds[0].text) <= 10:
				rankClass = "positive"
			elif int(tds[0].text) >= 20:
				rankClass = "negative"
			rankings[team][ranking] = {
				"rank": int(tds[0].text),
				"rankSuffix": addNumSuffix(int(tds[0].text)),
				"rankClass": rankClass,
				"season": float(tds[2].text.replace("--", "0").replace("%", "")),
				"last3": float(tds[3].text.replace("--", "0").replace("%", "")),
				"last1": float(tds[4].text.replace("--", "0").replace("%", "")),
				"home": float(tds[5].text.replace("--", "0").replace("%", "")),
				"away": float(tds[6].text.replace("--", "0").replace("%", "")),
				"lastYear": float(tds[7].text.replace("--", "0").replace("%", ""))
			}

			lastYearRanks.append({"team": team, "lastYear": float(tds[7].text.replace("--", "0").replace("%", ""))})

		reverse=True
		if "allowed" in ranking:
			reverse=False
		for idx, x in enumerate(sorted(lastYearRanks, key=lambda k: k["lastYear"], reverse=reverse)):
			rankings[x["team"]][ranking]["lastYearRank"] = idx+1
			rankClass = ""
			if idx+1 <= 10:
				rankClass = "positive"
			elif idx+1 >= 20:
				rankClass = "negative"
			rankings[x["team"]][ranking]["lastYearRankClass"] = rankClass
			rankings[x["team"]][ranking]["lastYearRankSuffix"] = addNumSuffix(idx+1)

	combined = []
	for team in rankings:
		j = {"team": team}
		for k in ["season", "last3", "last1", "home", "away", "lastYear"]:
			j[k] = rankings[team][f"h"][k]+rankings[team][f"r"][k]+rankings[team][f"rbi"][k]
		combined.append(j)

	for idx, x in enumerate(sorted(combined, key=lambda k: k["season"], reverse=True)):
		rankings[x["team"]][f"h+r+rbi"] = x.copy()
		rankings[x["team"]][f"h+r+rbi"]["rank"] = idx+1
		rankings[x["team"]][f"h+r+rbi"]["rankSuffix"] = addNumSuffix(idx+1)
		rankClass = ""
		if idx+1 <= 10:
			rankClass = "positive"
		elif idx+1 >= 20:
			rankClass = "negative"
		rankings[x["team"]][f"h+r+rbi"]["rankClass"] = rankClass

	combined = []
	for team in rankings:
		j = {"team": team}
		for k in ["season", "last3", "last1", "home", "away", "lastYear"]:
			j[k] = rankings[team][f"h_allowed"][k]+rankings[team][f"er"][k]
		combined.append(j)

	for idx, x in enumerate(sorted(combined, key=lambda k: k["season"], reverse=True)):
		rankings[x["team"]][f"h+r+rbi_allowed"] = x.copy()
		rankings[x["team"]][f"h+r+rbi_allowed"]["rank"] = idx+1
		rankings[x["team"]][f"h+r+rbi_allowed"]["rankSuffix"] = addNumSuffix(idx+1)
		rankClass = ""
		if idx+1 <= 10:
			rankClass = "positive"
		elif idx+1 >= 20:
			rankClass = "negative"
		rankings[x["team"]][f"h+r+rbi_allowed"]["rankClass"] = rankClass

	for idx, x in enumerate(sorted(combined, key=lambda k: k["lastYear"], reverse=True)):
		rankings[x["team"]][f"h+r+rbi_allowed"]["lastYearRank"] = idx+1
		rankings[x["team"]][f"h+r+rbi_allowed"]["lastYearRankSuffix"] = addNumSuffix(idx+1)

	with open(f"{prefix}static/baseballreference/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)


def write_batting_pitches():
	url = "https://www.baseball-reference.com/leagues/majors/2023-pitches-batting.shtml"
	time.sleep(0.2)
	outfile = "outmlb2"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	headers = []
	for td in soup.find("tr").findAll("th")[1:]:
		headers.append(td.text.lower())

	battingPitches = {}
	for tr in soup.findAll("tr")[1:]:
		try:
			team = convertRotoTeam(tr.find("th").find("a").get("href").split("/")[-2].lower())
		except:
			continue
		j = {}
		for td, hdr in zip(tr.findAll("td"), headers):
			j[hdr] = td.text

		battingPitches[team] = j

	playerBattingPitches = {}
	referenceIds = {}
	for comment in soup.findAll(text=lambda text:isinstance(text, Comment)):
		if "div_players_pitches_batting" in comment:
			soup = BS(comment, "lxml")

			headers = []
			for th in soup.find("tr").findAll("th")[1:]:
				headers.append(th.text.lower())

			for tr in soup.findAll("tr")[1:]:
				tds = tr.findAll("td")
				if not tds or not tr.find("a"):
					continue
				j = {}
				for td, hdr in zip(tds, headers):
					j[hdr] = td.text

				team = convertRotoTeam(j["tm"].lower())
				player = strip_accents(tr.find("a").text.lower().replace("\u00a0", " ").replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", ""))
				if team not in playerBattingPitches:
					playerBattingPitches[team] = {}
				if team not in referenceIds:
					referenceIds[team] = {}
				playerBattingPitches[team][player] = j
				referenceIds[team][player] = tr.find("a").get("href")

			break

	with open(f"{prefix}static/baseballreference/playerBattingPitches.json", "w") as fh:
		json.dump(playerBattingPitches, fh, indent=4)
	with open(f"{prefix}static/baseballreference/battingPitches.json", "w") as fh:
		json.dump(battingPitches, fh, indent=4)
	with open(f"{prefix}static/baseballreference/referenceIds.json", "w") as fh:
		json.dump(referenceIds, fh, indent=4)


def write_pitching_pitches():
	url = "https://www.baseball-reference.com/leagues/majors/2023-pitches-pitching.shtml"
	time.sleep(0.2)
	outfile = "outmlb2"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	headers = []
	for td in soup.find("tr").findAll("th")[1:]:
		headers.append(td.text.lower())

	pitchingPitches = {}
	for tr in soup.findAll("tr")[1:]:
		try:
			team = convertRotoTeam(tr.find("th").find("a").get("href").split("/")[-2].lower())
		except:
			continue
		j = {}
		for td, hdr in zip(tr.findAll("td"), headers):
			j[hdr] = td.text

		pitchingPitches[team] = j

	playerPitchingPitches = {}
	for comment in soup.findAll(text=lambda text:isinstance(text, Comment)):
		if "div_players_pitches_pitching" in comment:
			soup = BS(comment, "lxml")

			headers = []
			for th in soup.find("tr").findAll("th")[1:]:
				headers.append(th.text.lower())

			for tr in soup.findAll("tr")[1:]:
				tds = tr.findAll("td")
				if not tds or not tr.find("a"):
					continue
				j = {}
				for td, hdr in zip(tds, headers):
					j[hdr] = td.text

				team = convertRotoTeam(j["tm"].lower())
				player = strip_accents(tr.find("a").text.lower().replace("\u00a0", " ").replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", ""))
				if team not in playerPitchingPitches:
					playerPitchingPitches[team] = {}
				playerPitchingPitches[team][player] = j

			break

	with open(f"{prefix}static/baseballreference/playerPitchingPitches.json", "w") as fh:
		json.dump(playerPitchingPitches, fh, indent=4)
	with open(f"{prefix}static/baseballreference/pitchingPitches.json", "w") as fh:
		json.dump(pitchingPitches, fh, indent=4)


def write_pitching():
	with open(f"{prefix}static/baseballreference/pitching.json") as fh:
		pitching = json.load(fh)

	pitchingData = {}
	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	for file in os.listdir(f"{prefix}static/mlbprops/stats/"):
		year = file[:4]

		with open(f"{prefix}static/mlbprops/stats/{file}") as fh:
			yearStats = json.load(fh)

		for team in yearStats:
			if team not in pitching:
				pitching[team] = {}
			if team not in pitchingData:
				pitchingData[team] = {}
			for player in yearStats[team]:
				pos = roster[team].get(player, "")
				if "P" in pos:
					for d in yearStats[team][player]:
						if d not in pitchingData[team]:
							pitchingData[team][d] = yearStats[team][player][d]
							pitching[team][d] = player
						else:
							ip = pitchingData[team][d]["ip"]
							if yearStats[team][player][d]["ip"] > ip:
								pitchingData[team][d] = yearStats[team][player][d]
								pitching[team][d] = player

	with open(f"{prefix}static/baseballreference/pitching.json", "w") as fh:
		json.dump(pitching, fh, indent=4)

def convertRotoTeam(team):
	team = team.lower()
	if team == "cws":
		return "chw"
	elif team == "az":
		return "ari"
	elif team == "sfg":
		return "sf"
	elif team == "sdp":
		return "sd"
	elif team == "kcr":
		return "kc"
	elif team == "tbr":
		return "tb"
	elif team == "wsn":
		return "wsh"
	return team

def convertSavantTeam(team):
	if team == "angels":
		return "laa"
	elif team == "orioles":
		return "bal"
	elif team == "red sox":
		return "bos"
	elif team == "white sox":
		return "chw"
	elif team == "guardians":
		return "cle"
	elif team == "royals":
		return "kc"
	elif team == "athletics":
		return "oak"
	elif team == "rays":
		return "tb"
	elif team == "blue jays":
		return "tor"
	elif team == "d-backs":
		return "ari"
	elif team == "cubs":
		return "chc"
	elif team == "rockies":
		return "col"
	elif team == "dodgers":
		return "lad"
	elif team == "pirates":
		return "pit"
	elif team == "brewers":
		return "mil"
	elif team == "reds":
		return "cin"
	elif team == "cardinals":
		return "stl"
	elif team == "marlins":
		return "mia"
	elif team == "astros":
		return "hou"
	elif team == "tigers":
		return "det"
	elif team == "giants":
		return "sf"
	elif team == "braves":
		return "atl"
	elif team == "padres":
		return "sd"
	elif team == "phillies":
		return "phi"
	elif team == "mariners":
		return "sea"
	elif team == "rangers":
		return "tex"
	elif team == "mets":
		return "nym"
	elif team == "nationals":
		return "wsh"
	elif team == "twins":
		return "min"
	elif team == "yankees":
		return "nyy"
	return team

def writeSavantParkFactors():
	url = "https://baseballsavant.mlb.com/leaderboard/statcast-park-factors?type=year&year=2023&batSide=&stat=index_wOBA&condition=All&rolling="
	time.sleep(0.2)
	outfile = "outmlb2"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = "{}"
	for script in soup.findAll("script"):
		if "var data" in script.string:
			m = re.search(r"var data = \[{(.*?)}\];", script.string)
			if m:
				data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
				data = f"{{{data}}}"
				break

	data = eval(data)

	parkFactors = {}
	arr = []
	for row in data:
		if not row["name_display_club"]:
			continue
		team = convertSavantTeam(row["name_display_club"].lower())
		parkFactors[team] = {}

		j = {"team": team}
		for hdr in row:
			parkFactors[team][hdr] = row[hdr]
			j[hdr] = row[hdr]

		arr.append(j)

	for prop in ["hits", "hr"]:
		for idx, row in enumerate(sorted(arr, key=lambda k: int(k[f"index_{prop}"]), reverse=True)):
			parkFactors[row["team"]][f"{prop}Rank"] = idx+1

	with open(f"{prefix}static/baseballreference/parkfactors.json", "w") as fh:
		json.dump(parkFactors, fh, indent=4)


def writeSavantExpected():
	url = "https://baseballsavant.mlb.com/leaderboard/expected_statistics"
	expected = {}
	for t in ["", "?type=pitcher"]:
		time.sleep(0.2)
		outfile = "outmlb2"
		call(["curl", "-k", url+t, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		data = "{}"
		for script in soup.findAll("script"):
			if "var data" in script.string:
				m = re.search(r"var data = \[{(.*?)}\];", script.string)
				if m:
					data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
					data = f"{{{data}}}"
					break

		data = eval(data)
		
		for row in data:
			team = convertRotoTeam(row["entity_team_name_alt"].lower())
			if team not in expected:
				expected[team] = {}

			player = strip_accents(row["entity_name"]).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
			last, first = map(str, player.split(", "))
			player = f"{first} {last}"

			expected[team][player] = row.copy()


	with open(f"{prefix}static/baseballreference/expected.json", "w") as fh:
		json.dump(expected, fh, indent=4)

def writeSavantPitcherAdvanced():
	url = "https://baseballsavant.mlb.com/leaderboard/custom?year=2023&type=pitcher&filter=&sort=1&sortDir=desc&min=10&selections=p_walk,p_k_percent,p_bb_percent,p_ball,p_called_strike,p_hit_into_play,xba,exit_velocity_avg,launch_angle_avg,sweet_spot_percent,barrel_batted_rate,out_zone_percent,out_zone,in_zone_percent,in_zone,pitch_hand,n,&chart=false&x=p_walk&y=p_walk&r=no&chartType=beeswarm"
	advanced = {}
	time.sleep(0.2)
	outfile = "outmlb2"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = "{}"
	for script in soup.findAll("script"):
		if "var data" in script.string:
			m = re.search(r"var data = \[{(.*?)}\];", script.string)
			if m:
				data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
				data = f"{{{data}}}"
				break

	data = eval(data)
	
	for row in data:
		player = strip_accents(row["player_name"]).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
		last, first = map(str, player.split(", "))
		player = f"{first} {last}"

		advanced[player] = row.copy()

	sortedRankings = {}
	for player in advanced:
		for hdr in advanced[player]:
			if "_rate" in hdr or "_percent" in hdr or "_swing" in hdr or hdr.startswith("x") or hdr in ["ba", "bacon", "babip", "obp", "slg", "iso", "woba"]:
				if hdr not in sortedRankings:
					sortedRankings[hdr] = []

				try:
					val = float(advanced[player][hdr])
				except:
					val = 0
				sortedRankings[hdr].append(val)

	for hdr in sortedRankings:
		reverse = True
		# Flip if it's better for the value to be higher
		if hdr in ["k_percent", "p_k_percent", "in_zone_percent", "edge_percent", "z_swing_percent", "oz_swing_percent", "whiff_percent", "f_strike_percent", "swing_percent", "z_swing_miss_percent", "oz_swing_miss_percent", "popups_percent", "flyballs_percent", "linedrives_percent", "groundballs_percent"]:
			reverse = False
		sortedRankings[hdr] = sorted(sortedRankings[hdr], reverse=reverse)

	for player in advanced:
		newData = {}
		for hdr in advanced[player]:
			try:
				val = float(advanced[player][hdr])
				idx = sortedRankings[hdr].index(val)
				dupes = sortedRankings[hdr].count(val)

				newData[hdr] = ((idx + 0.5 * dupes) / len(sortedRankings[hdr])) * 100
			except:
				pass

		for hdr in newData:
			advanced[player][hdr+"Percentile"] = round(newData[hdr], 2)

	with open(f"{prefix}static/baseballreference/advanced.json", "w") as fh:
		json.dump(advanced, fh, indent=4)

def writeSavantExpectedHR():
	url = "https://baseballsavant.mlb.com/leaderboard/home-runs"
	expected = {}
	for t in ["", "?year=2023&team=&player_type=Pitcher&min=0"]:
		time.sleep(0.2)
		outfile = "outmlb2"
		call(["curl", "-k", url+t, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		data = "{}"
		for script in soup.findAll("script"):
			if "var data" in script.string:
				m = re.search(r"var data = \[{(.*?)}\];", script.string)
				if m:
					data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
					data = f"{{{data}}}"
					break

		data = eval(data)
		
		for row in data:
			team = convertRotoTeam(row["team_abbrev"].lower())
			if team not in expected:
				expected[team] = {}

			player = strip_accents(row["player"]).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")

			expected[team][player] = row.copy()


	with open(f"{prefix}static/baseballreference/expectedHR.json", "w") as fh:
		json.dump(expected, fh, indent=4)


# write batter vs pitcher
def writeBVP(dateArg):

	with open(f"{prefix}static/baseballreference/bvp.json") as fh:
		bvp = json.load(fh)

	date = str(datetime.datetime.now())[:10]
	if int(dateArg.split("-")[-1]) > int(date.split("-")[-1]):
		date = str(datetime.datetime.now() + datetime.timedelta(days=1))[:10]

	for hotCold in ["hot", "cold"]:
		outfile = "outmlb2"
		time.sleep(0.2)
		url = f"https://www.rotowire.com/baseball/tables/matchup.php?type={hotCold}batter&bab=1&bhothr=0&bhotavg=0&bhottops=0&start={date}&end={date}"
		call(["curl", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		for row in data:
			pitcher = row["pitcher"].lower()
			team = convertRotoTeam(row["team"])
			opp = convertRotoTeam(row["opponent"])
			player = row["player"].lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")

			matchup = f"{player} v {pitcher}"

			if team not in bvp:
				bvp[team] = {}
			if matchup not in bvp[team]:
				bvp[team][matchup] = {}

			for key, hdr in [("atbats", "ab"), ("hits", "h"), ("hr", "hr"), ("rbi", "rbi"), ("bb", "bb"), ("k", "so")]:
				bvp[team][matchup][hdr] = int(row[key])


	with open(f"{prefix}static/baseballreference/bvp.json", "w") as fh:
		json.dump(bvp, fh, indent=4)

def writeTrades():

	url = "https://www.espn.com/mlb/transactions"
	outfile = "outmlb2"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = "{}"
	for script in soup.findAll("script"):
		if script.string and '"transactions"' in script.string:
			m = re.search(r"transactions\":\[{(.*?)}}\],", script.string)
			if m:
				data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
				data = f"{{{data}}}}}"
				break

	data = eval(data)

	with open("t", "w") as fh:
		json.dump(data, fh, indent=4)


def writeBaseballReferencePH():
	with open(f"{prefix}static/mlbprops/ev_hr.json") as fh:
		ev = json.load(fh)

	with open(f"{prefix}static/baseballreference/referenceIds.json") as fh:
		referenceIds = json.load(fh)

	with open(f"{prefix}static/baseballreference/ph.json") as fh:
		ph = json.load(fh)

	date = datetime.datetime.now()
	for player in ev:
		team = ev[player]["team"]
		if team not in ph:
			ph[team] = {}
		if player in ph[team] and ph[team][player]["updated"] == str(date)[:10]:
			continue

		if player not in referenceIds[team]:
			continue
		ph[team][player] = {
			"updated": str(date)[:10],
			"phf": 0,
			"ph": 0,
			"games": 0,
			"rest": []
		}

		pid = referenceIds[team][player].split("/")[-1][:-6]
		print(pid)
		time.sleep(0.3)
		url = f"https://www.baseball-reference.com/players/gl.fcgi?id={pid}&t=b&year={date.year}"
		outfile = "outmlb3"
		call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")
		betweenRest = 0
		for tr in soup.find("table", id="batting_gamelogs").find("tbody").findAll("tr"):
			if tr.get("class") and ("thead" in tr.get("class") or "partial_table" in tr.get("class")):
				continue
			inngs = tr.findAll("td")[7].text.lower()
			ph[team][player]["games"] += 1
			if "gs" in inngs:
				ph[team][player]["phf"] += 1
			elif "cg" not in inngs:
				ph[team][player]["ph"] += 1

			if "(" in tr.findAll("td")[1].text:
				daysSinceLast = int(tr.findAll("td")[1].text.split("(")[-1][:-1])
				if daysSinceLast == 1:
					ph[team][player]["rest"].append(betweenRest)
				betweenRest = 0
			betweenRest += 1

	with open(f"{prefix}static/baseballreference/ph.json", "w") as fh:
		json.dump(ph, fh, indent=4)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("--bvp", action="store_true", help="Batter Vs Pitcher")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--averages", help="Last Yr Averages", action="store_true")
	parser.add_argument("--rankings", help="Rankings", action="store_true")
	parser.add_argument("--roster", help="Roster", action="store_true")
	parser.add_argument("--schedule", help="Schedule", action="store_true")
	parser.add_argument("--stats", action="store_true")
	parser.add_argument("--splits", action="store_true")
	parser.add_argument("--pitches", help="Pitches", action="store_true")
	parser.add_argument("--totals", help="Totals", action="store_true")
	parser.add_argument("--trades", help="Trades", action="store_true")
	parser.add_argument("--pitching", help="Pitching", action="store_true")
	parser.add_argument("--ttoi", help="Team TTOI", action="store_true")
	parser.add_argument("--ph", help="baseball reference pinch hits", action="store_true")
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
		writeStatsVsTeam()
	elif args.bvp:
		writeBVP(date)
	elif args.ph:
		writeBaseballReferencePH()
	elif args.rankings:
		write_rankings()
		write_player_rankings()
	elif args.roster:
		writeRoster()
	elif args.pitches:
		write_batting_pitches()
		write_pitching_pitches()
	elif args.pitching:
		write_pitching()
	elif args.schedule:
		write_schedule(date)
	elif args.stats:
		write_stats(date)
	elif args.splits:
		writeSplits()
	elif args.trades:
		writeTrades()
	elif args.cron:
		write_rankings()
		write_player_rankings()
		write_batting_pitches()
		write_pitching_pitches()
		writeBVP(date)
		write_schedule(date)
		write_stats(date)
		writeSavantExpected()
		writeSavantParkFactors()
		writeSavantExpectedHR()
		writeSavantPitcherAdvanced()

	writeStatsVsTeam()
	#write_pitching()
	#writeYearAverages()
	#write_schedule(date)
	#write_stats(date)
	#write_totals()
	#write_curr_year_averages()
	#writeSavantParkFactors()
	#writeSavantExpectedHR()
	#writeSavantPitcherAdvanced()