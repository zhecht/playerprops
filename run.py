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

def run(sport):
	if sport == "dinger":
		writeAll()
	else:
		books = ["fd", "dk", "mgm", "espn", "bet365"]
		for book in books:
			with open(f"outRun{sport}{book}.log", "w") as f:
				subprocess.Popen(["python", "scrape.py", f"--{book}", "--sport", sport], stdout=f, stderr=f)
		books = ["pn", "kambi"]
		for book in books:
			with open(f"outRun{sport}{book}.log", "w") as f:
				subprocess.Popen(["python", f"controllers/{sport}.py", f"--{book}"], stdout=f, stderr=f)
		# CZ

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--sport")
	parser.add_argument("-u", "--update", action="store_true")

	args = parser.parse_args()

	if args.sport:
		run(args.sport)