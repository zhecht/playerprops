from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime

import argparse
import glob
import json
import math
import operator
import os
import subprocess
import re

altprops_blueprint = Blueprint('altprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	prefix = "/home/zhecht/playerprops/"

def convertPropTeam(team):
	if team == "ny":
		return "nyk"
	elif team == "no":
		return "nop"
	elif team == "sa":
		return "sas"
	elif team == "gs":
		return "gsw"
	return team

@altprops_blueprint.route('/getAltProps')
def getProps_route():
	date = datetime.now()
	date = str(date)[:10]

	with open(f"{prefix}static/nbaprops/customProps.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/nbaprops/dates/{date}.json") as fh:
		todaysPropData = json.load(fh)
	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/basketballreference/totals.json") as fh:
		totals = json.load(fh)
	with open(f"{prefix}static/basketballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/basketballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	data = []
	for game in schedule[date]:
		for team in game.split(" @ "):
			propTeam = convertPropTeam(team)
			for player in propData[team]:
				avgMin = 0
				if player in totals[team] and totals[team][player]["gamesPlayed"]:
					avgMin = int(totals[team][player]["min"] / totals[team][player]["gamesPlayed"])

				for prop in propData[team][player]:
					lines = propData[team][player][prop]["line"]
					odds = propData[team][player][prop]["odds"]
					isOver = True

					overOdds = underOdds = float('-inf')
					if propTeam in todaysPropData and player in todaysPropData[propTeam] and prop in todaysPropData[propTeam][player]:
						for book in todaysPropData[propTeam][player][prop]:
							if book == "line" or not todaysPropData[propTeam][player][prop][book]["over"]:
								continue

							line = todaysPropData[propTeam][player][prop]["line"][1:]
							over = todaysPropData[propTeam][player][prop][book]["over"]
							overLine = over.split(" ")[0][1:]
							overOdd = int(over.split(" ")[1][1:-1])
							if overLine == line and overOdd > overOdds:
								overOdds = overOdd

							under = todaysPropData[propTeam][player][prop][book].get("under", 0)
							if under:
								underLine = under.split(" ")[0][1:]
								underOdd = int(under.split(" ")[1][1:-1])
								if underLine == line and underOdd > underOdds:
									underOdds = underOdd

					overOdds = str(overOdds)
					underOdds = str(underOdds)
					if not overOdds.startswith("-"):
						overOdds = "+"+overOdds
					if not underOdds.startswith("-"):
						underOdds = "+"+underOdds

					avg = 0.0
					if player in totals[team] and totals[team][player]["gamesPlayed"]:
						val = 0
						if "+" in prop:
							for p in prop.split("+"):
								val += totals[team][player][p]
						elif prop in totals[team][player]:
							val = totals[team][player][prop]
						avg = round(val / totals[team][player]["gamesPlayed"], 1)
					lastAvg = 0
					if player in averages[team]:
						if "+" in prop:
							for p in prop.split("+"):
								lastAvg += averages[team][player][p]
						elif prop in averages[team][player]:
							lastAvg = averages[team][player][prop]
						lastAvg = round(lastAvg, 1)

					for idx, line in enumerate(lines):
						if idx == 1:
							isOver = False
						odd = odds[idx]
						line = float(line[1:])

						lastTotOver = lastTotGames = 0
						if player in lastYearStats[team]:
							for dt in lastYearStats[team][player]:
								minutes = lastYearStats[team][player][dt]["min"]
								if minutes:
									lastTotGames += 1
									val = 0.0
									if "+" in prop:
										for p in prop.split("+"):
											val += lastYearStats[team][player][dt][p]
									else:
										val = lastYearStats[team][player][dt][prop]
									valPerMin = float(val / minutes)
									linePerMin = line / avgMin
									if valPerMin >= linePerMin:
										lastTotOver += 1
						if lastTotGames:
							lastTotOver = round((lastTotOver / lastTotGames) * 100)

						totalOver = totalGames = 0
						last5 = []
						if avgMin:
							files = sorted(glob.glob(f"{prefix}static/basketballreference/{team}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
							for file in files:
								with open(file) as fh:
									gameStats = json.load(fh)
								if player in gameStats:
									minutes = gameStats[player]["min"]
									if minutes > 0:
										totalGames += 1
										val = 0.0
										if "+" in prop:
											for p in prop.split("+"):
												val += gameStats[player][p]
										else:
											val = gameStats[player][prop]

										if len(last5) < 7:
											last5.append(str(int(val)))
										valPerMin = float(val / minutes)
										linePerMin = float(line) / avgMin
										#if valPerMin > linePerMin:
										if val > float(line):
											totalOver += 1
						if totalGames:
							totalOver = round((totalOver / totalGames) * 100)

						data.append({
							"player": player.title(),
							"team": team.upper(),
							"game": game,
							"propType": prop,
							"isOver": isOver,
							"line": line,
							"avg": avg,
							"odds": odd,
							"overOdds": overOdds,
							"underOdds": underOdds,
							"lastAvg": lastAvg,
							"avgMin": avgMin,
							"totalOver": totalOver,
							"lastTotalOver": lastTotOver,
							"last5": ",".join(last5)
						})
	return jsonify(data)

@altprops_blueprint.route('/altprops')
def props_route():
	return render_template("altprops.html")
