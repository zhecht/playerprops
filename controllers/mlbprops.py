#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime
from datetime import timedelta

from itertools import zip_longest
import argparse
import time
import glob
import json
import math
import operator
import os
import subprocess
import re

mlbprops_blueprint = Blueprint('mlbprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def convertDKTeam(team):
	if team == "cws":
		return "chw"
	elif team == "was":
		return "wsh"
	elif team == "sfg":
		return "sf"
	return team

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

def writeGameLines(date):
	lines = {}
	if os.path.exists(f"{prefix}static/mlbprops/lines/{date}.json"):
		with open(f"{prefix}static/mlbprops/lines/{date}.json") as fh:
			lines = json.load(fh)

	time.sleep(0.3)
	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/84240/categories/493/subcategories/4519?format=json"
	outfile = "outmlb"
	call(["curl", "-k", url, "-o", outfile])

	with open("outmlb") as fh:
		data = json.load(fh)

	events = {}
	lines = {}
	displayTeams = {}
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		displayTeams[event["teamName1"].lower()] = event.get("teamShortName1", "").lower()
		displayTeams[event["teamName2"].lower()] = event.get("teamShortName2", "").lower()
		if "teamShortName1" not in event:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		else:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
			continue
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
					try:
						game = events[row["eventId"]]
						gameType = row["label"].lower().split(" ")[-1]
					except:
						continue

					switchOdds = False
					team1 = ""
					if gameType != "total":
						outcomeTeam1 = row["outcomes"][0]["label"].lower()
						team1 = displayTeams[outcomeTeam1]
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

	with open(f"{prefix}static/mlbprops/lines/{date}.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def convertDKProp(mainCat, prop):
	if prop == "home runs":
		return "hr"
	elif prop == "total bases":
		return "tb"
	elif prop in ["hits"]:
		return "h"
	elif prop == "rbis":
		return "rbi"
	elif prop == "runs scored":
		return "r"
	elif prop == "earned runs":
		return "er"
	elif prop == "outs recorded":
		return "outs"
	elif prop == "hits + runs + rbis":
		return "h+r+rbi"
	elif prop == "strikeouts":
		if mainCat == "batter":
			return "so"
		return "k"
	elif prop == "walks":
		if mainCat == "batter":
			return "bb"
		return "bb_allowed"
	elif prop == "singles":
		return "1b"
	elif prop == "doubles":
		return "2b"
	elif prop == "to record a win":
		return "win"
	
	return "_".join(prop.split(" "))

def writeProps(date):

	props = {}
	if os.path.exists(f"{prefix}static/mlbprops/dates/{date}.json"):
		with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
			props = json.load(fh)

	mainCats = {
		"batter": 743,
		"pitcher": 1031 
	}

	for mainCat in mainCats:
		time.sleep(0.4)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/84240/categories/{mainCats[mainCat]}?format=json"
		outfile = "outmlb"
		call(["curl", "-k", url, "-o", outfile])

		with open("outmlb") as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
			startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=5)
			if startDt.day != int(date[-2:]):
				continue
				pass
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
				continue
			if game not in props:
				props[game] = {}
			events[event["eventId"]] = game

		subCats = {}
		for catRow in data["eventGroup"]["offerCategories"]:
			if catRow["offerCategoryId"] != mainCats[mainCat]:
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["name"].startswith("1st") or cRow["name"].startswith("H2H"):
					continue
				#print(mainCat, cRow["name"])
				prop = convertDKProp(mainCat, cRow["name"].lower())
				subCats[prop] = cRow["subcategoryId"]

		for prop in subCats:
			time.sleep(0.4)
			url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/84240/categories/{mainCats[mainCat]}/subcategories/{subCats[prop]}?format=json"
			outfile = "outmlb"
			#print(url)
			call(["curl", "-k", url, "-o", outfile])

			with open("outmlb") as fh:
				data = json.load(fh)

			for catRow in data["eventGroup"]["offerCategories"]:
				if "offerSubcategoryDescriptors" not in catRow:
					continue
				for cRow in catRow["offerSubcategoryDescriptors"]:
					if "offerSubcategory" not in cRow:
						continue
					for offerRow in cRow["offerSubcategory"]["offers"]:
						for row in offerRow:
							try:
								game = events[row["eventId"]]
							except:
								continue
							try:
								player = row["outcomes"][0]["participant"].lower().replace(".", "").replace("'", "").replace("-", " ")
							except:
								continue
							odds = ["+0","+0"]
							try:
								line = row["outcomes"][0]["line"]
							except:
								line = 0
							for outcome in row["outcomes"]:
								if outcome["label"].lower() == "over" or (prop == "win" and outcome["label"].lower() == "yes"):
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

	with open(f"{prefix}static/mlbprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def writeCsvs(props):
	csvs = {}
	splitProps = {"full": []}
	headerList = ["NAME","POS","TEAM","OPP","OPP RANK","OPP RANK VAL","PROP","LINE","LYR AVG","LYR % Over","LYR Matchup","# Matchups","OVER","UNDER"]
	headers = "\t".join(headerList)
	reddit = "|".join(headers.split("\t"))
	reddit += "\n"+"|".join([":--"]*len(headerList))

	for row in props:
		if row["prop"] not in splitProps:
			splitProps[row["prop"]] = []

		if row["overOdds"] == '-inf':
			continue

		splitProps[row["prop"]].append(row)
		splitProps["full"].append(row)

	for prop in splitProps:
		csvs[prop] = headers
		rows = sorted(splitProps[prop], key=lambda k: (k["lastYearTotalOver"]), reverse=True)
		for row in rows:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			avg = row["lastYearAvg"]
			if underOdds == '-inf':
				underOdds = 0
			if int(overOdds) > 0:
				overOdds = "'"+overOdds
			if int(underOdds) > 0:
				underOdds = "'"+underOdds
			#if avg >= row["line"]:
			#	avg = f"**{avg}**"
			csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], row["pos"], row["team"], row["opponent"], addNumSuffix(row["oppRank"]), row["oppRankVal"], row["prop"], row["line"], avg, f"{row['lastYearTotalOver']}%", f"{row['lastYearTeamMatchupOver']}%", f"{row['matchups']}", overOdds, underOdds]])

	# add full rows
	csvs["full"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		avg = row["lastYearAvg"]
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		#if avg >= row["line"]:
		#	avg = f"**{avg}**"
		csvs["full"] += "\n" + "\t".join([str(x) for x in [row["player"], row["pos"], row["team"], row["opponent"], addNumSuffix(row["oppRank"]), row["oppRankVal"], row["prop"], row["line"], avg, f"{row['lastYearTotalOver']}%", f"{row['lastYearTeamMatchupOver']}%", f"{row['matchups']}", overOdds, underOdds]])

	# add top 4 to reddit
	for prop in ["h", "h+r+rbi", "so", "k", "hits_allowed"]:
		if prop in splitProps:
			rows = sorted(splitProps[prop], key=lambda k: (k["lastYearTotalOver"]), reverse=True)
			for row in rows[:3]:
				overOdds = row["overOdds"]
				underOdds = row["underOdds"]
				avg = row["lastYearAvg"]
				if avg >= row["line"]:
					avg = f"**{avg}**"
				reddit += "\n" + "|".join([str(x) for x in [row["player"], row["pos"], row["team"], row["opponent"], addNumSuffix(row["oppRank"]), row["oppRankVal"], row["prop"], row["line"], avg, f"{row['lastYearTotalOver']}%", f"{row['lastYearTeamMatchupOver']}%", f"{row['matchups']}", overOdds, underOdds]])
			reddit += "\n"+"|".join(["-"]*len(headerList))

	with open(f"{prefix}static/mlbprops/csvs/reddit", "w") as fh:
		fh.write(reddit)

	for prop in csvs:
		with open(f"{prefix}static/mlbprops/csvs/{prop}.csv", "w") as fh:
			fh.write(csvs[prop])

def writeStaticProps():
	props = getPropData()

	writeCsvs(props)

	with open(f"{prefix}static/betting/mlb.json", "w") as fh:
		json.dump(props, fh, indent=4)
	for prop in ["k", "outs", "wins", "hits_allowed", "bb", "er"]:
		filteredProps = [p for p in props if p["prop"] == prop]
		with open(f"{prefix}static/betting/mlb_{prop}.json", "w") as fh:
			json.dump(filteredProps, fh, indent=4)

def convertProp(prop):
	if prop == "bb_allowed":
		return "bb"
	elif prop == "hits_allowed":
		return "h"
	return prop

def convertRankingsProp(prop):
	if prop == "k":
		return "so"
	elif prop == "so":
		return "k"
	elif prop in ["r", "rbi"]:
		return "er"
	elif prop == "er":
		return "r"
	elif prop == "bb":
		return "bb_allowed"
	elif prop == "bb_allowed":
		return "bb"
	elif prop == "hr_allowed":
		return "hr"
	elif prop == "hr":
		return "hr_allowed"
	elif prop == "hits_allowed":
		return "h"
	elif prop == "h":
		return "hits_allowed"
	elif prop == "h+r+rbi_allowed":
		return "h+r+rbi"
	elif prop == "h+r+rbi":
		return "h+r+rbi_allowed"
	return prop

def getPropData(date = None, playersArg = [], teams = "", pitchers=False):
	
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/baseballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/baseballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/baseballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/mlbprops/lines/{date}.json") as fh:
		gameLines = json.load(fh)
	with open(f"{prefix}static/mlbprops/lineups.json") as fh:
		lineups = json.load(fh)

	props = []
	for game in propData:
		awayTeam, homeTeam = map(str, game.split(" @ "))

		for player in propData[game]:

			if player in roster[awayTeam]:
				team = awayTeam
				opp = homeTeam
			else:
				team = homeTeam
				opp = awayTeam

			try:
				pos = roster[team][player]
			except:
				print(game, player)
				continue

			if teams and team not in teams:
				continue

			for propName in propData[game][player]:
				prop = convertProp(propName)
				lastYearAvg = lastYearTotalOver = gamesPlayed = battingNumber = 0
				hit = False

				try:
					battingNumber = lineups[team].index(player)+1
				except:
					pass

				line = propData[game][player][propName]["line"]
				overOdds = propData[game][player][propName]["over"]
				underOdds = propData[game][player][propName]["under"]

				if player in averages[team]:
					lastYrGamesPlayed = 0
					if player in averages[team]:
						lastYrGamesPlayed = averages[team][player].get("gamesPlayed", 0)
					for p in prop.split("+"):
						lastYearAvg += averages[team][player].get(p, 0)

					if lastYrGamesPlayed:
						lastYearAvg = round(lastYearAvg / lastYrGamesPlayed, 2)

					gamesPlayed = lastYrGamesPlayed

				prevMatchup = []
				lastTotalGames = 0
				if player in lastYearStats[team]:
					for d in lastYearStats[team][player]:
						lastTotalGames += 1
						val = 0
						for p in prop.split("+"):
							val += lastYearStats[team][player][d].get(p, 0)

						if val > line:
							lastYearTotalOver += 1

						if lastYearStats[team][player][d]["vs"] == opp:
							prevMatchup.append(val)

				if lastTotalGames:
					lastYearTotalOver = round(lastYearTotalOver * 100 / lastTotalGames)

				lastYearTeamMatchupOver = 0
				if prevMatchup:
					over = len([x for x in prevMatchup if x > line])
					lastYearTeamMatchupOver = round(over * 100 / len(prevMatchup))

				lastAll = []

				oppRank = ""
				oppRankVal = ""
				rankingsProp = convertRankingsProp(propName)
				
				if rankingsProp in rankings[opp]:
					oppRankVal = str(rankings[opp][rankingsProp]["season"])
					oppRank = rankings[opp][rankingsProp]['rank']

				hitRateOdds = diff = 0
				if lastYearTotalOver != 100:
					hitRateOdds = int((100 * lastYearTotalOver) / (-100 + lastYearTotalOver))
					diff = -1 * (hitRateOdds - int(overOdds))

				props.append({
					"game": game,
					"player": player.title(),
					"team": team.upper(),
					"opponent": opp.upper(),
					"hit": hit,
					#"awayHomeSplits": awayHomeSplits,
					#"winLossSplits": winLossSplits,
					"battingNumber": battingNumber,
					"pos": pos,
					"prop": propName,
					"displayProp": prop,
					"gamesPlayed": gamesPlayed,
					"matchups": len(prevMatchup),
					"line": line or "-",
					"diff": diff,
					"hitRateOdds": hitRateOdds,
					"lastYearAvg": lastYearAvg,
					"lastYearTotalOver": lastYearTotalOver,
					"lastYearTeamMatchupOver": lastYearTeamMatchupOver,
					"lastAll": ",".join(lastAll),
					"oppRank": oppRank,
					"oppRankVal": oppRankVal,
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	return props

def writeLineups():
	url = f"https://www.rotowire.com/baseball/daily-lineups.php"
	outfile = "outmlb"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	lineups = {}
	for box in soup.findAll("div", class_="lineup"):
		if "is-tools" in box.get("class") or "is-ad" in box.get("class"):
			continue

		away = convertDKTeam(box.findAll("div", class_="lineup__abbr")[0].text.lower())
		home = convertDKTeam(box.findAll("div", class_="lineup__abbr")[1].text.lower())

		for idx, lineupList in enumerate(box.findAll("ul", class_="lineup__list")):
			team = away if idx == 0 else home
			status = "confirmed" if "is-green" in lineupList.find("div", class_="dot").get("class") else "expected"
			lineups[team] = []
			for li in lineupList.findAll("li")[2:]:
				try:
					player = " ".join(li.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
					lineups[team].append(player)
				except:
					pass

	with open(f"{prefix}static/mlbprops/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)

@mlbprops_blueprint.route('/getMLBProps')
def getProps_route():
	pitchers = False
	if request.args.get("pitchers"):
		pitchers = True
	if request.args.get("teams") or request.args.get("players") or request.args.get("date"):
		teams = ""
		if request.args.get("teams"):
			teams = request.args.get("teams").lower().split(",")
		players = ""
		if request.args.get("players"):
			players = request.args.get("players").lower().split(",")
		props = getPropData(date=request.args.get("date"), playersArg=players, teams=teams, pitchers=pitchers)
	elif request.args.get("prop"):
		with open(f"{prefix}static/betting/mlb_{request.args.get('prop')}.json") as fh:
			props = json.load(fh)
	else:
		with open(f"{prefix}static/betting/mlb.json") as fh:
			props = json.load(fh)
	return jsonify(props)

@mlbprops_blueprint.route('/mlbprops')
def props_route():
	prop = date = teams = players = ""
	if request.args.get("prop"):
		prop = request.args.get("prop").replace(" ", "+")

	if request.args.get("date"):
		date = request.args.get("date")
		if date == "yesterday":
			date = str(datetime.now() - timedelta(days=1))[:10]
		elif date == "today":
			date = str(datetime.now())[:10]
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("players"):
		players = request.args.get("players")

	# locks
	bets = []
	# singles
	bets.extend([])
	bets = ",".join(bets)
	return render_template("mlbprops.html", prop=prop, date=date, teams=teams, bets=bets, players=players)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("--lineups", help="Lineups", action="store_true")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.lineups:
		writeLineups()
	elif args.cron:
		writeLineups()
		writeProps(date)
		writeGameLines(date)
		writeStaticProps()

	writeStaticProps()