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

nhlprops_blueprint = Blueprint('nhlprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def convertProp(prop):
	if prop == "sog":
		return "s"
	elif prop == "goals":
		return "g"
	elif prop == "ast":
		return "a"
	elif prop == "saves":
		return "sv"
	return prop

def getSplits(rankings, schedule, ttoi, dateArg):
	splits = {}
	for team in rankings:
		splits[team] = {}

		for key, which in zip(["savesPer60", "oppSavesAgainstPer60"], ["sv/gp", "opp sv/gp"]):
			for period in ["", "last1", "last3", "last5"]:
				if key.startswith("opp"):
					if not period:
						splits[team][key+period.capitalize()] = round((rankings[team]["tot"][which]*ttoi[team]["oppTTOI"])/(60*rankings[team]["tot"]["gp"]), 1)
					else:
						splits[team][key+period.capitalize()] = round((rankings[team][period][which]*ttoi[team]["oppTTOI"+period[0].upper()+period[-1]])/(60*rankings[team][period]["gp"]), 1)
				else:
					if not period:
						splits[team][key+period.capitalize()] = round((rankings[team]["tot"][which]*ttoi[team]["ttoi"])/(60*rankings[team]["tot"]["gp"]), 1)
					else:
						splits[team][key+period.capitalize()] = round((rankings[team][period][which]*ttoi[team]["ttoi"+period[0].upper()+period[-1]])/(60*rankings[team][period]["gp"]), 1)

	today = datetime.now()
	today = str(today)[:10]

	for team in splits:
		opps = {}
		for date in sorted(schedule, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
			if date == dateArg or datetime.strptime(date, "%Y-%m-%d") > datetime.strptime(dateArg, "%Y-%m-%d"):
				continue
			for game in schedule[date]:
				gameSp = game.split(" @ ")
				if team in gameSp:
					opp = gameSp[0] if team == gameSp[1] else gameSp[1]
					opps[date] = opp

		savesAboveAvg = []
		oppSavesAgainstAboveAvg = []
		for date in sorted(opps, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
			
			opp = opps[date]

			try:
				with open(f"{prefix}static/hockeyreference/{team}/{date}.json") as fh:
					stats = json.load(fh)
				with open(f"{prefix}static/hockeyreference/{opp}/{date}.json") as fh:
					oppStats = json.load(fh)
			except:
				continue
			
			saves = 0
			for player in stats:
				saves += stats[player].get("saves", 0)
			oppSavesAgainst = 0
			for player in oppStats:
				oppSavesAgainst += oppStats[player].get("saves", 0)
			
			if saves == 0:
				print(team,date,saves)
			if oppSavesAgainst == 0:
				print(opp,date,oppSavesAgainst)

			oppSvAgainstPer60 = splits[opp]["oppSavesAgainstPer60"]
			savesAboveAvg.append((saves / oppSvAgainstPer60) - 1)

			savesPer60 = splits[team]["savesPer60"]
			oppSavesAgainstAboveAvg.append((oppSavesAgainst / savesPer60) - 1)


		splits[team]["savesAboveAvg"] = round(sum(savesAboveAvg) / len(savesAboveAvg), 3)
		splits[team]["savesAboveAvgLast5"] = round(sum(savesAboveAvg[:5]) / len(savesAboveAvg[:5]), 3)
		splits[team]["savesAboveAvgLast3"] = round(sum(savesAboveAvg[:3]) / len(savesAboveAvg[:3]), 3)
		splits[team]["oppSavesAgainstAboveAvg"] = round(sum(oppSavesAgainstAboveAvg) / len(oppSavesAgainstAboveAvg), 3)
		splits[team]["oppSavesAgainstAboveAvgLast5"] = round(sum(oppSavesAgainstAboveAvg[:5]) / len(oppSavesAgainstAboveAvg[:5]), 3)
		splits[team]["oppSavesAgainstAboveAvgLast3"] = round(sum(oppSavesAgainstAboveAvg[:3]) / len(oppSavesAgainstAboveAvg[:3]), 3)
	return splits

def getOpportunitySplits(opportunities, slate=False):
	oppSplits = {}

	for team in opportunities:
		oppSplits[team] = {}
		for period in opportunities[team]:
			oppSplits[team][period] = opportunities[team][period]
			for stat in ["cf", "ca", "ff", "fa", "sf", "sa", "scf", "sca"]:
				oppSplits[team][period][stat+"Per60"] = round(opportunities[team][period][stat]/opportunities[team][period]["toi"]*60, 1)

		formats = {
			"cf": "corsi",
			"ff": "fenwick",
			"sf": "shots",
			"scf": "scoring",
			"ca": "corsiAgainst",
			"fa": "fenwickAgainst",
			"sa": "shotsAgainst",
			"sca": "scoringAgainst"
		}

		for stat in formats:
			display = []
			arr = ["tot", "last10", "last5", "last3"]
			if slate:
				arr.append("last1")
			for period in arr:
				pct = 0
				val = "-"
				if period not in oppSplits[team]:
					#continue
					pass
				else:
					pct = oppSplits[team][period][stat.replace('a','f')+'%']
					if "Against" in formats[stat]:
						pct = 100-pct
					val = f"{round(pct, 1)}% ({oppSplits[team][period][stat+'Per60']})"

				display.append(val)
				oppSplits[team][formats[stat]+period.title()] = val
			oppSplits[team][formats[stat]+"Format"] = " // ".join(display)
	return oppSplits

@nhlprops_blueprint.route('/getNHLProps')
def getProps_route():
	if request.args.get("teams") or request.args.get("players") or request.args.get("date"):
		teams = ""
		if request.args.get("teams"):
			teams = request.args.get("teams").lower().split(",")
		players = ""
		if request.args.get("players"):
			players = request.args.get("players").lower().split(",")
		props = getPropData(date=request.args.get("date"), playersArg=players, teams=teams)
	elif request.args.get("prop"):
		with open(f"{prefix}static/nhl/{request.args.get('prop')}.json") as fh:
			props = json.load(fh)
	else:
		with open(f"{prefix}static/betting/nhl.json") as fh:
			props = json.load(fh)
	return jsonify(props)

def writeStaticProps():
	props = getPropData()
	#teamTotals()
	writeCsvs(props)

	with open(f"{prefix}static/nhl/nhl.json", "w") as fh:
		json.dump(props, fh, indent=4)
	for prop in ["pts", "ast", "sog", "saves", "atgs", "bs"]:
		filteredProps = [p for p in props if p["propType"] == prop]
		with open(f"{prefix}static/nhl/{prop}.json", "w") as fh:
			json.dump(filteredProps, fh, indent=4)

def getLines():
	with open(f"static/nhl/fanduelLines.json") as fh:
		fd = json.load(fh)
	with open(f"static/nhl/mgm.json") as fh:
		mgm = json.load(fh)
	with open(f"static/nhl/caesars.json") as fh:
		cz = json.load(fh)
	with open(f"static/nhl/draftkings.json") as fh:
		dk = json.load(fh)

	lines = {}

	for game in fd:
		lines[game] = {}
		for prop in ["sog", "ast", "atgs", "pts", "saves"]:
			lines[game][prop] = {}
			for book, bookData in zip(["fd", "mgm", "cz", "dk"], [fd, mgm, cz, dk]):
				if game not in bookData or prop not in bookData[game]:
					continue

				lines[game][prop][book] = bookData[game][prop]

	return lines

def convertStatMuseTeam(team):
	team = team.lower()
	if team.startswith("montreal"):
		return "mtl"
	elif team.endswith("islanders"):
		return "nyi"
	elif team.endswith("rangers"):
		return "nyr"
	elif team.endswith("devils"):
		return "nj"
	elif team.endswith("kings"):
		return "la"
	elif team.endswith("blues"):
		return "stl"
	elif team.endswith("flames"):
		return "cgy"
	elif team.endswith("capitals"):
		return "wsh"
	elif team.endswith("knights"):
		return "vgk"
	elif team.endswith("jackets"):
		return "cbj"
	elif team.endswith("jets"):
		return "wpg"
	elif team.endswith("panthers"):
		return "fla"
	elif team.endswith("lightning"):
		return "tb"
	elif team.endswith("sharks"):
		return "sj"
	elif team.endswith("predators"):
		return "nsh"
	return team[:3]

def writeRankings():
	baseurl = f"https://www.statmuse.com/nhl/ask/"

	rankings = {}
	shortIds = ["tot", "last1", "last3", "last5", "tot", "last1", "last3", "last5"]
	urls = ["nhl-team-saves-per-game-this-season", "nhl-team-saves-per-game-last-1-games", "nhl-team-saves-per-game-last-3-games", "nhl-team-saves-per-game-last-5-games", "nhl-team-saves-allowed-per-game-this-season", "nhl-team-saves-allowed-per-game-last-1-games", "nhl-team-saves-allowed-per-game-last-3-games", "nhl-team-saves-allowed-per-game-last-5-games"]
	for timePeriod, url in zip(shortIds, urls):
		outfile = "outnhl"
		time.sleep(0.3)
		call(["curl", baseurl+url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		headers = []
		for hdr in soup.find_all("th"):
			headers.append(hdr.text.lower().strip())

		for row in soup.find("tbody").find_all("tr"):
			team = convertStatMuseTeam(row.find("td").text.lower().strip())
			if team not in rankings:
				rankings[team] = {}
			rankings[team][timePeriod] = {}
			for td, hdr in zip(row.find_all("td")[2:], headers[2:]):
				rankings[team][timePeriod][hdr] = td.text.strip()

	with open(f"static/nhl/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)

def getPropData(date = None, playersArg = "", teams = ""):
	res = []

	if not date:
		date = datetime.now()
		date = str(date)[:10]

	yesterday = str(datetime.now() - timedelta(days=1))[:10]

	#propData = getLines()
	with open(f"static/nhl/draftkings.json") as fh:
		dkData = json.load(fh)
	with open(f"static/nhl/fanduelLines.json") as fh:
		fdData = json.load(fh)
	with open(f"static/nhl/kambi.json") as fh:
		kambiData = json.load(fh)

	propData = {}
	for game in dkData:
		propData[game] = {}
		for prop in ["saves", "ast", "pts", "sog"]:
			if prop not in dkData[game]:
				continue
			for player in dkData[game][prop]:
				if player not in propData[game]:
					propData[game][player] = {}
				line = list(dkData[game][prop][player].keys())[0]
				over = dkData[game][prop][player][line].split("/")[0]
				under = "0"
				try:
					under = dkData[game][prop][player][line].split("/")[1]
				except:
					pass
				try:
					fd = fdData[game][prop][player][line]
				except:
					fd = "0"
				try:
					kambi = kambiData[game][prop][player][line]
				except:
					kambi = "0"
				lowestLine = int(over)
				lowestBook = "DK"
				if fd != "0" and int(fd.split("/")[0]) > lowestLine:
					lowestLine = int(fd.split("/")[0])
					lowestBook = "FD"
				if kambi != "0" and int(kambi.split("/")[0]) > lowestLine:
					lowestLine = int(kambi.split("/")[0])
					lowestBook = "BR"
				implied = 0
				if lowestLine > 0:
					implied = 100 / (lowestLine + 100)
				else:
					implied = -1*lowestLine / (-1*lowestLine + 100)
				implied *= 100
				propData[game][player][prop] = {
					"line": line,
					"over": over,
					"under": under,
					"dk": dkData[game][prop][player][line],
					"fd": fd,
					"kambi": kambi,
					"lowest": lowestLine,
					"lowestBook": lowestBook,
					"implied": implied
				}


	with open(f"{prefix}static/nhl/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/hockeyreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/hockeyreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/hockeyreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/hockeyreference/ttoi.json") as fh:
		ttoi = json.load(fh)
	with open(f"static/nhl/opportunities.json") as fh:
		opportunities = json.load(fh)
	with open(f"static/nhl/expectedGoalies.json") as fh:
		expectedGoalies = json.load(fh)
	with open(f"{prefix}static/hockeyreference/trades.json") as fh:
		trades = json.load(fh)

	opportunitySplits = getOpportunitySplits(opportunities)

	gameLines = {}
	if os.path.exists(f"{prefix}static/nhlprops/lines/{date}.json"):
		with open(f"{prefix}static/nhlprops/lines/{date}.json") as fh:
			gameLines = json.load(fh)
	with open(f"static/nhl/goalies.json") as fh:
		goalies = json.load(fh)
	with open(f"static/nhl/expected.json") as fh:
		expected = json.load(fh)
	with open(f"static/nhl/lineups.json") as fh:
		lineups = json.load(fh)

	#goalieLines(propData)
	#splits = getSplits(rankings, schedule, ttoi, date)

	allGoalies = {}
	for game in propData:
		teamSp = game.split(" @ ")
		for player in propData[game]:
			if "saves" not in propData[game][player]:
				continue
			shortFirstName = player.split(" ")[0][0]
			restName = " ".join(player.title().split(" ")[1:])
			name = f"{shortFirstName.upper()}. {restName.replace('-', ' ')}"
			if name in stats[teamSp[0]]:
				team = teamSp[0]
			else:
				team = teamSp[1]
			allGoalies[team] = player

	props = []
	for game in propData:
		for player in propData[game]:
			shortFirstName = player.split(" ")[0][0]
			restName = " ".join(player.title().split(" ")[1:])
			name = f"{shortFirstName.upper()}. {restName.replace('-', ' ')}"

			team = opp = ""
			gameSp = game.split(" @ ")
			team1, team2 = gameSp[0], gameSp[1]
			if name in stats[team1] and name in stats[team2]:
				if player in trades:
					if team1 == trades[player]:
						team = team1
						opp = team2
					else:
						team = team1
						opp = team2
				elif stats[team1][name]["gamesPlayed"] > stats[team2][name]["gamesPlayed"]:
					team = team1
					opp = team2	
				else:
					team = team2
					opp = team1
			elif name in stats[team1]:
				team = team1
				opp = team2
			elif name in stats[team2]:
				team = team2
				opp = team1
			else:
				continue

			if teams and team not in teams:
				continue

			if playersArg and player not in playersArg:
				continue

			beforeTradeTeam = ""
			if player in trades:
				beforeTradeTeam = trades[player]

			avgMin = 0
			if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
				if beforeTradeTeam:
					avgMin = int((stats[team][name]["toi"] + stats[beforeTradeTeam][name]["toi"]) / (stats[team][name]["gamesPlayed"] + stats[beforeTradeTeam][name]["gamesPlayed"]))
				else:
					avgMin = int(stats[team][name]["toi"] / stats[team][name]["gamesPlayed"])

			for prop in propData[game][player]:
				convertedProp = convertProp(prop)
				line = float(propData[game][player][prop]["line"])
				avg = 0

				if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
					gamesPlayed = stats[team][name]["gamesPlayed"]
					val = 0
					if convertedProp == "pts":
						val = stats[team][name]["g"] + stats[team][name]["a"]
					elif convertedProp in stats[team][name]:
						val = stats[team][name][convertedProp]

					if beforeTradeTeam:
						gamesPlayed += stats[beforeTradeTeam][name]["gamesPlayed"]
						if convertedProp == "pts":
							val += stats[beforeTradeTeam][name]["g"] + stats[beforeTradeTeam][name]["a"]
						elif convertedProp in stats[beforeTradeTeam][name]:
							val += stats[beforeTradeTeam][name][convertedProp]

					avg = round(val / gamesPlayed, 2)

				overOdds = propData[game][player][prop]["over"]
				underOdds = propData[game][player][prop]["under"]

				lastAvg = lastAvgMin = 0
				proj = 0
				lastYearTeam = team
				if beforeTradeTeam and name in averages[beforeTradeTeam]:
					lastYearTeam = beforeTradeTeam
				if name in averages[lastYearTeam] and averages[lastYearTeam][name]:
					lastAvgMin = averages[lastYearTeam][name]["toi/g"]
					if convertedProp in averages[lastYearTeam][name]:
						lastAvg = averages[lastYearTeam][name][convertedProp]
					lastAvg = lastAvg / averages[lastYearTeam][name]["gamesPlayed"]
					proj = lastAvg / lastAvgMin
					lastAvg = round(lastAvg, 2)

				diff = diffAvg = 0
				if avg and line:
					diffAvg = round((avg / float(line) - 1), 2)
				if lastAvg and line:
					diff = round((lastAvg / float(line) - 1), 2)

				lastTotalOver = lastTotalGames = 0
				lastYearTeam = team
				if beforeTradeTeam and name in lastYearStats[beforeTradeTeam]:
					lastYearTeam = beforeTradeTeam
				if line and avgMin and name in lastYearStats[lastYearTeam] and lastYearStats[lastYearTeam][name]:
					for d in lastYearStats[lastYearTeam][name]:
						minutes = lastYearStats[lastYearTeam][name][d]["toi/g"]
						if minutes > 0 and convertedProp in lastYearStats[lastYearTeam][name][d]:
							lastTotalGames += 1
							val = lastYearStats[lastYearTeam][name][d][convertedProp]
							valPerMin = float(val / minutes)
							linePerMin = float(line) / avgMin
							if valPerMin > linePerMin:
								lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				winLossSplits = [[],[]]
				awayHomeSplits = [[],[]]
				totalOver = totalOverLast5 = totalOverLast15 = totalGames = 0
				last5 = []
				lastAll = []
				last5PlusMinus = []
				prevMatchup = []
				hit = playedYesterday = False
				if line and avgMin:
					files = glob.glob(f"{prefix}static/hockeyreference/{team}/*.json")
					if beforeTradeTeam:
						files.extend(glob.glob(f"{prefix}static/hockeyreference/{beforeTradeTeam}/*.json"))
					files = sorted(files, key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
					for file in files:
						chkDate = file.split("/")[-1].replace(".json","")
						currTeam = file.split("/")[-2]
						with open(file) as fh:
							gameStats = json.load(fh)

						if chkDate == yesterday:
							playedYesterday = True

						if name in gameStats:
							minutes = gameStats[name]["toi"]
							if minutes > 0:
								val = 0.0
								if convertedProp == "pts":
									val = gameStats[name]["a"] + gameStats[name]["g"]
								elif convertedProp in gameStats[name]:
									val = gameStats[name][convertedProp]

								pastOpp = ""
								teamIsAway = False
								for g in schedule[chkDate]:
									gameSp = g.split(" @ ")
									if currTeam in gameSp:
										if currTeam == gameSp[0]:
											teamIsAway = True
											pastOpp = gameSp[1]
										else:
											pastOpp = gameSp[0]
										break

								if pastOpp == opp:
									prevMatchup.append(f"{chkDate} {val} {prop}")

								if chkDate == date:
									if val > float(line):
										hit = True

								lastAll.append(str(int(val)))

								if float(val) > float(line):
									if chkDate != date:
										totalOver += 1
										if len(last5) < 5:
											totalOverLast5 += 1
										if len(lastAll) < 15:
											totalOverLast15 += 1

								if len(last5) < 10:
									v = str(int(val))
									if chkDate == date:
										v = f"'{v}'"
										last5.append(v)
										continue
									last5PlusMinus.append(gameStats[name].get("+/-", 0))
									last5.append(v)

								if chkDate == date or datetime.strptime(chkDate, "%Y-%m-%d") > datetime.strptime(date, "%Y-%m-%d"):
									continue

								totalGames += 1
								valPerMin = float(val / minutes)
								teamScore = scores[chkDate][currTeam]
								oppScore = scores[chkDate][pastOpp]
								winLossVal = val
								if False:
									winLossVal = valPerMin
									if prop == "saves":
										winLossVal *= 60
									else:
										winLossVal *= avgMin

								if teamIsAway:
									awayHomeSplits[0].append(val)
								else:
									awayHomeSplits[1].append(val)

								if teamScore > oppScore:
									winLossSplits[0].append(winLossVal)
								elif teamScore < oppScore:
									winLossSplits[1].append(winLossVal)

								linePerMin = float(line) / avgMin


				if totalGames:
					totalOver = round((totalOver / totalGames) * 100)
					
					realLast5 = [x for x in last5 if "'" not in x]
					last5Size = len(realLast5) if len(realLast5) < 5 else 5
					last15Size = len(lastAll) if len(lastAll) < 15 else 15
					if last5Size:
						totalOverLast5 = round((totalOverLast5 / last5Size) * 100)
						totalOverLast15 = round((totalOverLast15 / last15Size) * 100)

				last5PlusMinus = sum(last5PlusMinus)

				diffAbs = 0
				if avgMin:
					proj = round(proj*float(avgMin), 1)
					if line:
						diffAbs = round((proj / float(line) - 1), 2)
					else:
						diffAbs = diffAvg

				winSplitAvg = lossSplitAvg = 0
				if len(winLossSplits[0]):
					arr = [x for x in winLossSplits[0] if x > line]
					winSplitAvg = round(len(arr) * 100 / len(winLossSplits[0]))
				if len(winLossSplits[1]):
					arr = [x for x in winLossSplits[1] if x > line]
					lossSplitAvg = round(len(arr) * 100 / len(winLossSplits[1]))
				winLoss = f"{winSplitAvg}% - {lossSplitAvg}%"

				awaySplitAvg = homeSplitAvg = 0
				if len(awayHomeSplits[0]):
					arr = [x for x in awayHomeSplits[0] if x > line]
					awaySplitAvg = round(len(arr) * 100 / len(awayHomeSplits[0]))
				if len(awayHomeSplits[1]):
					arr = [x for x in awayHomeSplits[1] if x > line]
					homeSplitAvg = round(len(arr) * 100 / len(awayHomeSplits[1]))
				awayHome = f"{awaySplitAvg}% - {homeSplitAvg}%"

				oppOver = oppOverTot = 0
				if prop == "saves":
					for dt in schedule:
						for g in schedule[dt]:
							gameSp = g.split(" @ ")
							if opp not in gameSp:
								continue
							t = gameSp[0] if opp == gameSp[1] else gameSp[1]
							file = f"{prefix}static/hockeyreference/{t}/{dt}.json"
							if not os.path.exists(file):
								continue
							with open(file) as fh:
								gameStats = json.load(fh)
							oppOverTot += 1
							totSaves = 0
							for p in gameStats:
								totSaves += gameStats[p].get("saves", 0)
							if totSaves > float(line):
								oppOver += 1
					oppOver = round(oppOver * 100 / oppOverTot)

				teamOver = teamOverTot = 0
				if prop == "saves":
					files = sorted(glob.glob(f"{prefix}static/hockeyreference/{team}/*.json"))
					prevMatchup = []
					for file in files:
						with open(file) as fh:
							gameStats = json.load(fh)
						chkDate = file.split("/")[-1].replace(".json","")
						teamOverTot += 1
						totSaves = 0
						for p in gameStats:
							totSaves += gameStats[p].get("sv", 0)
						if totSaves > float(line):
							teamOver += 1

						g = [x for x in schedule[chkDate] if team in x.split(" @ ") and opp in x.split(" @ ")]
						if chkDate != date and len(g):
							prevMatchup.append(f"{chkDate} {g[0]} {totSaves} sv")
					teamOver = round(teamOver * 100 / teamOverTot)

				gameLine = 0
				if game in dkData:
					gameOdds = dkData[game]["ml"].split("/")
					if team == game.split(" @ ")[0]:
						gameLine = gameOdds[0]
					else:
						gameLine = gameOdds[1]

				savesAboveExp = gsaa = "-"
				goalieStatus = "expected"
				if prop == "saves":
					p = player.replace("-", " ")
					if p not in expected:
						continue
					savesAboveExp = round((float(expected[p]["xgoals"])-float(expected[p]["goals"]))*60*60 / float(expected[p]["icetime"]), 3)
					try:
						if "tot" in goalies and p in goalies["tot"]:
							gsaa = float(goalies["tot"][p]["gsaa"])
						else:
							gsaa = float(goalies[team][p]["gsaa"])
					except:
						gsaa = "-"
				else:
					if opp in allGoalies:
						goalie = allGoalies[opp]
						if goalie in expected:
							savesAboveExp = round((float(expected[goalie]["xgoals"])-float(expected[goalie]["goals"]))*60*60 / float(expected[goalie]["icetime"]), 3)
						else:
							savesAboveExp = "-"
						try:
							if "tot" in goalies and goalie in goalies["tot"]:
								gsaa = float(goalies["tot"][goalie]["gsaa"])
							else:
								gsaa = float(goalies[opp][goalie]["gsaa"])
						except:
							gsaa = "-"
					elif opp in expectedGoalies["confirmed"] or expectedGoalies["expected"]:
						if opp in expectedGoalies["confirmed"]:
							goalieStatus = "confirmed"

						if opp not in expectedGoalies[goalieStatus]:
							continue
						goalie = expectedGoalies[goalieStatus][opp]
						if goalie in expected:
							savesAboveExp = round((float(expected[goalie]["xgoals"])-float(expected[goalie]["goals"]))*60*60 / float(expected[goalie]["icetime"]), 3)
						else:
							savesAboveExp = "-"
						try:
							if "tot" in goalies and goalie in goalies["tot"]:
								gsaa = float(goalies["tot"][goalie]["gsaa"])
							else:
								gsaa = float(goalies[opp][goalie]["gsaa"])
						except:
							gsaa = "-"

				plusMinus = int(stats[team][name].get("+/-", 0))
				if plusMinus > 0:
					plusMinus = f"+{plusMinus}"
				if last5PlusMinus > 0:
					last5PlusMinus = f"+{last5PlusMinus}"

				ppLine = ""
				if team in lineups and player in lineups[team]["power play #1"]:
					ppLine = "PP1"
				elif team in lineups and player in lineups[team]["power play #2"]:
					ppLine = "PP2"

				props.append({
					"player": player.title(),
					"team": team.upper(),
					"opponent": opp.upper(),
					"propType": prop,
					"line": line or "-",
					"ppLine": ppLine,
					"avg": avg,
					"hit": hit,
					"diffAvg": diffAvg,
					"diffAbs": abs(diffAbs),
					"lastAvg": lastAvg,
					"diff": diff,
					"avgMin": avgMin,
					"proj": proj,
					"lastAvgMin": lastAvgMin,
					"oppOver": oppOver,
					"teamOver": teamOver,
					"gameLine": gameLine,
					"+/-": plusMinus,
					"L5_+/-": last5PlusMinus,
					"prevMatchup": " ".join(prevMatchup),
					"winLossSplits": winLoss,
					"awayHome": "A" if team == game.split(" @ ")[0] else "H",
					"playedYesterday": "Y" if playedYesterday else "N",
					"awayHomeSplits": awayHome,
					"savesAboveExp": savesAboveExp,
					"gsaa": gsaa,
					"corsi": opportunitySplits[team]["corsiFormat"],
					"fenwick": opportunitySplits[team]["fenwickFormat"],
					"shots": opportunitySplits[team]["shotsFormat"],
					"scoring": opportunitySplits[team]["scoringFormat"],
					"corsiAgainst": opportunitySplits[team]["corsiAgainstFormat"],
					"fenwickAgainst": opportunitySplits[team]["fenwickAgainstFormat"],
					"shotsAgainst": opportunitySplits[team]["shotsAgainstFormat"],
					"scoringAgainst": opportunitySplits[team]["scoringAgainstFormat"],
					"oppCorsi": opportunitySplits[opp]["corsiFormat"],
					"oppFenwick": opportunitySplits[opp]["fenwickFormat"],
					"oppShots": opportunitySplits[opp]["shotsFormat"],
					"oppScoring": opportunitySplits[opp]["scoringFormat"],
					"oppCorsiAgainst": opportunitySplits[opp]["corsiAgainstFormat"],
					"oppFenwickAgainst": opportunitySplits[opp]["fenwickAgainstFormat"],
					"oppShotsAgainst": opportunitySplits[opp]["shotsAgainstFormat"],
					"oppScoringAgainst": opportunitySplits[opp]["scoringAgainstFormat"],


					#"savesPerGame": round(rankings[team]["tot"]["SV/GP"], 1),
					#"savesPerGameLast1": round(rankings[team]["last1"]["SV/GP"], 1),
					#"savesPerGameLast3": round(rankings[team]["last3"]["SV/GP"], 1),
					#"savesPerGameLast5": round(rankings[team]["last5"]["SV/GP"], 1),
					#"shotsPerGame": round(rankings[team]["tot"]["S/GP"], 1),
					#"shotsPerGameLast5": round(rankings[team]["last5"]["S/GP"], 1),
					#"shotsAgainstPerGame": round(rankings[team]["tot"]["SA/GP"], 1),
					#"shotsAgainstPerGameLast5": round(rankings[team]["last5"]["SA/GP"], 1),
					#"oppShotsAgainstPerGame": round(rankings[opp]["tot"]["SA/GP"], 1),
					#"oppShotsAgainstPerGameLast5": round(rankings[opp]["last5"]["SA/GP"], 1),

					#"oppSavesAgainstPer60": splits[opp]["oppSavesAgainstPer60"],
					#"oppSavesAgainstPer60Last1": splits[opp]["oppSavesAgainstPer60Last1"],
					#"oppSavesAgainstPer60Last3": splits[opp]["oppSavesAgainstPer60Last3"],
					#"oppSavesAgainstPer60Last5": splits[opp]["oppSavesAgainstPer60Last5"],
					#"savesProj": round(splits[team]["savesPer60"]+splits[team]["savesPer60"]*splits[opp]["oppSavesAgainstAboveAvg"], 1),
					#"savesProjLast5": round(splits[team]["savesPer60Last5"]+splits[team]["savesPer60Last5"]*splits[opp]["oppSavesAgainstAboveAvgLast5"], 1),
					#"savesProjLast3": round(splits[team]["savesPer60Last3"]+splits[team]["savesPer60Last3"]*splits[opp]["oppSavesAgainstAboveAvgLast3"], 1),
					#"oppSavesAgainstProj": round(splits[opp]["oppSavesAgainstPer60"]+splits[opp]["oppSavesAgainstPer60"]*splits[team]["savesAboveAvg"], 1),
					#"oppSavesAgainstProjLast5": round(splits[opp]["oppSavesAgainstPer60Last5"]+splits[opp]["oppSavesAgainstPer60Last5"]*splits[team]["savesAboveAvgLast5"], 1),
					#"oppSavesAgainstProjLast3": round(splits[opp]["oppSavesAgainstPer60Last3"]+splits[opp]["oppSavesAgainstPer60Last3"]*splits[team]["savesAboveAvgLast3"], 1),
					"totalOver": totalOver,
					"totalOverLast5": totalOverLast5,
					"totalOverLast15": totalOverLast15,
					"lastTotalOver": lastTotalOver,
					"last5": ",".join(last5),
					"fd": propData[game][player][prop]["fd"],
					"dk": propData[game][player][prop]["dk"],
					"kambi": propData[game][player][prop]["kambi"],
					"lowest": f"{propData[game][player][prop]['lowest']} {propData[game][player][prop]['lowestBook']}",
					"implied": propData[game][player][prop]["implied"],
					"overOdds": overOdds,
					"underOdds": underOdds,
					"overUnder": f"{overOdds} / {underOdds}"
				})
	return props

@nhlprops_blueprint.route('/nhlprops')
def props_route():
	prop = alt = date = teams = players = ""
	if request.args.get("prop"):
		prop = request.args.get("prop")
	if request.args.get("alt"):
		alt = request.args.get("alt")
	if request.args.get("date"):
		date = request.args.get("date")
		if date == "yesterday":
			date = str(datetime.now() - timedelta(days=1))[:10]
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("players"):
		players = request.args.get("players")

	# locks
	bets = []
	# singles
	bets.extend([])
	# meh
	bets.extend([])
	# goalies
	bets.extend([])
	bets = ",".join(bets)
	return render_template("nhlprops.html", prop=prop, alt=alt, date=date, teams=teams, bets=bets, players=players)

def getTotals(schedule, scores, lines):
	totals = {}
	dates = sorted(schedule.keys(), key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True)
	for date in dates:
		for game in schedule[date]:
			gameSp = game.split(" @ ")
			for idx, team in enumerate(gameSp):
				opp = gameSp[0] if idx == 1 else gameSp[1]

				if date not in scores or team not in scores[date]:
					continue

				if team not in totals:
					totals[team] = {"away": 0, "home": 0, "wins": 0, "loss": 0, "gpg": 0, "gpga": 0, "games": 0, "overs": [], "ttOvers": [], "opp_ttOvers": [], "gpgWins": 0, "gpgLoss": 0, "gpgAway": 0, "gpgHome": 0, "gpgaWins": 0, "gpgaLoss": 0, "gpgaAway": 0, "gpgaHome": 0}
				totals[team]["games"] += 1
				totals[team]["gpg"] += scores[date][team]
				totals[team]["gpga"] += scores[date][opp]
				if scores[date][team] > scores[date][opp]:
					totals[team]["wins"] += 1
					totals[team]["gpgWins"] += scores[date][team]
					totals[team]["gpgaWins"] += scores[date][opp]
				elif scores[date][team] < scores[date][opp]:
					totals[team]["loss"] += 1
					totals[team]["gpgLoss"] += scores[date][team]
					totals[team]["gpgaLoss"] += scores[date][opp]

				if idx == 0:
					totals[team]["away"] += 1
					totals[team]["gpgAway"] += scores[date][team]
					totals[team]["gpgaAway"] += scores[date][opp]
				else:
					totals[team]["home"] += 1
					totals[team]["gpgHome"] += scores[date][team]
					totals[team]["gpgaHome"] += scores[date][opp]
				totals[team]["ttOvers"].append(str(scores[date][team]))
				totals[team]["opp_ttOvers"].append(str(scores[date][opp]))
				totals[team]["overs"].append(str(scores[date][team] + scores[date][opp]))
	return totals

@nhlprops_blueprint.route('/getNHLSlate')
def getSlate_route():

	if request.args.get("date") or request.args.get("teams"):
		res = getSlateData(date=request.args.get("date"), teams=request.args.get("teams"))
	else:
		res = getSlateData()

	return jsonify(res)

def getSlateData(date = None, teams=""):
	res = []

	if teams:
		teams = teams.lower().split(",")

	if not date:
		date = datetime.now()
		date = str(date)[:10]

	with open(f"static/nhl/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/hockeyreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/hockeyreference/ttoi.json") as fh:
		ttoi = json.load(fh)
	with open(f"static/nhl/opportunities.json") as fh:
		opportunities = json.load(fh)
	with open(f"static/nhl/expectedGoalies.json") as fh:
		expectedGoalies = json.load(fh)
	with open(f"static/nhl/goalies.json") as fh:
		goalies = json.load(fh)
	with open(f"static/nhl/expected.json") as fh:
		expected = json.load(fh)
	with open(f"{prefix}static/nhlprops/lines/{date}.json") as fh:
		gameLines = json.load(fh)
	with open(f"{prefix}static/nhlprops/tt.json") as fh:
		tt = json.load(fh)


	#splits = getSplits(rankings, schedule, ttoi, date)
	opportunitySplits = getOpportunitySplits(opportunities, slate=True)
	totals = getTotals(schedule, scores, gameLines)

	for game in schedule[date]:
		gameSp = game.split(" @ ")
		isAway = True
		for idx, team in enumerate(gameSp):
			opp = gameSp[0] if idx == 1 else gameSp[1]
			if idx == 1:
				isAway = False

			puckline = gameLines[game]["line"]["line"]
			totalLine = gameLines[game]["total"]["line"]
			if idx == 1:
				puckline *= -1

			if puckline > 0:
				puckline = f"+{puckline}"

			goalie = ""
			rbs = svPct = qs = ""
			goalieStatus = "expected"
			goalie = savesAboveExp = gsaa = gaa = goalieRecord = "-"
			if team in expectedGoalies["expected"] or team in expectedGoalies["confirmed"]:

				if team in expectedGoalies["confirmed"]:
					goalieStatus = "confirmed"
				goalie = expectedGoalies[goalieStatus][team].replace("-", " ")
				if goalie in expected:
					savesAboveExp = round((float(expected[goalie]["xgoals"])-float(expected[goalie]["goals"]))*60*60 / float(expected[goalie]["icetime"]), 3)
				else:
					savesAboveExp = "-"

				goalieTeam = team
				if "tot" in goalies and goalie in goalies["tot"]:
					goalieTeam = "tot"
				try:
					gsaa = float(goalies[goalieTeam][goalie]["gsaa"])
					gaa = float(goalies[goalieTeam][goalie]["gaa"])
					goalieRecord = f"{goalies[goalieTeam][goalie]['w']}W-{goalies[goalieTeam][goalie]['l']}L"
					qs = f"{round(goalies[goalieTeam][goalie]['qs%'] * 100, 1)}%"
					rbs = goalies[goalieTeam][goalie]["rbs"]
					svPct = f"{round(goalies[goalieTeam][goalie]['sv%'] * 100, 1)}%"
				except:
					pass

			goalieOvers = []
			goalieWinLossSplits = [0,0]
			if goalie:
				goalieName = f"{goalie[0].upper()}. {goalie.split(' ')[-1].title()}"
				files = sorted(glob.glob(f"{prefix}static/hockeyreference/{team}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
				for file in files:
					chkDate = file.split("/")[-1].replace(".json","")
					with open(file) as fh:
						gameStats = json.load(fh)
					currGame = [g for g in schedule[chkDate] if team in g.split(" @ ")][0]
					away = currGame.split(" @ ")[0]
					home = currGame.split(" @ ")[1]
					if goalieName in gameStats:
						minutes = gameStats[goalieName]["toi"]
						score1 = scores[chkDate][away]
						score2 = scores[chkDate][home]
						if score1+score2 == totalLine:
							continue
						goalieOvers.append(score1+score2)
						teamScore = score1 if team == away else score2
						oppScore = score2 if team == away else score1
						winLossIdx = 0 if teamScore > oppScore else 1
						if (team == away and not isAway) or (team == home and isAway):
							continue
						if minutes < 40:
							continue
						goalieWinLossSplits[winLossIdx] += 1

			goalieOver = ""
			if goalieOvers:
				goalieOver = f"{round(len([x for x in goalieOvers if x > totalLine]) * 100 / len(goalieOvers))}% SZN • {round(len([x for x in goalieOvers[:15] if x > totalLine]) * 100 / len(goalieOvers[:15]))}% L15 • {round(len([x for x in goalieOvers[:5] if x > totalLine]) * 100 / len(goalieOvers[:5]))}% L5 • {round(len([x for x in goalieOvers[:3] if x > totalLine]) * 100 / len(goalieOvers[:3]))}% L3"

			puckline = f"{puckline} ({gameLines[game]['line']['odds'].split(',')[idx]})"
			moneyline = gameLines[game]["moneyline"]["odds"].split(",")[idx]
			total = f"{'o' if idx == 0 else 'u'}{gameLines[game]['total']['line']} ({gameLines[game]['total']['odds'].split(',')[idx]})"

			prevMatchup = []
			lastPlayed = ""
			for dt in schedule:
				if dt == date or datetime.strptime(dt, "%Y-%m-%d") > datetime.strptime(date, "%Y-%m-%d"):
					continue
				for g in schedule[dt]:
					gSp = g.split(" @ ")
					if team in gSp:
						lastPlayed = dt
					if gSp[0] in scores[dt] and team in gSp and opp in gSp:
						score1 = scores[dt][gSp[0]]
						score2 = scores[dt][gSp[1]]
						wonLost = "Won"
						currGoalie = []
						score = f"{score1}-{score2}"
						file = f"{prefix}static/hockeyreference/{team}/{dt}.json"
						with open(file) as fh:
							gameStats = json.load(fh)
						for p in gameStats:
							if "saves" in gameStats[p]:
								currGoalie.append(p)
						if score2 > score1:
							score = f"{score2}-{score1}"
							if team == gSp[0]:
								wonLost = "Lost"
						elif team == gSp[1]:
							wonLost = "Lost"
						prevMatchup.append(f"{dt} {wonLost} {score} ({','.join(currGoalie)})")

			teamOver = f"{round(len([x for x in totals[team]['overs'] if int(x) > totalLine]) * 100 / len(totals[team]['overs']))}% // {round(len([x for x in totals[team]['overs'][:10] if int(x) > totalLine]) * 100 / len(totals[team]['overs'][:10]))}% // {round(len([x for x in totals[team]['overs'][:5] if int(x) > totalLine]) * 100 / len(totals[team]['overs'][:5]))}% // {round(len([x for x in totals[team]['overs'][:3] if int(x) > totalLine]) * 100 / len(totals[team]['overs'][:3]))}%"
			teamOverShort = f"{round(len([x for x in totals[team]['overs'] if int(x) > totalLine]) * 100 / len(totals[team]['overs']))}% SZN • {round(len([x for x in totals[team]['overs'][:15] if int(x) > totalLine]) * 100 / len(totals[team]['overs'][:15]))}% L15 • {round(len([x for x in totals[team]['overs'][:5] if int(x) > totalLine]) * 100 / len(totals[team]['overs'][:5]))}% L5 • {round(len([x for x in totals[team]['overs'][:3] if int(x) > totalLine]) * 100 / len(totals[team]['overs'][:3]))}% L3"
			teamOverSzn = f"{round(len([x for x in totals[team]['overs'] if int(x) > totalLine]) * 100 / len(totals[team]['overs']))}%"

			res.append({
				"game": game,
				"team": team,
				"opp": opp,
				"awayHome": "A" if isAway else "H",
				"prevMatchup": " • ".join(prevMatchup),
				"prevMatchupList": prevMatchup,
				"lastPlayed": lastPlayed,
				"puckline": puckline,
				"moneylineOdds": moneyline,
				"tt": tt[team]["line"],
				"ttOU": f"{tt[team]['overOdds']} / {tt[team]['underOdds']}",
				"total": total,
				"gsaa": gsaa,
				"gaa": gaa,
				"qs": qs,
				"rbs": rbs,
				"svPct": svPct,
				"savesAboveExp": savesAboveExp,
				"goalie": goalie,
				"goalieStatus": True if goalieStatus == "confirmed" else False,
				"goalieRecord": goalieRecord,
				"goalieSplits": f"{goalieWinLossSplits[0]}-{goalieWinLossSplits[1]}",
				"gpg": round(totals[team]["gpg"] / totals[team]["games"], 1),
				"gpgSplits": f"{round(totals[team]['gpgAway'] / totals[team]['away'], 1)} - {round(totals[team]['gpgHome'] / totals[team]['home'], 1)}",
				"ttOvers": ",".join(totals[team]["ttOvers"][:10]),
				"gpga": round(totals[team]["gpga"] / totals[team]["games"], 1),
				"gpgaSplits": f"{round(totals[team]['gpgaAway'] / totals[team]['away'], 1)} - {round(totals[team]['gpgaHome'] / totals[team]['home'], 1)}",
				"opp_ttOvers": ",".join(totals[team]["opp_ttOvers"][:10]),
				"oversAvg": round(sum([int(x) for x in totals[team]["overs"]]) / len(totals[team]["overs"]), 1),
				"overs": totals[team]["overs"][:20],
				"oversL10": totals[team]["overs"][:10],
				"teamOver": teamOver,
				"teamOverShort": teamOverShort,
				"teamOverSzn": teamOverSzn,
				"goalieOver": goalieOver,
				"corsi": opportunitySplits[team]["corsiFormat"],
				"corsiTot": opportunitySplits[team]["corsiTot"],
				"fenwick": opportunitySplits[team]["fenwickFormat"],
				"fenwickTot": opportunitySplits[team]["fenwickTot"],
				"shotsTot": opportunitySplits[team]["shotsTot"],
				"shotsLast5": opportunitySplits[team]["shotsLast5"],
				"shotsAgainstTot": opportunitySplits[team]["shotsAgainstTot"],
				"shots": opportunitySplits[team]["shotsFormat"],
				"scoring": opportunitySplits[team]["scoringFormat"],
				"scoringTot": opportunitySplits[team]["scoringTot"],
				"scoringLast5": opportunitySplits[team]["scoringLast5"],
				"scoringAgainstTot": opportunitySplits[team]["scoringAgainstTot"],
				"corsiAgainst": opportunitySplits[team]["corsiAgainstFormat"],
				"fenwickAgainst": opportunitySplits[team]["fenwickAgainstFormat"],
				"shotsAgainst": opportunitySplits[team]["shotsAgainstFormat"],
				"scoringAgainst": opportunitySplits[team]["scoringAgainstFormat"],
				"oppCorsi": opportunitySplits[opp]["corsiFormat"],
				"oppFenwick": opportunitySplits[opp]["fenwickFormat"],
				"oppShots": opportunitySplits[opp]["shotsFormat"],
				"oppScoring": opportunitySplits[opp]["scoringFormat"],
				"oppCorsiAgainst": opportunitySplits[opp]["corsiAgainstFormat"],
				"oppFenwickAgainst": opportunitySplits[opp]["fenwickAgainstFormat"],
				"oppShotsAgainst": opportunitySplits[opp]["shotsAgainstFormat"],
				"oppScoringAgainst": opportunitySplits[opp]["scoringAgainstFormat"],
			})

	return res

@nhlprops_blueprint.route('/slate')
def slate_route():
	data = getSlateData()
	grouped = {}
	for row in data:
		if row["game"] not in grouped:
			grouped[row["game"]] = {}
		grouped[row["game"]][row["awayHome"]] = row

	return render_template("slate.html", data=grouped)

@nhlprops_blueprint.route('/slatenhl')
def slatenhl_route():
	prop = alt = date = teams = players = collapse = ""
	if request.args.get("date"):
		date = request.args.get("date")
		if date == "yesterday":
			date = str(datetime.now() - timedelta(days=1))[:10]
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("collapse"):
		collapse = request.args.get("collapse")

	return render_template("slatenhl.html", date=date, teams=teams, collapse=collapse)

def teamTotals():
	today = datetime.now()
	today = str(today)[:10]

	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/hockeyreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/nhlprops/lines/{today}.json") as fh:
		lines = json.load(fh)

	totals = {}
	dates = sorted(schedule.keys(), key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True)
	for date in dates:
		for game in schedule[date]:
			gameSp = game.split(" @ ")
			for idx, team in enumerate(gameSp):
				opp = gameSp[0] if idx == 1 else gameSp[1]

				if date not in scores or team not in scores[date]:
					continue

				if team not in totals:
					totals[team] = {"gpg": 0, "gpga": 0, "games": 0, "overs": [], "ttOvers": [], "opp_ttOvers": []}
				totals[team]["games"] += 1
				totals[team]["gpg"] += scores[date][team]
				totals[team]["gpga"] += scores[date][opp]
				totals[team]["ttOvers"].append(str(scores[date][team]))
				totals[team]["opp_ttOvers"].append(str(scores[date][opp]))
				totals[team]["overs"].append(str(scores[date][team] + scores[date][opp]))

	out = "\t".join([x.upper() for x in ["team", "gpg", "tt overs", "gpga", "opp tt overs", "overs avg", "overs", "line", f"% over", f"% over L5"]]) + "\n"
	cutoff = 10
	for game in schedule[today]:
		totalLine = lines[game]["total"]["line"]
		totalOdds = lines[game]["total"]["odds"].split(",")
		away, home = map(str, game.split(" @ "))
		gpg = round(totals[away]["gpg"] / totals[away]["games"], 1)
		gpga = round(totals[away]["gpga"] / totals[away]["games"], 1)
		overs = ",".join(totals[away]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[away]["overs"]]) / len(totals[away]["overs"]), 1)
		ttOvers = ",".join(totals[away]["ttOvers"][:cutoff])
		opp_ttOvers = ",".join(totals[away]["opp_ttOvers"][:cutoff])
		totalOver = round(len([x for x in totals[away]["overs"] if int(x) > totalLine]) * 100 / len(totals[away]["overs"]))
		totalOverLast5 = round(len([x for x in totals[away]["overs"][:5] if int(x) > totalLine]) * 100 / len(totals[away]["overs"][:5]))

		out += "\t".join([str(x) for x in [away.upper(), gpg, ttOvers, gpga, opp_ttOvers, oversAvg, overs, f"o{totalLine} ({totalOdds[0]})", f"{totalOver}%", f"{totalOverLast5}%"]]) + "\n"

		gpg = round(totals[home]["gpg"] / totals[home]["games"], 1)
		gpga = round(totals[home]["gpga"] / totals[home]["games"], 1)
		overs = ",".join(totals[home]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[home]["overs"]]) / len(totals[home]["overs"]), 1)
		ttOvers = ",".join(totals[home]["ttOvers"][:cutoff])
		opp_ttOvers = ",".join(totals[home]["opp_ttOvers"][:cutoff])
		totalOver = round(len([x for x in totals[home]["overs"] if int(x) > totalLine]) * 100 / len(totals[home]["overs"]))
		totalOverLast5 = round(len([x for x in totals[home]["overs"][:5] if int(x) > totalLine]) * 100 / len(totals[home]["overs"][:5]))

		out += "\t".join([home.upper(), str(gpg), ttOvers, str(gpga), opp_ttOvers, str(oversAvg), overs, f"u{totalLine} ({totalOdds[1]})", f"{totalOver}%", f"{totalOverLast5}%"]) + "\n"
		out += "\t".join(["-"]*8) + "\n"

	with open(f"{prefix}static/nhlprops/csvs/totals.csv", "w") as fh:
		fh.write(out)


def writeCsvs(props):
	csvs = {}
	splitProps = {"full": []}
	headers = "\t".join(["NAME","TEAM","ML","A/H","LINE","SZN AVG","W-L Splits","A-H Splits","% OVER","L15 OVER","L5 OVER","LAST 10 GAMES","LYR OVER","FD","DK","Best","Implied"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

	for row in props:
		if row["propType"] not in splitProps:
			splitProps[row["propType"]] = []

		if row["overOdds"] == '-inf':
			continue

		splitProps[row["propType"]].append(row)
		splitProps["full"].append(row)

	for prop in splitProps:
		csvs[prop] = headers
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOver"], k["totalOverLast5"]), reverse=True)
		for row in rows:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			gameLine = int(row["gameLine"])
			fd = row["fd"]
			dk = row["dk"]
			if fd.startswith("+"):
				fd = "'"+fd
			if dk.startswith("+"):
				dk = "'"+dk
			avg = row["avg"]
			winLossSplits = row["winLossSplits"].split(" - ")
			if gameLine < 0:
				winLossSplits[0] = f"*{winLossSplits[0]}*"
			else:
				winLossSplits[1] = f"*{winLossSplits[1]}*"
			winLossSplits = " - ".join(winLossSplits)
			awayHomeSplits = row["awayHomeSplits"].split(" - ")
			if row["awayHome"] == "A":
				awayHomeSplits[0] = f"*{awayHomeSplits[0]}*"
			else:
				awayHomeSplits[1] = f"*{awayHomeSplits[1]}*"
			awayHomeSplits = " - ".join(awayHomeSplits)
			if gameLine > 0:
				gameLine = "'"+str(gameLine)
			#if avg >= row["line"]:
			#	avg = f"**{avg}**"
			arr = row["last5"][::-1]
			csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], row["team"], gameLine, row["awayHome"], row["line"], avg, winLossSplits, awayHomeSplits, f"{row['totalOver']}%", f"{row['totalOverLast15']}%", f"{row['totalOverLast5']}%", arr, f"{row['lastTotalOver']}%",fd, dk, f"{row['lowest']}", f"{row['implied']}%"]])

	# add full rows
	csvs["full"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		gameLine = int(row["gameLine"])
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		avg = row["avg"]
		winLossSplits = row["winLossSplits"].split(" - ")
		if gameLine < 0:
			winLossSplits[0] = f"'{winLossSplits[0]}'"
		else:
			winLossSplits[1] = f"'{winLossSplits[1]}'"
		winLossSplits = " - ".join(winLossSplits)
		awayHomeSplits = row["awayHomeSplits"].split(" - ")
		if row["awayHome"] == "A":
			awayHomeSplits[0] = f"'{awayHomeSplits[0]}'"
		else:
			awayHomeSplits[1] = f"'{awayHomeSplits[1]}'"
		awayHomeSplits = " - ".join(awayHomeSplits)
		if int(gameLine) > 0:
			gameLine = "'"+str(gameLine)
		#if avg >= row["line"]:
		#	avg = f"**{avg}**"
		csvs["full"] += "\n" + "\t".join([str(x) for x in [row["player"], row["team"], gameLine, row["awayHome"], row["propType"], row["line"], avg, winLossSplits, awayHomeSplits, f"{row['totalOver']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds]])

	# add top 4 to reddit
	for prop in ["sog", "pts"]:
		if prop in splitProps:
			rows = sorted(splitProps[prop], key=lambda k: (k["totalOver"], k["totalOverLast5"]), reverse=True)
			for row in rows[:4]:
				gameLine = int(row["gameLine"])
				avg = row["avg"]
				if avg >= row["line"]:
					avg = f"**{avg}**"
				fd = row["fd"]
				dk = row["dk"]
				if fd.startswith("+"):
					fd = "'"+fd
				if dk.startswith("+"):
					dk = "'"+dk
				winLossSplits = row["winLossSplits"].split(" - ")
				if gameLine < 0:
					winLossSplits[0] = f"'**{winLossSplits[0]}**'"
				else:
					winLossSplits[1] = f"'**{winLossSplits[1]}**'"
				winLossSplits = " - ".join(winLossSplits)
				awayHomeSplits = row["awayHomeSplits"].split(" - ")
				if row["awayHome"] == "A":
					awayHomeSplits[0] = f"'**{awayHomeSplits[0]}**'"
				else:
					awayHomeSplits[1] = f"'**{awayHomeSplits[1]}**'"
				awayHomeSplits = " - ".join(awayHomeSplits)
				arr = row["last5"][::-1]
				reddit += "\n" + "|".join([str(x) for x in [row["player"], row["team"], row["gameLine"], row["awayHome"], row["propType"], row["line"], avg, winLossSplits, awayHomeSplits, f"{row['totalOver']}%", f"{row['totalOverLast15']}%", f"{row['totalOverLast5']}%", arr, f"{row['lastTotalOver']}%",fd, dk]])
		reddit += "\n-|-|-|-|-|-|-|-|-|-|-|-|-|-|-"

	with open(f"{prefix}static/nhl/reddit.csv", "w") as fh:
		fh.write(reddit)

	for prop in csvs:
		with open(f"{prefix}static/nhl/{prop}.csv", "w") as fh:
			fh.write(csvs[prop])

def addNumSuffix(val):
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

def convertDKTeam(team):
	if team == "cls":
		return "cbj"
	elif team == "was":
		return "wsh"
	elif team == "anh":
		return "ana"
	elif team == "mon":
		return "mtl"
	elif team == "ny":
		return "nyi"
	return team

def writeGameLines(date):
	lines = {}
	if os.path.exists(f"{prefix}static/nhlprops/lines/{date}.json"):
		with open(f"{prefix}static/nhlprops/lines/{date}.json") as fh:
			lines = json.load(fh)

	time.sleep(0.3)
	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42133?format=json"
	outfile = "outnhl"
	call(["curl", "-k", url, "-o", outfile])

	with open("outnhl") as fh:
		data = json.load(fh)

	events = {}
	displayTeams = {}
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		displayTeams[event["teamName1"].lower()] = event["teamShortName1"].lower()
		displayTeams[event["teamName2"].lower()] = event["teamShortName2"].lower()
		game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
			continue
			pass
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
						gameType = row["label"].lower().split(" (")[0]
						if gameType.startswith("o/u"):
							gameType = "total"
						elif gameType.startswith("winner"):
							gameType = "moneyline"
						elif gameType.startswith("puck"):
							gameType = "line"
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

	with open(f"{prefix}static/nhlprops/lines/{date}.json", "w") as fh:
		json.dump(lines, fh, indent=4)


def writeGoalieProps(date):

	time.sleep(0.3)
	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42133/categories/1064?format=json"
	outfile = "outnhl"
	call(["curl", "-k", url, "-o", outfile])

	with open("outnhl") as fh:
		data = json.load(fh)

	with open(f"{prefix}static/nhlprops/dates/{date}.json") as fh:
		props = json.load(fh)

	events = {}
	
	prop = "sv"
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		if "teamShortName1" not in event:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		else:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if game not in props:
			props[game] = {}
		events[event["eventId"]] = game

	for catRow in data["eventGroup"]["offerCategories"]:
		if not catRow["name"].lower() == "goalie props":
			continue
		for cRow in catRow["offerSubcategoryDescriptors"]:
			if cRow["name"].lower() != "saves":
				continue
			for offerRow in cRow["offerSubcategory"]["offers"]:
				for row in offerRow:
					game = events[row["eventId"]]
					player = " ".join(row["label"].lower().replace(".", "").replace("'", "").split(" ")[:-1])
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
	with open(f"{prefix}static/nhlprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def writeTT(date):

	tt = {}

	time.sleep(0.2)
	outfile = "outnhl"
	url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42133/categories/1193/subcategories/12055?format=json"
	call(["curl", "-k", url, "-o", outfile])

	with open(outfile) as fh:
		data = json.load(fh)

	events = {}
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		if "teamShortName1" not in event:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		else:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
			continue
		events[event["eventId"]] = game

	for catRow in data["eventGroup"]["offerCategories"]:
		if catRow["offerCategoryId"] != 1193:
			continue
		for cRow in catRow["offerSubcategoryDescriptors"]:
			if cRow["subcategoryId"] != 12055:
				continue
			for offerRow in cRow["offerSubcategory"]["offers"]:
				for row in offerRow:
					team = convertDKTeam(row["label"].lower().split(" ")[0])
					if team == "nyi":
						if "rangers" in row["label"].lower():
							team = "nyr"
						else:
							team = "nyi"
					tt[team] = {}

					for outcome in row["outcomes"]:
						if "main" not in outcome:
							continue

						ou = outcome["label"].lower()
						tt[team]["line"] = outcome["line"]
						tt[team][f"{ou}Odds"] = outcome["oddsAmerican"]

	with open(f"{prefix}static/nhlprops/tt.json", "w") as fh:
		json.dump(tt, fh, indent=4)

def writeProps(date):
	propNames = ["sog", "pts", "ast", "g", "bs"]
	catIds = [1189,550,550,1190,550]
	subCatIds = [12040,5586,5587,12041,10296]

	props = {}
	if os.path.exists(f"{prefix}static/nhlprops/dates/{date}.json"):
		with open(f"{prefix}static/nhlprops/dates/{date}.json") as fh:
			props = json.load(fh)

	for catId, subCatId, prop in zip(catIds, subCatIds, propNames):
		time.sleep(0.5)
		outfile = "outnhl"
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42133/categories/{catId}/subcategories/{subCatId}?format=json"
		call(["curl", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
				continue
			if game not in props:
				props[game] = {}
			events[event["eventId"]] = game

		for catRow in data["eventGroup"]["offerCategories"]:
			if catRow["offerCategoryId"] != catId:
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["subcategoryId"] != subCatId:
					continue
				for offerRow in cRow["offerSubcategory"]["offers"]:
					for row in offerRow:
						game = events[row["eventId"]]
						odds = ["",""]
						line = ""
						if prop != "g":
							line = row["outcomes"][0]["line"]
						player = ""
						for outcome in row["outcomes"]:
							if prop == "g" and outcome["criterionName"].lower() == "anytime scorer":
								player = outcome["label"].lower().replace(".", "").replace("'", "")
								odds[0] = outcome["oddsAmerican"]
								if player not in props[game]:
									props[game][player] = {}
								if prop not in props[game][player]:
									props[game][player][prop] = {}
								props[game][player][prop] = {
									"line": 0.5,
									"over": odds[0],
									"under": "0"
								}
							elif outcome["label"].lower() == "over":
								odds[0] = outcome["oddsAmerican"]
								if "participant" in outcome:
									player = outcome["participant"].lower().replace(".", "").replace("'", "")
							else:
								odds[1] = outcome["oddsAmerican"]
								if "participant" in outcome:
									player = outcome["participant"].lower().replace(".", "").replace("'", "")

						if prop != "g":
							if player not in props[game]:
								props[game][player] = {}
							if prop not in props[game][player]:
								props[game][player][prop] = {}
							props[game][player][prop] = {
								"line": line,
								"over": odds[0],
								"under": odds[1]
							}

	with open(f"{prefix}static/nhlprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def goalieLines(props):
	with open(f"{prefix}static/nhlprops/goalieProps.json") as fh:
		goalieProps = json.load(fh)

	for game in goalieProps:
		if game not in props:
			props[game] = {}
		for player in goalieProps[game]:
			props[game][player] = {
				"sv": {
					"line": goalieProps[game][player]["sv"]["line"],
					"over": goalieProps[game][player]["sv"]["over"],
					"under": goalieProps[game][player]["sv"]["under"],
				}
			}
	pass

def writeGoalieStats():
	url = "https://www.hockey-reference.com/leagues/NHL_2024_goalies.html"
	outfile = "outnhl"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	rows = soup.find_all("tr")
	headers = []
	for header in rows[1].find_all("th")[1:]:
		headers.append(header.text.lower())

	stats = {}
	for tr in rows[2:]:
		if "thead" in tr.get("class", []):
			continue
		rowStats = {}
		for hdr, td in zip(headers, tr.find_all("td")):
			val = td.text
			if "." in val:
				val = float(val)
			else:
				try:
					val = int(val)
				except:
					pass
			rowStats[hdr] = val

		player = rowStats["player"].lower().replace("-", " ").replace("\u00f6", "o").replace("\u00ed", "i").replace("\u00e1", "a").replace("\u00e9", "e").replace("\u011b", "e").replace("\u010d", "c").replace("\u0161", "s").replace("\u0159", "r")
		if player == "daniel vladar":
			player = "dan vladar"
		team = rowStats["tm"].lower()
		if team == "lak":
			team = "la"
		elif team == "sjs":
			team = "sj"
		elif team == "njd":
			team = "nj"
		elif team == "veg":
			team = "vgk"
		elif team == "tbl":
			team = "tb"

		if team not in stats:
			stats[team] = {}

		stats[team][player] = rowStats

	with open(f"static/nhl/goalies.json", "w") as fh:
		json.dump(stats, fh, indent=4)

def writeExpectations():
	url = "https://www.moneypuck.com/moneypuck/playerData/seasonSummary/2023/regular/goalies.csv"
	outfile = f"{prefix}static/nhlprops/goalies.csv"

	goalies = {}
	lines = open(outfile).readlines()
	headers = []
	for header in lines[0].split(","):
		headers.append(header.lower())

	for line in lines[1:]:
		data = {}
		for header, val in zip(headers,line.replace("\n", "").split(",")):
			data[header] = val
		if data["situation"] != "all":
			continue
		goalies[data["name"].lower().replace("-", " ")] = data

	with open(f"static/nhl/expected.json", "w") as fh:
		json.dump(goalies, fh, indent=4)

def convertNaturalStatTeam(team):
	if team.startswith("columbus"):
		return "cbj"
	elif team.endswith("rangers"):
		return "nyr"
	elif team.endswith("islanders"):
		return "nyi"
	elif team.endswith("sharks"):
		return "sj"
	elif team.endswith("capitals"):
		return "wsh"
	elif team.endswith("predators"):
		return "nsh"
	elif team.endswith("knights"):
		return "vgk"
	elif team.endswith("lightning"):
		return "tb"
	elif team.endswith("kings"):
		return "la"
	elif team.endswith("canadiens"):
		return "mtl"
	elif team.endswith("panthers"):
		return "fla"
	elif team.endswith("jets"):
		return "wpg"
	elif team.endswith("devils"):
		return "nj"
	elif team.endswith("flames"):
		return "cgy"

	return team.replace(" ", "")[:3]

def writeExpectedGoalies(date):
	url = f"https://www.rotowire.com/hockey/tables/projected-goalies.php?date={date}"
	outfile = "outnhl"
	time.sleep(0.3)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open("outnhl") as fh:
		data = json.load(fh)

	expected = {"confirmed": {}, "expected": {}}
	for row in data:
		away = convertDKTeam(row["visitteam"].lower())
		home = convertDKTeam(row["hometeam"].lower())
		expected[row["visitStatus"].lower()][away] = row["visitPlayer"].lower()
		expected[row["homeStatus"].lower()][home] = row["homePlayer"].lower()

	with open(f"static/nhl/expectedGoalies.json", "w") as fh:
		json.dump(expected, fh, indent=4)

def writeLineups():
	url = f"https://www.rotowire.com/hockey/nhl-lineups.php"
	if datetime.now().hour >= 20 or datetime.now().hour < 3:
		url += "?date=tomorrow"

	outfile = "outnhl"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	lineups = {}
	expected = {"confirmed": {}, "expected": {}}
	for box in soup.find_all("div", class_="lineup"):
		if "is-tools" in box.get("class") or "is-ad" in box.get("class"):
			continue

		away = convertDKTeam(box.find_all("div", class_="lineup__abbr")[0].text.lower())
		home = convertDKTeam(box.find_all("div", class_="lineup__abbr")[1].text.lower())

		for idx, lineupList in enumerate(box.find_all("ul", class_="lineup__list")):
			team = away if idx == 0 else home
			status = "confirmed" if "is-green" in lineupList.find("div", class_="dot").get("class") else "expected"
			expected[status][team] = " ".join(lineupList.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
			title = ""
			for li in lineupList.find_all("li")[1:]:
				try:
					if "lineup__title" in li.get("class"):
						title = li.text.lower()
						if team not in lineups:
							lineups[team] = {}
						lineups[team][title] = []
					else:
						player = " ".join(li.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
						lineups[team][title].append(player)
				except:
					pass

	with open(f"static/nhl/expectedGoalies.json", "w") as fh:
		json.dump(expected, fh, indent=4)
	with open(f"static/nhl/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)


def writeOpportunities():

	date = datetime.now()
	date = str(date)[:10]

	twoWeeksAgo = datetime.now() - timedelta(days=10)
	twoWeeksAgo = str(twoWeeksAgo)[:10]
	oneWeekAgo = datetime.now() - timedelta(days=6)
	oneWeekAgo = str(oneWeekAgo)[:10]
	daysAgo = datetime.now() - timedelta(days=2)
	daysAgo = str(daysAgo)[:10]

	baseUrl = "https://www.naturalstattrick.com/teamtable.php?fromseason=20232024&thruseason=20232024&stype=2&sit=all&score=all&rate=n&team=all&loc=B"
	periods = {
		"last10": "&gpf=10",
		"last5": f"&fd={twoWeeksAgo}&td={date}",
		"last3": f"&fd={oneWeekAgo}&td={date}",
		"last1": f"&fd={daysAgo}&td={date}",
		"tot": ""
	}

	opps = {}

	for period in periods:
		url = f"{baseUrl}{periods[period]}"
		outfile = "outnhl"
		time.sleep(0.3)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		headers = []
		for th in soup.find("tr").find_all("th")[1:]:
			headers.append(th.text.strip().lower().replace(" ", ""))

		for row in soup.find_all("tr")[1:]:
			rowStats = {}
			for hdr, td in zip(headers, row.find_all("td")[1:]):
				val = td.text
				try:
					if "." in val:
						val = float(val)
					else:
						val = int(val)
				except:
					pass
				rowStats[hdr] = val

			team = convertNaturalStatTeam(rowStats["team"].lower())
			rowStats["toi"] = int(rowStats["toi"].split(":")[0]) + (int(rowStats["toi"].split(":")[-1]) / 60)

			if team not in opps:
				opps[team] = {}
			opps[team][period] = rowStats

	with open(f"static/nhl/opportunities.json", "w") as fh:
		json.dump(opps, fh, indent=4)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("-l", "--lineups", action="store_true", help="Write Lineups")
	parser.add_argument("-p", "--props", action="store_true", help="Props")
	parser.add_argument("-g", "--goalies", action="store_true", help="Goalie Stats")
	parser.add_argument("--opp", action="store_true", help="Opportunities")
	parser.add_argument("--rankings", action="store_true", help="Rankings")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.lines:
		writeGameLines(date)
		writeTT(date)
		writeExpectations()
	elif args.goalies:
		writeExpectations()
		writeGoalieStats()
		writeExpectedGoalies(date)
	elif args.opp:
		writeOpportunities()
	elif args.lineups:
		writeLineups()
	elif args.props:
		writeStaticProps()
	elif args.rankings:
		writeRankings()
	elif args.cron:
		#writeProps(date)
		#writeTT(date)
		#writeGoalieProps(date)
		writeRankings()
		writeGoalieStats()
		writeExpectations()
		#writeGameLines(date)
		try:
			writeOpportunities()
		except:
			print("no opps")
			pass
		#writeExpectedGoalies(date)
		writeLineups()
		writeStaticProps()

