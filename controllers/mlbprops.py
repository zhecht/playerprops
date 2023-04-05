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
	outfile = "outmlb2"
	call(["curl", "-k", url, "-o", outfile])

	with open("outmlb2") as fh:
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
	elif prop == "stolen bases":
		return "sb"
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
		outfile = "outmlb2"
		call(["curl", "-k", url, "-o", outfile])

		with open("outmlb2") as fh:
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
			outfile = "outmlb2"
			#print(url)
			call(["curl", "-k", url, "-o", outfile])

			with open("outmlb2") as fh:
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
	headerList = ["NAME","POS","R/L","Batting #","TEAM","A/H","OPP","OPP RANK","OPP RANK VAL","PITCHER","THROWS","VS PITCHER","PROP","LINE","LAST ➡️","% OVER", "LYR AVG","LYR % OVER","LYR # MATCHUPS","LYR MATCHUPS","OVER","UNDER"]
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
		rows = sorted(splitProps[prop], key=lambda k: (k["careerTotalOver"]), reverse=True)
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
			csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], row["pos"], row["bats"], row["battingNumber"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), row["oppRankVal"], row["pitcher"], row["pitcherThrows"], row["againstPitcherStats"], row["prop"], row["line"], row["lastDisplay"], f"{row['totalOver']}%", avg, f"{row['lastYearTotalOver']}%", f"{row['matchups']}", f"{row['lastYearTeamMatchupOver']}%", overOdds, underOdds]])

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
		csvs["full"] += "\n" + "\t".join([str(x) for x in [row["player"], row["pos"], row["bats"], row["battingNumber"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), row["oppRankVal"], row["pitcher"], row["pitcherThrows"], row["againstPitcherStats"], row["prop"], row["line"], row["lastDisplay"], f"{row['totalOver']}%", avg, f"{row['lastYearTotalOver']}%", f"{row['matchups']}", f"{row['lastYearTeamMatchupOver']}%", overOdds, underOdds]])

	# add top 4 to reddit
	headerList = ["NAME","POS","Batting #","TEAM","A/H","OPP","OPP RANK","LYR OPP RANK","PROP","LINE","LAST ➡️","AVG","% OVER", "CAREER % OVER", "% OVER VS TEAM", "VS TEAM", "PITCHER", "VS PITCHER", "OVER","UNDER"]
	headers = "\t".join(headerList)
	reddit = "|".join(headers.split("\t"))
	reddit += "\n"+"|".join([":--"]*len(headerList))

	for prop in ["h", "h+r+rbi", "hr", "so"]:
		if prop in splitProps:
			rows = sorted(splitProps[prop], key=lambda k: (k["careerTotalOver"]), reverse=True)
			for row in [r for r in rows if int(str(r["battingNumber"]).replace('-', '10')) <= 5][:3]:
				overOdds = row["overOdds"]
				underOdds = row["underOdds"]
				avg = row["lastYearAvg"]
				reddit += "\n" + "|".join([str(x) for x in [row["player"], row["pos"], row["battingNumber"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"], row["avg"], f"{row['totalOver']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", row["pitcher"], row["againstPitcherStats"], overOdds, underOdds]])
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
	elif prop in ["r"]:
		return "er"
	elif prop == "rbi":
		return "opp_rbi"
	elif prop == "er":
		return "r"
	elif prop == "sb":
		return "opp_sb"
	elif prop == "tb":
		return "opp_tb"
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
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/baseballreference/bvp.json") as fh:
		bvp = json.load(fh)
	with open(f"{prefix}static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)
	with open(f"{prefix}static/baseballreference/pitching.json") as fh:
		pitching = json.load(fh)
	with open(f"{prefix}static/baseballreference/statsVsTeam.json") as fh:
		statsVsTeam = json.load(fh)
	with open(f"{prefix}static/mlbprops/lines/{date}.json") as fh:
		gameLines = json.load(fh)
	with open(f"{prefix}static/mlbprops/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/mlbprops/stats/2022.json") as fh:
		lastYearStats = json.load(fh)
	yearStats = {}
	for yr in os.listdir(f"{prefix}static/mlbprops/stats/"):
		with open(f"{prefix}static/mlbprops/stats/{yr}") as fh:
			s = json.load(fh)
		yearStats[yr[:4]] = s

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
				pitcher = pitcherThrows = awayHomeSplits = ""

				bats = leftOrRight[team].get(player, "")
				hip = bbip = hrip = kip = 0
				try:
					pitcher = lineups[opp]["pitching"]
					pitcherThrows = leftOrRight[opp][pitcher]
					hip = round(stats[opp][pitcher]["h_allowed"] / stats[opp][pitcher]["ip"], 2)

					hip = round(averages[opp][pitcher]["tot"]["h"] / averages[opp][pitcher]["tot"]["ip"], 2)
					hrip = round(averages[opp][pitcher]["tot"]["hr"] / averages[opp][pitcher]["tot"]["ip"], 2)
					kip = round(averages[opp][pitcher]["tot"]["k"] / averages[opp][pitcher]["tot"]["ip"], 2)
				except:
					pass

				if "P" in pos:
					try:
						hip = round(averages[team][player]["tot"]["h"] / averages[team][player]["tot"]["ip"], 2)
						bbip = round(averages[team][player]["tot"]["bb"] / averages[team][player]["tot"]["ip"], 2)
					except:
						pass

				try:
					battingNumber = lineups[team]["batting"].index(player)+1
				except:
					battingNumber = "-"

				line = propData[game][player][propName]["line"]
				overOdds = propData[game][player][propName]["over"]
				underOdds = propData[game][player][propName]["under"]

				lastYrGamesPlayed = 0
				if team in averages and player in averages[team] and "2022" in averages[team][player]:
					lastYrGamesPlayed = averages[team][player]["2022"].get("gamesPlayed", 0)
					for p in prop.split("+"):
						lastYearAvg += averages[team][player]["2022"].get(p, 0)

					if lastYrGamesPlayed:
						lastYearAvg = round(lastYearAvg / lastYrGamesPlayed, 2)

				prevMatchup = []
				lastTotalGames = careerTotalGames = careerTotalOver = careerAvg = againstTeamTotalOver = 0
				lastYrAwayHomeSplits = [[], []]
				lastYrLast20 = []
				againstTeamLastYearStats = {"ab": 0, "h": 0, "hr": 0, "rbi": 0, "bb": 0, "so": 0}
				againstTeamStats = {}

				try:
					againstTeamStats = statsVsTeam[team][opp][player]
					over = 0
					for p in prop.split("+"):
						over += againstTeamStats[p]
					againstTeamTotalOver = round(againstTeamStats[prop+"Overs"][str(math.ceil(line))] * 100 / againstTeamStats["gamesPlayed"])
				except:
					pass

				if player in averages[team]:
					for yr in averages[team][player]:
						if yr == "tot":
							continue
						overLine = math.ceil(line)
						try:
							over = averages[team][player][yr][f"{prop}Overs"][str(overLine)]
							careerTotalGames += averages[team][player][yr]["gamesPlayed"]
							careerTotalOver += over
						except:
							pass

				if careerTotalGames:
					careerTotalOver = round(careerTotalOver * 100 / careerTotalGames)
					try:
						careerAvg = 0
						for p in prop.split("+"):
							careerAvg += averages[team][player]["tot"][p]
						careerAvg = round(careerAvg / averages[team][player]["gamesPlayed"])

					except:
						pass


				if team in lastYearStats and player in lastYearStats[team]:
					l = [d.replace(" gm2", "") for d in lastYearStats[team][player] if d != "tot"]
					seen = {}
					for d in sorted(l, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
						if d in seen:
							d += " gm2"
						seen[d] = True
						lastTotalGames += 1
						val = 0
						for p in prop.split("+"):
							val += lastYearStats[team][player][d].get(p, 0)

						if val > line:
							lastYearTotalOver += 1

						if len(lastYrLast20) < 20:
							lastYrLast20.append(val)

						currOpp = lastYearStats[team][player][d]["vs"]

						if currOpp == opp:
							prevMatchup.append(val)
							for hdr in againstTeamLastYearStats:
								againstTeamLastYearStats[hdr] += lastYearStats[team][player][d].get(hdr, 0)

						if lastYearStats[team][player][d]["isAway"]:
							lastYrAwayHomeSplits[0].append(val)
						else:
							lastYrAwayHomeSplits[1].append(val)

				if lastTotalGames:
					lastYearTotalOver = round(lastYearTotalOver * 100 / lastTotalGames)
				awayGames = len(lastYrAwayHomeSplits[0])
				homeGames = len(lastYrAwayHomeSplits[1])
				if awayGames:
					awayGames = round(sum(lastYrAwayHomeSplits[0]) / awayGames, 2)
				if homeGames:
					homeGames = round(sum(lastYrAwayHomeSplits[1]) / homeGames, 2)
				lastYrAwayHomeSplits = f"{awayGames} - {homeGames}"

				lastYearTeamMatchupOver = 0
				if prevMatchup:
					over = len([x for x in prevMatchup if x > line])
					lastYearTeamMatchupOver = round(over * 100 / len(prevMatchup))

				# current year stats
				lastAll = []
				awayHomeSplits = [[], []]
				winLossSplits = [[], []]
				totalOver = 0
				avg = 0
				if player in stats[team] and "P" not in pos:
					playerStats = stats[team][player]
					gamesPlayed = playerStats["gamesPlayed"]
					val = 0
					for p in prop.split("+"):
						val += stats[team][player].get(p, 0)
					avg = round(val / gamesPlayed, 2)						
					avg = str(format(round(playerStats['h']/playerStats['ab'], 3), '.3f'))[1:]
					

				files = glob.glob(f"{prefix}static/baseballreference/{team}/*.json")
				files = sorted(files, key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
				for file in files:
					chkDate = file.split("/")[-1].replace(".json","")
					currTeam = file.split("/")[-2]
					currOpp = ""
					currIsAway = False
					for g in schedule[chkDate]:
						gameSp = g.split(" @ ")
						if currTeam in gameSp:
							if currTeam == gameSp[0]:
								currIsAway = True
								currOpp = gameSp[1]
							else:
								currOpp = gameSp[0]
							break

					with open(file) as fh:
						gameStats = json.load(fh)
					if player in gameStats:
						val = 0
						for p in prop.split("+"):
							val += gameStats[player].get(p, 0)

						if chkDate == date:
							if val > float(line):
								hit = True

						lastAll.append(int(val))

						if val > line:
							if chkDate != date:
								totalOver += 1

						if len(lastAll) < 10:
							v = str(int(val))
							if chkDate == date:
								v = f"'{v}'"
								lastAll.append(v)
								continue

						if chkDate == date or datetime.strptime(chkDate, "%Y-%m-%d") > datetime.strptime(date, "%Y-%m-%d"):
							continue

						teamScore = scores[chkDate].get(currTeam, 0)
						oppScore = scores[chkDate].get(currOpp, 0)

						if currIsAway:
							awayHomeSplits[0].append(val)
						else:
							awayHomeSplits[1].append(val)

						if teamScore > oppScore:
							winLossSplits[0].append(val)
						elif teamScore < oppScore:
							winLossSplits[1].append(val)

				awayGames = len(awayHomeSplits[0])
				homeGames = len(awayHomeSplits[1])
				if awayGames:
					awayGames = round(sum(awayHomeSplits[0]) / awayGames, 2)
				if homeGames:
					homeGames = round(sum(awayHomeSplits[1]) / homeGames, 2)
				awayHomeSplits = f"{awayGames} - {homeGames}"

				if gamesPlayed:
					totalOver = round(totalOver * 100 / gamesPlayed)


				oppRank = oppRankVal = oppABRank = ""
				oppRankLastYear = ""
				rankingsProp = convertRankingsProp(propName)
				
				if rankingsProp in rankings[opp]:
					oppRankVal = str(rankings[opp][rankingsProp]["season"])
					oppRank = rankings[opp][rankingsProp]['rank']
					oppRankLastYear = rankings[opp]["ly_"+rankingsProp]['rank']
					oppABRank = rankings[opp]["opp_ab"]["rank"]

				hitRateOdds = diff = 0
				if lastYearTotalOver != 100:
					hitRateOdds = int((100 * lastYearTotalOver) / (-100 + lastYearTotalOver))
					diff = -1 * (hitRateOdds - int(overOdds))

				againstPitcherStats = ""
				try:
					againstPitcherStats = f"{str(format(round(bvp[team][player+' v '+pitcher]['h']/bvp[team][player+' v '+pitcher]['ab'], 3), '.3f'))[1:]} {int(bvp[team][player+' v '+pitcher]['h'])}-{int(bvp[team][player+' v '+pitcher]['ab'])}, {int(bvp[team][player+' v '+pitcher]['hr'])} HR, {int(bvp[team][player+' v '+pitcher]['rbi'])} RBI, {int(bvp[team][player+' v '+pitcher]['bb'])} BB, {int(bvp[team][player+' v '+pitcher]['so'])} SO"
				except:
					pass

				try:
					if againstTeamLastYearStats.get("ab", 0):
						againstTeamLastYearStats = f"{str(format(round(againstTeamLastYearStats['h']/againstTeamLastYearStats['ab'], 3), '.3f'))[1:]} {int(againstTeamLastYearStats['h'])}-{int(againstTeamLastYearStats['ab'])}, {int(againstTeamLastYearStats['hr'])} HR, {int(againstTeamLastYearStats['rbi'])} RBI, {int(againstTeamLastYearStats['bb'])} BB, {int(againstTeamLastYearStats['so'])} SO"
					elif againstTeamLastYearStats.get("ip"):
						againstTeamLastYearStats = f"{round(againstTeamLastYearStats['ip'], 1)} IP {int(againstTeamLastYearStats['k'])} K, {int(againstTeamLastYearStats['h'])} H, {int(againstTeamLastYearStats['bb'])} BB"
					else:
						againstTeamLastYearStats = ""
				except:
					againstTeamLastYearStats = ""

				try:
					if againstTeamStats.get("ab", 0):
						againstTeamStats = f"{str(format(round(againstTeamStats['h']/againstTeamStats['ab'], 3), '.3f'))[1:]} {int(againstTeamStats['h'])}-{int(againstTeamStats['ab'])}, {int(againstTeamStats['hr'])} HR, {int(againstTeamStats['rbi'])} RBI, {int(againstTeamStats['bb'])} BB, {int(againstTeamStats['so'])} SO"
					elif againstTeamStats.get("ip"):
						againstTeamStats = f"{round(againstTeamStats['ip'], 1)} IP {int(againstTeamStats['k'])} K, {int(againstTeamStats['h'])} H, {int(againstTeamStats['bb'])} BB"
					else:
						againstTeamStats = ""
				except:
					againstTeamStats = ""

				last20Over = last10Over = 0
				arr = lastAll.copy()
				if len(arr) < 10:
					arr.extend(lastYrLast20[:10-len(lastAll)])
				if arr:
					last10Over = round(len([x for x in arr if float(str(x).replace("'", "")) > line]) * 100 / len(arr))
				arr = lastAll.copy()
				if len(arr) < 20:
					arr.extend(lastYrLast20[:20-len(lastAll)])
				if arr:
					last20Over = round(len([x for x in arr if float(str(x).replace("'", "")) > line]) * 100 / len(arr))

				if True:
					awayHomeSplits = lastYrAwayHomeSplits
					gamesPlayed = lastYrGamesPlayed

				props.append({
					"game": game,
					"player": player.title(),
					"team": team.upper(),
					"opponent": opp.upper(),
					"hit": hit,
					"awayHome": "@" if awayTeam == team else "v",
					"awayHomeSplits": awayHomeSplits,
					#"winLossSplits": winLossSplits,
					"bats": bats,
					"battingNumber": battingNumber,
					"pos": pos,
					"againstPitcherStats": againstPitcherStats,
					"againstTeamStats": againstTeamStats,
					"againstTeamLastYearStats": againstTeamLastYearStats,
					"pitcher": pitcher.split(" ")[-1].title(),
					"pitcherThrows": pitcherThrows,
					"hip": hip,
					"bbip": bbip,
					"hrip": hrip,
					"kip": kip,
					"prop": propName,
					"displayProp": prop,
					"gamesPlayed": gamesPlayed,
					"matchups": len(prevMatchup),
					"line": line or "-",
					"avg": avg,
					"diff": diff,
					"hitRateOdds": hitRateOdds,
					"careerTotalOver": careerTotalOver,
					"againstTeamTotalOver": againstTeamTotalOver,
					"totalOver": totalOver,
					"last10Over": last10Over,
					"last20Over": last20Over,
					"lastYearAvg": lastYearAvg,
					"lastYearTotalOver": lastYearTotalOver,
					"lastYearTeamMatchupOver": lastYearTeamMatchupOver,
					"lastDisplay": ",".join([str(x) for x in lastAll[:10]]),
					"lastAll": ",".join([str(x) for x in lastAll]),
					"oppABRank": oppABRank,
					"oppRankLastYear": oppRankLastYear,
					"oppRank": oppRank,
					"oppRankVal": oppRankVal,
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	return props

def writeLineups():
	url = f"https://www.rotowire.com/baseball/daily-lineups.php"
	#url += "?date=tomorrow"
	outfile = "outmlb2"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)

	lineups = {}
	for box in soup.findAll("div", class_="lineup"):
		if "is-tools" in box.get("class") or "is-ad" in box.get("class"):
			continue

		away = convertDKTeam(box.findAll("div", class_="lineup__abbr")[0].text.lower())
		home = convertDKTeam(box.findAll("div", class_="lineup__abbr")[1].text.lower())

		for idx, lineupList in enumerate(box.findAll("ul", class_="lineup__list")):
			team = away if idx == 0 else home

			if team not in leftOrRight:
				leftOrRight[team] = {}

			status = "confirmed" if "is-green" in lineupList.find("div", class_="dot").get("class") else "expected"
			startingPitcher = " ".join(lineupList.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
			leftOrRight[team][startingPitcher] = lineupList.find("span", class_="lineup__throws").text
			lineups[team] = {
				"batting": [],
				"pitching": startingPitcher
			}
			for li in lineupList.findAll("li")[2:]:
				try:
					player = " ".join(li.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
					lineups[team]["batting"].append(player)
					leftOrRight[team][player] = li.find("span", class_="lineup__bats").text
				except:
					pass

	with open(f"{prefix}static/mlbprops/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)
	with open(f"{prefix}static/baseballreference/leftOrRight.json", "w") as fh:
		json.dump(leftOrRight, fh, indent=4)

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
	parser.add_argument("-p", "--props", action="store_true", help="Props")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.lineups:
		writeLineups()
	elif args.props:
		writeStaticProps()
	elif args.cron:
		writeLineups()
		writeProps(date)
		writeGameLines(date)
		writeStaticProps()

	#writeStaticProps()