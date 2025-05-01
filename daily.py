import os
import time
import json
import nodriver as uc
import argparse
import subprocess
import threading
import queue
from bs4 import BeautifulSoup as BS

from controllers.shared import *
from datetime import datetime, timedelta

q = queue.Queue()
lock = threading.Lock()

def writeSchedule(sport, date):
	if not date:
		date = str(datetime.now())[:10]

	with open(f"static/{sport}/schedule.json") as fh:
		schedule = json.load(fh)

	url = f"https://www.espn.com/{sport}/schedule?date={date.replace('-', '')}"
	outfile = "outDailySchedule"
	os.system(f"curl {url} -o {outfile}")
	soup = BS(open(outfile), "lxml")

	for div in soup.find_all("div", class_="ScheduleTables"):
		date = div.select(".Table__Title")[0].text.lower()
		if "spring training" in date:
			continue

		date = str(datetime.strptime(date.split(" - ")[0].strip(), "%A, %B %d, %Y"))[:10]
		schedule[date] = []
		seen = {}
		for tbody in div.find_all("tbody")[::-1]:
			for row in tbody.find_all("tr"):
				tds = row.find_all("td")
				awayTeam = tds[0].find("a").get("href").split("/")[-2]
				homeTeam = tds[1].find("a").get("href").split("/")[-2]
				result = tds[2]
				href = result.find("a").get("href")
				score = start = ""

				if ", " in result.text:
					winSide, lossSide = map(str, result.text.lower().split(", "))
					winTeam, winScore = map(str, winSide.split(" "))
					lossTeam, lossScore = map(str, lossSide.split(" (")[0].split(" "))

					score = f"{winScore}-{lossScore}"
					if winTeam != awayTeam:
						score = f"{lossScore}-{winScore}"
				else:
					start = result.text.strip()

				game = f"{awayTeam} @ {homeTeam}"
				if game in seen:
					game = f"{awayTeam}-gm2 @ {homeTeam}-gm2"
				seen[game] = True
				j = {
					"game": game,
					"link": "https://www.espn.com"+href,
					"score": score,
					"start": start
				}
				schedule[date].append(j)

	with open(f"static/{sport}/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

def getPlayType(sport, play):
	txt = play["txt"].lower()
	if sport == "mlb":
		if "single" in txt:
			return "1b"
		elif "double" in txt:
			return "2b"
		elif "triple" in txt:
			return "3b"
	return ""

def writeStats(sport, date):
	if not date:
		date = str(datetime.now())[:10]
	with open(f"static/{sport}/schedule.json") as fh:
		schedule = json.load(fh)

	if date not in schedule:
		print("Not in Schedule")
		exit()

	stats = nested_dict()
	outfile = "outDailyStats"
	for gameData in schedule[date]:
		result = subprocess.run(["curl", gameData["link"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		soup = BS(result.stdout, "html.parser")

		script_tag = soup.find('script', string=lambda t: t and 'window[\'__espnfitt__\']' in t)
		if not script_tag:
			return

		content = script_tag.string
		j = content.split("window['__espnfitt__']=")[-1].rstrip(";")
		data = json.loads(j)

		try:
			boxscore = data["page"]["content"]["gamepackage"]["bxscr"]
			plays = data["page"]["content"]["gamepackage"]["plys"]
		except:
			continue

		playData = {}
		for play in plays:
			playData[play["id"]] = play

		awayTeam, homeTeam = map(str, gameData["game"].split(" @ "))
		for team, teamStats in zip([awayTeam, homeTeam], boxscore):
			awayHome = "H" if team == homeTeam else "A"
			opp = awayTeam if team == homeTeam else homeTeam
			for pos, posStats in zip(["h", "p"], teamStats["stats"]):
				for playerStats in posStats["athlts"]:
					player = parsePlayer(playerStats["athlt"]["dspNm"])
					stats[team][player]["awayHome"] = awayHome
					stats[team][player]["opp"] = opp

					for play in playerStats.get("plys", []):
						p = getPlayType(sport, playData[play])
						if p:
							stats[team][player][p] = stats[team][player].get(p, 0) + 1
					
					for k, v in zip(posStats["lbls"], playerStats["stats"]):
						k = k.lower()
						if k == "k" and pos == "h":
							k = "so"
						if "-" in k:
							k1,k2 = map(str, k.split("-"))
							v1,v2 = map(int, v.split("-"))
							stats[team][player][k1] = v1
							stats[team][player][k2] = v2
						elif "." in v:
							stats[team][player][k] = float(v)
							if k == "ip":
								stats[team][player]["outs"] = int(float(v))*3 + int(str(v).split(".")[-1])
						elif v == "INF":
							stats[team][player][k] = float('inf')
						else:
							if k in ["h", "bb", "hr"] and pos == "p":
								k += "_allowed"
							try:
								stats[team][player][k] = int(v)
							except:
								stats[team][player][k] = v

				if sport == "mlb" and pos == "h":
					for team in stats:
						for player in stats[team]:
							if stats[team][player].get("ip"):
								continue
							tb = 0
							#for k in ["1b", "2b", "3b", "hr", "h", "r", "rbi"]:
							for k in ["1b", "2b", "3b", "hr"]:
								if k not in stats[team][player]:
									stats[team][player][k] = 0
							pStats = stats[team][player]
							stats[team][player]["tb"] = pStats["1b"] + pStats["2b"] + pStats["3b"] + pStats["hr"]
							stats[team][player]["h+r+rbi"] = pStats.get("h", 0) + pStats.get("r", 0) + pStats.get("rbi", 0)


	with open(f"static/splits/{sport}/{date}.json", "w") as fh:
		json.dump(stats, fh)

	writeTeamSplits()

def writeTeamSplits():
	data = nested_dict()
	for file in sorted(os.listdir(f"static/splits/{sport}/")):
		if "-" not in file:
			continue
		dt = file.split(".")[0]
		path = f"static/splits/{sport}/{file}"

		with open(path) as fh:
			gameData = json.load(fh)

		for team, players in gameData.items():
			#print(file, team, players)
			team = team.replace("-gm2", "")
			for player, playerData in players.items():
				playerData["dt"] = dt
				for prop, val in playerData.items():
					data[team][player].setdefault(prop, [])
					data[team][player][prop].append(val)

	for team, players in data.items():
		with open(f"static/splits/{sport}/{team}.json", "w") as fh:
			json.dump(players, fh)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--date", "-d")
	parser.add_argument("--sport")
	parser.add_argument("--nhl", action="store_true")
	parser.add_argument("--mlb", action="store_true")
	parser.add_argument("-u", "--update", action="store_true")
	parser.add_argument("--run", action="store_true")
	parser.add_argument("--schedule", action="store_true")
	parser.add_argument("--stats", action="store_true")
	parser.add_argument("--tmrw", action="store_true")
	parser.add_argument("--yest", action="store_true")

	args = parser.parse_args()

	sport = args.sport
	if args.nhl:
		sport = "nhl"
	elif args.mlb:
		sport = "mlb"

	if not sport:
		print("NEED SPORT")
		exit()

	date = args.date
	if args.tmrw:
		date = str(datetime.now() + timedelta(days=1))[:10]
	elif args.yest:
		date = str(datetime.now() - timedelta(days=1))[:10]
	elif not date:
		date = str(datetime.now())[:10]

	if args.update:
		writeSchedule(sport, date)
		writeStats(sport, date)
		print("feed")
		subprocess.Popen(["python", "dingers.py", "--months", "--feed", "-d", date])
		print("cron")
		subprocess.Popen(["python", "controllers/baseballreference.py", "-c"])
	elif args.stats:
		writeStats(sport, date)
	elif args.schedule:
		writeSchedule(sport, date)