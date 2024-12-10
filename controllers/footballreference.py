import argparse
from datetime import datetime
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

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "")
	if player == "josh palmer":
		player = "joshua palmer"
	elif player == "gabe davis":
		player = "gabriel davis"
	elif player == "trevon moehrig woodard":
		player = "trevon moehrig"
	elif player == "chig okonkwo":
		player = "chigoziem okonkwo"
	return player

def writeStats(week):
	with open(f"static/nfl/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"static/nfl/stats.json") as fh:
		stats = json.load(fh)

	if week not in stats:
		stats[week] = {}

	for game in boxscores[week]:
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/summary?region=us&lang=en&contentorigin=espn&event={boxscores[week][game]}"
		stats[week][game] = {}

		outfile = "outnfl"
		time.sleep(0.2)
		call(["curl", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		if "boxscore" not in data or "players" not in data["boxscore"]:
			continue

		stats[week][game]["scoring"] = {}
		score = [0,0]
		twoPt = {}
		for scoring in data["scoringPlays"]:
			q = str(scoring["period"]["number"])
			if q not in stats[week][game]["scoring"]:
				stats[week][game]["scoring"][q] = [0,0]
				stats[week][game]["scoring"][q] = [scoring["awayScore"] - score[0], scoring["homeScore"] - score[1]]
			else:
				stats[week][game]["scoring"][q] = [stats[week][game]["scoring"][q][0] + scoring["awayScore"] - score[0], stats[week][game]["scoring"][q][1] + scoring["homeScore"] - score[1]]
			#print(q, score, scoring["awayScore"], scoring["homeScore"])
			score = [scoring["awayScore"], scoring["homeScore"]]
			if "Two-Point Conversion" in scoring["text"]:
				txt = scoring["text"].lower()
				if "failed" in txt:
					continue
				if " run " in txt:
					player = parsePlayer(txt.split("(")[-1].split(" run ")[0])
					if player not in twoPt:
						twoPt[player] = 0
					twoPt[player] += 1
				else:
					player = parsePlayer(txt.split("(")[-1].split(" pass ")[0])
					if player not in twoPt:
						twoPt[player] = 0
					twoPt[player] += 1

					player = parsePlayer(txt.split("(")[-1].split(" pass to ")[-1].split(" for two")[0])
					if player not in twoPt:
						twoPt[player] = 0
					twoPt[player] += 1

		for i in range(1, 5):
			if str(i) not in stats[week][game]["scoring"]:
				stats[week][game]["scoring"][str(i)] = [0,0]


		for teamRow in data["boxscore"]["players"]:
			for statRow in teamRow["statistics"]:
				prop = statRow["name"].replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("defensive", "def").replace("interceptions", "int")
				if prop in ["punting", "puntReturns", "kickReturns"]:
					continue

				headers = []
				for hdr in statRow["labels"]:
					h = hdr.lower().replace("yds", "yd")
					p = f"{prop}_{h}"
					if p == "pass_int":
						p = "int"
					elif p == "pass_c/att":
						p = "pass_cmp/att"
					elif p == "rush_car":
						p = "rush_att"
					elif p == "rec_rec":
						p = "rec"
					elif p == "rec_tgts":
						p = "tgt"
					elif p == "def_tot":
						p = "tackles+ast"
					elif p == "def_sacks":
						p = "sacks"
					elif p == "kicking_fg":
						p = "fgm/fga"
					elif p == "rush_long":
						p = "longest_rush"
					elif p == "rec_long":
						p = "longest_rec"
					headers.append(p)

				for playerRow in statRow["athletes"]:
					player = parsePlayer(playerRow["athlete"]["displayName"])
					if player not in stats[week][game]:
						stats[week][game][player] = {"2pt": 0}
					if player in twoPt:
						stats[week][game][player]["2pt"] += twoPt[player]
						del twoPt[player]
					for stat, hdr in zip(playerRow["stats"], headers):
						if "/" in hdr:
							s1,s2 = map(str, stat.split("/"))
							stats[week][game][player][hdr.split("/")[0]] = s1
							stats[week][game][player]["pass_"+hdr.split("/")[1]] = s2
						else:
							stats[week][game][player][hdr] = stat

					if "rec_yd" in stats[week][game][player]:
						if "fumbles_lost" not in stats[week][game][player]:
							stats[week][game][player]["fumbles_lost"] = 0.0
							stats[week][game][player]["fumbles_fum"] = 0.0
							stats[week][game][player]["fumbles_rec"] = 0.0

	with open(f"static/nfl/stats.json", "w") as fh:
		json.dump(stats, fh, indent=4)

	writeTotals()

def writeTotals():
	with open(f"static/nfl/stats.json") as fh:
		stats = json.load(fh)

	with open(f"static/nfl/schedule.json") as fh:
		schedule = json.load(fh)

	totals = {}
	for week in stats:
		for game in stats[week]:
			for player in stats[week][game]:

				if player == "scoring":
					away = True
					for idx, team in enumerate(game.split(" @ ")):
						away = idx == 0
						if team not in totals:
							totals[team] = {
								"1h": [], "1h_against": [], "2h": [], "2h_against": [], "full": [], "full_against": []
							}
						for i in range(1, 5):
							a = stats[week][game][player][str(i)]
							if not away:
								a = a[::-1]
							if str(i) not in totals[team]:
								totals[team][f"{i}"] = []
								totals[team][f"{i}_against"] = []

							totals[team][f"{i}"].append(a[0])
							totals[team][f"{i}_against"].append(a[1])

						w = int(week) - 1
						bye = False
						for wk in schedule:
							found = False
							for g in schedule[wk]:
								if team in g.split(" @ "):
									found = True
									break
							if not found:
								bye = True
						if bye:
							w -= 1

						try:
							for which in ["", "_against"]:
								totals[team][f"1h{which}"].append(totals[team][f"1{which}"][w] + totals[team][f"2{which}"][w])
								totals[team][f"2h{which}"].append(totals[team][f"3{which}"][w] + totals[team][f"4{which}"][w])
								totals[team][f"full{which}"].append(totals[team][f"1h{which}"][w] + totals[team][f"2h{which}"][w])
						except:
							continue
					continue

				if player not in totals:
					totals[player] = {"gamesPlayed": 0}

				totals[player]["gamesPlayed"] += 1
				for hdr in stats[week][game][player]:
					if hdr not in totals[player]:
						totals[player][hdr] = 0
						totals[player][hdr+"Splits"] = []

					val = stats[week][game][player][hdr]

					try:
						val = float(val)
						totals[player][hdr] += val
					except:
						pass

					totals[player][hdr+"Splits"].append(val)

	with open(f"static/nfl/totals.json", "w") as fh:
		#json.dump(totals, fh)
		json.dump(totals, fh, indent=4)

def writeRedzone():
	redzone = {}
	redzoneTotals = {}
	outfile = f"outnfl"
	year = datetime.now().year

	for team in SNAP_LINKS:
		#continue
		url = f"https://www.footballguys.com/stats/redzone/teams?team={team.upper()}&year={year}"
		time.sleep(0.2)
		os.system(f"curl -k \"{url}\" -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")

		redzone[team] = {}
		redzoneTotals[team] = {}
		rows = soup.find("div", id="stats_redzone_team_data").findAll("tr")[::-1]
		pos = ""
		for row in rows:
			txt = row.find("td").text.lower().strip()
			if "qb totals" in txt:
				break

			if "totals" in txt:
				pos = txt.split(" ")[0]
				redzoneTotals[team][pos] = []
				for td in row.findAll("td")[1:-1]:
					redzoneTotals[team][pos].append(int(td.text))
			else:
				player = parsePlayer(txt)
				redzone[team][player] = {
					"pos": pos,
					"looks": []
				}
				for td in row.findAll("td")[1:-1]:
					redzone[team][player]["looks"].append(int(td.text))

	snaps = {}
	for team in SNAP_LINKS:
		#continue
		url = f"https://www.footballguys.com/stats/snap-counts/teams?team={team.upper()}&year={year}"
		time.sleep(0.2)
		os.system(f"curl -k \"{url}\" -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")

		snaps[team] = {}
		rows = soup.find("div", id="stats_snapcounts_data").findAll("tr")
		pos = "qb"
		for row in rows:
			txt = row.find("td").text.lower().strip()

			pos = row.findPrevious("thead").find("th").text.strip().lower().split(" ")[0].replace("running", "rb").replace("wide", "wr").replace("tight", "te")
			if "defensive" in pos:
				break

			if pos in ["rb", "wr", "te"]:
				player = parsePlayer(txt)
				snaps[team][player] = {
					"pos": pos,
					"tot": [],
					"pct": []
				}
				for td in row.findAll("td")[1:-1]:
					if not td.find("div") or not td.find("div").text:
						snaps[team][player]["tot"].append(0)
						snaps[team][player]["pct"].append("0")
					else:
						tot = int(td.find("div").text)
						snaps[team][player]["tot"].append(tot)
						snaps[team][player]["pct"].append(td.find("b").text)

	targets = {}
	teamTargets = {}
	#for team in ["ari"]:
	for team in SNAP_LINKS:
		url = f"https://www.footballguys.com/stats/targets/teams?team={team.upper()}&year={year}"
		time.sleep(0.2)
		os.system(f"curl -k \"{url}\" -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")

		targets[team] = {}
		teamTargets[team] = {}
		rows = soup.find("div", id="stats_targets_data").findAll("tr")[1:][::-1]
		pos = "qb"
		for row in rows:
			txt = row.find("td").text.lower().strip()

			if "totals" in txt:
				pos = txt.split(" ")[0]
				teamTargets[team][pos] = []
				for td in row.findAll("td")[1:-1]:
					teamTargets[team][pos].append(int(td.text))
			else:
				player = parsePlayer(txt)
				targets[team][player] = {
					"pos": pos,
					"tot": []
				}
				for td in row.findAll("td")[1:-1]:
					targets[team][player]["tot"].append(int(td.text))

	with open(f"static/nfl/snaps.json", "w") as fh:
		json.dump(snaps, fh, indent=4)

	with open(f"static/nfl/targets.json", "w") as fh:
		json.dump(targets, fh, indent=4)

	with open(f"static/nfl/teamTargets.json", "w") as fh:
		json.dump(teamTargets, fh, indent=4)

	with open(f"static/nfl/redzone.json", "w") as fh:
		json.dump(redzone, fh, indent=4)

	with open(f"static/nfl/redzoneTotals.json", "w") as fh:
		json.dump(redzoneTotals, fh, indent=4)

def calculatePoints(stats):
	pts = 0
	pts += 0.5 * int(stats.get("rec", 0))
	pts += 0.1 * int(stats.get("rec_yd", 0))
	pts += 0.1 * int(stats.get("rush_yd", 0))
	pts += 6 * int(stats.get("rec_td", 0))
	pts += 6 * int(stats.get("rush_td", 0))
	pts += -2 * int(stats.get("fumbles_lost", 0))
	return round(pts, 1)

def writeTrends():
	with open(f"static/nfl/snaps.json") as fh:
		snaps = json.load(fh)

	with open(f"static/nfl/redzone.json") as fh:
		redzone = json.load(fh)

	with open(f"static/nfl/redzoneTotals.json") as fh:
		redzoneTotals = json.load(fh)

	with open(f"static/nfl/targets.json") as fh:
		targets = json.load(fh)

	with open(f"static/nfl/teamTargets.json") as fh:
		teamTargets = json.load(fh)

	with open(f"static/nfl/stats.json") as fh:
		stats = json.load(fh)

	week = max(len(redzoneTotals["ari"]["rb"]), len(redzoneTotals["atl"]["rb"]))
	for pos in ["rb", "wr/te"]:
		data = []
		table = []
		for team in snaps:
			for player in snaps[team]:

				if player in ["khalil herbert", "cam akers"]:
					continue

				if pos == "rb" and snaps[team][player]["pos"] != "rb":
					continue
				elif pos == "wr/te" and snaps[team][player]["pos"] == "rb":
					continue

				wkPts = pts = gamesPlayed = 0
				playerConverted = player.replace("ken walker", "kenneth walker")
				for wk in stats:
					for game in stats[wk]:
						if team not in game:
							continue
						if playerConverted in stats[wk][game]:
							p = calculatePoints(stats[wk][game][playerConverted])
							gamesPlayed += 1
							if wk == str(week):
								wkPts = p
							pts += p

				if gamesPlayed:
					pts = round(pts / gamesPlayed, 1)

				sznSnap = []
				rzShare = []
				tgtShare = []
				wk = 0
				for snapTot, snapPct in zip(snaps[team][player]["tot"], snaps[team][player]["pct"]):
					if snapTot:
						sznSnap.append(int(snapPct[:-1]))
						try:
							rzShare.append(redzone[team][player]["looks"][wk])
						except:
							pass
						try:
							tgtShare.append(targets[team][player]["tot"][wk])
						except:
							pass
					wk += 1

				if not sznSnap:
					sznSnap = 0
					continue
				else:
					sznSnap = round(sum(sznSnap) / len(sznSnap))
				try:
					if snaps[team][player]["tot"][-1]:
						if pos == "wr/te":
							totRZ = redzoneTotals[team]["te"][-1] + redzoneTotals[team]["wr"][-1]
						else:
							totRZ = redzoneTotals[team][pos][-1]
						if not totRZ:
							wkRzShare = 0
						else:
							wkRzShare = round(rzShare[-1] * 100 / totRZ)
					if pos == "rb":
						totRZ = 0
						for snapTot, tot in zip(snaps[team][player]["tot"], redzoneTotals[team][pos]):
							if snapTot:
								totRZ += tot
					else:
						totRZ = 0
						i = 0
						for snapTot, tot in zip(snaps[team][player]["tot"], redzoneTotals[team]["wr"]):
							if snapTot:
								totRZ += tot + redzoneTotals[team]["te"][i]
							i += 1

					if pos != "rb" and sum(rzShare) < 10:
						continue
					rzShare = round(sum(rzShare) * 100 / totRZ)
				except:
					rzShare = 0
					wkRzShare = 0
				try:
					if snaps[team][player]["tot"][-1]:
						if pos == "rb":
							tot = teamTargets[team][pos][-1]
						else:
							tot = teamTargets[team]["te"][-1] + teamTargets[team]["wr"][-1]
						if not tot:
							wkTgtShare = 0
						else:
							wkTgtShare = round(tgtShare[-1] * 100 / tot)
					if pos == "rb":
						tot = 0
						for snapTot, t in zip(snaps[team][player]["tot"], teamTargets[team][pos]):
							if snapTot:
								tot += t
					else:
						tot = 0
						i = 0
						for snapTot, t in zip(snaps[team][player]["tot"], teamTargets[team]["wr"]):
							if snapTot:
								tot += t + teamTargets[team]["te"][i]
							i += 1
					tgtShare = round(sum(tgtShare) * 100 / tot)
				except:
					tgtShare = "0"
					wkTgtShare = "0"

				wkSnap = snaps[team][player]["pct"][-1]
				if wkSnap == "0%" or wkSnap == "0":
					wkRzShare = "-"
					wkTgtShare = "-"
				arr = [team.upper(), player.title(), pts, wkPts, f"{sznSnap}%", wkSnap, f"{rzShare}%", f"{wkRzShare}%", f"{tgtShare}%", f"{wkTgtShare}%"]
				if pos == "rb":
					data.append((team, wkPts*-1, pts*-1, arr))
				else:
					data.append((rzShare*-1, int(str(wkRzShare).replace("-", "0"))*-1, arr))

		posHdr = "RB" if pos == "rb" else "WR/TE"
		hdrs = ["Team", "Player", "AVG PTS", f"WK{week} PTS", "SZN Snap %", f"WK{week} Snap %", f"{posHdr} RZ Look Share", f"WK{week} {posHdr} RZ Share", f"{posHdr} Target Share", f"WK{week} {posHdr} Target Share"]
		tableHdrs = ["team", "player", "pts", "lastPts", "snap", "lastSnap", "rz", "lastRz", "tgt", "lastTgt"]
		csv = "\t".join(hdrs)+"\n"
		reddit = "#ARI\n"+"|".join(hdrs)+"\n"
		reddit += "|".join([":--"]*len(hdrs))+"\n"
		team = data[0][0]
		table = []
		for idx, row in enumerate(sorted(data)):
			if pos == "rb" and team != row[-1][0].lower():
				csv += "\t".join(["-"]*len(hdrs))+"\n"
				#reddit += "|".join(["-"]*len(hdrs))+"\n"
				reddit += "\n#"+row[-1][0]+"\n"+"|".join(hdrs)+"\n"
				reddit += "|".join([":--"]*len(hdrs))+"\n"
				team = row[-1][0].lower()

			csv += "\t".join([str(x) for x in row[-1]])+"\n"
			table.append({hdr: val for hdr, val in zip(tableHdrs, row[-1])})


			if pos == "rb" or idx < 40:
				reddit += "|".join([str(x) for x in row[-1]])+"\n"

		with open(f"static/nfl/{pos.replace('/', '')}Trends.csv", "w") as fh:
			fh.write(csv)
		with open(f"static/nfl/{pos.replace('/', '')}Trends.reddit", "w") as fh:
			fh.write(reddit)
		with open(f"static/nfl/{pos.replace('/', '')}Trends.json", "w") as fh:
			json.dump(table, fh, indent=4)

def writeRosters():
	outfile = "out"

	teams = []
	path = "static/nfl/espnTeams.json"
	if os.path.exists(path):
		with open(path) as fh:
			teams = json.load(fh)
	else:
		url = "https://www.espn.com/nfl/teams"
		os.system(f"curl {url} -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for div in soup.findAll("div", class_="TeamLinks__Links"):
			team = div.findAll("a")[2].get("href").split("/")[-2]
			if team == "wsh":
				team = "was"
			teams.append(team)

		with open(path, "w") as fh:
			json.dump(teams, fh, indent=4)

	roster = {}
	playerIds = {}
	for team in teams:
		url = f"https://www.espn.com/nfl/team/roster/_/name/{team}/"
		if team == "wsh":
			team = "was"
		time.sleep(0.2)
		os.system(f"curl {url} -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")
		roster[team] = {}
		playerIds[team] = {}

		for table in soup.findAll("table"):
			for row in table.findAll("tr")[1:]:
				nameLink = row.findAll("td")[1].find("a").get("href").split("/")
				fullName = parsePlayer(nameLink[-1].replace("-", " "))
				playerId = int(nameLink[-2])
				playerIds[team][fullName] = playerId
				roster[team][fullName] = row.findAll("td")[2].text.strip()
				if fullName == "taysom hill":
					roster[team][fullName] = "TE"

	with open(f"static/nfl/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

	with open(f"static/nfl/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def writeSchedule(week):
	url = f"https://www.espn.com/nfl/schedule/_/week/{week}/year/2024/seasontype/2"
	outfile = "outnfl"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"static/nfl/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"static/nfl/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"static/nfl/scores.json") as fh:
		scores = json.load(fh)

	schedule[week] = []
	for table in soup.findAll("div", class_="ResponsiveTable"):
		if week not in boxscores:
			boxscores[week] = {}
		if week not in scores:
			scores[week] = {}

		seen = {}
		for row in table.findAll("tr")[1:]:
			tds = row.findAll("td")
			try:
				awayTeam = tds[0].findAll("a")[-1].get("href").split("/")[-2].replace("wsh", "was")
				homeTeam = tds[1].findAll("a")[-1].get("href").split("/")[-2].replace("wsh", "was")
			except:
				continue

			boxscore = tds[2].find("a").get("href").split("/")[-2]
			score = tds[2].find("a").text.strip()

			if ", " in score:
				scoreSp = score.split(", ")
				if awayTeam == scoreSp[0].split(" ")[0].lower():
					scores[week][awayTeam] = int(scoreSp[0].split(" ")[1])
					scores[week][homeTeam] = int(scoreSp[1].split(" ")[1])
				else:
					scores[week][awayTeam] = int(scoreSp[1].split(" ")[1])
					scores[week][homeTeam] = int(scoreSp[0].split(" ")[1])

			boxscores[week][f"{awayTeam} @ {homeTeam}"] = boxscore
			schedule[week].append(f"{awayTeam} @ {homeTeam}")

	with open(f"static/nfl/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"static/nfl/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"static/nfl/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("--schedule", action="store_true", help="Schedule")
	parser.add_argument("--totals", action="store_true", help="Totals")
	parser.add_argument("--redzone", action="store_true", help="Redzone")
	parser.add_argument("--trends", action="store_true", help="Trends")
	parser.add_argument("--roster", action="store_true")
	parser.add_argument("-s", "--stats", action="store_true", help="Stats")
	parser.add_argument("-w", "--week", help="Week")

	args = parser.parse_args()

	if args.totals:
		writeTotals()

	if args.redzone:
		writeRedzone()

	if args.trends:
		writeTrends()

	if args.roster:
		writeRosters()

	if not args.week:
		print("need week")
		exit()

	week = args.week

	if args.schedule:
		writeSchedule(week)
	if args.stats:
		writeStats(week)

	if args.update:
		writeSchedule(week)
		writeStats(week)