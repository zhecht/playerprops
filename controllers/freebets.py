
from datetime import datetime
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

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

def writeKambi():
	data = {}
	outfile = f"out.json"
	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/baseball/mlb/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	eventIds = {}
	for event in j["events"]:
		game = event["event"]["name"]
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]


	for game in eventIds:
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		for betOffer in j["betOffers"]:
			label = betOffer["criterion"]["label"]
			if not teamIds and "Handicap" in label:
				for row in betOffer["outcomes"]:
					team = convertFDTeam(row["label"].lower())
					teamIds[row["participantId"]] = team
					data[team] = {}

			elif "to hit a Home Run" in label:
				player = strip_accents(betOffer["outcomes"][0]["participant"])
				try:
					last, first = map(str, player.lower().split(", "))
					player = f"{first} {last}"
				except:
					player = player.lower()
				player = player.replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
				over = betOffer["outcomes"][0]["oddsAmerican"]
				under = betOffer["outcomes"][1]["oddsAmerican"]
				team = teamIds[betOffer["outcomes"][0]["eventParticipantId"]]
				data[team][player] = f"{over}/{under}"


	with open(f"{prefix}static/freebets/kambi.json", "w") as fh:
		json.dump(data, fh, indent=4)



def writeActionNetwork():
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel",
		#15: "betmgm",
		283: "mgm",
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
		url = f"https://api.actionnetwork.com/web/v1/leagues/8/props/core_bet_type_{prop}?bookIds=69,68,283,348,351,355&date={date.replace('-', '')}"
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
			playerIds[row["id"]] = row["full_name"].lower().replace(".", "").replace("-", " ").replace("'", "").replace(" jr", "").replace(" ii", "")

		books = market["books"]
		for bookData in books:
			bookId = bookData["book_id"]
			if bookId not in actionNetworkBookIds or not actionNetworkBookIds[bookId]:
				continue
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
					odds[team][player][prop][book] = f"{oddData['money']}"
				elif overUnder == "over":
					odds[team][player][prop][book] = f"{oddData['money']}/{odds[team][player][prop][book]}"
				else:
					odds[team][player][prop][book] += f"/{oddData['money']}"

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
  "https://mi.sportsbook.fanduel.com/baseball/mlb/san-diego-padres-@-philadelphia-phillies-32475159",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/san-francisco-giants-@-pittsburgh-pirates-32475160",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/miami-marlins-@-baltimore-orioles-32475168",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/milwaukee-brewers-@-cincinnati-reds-32475156",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/los-angeles-dodgers-@-new-york-mets-32475157",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/chicago-white-sox-@-atlanta-braves-32475167",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/cleveland-guardians-@-texas-rangers-32475162",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/boston-red-sox-@-chicago-cubs-32475166",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/tampa-bay-rays-@-kansas-city-royals-32475161",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/new-york-yankees-@-colorado-rockies-32475170",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/houston-astros-@-los-angeles-angels-32475164",
  "https://mi.sportsbook.fanduel.com/baseball/mlb/detroit-tigers-@-seattle-mariners-32475165"
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

			if marketName in ["to hit a home run", "to hit a double", "to hit a triple", "to record a hit"]:
				prop = "hr"
				if "double" in marketName:
					prop = "double"
				elif "triple" in marketName:
					prop = "triple"
				elif "record" in marketName:
					prop = "h"
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

def devigger(evData, player="", bet365Odds="575/-900", finalOdds=630, dinger=False, avg=False):

	if dinger:
		# assuming 2hr/g = 40% FB @ 70% conversion
		finalOdds = f"1={finalOdds};n=0.28x"
		# 80% conversion
		#finalOdds = f"1={finalOdds};n=0.36x"

	outfile = "out"
	post = ["curl", 'http://crazyninjamike.com/public/sportsbooks/sportsbook_devigger.aspx', "-X", "POST", "-H", 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0', "-H", 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', "-H",'Accept-Language: en-US,en;q=0.5', "-H",'Accept-Encoding: gzip, deflate', "-H",'Content-Type: application/x-www-form-urlencoded', "-H",'Origin: http://crazyninjamike.com', "-H",'Connection: keep-alive', "-H",'Referer: http://crazyninjamike.com/public/sportsbooks/sportsbook_devigger.aspx', "-H",'Cookie: General=KellyMultiplier=.25&KellyBankRoll=1000&DevigMethodIndex=4&WorstCaseDevigMethod_Multiplicative=True&WorstCaseDevigMethod_Additive=True&WorstCaseDevigMethod_Power=True&WorstCaseDevigMethod_Shin=True&MultiplicativeWeight=0&AdditiveWeight=0&PowerWeight=0&ShinWeight=0&ShowEVColorIndicator=False&ShowDetailedDevigInfo=True&CopyToClipboard_Reddit=False&ShowHedgeDevigMethod=False&UseMultilineTextbox=False; ASP.NET_SessionId=h2cklqfayhnovxkckdykfm4o', "-H",'Upgrade-Insecure-Requests: 1', "-H",'Pragma: no-cache', "-H",'Cache-Control: no-cache', "--data-raw", '__EVENTTARGET=&__EVENTARGUMENT=&__LASTFOCUS=&__VIEWSTATE=%2FwEPDwUKLTg5NDkxNjMyNg9kFgICAw9kFhwCJw8PFgIeB1Zpc2libGVoZGQCNQ8PFgQeBFRleHRlHwBoZGQCNw8PFgIfAQWBAjxiPldvcnN0LWNhc2U6IChQb3dlcik8L2I%2BPC9icj5MZWcjMSAoKzQ1MCk7IE1hcmtldCBKdWljZSA9IDQuOCAlOyBMZWcncyBKdWljZSA9IDQuNCAlOyBGYWlyIFZhbHVlID0gKzU3NSAoMTQuOCAlKTwvYnI%2BRmluYWwgT2RkcyAoKzQ4MCk7IM6jKE1hcmtldCBKdWljZSkgPSA0Ljg1ICU7IM6jKExlZydzIEp1aWNlKSA9IDQuNCAlOyBGYWlyIFZhbHVlID0gKzU3NSAoMTQuOCAlKTwvYnI%2BU3VtbWFyeTsgRVYlID0gLTE0LjEgJSAoRkIgPSA3MS4xICUpZGQCOQ8PFgIeCEltYWdlVXJsZWRkAjsPDxYCHwEF0gI8L2JyPjwvYnI%2BPGJ1dHRvbiB0eXBlPSJidXR0b24iIG9uY2xpY2s9IkNvcHlUb0NsaXBib2FyZCgnVGV4dGJveF9EZXZpZ3NVUkxfZGV2aWdzdXJsJykiPkNvcHkgRGV2aWcncyBVUkw8L2J1dHRvbj48dGV4dGFyZWEgaWQ9IlRleHRib3hfRGV2aWdzVVJMX2Rldmlnc3VybCIgbmFtZT0iVGV4dDEiIGNvbHM9IjQwIiByb3dzPSI1IiBzdHlsZT0iZGlzcGxheTogbm9uZSI%2BaHR0cDovL2NyYXp5bmluamFtaWtlLmNvbS9QdWJsaWMvc3BvcnRzYm9va3Mvc3BvcnRzYm9va19kZXZpZ2dlci5hc3B4P2F1dG9maWxsPTEmTGVnT2Rkcz0lMmI0NTAlMmYtNjUwJkZpbmFsT2Rkcz00ODA8L3RleHRhcmVhPmRkAj0PDxYCHwFlZGQCQQ8PFgIfAWVkZAJDDw8WAh8BZWRkAkcPDxYCHwFlZGQCSQ8PFgIfAWVkZAJNDw8WAh8BZWRkAk8PDxYCHwFlZGQCUw8PFgIfAWVkZAJfDxBkZBYBZmQYAQUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFhUFE0NoZWNrQm94Q29ycmVsYXRpb24FDUNoZWNrQm94Qm9vc3QFFlJhZGlvQnV0dG9uQm9vc3RQcm9maXQFE1JhZGlvQnV0dG9uQm9vc3RBbGwFE1JhZGlvQnV0dG9uQm9vc3RBbGwFFENoZWNrQm94RGFpbHlGYW50YXN5BQ5DaGVja0JveFJld2FyZAUlQ2hlY2tCb3hMaXN0V29yc3RDYXNlTWV0aG9kU2V0dGluZ3MkMAUlQ2hlY2tCb3hMaXN0V29yc3RDYXNlTWV0aG9kU2V0dGluZ3MkMQUlQ2hlY2tCb3hMaXN0V29yc3RDYXNlTWV0aG9kU2V0dGluZ3MkMgUlQ2hlY2tCb3hMaXN0V29yc3RDYXNlTWV0aG9kU2V0dGluZ3MkMwUlQ2hlY2tCb3hMaXN0V29yc3RDYXNlTWV0aG9kU2V0dGluZ3MkMwUlQ2hlY2tCb3hMaXN0Q29weVRvQ2xpcGJvYXJkU2V0dGluZ3MkMAUlQ2hlY2tCb3hMaXN0Q29weVRvQ2xpcGJvYXJkU2V0dGluZ3MkMQUlQ2hlY2tCb3hMaXN0Q29weVRvQ2xpcGJvYXJkU2V0dGluZ3MkMgUlQ2hlY2tCb3hMaXN0Q29weVRvQ2xpcGJvYXJkU2V0dGluZ3MkMgUaQ2hlY2tCb3hMaXN0TWlzY1NldHRpbmdzJDAFGkNoZWNrQm94TGlzdE1pc2NTZXR0aW5ncyQxBRpDaGVja0JveExpc3RNaXNjU2V0dGluZ3MkMQURQ2hlY2tCb3hTaG93SGVkZ2UFG0NoZWNrQm94VXNlTXVsdGlsaW5lVGV4dGJveKOjTHKsFcieE9KKzTJQiI3AJR6B&__VIEWSTATEGENERATOR=75A63123&__EVENTVALIDATION=%2FwEdAEIw9X7iCaxD%2F3rNNZYgx5HDVduh02rwiY5pxbMa1RNJ5aQWjQCmzgVoWED6ZF3QmBhQwDtP%2FiI7M6rA7bM7sw79dcexLTc65mHP6HSLc%2Bf1LffPdxAlAXM62AauCNlhmmvcpkkrUUk0wKmeRC%2Bo5Y4X6geodp8Olur%2BmlGM1%2FKrX0%2FlhO7FgJVfVmSrfexz2O8O1Hi%2Fs4JOEIbuo8tqstA4FSD8tQvxjLeGTr%2FZjbpMMCoLzpV5VCswEluevhpgd9wk6hQu8IzOUf9SV1fT41DJrES61htWrWjs6qQMwbhFAInbbXKrUyuaH0WERw6pAco%2FDYrJ17Id28pC779glSqiyuRmS0vMxthemNSZxFYiWcucIPcus%2FOzSDEyoeofXW3aOzoxxlnSXry0La7j6r%2Fs%2BfHYZidJ9iL1XbUgK8hpdJe%2BtzEYMgx%2BTUfzwbS304A%2FY8oqBpGAsYx8Mop1jRjezzZQ%2B9tmmKZqyksYCdJDpzyJeqLpB5t8%2F2GJQ3xLbuvhfOPVw%2FvZ64GRORAnyiUeAIH4rCiLrkEjcbAVN3KRLGcEq1QxEeM%2Fjkzi4zrZhPrdYjFyIOpXU7VVEH8x6qLFK%2FgiX4R7k%2BePj3bS7J%2BgWBTnTMwDkbtKRoDY9CgTs7Im6q5QJGQ4Zop7C9MPh%2FovUZMCC%2B0SDrnxmEkAW9uYtxLt%2Fyzf7D%2FO38iSXXKKjp%2F7pQZSXQqK%2BkHRq0%2F8hxlteb8BqBsXIQ3Id4DTK3MIxXuZIjIbmxHxK2jQvvnkl2IojkGDopgGMUjBgFQSCSRWR%2BvnMJoIOfBUI43VZFoFoOWmJfOGgotEV0SbRtvJlGGgBtNu745bl1XM%2FNjSIkmj0hpqvWk5jUlJo8y5DJZi2FeCfzTe16FW7YBUVAarIwORcYHwHlUbtxUIovxtp6Fnp9PZDrtAO8BRQYb%2BM2XZoW6ZGCGPI3Vs4qn7bWwKvOZxJ0hkpY3JuBY8dUINwhWy9tBMMMleqCemET2u7gRHPAbTtEEA0M6r7Zrzlm%2BXOIAyERXQ8XPFFqsFxOEZFeuxKH%2FI7Em%2FLOYrJZQEF%2FXmnfJtqlZ119DKEMgOAXJKwTjbHfIVMvqWcHvFBXtSrRli%2BLXSuvmx4sYD3Q%2FsmNkE8GK1s%2FT%2FRpPmdWeEsxFtygifU2vOaYXIhnkpGZxXMYRub%2FxoObcM1wBoVb5Wzqjq1e%2FUwuJUFie73%2BFPJ7NCOPtptpM51QcGXfw1UVjBtUMFQwE9YmMRS%2Fc7ytpgEPqE7kUGVOuNjuWHehORBMX7COGM4yNZD1WpVnhcev8qNkDbxq5sREhC1cwZ55vP6Xc17lJ6ph6EVKavxKi9ab3UpqFaLnG9DBjpZB8pgNUE1JFtQ3x0%2FNrX218CPsGBv3ktYhe8eeW7rbcwKmHEyYPn1r%2FO2TD8UgBuluW1SPDteuzIU6xb9g%3D%3D&TextBoxKellyMultiplier=.25&TextBoxBankRoll=1000&RadioButtonListDevigMethod=worstcase&TextBoxLegOdds='+str(bet365Odds)+'&TextBoxFinalOdds='+str(finalOdds)+'&TextBoxCorrelation=0&TextBoxBoost=0%25&Boost=RadioButtonBoostProfit&DropDownListDailyFantasy=0&ButtonCalculate=Calculate&Text1=http%3A%2F%2Fcrazyninjamike.com%2FPublic%2Fsportsbooks%2Fsportsbook_devigger.aspx%3Fautofill%3D1%26LegOdds%3D%252b450%252f-650%26FinalOdds%3D480&CheckBoxListWorstCaseMethodSettings%240=The+Multiplicative%2FNormalization%2FTraditional+Method&CheckBoxListWorstCaseMethodSettings%241=The+Additive+Method&CheckBoxListWorstCaseMethodSettings%242=The+Power+Method&CheckBoxListWorstCaseMethodSettings%243=The+Shin+Method&TextBoxMultiplicativeWeight=0%25&TextBoxAdditiveWeight=0%25&TextBoxPowerWeight=0%25&TextBoxShinWeight=0%25&CheckBoxListCopyToClipboardSettings%240=devigurl&CheckBoxListMiscSettings%241=Show+Detailed+Devig+Info', "-o", outfile]

	time.sleep(0.3)
	call(post)

	soup = BS(open(outfile, 'rb').read(), "lxml")
	try:
		output = soup.find("span", id="LabelOutput").text
	except:
		return

	m = re.search(r".* Fair Value = (.*?) \((.*?)\)Summary\; EV% = (.*?) .*FB = (.*?)\)", output)
	if m:
		fairVal = m.group(1)
		implied = m.group(2)
		ev = m.group(3)
		fb = m.group(4)
		if player not in evData:
			evData[player] = {}
		evData[player]["fairVal"] = fairVal
		evData[player]["implied"] = implied
		evData[player]["fb"] = fb
		if avg:
			evData[player]["ev"] = ev
		else:
			evData[player]["bet365ev"] = ev
			evData[player]["bet365Implied"] = implied

def write365():
	js = """
		let data = {};
		for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
			if (div.classList.contains("src-FixtureSubGroup_Closed")) {
				div.click();
			}
			let playerList = [];
			for (playerDiv of div.getElementsByClassName("srb-ParticipantLabelWithTeam")) {
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
			for (playerDiv of div.getElementsByClassName("gl-Market")[1].getElementsByClassName("gl-ParticipantCenteredStacked")) {
				let team = playerList[idx][0];
				let player = playerList[idx][1];

				data[team][player] = playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
				idx += 1;
			}

			idx = 0;
			for (playerDiv of div.getElementsByClassName("gl-Market")[2].getElementsByClassName("gl-ParticipantCenteredStacked")) {
				let team = playerList[idx][0];
				let player = playerList[idx][1];

				data[team][player] += "/" + playerDiv.getElementsByClassName("gl-ParticipantCenteredStacked_Odds")[0].innerText;
				idx += 1;
			}
			
		}
		console.log(data)

	"""
	pass

def writeEV(dinger=False, date=None, useDK=False, avg=False):

	if not date:
		date = str(datetime.now())[:10]

	with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/mlbprops/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/baseballreference/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/freebets/kambi.json") as fh:
		kambi = json.load(fh)

	with open(f"{prefix}static/freebets/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	with open(f"{prefix}static/mlbprops/ev.json") as fh:
		evData = json.load(fh)

	evData = {}

	for game in fdLines:
		for player in fdLines[game]:
			if "hr" not in fdLines[game][player]:
				continue
			team1, team2 = map(str, game.split(" @ "))
			team = ""
			if not useDK:
				if team1 in bet365Lines and player in bet365Lines[team1]:
					team = team1
				elif team2 in bet365Lines and player in bet365Lines[team2]:
					team = team2
				else:
					if team1 in actionnetwork and player in actionnetwork[team1]:
						team = team1
					elif team2 in actionnetwork and player in actionnetwork[team2]:
						team = team2
					else:
						continue

			fdLine = fdLines[game][player]["hr"]

			dkLine = 0
			if game in dkLines and player in dkLines[game] and "hr" in dkLines[game][player]:
				dkLine = int(dkLines[game][player]["hr"]["over"])
			elif useDK:
				continue

			dk = mgm = pb = cz = br = kambi = ""
			if team in actionnetwork and player in actionnetwork[team] and "hr" in actionnetwork[team][player]:
				dk = actionnetwork[team][player]["hr"].get("draftkings", "-")
				mgm = actionnetwork[team][player]["hr"].get("mgm", "-")
				br = actionnetwork[team][player]["hr"].get("betrivers", "-")
				cz = actionnetwork[team][player]["hr"].get("caesars", "-")
				pb = actionnetwork[team][player]["hr"].get("pointsbet", "-")

			if team not in bet365Lines or player not in bet365Lines[team]:
				bet365ou = ""
			else:
				bet365ou = bet365Lines[team][player]

			avgOver = []
			avgUnder = []
			for book in [bet365ou, dk, mgm, pb]:
				if book and book != "-":
					avgOver.append(int(book.split("/")[0]))
					if "/" in book:
						avgUnder.append(int(book.split("/")[1]))
			if avgOver:
				avgOver = int(sum(avgOver) / len(avgOver))
			else:
				avgOver = "-"
			if avgUnder:
				avgUnder = int(sum(avgUnder) / len(avgUnder))
			else:
				avgUnder = "-"
			ou = f"{avgOver}/{avgUnder}"

			if ou == "-/-":
				continue

			sharpUnderdog = 0
			if useDK:
				sharpUnderdog = dkLine
			elif avg:
				sharpUnderdog = int(ou.split("/")[0])
			else:
				sharpUnderdog = int(bet365Lines[team][player].split("/")[0])

			#fdLine = fdLine * 1.5

			line = fdLine
			fd = True
			if False and not useDK and dkLine > fdLine and dkLine > sharpUnderdog:
				line = dkLine
				fd = False
				#print(fdLine, dkLine, sharpUnderdog, player)

			if player in evData:
				continue
			if dinger or line > sharpUnderdog:
				pass
				if useDK:
					bet365ou = ou = f"{sharpUnderdog}/{dkLines[game][player]['hr']['under']}"

				devigger(evData, player, bet365ou, line, dinger)
				devigger(evData, player, ou, line, dinger, avg=True)
				if player not in evData:
					print(player)
					continue
				evData[player]["game"] = game
				evData[player]["team"] = team
				evData[player]["ou"] = ou
				evData[player]["bet365"] = bet365ou
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

	with open(f"{prefix}static/mlbprops/bpp.json") as fh:
		bppLines = json.load(fh)

	with open(f"{prefix}static/freebets/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/freebets/actionnetwork.json") as fh:
		actionnetwork = json.load(fh)

	data = []
	bet365data = []
	for player in evData:
		ev = float(evData[player]["ev"])
		if "bet365ev" not in evData[player]:
			bet365ev = 0
		else:
			bet365ev = float(evData[player]["bet365ev"])
		bpp = dk = mgm = pb = cz = br = kambi = ""
		team = evData[player].get("team", "")
		if team and team in bppLines and player in bppLines[team]:
			bpp = "\t".join([x or '-' for x in [bppLines[team][player]["mgm"], bppLines[team][player]["cz"], bppLines[team][player]["pn"], bppLines[team][player]["bs"]]])
		else:
			bpp = "\t".join(['-']*4)

		if team and team in actionnetwork and player in actionnetwork[team] and "hr" in actionnetwork[team][player]:
			dk = actionnetwork[team][player]["hr"].get("draftkings", "-")
			mgm = actionnetwork[team][player]["hr"].get("mgm", "-")
			br = actionnetwork[team][player]["hr"].get("betrivers", "-")
			cz = actionnetwork[team][player]["hr"].get("caesars", "-")
			pb = actionnetwork[team][player]["hr"].get("pointsbet", "-")

		if team and team in kambiLines and player in kambiLines[team]:
			kambi = kambiLines[team][player]

		bet365 = evData[player]['bet365'][1:]
		avg = evData[player]['ou']

		#print(evData[player]["bet365"])
		tab = "\t".join([str(x) for x in [ev, bet365ev, team.upper(), player.title(), evData[player].get("fanduel", 0), avg, bet365, dk, mgm, cz, pb, br, "-", "-", kambi]])
		data.append((ev, player, tab, evData[player]))
		bet365data.append((bet365ev, player, tab, evData[player]))

	dt = datetime.strftime(datetime.now(), "%I %p")
	output = f"\t\t\tUPD: {dt}\n\n"
	output += "\t".join(["EV (AVG)", "EV (365)", "Team", "Player", "FD", "AVG", "bet365", "DK", "MGM", "CZ","PB", "BR", "PN", "BS", "Kambi"]) + "\n"
	bet365output = output
	reddit = bet365reddit = ""
	for row in sorted(data, reverse=True):
		playerData = row[-1]
		line = f"{playerData['fanduel']} FD"
		if not playerData["fanduel"]:
			line = f"{playerData['other']} {playerData['otherBook']}"
		output += f"{row[-2]}\n"
		reddit += f"{playerData['ev']}% EV: {playerData.get('team', '').upper()} {row[1].title()} +{line} vs AVG {playerData['ou']}  \n"

	for row in sorted(bet365data, reverse=True):
		playerData = row[-1]
		line = f"{playerData['fanduel']} FD"
		if not playerData["fanduel"]:
			line = f"{playerData['other']} {playerData['otherBook']}"
		bet365output += f"{row[-2]}\n"
		bet365reddit += f"{playerData.get('bet365ev', '-')}% EV: {playerData.get('team', '').upper()} {row[1].title()} +{line} vs bet365 {playerData['bet365']}  \n"

	with open(f"{prefix}static/freebets/reddit", "w") as fh:
		fh.write(reddit)

	with open(f"{prefix}static/freebets/reddit365", "w") as fh:
		fh.write(bet365reddit)

	with open(f"{prefix}static/freebets/ev.csv", "w") as fh:
		fh.write(output)

	with open(f"{prefix}static/freebets/ev365.csv", "w") as fh:
		fh.write(bet365output)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--avg", action="store_true", help="AVG")
	parser.add_argument("--fd", action="store_true", help="Fanduel")
	parser.add_argument("--dk", action="store_true", help="Draftkings")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("-p", "--print", action="store_true", help="Print")
	parser.add_argument("--dinger", action="store_true", help="Dinger Tues")

	args = parser.parse_args()

	dinger = False
	if args.dinger:
		dinger = True

	if args.fd:
		writeFanduel()

	if args.kambi:
		writeKambi()

	if args.ev:
		writeEV(dinger=dinger, date=args.date, useDK=args.dk, avg=args.avg)

	if args.bpp:
		checkBPP()

	if args.action:
		writeActionNetwork()

	if args.print:
		sortEV()
	#write365()
	#writeActionNetwork()

	data = {}
	#devigger(data, player="anthony santander", bet365Odds="+360/-500", finalOdds=390)
	#devigger(data, player="anthony santander", bet365Odds="300/-465", finalOdds=390, avg=True)
	#print(data)
