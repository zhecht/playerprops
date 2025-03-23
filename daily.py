import os
import time
import json
import nodriver as uc
import argparse
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

		for row in div.find("tbody").find_all("tr"):
			tds = row.find_all("td")
			awayTeam = tds[0].find("a").get("href").split("/")[-2]
			homeTeam = tds[1].find("a").get("href").split("/")[-2]
			result = tds[2]
			href = result.find("a").get("href")
			score = start = ""

			if ", " in result.text:
				winSide, lossSide = map(str, result.text.lower().split(", "))
				winTeam, winScore = map(str, winSide.split(" "))
				lossTeam, lossScore = map(str, lossSide.split(" "))

				score = f"{winScore}-{lossScore}"
				if winTeam != awayTeam:
					score = f"{lossScore}-{winScore}"
			else:
				start = result.text.strip()

			j = {
				"game": f"{awayTeam} @ {homeTeam}",
				"link": href,
				"score": score,
				"start": start
			}
			schedule[date].append(j)

	with open(f"static/{sport}/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

def writeStats(sport, date):
	if not date:
		date = str(datetime.now())[:10]
	with open(f"static/{sport}/schedule.json") as fh:
		schedule = json.load(fh)

	if date not in schedule:
		print("Not in Schedule")
		exit()

	for gameData in schedule[date]:
		pass

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--date", "-d")
	parser.add_argument("--sport")
	parser.add_argument("-u", "--update", action="store_true")
	parser.add_argument("--run", action="store_true")

	args = parser.parse_args()

	if not args.sport:
		print("NEED SPORT")
		exit()

	if args.update:
		writeSchedule(args.sport, args.date)
		writeStats(args.sport, args.date)