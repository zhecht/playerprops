
from datetime import datetime
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import time

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def writeBallparkpal():
	js = """
		const data = {};
		for (row of document.getElementsByTagName("tr")) {
			tds = row.getElementsByTagName("td");
			if (tds.length === 0) {
				continue;
			}
			let team = tds[0].innerText.toLowerCase();
			if (team === "was") {
				team = "wsh";
			}

			if (data[team] === undefined) {
				data[team] = {};
			}

			let player = tds[1].innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
			if (tds[2].innerText.indexOf("HR") < 0) {
				continue;
			}

			let max = 0;
			let maxBooks = [];
			let books = ["fd", "dk", "mgm", "cz", "pn", "bs"];
			let idx = 4;
			while (idx < 10) {
				if (tds[idx].innerText) {
					const odds = parseInt(tds[idx].innerText);
					if (odds == max) {
						maxBooks.push(books[idx-4]);
					} else if (odds > max) {
						maxBooks = [books[idx-4]];
						max = odds;
					}
				}
				idx++;
			}

			data[team][player] = {
				bpp: tds[3].innerText,
				fd: tds[4].innerText,
				dk: tds[5].innerText,
				mgm: tds[6].innerText,
				cz: tds[7].innerText,
				pn: tds[8].innerText,
				bs: tds[9].innerText,
				max: max,
				maxBooks: maxBooks
			}
		}
		console.log(data);

	"""

def checkBPP():
	with open(f"{prefix}static/mlbprops/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/mlbprops/bpp.json") as fh:
		bppLines = json.load(fh)

	data = []
	for team in bppLines:
		for player in bppLines[team]:
			try:
				bet365Underdog = int(bet365Lines[team][player].split("/")[0])
			except:
				continue

			maxBpp = bppLines[team][player]["max"]
			maxBooks = bppLines[team][player]["maxBooks"]
			fd = bppLines[team][player]["fd"]
			if maxBpp > bet365Underdog and maxBooks != ["fd"]:
				summary = f"{player} bet={bet365Lines[team][player]}; max={maxBpp}; maxBooks={maxBooks}; fd={fd}"
				diff = (maxBpp - bet365Underdog) / bet365Underdog
				data.append((diff, summary))

	for row in sorted(data, reverse=True):
		print(row[1])



def writeActionNetwork():
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel",
		15: "betmgm",
		283: "betmgm",
		348: "betrivers",
		351: "pointsbet",
		355: "caesars"
	}

	props = ["35_doubles", "33_hr"]
	odds = {}
	optionTypes = {}

	date = datetime.now()
	date = str(date)[:10]

	for prop in props:
		path = f"out.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/8/props/core_bet_type_{prop}?bookIds=69,68,15,283,348,351,355&date={date.replace('-', '')}"
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		prop = prop.split("_")[-1]

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
				#continue
				pass
			for oddData in bookData["odds"]:
				player = playerIds[oddData["player_id"]]
				team = teamIds[oddData["team_id"]]
				overUnder = optionTypes[oddData["option_type_id"]]
				book = actionNetworkBookIds.get(bookId, "")

				if team not in odds:
					odds[team] = {}
				if player not in odds[team]:
					odds[team][player] = {}
				if prop not in odds[team][player]:
					odds[team][player][prop] = {}
				if book not in odds[team][player][prop]:
					odds[team][player][prop][book] = {}
				odds[team][player][prop][book][overUnder] = f"{overUnder[0]}{oddData['value']} ({oddData['money']})"

				if player == "yandy diaz":
					#print(bookId, player, team, f"{overUnder[0]}{oddData['value']} ({oddData['money']})")
					pass
				if "line" not in odds[team][player][prop]:
					odds[team][player][prop]["line"] = f"o{oddData['value']}"
				elif oddData['value'] < float(odds[team][player][prop]["line"][1:]):
					odds[team][player][prop]["line"] = f"o{oddData['value']}"

	with open(f"{prefix}static/freebets/actionnetwork.json", "w") as fh:
		json.dump(odds, fh, indent=4)

def convertFDTeam(team):
	team = team.replace("pittsburgh pirates", "pit").replace("detroit tigers", "det").replace("cincinnati reds", "cin").replace("colorado rockies", "col").replace("minnesota twins", "min").replace("los angeles dodgers", "lad").replace("arizona diamondbacks", "ari").replace("oakland athletics", "oak").replace("philadelphia phillies", "phi").replace("san francisco giants", "sf").replace("kansas city royals", "kc").replace("san diego padres", "sd").replace("los angeles angels", "laa").replace("baltimore orioles", "bal").replace("washington nationals", "wsh").replace("miami marlins", "mia").replace("new york yankees", "nyy").replace("toronto blue jays", "tor").replace("seattle mariners", "sea").replace("boston red sox", "bos").replace("tampa bay rays", "tb").replace("new york mets", "nym").replace("milwaukee brewers", "mil").replace("st. louis cardinals", "stl").replace("atlanta braves", "atl").replace("texas rangers", "tex").replace("cleveland guardians", "cle").replace("chicago white sox", "chw").replace("chicago cubs", "chc").replace("houston astros", "hou")
	return team

def writeFanduel():
	apiKey = "FhMFpcPWXMeyZxOx"

	
	js = """
		const as = document.getElementsByTagName("a");
		const urls = {};
		for (a of as) {
			if (a.href.indexOf("/baseball/mlb") >= 0) {
				urls[a.href] = 1;
			}
		}
		console.log(Object.keys(urls));
	"""

	games = [
	"https://mi.sportsbook.fanduel.com/baseball/mlb/new-york-yankees-@-cincinnati-reds-32368519",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/chicago-cubs-@-philadelphia-phillies-32368513",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/arizona-diamondbacks-@-pittsburgh-pirates-32368514",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/seattle-mariners-@-atlanta-braves-32368521",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/detroit-tigers-@-washington-nationals-32368522",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/baltimore-orioles-@-toronto-blue-jays-32368517",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/cleveland-guardians-@-new-york-mets-32368524",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/milwaukee-brewers-@-tampa-bay-rays-32368899",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/oakland-athletics-@-houston-astros-32368516",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/kansas-city-royals-@-chicago-white-sox-32369768",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/los-angeles-dodgers-@-st.-louis-cardinals-32368512",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/colorado-rockies-@-texas-rangers-32368518",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/miami-marlins-@-san-francisco-giants-32368511",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/minnesota-twins-@-los-angeles-angels-32368515",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/boston-red-sox-@-san-diego-padres-32368523",
	"https://mi.sportsbook.fanduel.com/baseball/mlb/cleveland-guardians-@-new-york-mets-32368520"
	]

	lines = {}
	for game in games:
		gameId = game.split("-")[-1]
		game = convertFDTeam(game.split("/")[-1][:-9].replace("-", " "))
		if game in lines:
			continue
		lines[game] = {}

		outfile = "out"
		time.sleep(0.42)
		url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}&tab=batter-props"
		call(["curl", "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		if "markets" not in data["attachments"]:
			continue
		for market in data["attachments"]["markets"]:
			marketName = data["attachments"]["markets"][market]["marketName"].lower()

			if marketName in ["to hit a home run", "to hit a double"]:
				prop = "double" if "double" in marketName else "hr"
				for playerRow in data["attachments"]["markets"][market]["runners"]:
					player = playerRow["runnerName"].lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
					try:
						odds = playerRow["winRunnerOdds"]["americanDisplayOdds"]["americanOdds"]
					except:
						continue

					if player not in lines[game]:
						lines[game][player] = {}
					lines[game][player][prop] = odds
	
	with open(f"{prefix}static/baseballreference/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devigger(evData, player="", bet365Odds="575/-900", finalOdds=630, dinger=False):

	if dinger:
		# assuming 2hr/g = 40% FB @ 70% conversion
		finalOdds = f"1={finalOdds};n=0.28x"
		# 80% conversion
		#finalOdds = f"1={finalOdds};n=0.36x"

	outfile = "out"
	post = ["curl", 'http://crazyninjamike.com/public/sportsbooks/sportsbook_devigger.aspx', "-X", "POST", "-H", 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0', "-H", 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', "-H",'Accept-Language: en-US,en;q=0.5', "-H",'Accept-Encoding: gzip, deflate', "-H",'Content-Type: application/x-www-form-urlencoded', "-H",'Origin: http://crazyninjamike.com', "-H",'Connection: keep-alive', "-H",'Referer: http://crazyninjamike.com/public/sportsbooks/sportsbook_devigger.aspx', "-H",'Cookie: General=KellyMultiplier=.25&KellyBankRoll=1000&DevigMethodIndex=4&WorstCaseDevigMethod_Multiplicative=True&WorstCaseDevigMethod_Additive=True&WorstCaseDevigMethod_Power=True&WorstCaseDevigMethod_Shin=True&MultiplicativeWeight=0&AdditiveWeight=0&PowerWeight=0&ShinWeight=0&ShowEVColorIndicator=False&ShowDetailedDevigInfo=True&CopyToClipboard_Reddit=False&ShowHedgeDevigMethod=False&UseMultilineTextbox=False; ASP.NET_SessionId=h2cklqfayhnovxkckdykfm4o', "-H",'Upgrade-Insecure-Requests: 1', "-H",'Pragma: no-cache', "-H",'Cache-Control: no-cache', "--data-raw", '__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=%2FwEPDwUKMjA1MjMyNjgxMA9kFgICAw9kFhgCJw8PFgIeB1Zpc2libGVoZGQCNQ8PFgIeBFRleHQFgAI8Yj5Xb3JzdC1jYXNlOiAoUG93ZXIpPC9iPjwvYnI%2BTGVnIzEgKDU3NSk7IE1hcmtldCBKdWljZSA9IDQuOCAlOyBMZWcncyBKdWljZSA9IDQuNSAlOyBGYWlyIFZhbHVlID0gKzc4MyAoMTEuMyAlKTwvYnI%2BRmluYWwgT2RkcyAoKzYzMCk7IM6jKE1hcmtldCBKdWljZSkgPSA0LjgxICU7IM6jKExlZydzIEp1aWNlKSA9IDQuNSAlOyBGYWlyIFZhbHVlID0gKzc4MyAoMTEuMyAlKTwvYnI%2BU3VtbWFyeTsgRVYlID0gLTE3LjMgJSAoRkIgPSA3MS4zICUpZGQCNw8PFgIeCEltYWdlVXJsZWRkAjkPDxYCHwEFBTwvYnI%2BZGQCOw8PFgIfAWVkZAI%2FDw8WAh8BZWRkAkEPDxYCHwFlZGQCRQ8PFgIfAWVkZAJHDw8WAh8BZWRkAksPDxYCHwFlZGQCTQ8PFgIfAWVkZAJRDw8WAh8BZWRkGAEFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYTBRNDaGVja0JveENvcnJlbGF0aW9uBQ1DaGVja0JveEJvb3N0BRZSYWRpb0J1dHRvbkJvb3N0UHJvZml0BRNSYWRpb0J1dHRvbkJvb3N0QWxsBRNSYWRpb0J1dHRvbkJvb3N0QWxsBRRDaGVja0JveERhaWx5RmFudGFzeQUOQ2hlY2tCb3hSZXdhcmQFJUNoZWNrQm94TGlzdFdvcnN0Q2FzZU1ldGhvZFNldHRpbmdzJDAFJUNoZWNrQm94TGlzdFdvcnN0Q2FzZU1ldGhvZFNldHRpbmdzJDEFJUNoZWNrQm94TGlzdFdvcnN0Q2FzZU1ldGhvZFNldHRpbmdzJDIFJUNoZWNrQm94TGlzdFdvcnN0Q2FzZU1ldGhvZFNldHRpbmdzJDMFJUNoZWNrQm94TGlzdFdvcnN0Q2FzZU1ldGhvZFNldHRpbmdzJDMFJUNoZWNrQm94TGlzdENvcHlUb0NsaXBib2FyZFNldHRpbmdzJDAFJUNoZWNrQm94TGlzdENvcHlUb0NsaXBib2FyZFNldHRpbmdzJDAFGkNoZWNrQm94TGlzdE1pc2NTZXR0aW5ncyQwBRpDaGVja0JveExpc3RNaXNjU2V0dGluZ3MkMQUaQ2hlY2tCb3hMaXN0TWlzY1NldHRpbmdzJDEFEUNoZWNrQm94U2hvd0hlZGdlBRtDaGVja0JveFVzZU11bHRpbGluZVRleHRib3j3YSa0x8tCP%2FIRsSJbwRSmbvip%2FQ%3D%3D&__VIEWSTATEGENERATOR=75A63123&__EVENTVALIDATION=%2FwEdAD0xhk8EdsoMEQ9SrpSOuYvpVduh02rwiY5pxbMa1RNJ5aQWjQCmzgVoWED6ZF3QmBhQwDtP%2FiI7M6rA7bM7sw79dcexLTc65mHP6HSLc%2Bf1LffPdxAlAXM62AauCNlhmmvcpkkrUUk0wKmeRC%2Bo5Y4X6geodp8Olur%2BmlGM1%2FKrX0%2FlhO7FgJVfVmSrfexz2O8O1Hi%2Fs4JOEIbuo8tqstA4FSD8tQvxjLeGTr%2FZjbpMMCoLzpV5VCswEluevhpgd9wk6hQu8IzOUf9SV1fT41DJrES61htWrWjs6qQMwbhFAInbbXKrUyuaH0WERw6pAco%2FDYrJ17Id28pC779glSqiyuRmS0vMxthemNSZxFYiWcucIPcus%2FOzSDEyoeofXW3aOzoxxlnSXry0La7j6r%2Fs%2BfHYZidJ9iL1XbUgK8hpdJe%2BtzEYMgx%2BTUfzwbS304A%2FY8oqBpGAsYx8Mop1jRjezzZQ%2B9tmmKZqyksYCdJDpzyJeqLpB5t8%2F2GJQ3xLbuvhfOPVw%2FvZ64GRORAnyiUeAIH4rCiLrkEjcbAVN3KRLGcEq1QxEeM%2Fjkzi4zrZhPrdYjFyIOpXU7VVEH8x6qLFK%2FgiX4R7k%2BePj3bS7J%2BgWBTnTMwDkbtKRoDY9CgTs7Im6q5QJGQ4Zop7C9MPh%2FovUZMCC%2B0SDrnxmEkAW9uYtxLt%2Fyzf7D%2FO38iSXXKKjp%2F7pQZSXQqK%2BkHRq0%2F8hxlteb8BqBsXIQ3Id4DTK3MIxXuZIjIbmxHxK2jQvvnkl2IojkGDopgGMUjBgFQSCSRWR%2BvnMJoIOfBUI43VZFoFoOWmJfOGgotEV0SbRtvJlGGgBtNu745bl1XM%2FNjSIkmj0hpqvWk5jUlJo8y5DJZi2FeCfzTe16FW7YBUVAarIwORcYHwHlUbtxUIovxtp6Fnp9PZDrtAO8BRQYb%2BM2XZoW6ZGCGPI3Vs4qn7bWwKvOZxJ0hkpY3JuBY8dUINwhWy9tBMMMleqCemET2u7gRHPAbTtEEA0M6r7Zrzlm%2BXOIAyERXQ8XPFFqsFxOEZFeuxKH%2FI7Em%2FLOYrJZQEF%2FXmnfJtqlZ119DKEMgOAXJKwTjbHfIVMvqWcHvFBXtSrRli%2BLXSuvmx4sYD3Q%2FsmNkE8GK1s%2FT%2FRpPmdWeEsxFtygifU2vOaYXIhnkpGZxXMYRub%2FxoObcM1wBoVb5Wzqjq1UUGVOuNjuWHehORBMX7COFSeqYehFSmr8SovWm91KahWi5xvQwY6WQfKYDVBNSRbUN8dPza19tfAj7Bgb95LWIXvHnlu623MCphxMmD59a%2F8FmjcA2Psl5LiAJUgZxsX0wLL3s%3D&TextBoxKellyMultiplier=.25&TextBoxBankRoll=1000&RadioButtonListDevigMethod=worstcase&TextBoxLegOdds='+str(bet365Odds)+'&TextBoxFinalOdds='+str(finalOdds)+'&TextBoxCorrelation=0&TextBoxBoost=0%25&Boost=RadioButtonBoostProfit&DropDownListDailyFantasy=0&ButtonCalculate=Calculate&CheckBoxListWorstCaseMethodSettings%240=The+Multiplicative%2FNormalization%2FTraditional+Method&CheckBoxListWorstCaseMethodSettings%241=The+Additive+Method&CheckBoxListWorstCaseMethodSettings%242=The+Power+Method&CheckBoxListWorstCaseMethodSettings%243=The+Shin+Method&TextBoxMultiplicativeWeight=0%25&TextBoxAdditiveWeight=0%25&TextBoxPowerWeight=0%25&TextBoxShinWeight=0%25&CheckBoxListMiscSettings%241=Show+Detailed+Devig+Info', "-o", outfile]

	time.sleep(0.3)
	call(post)

	soup = BS(open(outfile, 'rb').read(), "lxml")
	output = soup.find("span", id="LabelOutput").text

	m = re.search(r".* Fair Value = (.*?) \((.*?)\)Summary\; EV% = (.*?) .*FB = (.*?)\)", output)
	if m:
		fairVal = m.group(1)
		implied = m.group(2)
		ev = m.group(3)
		fb = m.group(4)
		evData[player] = {
			"fairVal": fairVal,
			"implied": implied,
			"ev": ev,
			"fb": fb
		}

def write365():
	js = """
		let data = {};
		for (div of document.getElementsByClassName("gl-MarketGroupButton_Text")) {
			let playerList = [];
			if (div.innerText == "Player Home Runs") {
				for (playerDiv of div.parentNode.nextSibling.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
					let player = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Name")[0].innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
					let team = playerDiv.getElementsByClassName("srb-ParticipantLabelWithTeam_Team")[0].innerText.toLowerCase().split(" - ")[0];

					if (team === "la angels") {
						team = "laa";
					} else if (team === "la dodgers") {
						team = "lad";
					} else if (team === "chi white sox") {
						team = "chw";
					} else if (team === "chi cubs") {
						team = "chc";
					} else if (team === "was nationals") {
						team = "wsh";
					} else if (team === "ny mets") {
						team = "nym";
					} else if (team === "ny yankees") {
						team = "nyy";
					} else {
						team = team.split(" ")[0];
					}
					
					if (data[team] === undefined) {
						data[team] = {};
					}
					data[team][player] = "";
					playerList.push([team, player]);
				}

				let idx = 0;
				for (playerDiv of div.parentNode.nextSibling.getElementsByClassName("gl-Market")[1].getElementsByClassName("gl-ParticipantCenteredStacked")) {
					let team = playerList[idx][0];
					let player = playerList[idx][1];

					data[team][player] = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
					idx += 1;
				}

				idx = 0;
				for (playerDiv of div.parentNode.nextSibling.getElementsByClassName("gl-Market")[2].getElementsByClassName("gl-ParticipantCenteredStacked")) {
					let team = playerList[idx][0];
					let player = playerList[idx][1];

					data[team][player] += "/" + playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
					idx += 1;
				}
			}
		}
		console.log(data)
	"""
	pass

def writeEV(dinger=False):

	date = str(datetime.now())[:10]

	with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/mlbprops/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/baseballreference/fanduelLines.json") as fh:
		fdLines = json.load(fh)


	with open(f"{prefix}static/mlbprops/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	for game in fdLines:
		for player in fdLines[game]:
			if "hr" not in fdLines[game][player]:
				continue
			team1, team2 = map(str, game.split(" @ "))
			if team1 in bet365Lines and player in bet365Lines[team1]:
				team = team1
			elif team2 in bet365Lines and player in bet365Lines[team2]:
				team = team2
			else:
				continue

			fdLine = fdLines[game][player]["hr"]

			dkLine = 0
			if game in dkLines and player in dkLines[game] and "hr" in dkLines[game][player]:
				dkLine = int(dkLines[game][player]["hr"]["over"])

			sharpUnderdog = int(bet365Lines[team][player].split("/")[0])

			line = fdLine
			fd = True
			if dkLine > fdLine and dkLine > sharpUnderdog:
				line = dkLine
				fd = False
				#print(fdLine, dkLine, sharpUnderdog, player)

			if player in evData:
				continue
			if line > sharpUnderdog:
				pass
				devigger(evData, player, bet365Lines[team][player], line, dinger)
				evData[player]["game"] = game
				evData[player]["team"] = team
				evData[player]["bet365"] = bet365Lines[team][player]
				if not fd:
					fdLine = 0
					evData[player]["other"] = line
					evData[player]["otherBook"] = "DK"
				evData[player]["fanduel"] = fdLine



	with open(f"{prefix}static/mlbprops/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def sortEV():
	with open(f"{prefix}static/mlbprops/ev.json") as fh:
		evData = json.load(fh)

	data = []

	for player in evData:
		ev = float(evData[player]["ev"])
		data.append((ev, player, evData[player]))

	for row in sorted(data, reverse=True):
		playerData = row[-1]
		line = f"{playerData['fanduel']} FD"
		if not playerData["fanduel"]:
			line = f"{playerData['other']} {playerData['otherBook']}"
		print(f"{playerData['ev']}% EV: {playerData.get('team', '').upper()} {row[1].title()} +{line} compared to {playerData['bet365']}. Implied Prob = {playerData['implied'].replace(' ', '')}")

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--fd", action="store_true", help="Fanduel")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("-p", "--print", action="store_true", help="Print")
	parser.add_argument("--dinger", action="store_true", help="Dinger Tues")

	args = parser.parse_args()

	dinger = False
	if args.dinger:
		dinger = True

	if args.fd:
		writeFanduel()

	if args.ev:
		writeEV(dinger)

	if args.bpp:
		checkBPP()

	if args.print:
		sortEV()
	#write365()
	#writeActionNetwork()
	#devigger({}, dinger=dinger)

	freeBet = 170
