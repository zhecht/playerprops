#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime
from datetime import timedelta

import argparse
import glob
import json
import math
import operator
import os
import subprocess
import re
import time

ncaabprops_blueprint = Blueprint('ncaabprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def teamTotals(today, schedule):
	with open(f"{prefix}static/ncaabreference/scores.json") as fh:
		scores = json.load(fh)
	totals = {}
	for date in scores:
		games = schedule[date]
		for team in scores[date]:
			opp = ""
			for game in games:
				if team in game.split(" @ "):
					opp = game.replace(team, "").replace(" @ ", "")
			if team not in totals:
				totals[team] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			if opp not in totals:
				totals[opp] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			totals[team]["games"] += 1
			totals[team]["ppg"] += scores[date][team]
			totals[team]["ppga"] += scores[date][opp]
			totals[team]["ttOvers"].append(str(scores[date][team]))
			totals[team]["overs"].append(str(scores[date][team] + scores[date][opp]))

	out = "team|ppg|ppga|overs|overs avg|ttOvers|TT avg\n"
	out += ":--|:--|:--|:--|:--|:--|:--\n"
	for game in schedule[today]:
		away, home = map(str, game.split(" @ "))
		ppg = round(totals[away]["ppg"] / totals[away]["games"], 1)
		ppga = round(totals[away]["ppga"] / totals[away]["games"], 1)
		overs = ",".join(totals[away]["overs"])
		oversAvg = round(sum([int(x) for x in totals[away]["overs"]]) / len(totals[away]["overs"]), 1)
		ttOvers = ",".join(totals[away]["ttOvers"])
		ttOversAvg = round(sum([int(x) for x in totals[away]["ttOvers"]]) / len(totals[away]["ttOvers"]), 1)
		out += f"{away}|{ppg}|{ppga}|{overs}|{oversAvg}|{ttOvers}|{ttOversAvg}\n"
		ppg = round(totals[home]["ppg"] / totals[home]["games"], 1)
		ppga = round(totals[home]["ppga"] / totals[home]["games"], 1)
		overs = ",".join(totals[home]["overs"])
		oversAvg = round(sum([int(x) for x in totals[home]["overs"]]) / len(totals[home]["overs"]), 1)
		ttOvers = ",".join(totals[home]["ttOvers"])
		ttOversAvg = round(sum([int(x) for x in totals[home]["ttOvers"]]) / len(totals[home]["ttOvers"]), 1)
		out += f"{home}|{ppg}|{ppga}|{overs}|{oversAvg}|{ttOvers}|{ttOversAvg}\n"
		out += "-|-|-|-|-|-|-\n"

	with open("out2", "w") as fh:
		fh.write(out)

def customPropData(propData):
	pass

def getOppOvers(schedule, roster):
	overs = {}
	for team in roster:
		files = sorted(glob.glob(f"{prefix}static/ncaabreference/{team}/*-*-*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
		for file in files:
			chkDate = file.split("/")[-1].replace(".json","")
			opp = ""
			for game in schedule[chkDate]:
				if team in game.split(" @ "):
					opp = [t for t in game.split(" @ ") if t != team][0]
			if opp not in overs:
				overs[opp] = {}

			with open(file) as fh:
				gameStats = json.load(fh)
			for player in gameStats:
				if player not in roster[team] or gameStats[player].get("min", 0) < 25:
					continue

				pos = roster[team][player]
				if pos not in overs[opp]:
					overs[opp][pos] = {}
				for prop in ["pts", "ast", "reb", "pts+reb+ast", "3ptm"]:
					if prop not in overs[opp][pos]:
						overs[opp][pos][prop] = []
					if "+" in prop or prop in gameStats[player]:
						val = 0.0
						if "+" in prop:
							for p in prop.split("+"):
								val += gameStats[player][p]
						else:
							val = gameStats[player][prop]
						val = val / gameStats[player]["min"]
						overs[opp][pos][prop].append(val)
	return overs

@ncaabprops_blueprint.route('/getNCAABProps')
def getProps_route():
	if request.args.get("teams") or request.args.get("date"):
		teams = ""
		if request.args.get("teams"):
			teams = request.args.get("teams").lower().split(",")
		props = getPropData(date=request.args.get("date"), teams=teams)
	elif request.args.get("prop"):
		with open(f"{prefix}static/betting/ncaab_{request.args.get('prop')}.json") as fh:
			props = json.load(fh)
	else:
		with open(f"{prefix}static/betting/ncaab.json") as fh:
			props = json.load(fh)
	return jsonify(props)

def writeStaticProps():
	props = getPropData()
	writeCsvs(props)

	with open(f"{prefix}static/betting/ncaab.json", "w") as fh:
		json.dump(props, fh, indent=4)
	for prop in ["pts", "ast", "reb", "pts+reb+ast", "3ptm"]:
		filteredProps = [p for p in props if p["propType"] == prop]
		with open(f"{prefix}static/betting/ncaab_{prop}.json", "w") as fh:
			json.dump(filteredProps, fh, indent=4)

def getPropData(teams = "", date = None):

	if not date:
		date = datetime.now()
		date = str(date)[:10]

	with open(f"{prefix}static/ncaabprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/ncaabreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/ncaabreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/ncaabreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/ncaabreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/ncaabreference/teams.json") as fh:
		teamIds = json.load(fh)
	with open(f"{prefix}static/ncaabreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/ncaabprops/lines/{date}.json") as fh:
		gameLines = json.load(fh)

	#propData = customPropData(propData)
	#teamTotals(date, schedule)

	oppOvers = getOppOvers(schedule, roster)

	props = []
	for game in propData:
		for propName in propData[game]:
			name = propName

			team = opp = ""
			gameSp = game.split(" @ ")
			team1, team2 = gameSp[0], gameSp[1]
			if team1 not in stats:
				print(team1)
				continue
			if team2 not in stats:
				print(team2)
				continue

			if name in stats[team1]:
				team = team1
				opp = team2
			elif name in stats[team2]:
				team = team2
				opp = team1
			else:
				print(game, name)
				continue

			if teams and team not in teams:
				continue

			with open(f"{prefix}static/ncaabreference/{team}/lastYearStats.json") as fh:
				lastYearStats = json.load(fh)

			avgMin = 0
			if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
				avgMin = int(stats[team][name]["min"] / stats[team][name]["gamesPlayed"])
			for prop in propData[game][propName]:
				if prop == "pts+reb+ast":
					continue
				line = propData[game][propName][prop]["line"]
				avg = "-"

				if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
					val = 0
					if "+" in prop:
						for p in prop.split("+"):
							val += stats[team][name][p]
					elif prop in stats[team][name]:
						val = stats[team][name][prop]
					avg = round(val / stats[team][name]["gamesPlayed"], 1)
				# get best odds
				overOdds = propData[game][propName][prop]["over"]
				underOdds = propData[game][propName][prop]["under"]

				lastAvg = lastAvgMin = 0
				diff = diffAvg = 0
				if avg != "-" and line:
					diffAvg = round((avg / float(line) - 1), 2)
				if lastAvg and line:
					diff = round((lastAvg / float(line) - 1), 2)

				totalOverPerMin = totalOver = totalOverLast5 = totalGames = 0
				last5 = []
				winLossSplits = [[],[]]
				awayHomeSplits = [[],[]]
				hit = False
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/ncaabreference/{team}/*-*-*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
					for file in files:
						chkDate = file.split("/")[-1].replace(".json","")
						with open(file) as fh:
							gameStats = json.load(fh)
						if name in gameStats:
							minutes = gameStats[name].get("min", 0)
							if minutes > 0:
								totalGames += 1
								val = 0.0
								if "+" in prop:
									for p in prop.split("+"):
										val += gameStats[name][p]
								else:
									val = gameStats[name][prop]

								pastOpp = ""
								teamIsAway = False
								for g in schedule[chkDate]:
									gameSp = g.split(" @ ")
									if team in gameSp:
										if team == gameSp[0]:
											teamIsAway = True
											pastOpp = gameSp[1]
										else:
											pastOpp = gameSp[0]
										break

								if val > float(line):
									if chkDate == date:
										hit = True

								if len(last5) < 10:
									v = str(int(val))
									if chkDate == date:
										v = f"'{v}'"
										last5.append(v)
										continue
									last5.append(v)

								teamScore = scores[chkDate][team]
								oppScore = scores[chkDate][pastOpp]

								if teamScore > oppScore:
									winLossSplits[0].append(val)
								elif teamScore < oppScore:
									winLossSplits[1].append(val)

								if teamIsAway:
									awayHomeSplits[0].append(val)
								else:
									awayHomeSplits[1].append(val)

								valPerMin = float(val / minutes)
								linePerMin = float(line) / avgMin
								#if valPerMin > linePerMin:
								if val > float(line):
									totalOver += 1
									if len(last5) <= 5:
										totalOverLast5 += 1
				if totalGames:
					totalOver = round((totalOver / totalGames) * 100)
					last5Size = len(last5) if len(last5) < 5 else 5
					totalOverLast5 = round((totalOverLast5 / last5Size) * 100)

				lastTotalOver = lastTotalGames = 0
				if line and avgMin and name in lastYearStats and lastYearStats[name]:
					for dt in lastYearStats[name]:
						minutes = lastYearStats[name][dt]["min"]
						if minutes > 0:
							lastTotalGames += 1
							if "+" in prop:
								val = 0.0
								for p in prop.split("+"):
									val += lastYearStats[name][dt][p]
							else:
								val = lastYearStats[name][dt][prop]
							valPerMin = float(val / minutes)
							linePerMin = float(line) / avgMin
							if valPerMin > linePerMin:
								lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				pos = ""
				if team in roster and name in roster[team]:
					pos = roster[team][name]

				oppOver = 0
				overPos = pos
				if overPos == "C" and overPos not in oppOvers[opp]:
					overPos = "F"

				try:
					overList = oppOvers[opp][overPos][prop]
				except:
					continue
				linePerMin = 0
				if avgMin:
					linePerMin = line / avgMin
				if overList:
					oppOver = round(len([x for x in overList if x > linePerMin]) * 100 / len(overList))

				winSplitAvg = lossSplitAvg = 0
				if len(winLossSplits[0]):
					winSplitAvg = round(sum(winLossSplits[0]) / len(winLossSplits[0]),2)
				if len(winLossSplits[1]):
					lossSplitAvg = round(sum(winLossSplits[1]) / len(winLossSplits[1]),2)
				winLossSplits = f"{winSplitAvg} - {lossSplitAvg}"

				awaySplitAvg = homeSplitAvg = 0
				if len(awayHomeSplits[0]):
					awaySplitAvg = round(sum(awayHomeSplits[0]) / len(awayHomeSplits[0]),2)
				if len(awayHomeSplits[1]):
					homeSplitAvg = round(sum(awayHomeSplits[1]) / len(awayHomeSplits[1]),2)
				awayHomeSplits = f"{awaySplitAvg} - {homeSplitAvg}"

				gameLine = 0
				if game in gameLines and "moneyline" in gameLines[game]:
					gameOdds = gameLines[game]["moneyline"]["odds"].split(",")
					if team == game.split(" @ ")[0]:
						gameLine = gameOdds[0]
					else:
						gameLine = gameOdds[1]

				props.append({
					"player": name.title(),
					"team": team.upper(),
					"display": teamIds[team]["display"].lower().replace(" ", "-"),
					"pos": pos,
					"gameLine": gameLine,
					"awayHome": "A" if team == game.split(" @ ")[0] else "H",
					"awayHomeSplits": awayHomeSplits,
					"winLossSplits": winLossSplits,
					"opponent": opp.upper(),
					"propType": prop,
					"line": line or "-",
					"avg": avg,
					"hit": hit,
					"avgMin": avgMin,
					"oppOver": oppOver,
					"totalOver": totalOver,
					"lastTotalOver": lastTotalOver,
					"totalOverLast5": totalOverLast5,
					"last5": ",".join(last5),
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	return props

def updateTeamStats(date):
	with open(f"{prefix}static/ncaabprops/lines/{date}.json") as fh:
		games = json.load(fh)
	with open(f"{prefix}static/ncaabreference/totals.json") as fh:
		stats = json.load(fh)

	teams = []
	for game in games:
		for team in game.split(" @ "):
			if team in stats:
				teams.append(team)

	call(["python", f"{prefix}controllers/ncaabreference.py", "--teams", f"{','.join(teams)}"])


def writeCsvs(props):
	csvs = {}
	splitProps = {"full": []}
	headers = "\t".join(["NAME","POS","ML","A/H","TEAM","OPP","PROP","LINE","SZN AVG","W-L Splits","A-H Splits","% OVER","L5 % OVER","LAST 7 GAMES ➡️","OVER", "UNDER"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

	for row in props:
		if row["propType"] not in splitProps:
			splitProps[row["propType"]] = []
		splitProps[row["propType"]].append(row)
		splitProps["full"].append(row)

	# add full rows
	csvs["full_name"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"], -k["totalOver"], -k["totalOverLast5"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		gameLine = row["gameLine"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		if int(gameLine) > 0:
			gameLine = "'"+gameLine
		try:
			csvs["full_name"] += "\n" + "\t".join([str(x) for x in [row["player"], row["pos"], gameLine, row["awayHome"], row["team"], row["opponent"].upper(), row["propType"], row["line"], row["avg"], row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], overOdds, underOdds]])
		except:
			pass

	csvs["full_hit"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["totalOver"], k["totalOverLast5"]), reverse=True)
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		gameLine = row["gameLine"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		if int(gameLine) > 0:
			gameLine = "'"+gameLine
		try:
			csvs["full_hit"] += "\n" + "\t".join([str(x) for x in [row["player"], row["pos"], gameLine, row["awayHome"], row["team"], row["opponent"].upper(), row["propType"], str(row["line"]), str(row["avg"]), row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], overOdds, underOdds]])
		except:
			pass

	for prop in csvs:
		if prop == "full":
			continue
		with open(f"{prefix}static/ncaabprops/csvs/{prop}.csv", "w") as fh:
			fh.write(csvs[prop])

def writeGameLines(date):
	lines = {}
	if os.path.exists(f"{prefix}static/ncaabprops/lines/{date}.json"):
		with open(f"{prefix}static/ncaabprops/lines/{date}.json") as fh:
			lines = json.load(fh)

	time.sleep(0.2)
	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/92483?format=json"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	events = {}
	lines = {}
	displayTeams = {}
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		displayTeams[event["teamName1"].lower()] = event["teamShortName1"].lower()
		displayTeams[event["teamName2"].lower()] = event["teamShortName2"].lower()
		game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if game not in lines:
			lines[game] = {}
		events[event["eventId"]] = game

	for catRow in data["eventGroup"]["offerCategories"]:
		if catRow["name"].lower() != "game lines":
			continue
		for cRow in catRow["offerSubcategoryDescriptors"]:
			if cRow["name"].lower() != "game":
				continue
			for offerRow in cRow["offerSubcategory"]["offers"]:
				for row in offerRow:
					game = events[row["eventId"]]
					try:
						gameType = row["label"].lower().split(" ")[-1]
					except:
						continue

					switchOdds = False
					team1 = ""
					if gameType != "total":
						outcomeTeam1 = row["outcomes"][0]["label"].lower()
						team1 = convertDKTeam(displayTeams[outcomeTeam1])
						if team1 != game.split(" @ ")[0]:
							switchOdds = True

					odds = [row["outcomes"][0]["oddsAmerican"], row["outcomes"][1]["oddsAmerican"]]
					if switchOdds:
						odds[0], odds[1] = odds[1], odds[0]

					line = row["outcomes"][0].get("line", 0)
					lines[game][gameType] = {
						"line": line,
						"odds": ",".join(odds)
					}

	with open(f"{prefix}static/ncaabprops/lines/{date}.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def convertDKTeam(team):
	if team == "tx a&m-cc":
		return "amcc"
	elif team == "az st":
		return "asu"
	elif team == "bsu":
		return "bois"
	elif team == "cal poly":
		return "cp"
	elif team == "chatt":
		return "utc"
	elif team == "charl":
		return "cofc"
	elif team == "chi st":
		return "chst"
	elif team == "cle st":
		return "clev"
	elif team == "la salle":
		return "las"
	elif team == "fair d":
		return "fdu"
	elif team == "ford":
		return "for"
	elif team == "furm":
		return "fur"
	elif team == "michigan":
		return "mich"
	elif team == "minnesota":
		return "minn"
	elif team == "jville st":
		return "jvst"
	elif team == "merr":
		return "mrmk"
	elif team == "mizz":
		return "miz"
	elif team == "miss st":
		return "mvsu"
	elif team == "nc cent":
		return "nccu"
	elif team == "nw":
		return "nu"
	elif team == "or st":
		return "orst"
	elif team == "ind":
		return "iu"
	elif team == "lasalle":
		return "las"
	elif team == "lu":
		return "lib"
	elif team == "loy chi":
		return "luc"
	elif team == "kennst":
		return "kenn"
	elif team == "g'town":
		return "gtwn"
	elif team == "hofst":
		return "hof"
	elif team == "nc st":
		return "ncst"
	elif team == "ut-mar":
		return "utm"
	elif team == "ma-low":
		return "uml"
	elif team == "um-mil":
		return "milw"
	elif team == "mary":
		return "md"
	elif team == "mia fl":
		return "mia"
	elif team == "no ala":
		return "una"
	elif team == "no co":
		return "unco"
	elif team == "ok st":
		return "okst"
	elif team == "pacif":
		return "pac"
	elif team == "prvw":
		return "pv"
	elif team == "rider":
		return "rid"
	elif team == "s clara":
		return "scu"
	elif team == "tulsa":
		return "tlsa"
	elif team == "valpo":
		return "val"
	elif team == "drake":
		return "drke"
	elif team == "sam hou":
		return "shsu"
	elif team == "san fran":
		return "sf"
	elif team == "scar":
		return "sc"
	elif team == "st. joe":
		return "joes"
	elif team == "tarst":
		return "tar"
	elif team == "tntech":
		return "tntc"
	elif team == "toledo":
		return "tol"
	elif team == "towson":
		return "tow"
	elif team == "tulane":
		return "tuln"
	elif team == "tamu":
		return "ta&m"
	elif team == "uc riv":
		return "ucr"
	elif team == "uc dav":
		return "ucd"
	elif team == "uc-bap":
		return "cbu"
	elif team == "ul-laf":
		return "laf"
	elif team == "umass":
		return "mass"
	elif team == "ut val":
		return "uvu"
	elif team == "uw-gb" or team == "green bay":
		return "gb"
	elif team == "uconn":
		return "conn"
	elif team == "ust":
		return "stmn"
	elif team == "wis":
		return "wisc"
	elif team == "woff":
		return "wof"
	elif team == "wich st":
		return "wich"
	return team.replace(" ", "").replace("'", "")

def writeProps(date):
	ids = {
		"pts": [1215, 12488],
		"reb": [1216, 12492],
		"ast": [1217, 12495],
		"pts+reb+ast": [583, 5001],
		"3ptm": [1218, 12497]
	}

	props = {}
	if os.path.exists(f"{prefix}static/ncaabprops/dates/{date}.json"):
		with open(f"{prefix}static/ncaabprops/dates/{date}.json") as fh:
			props = json.load(fh)

	for prop in ids:
		time.sleep(0.4)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/92483/categories/{ids[prop][0]}/subcategories/{ids[prop][1]}?format=json"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
			startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=5)
			if startDt.day != int(date[-2:]):
				continue
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if game not in props:
				props[game] = {}
			events[event["eventId"]] = game

		for catRow in data["eventGroup"]["offerCategories"]:
			if catRow["offerCategoryId"] != ids[prop][0]:
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["subcategoryId"] != ids[prop][1]:
					continue
				for offerRow in cRow["offerSubcategory"]["offers"]:
					for row in offerRow:
						if row["eventId"] not in events:
							continue
						game = events[row["eventId"]]
						player = row["label"].lower().replace(".", "").replace("'", "").replace(" "+cRow["offerSubcategory"]["name"].lower(), "").replace(" points + assists + rebounds", "").replace(" three pointers made", "").replace("-", " ")
						odds = ["",""]
						line = row["outcomes"][0]["line"]
						for outcome in row["outcomes"]:

							if outcome["label"].lower() == "over":
								odds[0] = outcome["oddsAmerican"]
							else:
								odds[1] = outcome["oddsAmerican"]

						if player not in props[game]:
							props[game][player] = {}
						if prop not in props[game][player]:
							props[game][player][prop] = {}
						props[game][player][prop] = {
							"line": line,
							"over": odds[0],
							"under": odds[1]
						}

	with open(f"{prefix}static/ncaabprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(props):
	pass

def writeTranslations(date):
	with open(f"{prefix}static/ncaabreference/translations.json") as fh:
		translations = json.load(fh)

	with open(f"{prefix}static/ncaabprops/{date}.json") as fh:
		props = json.load(fh)

	shortNames = translations.values()
	for idx, team in enumerate(props):
		if team not in shortNames:
			translations[idx] = team

	with open(f"{prefix}static/ncaabreference/translations.json", "w") as fh:
		json.dump(translations, fh, indent=4)

@ncaabprops_blueprint.route('/ncaabprops')
def props_route():
	teams = request.args.get("teams") or ""
	date = request.args.get("date") or ""
	prop = request.args.get("prop") or ""
	return render_template("ncaabprops.html", teams=teams, date=date, prop=prop)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("--zero", help="Zero CustomProp Odds", action="store_true")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	#writeTranslations(date)

	if args.cron:
		writeProps(date)
		writeGameLines(date)
		updateTeamStats(date)
		writeStaticProps()
	elif args.lines:
		writeGameLines(date)

	#updateTeamStats(date)