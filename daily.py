
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

def writeStats():
	url = ""

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--sport")
	parser.add_argument("-u", "--update", action="store_true")

	args = parser.parse_args()

	if args.update:
		writeStats()