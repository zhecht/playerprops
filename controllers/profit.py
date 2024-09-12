
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import time
from pypdf import PdfReader

def getSport(text, bet):
	sport = "nfl"
	if "home runs" in bet or "strikeouts" in bet or "rbi" in bet or "hit" in bet or "scoreless 1st" in bet or "1st inning" in bet or "walks" in bet:
		return "mlb"
	elif "goalscorer" in bet or "to score a goal" in bet or "saves" in bet:
		return "nhl"
	elif "double-double" in bet or "points" in bet or "three-pointers" in bet:
		return "nba"
	elif "full time" in bet or "corners" in bet:
		return "soccer"
	return sport

def readFanduel():
	js = """

	{
		let ul;
		for (u of document.querySelectorAll("ul")) {
			if (u.querySelector("span").innerText.includes("Bets placed in")) {
				ul = u;
				break;
			}
		}
		console.log(ul);
	}
"""

# Take transactions from pikkit and write
def writeTransactions():

	import csv
	with open("transactions.csv") as fh:
		reader = csv.reader(fh)
		rows = [x for x in reader]

	sortedData = []
	#bet_id,sportsbook,type,status,odds,closing_line,ev,amount,profit,time_placed,time_settled,bet_info,tags,sports,leagues
	for row in rows[1:]:
		# hedge but doesn't have the other side on FD
		book = convertBook(row[1])
		if book != "fanduel":
			continue
		if row[1] == "BetMGM" and row[0] == "1Z3JN4C9LE":
			continue
		m,d,y = map(str, row[9].split(" ")[0].split("/"))
		dt = f"{y}-{m}-{d}"
		sortedData.append((dt, row))

	output = "bet_id,sportsbook,type,status,odds,closing_line,ev,amount,profit,time_placed,time_settled,bet_info,tags,sports,leagues\n"
	for dt, row in sorted(sortedData):
		output += ",".join(row)+"\n"

	#with open("static/profit/transactions.csv", "w") as fh:
	#	fh.write(output)

	with open("out", "w") as fh:
		fh.write(output)

def convertBook(book):
	return book.lower().split(" ")[0]

def calcProfit():
	import csv
	with open("static/profit/transactions.csv") as fh:
		reader = csv.reader(fh)
		rows = [x for x in reader]

	data = {}
	sports = {}
	hdrs = "bet_id,sportsbook,type,status,odds,closing_line,ev,amount,profit,time_placed,time_settled,bet_info,tags,sports,leagues".split(",")
	profit = []
	boosts = 0
	rows = rows[1:]
	skip = 1
	for idx in range(0, len(rows), skip):
		row = rows[idx]

		skip = 1
		if row[-1].endswith("&"):
			row.extend(rows[idx+1])
			skip = 2

		if row[hdrs.index("status")] not in ["SETTLED_LOSS", "SETTLED_WIN"]:
			continue
		isWin = row[hdrs.index("status")] == "SETTLED_WIN"
		book = convertBook(row[1])
		if book not in data:
			data[book] = []
			data[book+"Boosts"] = []

		sport = row[-2]
		if sport and sport not in sports:
			sports[sport] = []

		bet = row[hdrs.index("bet_info")]
		amt = float(row[hdrs.index("profit")])
		profit.append(amt)
		data[book].append(amt)
		if "boost" in bet.lower() or "specials" in bet.lower() or "combine" in bet.lower() or "each record" in bet.lower():
			boosts += amt
			data[book+"Boosts"].append(amt)
		if sport:
			if "/" in sport:
				print(bet)
			sports[sport].append(amt)

	print(f"tot profit = {round(sum(profit), 2)} ({len(profit)})\n")
	for book in data:
		if "Boosts" not in book:
			print(f"{book} = {round(sum(data[book]), 2)}")

	print(f"\nboosts = {round(boosts, 2)}\n")
	for book in data:
		if "Boosts" in book:
			print(f"{book.replace('Boosts', '')} boosts = {round(sum(data[book]), 2)} ({len(data[book])})")

	print("\n")
	for sport in sports:
		print(f"{sport} = {round(sum(sports[sport]), 2)}")


if __name__ == '__main__':
	#writeMGM()

	#writeTransactions()
	calcProfit()

	"""
	up until 9/9/2024
		DK and FD show only 6 months prior

	cash balance: 4022.01
	at risk: 1850

	-$738.26 (811-1181-159)
		ESPN 8-7 +404.96
		FD 72-227-100 +140.17
		DK 251-353-22 -95.70
		MGM 126-201-20 -338.05
		CZ 250-277-12 -708.11
		BR 104-116-5 -141.53
	"""
