import argparse
import json
import math
import os
import operator
import re
import threading
import queue
import requests
import time
import nodriver as uc
import csv
import unicodedata

from bs4 import BeautifulSoup as BS
from bs4 import Comment
import datetime
from sys import platform
from subprocess import call
from glob import glob
from datetime import datetime, timedelta

try:
	from controllers.functions import *
	from controllers.shared import *
except:
	from functions import *
	from shared import *

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

q = queue.Queue()
historyLock = threading.Lock()

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
	allStats = {}
	teams = [x for x in os.listdir("static/baseballreference/") if len(x) <= 3 and not x.endswith("json")]
	for team in teams:
		with open(f"static/baseballreference/{team}/stats.json") as fh:
			allStats[team] = json.load(fh)

	for date in dates:
		for game in boxscores[date]:
			if game not in schedule[date]:
				print("Game not in schedule")
				continue
			away, home = map(str, game.split(" @ "))

			gameId = boxscores[date][game].split("/")[-2]
			url = f"https://site.web.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
			outfile = "outmlb3"
			time.sleep(0.3)
			call(["curl", "-s", url, "-o", outfile])

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

			allStats[away][date] = {}
			allStats[home][date] = {}

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
						if player not in allStats[t][date]:
							allStats[t][date][player] = {}

						pitchingDecision = ""
						if "notes" in playerRow and playerRow["notes"][0]["type"] == "pitchingDecision":
							pitchingDecision = playerRow["notes"][0]["text"][0].lower()
							if pitchingDecision == "h":
								pitchingDecision = "hold"
							elif pitchingDecision == "s":
								pitchingDecision = "sv"
							try:
								allStats[t][date][player][pitchingDecision] += 1
							except:
								allStats[t][date][player][pitchingDecision] = 1

						for header, stat in zip(headers, playerRow["stats"]):
							if header == "h-ab":
								continue
							if header == "k" and title == "batting":
								header = "so"
							if header in ["pc-st"]:
								pc, st = map(int, stat.split("-"))
								allStats[t][date][player]["pc"] = pc
								allStats[t][date][player]["st"] = st
							elif header in ["bb", "hr", "h"] and title == "pitching":
								try:
									allStats[t][date][player][header+"_allowed"] = int(stat)
								except:
									allStats[t][date][player][header+"_allowed"] = 0
							else:
								val = stat
								try:
									val = int(val)
								except:
									try:
										val = float(val)
									except:
										val = 0
								allStats[t][date][player][header] = val

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
						if player not in allStats[t][date]:
							continue
						allStats[t][date][player][stat] = val

			for rosterRow in data["rosters"]:
				team = rosterRow["team"]["abbreviation"].lower()
				t = team+" gm2" if "gm2" in away else team
				if "roster" not in rosterRow:
					continue
				for playerRow in rosterRow["roster"]:
					player = parsePlayer(playerRow["athlete"]["displayName"])
					for statRow in playerRow.get("stats", []):
						hdr = statRow["shortDisplayName"].lower()
						if hdr not in allStats[t][date][player]:
							val = statRow["value"]
							try:
								val = int(val)
							except:
								pass
							allStats[t][date][player][hdr] = val

			for team in allStats:
				for player in allStats[team][date]:
					if "ip" in allStats[team][date][player]:
						ip = allStats[team][date][player]["ip"]
						outs = int(ip)*3 + int(str(ip).split(".")[-1])
						allStats[team][date][player]["outs"] = outs
					elif "ab" in allStats[team][date][player]:
						_3b = allStats[team][date][player].get("3b", 0)
						_2b = allStats[team][date][player].get("2b", 0)
						hr = allStats[team][date][player]["hr"]
						h = allStats[team][date][player]["h"]
						_1b = h - (_3b+_2b+hr)
						allStats[team][player]["1b"] = _1b
						allStats[team][player]["tb"] = 4*hr + 3*_3b + 2*_2b + _1b

						r = allStats[team][date][player]["r"]
						rbi = allStats[team][date][player]["rbi"]
						allStats[team][date][player]["h+r+rbi"] = h + r + rbi

		for team in allStats:
			realTeam = team.replace(" gm2", "")
			if not os.path.isdir(f"{prefix}static/baseballreference/{realTeam}"):
				os.mkdir(f"{prefix}static/baseballreference/{realTeam}")

			d = date+"-gm2" if "gm2" in team else date
			with open(f"{prefix}static/baseballreference/{realTeam}/stats.json", "w") as fh:
				json.dump(allStats[team], fh, indent=4)

	write_totals()
	writeSplits()

	with open(f"{prefix}static/baseballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def writeSplits():
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)

	splits = {}
	teams = [x for x in os.listdir("static/baseballreference/") if len(x) <= 3 and not x.endswith("json")]
	for team in teams:
		if team not in splits:
			splits[team] = {}

		with open(f"static/baseballreference/{team}/stats.json") as fh:
			stats = json.load(fh)

		if not stats:
			continue

		for date in stats:
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

			for player in stats[date]:
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

				for header in stats[date][player]:
					if header not in splits[team][player]:
						splits[team][player][header] = []
					val = stats[date][player][header]
					if header == "sb":
						val = int(val)
					splits[team][player][header].append(str(val))

				if "ab" in stats[date][player]:
					for header in ["2b", "3b", "sf"]:
						if header not in stats[date][player]:
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
	year = datetime.now().year
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

def writeYearByYear():
	outfile = "outYearByYear"
	url = "https://www.baseball-reference.com/leagues/majors/bat.shtml"
	call(["curl", "-s", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	table = soup.find("table", id="teams_standard_batting_totals")
	data = []
	for row in table.find_all("tr")[1:]:
		tds = row.find_all("td")
		if not tds:
			continue
		j = {"year": row.find("th").text}
		for td in tds:
			j[td.get("data-stat").lower()] = td.text
		data.append(j)
	
	with open("static/mlb/year_by_year.json", "w") as fh:
		json.dump(data, fh, indent=4)

def write_schedule(date):
	url = f"https://www.espn.com/mlb/schedule/_/date/{date.replace('-', '')}"
	outfile = "outmlb3"
	call(["curl", "-s", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/baseballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)

	#schedule[date] = []

	date = ""

	for table in soup.find_all("div", class_="ResponsiveTable"):
		if table.find("div", class_="Table__Title"):
			if "spring training" in table.find("div", class_="Table__Title").text.lower():
				continue
			date = table.find("div", class_="Table__Title").text.strip()
			date = str(datetime.strptime(date, "%A, %B %d, %Y"))[:10]
			date = date.split(" ")[-1]
		else:
			pass

		if table.find("a", class_="Schedule__liveLink"):
			continue

		if not date:
			continue

		schedule[date] = []
		if date not in boxscores:
			boxscores[date] = {}
		if date not in scores:
			scores[date] = {}

		seen = {}
		for row in table.find_all("tr")[1:]:
			tds = row.find_all("td")
			try:
				awayTeam = tds[0].find_all("a")[-1].get("href").split("/")[-2]
				homeTeam = tds[1].find_all("a")[-1].get("href").split("/")[-2]
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

async def writeHistory(playerArg, teamArg, force=False):
	if playerArg:
		playerArg = playerArg.replace("-", " ")
	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"{prefix}static/dailyev/odds.json") as fh:
		odds = json.load(fh)
	players = []
	for game in odds:
		players.extend(odds[game].keys())

	historical = nested_dict()
	urls = []
	for team in roster:
		if teamArg and teamArg != team:
			continue
		path = f"static/splits/mlb_historical/{team}.json"
		if os.path.exists(path):
			with open(path) as fh:
				historical[team] = json.load(fh)
		else:
			with open(path, "w") as fh:
				json.dump({}, fh)

		for player in roster[team]:
			if playerArg and player != playerArg:
				continue
			
			if not playerArg and player in historical[team] and not force:
				found = False
				for y in historical[team][player]:
					if "h+r+rbi" in historical[team][player][y]:
						found = True
						break
				# if we need to update HRR, continue
				if found:
					continue

			if not force and not playerArg and player not in players:
				continue
			pId = ids[team][player]
			url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}"
			urls.append((team, player, url))

	#urls = [("det", "dillon dingler", "https://www.espn.com/mlb/player/gamelog/_/id/4345620")]
	#if playerArg:
	#	print(urls)
	totThreads = min(len(urls), 7)
	threads = []
	for _ in range(totThreads):
		thread = threading.Thread(target=runHistory, args=())
		thread.start()
		threads.append(thread)

	for row in urls:
		q.put(row)

	q.join()

	for _ in range(totThreads):
		q.put((None, None, None))
	for thread in threads:
		thread.join()

def runHistory():
	uc.loop().run_until_complete(writePlayerHistory())

async def writePlayerHistory():
	browser = await uc.start(no_sandbox=True)

	while True:
		data = nested_dict()
		(team, player, url) = q.get()
		if url is None:
			q.task_done()
			break

		page = await browser.get(url)
		try:
			await page.wait_for(selector=".gamelog .dropdown__select option")
			time.sleep(0.5)
		except:
			q.task_done()
			continue

		select = await page.query_selector(".gamelog .dropdown__select")

		if not select:
			q.task_done()
			continue
		years = []
		for option in select.children:
			if option.text == datetime.now().year:
				continue
			years.append(option.text)

		#years = ["2024"]
		for year in years:
			u = f"{url}/year/{year}"

			page = await browser.get(u)
			await page.wait_for(selector=".gamelog")

			html = await page.get_content()
			soup = BS(html, "html.parser")
			hdrs = []
			for row in soup.select(".gamelog tr"):
				if row.find("td") and row.find("td").text == "Totals":
					continue
				if "totals_row" in row.get("class"):
					continue
				elif "Table__sub-header" in row.get("class"):
					hdrs = []
					for th in row.find_all("th"):
						hdrs.append(th.text.lower())
				else:
					for hdr, td in zip(hdrs, row.find_all("td")):
						# format val
						val = td.text.lower()
						if hdr == "date":
							try:
								m,d = map(int, val.split(" ")[-1].split("/"))
							except:
								print(year, url)
								continue
							val = f"{year}-{m:02}-{d:02}"
						elif hdr == "opp":
							try:
								val = td.find_all("a")[-1].text.lower()
							except:
								continue
						else:
							try:
								val = int(val)
							except:
								try:
									val = float(val)
								except:
									pass

						if val == "Infinity":
							val = None

						ks, vs = [hdr], [val]

						# add custom hdrs
						if hdr == "opp":
							ks.append("awayHome")
							vs.append("A" if "@" in td.text else "H")

						for k, v in zip(ks, vs):
							if k not in data[player][year]:
								data[player][year][k] = []	
							data[player][year][k].append(v)

			
			if "rbi" in data[player][year]:
				k = "h+r+rbi"
				if k not in data[player][year]:
					data[player][year][k] = []

				for h,r,rbi in zip(data[player][year]["h"],data[player][year]["r"],data[player][year]["rbi"]):
					data[player][year][k].append(h+r+rbi)

		with historyLock:
			path = f"static/splits/mlb_historical/{team}.json"
			try:
				with open(path) as fh:
					d = json.load(fh)
			except:
				d = {}
			d.update(data)
			with open(path, "w") as fh:
				#json.dump(d, fh, indent=4)
				json.dump(d, fh)
		q.task_done()

	browser.stop()

def writeYears():
	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		ids = json.load(fh)

	currYear = str(datetime.now())[:4]

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
			"bos": {
				"masataka yoshida": 4872598
			}
		}

	for team in ids:
		for player in ids[team]:
			pId = ids[team][player]

			time.sleep(0.2)
			url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}"
			outfile = "outmlb3"
			call(["curl", "-s", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")
			#print(url)
			if not soup.find("div", class_="gamelog"):
				continue
			select = soup.find("div", class_="gamelog").find("select", class_="dropdown__select")
			if not select:
				continue
			years = [y.text for y in select.find_all("option")]

			for year in years:
				if year == currYear:
					continue
				if year != "2020":
					#continue
					pass
				if len(year) != 4:
					for title in soup.find("div", class_="gamelog").find_all("div", class_="Table__Title"):
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

				yearStats[year][team][player] = {"tot": {}, "splits": {}}
				gamesPlayed = 0

				time.sleep(0.2)
				url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}/type/mlb/year/{year}"
				outfile = "outmlb3"
				call(["curl", "-s", url, "-o", outfile])
				soup = BS(open(outfile, 'rb').read(), "lxml")

				headers = []
				table = soup.find("div", class_="gamelog")
				rows = table.find_all("tr")
				for rowIdx, row in enumerate(rows):
					try:
						title = row.findPrevious("div", class_="Table__Title").text.lower()
					except:
						title = ""
					if "regular season" not in title:
						continue
					if not headers and row.text.lower().startswith("date"):
						tds = row.find_all("td")[3:]
						if not tds:
							tds = row.find_all("th")[3:]
						for td in tds:
							headers.append(td.text.strip().lower())
					elif "totals" in row.text.lower() or rowIdx == len(rows) - 1:
						if "totals" not in row.text.lower() and "totals_row" not in row.get("class"):
							continue
						for idx, td in enumerate(row.find_all("td")[1:]):
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
						tds = row.find_all("td")
						if len(tds) > 1 and ("@" in tds[1].text or "vs" in tds[1].text):
							date = str(datetime.strptime(tds[0].text.strip()+"/"+year, "%a %m/%d/%Y")).split(" ")[0]
							awayHome = "A" if "@" in tds[1].text else "H"
							try:
								opp = tds[1].find_all("a")[-1].get("href").split("/")[-2]
							except:
								continue

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
								for i in range(1, int(val)+1):
									if i not in yearStats[year][team][player]["tot"][hdrOver]:
										yearStats[year][team][player]["tot"][hdrOver][i] = 0
									yearStats[year][team][player]["tot"][hdrOver][i] += 1

				for hdr in yearStats[year][team][player]["splits"]:
					arr = ",".join([str(x) for x in yearStats[year][team][player]["splits"][hdr]][::-1])
					yearStats[year][team][player]["splits"][hdr] = arr


				with open(f"{prefix}static/mlbprops/stats/{year}.json", "w") as fh:
					#print(year)
					json.dump(yearStats[year], fh, indent=4)

def writeAverages():
	averages = {}

	for year in os.listdir(f"{prefix}static/mlbprops/stats/"):
		year = year[:4]

		with open(f"static/mlbprops/stats/{year}.json") as fh:
			yearStats = json.load(fh)

		for team in yearStats:
			if team not in averages:
				averages[team] = {}
			for player in yearStats[team]:
				if player not in averages[team]:
					averages[team][player] = {"tot": {}}

				averages[team][player][year] = yearStats[team][player]["tot"].copy()

				for hdr in averages[team][player][year]:
					if hdr not in averages[team][player]["tot"]:
						averages[team][player]["tot"][hdr] = averages[team][player][year][hdr]
					elif hdr.endswith("Overs"):
						for over in averages[team][player][year][hdr]:
							if over not in averages[team][player]["tot"][hdr]:
								averages[team][player]["tot"][hdr][over] = 0
							averages[team][player]["tot"][hdr][over] += averages[team][player][year][hdr][over]
					else:
						val = averages[team][player][year][hdr]
						try:
							val = int(val)
						except:
							try:
								val = float(val)
							except:
								continue
						averages[team][player]["tot"][hdr] += val

	with open(f"{prefix}static/baseballreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

def writeStatsVsTeam():
	statsVsTeam = {}
	statsVsTeamLastYear = {}
	lastYear = str(datetime.now().year - 1)
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
			if team not in statsVsTeamLastYear:
				statsVsTeamLastYear[team] = {}
			for player in stats[team]:
				if player not in statsVsTeam[team]:
					statsVsTeam[team][player] = {}
				if year == lastYear and player not in statsVsTeamLastYear[team]:
					statsVsTeamLastYear[team][player] = {}
				splits = stats[team][player]["splits"]
				if not splits:
					continue
				opps = splits["opp"].split(",")
				for idx, opp in enumerate(opps):
					if opp not in statsVsTeam[team][player]:
						statsVsTeam[team][player][opp] = {"gamesPlayed": 0}
					if year == lastYear and opp not in statsVsTeamLastYear[team][player]:
						statsVsTeamLastYear[team][player][opp] = {"gamesPlayed": 0}

					statsVsTeam[team][player][opp]["gamesPlayed"] += 1
					if year == lastYear:
						statsVsTeamLastYear[team][player][opp]["gamesPlayed"] += 1
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
							if year == lastYear:
								statsVsTeamLastYear[team][player][opp][stat] += val
						except:
							statsVsTeam[team][player][opp][stat] = val
							if year == lastYear:
								statsVsTeamLastYear[team][player][opp][stat] = val

						if stat in ["h", "1b", "tb", "r", "rbi", "outs", "h+r+rbi", "bb", "hr", "sb", "so", "k", "er"]:
							if stat+"Overs" not in statsVsTeam[team][player][opp]:
								statsVsTeam[team][player][opp][stat+"Overs"] = {}
							if year == lastYear and stat+"Overs" not in statsVsTeamLastYear[team][player][opp]:
								statsVsTeamLastYear[team][player][opp][stat+"Overs"] = {}
							for i in range(1, int(val)+1):
								if i not in statsVsTeam[team][player][opp][stat+"Overs"]:
									statsVsTeam[team][player][opp][stat+"Overs"][i] = 0
								if year == lastYear and i not in statsVsTeamLastYear[team][player][opp][stat+"Overs"]:
									statsVsTeamLastYear[team][player][opp][stat+"Overs"][i] = 0

								statsVsTeam[team][player][opp][stat+"Overs"][i] += 1
								if year == lastYear:
									statsVsTeamLastYear[team][player][opp][stat+"Overs"][i] += 1

	with open(f"{prefix}static/baseballreference/statsVsTeam.json", "w") as fh:
		json.dump(statsVsTeam, fh, indent=4)

	with open(f"{prefix}static/baseballreference/statsVsTeamLastYear.json", "w") as fh:
		json.dump(statsVsTeamLastYear, fh, indent=4)

def readBirthdays():
	with open("static/baseballreference/birthdays.json") as fh:
		bdays = json.load(fh)

	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)


	for player in bdays:
		bday = bdays[player]
		month = bday.split("-")[1]
		day = bday.split("-")[2]

		if int(month) < 3 or int(month) > 9:
			continue

		team = ""
		for t in roster:
			if player in roster[t]:
				team = t
				break

		if not team:
			continue

		statUrl = f"static/baseballreference/{team}/2024-{month}-{day}.json"
		if os.path.exists(statUrl):
			with open(statUrl) as fh:
				stats = json.load(fh)

			#print(player)
			if player in stats and "ab" in stats[player]:
				print(player, stats[player]["hr"])



def writeBirthdays():

	bdays = {}
	year = 1983
	while year != 2005:
		url = f"https://www.baseball-almanac.com/players/baseball_births.php?y={year}"
		year += 1
		time.sleep(0.3)
		outfile = "outmlb3"
		call(["curl", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for row in soup.find_all("tr")[2:]:
			tds = row.find_all("td")
			if tds[-1].text != "Active":
				continue

			player = parsePlayer(tds[0].find("a").text.replace(" ", " "))
			
			m, d, y = map(str, tds[1].text.split("-"))
			date = f"{y}-{m}-{d}"

			if player not in bdays:
				bdays[player] = date
			else:
				print(player)
				bdays[tds[0].find("a").get("href").split("=")[-1]] = date

	with open("static/baseballreference/birthdays.json", "w") as fh:
		json.dump(bdays, fh, indent=4)

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
	#teams = os.listdir(f"{prefix}static/baseballreference/")
	teams = [x.replace(".png", "") for x in os.listdir(f"/mnt/c/Users/zhech/Documents/dailyev/logos/mlb/")]
	#teams = ["chc", "lad"]
	for team in teams:

		if team not in playerIds:
			playerIds[team] = {}

		roster[team] = {}
		time.sleep(0.2)
		url = f"https://www.espn.com/mlb/team/roster/_/name/{team}/"
		outfile = "outmlb3"
		call(["curl", "-s", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for table in soup.find_all("table"):
			for row in table.find_all("tr")[1:]:
				nameLink = row.find_all("td")[1].find("a").get("href").split("/")
				fullName = parsePlayer(row.find_all("td")[1].find("a").text)
				playerId = int(nameLink[-1])
				playerIds[team][fullName] = playerId
				roster[team][fullName] = row.find_all("td")[2].text.strip()

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
	elif team == "sacramento":
		return "ath"
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
		outfile = "outmlb3"
		time.sleep(0.2)
		call(["curl", "-s", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")
		ranking = ids[idx]

		for row in soup.find("table").find_all("tr")[1:]:
			tds = row.find_all("td")
			player = row.find("a").text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "").split(" (")[0]
			team = convertTeamRankingsTeam(row.find_all("a")[1].text.lower())

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


def writeRankings():
	baseUrl = "https://www.teamrankings.com/mlb/stat/"
	pages = ["at-bats-per-game", "strikeouts-per-game", "walks-per-game", "runs-per-game", "hits-per-game", "home-runs-per-game", "singles-per-game", "doubles-per-game", "rbis-per-game", "total-bases-per-game", "earned-run-average", "earned-runs-against-per-game", "strikeouts-per-9", "home-runs-per-9", "hits-per-9", "walks-per-9", "opponent-runs-per-game", "opponent-stolen-bases-per-game", "opponent-total-bases-per-game", "opponent-rbis-per-game", "opponent-at-bats-per-game", "opponent-singles-per-game", "opponent-doubles-per-game", "opponent-home-runs-per-game", "opponent-hits-per-game", "opponent-runs-per-game"]
	ids = ["ab", "so", "bb", "r", "h", "hr", "1b", "2b", "rbi", "tb", "era", "er", "k", "hr_allowed", "h_allowed", "bb_allowed", "r_allowed", "opp_sb", "opp_tb", "opp_rbi", "opp_ab", "opp_1b", "opp_2b", "opp_hr", "opp_h", "opp_r"]

	rankings = {}
	for idx, page in enumerate(pages):
		url = baseUrl+page
		outfile = "outmlb3"
		time.sleep(0.2)
		call(["curl", "-s", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")
		ranking = ids[idx]
		lastYearRanks = []

		for row in soup.find("table").find_all("tr")[1:]:
			tds = row.find_all("td")
			team = convertTeamRankingsTeam(row.find("a").text.lower())
			if team not in rankings:
				rankings[team] = {}
			
			if ranking not in rankings[team]:
				rankings[team][ranking] = {}

			rankClass = ""
			if int(tds[0].text) <= 10:
				rankClass = "positive" if "opp" not in ranking else "negative"
			elif int(tds[0].text) >= 20:
				rankClass = "negative" if "opp" not in ranking else "positive"

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
			j[k] = rankings[team][f"opp_h"][k]+rankings[team][f"opp_r"][k]+rankings[team][f"opp_rbi"][k]
		combined.append(j)

	for idx, x in enumerate(sorted(combined, key=lambda k: k["season"], reverse=True)):
		rankings[x["team"]][f"opp_h+r+rbi"] = x.copy()
		rankings[x["team"]][f"opp_h+r+rbi"]["rank"] = idx+1
		rankings[x["team"]][f"opp_h+r+rbi"]["rankSuffix"] = addNumSuffix(idx+1)
		rankClass = ""
		if idx+1 <= 10:
			rankClass = "positive"
		elif idx+1 >= 20:
			rankClass = "negative"
		rankings[x["team"]][f"opp_h+r+rbi"]["rankClass"] = rankClass

	for idx, x in enumerate(sorted(combined, key=lambda k: k["lastYear"], reverse=True)):
		rankings[x["team"]][f"opp_h+r+rbi"]["lastYearRank"] = idx+1
		rankings[x["team"]][f"opp_h+r+rbi"]["lastYearRankSuffix"] = addNumSuffix(idx+1)

	with open(f"{prefix}static/baseballreference/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)


def write_batting_pitches():
	url = "https://www.baseball-reference.com/leagues/majors/2025-pitches-batting.shtml"
	time.sleep(0.2)
	outfile = "outmlb3"
	call(["curl", "-s", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	headers = []
	for td in soup.find("tr").find_all("th")[1:]:
		headers.append(td.text.lower())

	battingPitches = {}
	for tr in soup.find_all("tr")[1:]:
		try:
			team = convertRotoTeam(tr.find("th").find("a").get("href").split("/")[-2].lower())
		except:
			continue
		j = {}
		for td, hdr in zip(tr.find_all("td"), headers):
			j[hdr] = td.text

		battingPitches[team] = j

	playerBattingPitches = {}
	referenceIds = {}
	for comment in soup.find_all(text=lambda text:isinstance(text, Comment)):
		if "div_players_pitches_batting" in comment:
			soup = BS(comment, "lxml")

			headers = []
			for th in soup.find("tr").find_all("th")[1:]:
				headers.append(th.text.lower())

			for tr in soup.find_all("tr")[1:]:
				tds = tr.find_all("td")
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
	url = "https://www.baseball-reference.com/leagues/majors/2024-pitches-pitching.shtml"
	time.sleep(0.2)
	outfile = "outmlb3"
	call(["curl", "-s", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	headers = []
	for td in soup.find("tr").find_all("th")[1:]:
		headers.append(td.text.lower())

	pitchingPitches = {}
	for tr in soup.find_all("tr")[1:]:
		try:
			team = convertRotoTeam(tr.find("th").find("a").get("href").split("/")[-2].lower())
		except:
			continue
		j = {}
		for td, hdr in zip(tr.find_all("td"), headers):
			j[hdr] = td.text

		pitchingPitches[team] = j

	playerPitchingPitches = {}
	for comment in soup.find_all(text=lambda text:isinstance(text, Comment)):
		if "div_players_pitches_pitching" in comment:
			soup = BS(comment, "lxml")

			headers = []
			for th in soup.find("tr").find_all("th")[1:]:
				headers.append(th.text.lower())

			for tr in soup.find_all("tr")[1:]:
				tds = tr.find_all("td")
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
		return "ath"
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

def writeBarrels(date):
	last_year = str(datetime.now().year - 1)

	with open(f"updated.json") as fh:
		updated = json.load(fh)
	updated["barrels"] = str(datetime.now())
	with open(f"updated.json", "w") as fh:
		json.dump(updated, fh, indent=4)

	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)
	teamGameDts = {}
	for dt, gameRows in schedule.items():
		for row in gameRows:
			away,home = map(str, row["game"].split(" @ "))
			teamGameDts.setdefault(away, [])
			teamGameDts.setdefault(home, [])
			teamGameDts[away].append(dt)
			teamGameDts[home].append(dt)

	gamesToday = schedule[date]
	teamGame = {}
	for row in schedule[date]:
		game = row["game"]
		a,h = map(str, game.split(" @ "))
		teamGame[a] = game
		teamGame[h] = game

	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open("static/baseballreference/percentiles.json") as fh:
		percentiles = json.load(fh)

	with open("static/baseballreference/expected.json") as fh:
		expected = json.load(fh)

	with open("static/baseballreference/expected_sorted.json") as fh:
		expectedHist = json.load(fh)

	with open("static/baseballreference/homer_logs.json") as fh:
		homerLogs = json.load(fh)

	b = "https://api.github.com/repos/zhecht/lines/contents/static"
	hdrs = {"Accept": "application/vnd.github.v3.raw"}
	response = requests.get(f"{b}/dingers/ev.json", headers=hdrs)
	evData = response.json()

	response = requests.get(f"{b}/bpp/factors.json", headers=hdrs)
	bppFactors = response.json()

	barrels = []
	for team, players in expectedHist.items():
		game = teamGame.get(team, "")
		with open(f"static/splits/mlb/{team}.json") as fh:
			splits = json.load(fh)
		with open(f"static/splits/mlb_historical/{team}.json") as fh:
			splitsHist = json.load(fh)

		for player, data in players.items():
			hrLogs = []
			dtLogs = []

			if "P" in roster[team].get(player, "") or data["grouping_code"][0] == "Pitcher":
				continue

			try:
				hrLogs.extend(splitsHist[player][last_year]["hr"])
				dtLogs.extend(splitsHist[player][last_year]["date"])
			except:
				pass

			try:
				hrLogs.extend(splits[player]["hr"])
				dtLogs.extend(splits[player]["dt"])
			except:
				pass

			evBook = evLine = ""
			if player in evData:
				evBook = evData[player]["book"]
				evLine = evData[player]["line"]

			# Trends
			realExpected = nested_dict()
			dts = data["dt"]
			for key, vals in data.items():
				realExpected[key] = []
				for i in range(len(vals)):
					if dts[i] in teamGameDts[team]:
						realExpected[key].append(vals[i])

			game_trends = nested_dict()
			for key, vals in realExpected.items():
				if key in ["entity_name", "href"]:
					continue
				if not vals:
					continue
				if "." in str(vals[-1]):
					vals = [float(x or 0) for x in vals]
				else:
					try:
						vals = [int(x or 0) for x in vals]
					except:
						continue
				if len(vals) >= 5:
					diff = vals[-1] - vals[-4]
					if isinstance(diff, float) and not diff.is_integer():
						diff = round(diff, 2)
					game_trends[key]["3G"] = diff
				if len(vals) >= 7:
					diff = vals[-1] - vals[-6]
					if isinstance(diff, float) and not diff.is_integer():
						diff = round(diff, 2)
					game_trends[key]["5G"] = diff

			bppFactor = playerFactor = ""
			if game in bppFactors and player in bppFactors[game].get("players",[]):
				bppFactor = bppFactors[game]["hr"]
				playerFactor = bppFactors[game]["players"][player]["hr"]

			j = {
				"team": team, "game": game,
				"book": evBook, "line": evLine,
				"player": player,
				"homerLogs": homerLogs[team].get(player, {}),
				"game_trends": game_trends,
				"bpp": bppFactor, "playerFactor": playerFactor
			}

			for key in ["bip", "pa", "barrel_ct", "barrels_per_bip", "launch_angle_avg", "sweet_spot_percent", "hard_hit_ct", "hard_hit_percent", "exit_velocity_avg", "distance_hr_avg", "distance_avg"]:
				j[key] = data[key][-1]
				if "." in str(j[key]):
					j[key] = round(float(j[key]), 2)
				#j[key+"Percentile"] = percentiles.get(key, {})

			barrels.append(j)

	#percentiles = nested_dict()
	trendsArrs = nested_dict()
	for row in barrels:
		for key in ["barrel_ct", "hard_hit_ct", "barrels_per_bip", "hard_hit_percent", "exit_velocity_avg"]:
			for period, val in row["game_trends"][key].items():
				trendsArrs[key].setdefault(period, [])
				trendsArrs[key][period].append(val)

	for key, periods in trendsArrs.items():
		for period, arr in periods.items():
			k = f"game_trends.{key}.{period}"

			arr = np.array(arr)
			all_percentiles =  [(np.sum(arr < val) / len(arr)) * 100 for val in arr]
			# val -> percentile map
			percentiles[k] = {str(float(round(k2, 2))): round(v2) for k2,v2 in zip(arr,all_percentiles)}

	for row in barrels:
		for key in ["barrel_ct", "hard_hit_ct", "barrels_per_bip", "hard_hit_percent", "exit_velocity_avg"]:
			for period, val in list(row["game_trends"][key].items()):
				k = f"game_trends.{key}.{period}"
				row["game_trends"][key][period+"Percentile"] = percentiles[k][str(float(val))]

	for row in barrels:
		keys = []
		for key in row:
			if percentiles.get(key):
				keys.append(key)
		for key in keys:
			if row[key] is None:
				continue
			v = str(float(row[key]))
			row[key+"Percentile"] = percentiles[key].get(v, 0)

	with open("static/baseballreference/barrels.json", "w") as fh:
		json.dump(barrels, fh)


def writeHomerLogs2():
	CURR_YEAR = str(datetime.now().year)
	homerLogs = nested_dict()



	with open("static/baseballreference/homer_logs.json", "w") as fh:
		json.dump(homerLogs, fh, indent=4)

def writeHomerLogs():
	CURR_YEAR = str(datetime.now().year)
	b = "https://api.github.com/repos/zhecht/lines/contents/static/dingers/ev.json"
	hdrs = {"Accept": "application/vnd.github.v3.raw"}
	response = requests.get(f"{b}", headers=hdrs)
	evData = response.json()

	homerLogs = nested_dict()
	for team in os.listdir(f"static/splits/mlb_historical/"):
		with open(f"static/splits/mlb_historical/{team}") as fh:
			hist = json.load(fh)
		with open(f"static/splits/mlb/{team}") as fh:
			teamLogs = json.load(fh)
		with open(f"static/splits/mlb_feed/{team}") as fh:
			teamFeeds = json.load(fh)

		team = team.replace(".json", "")
		for player, data in teamLogs.items():
			if "hr" not in data or "ab" not in data:
				continue
			hrs = [(dt,hr,ab) for dt,hr,ab in zip(data["dt"], data["hr"], data["ab"])]

			for year, yearData in hist.get(player, {}).items():
				if year == CURR_YEAR:
					continue
				if yearData and "ab" in yearData:
					hrs.extend([(dt,hr,ab) for dt,hr,ab in zip(yearData["date"], yearData["hr"], yearData["ab"])])

			hrs = sorted(hrs)
			if not hrs:
				continue

			hits = []
			btwn = btwnAB = 0
			for dt, val, ab in hrs:
				if val > 0:
					# -1 on AB to exclude HR
					hits.append((dt, btwn, btwnAB-1))
					btwn = btwnAB = 0
				btwn += 1
				btwnAB += ab

			if hits:
				lastHRDt = hits[-1][0]
				lastHR = btwn
				lastHR_AB = btwnAB-1

			gamesBtwn = [x for _,x,ab in hits]
			if len(gamesBtwn) > 1:
				gamesBtwnAvg = round(sum(gamesBtwn) / len(gamesBtwn), 1)
				std_dev = np.std(gamesBtwn, ddof=1)
				if np.isnan(std_dev):
					std_dev = 0
				else:
					std_dev = round(std_dev, 2)

				if std_dev:
					z_score = round((lastHR - gamesBtwnAvg) / std_dev, 2)
				gamesBtwnMed = median(gamesBtwn)
				gamesBtwnDiff = round(lastHR - gamesBtwnAvg, 2)

			abBtwn = [ab for _,x,ab in hits]
			std_devAB = abBtwnMed = abBtwnDiff = 0
			if len(abBtwn) > 1:
				abBtwnAvg = round(sum(abBtwn) / len(abBtwn), 1)
				std_devAB = np.std(abBtwn, ddof=1)
				if np.isnan(std_devAB):
					std_devAB = 0
				else:
					std_devAB = round(std_devAB, 2)

				abBtwnMed = median(abBtwn)
				abBtwnDiff = round(lastHR_AB - abBtwnAvg, 2)
				if std_devAB:
					z_scoreAB = round((lastHR_AB - abBtwnAvg) / std_devAB, 2)
					ab_med_z_score = round((lastHR_AB - abBtwnMed) / std_devAB, 2)

			evBook = evLine = ""
			if player in evData:
				evBook = evData[player]["book"]
				evLine = evData[player]["line"]

			# Closest
			playerFeeds = teamFeeds.get(player, {})
			closest = []
			feedDts = []
			for dt_pa, row in sorted(playerFeeds.items()):
				y,m,d,pa = map(str, dt_pa.split("-"))
				dt = f"{y}-{m}-{d}"
				if dt not in feedDts:
					feedDts.append(dt)
				if row["result"] != "Home Run" and int(row["hr/park"].split("/")[0] or 0) > 0:
					row["dt"] = dt
					closest.append(row)

			lastClosest = 0
			lastClosestDt = ""
			if closest:
				lastClosestDt = closest[-1]["dt"]
				lastClosest = len(feedDts) - feedDts.index(closest[-1]["dt"])

			homerLogs[team][player] = {
				"last": lastHR, "lastHRDt": lastHRDt,
				"lastHR_AB": lastHR_AB,
				"sd": std_dev, "z": z_score,
				"book": evBook, "line": evLine,
				"gamesBtwnMed": gamesBtwnMed, "gamesBtwnAvg": gamesBtwnAvg, "gamesBtwnDiff": gamesBtwnDiff,
				#"gamesBtwn": ",".join(map(str, gamesBtwn)),
				#"abBtwn": ",".join(map(str, abBtwn)),
				#"homerDts": [x for x,_,_ in hits],
				"gamesBtwn": gamesBtwn,
				"abBtwn": abBtwn,
				"abSD": std_devAB, "abZ": z_scoreAB, "ab_med_z_score": ab_med_z_score,
				"abBtwnMed": abBtwnMed, "abBtwnAvg": abBtwnAvg, "abBtwnDiff": abBtwnDiff,
				"closest_ct": len(closest), "lastClosest": lastClosest, "lastClosestDt": lastClosestDt
			}

	with open("static/baseballreference/homer_logs.json", "w") as fh:
		json.dump(homerLogs, fh, indent=4)

def writeSavantPercentiles():
	with open("static/baseballreference/qualified_expected.json") as fh:
		expected = json.load(fh)

	# Percentile Rankings Qualifiers: 2.1 PA per team game for batters, 1.25 PA per team game for pitchers. 
	rows = []
	for team, players in expected.items():
		for player, data in players.items():
			data["team"] = team
			data["player"] = player
			rows.append(data)

	percentiles = nested_dict()
	keys = ["barrel_ct", "barrels_per_bip", "launch_angle_avg", "sweet_spot_percent", "hard_hit_ct", "hard_hit_percent", "exit_velocity_avg", "distance_hr_avg", "distance_avg"]
	#keys = ["sweet_spot_percent"]
	for key in keys:
		arr = np.array([x[key] for x in rows if x[key]])
		arr = arr.astype(float)

		all_percentiles =  [(np.sum(arr < val) / len(arr)) * 100 for val in arr]
		# val -> percentile map
		percentiles[key] = {str(round(k2, 2)): round(v2) for k2,v2 in zip(arr,all_percentiles)}

	with open("static/baseballreference/percentiles.json", "w") as fh:
		json.dump(percentiles, fh)

def writePitcherSavantPercentiles():
	with open("static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)

	rows = []
	for player, data in advanced.items():
		data["player"] = player
		rows.append(data)

	keys = [x for x in rows[0] if x.endswith("Percentile")]
	#keys = ["barrel_batted_ratePercentile"]

	percentiles = nested_dict()
	for key in keys:
		stat = key.replace("Percentile", "")
		arr = [(x[key],x[stat]) for x in rows]
		closest30 = min(arr, key=lambda x: abs(x[0] - 30))
		closest70 = min(arr, key=lambda x: abs(x[0] - 70))

		#print(key, closest30, closest70)
		percentiles[stat] = [closest70[-1], closest30[-1]]

	with open("static/baseballreference/percentiles.json", "w") as fh:
		json.dump(percentiles, fh)

def writeSavantParkFactors():
	year = datetime.now().year
	url = f"https://baseballsavant.mlb.com/leaderboard/statcast-park-factors?type=year&year={year}&batSide=&stat=index_wOBA&condition=All&rolling="
	time.sleep(0.2)
	outfile = "outmlb3"
	call(["curl", "-s", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = "{}"
	for script in soup.find_all("script"):
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

def writeQualified():
	outfile = "outmlb3"
	qualified_expected = nested_dict()
	url = "https://baseballsavant.mlb.com/leaderboard/expected_statistics"
	call(["curl", "-s", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = "{}"
	for script in soup.find_all("script"):
		if "var data" in script.string:
			m = re.search(r"var data = \[{(.*?)}\];", script.string)
			if m:
				data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
				data = f"{{{data}}}"
				break

	data = eval(data)
	
	for row in data:
		team = convertRotoTeam(row["entity_team_name_alt"].lower())
		player = parsePlayer(row["entity_name"])
		#print(player)
		last, first = map(str, player.split(", "))
		player = f"{first} {last}"

		row["dt"] = date
		qualified_expected[team][player] = row.copy()

	with open(f"{prefix}static/baseballreference/qualified_expected.json", "w") as fh:
		json.dump(qualified_expected, fh, indent=4)

def writeSavantExpected(date):
	with open(f"{prefix}static/baseballreference/expected_historical.json") as fh:
		expectedHist = json.load(fh)

	writeQualified()

	outfile = "outmlb3"
	url = "https://baseballsavant.mlb.com/leaderboard/expected_statistics?min=1"
	expected = nested_dict()
	for t in ["", "&type=pitcher"]:
		time.sleep(0.2)
		call(["curl", "-s", url+t, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		data = "{}"
		for script in soup.find_all("script"):
			if "var data" in script.string:
				m = re.search(r"var data = \[{(.*?)}\];", script.string)
				if m:
					data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
					data = f"{{{data}}}"
					break

		data = eval(data)
		
		for row in data:
			team = convertRotoTeam(row["entity_team_name_alt"].lower())
			player = parsePlayer(row["entity_name"])
			#print(player)
			last, first = map(str, player.split(", "))
			player = f"{first} {last}"

			row["dt"] = date
			expected[team][player] = row.copy()


			expectedHist.setdefault(team, {})
			expectedHist[team].setdefault(player, {})
			expectedHist[team][player][date] = row.copy()

	with open(f"{prefix}static/baseballreference/expected.json", "w") as fh:
		json.dump(expected, fh, indent=4)
	with open(f"{prefix}static/baseballreference/expected_historical.json", "w") as fh:
		json.dump(expectedHist, fh)

	hist_sorted = nested_dict()
	for team, players in expectedHist.items():
		for player, dts in players.items():
			for dt, data in sorted(dts.items()):
				if "dt" not in data:
					data["dt"] = dt
				for key, val in data.items():
					hist_sorted[team][player].setdefault(key, [])
					hist_sorted[team][player][key].append(val)

	with open(f"{prefix}static/baseballreference/expected_sorted.json", "w") as fh:
		json.dump(hist_sorted, fh)

def writeSavantPitcherAdvanced():

	advanced = {}
	year = datetime.now().year
	lastYear = year - 1
	for yr in [year, lastYear]:
		url = f"https://baseballsavant.mlb.com/leaderboard/custom?year={yr}&type=pitcher&filter=&sort=1&sortDir=desc&min=10&selections=babip,p_walk,p_k_percent,p_bb_percent,p_ball,p_called_strike,p_hit_into_play,xba,exit_velocity_avg,launch_angle_avg,sweet_spot_percent,barrel_batted_rate,hard_hit_percent,out_zone_percent,out_zone,in_zone_percent,in_zone,pitch_hand,n,&chart=false&x=p_walk&y=p_walk&r=no&chartType=beeswarm"
		time.sleep(0.2)
		outfile = "outmlb3"
		call(["curl", "-s", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		data = "{}"
		for script in soup.find_all("script"):
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

		url = "advanced"
		if yr == lastYear:
			url += "LastYear"
		with open(f"{prefix}static/baseballreference/{url}.json", "w") as fh:
			json.dump(advanced, fh, indent=4)

def writeSavantExpectedHR():
	url = "https://baseballsavant.mlb.com/leaderboard/home-runs"
	expected = {}
	for t in ["", "?year=2024&team=&player_type=Pitcher&min=0"]:
		time.sleep(0.2)
		outfile = "outmlb3"
		call(["curl", "-s", url+t, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		data = "{}"
		for script in soup.find_all("script"):
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

def writeTrades():

	url = "https://www.espn.com/mlb/transactions"
	outfile = "outmlb3"
	call(["curl", "-s", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = "{}"
	for script in soup.find_all("script"):
		if script.string and '"transactions"' in script.string:
			m = re.search(r"transactions\":\[{(.*?)}}\],", script.string)
			if m:
				data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
				data = f"{{{data}}}}}"
				break

	data = eval(data)

	with open("t", "w") as fh:
		json.dump(data, fh, indent=4)

async def writePH(playerArg):
	with open(f"{prefix}static/baseballreference/referenceIds.json") as fh:
		referenceIds = json.load(fh)

	with open(f"{prefix}static/baseballreference/ph.json") as fh:
		ph = json.load(fh)

	with open("static/dailyev/odds.json") as fh:
		odds = json.load(fh)

	browser = await uc.start(no_sandbox=True)
	for game in odds:
		away, home = map(str, game.split(" @ "))
		for player in odds[game]:
			if playerArg and player != playerArg:
				continue

			if player in referenceIds[away]:
				team = away
			elif player in referenceIds[home]:
				team = home
			else:
				continue

			if not playerArg and team in ph and player in ph[team]:
				continue

			pid = referenceIds[team][player]
			url = f"https://www.baseball-reference.com{pid}"

			ph.setdefault(team, {})
			ph[team].setdefault(player, {})
			ph[team][player] = {}

			page = await browser.get(url)
			await page.wait_for(selector="#appearances tbody tr")
			html = await page.get_content()
			soup = BS(html, "lxml")
			for row in soup.select("#appearances tbody tr"):
				if row.get("class") and ("spacer" in row.get("class") or "partial_table" in row.get("class")):
					continue
				year = row.find("th").text
				#print(player, year)
				try:
					g = row.select("td[data-stat=games_all]")[0].text
				except:
					continue
				gs = row.select("td[data-stat=games_started_all]")[0].text
				phs = row.select("td[data-stat=games_at_ph]")
				if not phs:
					continue

				ph[team][player].setdefault(year, {})

				ph[team][player][year]["ph"] = int(phs[0].text or 0)
				ph[team][player][year]["g"] = int(g or 0)
				ph[team][player][year]["gs"] = int(gs or 0)

			with open(f"{prefix}static/baseballreference/ph.json", "w") as fh:
				json.dump(ph, fh, indent=4)

	browser.stop()
	with open(f"{prefix}static/baseballreference/ph.json", "w") as fh:
		json.dump(ph, fh, indent=4)

def writeBaseballReferencePH(playerArg):
	with open(f"{prefix}static/dailyev/odds.json") as fh:
		evOdds = json.load(fh)

	with open(f"{prefix}static/baseballreference/referenceIds.json") as fh:
		referenceIds = json.load(fh)

	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"{prefix}static/baseballreference/ph.json") as fh:
		ph = json.load(fh)

	date = datetime.now()
	for game in evOdds:
		for player in evOdds[game]:
			if playerArg and player != playerArg:
				continue

			away, home = map(str, game.split(" @ "))
			team = ""
			if player in roster[away]:
				team = away
			elif player in roster[home]:
				team = home

			if team not in ph:
				ph[team] = {}

			if player not in referenceIds[team]:
				continue

			pid = referenceIds[team][player]
			print(pid)
			time.sleep(0.3)
			url = f"https://www.baseball-reference.com{pid}"
			outfile = "outmlb3"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-s", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			print(len(soup.select("#appearances")))
			for row in soup.select("#appearances tbody tr"):
				if "spacer" in row.get("class"):
					continue
				year = row.find("th").text
				print(year)
				g = row.select("td[data-stat=games_all]")[0].text
				gs = row.select("td[data-stat=games_started_all]")[0].text
				ph[team].setdefault(player, {})
				ph[team][player].setdefault(year, {})
				ph[team][player][year]["ph"] = row.select("td[data-stat=games_at_ph]")[0].text
				ph[team][player][year]["g"] = g
				ph[team][player][year]["gs"] = gs
			continue

			# full game logs
			url = f"https://www.baseball-reference.com/players/gl.fcgi?id={pid}&t=b&year=2024"
			outfile = "outmlb3"
			call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-s", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")
			betweenRest = 0
			for tr in soup.find("table", id="players_standard_batting").find("tbody").find_all("tr"):
				if tr.get("class") and ("thead" in tr.get("class") or "partial_table" in tr.get("class")):
					continue
				inngs = tr.find_all("td")[7].text.lower()
				ph[team][player]["games"] += 1
				if "gs" in inngs:
					ph[team][player]["phf"] += 1
				elif "cg" not in inngs:
					ph[team][player]["ph"] += 1

				if "(" in tr.find_all("td")[1].text:
					daysSinceLast = int(tr.find_all("td")[1].text.split("(")[-1][:-1])
					if daysSinceLast == 1:
						ph[team][player]["rest"].append(betweenRest)
					betweenRest = 0
				betweenRest += 1

	with open(f"{prefix}static/baseballreference/ph.json", "w") as fh:
		json.dump(ph, fh, indent=4)

def printStuff():

	if False:
		# https://www.retrosheet.org/gamelogs/glfields.txt
		hrs = {}
		for gamelog in glob("static/mlbprops/gamelogs/*"):
			with open(gamelog) as fh:
				reader = csv.reader(fh)
				rows = [x for x in reader]

			for row in rows:
				date = row[0]
				if date not in hrs:
					hrs[date] = []

				awayHR = int(row[25])
				homeHR = int(row[53])
				hrs[date].append(awayHR + homeHR)

		for team in glob("static/baseballreference/*"):
			if team.endswith("json"):
				continue

			for file in glob(f"{team}/*"):
				date = file.split("/")[-1].replace(".json", "").replace("-", "").replace(" gm2", "")
				with open(file) as fh:
					stats = json.load(fh)

				if date not in hrs:
					hrs[date] = []

				hr = 0
				for player in stats:
					if "ab" not in stats[player]:
						continue
					hr += stats[player].get("hr", 0)

				hrs[date].append(hr)

		res = {}
		days = {}
		for date in hrs:
			year = date[:4]
			month = date[4:6]
			day = date[6:].replace("gm2", "")
			if month not in ["04", "05", "06"]:
				continue
			if year not in res:
				res[year] = {}
				days[year] = {}
			if month not in res[year]:
				res[year][month] = []
				days[year][month] = {}
			if day not in days[year][month]:
				days[year][month][day] = []

			res[year][month].extend(hrs[date])
			days[year][month][day].extend(hrs[date])

		for year in sorted(res):
			for month in sorted(res[year]):
				hrPerGame = sum(res[year][month]) / len(res[year][month])
				if year == "2024":
					hrPerGame *= 2
				print(year, month, round(hrPerGame, 2))

				if year == "2024":
					for day in sorted(days[year][month]):
						hrPerGame = sum(days[year][month][day]) / len(days[year][month][day])
						print("\t", year, month, day, round(hrPerGame, 2))
						#print("\t", year, month, day, sum(days[year][month][day]))


def writeDailyHomers():
	res = {}
	for team in os.listdir("static/baseballreference/"):
		if team.endswith("json"):
			continue
		for file in glob(f"static/baseballreference/{team}/*"):
			date = file.replace(".json", "").split("/")[-1]
			if date not in res:
				res[date] = []

			with open(file) as fh:
				stats = json.load(fh)

			for player in stats:
				if "ab" in stats[player]:
					if stats[player]["hr"] > 0:
						res[date].append((team, player))

	txt = ""
	for date in sorted(res):
		txt += f"{date}\n"
		for team, player in res[date]:
			txt += f"\t{team}: {player}\n"

	with open("homers", "w") as fh:
		fh.write(txt)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("--bvp", action="store_true", help="Batter Vs Pitcher")
	parser.add_argument("--player")
	parser.add_argument("--team", "-t")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--averages", help="Last Yr Averages", action="store_true")
	parser.add_argument("--birthdays", action="store_true")
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
	parser.add_argument("--year", help="Year by Year Avg", action="store_true")
	parser.add_argument("--history", action="store_true")
	parser.add_argument("--force", action="store_true")
	parser.add_argument("--commit", action="store_true")
	parser.add_argument("--brl", action="store_true")
	parser.add_argument("--tmrw", action="store_true")

	args = parser.parse_args()

	if args.start:
		curr_week = args.start

	date = args.date
	if args.tmrw:
		date = str(datetime.now() + timedelta(days=1))[:10]
	elif not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.year:
		writeYearByYear()

	if args.history:
		uc.loop().run_until_complete(writeHistory(args.player, args.team, args.force))

	if args.averages:
		writeYears()
		writeStatsVsTeam()
		writeAverages()
	elif args.birthdays:
		writeBirthdays()
	elif args.ph:
		uc.loop().run_until_complete(writePH(args.player))
		#writeBaseballReferencePH(args.player)
	elif args.rankings:
		writeRankings()
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
	elif args.brl:
		writeHomerLogs()
		writeBarrels(date)
	elif args.cron:
		writeRankings()
		write_player_rankings()
		write_batting_pitches()
		write_pitching_pitches()
		#write_schedule(date)
		#write_stats(date)
		writeSavantExpected(date)
		writeSavantParkFactors()
		writeSavantPercentiles()
		writeHomerLogs()
		writeBarrels(date)
		writeSavantExpectedHR()
		writeSavantPitcherAdvanced()

	#readBirthdays()
	#writeSavantExpected(date)
	#writeSavantPercentiles()
	#writeHomerLogs()
	#writeBarrels()

	#writeYears()
	#writeStatsVsTeam()
	#writeAverages()
	#write_pitching()
	#write_schedule(date)
	#write_stats(date)
	#write_totals()
	#write_curr_year_averages()
	#writeSavantParkFactors()
	#writeSavantExpectedHR()
	#writeSavantPitcherAdvanced()

	if args.commit:
		commitChanges()