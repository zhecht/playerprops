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
from dingers import writeAll
from datetime import datetime, timedelta

q = queue.Queue()
lock = threading.Lock()

def run(sport, date, game):
	extraArgs = []
	nextDay = str(datetime.now() + timedelta(days=1))[:10]
	if sport == "dinger":
		writeAll()
	else:
		books = ["fd", "mgm", "espn", "bet365"]
		for book in books:
			cmd = ["python", "scrape.py", f"--{book}", "--sport", sport]
			if game:
				cmd.extend(["-g", game])
			with open(f"outRun{sport}{book}.log", "w") as f:
				subprocess.Popen(cmd, stdout=f, stderr=f)
		books = ["dk", "pn", "cz", "kambi"]
		for book in books:
			cmd = ["python", f"controllers/{sport}.py", f"--{book}"]
			if game:
				cmd.extend(["-g", game])
			if date:
				cmd.extend(["-d", date])

		if sport == "nba":
			subprocess.Popen(["python", f"controllers/{sport}.py", f"--minutes"])

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--game", "-g")
	parser.add_argument("--sport")
	parser.add_argument("-d", "--date")
	parser.add_argument("--tomorrow", action="store_true")
	parser.add_argument("--tmrw", action="store_true")
	parser.add_argument("-u", "--update", action="store_true")

	args = parser.parse_args()

	if args.sport:
		run(args.sport, args.date, args.game)