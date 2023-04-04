import argparse
import datetime
import glob
import json
import math
import os
import operator
import re
import time

from bs4 import BeautifulSoup as BS
from bs4 import Comment
import datetime
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

def write_stats(date):
	with open(f"{prefix}static/baseballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	if date not in boxscores:
		print("No games found for this date")
		exit()

	allStats = {}
	for game in boxscores[date]:
		away, home = map(str, game.split(" @ "))

		if away not in allStats:
			allStats[away] = {}
		if home not in allStats:
			allStats[home] = {}


		gameId = boxscores[date][game].split("/")[-1].split("=")[-1]
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/baseball/mlb/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
		outfile = "outmlb2"
		time.sleep(0.3)
		call(["curl", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		if "code" in data and data["code"] == 400:
			continue

		if "players" not in data["boxscore"]:
			continue
		for teamRow in data["boxscore"]["players"]:
			team = teamRow["team"]["abbreviation"].lower()
			if team not in playerIds:
				playerIds[team] = {}

			for statRow in teamRow["statistics"]:
				title = statRow["type"]

				headers = [h.lower() for h in statRow["labels"]]

				for playerRow in statRow["athletes"]:
					player = playerRow["athlete"]["displayName"].lower().replace("'", "").replace(".", "")
					playerId = int(playerRow["athlete"]["id"])

					playerIds[team][player] = playerId
					if player not in allStats[team]:
						allStats[team][player] = {}

					for header, stat in zip(headers, playerRow["stats"]):
						if header == "h-ab":
							continue
						if header == "k" and title == "batting":
							header = "so"
						if header in ["pc-st"]:
							pc, st = map(float, stat.split("-"))
							allStats[team][player]["pc"] = pc
							allStats[team][player]["st"] = st
						elif header in ["bb", "hr", "r", "h"] and title == "pitching":
							allStats[team][player][header+"_allowed"] = float(stat)
						else:
							val = stat
							try:
								val = float(val)
							except:
								val = 0.0
							allStats[team][player][header] = val
					if "ab" in allStats[team][player]:
						_3b = allStats[team][player].get("3b", 0)
						_2b = allStats[team][player].get("2b", 0)
						hr = allStats[team][player]["hr"]
						h = allStats[team][player]["h"]
						_1b = h - (_3b+_2b+hr)
						allStats[team][player]["1b"] = _1b
						allStats[team][player]["tb"] = 4*hr + 3*_3b + 2*_2b + _1b

		for rosterRow in data["rosters"]:
			team = rosterRow["team"]["abbreviation"].lower()
			for playerRow in rosterRow["roster"]:
				player = playerRow["athlete"]["displayName"].lower().replace("'", "").replace(".", "")
				for statRow in playerRow["stats"]:
					hdr = statRow["shortDisplayName"].lower()
					if hdr not in allStats[team][player]:
						allStats[team][player][hdr] = statRow["value"]

	for team in allStats:
		if not os.path.isdir(f"{prefix}static/baseballreference/{team}"):
			os.mkdir(f"{prefix}static/baseballreference/{team}")
		with open(f"{prefix}static/baseballreference/{team}/{date}.json", "w") as fh:
			json.dump(allStats[team], fh, indent=4)

	write_totals()

	with open(f"{prefix}static/baseballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/baseballreference/"):
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/baseballreference/{team}/*.json"):
			with open(file) as fh:
				stats = json.load(fh)
			for player in stats:
				if player not in totals[team]:
					totals[team][player] = stats[player]
				else:
					for header in stats[player]:
						if header not in totals[team][player]:
							totals[team][player][header] = 0
						totals[team][player][header] += stats[player][header]

				if "gamesPlayed" not in totals[team][player]:
					totals[team][player]["gamesPlayed"] = 0
				totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/baseballreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def write_schedule(date):
	url = f"https://www.espn.com/mlb/schedule/_/date/{date.replace('-', '')}"
	outfile = "outmlb"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/baseballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)

	schedule[date] = []

	date = ""

	for table in soup.findAll("div", class_="ResponsiveTable"):
		if table.find("div", class_="Table__Title"):
			date = table.find("div", class_="Table__Title").text.strip()
			date = str(datetime.datetime.strptime(date, "%A, %B %d, %Y"))[:10]
		schedule[date] = []
		if date not in boxscores:
			boxscores[date] = {}
		if date not in scores:
			scores[date] = {}

		for row in table.findAll("tr")[1:]:
			tds = row.findAll("td")
			try:
				awayTeam = tds[0].findAll("a")[-1].get("href").split("/")[-2]
				homeTeam = tds[1].findAll("a")[-1].get("href").split("/")[-2]
			except:
				continue
			boxscore = tds[2].find("a").get("href")
			score = tds[2].find("a").text.strip()
			if score.lower() == "postponed":
				continue
			if ", " in score and os.path.exists(f"{prefix}static/baseballreference/{awayTeam}/{date}.json"):
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

def write_averages():
	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/baseballreference/averages.json") as fh:
		averages = json.load(fh)

	with open(f"{prefix}static/baseballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	currYear = str(datetime.datetime.now())[:4]

	#year = "2022"
	yearStats = {}
	for year in os.listdir(f"{prefix}static/mlbprops/stats/"):
		year = year[:4]
		if os.path.exists(f"{prefix}static/mlbprops/stats/{year}.json"):
			with open(f"{prefix}static/mlbprops/stats/{year}.json") as fh:
				stats = json.load(fh)
			yearStats[year] = stats

	for team in ids:
		if team not in averages:
			averages[team] = {}
		if team not in lastYearStats:
			lastYearStats[team] = {}

		for player in ids[team]:
			pId = ids[team][player]
			if player in averages[team]:
				pass
				continue
			
			averages[team][player] = {}
			lastYearStats[team][player] = {}

			time.sleep(0.175)
			url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}"
			outfile = "outmlb"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")
			#print(url)
			select = soup.find("div", class_="gamelog").find("select", class_="dropdown__select")
			if not select:
				continue
			years = [y.text for y in select.findAll("option")]

			for year in years:
				if len(year) != 4:
					for title in soup.find("div", class_="gamelog").findAll("div", class_="Table__Title"):
						if "regular" in title.text.lower():
							year = title.text.lower()[:4]
					if len(year) != 4:
						continue
				if year not in yearStats:
					yearStats[year] = {}
				if team not in yearStats[year]:
					yearStats[year][team] = {}
				
				if player not in yearStats[year][team]:
					yearStats[year][team][player] = {}
				elif year != currYear:
					continue

				yearStats[year][team][player] = {}
				gamesPlayed = 0

				time.sleep(0.175)
				url = f"https://www.espn.com/mlb/player/gamelog/_/id/{pId}/type/mlb/year/{year}"
				#print(url)
				outfile = "outmlb"
				call(["curl", "-k", url, "-o", outfile])
				soup = BS(open(outfile, 'rb').read(), "lxml")

				headers = []
				for row in soup.findAll("tr"):
					try:
						title = row.findPrevious("div", class_="Table__Title").text.lower()
					except:
						title = ""
					if "regular season" not in title:
						continue
					if not headers and row.text.lower().startswith("date"):
						tds = row.findAll("td")[3:]
						if not tds:
							tds = row.findAll("th")[3:]
						for td in tds:
							headers.append(td.text.strip().lower())
					elif row.text.startswith("Totals"):
						yearStats[year][team][player]["tot"] = {}
						for idx, td in enumerate(row.findAll("td")[1:]):
							header = headers[idx]
							try:
								val = float(td.text.strip())
							except:
								val = "-"
							yearStats[year][team][player]["tot"][header] = val
						yearStats[year][team][player]["tot"]["gamesPlayed"] = gamesPlayed
						if "ab" in yearStats[year][team][player]["tot"]:
							_3b = yearStats[year][team][player]["tot"]["3b"]
							_2b = yearStats[year][team][player]["tot"]["2b"]
							hr = yearStats[year][team][player]["tot"]["hr"]
							h = yearStats[year][team][player]["tot"]["h"]
							_1b = h - (_3b+_2b+hr)
							yearStats[year][team][player]["tot"]["1b"] = _1b
							yearStats[year][team][player]["tot"]["tb"] = 4*hr + 3*_3b + 2*_2b + _1b
					else:
						tds = row.findAll("td")
						if len(tds) > 1 and ("@" in tds[1].text or "vs" in tds[1].text):
							date = str(datetime.datetime.strptime(tds[0].text.strip()+"/"+year, "%a %m/%d/%Y")).split(" ")[0]
							gamesPlayed += 1
							isAway = "@" in tds[1].text
							try:
								vs = tds[1].findAll("a")[-1].get("href").split("/")[-2]
							except:
								continue

							if date not in yearStats[year][team][player]:
								yearStats[year][team][player][date] = {}
							else:
								date = date + " gm2"

							yearStats[year][team][player][date] = {
								"isAway": isAway,
								"vs": vs
							}
							for idx, td in enumerate(tds[3:]):
								header = headers[idx]

								val = 0.0
								if header in ["dec", "rel"]:
									val = td.text.strip()
								else:
									try:
										val = float(td.text.strip())
									except:
										val = "-"

								yearStats[year][team][player][date][header] = val
							if "ab" in yearStats[year][team][player][date]:
								_3b = yearStats[year][team][player][date]["3b"]
								_2b = yearStats[year][team][player][date]["2b"]
								hr = yearStats[year][team][player][date]["hr"]
								h = yearStats[year][team][player][date]["h"]
								_1b = h - (_3b+_2b+hr)
								yearStats[year][team][player][date]["1b"] = _1b
								yearStats[year][team][player][date]["tb"] = 4*hr + 3*_3b + 2*_2b + _1b

				with open(f"{prefix}static/mlbprops/stats/{year}.json", "w") as fh:
					json.dump(yearStats[year], fh, indent=4)

	writeYearAverages()

def writeYearAverages():
	averages = {}
	statsVsTeam = {}
	for file in os.listdir(f"{prefix}static/mlbprops/stats/"):
		year = file[:4]

		with open(f"{prefix}static/mlbprops/stats/{file}") as fh:
			yearStats = json.load(fh)

		for team in yearStats:

			if team not in averages:
				averages[team] = {}
			if team not in statsVsTeam:
				statsVsTeam[team] = {}

			for player in yearStats[team]:
				tot = {}
				playerStats = yearStats[team][player]
				if player not in averages[team]:
					averages[team][player] = {"tot": {}}
				if True or "tot" not in playerStats:
					gamesPlayed = totalHitGames = total2HitGames = 0
					for dt in playerStats:
						if dt == "tot":
							continue
						gamesPlayed += 1
						gameStats = playerStats[dt]
						currOpp = gameStats["vs"]
						if currOpp not in statsVsTeam[team]:
							statsVsTeam[team][currOpp] = {}
						if player not in statsVsTeam[team][currOpp]:
							statsVsTeam[team][currOpp][player] = {"gamesPlayed": 0}

						statsVsTeam[team][currOpp][player]["gamesPlayed"] += 1
						if "ab" in gameStats and "h+r+rbi" not in gameStats:
							gameStats["h+r+rbi"] = 0
						for header in gameStats:
							if header not in ["isAway", "vs"]:
								if header not in statsVsTeam[team][currOpp][player]:
									statsVsTeam[team][currOpp][player][header] = 0
								if header not in tot:
									tot[header] = 0
								try:
									val = 0
									for p in header.split("+"):
										val += gameStats[p]
									tot[header] += val
									statsVsTeam[team][currOpp][player][header] += val
									if header in ["h", "1b", "rbi", "h+r+rbi", "bb", "hr", "sb", "so", "k", "er"]:

										if header+"Overs" not in statsVsTeam[team][currOpp][player]:
											statsVsTeam[team][currOpp][player][header+"Overs"] = {}
										if header+"Overs" not in tot:
											tot[header+"Overs"] = {}

										for i in range(1, int(val)+1):
											if i not in tot[header+"Overs"]:
												tot[header+"Overs"][i] = 0
											if i not in statsVsTeam[team][currOpp][player][header+"Overs"]:
												statsVsTeam[team][currOpp][player][header+"Overs"][i] = 0

											statsVsTeam[team][currOpp][player][header+"Overs"][i] += 1
											tot[header+"Overs"][i] += 1
								except:
									pass

					tot["gamesPlayed"] = gamesPlayed
					yearStats[team][player]["tot"] = tot
				else:
					tot = playerStats["tot"]
				
				averages[team][player][year] = tot
				for header in tot:
					if header not in averages[team][player]["tot"]:
						averages[team][player]["tot"][header] = 0
					try:
						averages[team][player]["tot"][header] += tot[header]
					except:
						pass

		with open(f"{prefix}static/mlbprops/stats/{file}", "w") as fh:
			json.dump(yearStats, fh, indent=4)

	with open(f"{prefix}static/baseballreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	with open(f"{prefix}static/baseballreference/statsVsTeam.json", "w") as fh:
		json.dump(statsVsTeam, fh, indent=4)

def write_roster():

	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	roster = {}
	for team in os.listdir(f"{prefix}static/baseballreference/"):

		if team not in playerIds:
			playerIds[team] = {}

		if team.endswith(".json"):
			continue

		roster[team] = {}
		time.sleep(0.2)
		url = f"https://www.espn.com/mlb/team/roster/_/name/{team}/"
		outfile = "outmlb"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for table in soup.findAll("table"):
			for row in table.findAll("tr")[1:]:
				nameLink = row.findAll("td")[1].find("a").get("href").split("/")
				fullName = row.findAll("td")[1].find("a").text.lower().replace("'", "").replace("-", " ").replace(".", "")
				playerId = int(nameLink[-1])
				playerIds[team][fullName] = playerId
				roster[team][fullName] = row.findAll("td")[2].text.strip()

	with open(f"{prefix}static/baseballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/baseballreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

def convertTeamRankingsTeam(team):
	if team == "washington":
		return "wsh"
	elif team == "chi sox":
		return "chw"
	elif team == "chi cubs":
		return "chc"
	elif team == "sf giants":
		return "sf"
	elif team == "kansas city":
		return "kc"
	elif team == "san diego":
		return "sd"
	elif team == "tampa bay":
		return "tb"
	return team.replace(".", "").replace(" ", "")[:3]

def write_rankings():
	baseUrl = "https://www.teamrankings.com/mlb/stat/"
	pages = ["at-bats-per-game", "strikeouts-per-game", "walks-per-game", "runs-per-game", "hits-per-game", "home-runs-per-game", "singles-per-game", "doubles-per-game", "rbis-per-game", "total-bases-per-game", "earned-run-average", "earned-runs-against-per-game", "strikeouts-per-9", "home-runs-per-9", "hits-per-9", "walks-per-9", "opponent-stolen-bases-per-game", "opponent-total-bases-per-game", "opponent-rbis-per-game", "opponent-at-bats-per-game"]
	ids = ["ab", "so", "bb", "r", "h", "hr", "1b", "2b", "rbi", "tb", "era", "er", "k", "hr_allowed", "hits_allowed", "bb_allowed", "opp_sb", "opp_tb", "opp_rbi", "opp_ab"]

	rankings = {}
	for dt in ["", "?date=2022-11-06"]:
		rankingPrefix = "ly_" if dt else ""
		for idx, page in enumerate(pages):
			url = baseUrl+page+dt
			outfile = "outmlb2"
			time.sleep(0.2)
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			for row in soup.find("table").findAll("tr")[1:]:
				tds = row.findAll("td")
				team = convertTeamRankingsTeam(row.find("a").text.lower())
				if team not in rankings:
					rankings[team] = {}
				ranking = rankingPrefix+ids[idx]
				if ranking not in rankings[team]:
					rankings[team][ranking] = {}

				rankings[team][ranking] = {
					"rank": int(tds[0].text),
					"season": float(tds[2].text.replace("--", "0").replace("%", "")),
					"last3": float(tds[3].text.replace("--", "0").replace("%", ""))
				}

		combined = []
		for team in rankings:
			combined.append({
				"team": team,
				"val": rankings[team][f"{rankingPrefix}h"]["season"]+rankings[team][f"{rankingPrefix}r"]["season"]+rankings[team][f"{rankingPrefix}rbi"]["season"]
			})

		for idx, x in enumerate(sorted(combined, key=lambda k: k["val"], reverse=True)):
			rankings[x["team"]][f"{rankingPrefix}h+r+rbi"] = {
				"rank": idx+1,
				"season": x["val"]
			}

		combined = []
		for team in rankings:
			combined.append({
				"team": team,
				"val": rankings[team][f"{rankingPrefix}hits_allowed"]["season"]+rankings[team][f"{rankingPrefix}er"]["season"]
			})

		for idx, x in enumerate(sorted(combined, key=lambda k: k["val"], reverse=True)):
			rankings[x["team"]][f"{rankingPrefix}h+r+rbi_allowed"] = {
				"rank": idx+1,
				"season": x["val"]
			}

	with open(f"{prefix}static/baseballreference/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)

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
	return team

# write batter vs pitcher
def writeBVP():

	with open(f"{prefix}static/baseballreference/bvp.json") as fh:
		bvp = json.load(fh)

	date = str(datetime.datetime.now())[:10]
	if False:
		date = str(datetime.datetime.now() + datetime.timedelta(days=1))[:10]

	for hotCold in ["hot", "cold"]:
		outfile = "outmlb2"
		time.sleep(0.2)
		url = f"https://www.rotowire.com/baseball/tables/matchup.php?type={hotCold}batter&bab=1&bhothr=1&bhotavg=1&bhottops=1&start={date}&end={date}"
		call(["curl", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		for row in data:
			pitcher = row["pitcher"].lower()
			team = convertRotoTeam(row["team"])
			opp = convertRotoTeam(row["opponent"])
			player = row["player"].lower().replace(".", "").replace("'", "")

			matchup = f"{player} v {pitcher}"

			if team not in bvp:
				bvp[team] = {}
			if matchup not in bvp[team]:
				bvp[team][matchup] = {}

			for key, hdr in [("atbats", "ab"), ("hits", "h"), ("hr", "hr"), ("rbi", "rbi"), ("bb", "bb"), ("k", "so")]:
				bvp[team][matchup][hdr] = int(row[key])


	with open(f"{prefix}static/baseballreference/bvp.json", "w") as fh:
		json.dump(bvp, fh, indent=4)



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("--bvp", action="store_true", help="Batter Vs Pitcher")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--averages", help="Last Yr Averages", action="store_true")
	parser.add_argument("--rankings", help="Rankings", action="store_true")
	parser.add_argument("--roster", help="Roster", action="store_true")
	parser.add_argument("--schedule", help="Schedule", action="store_true")
	parser.add_argument("--totals", help="Totals", action="store_true")
	parser.add_argument("--stats", help="Stats", action="store_true")
	parser.add_argument("--pitching", help="Pitching", action="store_true")
	parser.add_argument("--ttoi", help="Team TTOI", action="store_true")
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	if args.start:
		curr_week = args.start

	date = args.date
	if not date:
		date = datetime.datetime.now()
		date = str(date)[:10]

	if args.averages:
		write_averages()
	elif args.bvp:
		writeBVP()
	elif args.rankings:
		write_rankings()
	elif args.roster:
		write_roster()
	elif args.pitching:
		write_pitching()
	elif args.cron:
		write_rankings()
		writeBVP()
		write_stats(date)
		write_schedule(date)

	#write_pitching()
	#writeYearAverages()
	#write_stats(date)
	#write_totals()