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

ncaafprops_blueprint = Blueprint('ncaafprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def teamTotals(today, schedule):
	with open(f"{prefix}static/ncaafreference/scores.json") as fh:
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
		files = sorted(glob.glob(f"{prefix}static/ncaafreference/{team}/*-*-*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
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

@ncaafprops_blueprint.route('/getNCAAFProps')
def getProps_route():
	res = []

	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.lower().split(",")

	date = datetime.now()
	date = str(date)[:10]
	if request.args.get("date"):
		date = request.args.get("date")

	with open(f"{prefix}static/ncaafprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/ncaafreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/ncaafreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/ncaafreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/ncaafreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/ncaafreference/teams.json") as fh:
		teamIds = json.load(fh)

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

			lastYearStats = {}
			if os.path.exists(f"{prefix}static/ncaafreference/{team}/lastYearStats.json"):
				with open(f"{prefix}static/ncaafreference/{team}/lastYearStats.json") as fh:
					lastYearStats = json.load(fh)

			for prop in propData[game][propName]:
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
				hit = False
				if line:
					files = sorted(glob.glob(f"{prefix}static/ncaafreference/{team}/*-*-*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
					for file in files:
						chkDate = file.split("/")[-1].replace(".json","")
						with open(file) as fh:
							gameStats = json.load(fh)
						if name in gameStats:
							totalGames += 1
							val = val = gameStats[name].get(prop, 0)

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
				if line and name in lastYearStats and lastYearStats[name]:
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
							if val > float(line):
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
				if overPos:
					overList = oppOvers[opp][overPos][prop]
					linePerMin = 0
					if overList:
						oppOver = round(len([x for x in overList if x > linePerMin]) * 100 / len(overList))

				props.append({
					"player": name.title(),
					"team": team.upper(),
					"display": teamIds[team]["display"].lower().replace(" ", "-"),
					"pos": pos,
					"opponent": opp.upper(),
					"propType": prop,
					"line": line or "-",
					"avg": avg,
					"hit": hit,
					"oppOver": oppOver,
					"totalOver": totalOver,
					"lastTotalOver": lastTotalOver,
					"totalOverLast5": totalOverLast5,
					"last5": ",".join(last5),
					"overOdds": overOdds,
					"underOdds": underOdds
				})


	writeCsvs(props)

	return jsonify(props)


def writeCsvs(props):
	csvs = {}
	splitProps = {"full": []}
	headers = "\t".join(["NAME","POS","TEAM","OPP","PROP","LINE","SZN AVG","% OVER","L5 % OVER","LAST 7 GAMES ➡️","OVER", "UNDER"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

	for row in props:
		if row["propType"] not in splitProps:
			splitProps[row["propType"]] = []
		splitProps[row["propType"]].append(row)
		splitProps["full"].append(row)

	# add full rows
	csvs["full_name"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"], -k["totalOverLast5"], -k["totalOver"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		try:
			csvs["full_name"] += "\n" + "\t".join([row["player"], row["pos"], row["team"], row["opponent"].upper(), row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], overOdds, underOdds])
		except:
			pass

	csvs["full_hit"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		try:
			csvs["full_hit"] += "\n" + "\t".join([row["player"], row["pos"], row["team"], row["opponent"].upper(), row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], overOdds, underOdds])
		except:
			pass

	for prop in csvs:
		if prop == "full":
			continue
		with open(f"{prefix}static/ncaafprops/csvs/{prop}.csv", "w") as fh:
			fh.write(csvs[prop])

def convertDKTeam(team):
	if team == "tx a&m-cc":
		return "amcc"
	elif team == "az st":
		return "asu"
	elif team == "bsu":
		return "bois"
	elif team == "cal poly":
		return "cp"
	elif team == "furm":
		return "fur"
	elif team == "michigan":
		return "mich"
	elif team == "minnesota":
		return "minn"
	elif team == "jville st":
		return "jvst"
	elif team == "mizz":
		return "miz"
	elif team == "miss st":
		return "mvsu"
	elif team == "nc cent":
		return "nccu"
	elif team == "or st":
		return "orst"
	elif team == "ind":
		return "iu"
	elif team == "g'town":
		return "gtwn"
	elif team == "nc st":
		return "ncst"
	elif team == "mary":
		return "md"
	elif team == "mia fl":
		return "mia"
	elif team == "ok st":
		return "okst"
	elif team == "s clara":
		return "scu"
	elif team == "valpo":
		return "val"
	elif team == "drake":
		return "drke"
	elif team == "scar":
		return "sc"
	elif team == "uc riv":
		return "ucr"
	elif team == "wis":
		return "wisc"
	return team.replace("'", "")

def writeProps(date):
	ids = {
		"pass_td": [1000, 9525],
		"pass_yds": [1000, 9524],
		"rush_td": [1001, 9515],
		"rec_td": [1001, 9513],
		"rush_yds": [1001, 9514],
		"rec_yds": [1001, 9512],
	}

	props = {}
	if os.path.exists(f"{prefix}static/ncaafprops/dates/{date}.json"):
		with open(f"{prefix}static/ncaafprops/dates/{date}.json") as fh:
			props = json.load(fh)

	for prop in ids:
		time.sleep(0.4)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/87637/categories/{ids[prop][0]}/subcategories/{ids[prop][1]}?format=json"
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
						#print(cRow["offerSubcategory"]["name"].split(" ")[0])
						player = row["label"].replace(".", "").replace("'", "").replace("-", " ").split(" "+cRow["offerSubcategory"]["name"].split(" ")[0])[0].lower()
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

	with open(f"{prefix}static/ncaafprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(props):
	pass

def writeTranslations(date):
	with open(f"{prefix}static/ncaafreference/translations.json") as fh:
		translations = json.load(fh)

	with open(f"{prefix}static/ncaafprops/{date}.json") as fh:
		props = json.load(fh)

	shortNames = translations.values()
	for idx, team in enumerate(props):
		if team not in shortNames:
			translations[idx] = team

	with open(f"{prefix}static/ncaafreference/translations.json", "w") as fh:
		json.dump(translations, fh, indent=4)

@ncaafprops_blueprint.route('/ncaafprops')
def props_route():
	teams = request.args.get("teams") or ""
	date = request.args.get("date") or ""
	prop = request.args.get("prop") or ""
	return render_template("ncaafprops.html", teams=teams, date=date, prop=prop)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
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