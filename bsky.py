
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import math
import json
import os
import re
import argparse
import unicodedata
import time
import csv
from glob import glob
import nodriver as uc

from controllers.shared import *

# 300 char limit

def dailyReport(date):
	if not date:
		date = str(datetime.now())[:10]
	with open("static/dailyev/feed.json") as fh:
		feed = json.load(fh)

	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	games = [x["game"] for x in schedule[date]]
	allFeed = []
	for game in games:
		allFeed.extend(feed[game])
	homers = []

	post = f"{feed['all']['']} HRs {datetime.strptime(date, "%Y-%m-%d").strftime("%b %-d")}"
	for game in games:
		post += f"{game.upper()}: \n"
	10 HRs Apr 3 (2.00 per Game)

	ARI @ NYY: Chisholm, Grisham, Judge
	HOU @ MIN: Pena, Walker
	COL @ PHI: Schwarber
	BOS @ BAL: Casas, Campbell, Mullins, Bregman

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

	args = parser.parse_args()

	dailyReport(args.date)