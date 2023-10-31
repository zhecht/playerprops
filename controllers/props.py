#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform

import glob
import json
import math
import operator
import os
import subprocess
import re

try:
	from controllers.profootballreference import *
	from controllers.read_rosters import *
	from controllers.functions import *
except:
	from functions import *
	from profootballreference import *
	from read_rosters import *

from datetime import datetime

props_blueprint = Blueprint('props', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

pffTeamTranslations = {"ARZ": "CRD", "BLT": "RAV", "CLV": "CLE", "GB": "GNB", "HST": "HTX", "IND": "CLT", "KC": "KAN", "LAC": "SDG", "LA": "RAM", "LV": "RAI", "NO": "NOR", "NE": "NWE", "SF": "SFO", "TB": "TAM", "TEN": "OTI"}

def getProfootballReferenceTeam(team):
	if team == "arz" or team == "ari":
		return "crd"
	elif team == "bal" or team == "blt":
		return "rav"
	elif team == "clv":
		return "cle"
	elif team == "gb":
		return "gnb"
	elif team == "hst" or team == "hou":
		return "htx"
	elif team == "ind":
		return "clt"
	elif team == "kc":
		return "kan"
	elif team == "la" or team == "lar":
		return "ram"
	elif team == "lac":
		return "sdg"
	elif team == "lv":
		return "rai"
	elif team == "no":
		return "nor"
	elif team == "ne":
		return "nwe"
	elif team == "sf":
		return "sfo"
	elif team == "tb":
		return "tam"
	elif team == "ten":
		return "oti"
	elif team == "wsh":
		return "was"
	return team

def getYahooTeam(team):
	if team == "arz":
		return "ari"
	elif team == "blt":
		return "bal"
	elif team == "clv":
		return "cle"
	elif team == "hst":
		return "hou"
	elif team == "la":
		return "lar"
	elif team == "sdg":
		return "lac"
	elif team == "was":
		return "wsh"
	return team

def getOppTotPlays(totPlays, team, opp):
	oppPlays = sum([int(x) for x in totPlays[opp].split(",")])
	plays = 0
	for idx, o in enumerate(get_opponents(team)):
		if idx >= CURR_WEEK:
			break
		if o == "BYE":
			continue
		plays += int(totPlays[o].split(",")[idx])

	return plays, oppPlays

def tacklesAnalysis():
	with open(f"{prefix}static/profootballreference/teams.json") as fh:
		teams = json.load(fh)

	res = {}
	for fullTeam in teams:
		team = fullTeam.split("/")[-2]
		res[team] = {}
		for idx, opp in enumerate(get_opponents(team)):
			if opp == "BYE":
				continue
			wk = idx+1
			res[team][wk] = {"dbs": 0, "lbs": 0}

			with open(f"{prefix}static/profootballreference/{opp}/stats.json") as fh:
				stats = json.load(fh)

			with open(f"{prefix}static/profootballreference/{opp}/roster.json") as fh:
				roster = json.load(fh)

			for player in stats:
				if player not in roster:
					continue
				pos = roster[player]

				if pos not in ["LB", "S", "SS", "FS", "CB", "DE", "DB", "DT", "NT"]:
					continue

				if f"wk{wk}" not in stats[player]:
					continue

				tackles = stats[player][f"wk{wk}"].get("tackles_combined", 0)
				if pos in ["LB", "DE", "DT", "NT"]:
					res[team][wk]["lbs"] += tackles
				else:
					res[team][wk]["dbs"] += tackles

	print(res["rav"])


def getDefPropsData(teamsArg):
	pastPropData = {}
	if 0:
		for file in glob.glob(f"{prefix}static/props/wk*_def.json"):
			wk = int(file.split("wk")[-1].split("_")[0])
			if wk <= CURR_WEEK:
				with open(file) as fh:
					data = json.load(fh)
				for name in data:
					if name not in pastPropData:
						pastPropData[name] = {}
					if not data[name]["line"]:
						continue
					pastPropData[name][wk] = data[name]["line"][1:]

	with open(f"{prefix}static/props/wk{CURR_WEEK+1}_def.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/tot_plays.json") as fh:
		playsData = json.load(fh)

	with open(f"{prefix}static/runPassTotals.json") as fh:
		runPassData = json.load(fh)

	with open(f"{prefix}static/profootballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/profootballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/profootballreference/totals.json") as fh:
		totals = json.load(fh)
	with open(f"{prefix}static/profootballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	#tacklesAnalysis()

	res = []
	for team in propData:
		for name in propData[team]:
			for prop in propData[team][name]:
				espnTeam = team

				if teamsArg and team.lower() not in teamsArg:
					continue

				opponents = get_opponents(espnTeam)
				opp = opponents[CURR_WEEK]
				if opp == "BYE":
					continue
				
				pos = "-"
				if name in roster[team]:
					pos = roster[team][name]

				#totPlays, oppTotPlays = getOppTotPlays(playsData, pff_team, opp)
				line = propData[team][name][prop]["line"]
				if line:
					line = line[1:]


				lastTotalOver = lastTotalGames = 0
				if line and name in lastYearStats[espnTeam] and lastYearStats[espnTeam][name]:
					for dt in lastYearStats[espnTeam][name]:
						lastTotalGames += 1
						val = 0
						if "tackles_combined" in lastYearStats[espnTeam][name][dt]:
							val = lastYearStats[espnTeam][name][dt]["tackles_combined"]
						if val > float(line):
							lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				playerStats = {}
				last5 = []
				last5WithLines = []
				totTackles = 0
				totTeamTackles = 0
				avg = 0
				totalOver = 0
				gamesPlayed = totals[espnTeam][name]["gamesPlayed"]
				totTeamSnaps = totSnaps = 0
				wks = glob.glob(f"{prefix}static/profootballreference/{espnTeam}/wk*.json")
				for wk in sorted(wks, key=lambda k: int(k.split("/")[-1][2:-5]), reverse=True):
					with open(wk) as fh:
						data = json.load(fh)
					if name not in data:
						continue

					week = int(wk.split("/")[-1][2:-5])
					tackles = data[name].get("tackles_combined", 0)
					totTackles += tackles
					if line and tackles > float(line):
						totalOver += 1

					t = str(int(tackles))
					last5.append(t)
					if name+" "+team.upper() in pastPropData and week in pastPropData[name+" "+team.upper()]:
						t += f"({pastPropData[name+' '+team.upper()][week]})"
					last5WithLines.append(t)

				if gamesPlayed:
					avg = round(totTackles / gamesPlayed, 1)
					totalOver = round((totalOver / gamesPlayed) * 100)

				overOdds = underOdds = float('-inf')
				for book in propData[team][name][prop]:
					if book == "line" or not propData[team][name][prop][book]["over"]:
						continue

					line = propData[team][name][prop]["line"][1:]
					over = propData[team][name][prop][book]["over"]
					overLine = over.split(" ")[0][1:]
					overOdd = int(over.split(" ")[1][1:-1])
					if overLine == line and overOdd > overOdds:
						overOdds = overOdd

					under = propData[team][name][prop][book]["under"]
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

				rank = oppRank = ""
				if "tpg" in rankings[espnTeam] and "otpg" in rankings[opp]:
					rank = rankings[espnTeam]["tpg"]["rank"]
					oppRank = rankings[opp]["otpg"]["rank"]

				res.append({
					"player": name.title(),
					"team": getYahooTeam(team),
					"opponent": TEAM_TRANS.get(opp, opp),
					"hit": True,
					"pos": pos,
					"rank": rank,
					"oppRank": oppRank,
					"avg": avg,
					"totalOver": totalOver,
					"lastTotalOver": lastTotalOver,
					"last5": ",".join(last5),
					"last5WithLines": ",".join(last5WithLines),
					"propType": "tackles_combined",
					"line": line or "-",
					"overOdds": overOdds,
					"underOdds": underOdds
				})
	return res

def customPropData(propData):
	pass

@props_blueprint.route('/getDefProps')
def getDefProps_route():
	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.lower().split(",")
	return jsonify(getDefPropsData(teams))

def checkTrades(player, team, stats, totals):
	with open(f"{prefix}static/nfl_trades.json") as fh:
		trades = json.load(fh)

	if player not in totals[team]:
		return 0
	totGames = totals[team][player]["gamesPlayed"]

	if player not in trades:
		return totGames
	trade = trades[player]

	totGames += totals[trade["from"]][player]["gamesPlayed"]

	for file in glob.glob(f"{prefix}static/profootballreference/{trade['from']}/*.json"):
		with open(file) as fh:
			oldStats = json.load(fh)
		wk = file.split("/")[-1][:-5]
		if player in oldStats:
			stats[wk] = oldStats[player]

	return totGames

def getATTDRankings(roster):
	rankings = []
	with open(f"{prefix}static/profootballreference/schedule.json") as fh:
		schedule = json.load(fh)
	for wk in schedule:
		for game in schedule[wk]:
			pass
	return rankings

@props_blueprint.route('/getATTDProps')
def getProps_ATTD_route():
	res = []

	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.upper().split(",")

	with open(f"{prefix}static/props/attd.json") as fh:
		attd = json.load(fh)
	with open(f"{prefix}static/profootballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/profootballreference/totals.json") as fh:
		totals = json.load(fh)
	with open(f"{prefix}static/profootballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	rankings = getATTDRankings(roster)

	for team in attd:

		if teams and team.upper() not in teams:
			continue

		teamStats = {}
		opp = get_opponents(team)[CURR_WEEK]
		for file in glob.glob(f"{prefix}static/profootballreference/{team}/*.json"):
			with open(file) as fh:
				gameStats = json.load(fh)
			wk = file.split("/")[-1].replace(".json", "")
			teamStats[wk] = gameStats

		for player in attd[team]:
			if player.endswith("defense"):
				continue

			fd_odds = attd[team][player].get("fanduel", 0)
			dk_odds = attd[team][player].get("draftkings", 0)
			if fd_odds > 0:
				fd_odds = f"+{fd_odds}"
			if dk_odds > 0:
				dk_odds = f"+{dk_odds}"

			playerStats = {}
			for wk in teamStats:
				for p in teamStats[wk]:
					if p == player:
						playerStats[wk] = teamStats[wk][p]

			totGames = checkTrades(player, team,playerStats, totals)

			pos = "-"
			if team in roster and player in roster[team]:
				pos = roster[team][player]

			tds = []
			last3 = []
			for wk in sorted(playerStats.keys(), key=lambda k: int(k.replace("wk", "")), reverse=True):
				totTds = playerStats[wk].get("rush_td", 0) + playerStats[wk].get("rec_td", 0)
				tds.append(int(totTds))
				if len(last3) < 3:
					last3.append(int(totTds))

			scored = [x for x in tds if x > 0]
			avg = avgLast3 = totalOver = totalOverLast3 = 0
			if tds:
				totalOver = round(len(scored) * 100 / len(tds))
				totalOverLast3 = round(len([x for x in last3 if x > 0]) * 100 / len(last3))
				avg = round(sum(tds) / len(tds), 1)
				avgLast3 = round(sum(last3) / len(last3), 1)

			lastTotalOver = lastTotalGames = 0
			if player in lastYearStats[team] and lastYearStats[team][player]:
				for dt in lastYearStats[team][player]:
					lastTotalGames += 1
					val = lastYearStats[team][player][dt].get("rush_td", 0) + lastYearStats[team][player][dt].get("rec_td", 0)
					if val >= 1:
						lastTotalOver += 1
			if lastTotalGames:
				lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

			lastAvg = 0
			if player in averages[team] and averages[team][player]:
				lastAvg = averages[team][player].get("rush_td", 0) + averages[team][player].get("rec_td", 0)
				lastAvg = round(lastAvg, 1)

			res.append({
				"player": player.title(),
				"pos": pos,
				"team": team,
				"opponent": opp,
				"avg": avg,
				"avgLast3": avgLast3,
				"lastAvg": lastAvg,
				"prop": "ATTD",
				"line": 1,
				"dk_odds": dk_odds,
				"fd_odds": fd_odds,
				"totalOver": totalOver,
				"totalOverLast3": totalOverLast3,
				"lastTotalOver": lastTotalOver,
				"last": ",".join([str(x) for x in tds]),
			})

	return jsonify(res)

def writeCsvs(props):
	csvs = {}
	splitProps = {"full": []}
	headers = "\t".join(["NAME","ML","A/H","TEAM","OPP","OPP RANK","PROP","LINE","SZN AVG","W-L Splits","A-H Splits","% OVER","L3 % OVER","LAST GAMES ➡️","LAST YR % OVER","OVER","UNDER"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

	for row in props:
		if row["propType"] not in splitProps:
			splitProps[row["propType"]] = []
		splitProps[row["propType"]].append(row)
		splitProps["full"].append(row)


	if "tackles_combined" in splitProps:
		csvs["tackles_combined"] = headers
		rows = sorted(splitProps["tackles_combined"], key=lambda k: (k["player"], -k["totalOverLast3"], -k["totalOver"]))
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
			csvs["tackles_combined"] += "\n" + "\t".join([str(x) for x in [row["player"], gameLine, row["awayHome"], row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), "TACKLES", row["line"], row["avg"], row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast3']}%", row["last5"], f"{row['lastTotalOver']}%", overOdds, underOdds]])

	# add full rows
	csvs["full_name"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"], -k["totalOverLast3"], -k["totalOver"]))
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
		csvs["full_name"] += "\n" + "\t".join([str(x) for x in [row["player"], gameLine, row["awayHome"], row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], row["line"], row["avg"], row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast3']}%", row["last5"], f"{row['lastTotalOver']}%", overOdds, underOdds]])
		#except:
		#	pass

	csvs["full_hit"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["totalOverLast3"], k["totalOver"]), reverse=True)
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
			csvs["full_hit"] += "\n" + "\t".join([str(x) for x in [row["player"], gameLine, row["awayHome"], row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast3']}%", row["last5"], f"{row['lastTotalOver']}%", overOdds, underOdds]])
		except:
			pass

	for prop in csvs:
		if prop == "full":
			continue
		with open(f"{prefix}static/props/csvs/{prop}.csv", "w") as fh:
			fh.write(csvs[prop])

def getLongestRanks():
	with open(f"{prefix}static/profootballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/props/longestRanks.json") as fh:
		longestRanks = json.load(fh)
	ranks = {}
	for wk in schedule:
		if int(wk[2:]) > CURR_WEEK:
			continue
		for game in schedule[wk]:
			gameSp = game.split(" @ ")
			for gameIdx, team in enumerate(gameSp):
				opp = gameSp[0] if gameIdx == 1 else gameSp[1]
				if team not in ranks:
					ranks[team] = {}
				if wk not in ranks[team]:
					ranks[team][wk] = {}
				if "RB" not in longestRanks[opp][wk]:
					print(opp,wk)
				for pos in longestRanks[opp][wk]:
					ranks[team][wk][pos] = {
						"pass_long": max(longestRanks[opp][wk][pos]["pass_long"] or [0]),
						"rec_long": max(longestRanks[opp][wk][pos]["rec_long"] or [0]),
						"rush_long": max(longestRanks[opp][wk][pos]["rush_long"] or [0])
					}
	return ranks


@props_blueprint.route('/getLongestProps')
def getProps_longest_route():
	res = []

	propArg = request.args.get("prop") or ""
	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.upper().split(",")

	with open(f"{prefix}static/props/longest.json") as fh:
		longest = json.load(fh)
	with open(f"{prefix}static/profootballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/profootballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	longestRanks = getLongestRanks()

	for team in longest:

		if teams and team.upper() not in teams:
			continue

		teamStats = {}
		opp = get_opponents(team)[CURR_WEEK]
		for file in glob.glob(f"{prefix}static/profootballreference/{team}/*.json"):
			with open(file) as fh:
				gameStats = json.load(fh)
			wk = file.split("/")[-1].replace(".json", "")
			teamStats[wk] = gameStats

		for player in longest[team]:
			
			pos = "-"
			if team in roster and player in roster[team]:
				pos = roster[team][player]

			for prop in longest[team][player]:

				if propArg and prop != propArg:
					continue

				last = []
				last3 = []
				for wk in sorted(teamStats.keys(), key=lambda k: int(k.replace("wk", "")), reverse=True):
					if player in teamStats[wk]:
						val = teamStats[wk][player].get(prop, 0)
						last.append(int(val))
						if len(last3) < 3:
							last3.append(int(val))

				# get best odds
				overOdds = underOdds = float('-inf')
				line = ""
				for book in longest[team][player][prop]:
					if book == "line" or not longest[team][player][prop][book]["over"]:
						continue

					line = longest[team][player][prop]["line"][1:]
					over = longest[team][player][prop][book]["over"]
					overLine = over.split(" ")[0][1:]
					overOdd = int(over.split(" ")[1][1:-1])
					if overLine == line and overOdd > overOdds:
						overOdds = overOdd

					under = longest[team][player][prop][book].get("under", 0)
					if under:
						underLine = under.split(" ")[0][1:]
						underOdd = int(under.split(" ")[1][1:-1])
						if underLine == line and underOdd > underOdds:
							underOdds = underOdd

				try:
					line = float(line)
				except:
					line = 0.0

				oppOver = oppOverTot = 0
				oppOverList = []
				if pos != "-":
					for wk in sorted(longestRanks[opp], key=lambda k: int(k.replace("wk", "")), reverse=True):
						if pos in longestRanks[opp][wk] and longestRanks[opp][wk][pos][prop] > line:
							oppOver += 1
						try:
							oppOverList.append(longestRanks[opp][wk][pos][prop])
						except:
							oppOverList.append(0)
						oppOverTot += 1

				if oppOverTot:
					oppOver = round(oppOver * 100 / oppOverTot, 1)

				avg = avgLast3 = totalOver = totalOverLast3 = 0
				if last:
					scored = [x for x in last if x > line]
					totalOver = round(len(scored) * 100 / len(last))
					totalOverLast3 = round(len([x for x in last3 if x > line]) * 100 / len(last3))
					avg = round(sum(last) / len(last), 1)
					avgLast3 = round(sum(last3) / len(last3), 1)

				lastTotalOver = lastTotalGames = 0
				if player in lastYearStats[team] and lastYearStats[team][player]:
					for dt in lastYearStats[team][player]:
						lastTotalGames += 1
						val = lastYearStats[team][player][dt].get(prop, 0)
						if val > line:
							lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				lastAvg = 0
				if player in averages[team] and averages[team][player]:
					lastAvg = averages[team][player].get(prop, 0) * averages[team][player].get("gamesPlayed", 0)
					lastAvg = round(lastAvg, 1)

				res.append({
					"player": player.title(),
					"pos": pos,
					"team": team,
					"opponent": opp,
					"avg": avg,
					"avgLast3": avgLast3,
					"lastAvg": lastAvg,
					"prop": prop,
					"line": line,
					"overOdds": overOdds,
					"underOdds": underOdds,
					"totalOver": totalOver,
					"totalOverLast3": totalOverLast3,
					"lastTotalOver": lastTotalOver,
					"last": ",".join([str(x) for x in last]),
					"oppOver": oppOver,
					"oppOverList": ",".join([str(int(x)) for x in oppOverList])
				})

	return jsonify(res)

@props_blueprint.route('/getProps')
def getProps_route():
	res = []

	propArg = request.args.get("prop") or ""
	teamsArg = request.args.get("teams") or ""
	if teamsArg:
		teamsArg = teamsArg.lower().split(",")
	players = request.args.get("players") or []
	if players:
		players = players.split(",")

	with open(f"{prefix}static/props/dates/wk{CURR_WEEK+1}.json") as fh:
		props = json.load(fh)
	with open(f"{prefix}static/profootballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/profootballreference/totals.json") as fh:
		totals = json.load(fh)
	with open(f"{prefix}static/profootballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/profootballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/profootballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/profootballreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/props/lines.json") as fh:
		gameLines = json.load(fh)

	for game in props:
		for player in props[game]:

			team = opp = ""
			gameSp = game.split(" @ ")
			team1, team2 = gameSp[0], gameSp[1]
			if player in totals[team1]:
				team = team1
				opp = team2
			elif player in totals[team2]:
				team = team2
				opp = team1
			else:
				continue

			if teamsArg and team not in teamsArg:
				continue

			if players and player not in players:
				continue

			playerStats = {}
			for file in glob.glob(f"{prefix}static/profootballreference/{team}/*"):
				with open(file) as fh:
					gameStats = json.load(fh)
				wk = file.split("/")[-1][:-5]
				if player in gameStats:
					playerStats[wk] = gameStats[player]

			totGames = checkTrades(player, team.lower(),playerStats, totals)

			for prop in props[game][player]:
				if propArg and prop != propArg:
					continue
				if prop in ["kicking_pts", "pat", "rush+rec_yds", "pass+rush_yds"]:
					continue
				if "long" in prop:
					continue

				overOdds = props[game][player][prop]["over"]
				underOdds = props[game][player][prop]["under"]
				line = props[game][player][prop]["line"]

				lastTotalOver = lastTotalGames = 0
				if lastYearStats[team].get(player, {}):
					for dt in lastYearStats[team][player]:
						lastTotalGames += 1
						val = 0
						if prop == "rush+rec_yds":
							val = lastYearStats[team][player][dt].get("rush_yds", 0) + lastYearStats[team][player][dt].get("rec_yds", 0)
						else:
							if prop in lastYearStats[team][player][dt]:
								val = lastYearStats[team][player][dt][prop]
						if val > line:
							lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				winLossSplits = [[],[]]
				awayHomeSplits = [[],[]]
				last5 = []
				tot = totalOver = totalOverLast3 = 0
				for wk in sorted(playerStats.keys(), key=lambda k: int(k[2:]), reverse=True):
					val = 0
					if prop == "rush+rec_yds":
						val = playerStats[wk].get("rush_yds", 0) + playerStats[wk].get("rec_yds", 0)
					else:
						val = playerStats[wk].get(prop, 0)

					pastOpp = ""
					teamIsAway = False
					for g in schedule[wk]:
						gameSp = g.split(" @ ")
						if team in gameSp:
							if team == gameSp[0]:
								teamIsAway = True
								pastOpp = gameSp[1]
							else:
								pastOpp = gameSp[0]
							break

					if get_opponents(team)[int(wk[2:])-1] == "BYE":
						continue

					if teamIsAway:
						awayHomeSplits[0].append(val)
					else:
						awayHomeSplits[1].append(val)

					teamScore = scores[wk][team]
					oppScore = scores[wk][pastOpp]

					if teamScore > oppScore:
						winLossSplits[0].append(val)
					elif teamScore < oppScore:
						winLossSplits[1].append(val)
					else:
						winLossSplits[0].append(val)
						winLossSplits[1].append(val)
					tot += val
					last5.append(val)
					if val > line:
						totalOver += 1
						if len(last5) <= 3:
							totalOverLast3 += 1

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

				diff = 0
				if totGames:
					avg = tot / totGames

				if totalOver and totGames:
					totalOver = round((totalOver / totGames) * 100)
					last5Size = len(last5) if len(last5) < 3 else 3
					totalOverLast3 = round((totalOverLast3 / last5Size) * 100)

				avg = 0
				if totGames:
					avg = round(tot / totGames, 1)

				lastAvg = 0
				if player in averages[team] and averages[team][player]:
					if prop == "rush+rec_yds":
						if "rush_yds" in averages[team][player] and "rec_yds" in averages[team][player]:
							lastAvg = averages[team][player]["rush_yds"] + averages[team][player]["rec_yds"]
					else:
						lastAvg = averages[team][player].get(prop, 0)
					lastAvg = round(lastAvg, 1)

				oppRank = ""
				oppRankVal = ""
				rankingsProp = convertRankingsProp(prop)
				if opp != "BYE" and "o"+rankingsProp in rankings[opp]:
					oppRankVal = str(rankings[opp]["o"+rankingsProp]["season"])
					oppRank = rankings[opp]['o'+rankingsProp]['rank']

				gameLine = 0
				if game in gameLines:
					gameOdds = gameLines[game]["moneyline"]["odds"].split(",")
					if team == game.split(" @ ")[0]:
						gameLine = gameOdds[0]
					else:
						gameLine = gameOdds[1]

				pos = roster[team].get(player, "")

				res.append({
					"player": player.title(),
					"team": team.upper(),
					"opponent": opp.upper(),
					"awayHome": "A" if team == game.split(" @ ")[0] else "H",
					"oppRank": oppRank,
					"hit": True,
					"pos": pos,
					"lastAvg": lastAvg,
					"gameLine": gameLine,
					"avg": avg,
					"last5": ",".join([str(int(x)) for x in last5]),
					"lastAll": ",".join([str(int(x)) for x in last5]),
					"diff": diff,
					"totalOver": totalOver,
					"totalOverLast3": totalOverLast3,
					"lastTotalOver": lastTotalOver,
					"propType": prop,
					"winLossSplits": winLossSplits,
					"awayHomeSplits": awayHomeSplits,
					"line": line or "-",
					"overUnderOdds": f"{overOdds},{underOdds}",
					"overOdds": overOdds,
					"underOdds": underOdds,
					"stats": playerStats
				})

	teamTotals(schedule)
	writeCsvs(res)
	#h2h(res)
	return jsonify(res)

def convertDKTeam(team):
	if team.startswith("gb"):
		return "gb"
	elif team == "was":
		return "wsh"
	return team.replace(" ", "")[:3]

def h2h(props):
	with open(f"{prefix}static/props/h2h.json") as fh:
		h2h = json.load(fh)

	out = ""
	for game in h2h:
		out += "\n"+game.upper()+"\n"
		for prop in h2h[game]:
			tabLen = 1
			out += "\t"*tabLen+prop+"\n"
			tabLen += 1
			propKey = "_".join(prop.replace("_yds", "_yd").split("_")[:-1])
			h2hType = prop.split("_")[-1]

			for matchup in h2h[game][prop]:
				odds = h2h[game][prop][matchup]["odds"].split(",")
				line = h2h[game][prop][matchup]["line"]
				arrs = []
				players = matchup.split(" v ")
				arrs = [p for p in props if p["player"].lower() in players and p["propType"] == propKey]
				if len(arrs) < 2:
					#print(arrs)
					continue

				if players[0] != arrs[0]["player"].lower():
					arrs[0], arrs[1] = arrs[1], arrs[0]

				straightOver = straightTotal = 0
				spread = 0
				if h2hType == "spread":
					spread = line
				for num1, num2 in zip(arrs[0]["lastAll"].split(","), arrs[1]["lastAll"].split(",")):
					if h2hType == "total":
						if int(num1)+int(num2) > line:
							straightOver += 1
					else:
						if int(num1) == int(num2):
							continue
						elif int(num1)+spread > int(num2):
							straightOver += 1
					straightTotal += 1
				if straightTotal:
					straightOver = round(straightOver * 100 / straightTotal)

				allPairsOver = allPairsTotal = 0
				for num1 in arrs[0]["lastAll"].split(","):
					for num2 in arrs[1]["lastAll"].split(","):
						if h2hType == "total":
							if int(num1)+int(num2) > line:
								allPairsOver += 1
						else:
							if int(num1) == int(num2):
								continue
							elif int(num1)+spread > int(num2):
								allPairsOver += 1
						allPairsTotal += 1
				if allPairsTotal:
					allPairsOver = round(allPairsOver * 100 / allPairsTotal)

				out += "\t"*tabLen+f"Straight up: {straightOver}%\n"
				out += "\t"*tabLen+f"All Pairs: {allPairsOver}%\n"
				data = arrs[0]
				for player, odds in zip(players, odds):
					out += "\t"*tabLen+f"{player.title()} {data['line']}{propKey} ({odds}):\n"
					out += "\t"*(tabLen+1)+f"{data['lastAll']}\n"
					data = arrs[1]
				if line:
					out += "\t"*tabLen+f"Line: {line}\n"
				out += "\t"*tabLen+"-----\n"



	with open(f"{prefix}static/props/h2h.txt", "w") as fh:
		fh.write(out)

def writeH2H():
	time.sleep(0.3)
	url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/88808/categories/1185?format=json"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	h2h = {}
	events = {}
	subIds = []
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		try:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		except:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		if game not in h2h:
			h2h[game] = {}
		events[event["eventId"]] = game

	for catRow in data["eventGroup"]["offerCategories"]:
		if not catRow["name"].lower().startswith("h2h"):
			continue
		for cRow in catRow["offerSubcategoryDescriptors"]:
			prop = "_".join(cRow["name"].lower().split(" ")[:-1])
			prop = prop.replace("tds", "td").replace("completions", "cmp").replace("receptions", "rec").replace("targets", "rec_tgts")
			if "offerSubcategory" not in cRow:
				subIds.append(cRow["subcategoryId"])
				continue
			for offerRow in cRow["offerSubcategory"]["offers"]:
				for row in offerRow:
					game = events[row["eventId"]]
					try:
						h2hType = row["label"].lower().split(" ")[-1]
					except:
						continue
					matchup = row["label"].lower().split("_")[0].split(" - ")[0].replace("&", "v").replace(".", "").replace("'", "").replace("-", " ")
					player1 = row["outcomes"][0]["label"].lower().replace(".", "").replace("'", "").replace("-", " ")
					odds1 = row["outcomes"][0]["oddsAmerican"]
					line = ""
					if "line" in row["outcomes"][0]:
						if player1 != matchup.split(" v ")[0]:
							line = row["outcomes"][1]["line"]
						else:
							line = row["outcomes"][0]["line"]
					player2 = row["outcomes"][1]["label"].lower().replace(".", "").replace("'", "").replace("-", " ")
					odds2 = row["outcomes"][1]["oddsAmerican"]

					h2hProp = prop+"_"+h2hType
					if h2hProp not in h2h[game]:
						h2h[game][h2hProp] = {}
					h2h[game][h2hProp][matchup] = {
						"line": line,
						player1: odds1,
						player2: odds2,
					}

	for subCatId in subIds:
		time.sleep(0.4)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/88808/categories/1185/subcategories/{subCatId}?format=json"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			try:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			except:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			if game not in h2h:
				h2h[game] = {}
			events[event["eventId"]] = game

		for catRow in data["eventGroup"]["offerCategories"]:
			if not catRow["name"].lower().startswith("h2h"):
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				prop = "_".join(cRow["name"].lower().split(" ")[:-1])
				if prop == "pass_completions":
					prop = "pass_cmp"
				if "offerSubcategory" not in cRow:
					continue

				for offerRow in cRow["offerSubcategory"]["offers"]:
					for row in offerRow:
						game = events[row["eventId"]]
						try:
							h2hType = row["label"].lower().split(" ")[-1]
						except:
							continue
						matchup = row["label"].lower().split("_")[0].split(" - ")[0].replace("&", "v").replace(".", "").replace("'", "").replace("-", " ")
						player1 = row["outcomes"][0]["label"].lower().replace(".", "").replace("'", "").replace("-", " ")
						odds1 = row["outcomes"][0]["oddsAmerican"]
						line = ""
						if "line" in row["outcomes"][0]:
							if player1 != matchup.split(" v ")[0]:
								line = row["outcomes"][1]["line"]
							else:
								line = row["outcomes"][0]["line"]
						player2 = row["outcomes"][1]["label"].lower().replace(".", "").replace("'", "").replace("-", " ")
						odds2 = row["outcomes"][1]["oddsAmerican"]

						odds = [odds1,odds2]
						if player1 == "over":
							ps = row["label"].lower().split(" - ")[0].split(" & ")
							player1 = ps[0].replace(".", "").replace("'", "").replace("-", " ")
							player2 = ps[1].replace(".", "").replace("'", "").replace("-", " ")

						h2hProp = prop+"_"+h2hType
						if h2hProp not in h2h[game]:
							h2h[game][h2hProp] = {}
						h2h[game][h2hProp][matchup] = {
							"line": line,
							player1: odds1,
							player2: odds2,
						}

	with open(f"{prefix}static/props/h2h.json", "w") as fh:
		json.dump(h2h, fh, indent=4)

def addNumSuffix(val):
	if val == "":
		return ""
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

def getTeamTds(schedule):
	teamTds = {}
	wk = f"wk{CURR_WEEK+1}"
	for file in os.listdir(f"{prefix}static/profootballreference/"):
		if file.endswith("json"):
			continue
		team = file.split("/")[-1]
		wks = glob.glob(f"{prefix}static/profootballreference/{team}/wk*.json")
		for wk in sorted(wks, key=lambda k: int(k.split("/")[-1][2:-5]), reverse=True):
			with open(wk) as fh:
				stats = json.load(fh)

			week = int(wk.split("/")[-1][2:-5])
			opp = ""
			for games in schedule[f"wk{week}"]:
				if team in games.split(" @ "):
					opp = games.replace(team, "").replace(" @ ", "")
					break

			tds = 0
			for player in stats:
				tds += stats[player].get("pass_td", 0) + stats[player].get("rush_td", 0) + stats[player].get("def_td", 0) + stats[player].get("def_int_td", 0)

			if team not in teamTds:
				teamTds[team] = {"scored": [], "allowed": [0]*CURR_WEEK}
			if opp not in teamTds:
				teamTds[opp] = {"scored": [], "allowed": [0]*CURR_WEEK}
			teamTds[team]["scored"].append(int(tds))
			teamTds[opp]["allowed"][week-1] = int(tds)

	return teamTds


def teamTotals(schedule):
	with open(f"{prefix}static/profootballreference/scores.json") as fh:
		scores = json.load(fh)
	teamTds = getTeamTds(schedule)
	totals = {}
	for wk in scores:
		games = schedule[wk]
		for team in scores[wk]:
			opp = ""
			for game in games:
				if team in game.split(" @ "):
					opp = game.replace(team, "").replace(" @ ", "")
			if team not in totals:
				totals[team] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			if opp not in totals:
				totals[opp] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			totals[team]["games"] += 1
			totals[team]["ppg"] += scores[wk][team]
			totals[team]["ppga"] += scores[wk][opp]
			totals[team]["ttOvers"].append(str(scores[wk][team]))
			totals[team]["overs"].append(str(scores[wk][team] + scores[wk][opp]))

	out = "\t".join([x.upper() for x in ["team", "ppg", "ppga", "overs", "overs avg", "tt overs", "tt avg", "tot tds", "tot tds avg", "tot tds allowed", "tot tds allowed avg"]])
	out += "\n"
	#out += ":--|:--|:--|:--|:--|:--|:--\n"
	cutoff = 20
	for game in schedule[f"wk{CURR_WEEK+1}"]:
		away, home = map(str, game.split(" @ "))
		ppg = round(totals[away]["ppg"] / totals[away]["games"], 1)
		ppga = round(totals[away]["ppga"] / totals[away]["games"], 1)
		overs = ",".join(totals[away]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[away]["overs"]]) / len(totals[away]["overs"]), 1)
		ttOvers = ",".join(totals[away]["ttOvers"][:cutoff])
		ttOversAvg = round(sum([int(x) for x in totals[away]["ttOvers"]]) / len(totals[away]["ttOvers"]), 1)
		totTds = ",".join([str(x) for x in teamTds[away]["scored"]])
		totTdsAvg = round(sum(teamTds[away]["scored"]) / len(teamTds[away]["scored"]), 1)
		totTdsAllowed = ",".join([str(x) for x in teamTds[away]["allowed"][::-1]])
		totTdsAllowedAvg = round(sum(teamTds[away]["allowed"]) / len(teamTds[away]["allowed"]), 1)
		out += "\t".join([away.upper(), str(ppg), str(ppga), overs, str(oversAvg), ttOvers, str(ttOversAvg), totTds, str(totTdsAvg), totTdsAllowed, str(totTdsAllowedAvg)]) + "\n"
		ppg = round(totals[home]["ppg"] / totals[home]["games"], 1)
		ppga = round(totals[home]["ppga"] / totals[home]["games"], 1)
		overs = ",".join(totals[home]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[home]["overs"]]) / len(totals[home]["overs"]), 1)
		ttOvers = ",".join(totals[home]["ttOvers"][:cutoff])
		ttOversAvg = round(sum([int(x) for x in totals[home]["ttOvers"]]) / len(totals[home]["ttOvers"]), 1)
		totTds = ",".join([str(x) for x in teamTds[home]["scored"]])
		totTdsAvg = round(sum(teamTds[home]["scored"]) / len(teamTds[home]["scored"]), 1)
		totTdsAllowed = ",".join([str(x) for x in teamTds[home]["allowed"][::-1]])
		totTdsAllowedAvg = round(sum(teamTds[home]["allowed"]) / len(teamTds[home]["allowed"]), 1)
		out += "\t".join([home.upper(), str(ppg), str(ppga), overs, str(oversAvg), ttOvers, str(ttOversAvg), totTds, str(totTdsAvg), totTdsAllowed, str(totTdsAllowedAvg)]) + "\n"
		out += "\t".join(["-"]*11) + "\n"

	with open(f"{prefix}static/props/totals.csv", "w") as fh:
		fh.write(out)

def convertRankingsProp(prop):
	if "+" in prop:
		return prop
	elif prop in ["pass_cmp", "rec"]:
		return "cmppg"
	elif prop in ["pass_yds", "rec_yds"]:
		return "paydpg"
	elif prop in ["rush_yds"]:
		return "ydpra"
	elif prop in ["rush_att"]:
		return "ruattpg"
	elif prop in ["pass_att"]:
		return "paattpg"
	elif prop == "pass_td":
		return "patdpg"
	elif prop == "pass_int":
		return "intpg"
	elif prop == "tackles_combined":
		return "tpg"
	#return prop[0]+"pg"
	return prop

@props_blueprint.route('/props', methods=["POST"])
def props_post_route():
    favorites = request.args.get("favorites") 
    favs = []
    for data in favorites.split(";"):
    	favs.append({
    		"player": data.split("*")[0],
    		"propType": data.split("*")[1]
    	})

    with open(f"{prefix}static/favorite_props.json", "w") as fh:
    	json.dump(favs, fh, indent=4)
    return jsonify(success=1)

@props_blueprint.route('/attd')
def props_attd_route():
	teams = request.args.get("teams") or ""
	return render_template("attd.html", curr_week=CURR_WEEK, teams=teams)

@props_blueprint.route('/longest')
def props_longest_route():
	teams = request.args.get("teams") or ""
	prop = request.args.get("prop") or ""
	return render_template("longest.html", curr_week=CURR_WEEK, teams=teams, prop=prop)

@props_blueprint.route('/props')
def props_route():
	teams = request.args.get("teams") or ""
	prop = request.args.get("prop") or ""
	players = request.args.get("players") or ""
	line = request.args.get("line") or 0
	spread = request.args.get("spread") or 0
	return render_template("props.html", curr_week=CURR_WEEK, teams=teams, prop=prop, players=players, line=line, spread=spread)

@props_blueprint.route('/defprops')
def props_def_route():
	teams = request.args.get("teams") or ""
	return render_template("defprops.html", curr_week=CURR_WEEK, teams=teams)

def writeDefProps(week):
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel",
		1599: "betmgm"
	}
	prop = "tackles_combined"
	props = {}
	optionTypes = {}

	date = datetime.now()
	date = str(date)[:10]

	path = f"{prefix}static/props/wk{week+1}defprops.json"
	url = f"https://api.actionnetwork.com/web/v1/leagues/1/props/core_bet_type_70_tackles_assists?bookIds=69,68,1599&date={date.replace('-', '')}"
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

	with open(path) as fh:
		j = json.load(fh)

	with open(path, "w") as fh:
		json.dump(j, fh, indent=4)

	if "markets" not in j:
		return
	market = j["markets"][0]

	for option in market["rules"]["options"]:
		optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

	teamIds = {}
	for row in market["teams"]:
		teamIds[row["id"]] = row["abbr"].lower()

	playerIds = {}
	for row in market["players"]:
		playerIds[row["id"]] = row["full_name"].lower().replace(".", "").replace("-", " ").replace("'", "")

	books = market["books"]
	for bookData in books:
		bookId = bookData["book_id"]
		if bookId not in actionNetworkBookIds:
			continue
		for oddData in bookData["odds"]:
			player = playerIds[oddData["player_id"]]
			if player == "lawrence guy sr":
				player = "lawrence guy"
			elif player == "devin bush jr":
				player = "devin bush"
			team = teamIds[oddData["team_id"]]
			overUnder = optionTypes[oddData["option_type_id"]]
			book = actionNetworkBookIds[bookId]

			if team not in props:
				props[team] = {}
			if player not in props[team]:
				props[team][player] = {}
			if prop not in props[team][player]:
				props[team][player][prop] = {}
			if book not in props[team][player][prop]:
				props[team][player][prop][book] = {}
			props[team][player][prop][book][overUnder] = f"{overUnder[0]}{oddData['value']} ({oddData['money']})"
			if "line" not in props[team][player][prop]:
				props[team][player][prop]["line"] = f"o{oddData['value']}"
			elif oddData['value'] < float(props[team][player][prop]["line"][1:]):
				props[team][player][prop]["line"] = f"o{oddData['value']}"

	with open(f"{prefix}static/props/wk{week+1}_def.json", "w") as fh:
		json.dump(props, fh, indent=4)

def writeActionNetworkProps(week):
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel",
		1599: "betmgm"
	}
	prop = "attd"
	props = {}

	date = datetime.now()
	date = str(date)[:10]

	time.sleep(0.3)
	path = f"out"
	url = f"https://api.actionnetwork.com/web/v1/leagues/1/props/core_bet_type_62_anytime_touchdown_scorer?bookIds=69,68,1599&date={date.replace('-', '')}"
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

	with open(path) as fh:
		j = json.load(fh)

	with open(path, "w") as fh:
		json.dump(j, fh, indent=4)

	if "markets" not in j:
		return
	market = j["markets"][0]

	teamIds = {}
	for row in market["teams"]:
		teamIds[row["id"]] = row["abbr"].lower()

	playerIds = {}
	for row in market["players"]:
		playerIds[row["id"]] = row["full_name"].lower().replace(".", "").replace("-", " ").replace("'", "")

	books = market["books"]
	for bookData in books:
		bookId = bookData["book_id"]
		if bookId not in actionNetworkBookIds:
			continue
		for oddData in bookData["odds"]:
			player = playerIds[oddData["player_id"]]
			if player == "ken walker iii":
				player = "kenneth walker iii"
			team = teamIds[oddData["team_id"]]
			book = actionNetworkBookIds[bookId]

			if team not in props:
				props[team] = {}
			if player not in props[team]:
				props[team][player] = {}
			props[team][player][book] = oddData['money']

	with open(f"{prefix}static/props/attd.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(propData):
	pass

def writeGameLines():
	with open(f"{prefix}static/props/lines.json") as fh:
		lines = json.load(fh)

	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/88808/categories/492/subcategories/4518?format=json"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	events = {}
	lines = {}
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		try:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		except:
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
					if row["eventId"] not in events:
						continue
					game = events[row["eventId"]]
					gameType = row["label"].lower()

					switchOdds = False
					team1 = ""
					if gameType != "total":
						team1 = row["outcomes"][0]["label"].lower().split(" ")[0]
						if team1 in ["ny", "la"]:
							team1 = row["outcomes"][0]["label"].lower().replace(" ", "")[:3]
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

	with open(f"{prefix}static/props/lines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writePFFProps():
	with open(f"{prefix}static/props/wk{CURR_WEEK+1}.csv") as fh:
		lines = [line.strip() for line in fh.readlines() if line.strip()]

	fields = [
		"propType", "player", "position", "team", "opponent", "line", "sideOneType", "sideOneOdds", "sideTwoOdds", "sideTwoType"
	]

	idxs = {}
	headers = lines[0].split(",")
	for field in fields:
		idxs[field] = headers.index(f'"{field}"')

	props = {}
	for line in lines[1:]:
		data = line.split(",")
		currProps = {}
		for field in idxs:
			currProps[field] = data[idxs[field]].replace('"', '')

		team = getYahooTeam(currProps["team"].lower())
		player = currProps["player"].lower().title().replace("Jr.", "Jr")
		player += " "+team.upper()
		#player = translations[player]
		if player not in props:
			props[player] = {}


		props[player][currProps["propType"]] = currProps

	with open(f"{prefix}static/props.json", "w") as fh:
			json.dump(props, fh, indent=4)

def convertDKProp(mainCat, prop):
	prop = prop.replace("tds", "td").replace("completions", "cmp").replace("attempts", "att").replace("interceptions", "int").replace(" + ", "+").replace("receptions", "rec").replace("reception", "rec")
	if prop == "int":
		if mainCat == "pass":
			return "pass_int"
	elif prop.startswith("longest"):
		prop = prop.replace("completion", "rec").replace("longest", "long").split(" ")[::-1]
		prop = "_".join(prop)
		if mainCat == "pass" and prop.startswith("rec"):
			return "pass_long"
		return prop
	elif prop == "tackles+ast":
		prop = "tackles_combined"
	elif prop == "fg made":
		prop = "fgm"
	elif prop == "pat made":
		prop = "pat"

	return "_".join(prop.split(" "))

def writeProps(curr_week):
	wk = f"wk{curr_week+1}"

	props = {}
	if os.path.exists(f"{prefix}static/props/dates/{wk}.json"):
		with open(f"{prefix}static/props/dates/{wk}.json") as fh:
			props = json.load(fh)

	mainCats = {
		"pass": 1000,
		"rush/rec": 1001,
		"dst": 1002
	}

	for mainCat in mainCats:
		time.sleep(0.4)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/88808/categories/{mainCats[mainCat]}?format=json"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
			#startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=5)
			#if startDt.day != int(date[-2:]):
			#	continue
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				if "teamShortName2" not in event:
					name2 = "tb"
				else:
					name2 = event["teamShortName2"].lower()
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(name2)
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
				if cRow["name"].startswith("Alt") or cRow["name"].startswith("Flash") or cRow["name"].endswith("H2H") or cRow["name"].startswith("Race to") or cRow["name"].endswith("Leaders") or "live" in cRow["name"].lower() or cRow["name"].lower() == "next play":
					continue
				prop = convertDKProp(mainCat, cRow["name"].lower())
				subCats[prop] = cRow["subcategoryId"]

		for prop in subCats:
			time.sleep(0.4)
			url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/88808/categories/{mainCats[mainCat]}/subcategories/{subCats[prop]}?format=json"
			outfile = "out"
			#print(url)
			call(["curl", "-k", url, "-o", outfile])

			with open("out") as fh:
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
							#print(row)
							if "participant" not in row["outcomes"][0]:
								continue
							player = row["outcomes"][0]["participant"].lower().replace(".", "").replace("'", "").replace("-", " ")
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

	with open(f"{prefix}static/props/dates/{wk}.json", "w") as fh:
		json.dump(props, fh, indent=4)

@props_blueprint.route('/getH2HNFLProps')
def getH2HProps_route():
	res = []

	teamsArg = request.args.get("teams") or ""
	if teamsArg:
		teamsArg = teamsArg.lower().split(",")
	playersArg = request.args.get("players") or []
	if playersArg:
		playersArg = players.split(",")

	date = datetime.now()
	date = str(date)[:10]

	wkStr = f"wk{CURR_WEEK+1}"
	with open(f"{prefix}static/props/dates/{wkStr}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/profootballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/profootballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/profootballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/props/h2h.json") as fh:
		h2h = json.load(fh)

	res = []
	playerStats = {}
	for game in h2h:
		teams = game.split(" @ ")

		if teamsArg and teams[0] not in teamsArg:
			continue
		if teamsArg and teams[1] not in teamsArg:
			continue

		for team in teams:
			if team not in playerStats:
				playerStats[team] = {}
			for file in glob.glob(f"{prefix}static/profootballreference/{team}/*.json"):
				wk = file.split("/")[-1][:-5]
				if wk not in playerStats[team]:
					with open(file) as fh:
						playerStats[team][wk] = json.load(fh)
		for propKey in h2h[game]:
			h2hType = propKey.split("_")[-1]
			prop = propKey.replace("_"+h2hType, "")
			prop = prop.replace("tds", "td")
			if prop.startswith("td") or "+" in prop or "fgs" in prop:
				continue
			for matchup in h2h[game][propKey]:
				players = matchup.replace("'", "").replace(".", "").replace("-", " ").split(" v ")
				line = h2h[game][propKey][matchup]["line"] or 0

				arrs = [[], []]
				lines = [0,0]
				playerTeams = ["", ""]
				for pIdx, player in enumerate(players):
					if player == "gabriel davis":
						player = "gabe davis"
					elif player == "travis etienne":
						player = "travis etienne jr"
					elif player == "terrace marshall":
						player = "terrace marshall jr"
					team = game.split(" @ ")[pIdx]
					if player not in roster[team]:
						team = game.split(" @ ")[0] if pIdx == 1 else game.split(" @ ")[1]
					playerTeams[pIdx] = team
					if game in propData and player in propData[game]:
						if prop in propData[game][player]:
							lines[pIdx] = propData[game][player][prop]["line"]
					for wk in sorted(playerStats[team], key=lambda k: int(k[2:]), reverse=True):
						if player in playerStats[team][wk] and prop in playerStats[team][wk][player]:
							arrs[pIdx].append(int(playerStats[team][wk][player][prop]))

				straightOver = straightTotal = 0
				for num1, num2 in zip(arrs[0], arrs[1]):
					if h2hType == "total":
						if num1+num2 > line:
							straightOver += 1
					else:
						if num1 == num2:
							continue
						elif num1+line > num2:
							straightOver += 1
					straightTotal += 1
				if straightTotal:
					straightOver = round(straightOver * 100 / straightTotal)

				allPairsOver = allPairsTotal = allPairsOdds = 0
				for num1 in arrs[0]:
					for num2 in arrs[1]:
						if h2hType == "total":
							if num1+num2 > line:
								allPairsOver += 1
						else:
							if num1 == num2:
								continue
							elif num1+line > num2:
								allPairsOver += 1
						allPairsTotal += 1
				if allPairsTotal:
					allPairsOver = round(allPairsOver * 100 / allPairsTotal)
					if allPairsOver == 100:
						allPairsOdds = -100000
					else:
						allPairsOdds = round((100*allPairsOver) / (-100+allPairsOver))
						if allPairsOver and allPairsOver < 50:
							allPairsOdds = round((100*(100-allPairsOver)) / (-100+(100-allPairsOver)))

				if "over" in h2h[game][propKey][matchup]:
					odds1 = h2h[game][propKey][matchup]["over"]
					odds2 = h2h[game][propKey][matchup]["under"]
				else:
					odds1 = h2h[game][propKey][matchup][players[0]]
					odds2 = h2h[game][propKey][matchup][players[1]]

				team1, team2 = playerTeams[0], playerTeams[1]
				ranks = ["", ""]
				rankingsProp = convertRankingsProp(prop)
				if "o"+rankingsProp in rankings[team1]:
					ranks[0] = rankings[team1]['o'+rankingsProp]['rank']
				if "o"+rankingsProp in rankings[team2]:
					ranks[1] = rankings[team2]['o'+rankingsProp]['rank']

				#print(team2, prop, ranks[1])
				res.append({
					"game": game,
					"prop": prop,
					"type": h2hType,
					"line": line or "ML",
					"player1": players[0].split(" ")[1].title(),
					"team1": team1,
					"rank1": ranks[0],
					"matchup": matchup,
					"odds1": odds1,
					"line1": lines[0],
					"log1": ",".join([str(x) for x in arrs[0]]),
					"player2": players[1].split(" ")[1].title(),
					"team2": team2,
					"rank2": ranks[1],
					"odds2": odds2,
					"line2": lines[1],
					"log2": ",".join([str(x) for x in arrs[1]]),
					"straightOver": straightOver,
					"allPairsOver": allPairsOver,
					"allPairsOdds": allPairsOdds
				})

	return jsonify(res)

@props_blueprint.route('/h2hnfl')
def h2hprops_route():
	teams = players = ""
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("players"):
		players = request.args.get("players")
	return render_template("h2hnfl.html", teams=teams, players=players)

def writeLongestProps(week):
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel",
		1599: "betmgm"
	}
	prop = ""
	props = {}
	optionTypes = {}

	date = datetime.now()
	date = str(date)[:10]

	apis = ["core_bet_type_58_longest_rush", "core_bet_type_59_longest_reception", "core_bet_type_60_longest_completion"]
	for api, prop in zip(apis, ["rush_long", "rec_long", "pass_long"]):
		time.sleep(0.3)
		path = f"out"
		url = f"https://api.actionnetwork.com/web/v1/leagues/1/props/{api}?bookIds=69,68,1599&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")
		time.sleep(0.4)

		with open(path) as fh:
			j = json.load(fh)

		if "markets" not in j:
			return
		market = j["markets"][0]

		for option in market["rules"]["options"]:
			optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

		teamIds = {}
		for row in market["teams"]:
			teamIds[row["id"]] = row["abbr"].lower()

		playerIds = {}
		for row in market["players"]:
			playerIds[row["id"]] = row["full_name"].lower().replace(".", "").replace("-", " ").replace("'", "")

		books = market["books"]
		for bookData in books:
			bookId = bookData["book_id"]
			if bookId not in actionNetworkBookIds:
				continue
			for oddData in bookData["odds"]:
				player = playerIds[oddData["player_id"]]
				team = teamIds[oddData["team_id"]]
				overUnder = optionTypes[oddData["option_type_id"]]
				book = actionNetworkBookIds[bookId]

				if team not in props:
					props[team] = {}
				if player not in props[team]:
					props[team][player] = {}
				if prop not in props[team][player]:
					props[team][player][prop] = {}
				if book not in props[team][player][prop]:
					props[team][player][prop][book] = {}
				props[team][player][prop][book][overUnder] = f"{overUnder[0]}{oddData['value']} ({oddData['money']})"
				if "line" not in props[team][player][prop]:
					props[team][player][prop]["line"] = f"o{oddData['value']}"
				elif oddData['value'] < float(props[team][player][prop]["line"][1:]):
					props[team][player][prop]["line"] = f"o{oddData['value']}"

	with open(f"{prefix}static/props/longest.json", "w") as fh:
		json.dump(props, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("--h2h", action="store_true", help="H2H")
	parser.add_argument("--lines", action="store_true", help="Lines")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()
	week = CURR_WEEK

	if args.week:
		week = args.week


	if args.h2h:
		writeH2H()
	elif args.lines:
		writeGameLines()
	elif args.cron:
		writeProps(week)
		writeActionNetworkProps(week)
		writeLongestProps(week)
		writeH2H()