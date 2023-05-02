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
import csv
import unicodedata

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
	elif team in ["was", "wsn"]:
		return "wsh"
	elif team in ["sfg", "sdp", "kcr", "tbr"]:
		return team[:2]
	elif team == "az":
		return "ari"
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
	displayTeams = {}
	if "eventGroup" not in data:
		return
	seen = {}
	for event in data["eventGroup"]["events"]:
		start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
		startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=5)
		if startDt.day != int(date[-2:]):
			continue
			pass
		displayTeams[event["teamName1"].lower()] = event.get("teamShortName1", "").lower()
		displayTeams[event["teamName2"].lower()] = event.get("teamShortName2", "").lower()
		if "teamShortName1" not in event:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		else:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
			continue

		if game in seen:
			game += " gm2"

		seen[game] = True
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
	elif prop == "hits allowed":
		return "h_allowed"
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
		return "w"
	
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
		seen = {}
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

			if game in seen:
				game += " gm2"
			seen[game] = True
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
							
							if "participant" not in row["outcomes"][0]:
								continue
							player = strip_accents(row["outcomes"][0]["participant"]).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "").split(" (")[0]
							odds = ["+0","+0"]
							try:
								line = row["outcomes"][0]["line"]
							except:
								line = 0
							for outcome in row["outcomes"]:
								if outcome["label"].lower() == "over" or (prop == "w" and outcome["label"].lower() == "yes"):
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
	headerList = ["NAME","OVER","POS","R/L","Batting #","B. AVG","TEAM","A/H","OPP","OPP RANK","OPP RANK LYR","PROP","LINE","LAST ➡️","AVG","% OVER","L10 % OVER","CAREER % OVER","% OVER VS TEAM","VS TEAM","PITCHER","THROWS","VS PITCHER","UNDER"]
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
		if prop in ["k", "outs", "win", "h_allowed", "bb_allowed", "er"]:
			csvs[prop] = "\t".join(["NAME","OVER","POS","R/L","TEAM","A/H","OPP","OPP RANK","OPP RANK LYR","PROP","LINE","LAST ➡️","AVG","% OVER","L10 % OVER","CAREER % OVER","% OVER VS TEAM","VS TEAM","UNDER"])
		else:
			csvs[prop] = headers
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOver"], k["careerTotalOver"]), reverse=True)
		for row in rows:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			avg = row["avg"]
			if underOdds == '-inf':
				underOdds = 0
			if int(overOdds) > 0:
				overOdds = "'"+overOdds
			if int(underOdds) > 0:
				underOdds = "'"+underOdds
			#if avg >= row["line"]:
			#	avg = f"**{avg}**"

			if prop in ["k", "outs", "win", "h_allowed", "bb_allowed", "er"]:
				csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], overOdds, row["pos"], row["bats"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"], row["avg"], f"{row['totalOver']}%", f"{row['last10Over']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", underOdds]])
			else:
				csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], overOdds, row["pos"], row["bats"], row["battingNumber"], row["battingAvg"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"], row["avg"], f"{row['totalOver']}%", f"{row['last10Over']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", row["pitcher"], row["pitcherThrows"], row["againstPitcherStats"], underOdds]])

	# add full rows
	csvs["full"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		avg = row["avg"]
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		#if avg >= row["line"]:
		#	avg = f"**{avg}**"
		csvs["full"] += "\n" + "\t".join([str(x) for x in [row["player"], overOdds, row["pos"], row["bats"], row["battingNumber"], row["battingAvg"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"], row["avg"], f"{row['totalOver']}%", f"{row['last10Over']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", row["pitcher"], row["pitcherThrows"], row["againstPitcherStats"], underOdds]])


	# add top 4 to reddit
	headerList = ["NAME","POS","Batting #","B. AVG","TEAM","A/H","OPP","OPP RANK","LYR OPP RANK","PROP","LINE","LAST ➡️","AVG","% OVER", "CAREER % OVER", "% OVER VS TEAM", "VS TEAM", "PITCHER", "VS PITCHER", "OVER","UNDER"]
	headers = "\t".join(headerList)
	reddit = "|".join(headers.split("\t"))
	reddit += "\n"+"|".join([":--"]*len(headerList))

	for prop in ["h", "h+r+rbi", "hr", "so"]:
		if prop in splitProps:
			rows = sorted(splitProps[prop], key=lambda k: (k["totalOver"], k["careerTotalOver"]), reverse=True)
			for row in [r for r in rows if int(str(r["battingNumber"]).replace('-', '10')) <= 5][:3]:
				overOdds = row["overOdds"]
				underOdds = row["underOdds"]
				avg = row["lastYearAvg"]
				reddit += "\n" + "|".join([str(x) for x in [row["player"], row["pos"], row["battingNumber"], row["battingAvg"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"], row["avg"], f"{row['totalOver']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", row["pitcher"], row["againstPitcherStats"], overOdds, underOdds]])
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
	for prop in ["h", "hr", "bb_allowed", "k", "outs", "wins", "h_allowed", "bb", "er"]:
		filteredProps = [p for p in props if p["prop"] == prop]
		with open(f"{prefix}static/betting/mlb_{prop}.json", "w") as fh:
			json.dump(filteredProps, fh, indent=4)

def convertProp(prop):
	if prop == "bb_allowed":
		return "bb"
	elif prop == "h_allowed":
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
	elif prop == "h_allowed":
		return "h"
	elif prop == "h":
		return "h_allowed"
	elif prop == "h+r+rbi_allowed":
		return "h+r+rbi"
	elif prop == "h+r+rbi":
		return "h+r+rbi_allowed"
	return prop

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

def getPropData(date = None, playersArg = [], teams = "", pitchers=False, lineArg=""):
	
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/baseballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/baseballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/baseballreference/expected.json") as fh:
		expected = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		playerIds = json.load(fh)
	with open(f"{prefix}static/baseballreference/expectedHR.json") as fh:
		expectedHR = json.load(fh)
	with open(f"{prefix}static/baseballreference/parkFactors.json") as fh:
		parkFactors = json.load(fh)
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerRankings.json") as fh:
		playerRankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)
	try:
		with open(f"{prefix}static/mlbprops/projections/{date}.json") as fh:
			projections = json.load(fh)
	except:
		projections = {}
	with open(f"{prefix}static/baseballreference/numberfireProjections.json") as fh:
		numberfireProjections = json.load(fh)
	with open(f"{prefix}static/baseballreference/bvp.json") as fh:
		bvp = json.load(fh)
	with open(f"{prefix}static/baseballreference/BPPlayerProps.json") as fh:
		ballparkPalProps = json.load(fh)
	with open(f"{prefix}static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)
	with open(f"{prefix}static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)
	with open(f"{prefix}static/baseballreference/leftRightSplits.json") as fh:
		leftRightSplits = json.load(fh)
	with open(f"{prefix}static/baseballreference/pitching.json") as fh:
		pitching = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerHRFactors.json") as fh:
		playerHRFactors = json.load(fh)
	with open(f"{prefix}static/baseballreference/statsVsTeam.json") as fh:
		statsVsTeam = json.load(fh)
	with open(f"{prefix}static/baseballreference/battingPitches.json") as fh:
		battingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/pitchingPitches.json") as fh:
		pitchingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerBattingPitches.json") as fh:
		playerBattingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerPitchingPitches.json") as fh:
		playerPitchingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/statsVsTeamCurrYear.json") as fh:
		statsVsTeamCurrYear = json.load(fh)
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

			try:
				playerId = playerIds[team][player]
			except:
				playerId = 0

			if teams and team not in teams:
				continue

			for propName in propData[game][player]:
				prop = convertProp(propName)
				lastYearAvg = lastYearTotalOver = gamesPlayed = battingNumber = 0
				hit = False
				pitcher = pitcherThrows = awayHomeSplits = ""

				bats = leftOrRight[team].get(player, "")
				hip = bbip = hrip = hpg = kip = 0
				try:
					pitcher = lineups[opp]["pitching"]
					pitcherThrows = leftOrRight[opp][pitcher]
					hip = round(stats[opp][pitcher]["h_allowed"] / stats[opp][pitcher]["ip"], 2)
					hpg = round(stats[opp][pitcher]["h_allowed"] / stats[opp][pitcher]["gamesPlayed"], 1)

					hip = round(averages[opp][pitcher]["tot"]["h"] / averages[opp][pitcher]["tot"]["ip"], 2)
					hrip = round(averages[opp][pitcher]["tot"]["hr"] / averages[opp][pitcher]["tot"]["ip"], 2)
					kip = round(averages[opp][pitcher]["tot"]["k"] / averages[opp][pitcher]["tot"]["ip"], 2)
					bbip = round(averages[opp][pitcher]["tot"]["bb"] / averages[opp][pitcher]["tot"]["ip"], 2)
				except:
					pass


				line = propData[game][player][propName]["line"]
				if line == "-":
					line = 0

				if lineArg:
					line = float(lineArg)

				if prop == "w":
					line = 0.5

				#
				bpOdds = 0
				try:
					if "P" in pos:
						bp = f"{addNumSuffix(ballparkPalProps[team][player][f'{line}{prop}']['bpRank'])} ({ballparkPalProps[team][player][f'{line}{prop}']['bp']})"
						bpOdds = ballparkPalProps[team][player][f'{line}{prop}']['bp']
					else:
						if prop in ballparkPalProps[team][player]:
							bp = f"{addNumSuffix(ballparkPalProps[team][player][prop]['bpRank'])} ({ballparkPalProps[team][player][prop]['bp']})"
							bpOdds = ballparkPalProps[team][player][prop]['bp']
						else:
							bp = f"{addNumSuffix(ballparkPalProps[team][player]['h']['bpRank'])} ({ballparkPalProps[team][player]['h']['bp']})"
							bpOdds = ballparkPalProps[team][player]['h']['bp']
				except:
					bp = ""

				# projection
				projIP = 0
				try:
					if propName in projections[team][player]:
						proj = round(projections[team][player][propName], 2)
					else:
						proj = round(projections[team][player][prop], 2)

					if "P" in pos:
						projIP = round(projections[team][player]["ip"], 2)
				except:
					proj = 0

				#numberfire projection
				numberfireProj = numberfireProjIP = 0
				try:
					numberfireProj = round(numberfireProjections[team][player][prop], 2)
					if "P" in pos:
						numberfireProjIP = round(numberfireProjections[team][player]["ip"], 2)
				except:
					pass

				# pitcher Projection
				try:
					pitcherProj = round(projections[opp][pitcher]["h_allowed"], 2)
				except:
					pitcherProj = 0

				kPerBB = pitchesPerPlate = "-"

				# advanced
				try:
					if "P" in pos:
						advancedPitcher = advanced[team][player].copy()
					else:
						advancedPitcher = advanced[opp][pitcher].copy()
				except:
					advancedPitcher = {}

				# pitches
				try:
					if "P" in pos:
						playerPitches = playerPitchingPitches[team][player].copy()
					else:
						playerPitches = playerPitchingPitches[opp][pitcher].copy()
				except:
					playerPitches = {}

				try:
					oppTeamBattingPitches = battingPitches[opp].copy()
				except:
					oppTeamBattingPitches = {}
				
				pitcherSummary = strikePercent = ""
				if "P" in pos:
					if player in advanced[opp]:
						pitcherSummary = f"{advanced[opp][player]['ba']} AVG, {advanced[opp][player]['xba']} xAVG, {advanced[opp][player]['babip']} BABIP, {advanced[opp][player]['out_zone_percent']}% Out Zone, {advanced[opp][player]['oz_contact_percent']}% Out Zone Contact, {advanced[opp][player]['iz_contact_percent']}% In Zone Contact, {advanced[opp][player]['barrel_batted_rate']}% Barrel Batted"
				else:
					if pitcher and pitcher in advanced[opp]:
						pitcherSummary = f"{advanced[opp][pitcher]['ba']} AVG, {advanced[opp][pitcher]['xba']} xAVG, {advanced[opp][pitcher]['babip']} BABIP, {advanced[opp][pitcher]['out_zone_percent']}% Out Zone, {advanced[opp][pitcher]['oz_contact_percent']}% Out Zone Contact, {advanced[opp][pitcher]['iz_contact_percent']}% In Zone Contact, {advanced[opp][pitcher]['barrel_batted_rate']}% Barrel Batted"

				if "P" in pos:
					try:
						hip = round(averages[team][player]["tot"]["h"] / averages[team][player]["tot"]["ip"], 2)
						bbip = round(averages[team][player]["tot"]["bb"] / averages[team][player]["tot"]["ip"], 2)
					except:
						pass

					# player rankings
					try:
						kPerBB = playerRankings[team][player]["k/bb"]["val"]
					except:
						pass

					try:
						pitchesPerPlate = playerPitchingPitches[team][player]["pit/pa"]
						strikePercent = playerPitchingPitches[team][player]["str%"]
					except:
						pass
				try:
					battingNumber = lineups[team]["batting"].index(player)+1
				except:
					battingNumber = "-"

				overOdds = propData[game][player][propName]["over"]
				underOdds = propData[game][player][propName]["under"]

				bpDiff = 0
				if bpOdds:
					bpDiff = round((int(overOdds) - bpOdds) / abs(int(overOdds)), 3)

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

				againstTeamStats = statsVsTeam[team][opp].get(player, {})

				if opp in statsVsTeamCurrYear[team] and player in statsVsTeamCurrYear[team][opp]:
					for hdr in statsVsTeamCurrYear[team][opp][player]:
						if hdr not in againstTeamStats:
							againstTeamStats[hdr] = statsVsTeamCurrYear[team][opp][player][hdr]
						elif hdr.endswith("Overs"):
							for over in statsVsTeamCurrYear[team][opp][player][hdr]:
								if over not in againstTeamStats[hdr]:
									againstTeamStats[hdr][over] = 0
								againstTeamStats[hdr][over] += statsVsTeamCurrYear[team][opp][player][hdr][over]
						else:
							sumStat(hdr, againstTeamStats, statsVsTeamCurrYear[team][opp][player])

				try:
					overs = againstTeamStats[prop+"Overs"][str(math.ceil(line))]
				except:
					overs = 0
				played = againstTeamStats.get("gamesPlayed", 0)
				if opp in statsVsTeamCurrYear[team] and player in statsVsTeamCurrYear[team][opp]:
					if f"{prop}Overs" in statsVsTeamCurrYear[team][opp][player]:
						overs += statsVsTeamCurrYear[team][opp][player][prop+"Overs"].get(str(math.ceil(line)), 0)
					played += statsVsTeamCurrYear[team][opp][player]["gamesPlayed"]
				if played:
					againstTeamTotalOver = round(overs * 100 / played)

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
					arr = [x for x in lastYrAwayHomeSplits[0] if x > line]
					awayGames = round(len(arr) * 100 / awayGames)
				if homeGames:
					arr = [x for x in lastYrAwayHomeSplits[1] if x > line]
					homeGames = round(len(arr) * 100 / homeGames)
				lastYrAwayHomeSplits = f"{awayGames}% - {homeGames}%"

				lastYearTeamMatchupOver = 0
				if prevMatchup:
					over = len([x for x in prevMatchup if x > line])
					lastYearTeamMatchupOver = round(over * 100 / len(prevMatchup))

				# current year stats
				lastAll = []
				awayHomeSplits = [[], []]
				winLossSplits = [[], []]
				totalOver = battingAvg = avg = babip = bbpg = 0
				
				if player in stats[team]:
					playerStats = stats[team][player]
					gamesPlayed = playerStats["gamesPlayed"]

					if gamesPlayed:
						bbpg = round(playerStats.get("bb", 0) / gamesPlayed, 2)
					val = 0
					currProp = prop
					if propName in stats[team][player]:
						currProp = propName
					for p in currProp.split("+"):
						val += stats[team][player].get(p, 0)
					avg = round(val / gamesPlayed, 2)

					if "P" in pos:
						if player in advanced[team]:
							babip = advanced[team][player]["babip"]
					else:
						battingAvg = str(format(round(playerStats['h']/playerStats['ab'], 3), '.3f'))[1:]
						dem = playerStats["ab"]-playerStats["so"]-playerStats["hr"]+playerStats.get("sf", 0)
						if dem:
							babip = format((playerStats["h"] - playerStats["hr"]) / dem, '.3f')[1:]
					

				files = glob.glob(f"{prefix}static/baseballreference/{team}/*.json")
				files = sorted(files, key=lambda k: datetime.strptime(k.replace("-gm2", "").split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
				for file in files:
					chkDate = file.replace("-gm2", "").split("/")[-1].replace(".json","")
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
						currProp = prop
						if propName in gameStats[player]:
							currProp = propName
						for p in currProp.split("+"):
							val += gameStats[player].get(p, 0)

						if chkDate == date:
							if val > float(line):
								hit = True

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

						lastAll.append(int(val))

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
					arr = [x for x in awayHomeSplits[0] if x > line]
					awayGames = round(len(arr) * 100 / awayGames)
				if homeGames:
					arr = [x for x in awayHomeSplits[1] if x > line]
					homeGames = round(len(arr) * 100 / homeGames)
				awayHomeSplits = f"{awayGames}% - {homeGames}%"

				if gamesPlayed:
					totalOver = round(totalOver * 100 / gamesPlayed)


				oppRank = oppRankVal = oppABRank = ""
				oppRankLastYear = oppRankLast3 = ""
				rankingsProp = convertRankingsProp(propName)
				
				if rankingsProp in rankings[opp]:
					oppRankVal = str(rankings[opp][rankingsProp]["season"])
					oppRank = rankings[opp][rankingsProp]['rank']
					oppRankLastYear = rankings[opp][rankingsProp].get('lastYearRank', 0)
					oppRankLast3 = rankings[opp][rankingsProp].get('last3', 0)
					oppABRank = rankings[opp]["opp_ab"]["rank"]

				hitRateOdds = diff = 0
				if lastYearTotalOver != 100:
					hitRateOdds = int((100 * lastYearTotalOver) / (-100 + lastYearTotalOver))
					diff = -1 * (hitRateOdds - int(overOdds))

				againstPitcherStats = ""
				againstPitcherStatsPerAB = ""
				try:
					againstPitcherStats = f"{str(format(round(bvp[team][player+' v '+pitcher]['h']/bvp[team][player+' v '+pitcher]['ab'], 3), '.3f'))[1:]} {int(bvp[team][player+' v '+pitcher]['h'])}-{int(bvp[team][player+' v '+pitcher]['ab'])}, {int(bvp[team][player+' v '+pitcher]['hr'])} HR, {int(bvp[team][player+' v '+pitcher]['rbi'])} RBI, {int(bvp[team][player+' v '+pitcher]['bb'])} BB, {int(bvp[team][player+' v '+pitcher]['so'])} SO"
					againstPitcherStatsPerAB = f"{str(format(round(bvp[team][player+' v '+pitcher]['h']/bvp[team][player+' v '+pitcher]['ab'], 3), '.3f'))[1:]} {int(bvp[team][player+' v '+pitcher]['h'])}-{bvp[team][player+' v '+pitcher]['ab']}, {round(bvp[team][player+' v '+pitcher]['hr'] / bvp[team][player+' v '+pitcher]['ab'], 2)} HR, {round(bvp[team][player+' v '+pitcher]['rbi'] / bvp[team][player+' v '+pitcher]['ab'], 2)} RBI, {round(bvp[team][player+' v '+pitcher]['bb'] / bvp[team][player+' v '+pitcher]['ab'], 2)} BB, {round(bvp[team][player+' v '+pitcher]['so'] / bvp[team][player+' v '+pitcher]['ab'], 2)} SO"
				except:
					pass

				try:
					if againstTeamLastYearStats.get("ab", 0):
						againstTeamLastYearStatsDisplay = f"{str(format(round(againstTeamLastYearStats['h']/againstTeamLastYearStats['ab'], 3), '.3f'))[1:]} {int(againstTeamLastYearStats['h'])}-{int(againstTeamLastYearStats['ab'])}, {int(againstTeamLastYearStats['hr'])} HR, {int(againstTeamLastYearStats['rbi'])} RBI, {int(againstTeamLastYearStats['bb'])} BB, {int(againstTeamLastYearStats['so'])} SO"
						againstTeamLastYearStatsPerAB = f"{str(format(round(againstTeamLastYearStats['h']/againstTeamLastYearStats['ab'], 3), '.3f'))[1:]} {int(againstTeamLastYearStats['h'])}-{int(againstTeamLastYearStats['ab'])}, {round(againstTeamLastYearStats['hr'] / againstTeamLastYearStats['ab'], 2)} HR, {round(againstTeamLastYearStats['rbi'] / againstTeamLastYearStats['ab'], 2)} RBI, {round(againstTeamLastYearStats['bb'] / againstTeamLastYearStats['ab'], 2)} BB, {round(againstTeamLastYearStats['so'] / againstTeamLastYearStats['ab'], 2)} SO"
					elif againstTeamLastYearStats.get("ip"):
						againstTeamLastYearStatsDisplay = f"{round(againstTeamLastYearStats['ip'], 1)} IP {int(againstTeamLastYearStats['k'])} K, {int(againstTeamLastYearStats['h'])} H, {int(againstTeamLastYearStats['bb'])} BB"
						againstTeamLastYearStats = f"{round(againstTeamLastYearStats['ip'], 1)} IP {round(againstTeamLastYearStats['k'] / againstTeamLastYearStats['ip'], 2)} K, {round(againstTeamLastYearStats['h'] / againstTeamLastYearStats['ip'], 2)} H, {round(againstTeamLastYearStats['bb'] / againstTeamLastYearStats['ip'], 2)} BB"
					else:
						againstTeamLastYearStatsDisplay = ""
						againstTeamLastYearStatsPerAB = ""
				except:
					againstTeamLastYearStatsDisplay = ""
					againstTeamLastYearStatsPerAB = ""

				#try:
				againstTeamStatsPerAB = ""
				if againstTeamStats.get("ab", 0):
					againstTeamStatsDisplay = f"{str(format(round(againstTeamStats['h']/againstTeamStats['ab'], 3), '.3f'))[1:]} {int(againstTeamStats['h'])}-{int(againstTeamStats['ab'])}, {int(againstTeamStats['hr'])} HR, {int(againstTeamStats['rbi'])} RBI, {int(againstTeamStats['bb'])} BB, {int(againstTeamStats['so'])} SO"
					againstTeamStatsPerAB = f"{str(format(round(againstTeamStats['h']/againstTeamStats['ab'], 3), '.3f'))[1:]} {int(againstTeamStats['h'])}-{int(againstTeamStats['ab'])}, {round(againstTeamStats['hr'] / againstTeamStats['ab'], 2)} HR, {round(againstTeamStats['rbi'] / againstTeamStats['ab'], 2)} RBI, {round(againstTeamStats['bb'] / againstTeamStats['ab'], 2)} BB, {round(againstTeamStats['so'] / againstTeamStats['ab'], 2)} SO"
				elif againstTeamStats.get("ip"):
					againstTeamStatsDisplay = f"{round(againstTeamStats['ip'], 1)} IP {int(againstTeamStats['k'])} K, {int(againstTeamStats.get('h', 0))} H, {int(againstTeamStats.get('bb', 0))} BB"
					againstTeamStatsPerAB = f"{round(againstTeamStats['ip'], 1)} IP {round(againstTeamStats['k'] / againstTeamStats['ip'], 2)} K, {round(againstTeamStats.get('h', 0) / againstTeamStats['ip'], 2)} H, {round(againstTeamStats.get('bb', 0) / againstTeamStats['ip'], 2)} BB"
				else:
					againstTeamStatsDisplay = ""
					againstTeamStatsPerAB = ""
				

				last20Over = last10Over = 0
				arr = lastAll.copy()
				if len(arr) < 10:
					arr.extend(lastYrLast20[:10-len(lastAll)])
				if arr:
					last10Over = round(len([x for x in arr[:10] if float(str(x).replace("'", "")) > line]) * 100 / len(arr[:10]))
				arr = lastAll.copy()
				if len(arr) < 20:
					arr.extend(lastYrLast20[:20-len(lastAll)])
				if arr:
					last20Over = round(len([x for x in arr if float(str(x).replace("'", "")) > line]) * 100 / len(arr))

				if True:
					gamesPlayed = lastYrGamesPlayed

				projDiff = 0
				if proj:
					projDiff = round((proj - line) / proj, 3)

				hrFactor = ""
				if team in playerHRFactors and player in playerHRFactors[team]:
					hrFactor = playerHRFactors[team][player]

				# savant
				xHR = 0
				try:
					xHR = expectedHR[team][player]["xhr_diff"]
				except:
					pass
				pitcherXBA = xBA = 0
				try:
					xBA = format(expected[team][player]["est_ba"], '.3f')[1:]
					if "P" in pos:
						battingAvg = format(expected[team][player]["ba"], '.3f')[1:]
					else:
						pitcherXBA = format(expected[opp][pitcher]["est_ba"], '.3f')[1:]
				except:
					pass

				stadiumHitsRank = parkFactors[homeTeam]["hitsRank"]
				stadiumHrRank = parkFactors[homeTeam]["hrRank"]

				# fangraphs
				leftRightAvg = 0
				try:
					leftRightAvg = format(leftRightSplits[team][player][f"{pitcherThrows}HP"]["avg"], '.3f')[1:]
				except:
					pass

				myProj = 0
				if projIP:
					avgIP = projIP
					if numberfireProjIP:
						avgIP = (projIP + numberfireProjIP) / 2
					myProj = avgIP * 3
					if propName == "bb_allowed":
						myProj *= float(advancedPitcher.get("p_bb_percent", 0)) * 0.01
					elif propName == "k":
						myProj *= float(advancedPitcher.get("p_k_percent", 0)) * 0.01
					elif propName == "h_allowed":
						myProj = avgIP * hip
					myProj = round(myProj, 2)

				props.append({
					"game": game,
					"playerId": playerId,
					"player": player.title(),
					"team": team.upper(),
					"opponent": opp.upper(),
					"hit": hit,
					"awayHome": "@" if awayTeam == team else "v",
					"awayHomeSplits": awayHomeSplits,
					"lastYearAwayHomeSplits": lastYrAwayHomeSplits,
					"playerPitches": playerPitches,
					"oppTeamBattingPitches": oppTeamBattingPitches,
					#"winLossSplits": winLossSplits,
					"bats": bats,
					"battingNumber": battingNumber,
					"hrFactor": hrFactor,
					"bp": bp,
					"babip": babip,
					"bbpg": bbpg,
					"xBA": xBA,
					"xHR": xHR,
					"pitcherXBA": pitcherXBA,
					"leftRightAvg": leftRightAvg,
					"stadiumHitsRank": stadiumHitsRank,
					"stadiumHrRank": stadiumHrRank,
					"pos": pos,
					"advancedPitcher": advancedPitcher,
					"againstPitcherStats": againstPitcherStats,
					"againstPitcherStatsPerAB": againstPitcherStatsPerAB,
					"againstTeamStats": againstTeamStatsDisplay,
					"againstTeamStatsPerAB": againstTeamStatsPerAB,
					"againstTeamLastYearStats": againstTeamLastYearStatsDisplay,
					"againstTeamLastYearStatsPerAB": againstTeamLastYearStatsPerAB,
					"pitcherSummary": pitcherSummary,
					"pitcher": pitcher.split(" ")[-1].title(),
					"pitcherThrows": pitcherThrows,
					"pitcherProj": pitcherProj,
					"k/bb": kPerBB,
					"pitchesPerPlate": pitchesPerPlate,
					"hip": hip,
					"hpg": hpg,
					"bbip": bbip,
					"hrip": hrip,
					"kip": kip,
					"prop": propName,
					"displayProp": prop,
					"gamesPlayed": gamesPlayed,
					"matchups": len(prevMatchup),
					"line": line or 0,
					"numberfireProj": numberfireProj,
					"myProj": myProj,
					"proj": proj,
					"numberfireProjIP": numberfireProjIP,
					"projIP": projIP,
					"projDiff": projDiff,
					"bpDiff": bpDiff,
					"battingAvg": battingAvg,
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
					"oppRankLast3": oppRankLast3,
					"oppRankVal": oppRankVal,
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	return props

def writeLineups():
	url = f"https://www.rotowire.com/baseball/daily-lineups.php"

	if datetime.now().hour > 21 or datetime.now().hour < 3:
		url += "?date=tomorrow"	
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
			try:
				leftOrRight[team][startingPitcher] = lineupList.find("span", class_="lineup__throws").text
			except:
				pass

			lineupTeam = team
			if team in lineups:
				lineupTeam += " gm2"
			lineups[lineupTeam] = {
				"batting": [],
				"pitching": startingPitcher
			}
			for li in lineupList.findAll("li")[2:]:
				try:
					player = " ".join(li.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
					lineups[lineupTeam]["batting"].append(player)
					leftOrRight[team][player] = li.find("span", class_="lineup__bats").text
				except:
					pass

	with open(f"{prefix}static/mlbprops/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)
	with open(f"{prefix}static/baseballreference/leftOrRight.json", "w") as fh:
		json.dump(leftOrRight, fh, indent=4)

def writeLeftRightSplits():
	url = "https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=1&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=1&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C10&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pg=0"

	leftRightSplits = {}

	for throws in ["LHP", "RHP"]:
		with open(f"{prefix}Splits Leaderboard Data vs {throws}.csv", newline="") as fh:
			reader = csv.reader(fh)

			headers = []
			for idx, row in enumerate(reader):
				if idx == 0:
					headers = [x.lower() for x in row]
				else:
					player = strip_accents(row[1]).lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
					team = convertDKTeam(row[2].lower())
					if team not in leftRightSplits:
						leftRightSplits[team] = {}
					if player not in leftRightSplits[team]:
						leftRightSplits[team][player] = {}
					if throws not in leftRightSplits[team][player]:
						leftRightSplits[team][player][throws] = {}

					for hdr, col in zip(headers, row):
						try:
							leftRightSplits[team][player][throws][f"{hdr}"] = float(col)
						except:
							leftRightSplits[team][player][throws][f"{hdr}"] = col

	with open(f"{prefix}static/baseballreference/leftRightSplits.json", "w") as fh:
		json.dump(leftRightSplits, fh, indent=4)


def write_numberfire_projections():
	projections = {}
	for t in ["batters", "pitchers"]:
		url = "https://www.numberfire.com/mlb/daily-fantasy/daily-baseball-projections/"+t

		outfile = "outmlb2"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for row in soup.find("table", class_="stat-table").find("tbody").findAll("tr"):
			try:
				team = row.find("span", class_="team-player__team active").text.strip().lower()
			except:
				continue
			#player = row.find("a", class_="full").get("href").split("/")[-1].lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "").replace("c j ", "cj ").replace("jd ", "jd ").replace("j p ", "jp ")
			player = row.find("a", class_="full").text.strip().lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "").replace("c j ", "cj ").replace("jd ", "jd ").replace("j p ", "jp ")
			
			if team not in projections:
				projections[team] = {}
			projections[team][player] = {}

			cutoff = 5 if t == "batters" else 4
			for td in row.findAll("td")[cutoff:]:
				hdr = td.get("class")[0]
				if hdr == "wl":
					w,l = map(float, td.text.strip().split("-"))
					projections[team][player]["w"] = w
					projections[team][player]["l"] = l
				else:
					val = float(td.text.strip())
					projections[team][player][hdr] = val

			if t == "batters":
				projections[team][player]["h"] = projections[team][player]["1b"]+projections[team][player]["2b"]+projections[team][player]["3b"]+projections[team][player]["hr"]
				projections[team][player]["h+r+rbi"] = projections[team][player]["h"]+projections[team][player]["r"]+projections[team][player]["rbi"]
				projections[team][player]["tb"] = projections[team][player]["1b"]+2*projections[team][player]["2b"]+3*projections[team][player]["3b"]+4*projections[team][player]["hr"]

	with open(f"{prefix}static/baseballreference/numberfireProjections.json", "w") as fh:
		json.dump(projections, fh, indent=4)

def write_projections(date):
	write_numberfire_projections()
	year = datetime.now().year

	projections = {}
	for HP in ["H", "P"]:
		with open(f"{prefix}FantasyPros_{year}_Projections_{HP}.csv", newline="") as fh:
			reader = csv.reader(fh)
			#data = fh.readlines()

			headers = []
			for idx, row in enumerate(reader):
				if idx == 0:
					headers = [x.lower() for x in row[5:-1]]
				else:
					if len(row) < 2:
						continue
					player = row[1].lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
					team = row[2].lower()
					if team == "cws":
						team = "chw"
					if team not in projections:
						projections[team] = {}
					if player not in projections[team]:
						projections[team][player] = {}

					if player.startswith("shohei") and row[3] != "SP,DH":
						continue
						

					for hdr, col in zip(headers, row[5:-1]):
						suffix = ""
						if HP == "P" and hdr in ["h", "bb", "hr"]:
							suffix = "_allowed"
						projections[team][player][f"{hdr}{suffix}"] = float(col)

					if "rbi" in projections[team][player]:
						projections[team][player]["h+r+rbi"] = round(projections[team][player]["h"]+projections[team][player]["r"]+projections[team][player]["rbi"], 2)
						projections[team][player]["1b"] = projections[team][player]["h"] - (projections[team][player]["hr"] + projections[team][player]["3b"] + projections[team][player]["2b"])
						projections[team][player]["tb"] = round(projections[team][player]["hr"]*4 + projections[team][player]["3b"]*3 + projections[team][player]["2b"]*2 + projections[team][player]["1b"], 2)
	with open(f"{prefix}static/mlbprops/projections/{date}.json", "w") as fh:
		json.dump(projections, fh, indent=4)

def getSlateData(date = None, teams=""):
	res = []

	if teams:
		teams = teams.lower().split(",")

	if not date:
		date = datetime.now()
		date = str(date)[:10]

	with open(f"{prefix}static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/baseballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)
	with open(f"{prefix}static/baseballreference/teamTotals.json") as fh:
		teamTotals = json.load(fh)
	with open(f"{prefix}static/mlbprops/lineups.json") as fh:
		lineups = json.load(fh)
	with open(f"{prefix}static/mlbprops/lines/{date}.json") as fh:
		gameLines = json.load(fh)

	for game in schedule[date]:
		gameSp = game.split(" @ ")
		isAway = True
		for idx, team in enumerate(gameSp):
			opp = gameSp[0] if idx == 1 else gameSp[1]
			if idx == 1:
				isAway = False

			if game not in gameLines or "line" not in gameLines[game]:
				continue

			runline = gameLines[game]["line"]["line"]
			totalLine = gameLines[game]["total"]["line"]
			if idx == 1:
				runline *= -1

			runlineSpread = runline

			if runline > 0:
				runline = f"+{runline}"

			pitcherStats = {}
			pitcherRecord = pitcher = pitcherThrows = ""
			try:
				pitcher = lineups[team]["pitching"]
				pitcherThrows = leftOrRight[team][pitcher]
				pitcherStats = stats[team][pitcher]
				pitcherRecord = f"{pitcherStats.get('w', 0)}W-{pitcherStats.get('l', 0)}L"
				pitcherStats["era"] = round(9 * pitcherStats["er"] / pitcherStats["ip"], 2)
				pitcherStats["whip"] = round((pitcherStats["h_allowed"]+pitcherStats["bb_allowed"]) / pitcherStats["ip"], 2)
				pitcherStats["hip"] = round((pitcherStats["h_allowed"]) / pitcherStats["ip"], 2)
				pitcherStats["kip"] = round((pitcherStats["k"]) / pitcherStats["ip"], 2)
				pitcherStats["bbip"] = round((pitcherStats["bb_allowed"]) / pitcherStats["ip"], 2)
			except:
				pass

			runline = f"{runline} ({gameLines[game]['line']['odds'].split(',')[idx]})"
			moneyline = gameLines[game]["moneyline"]["odds"].split(",")[idx]
			totalLine = gameLines[game]['total']['line']
			total = f"{'o' if idx == 0 else 'u'}{gameLines[game]['total']['line']} ({gameLines[game]['total']['odds'].split(',')[idx]})"

			prevMatchup = []
			totals = {"rpg": [], "rpga": [], "hpg": [], "hpga": [], "overs": [], "diff": []}
			for dt in sorted(schedule, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
				if dt == date or datetime.strptime(dt, "%Y-%m-%d") > datetime.strptime(date, "%Y-%m-%d"):
					continue
				for g in schedule[dt]:
					gSp = g.split(" @ ")
					if gSp[0] in scores[dt] and team in gSp:
						score1 = scores[dt][gSp[0]]
						score2 = scores[dt][gSp[1]]
						wonLost = "Won"
						currPitcher = []
						score = f"{score1}-{score2}"
						file = f"{prefix}static/baseballreference/{team}/{dt}.json"
						with open(file) as fh:
							gameStats = json.load(fh)

						if score2 > score1:
							score = f"{score2}-{score1}"
							if team == gSp[0]:
								wonLost = "Lost"
						elif team == gSp[1]:
							wonLost = "Lost"

						if opp in gSp:
							for p in gameStats:
								if "ip" in gameStats[p]:
									currPitcher.append(p)
							prevMatchup.append(f"{dt} {wonLost} {score} (SP: {currPitcher[0].title()})")

						teamScore = score1
						oppScore = score2
						if team == gSp[1]:
							teamScore, oppScore = oppScore, teamScore
						totals["rpg"].append(teamScore)
						totals["rpga"].append(oppScore)
						totals["overs"].append(teamScore+oppScore)
						totals["diff"].append(teamScore-oppScore)


			if len(totals["overs"]):
				totals["oversL10"] = ",".join([str(x) for x in totals["overs"][:10]])
				totals["ttL10"] = ",".join([str(x) for x in totals["rpg"][:10]])
				totals["totalOver"] = round(len([x for x in totals["overs"] if x > totalLine]) * 100 / len(totals["overs"]))
				totals["runlineOver"] = round(len([x for x in totals["diff"] if x+runlineSpread > 0]) * 100 / len(totals["diff"]))
				totals["teamOver"] = f"{round(len([x for x in totals['overs'] if int(x) > totalLine]) * 100 / len(totals['overs']))}% SZN • {round(len([x for x in totals['overs'][:15] if int(x) > totalLine]) * 100 / len(totals['overs'][:15]))}% L15 • {round(len([x for x in totals['overs'][:5] if int(x) > totalLine]) * 100 / len(totals['overs'][:5]))}% L5 • {round(len([x for x in totals['overs'][:3] if int(x) > totalLine]) * 100 / len(totals['overs'][:3]))}% L3"

			for p in ["h", "r"]:
				totals[f"{p}pg"] = rankings[team][f"{p}"]["season"]
				totals[f"{p}pgL3"] = rankings[team][f"{p}"]["last3"]
				totals[f"{p}pgRank"] = rankings[team][f"{p}"]["rank"]
				totals[f"{p}pga"] = rankings[team][f"{p}_allowed"]["season"]
				totals[f"{p}pgaRank"] = rankings[team][f"{p}_allowed"]["rank"]
			for key in ["overs"]:
				if len(totals[key]):
					totals[key] = round(sum(totals[key]) / len(totals[key]), 1)
				else:
					totals[key] = 0

			res.append({
				"game": game,
				"team": team,
				"opp": opp,
				"awayHome": "A" if isAway else "H",
				"prevMatchup": " • ".join(prevMatchup),
				"prevMatchupList": prevMatchup,
				"runline": runline,
				"moneylineOdds": moneyline,
				"total": total,
				"totals": totals,
				"pitcher": pitcher,
				"rankings": rankings[team],
				"pitcherStats": pitcherStats,
				"pitcherThrows": pitcherThrows,
				"pitcherRecord": pitcherRecord,
			})

	return res

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def writeBPPlayerProps(date):
	url = f"https://ballparkpal.com/PlayerProps.php?date={date}"

	playerProps = {}
	outfile = "outmlb2"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	bps = {}
	for row in soup.find("table", id="table_id").findAll("tr")[1:]:
		prop = row.findAll("td")[6].text.lower().split(" ")[1]
		if prop == "bases":
			prop = "tb"
		elif prop == "ks":
			prop = "k"
		elif prop == "hits":
			prop = "h"

		if prop == "k":
			line = row.findAll("td")[6].text.split(" ")[-1]
			prop = f"{line}k"

		if prop not in bps:
			bps[prop] = []

		try:
			bps[prop].append(int(row.findAll("td")[7].text))
		except:
			continue

	for prop in bps:
		bps[prop] = sorted(bps[prop])

	for row in soup.find("table", id="table_id").findAll("tr")[1:]:
		team = row.find("td").text.lower().replace("was", "wsh")
		player = row.findAll("td")[1].text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
		pa = float(row.findAll("td")[5].text)
		prop = row.findAll("td")[6].text.lower().split(" ")[1]
		if prop == "bases":
			prop = "tb"
		elif prop == "ks":
			prop = "k"
		elif prop == "hits":
			prop = "h"

		try:
			bp = int(row.findAll("td")[7].text)
		except:
			continue

		line = 0
		if prop == "k":
			line = row.findAll("td")[6].text.split(" ")[-1]
			prop = f"{line}k"

		if team not in playerProps:
			playerProps[team] = {}

		if player not in playerProps[team]:
			playerProps[team][player] = {}

		if prop not in playerProps[team][player]:
			playerProps[team][player][prop] = {}

		playerProps[team][player][prop] = {
			"pa": pa, "bp": bp, "bpRank": bps[prop].index(int(bp))
		}

	with open(f"{prefix}static/baseballreference/BPPlayerProps.json", "w") as fh:
		json.dump(playerProps, fh, indent=4)

def writeBallparks(date):
	url = f"https://ballparkpal.com/ParkFactors.php?date={date}"

	ballparks = {}
	playerHRFactors = {}
	outfile = "outmlb2"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	for row in soup.find("table", class_="parkFactorsTable").findAll("tr")[1:]:
		game = row.find("div", class_="matchupText").text.strip().lower().replace("was", "wsh")
		hr = row.find("td", class_="projectionText").text

		ballparks[game] = hr

	for row in soup.find("table", id="table_id").findAll("tr")[1:]:
		team = row.find("td").text.lower().replace("was", "wsh")
		player = row.findAll("td")[1].text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
		hr = float(row.findAll("td")[3].text)

		if team not in playerHRFactors:
			playerHRFactors[team] = {}
		playerHRFactors[team][player] = hr

	with open(f"{prefix}static/baseballreference/ballparks.json", "w") as fh:
		json.dump(ballparks, fh, indent=4)

	with open(f"{prefix}static/baseballreference/playerHRFactors.json", "w") as fh:
		json.dump(playerHRFactors, fh, indent=4)

@mlbprops_blueprint.route('/slatemlb')
def slate_route():
	date = None
	if request.args.get("date"):
		date = request.args.get("date")
	data = getSlateData(date=date)
	grouped = {}
	for row in data:
		if row["game"] not in grouped:
			grouped[row["game"]] = {}
		grouped[row["game"]][row["awayHome"]] = row

	return render_template("slatemlb.html", data=grouped)

@mlbprops_blueprint.route('/getMLBProps')
def getProps_route():
	pitchers = False
	if request.args.get("pitchers"):
		pitchers = True
	if request.args.get("players") or request.args.get("date") or request.args.get("line"):
		players = ""
		if request.args.get("players"):
			players = request.args.get("players").lower().split(",")
		props = getPropData(date=request.args.get("date"), playersArg=players, teams="", pitchers=pitchers, lineArg=request.args.get("line") or "")
	elif request.args.get("prop"):
		path = f"{prefix}static/betting/mlb_{request.args.get('prop')}.json"
		if not os.path.exists(path):
			with open(f"{prefix}static/betting/mlb.json") as fh:
				props = json.load(fh)
		else:
			with open(path) as fh:
				props = json.load(fh)
	else:
		with open(f"{prefix}static/betting/mlb.json") as fh:
			props = json.load(fh)

	if request.args.get("teams"):
		arr = []
		teams = request.args.get("teams").lower().split(",")
		for row in props:
			team1, team2 = map(str, row["game"].split(" @ "))
			if team1 in teams or team2 in teams:
				arr.append(row)
		props = arr

	if request.args.get("bet"):
		arr = []
		for row in props:
			if "P" in row["pos"]:
				arr.append(row)
			else:
				if int(str(row["battingNumber"]).replace("-", "10")) <= 6:
					arr.append(row)
		props = arr

	if request.args.get("pitchers"):
		arr = []
		for row in props:
			if "P" in row["pos"]:
				arr.append(row)
		props = arr

	return jsonify(props)

@mlbprops_blueprint.route('/mlbprops')
def props_route():
	prop = date = teams = players = bet = pitchers = line = ""
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
	if request.args.get("bet"):
		bet = request.args.get("bet")
	if request.args.get("line"):
		line = request.args.get("line")
	if request.args.get("pitchers"):
		pitchers = request.args.get("pitchers")

	with open(f"{prefix}bets") as fh:
		bets = json.load(fh)

	if prop in bets:
		bets = bets[prop]
	else:
		bets = []
		
	bets = ",".join(bets)
	return render_template("mlbprops.html", prop=prop, date=date, teams=teams, bets=bets, players=players, bet=bet, line=line, pitchers=pitchers)


def quartiles(arr):
	arr = sorted(arr)
	size = len(arr)
	mLen, qLen = int(size/2), int(size/4)
	q1, q3 = arr[qLen], arr[qLen*3]

	if size % 2 == 0:
		q1 = round((arr[qLen - 1] + arr[qLen]) / 2, 1)
		q3 = round((arr[3*qLen - 1] + arr[3*qLen]) / 2, 1)
		mid = round((arr[mLen-1] + arr[mLen]) / 2, 1)
	else:
		mid = arr[mLen]
	return q1, mid, q3

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("--lineups", help="Lineups", action="store_true")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("-p", "--props", action="store_true", help="Props")
	parser.add_argument("--projections", help="Projections", action="store_true")
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
	elif args.projections:
		write_projections(date)
		writeLeftRightSplits()
		writeStaticProps()
	elif args.cron:
		writeLineups()
		writeProps(date)
		writeBallparks(date)
		write_projections(date)
		writeBPPlayerProps(date)
		writeLeftRightSplits()
		writeGameLines(date)
		writeStaticProps()

	#writeBPPlayerProps(date)
	#writeGameLines(date)
	#write_numberfire_projections()
	#writeBallparks(date)
	#Walks Allowed (Proj) = (FantasyPros Projection) * (Pitches per Plate Appearance) * (Opponent BB Rank) * (K/BB) / (Season Average) * (Career Walk Average)

	#writeStaticProps()
	#writeBallparks()


	if False:
		with open(f"{prefix}static/baseballreference/schedule.json") as fh:
			schedule = json.load(fh)

		with open(f"{prefix}static/baseballreference/rankings.json") as fh:
			rankings = json.load(fh)

		with open(f"{prefix}static/baseballreference/ballparks.json") as fh:
			ballparks = json.load(fh)

		with open(f"{prefix}static/baseballreference/advanced.json") as fh:
			advanced = json.load(fh)

		with open(f"{prefix}static/mlbprops/lineups.json") as fh:
			lineups = json.load(fh)

		with open(f"{prefix}static/baseballreference/parkfactors.json") as fh:
			savantRank = json.load(fh)

		print("Rankings Source: [Team Rankings](https://www.teamrankings.com/mlb/stat/home-runs-per-game)  ")
		print("Park Factor % Source: [Ballparkpal](https://ballparkpal.com/ParkFactors.php)  ")
		print("Park Factor Rank Source: [baseball savant](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors)")
		print("\n")

		headers = ["Game", "Park Factor Rank", "Park Factor %", "Away", "Away HR/G", "Away Rank", "Away Opp HR/G", "Away Opp HR/G Rank", "Away A-H Splits", "Home", "Home HR/G", "Home Rank", "Home Opp HR/G", "Home Opp HR/G Rank", "Home A-H Splits"]

		print("|".join(headers))
		print("|".join([":--"]*len(headers)))
		seen = {}
		for game in schedule[date]:
			if game in seen:
				continue
			seen[game] = True
			away, home = map(str, game.split(" @ "))
			awayRank, awayVal = addNumSuffix(rankings[away]["hr"]["rank"]), rankings[away]["hr"]["season"]
			awayOppRank, awayOppVal = addNumSuffix(rankings[away]["hr_allowed"]["rank"]), rankings[away]["hr_allowed"]["season"]
			awaySplits = f"**{rankings[away]['hr']['away']}** - {rankings[away]['hr']['home']}"
			homeRank, homeVal = addNumSuffix(rankings[home]["hr"]["rank"]), rankings[home]["hr"]["season"]
			homeOppRank, homeOppVal = addNumSuffix(rankings[home]["hr_allowed"]["rank"]), rankings[home]["hr_allowed"]["season"]
			homeSplits = f"{rankings[home]['hr']['away']} - **{rankings[home]['hr']['home']}**"
			print(f"{game.upper()}|{addNumSuffix(savantRank[home]['hrRank'])}|{ballparks[game]}|{away.upper()}|{awayVal}|{awayRank}|{awayOppVal}|{awayOppRank}|{awaySplits}|{home.upper()}|{homeVal}|{homeRank}|{homeOppVal}|{homeOppRank}|{homeSplits}")

		print("\n")
		headers = ["Team", "Opp", "Opp Pitcher", "Sweet Spot %", "Hard Hit %", "Barrel Batted %", "Out of Zone %", "In Zone Contact %"]
		print("|".join(headers))
		print("|".join([":--"]*len(headers)))
		for game in schedule[date]:
			away, home = map(str, game.split(" @ "))
			awayPitcher, homePitcher = lineups[away]["pitching"], lineups[home]["pitching"]
			try:
				print(f"{away.upper()}|{home.upper()}|{homePitcher.title()}|{advanced[home][homePitcher]['sweet_spot_percent']}%|{advanced[home][homePitcher]['hard_hit_percent']}%|{advanced[home][homePitcher]['barrel_batted_rate']}%|{advanced[home][homePitcher]['out_zone_percent']}%|{advanced[home][homePitcher]['iz_contact_percent']}%")
				print(f"{home.upper()}|{away.upper()}|{awayPitcher.title()}|{advanced[away][awayPitcher]['sweet_spot_percent']}%|{advanced[away][awayPitcher]['hard_hit_percent']}%|{advanced[away][awayPitcher]['barrel_batted_rate']}%|{advanced[away][awayPitcher]['out_zone_percent']}%|{advanced[away][awayPitcher]['iz_contact_percent']}%")
			except:
				continue

	if False:

		totHits = {}
		games = {}
		for team in os.listdir("static/baseballreference/"):
			if team.endswith("json"):
				continue

			for dt in os.listdir(f"static/baseballreference/{team}/"):
				with open(f"static/baseballreference/{team}/{dt}") as fh:
					stats = json.load(fh)

				if not stats:
					continue

				dt = dt[:-5].replace("-gm2", "")
				if dt not in totHits:
					totHits[dt] = {"h": 0, "hr": 0, "r": 0}
				if dt not in games:
					games[dt] = 0

				games[dt] += 1

				for player in stats:
					if "ip" not in stats[player]:
						for hdr in totHits[dt]:
							totHits[dt][hdr] += stats[player][hdr]


		for p in ["h", "hr", "r"]:
			for dt in sorted(totHits, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
				for prop in totHits[dt]:
					if p != prop:
						continue
					avg = round(totHits[dt][prop] / (games[dt] / 2), 2)
					print(dt, prop, avg)
			print("\n")

		hrs = []
		for dt in totHits:
			hrs.append(totHits[dt]["hr"] / (games[dt] / 2))
		print(sum(hrs) / len(hrs))


	# Analyze pitchers
	if False:
		with open(f"{prefix}static/baseballreference/schedule.json") as fh:
			schedule = json.load(fh)
		with open(f"{prefix}static/baseballreference/roster.json") as fh:
			roster = json.load(fh)
		with open(f"{prefix}static/baseballreference/advanced.json") as fh:
			advanced = json.load(fh)

		analysis = {}
		dts = schedule.keys()
		#dts = ["2023-04-26"]
		for dt in sorted(dts, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):

			path = f"{prefix}static/mlbprops/dates/{dt}.json"
			if not os.path.exists(path):
				continue

			with open(path) as fh:
				props = json.load(fh)

			if datetime.strptime(dt, "%Y-%m-%d") >= datetime.strptime(str(datetime.now())[:10], "%Y-%m-%d"):
				continue

			for game in schedule[dt]:
				away, home = map(str, game.split(" @ "))

				for teamIdx, team in enumerate([away, home]):

					path = f"{prefix}static/baseballreference/{team}/{dt}.json"
					if not os.path.exists(path):
						continue

					with open(path) as fh:
						stats = json.load(fh)

					for player in stats:

						try:
							if "P" not in roster[team][player]:
								continue
						except:
							continue

						if game not in props or player not in props[game]:
							continue

						for prop in ["k", "bb_allowed", "h_allowed"]:
							if prop not in props[game][player] or prop not in stats[player]:
								continue

							if prop not in analysis:
								analysis[prop] = {}

							if player not in advanced[team]:
								continue

							hit = "miss"
							line = props[game][player][prop]["line"]
							if stats[player][prop] >= line:
								hit = "hit"

							for hdr in ["out_zone_percent", "z_swing_percent", "oz_swing_percent", "iz_contact_percent", "oz_contact_percent", "whiff_percent", "f_strike_percent", "swing_percent", "z_swing_miss_percent", "oz_swing_miss_percent"]:

								if hdr not in analysis[prop]:
									analysis[prop][hdr] = {"hit": [], "miss": []}
								
								analysis[prop][hdr][hit].append(advanced[team][player][hdr])
			
		for prop in analysis:
			print(prop)
			for hdr in analysis[prop]:
				arr = []
				for hit in analysis[prop][hdr]:
					arr.append(quartiles(analysis[prop][hdr][hit]))
				print("\t", hdr, arr)