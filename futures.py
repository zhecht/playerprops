import argparse
import json
import os
import random
import time
import nodriver as uc

from controllers.shared import *
from datetime import datetime, timedelta

async def writeFDPage(tabName, page, data):
	#await page.wait_for(selector="div[data-test-id=ArrowAction]")
	await page.wait_for(selector="div[role=button]")

	if tabName in ["world series", "league winners"]:
		arrows = []
	else:
		arrows = await page.query_selector_all("div[data-test-id=ArrowAction]")

	for arrowIdx, arrow in enumerate(arrows):
		prop = arrow.children[0].children[0].text.lower()
		if tabName == "playoffs" and "to make playoffs" not in prop:
			continue
		elif tabName == "win totals":
			if "team to win" not in prop and "regular season wins" not in prop:
				continue

		path = arrow.children[-1].children[0].children[0]
		if prop != "lines" and path.attributes[1].split(" ")[0] != "M.147":
			await arrow.click()

	els = await page.query_selector_all("div[aria-label='Show more']")
	for el in els:
		await el.click()

	btns = await page.query_selector_all("div[role=button]")
	for btn in btns:
		try:
			labelIdx = btn.attributes.index("aria-label")
		except:
			continue
		label = btn.attributes[labelIdx + 1].lower().split(", ")
		if "selection unavailable" in label[-1] or label[0].startswith("tab ") or len(label) <= 1:
			continue

		if label[0][:-5].endswith("home runs") or label[0][:-5].endswith("home runs leader"):
			p = "hr"
		elif label[0][:-5].endswith("strikeouts") or label[0][:-5].endswith("strikeouts leader"):
			p = "k"
		elif label[0][:-5].endswith("stolen bases") or label[0][:-5].endswith("stolen bases leader"):
			p = "sb"
		elif label[0][:-5].endswith("make playoffs"):
			p = "playoffs"
		elif label[0][:-5].endswith("regular season wins") or label[0][:-5].endswith("regular season games"):
			p = "team_wins"
		elif tabName == "league winners":
			p = "league"
		elif tabName == "divisions":
			p = "division"
		elif tabName in ["world series"]:
			p = tabName.replace(" ", "_")
		else:
			continue

		line = prop = ""
		if p in ["world_series", "league", "division", "team_wins"]:
			player = convertMLBTeam(label[1])
		elif label[0].startswith("player") or label[0].startswith("pitcher") or label[0].startswith("team to win"):
			line = str(float(label[0].split(' ')[3].replace("+", "")) - 0.5)
			prop = p
			player = parsePlayer(label[1])
		elif label[0].endswith("leader 2025"):
			prop = f"{p}_leader"
			player = parsePlayer(label[1])
		elif p == "playoffs":
			player = convertMLBTeam(label[0].split(" to ")[0])
		else:
			if p == "wins":
				player = convertMLBTeam(label[0].split(" regular")[0])
			else:
				player = parsePlayer(label[0].split(" regular")[0])
			line = label[1].split(" ")[1]

		if not prop:
			prop = p

		if prop not in data:
			data[prop] = {}
		if player not in data[prop]:
			data[prop][player] = {}

		if prop == "playoffs" and label[1] == "no":
			data[prop][player] += "/"+label[-1]
		elif not line:
			data[prop][player] = label[-1]
		else:
			if label[1].startswith("under"):
				if line in data[prop][player]:
					data[prop][player][line] += "/"+label[-1]
				else:
					data[prop][player][line] = f"-/{label[-1]}"
			else:
				data[prop][player][line] = label[-1]

async def writeFD(sport, keep):
	url = f"https://mi.sportsbook.fanduel.com/navigation/{sport}"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="nav")
	nav = await page.query_selector_all("nav")
	nav = nav[-1]
	tabs = await nav.query_selector_all("a")

	data = {}
	if keep:
		with open("static/mlbfutures/fanduel.json") as fh:
			data = json.load(fh)

	for tabIdx in range(len(tabs)):
		tabName = tabs[tabIdx].text_all.lower()
		if tabName in ["games", "spring training", "awards"]:
			continue
		if tabName not in ["divisions"]:
			pass
			#continue

			#await tabs[tabIdx].mouse_click()
		print(tabName)
		await tabs[tabIdx].click()
		await writeFDPage(tabName, page, data)
		nav = await page.query_selector_all("nav")
		tabs = await nav[-1].query_selector_all("a")

	browser.stop()

	with open(f"static/{sport}futures/fanduel.json", "w") as fh:
		json.dump(data, fh, indent=4)

async def writeDK(sport, keep):
	url = "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=champion&subcategory=champion"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector=".sportsbook-categories-tablist")
	mainTabs = await page.query_selector_all(".sportsbook-categories-tablist a[role=tab]")

	data = {}
	for mainIdx in range(len(mainTabs)):
		mainTab = mainTabs[mainIdx]
		mainTabName = mainTab.text.lower()
		if mainTabName in ["game lines", "series props", "awards", "start of season", "quick sgp"]:
			continue

		print(mainTabName)

		# testing
		if mainTabName != "team wins":
			pass
			#continue

		await mainTab.click()

		await page.wait_for(selector=".sportsbook-tabbed-subheader__tabs")
		subTabs = await page.query_selector_all(".sportsbook-tabbed-subheader__tabs a[role=tab]")

		for subIdx in range(len(subTabs)):
			subTab = subTabs[subIdx]
			prop = subTab.text.lower()
			#print(prop)

			if prop == "champion":
				prop = "world_series"
			elif prop == "wins o/u":
				prop = "team_wins"
			#elif prop == "to win x+ games":
			#	prop = "team_wins"
			elif prop == "to make the playoffs y/n":
				prop = "playoffs"
			elif prop == "winner" and mainTabName == "divisions":
				prop = "division"
			elif prop == "winner" and mainTabName == "leagues":
				prop = "league"
			elif mainTabName in ["home runs", "strikeouts", "stolen bases", "hits", "runs/rbis", "saves", "wins"]:
				prop = prop.replace(" ", "_").replace("stolen bases", "sb").replace("strikeouts", "k").replace("hits", "h").replace("runs", "r").replace("wins", "w").replace("saves", "sv")
			else:
				continue

			print(prop)

			if prop not in data:
				data[prop] = {}

			if subIdx != 0:
				await subTab.click()

			x = ".outcomes"
			if prop in ["world_series", "league", "sv_leader"]:
				x = ".game-props-card17"

			await page.wait_for(selector=f"{x} div[role=button]")
			btns = await page.query_selector_all(f"{x} div[role=button]")
			if prop in ["team_wins", "playoffs"]:
				for btnIdx in range(0, len(btns), 2):
					line = btns[btnIdx].text_all.split(" ")[1]
					team = convertMLBTeam(btns[btnIdx].parent.parent.parent.parent.children[0].text_all.lower().split(" regular")[0].split(" to make")[0])
					ou = f"{btns[btnIdx].text_all.split(' ')[-1]}/{btns[btnIdx+1].text_all.split(' ')[-1]}".replace("\u2212", "-")
					if prop == "playoffs":
						data[prop][team] = ou
					else:
						data[prop][team] = {
							line: ou
						}
			else:
				for btn in btns:
					text = btn.text_all.split(" ")
					odds = text[-1]
					if prop in ["world_series", "league", "division", "team_wins"]:
						player = convertMLBTeam(" ".join(text[:-1]))
					else:
						player = parsePlayer(" ".join(text[:-1]))

					if "+_" in prop:
						line = str(float(prop.split("+")[0]) - 0.5)
						p = prop.split("+_")[-1]
						if p not in data:
							data[p] = {}
						if player not in data[p]:
							data[p][player] = {}
						data[p][player][line] = odds.replace("\u2212", "-")
					else:
						data[prop][player] = odds.replace("\u2212", "-")

		mainTabs = await page.query_selector_all(".sportsbook-categories-tablist a[role=tab]")
	browser.stop()
	with open(f"static/{sport}futures/draftkings.json", "w") as fh:
		json.dump(data, fh, indent=4)

async def writeESPN(sport, keep):
	url = "https://espnbet.com/sport/baseball/organization/united-states/competition/mlb/section/futures"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="button[role=tab]")
	mainTabs = await page.query_selector_all("button[role=tab]")

	data = {}
	if keep:
		with open(f"static/{sport}futures/espn.json") as fh:
			data = json.load(fh)

	for mainIdx in range(len(mainTabs)):
		mainTabName = mainTabs[mainIdx].text.lower()

		if mainTabName != "player specials":
			continue
			pass
		
		if mainIdx != 0:
			await mainTabs[mainIdx].mouse_click()
			time.sleep(1)

		details = await page.query_selector_all("details")
		for detailIdx in range(len(details)):
			detail = details[detailIdx]
			prop = detail.children[0].children[0].text.lower()
			team = mainLine = ""

			if prop[5:] == "regular season home runs":
				prop = "hr"
			elif prop.endswith("or more home runs"):
				mainLine = str(float(prop.split(" ")[3]) - 0.5)
				prop = "hr"
			elif prop[5:] == "regular season strikeouts":
				prop = "k"
			elif prop.endswith("or more striekouts"):
				mainLine = str(float(prop.split(" ")[3]) - 0.5)
				prop = "k"
			elif prop.endswith("or more stolen bases"):
				mainLine = str(float(prop.split(" ")[3]) - 0.5)
				prop = "sb"
			elif prop == "to make playoffs":
				prop = "playoffs"
			elif mainTabName == "season wins":
				if "markets" in prop:
					team = convertMLBTeam(prop.split(" season")[0])
				else:
					mainLine = str(float(prop.split(" ")[3]) - 0.5)
				prop = "team_wins"
			else:
				continue

			if "open" not in detail.attributes:
				summary = detail.children[0]
				await summary.click()

			if prop not in data:
				data[prop] = {}

			#print(prop)

			btns = await detail.query_selector_all("button")
			if not btns:
				print(team)
				continue

			if btns[-1].text == "See All Lines":
				await btns[-1].click()
				await page.wait_for(selector=".modal")
				time.sleep(1)
				modal = await page.query_selector(".modal")
				btns = await modal.query_selector_all("button")
				for i in range(1, len(btns), 3):
					if prop == "playoffs":
						player = convertMLBTeam(btns[i].text_all.split(" To ")[0])
					else:
						player = parsePlayer(btns[i].text_all.split(" Regular")[0])

					if "pk" in btns[i+1].text_all:
						continue

					ou = f"{btns[i+1].text_all.split(' ')[-1]}/{btns[i+2].text_all.split(' ')[-1]}"
					if prop == "playoffs":
						data[prop][player] = ou.replace("Even", "+100")
						continue

					if player not in data[prop]:
						data[prop][player] = {}
					try:
						line = str(float(btns[i+1].text_all.split(" ")[-2]))
					except:
						continue
					data[prop][player][line] = ou.replace("Even", "+100")

				btn = await page.query_selector(".modal--see-all-lines button")
				await btn.click()
			elif team and prop == "team_wins":
				if team not in data[prop]:
					data[prop][team] = {}

				line = btns[0].text_all.split(" ")[1]
				ou = f"{btns[1].text_all}/{btns[3].text_all}"
				data[prop][team][line] = ou.replace("Even", "+100")
			elif prop == "team_wins":
				for btnIdx in range(0, len(btns), 2):
					team = convertMLBTeam(btns[btnIdx].text_all)
					ou = btns[btnIdx+1].text_all
					if team not in data[prop]:
						data[prop][team] = {}

					data[prop][team][mainLine] = ou.replace("Even", "+100")
			elif mainLine:
				for btn in btns:
					ou = btn.text_all.split(" ")[-1]
					player = parsePlayer(" ".join(btn.text_all.split(" ")[:-1]))
					if player not in data[prop]:
						data[prop][player] = {}
					#print(prop, player, mainLine)
					data[prop][player][mainLine] = ou.replace("Even", "+100")

	browser.stop()
	with open(f"static/{sport}futures/espn.json", "w") as fh:
		json.dump(data, fh, indent=4)

async def writeMGM(sport, keep):
	url = "https://sports.mi.betmgm.com/en/sports/events/2025-mlb-futures-16521886?market=-1"
	urls = ["https://sports.mi.betmgm.com/en/sports/events/2025-mlb-team-futures-16792859", "https://sports.mi.betmgm.com/en/sports/events/2025-mlb-player-specials-16752958?market=-1"]
	browser = await uc.start(no_sandbox=True)

	data = {}
	if keep:
		with open(f"static/{sport}futures/mgm.json") as fh:
			data = json.load(fh)

	for url in urls:
		page = await browser.get(url)

		await page.wait_for(selector="ms-option-panel")
		panels = await page.query_selector_all("ms-option-panel")

		for panelIdx, panel in enumerate(panels):
			prop = [x for x in panel.children if x.tag != "#comment"][0]
			if not prop:
				continue
			prop = prop.text_all.lower()
			if prop == "regular season wins":
				prop = "team_wins"
			elif prop == "to make the playoffs":
				prop = "playoffs"
			elif prop == "regular season home runs":
				prop = "hr"
			elif prop == "regular season hits":
				prop = "h"
			elif prop == "regular season rbis":
				prop = "rbi"
			elif prop == "regular season strikeouts":
				prop = "k"
			else:
				continue

			if prop not in data:
				data[prop] = {}

			up = await panel.query_selector("svg[title=theme-up]")
			if not up:
				up = await panel.query_selector(".clickable")
				await up.click()
				time.sleep(0.3)

			show = await panel.query_selector(".show-more-less-button")
			if show and show.text_all == "Show More":
				await show.click()
				await show.scroll_into_view()
				panels = await page.query_selector_all("ms-option-panel")
				panel = panels[panelIdx]
				time.sleep(0.3)

			teams = await panel.query_selector_all(".attribute-key")
			odds = await panel.query_selector_all("ms-option")
			#print(len(teams), len(odds))
			for teamIdx, team in enumerate(teams):
				if prop == "team_wins":
					team = convertMGMTeam(team.text.lower().strip())
				else:
					team = parsePlayer(team.text.lower().strip())
				over = await odds[teamIdx*2].query_selector(".value")
				under = await odds[teamIdx*2+1].query_selector(".value")
				if not over:
					continue
				ou = over.text
				if under:
					ou += "/"+under.text

				line = ""
				if prop == "playoffs":
					data[prop][team] = ou
				else:
					line = await odds[teamIdx*2].query_selector(".name")
					if not line:
						continue
					line = line.text.strip().split(" ")[-1]
					if team not in data[prop]:
						data[prop][team] = {}
					data[prop][team][line] = ou

		with open(f"static/{sport}futures/mgm.json", "w") as fh:
			json.dump(data, fh, indent=4)

	browser.stop()
	with open(f"static/{sport}futures/mgm.json", "w") as fh:
		json.dump(data, fh, indent=4)

async def write365(sport, keep):
	browser = await uc.start(no_sandbox=False)

	# E112265508, E112347081, E113646358, E112347082, E112347080
	# HR, RBI, SB, K, H
	urls = ["https://www.oh.bet365.com/?_h=r87CLpn5DwBruz4SjYRYyQ%3D%3D&btsffd=1#/AC/B16/C20934240/D1/E112347080/F2/"]

	# Milestones
	# E114485752, E114697449, E114696522, E114486791, E115896845
	urls = ["https://www.oh.bet365.com/?_h=N-Ejb9j5XJf0TwmJjL1fKA%3D%3D&btsffd=1#/AC/B16/C20934240/D1/E115896845/F2/"]

	# team wins
	#urls = ["https://www.oh.bet365.com/?_h=r87CLpn5DwBruz4SjYRYyQ%3D%3D&btsffd=1#/AC/B16/C20934240/D1/E112662049/F2/"]

	data = {}
	if keep:
		with open(f"static/{sport}futures/bet365.json") as fh:
			data = json.load(fh)

	for url in urls:
		page = await browser.get(url)

		await page.wait_for(selector=".rcl-MarketGroupButton_TextWrapper")
		dropdown = await page.query_selector(".rcl-MarketGroupButton_TextWrapper")

		if False:
			await dropdown.scroll_into_view()
			await dropdown.mouse_click()
			#await dropdown.click()
			await page.wait_for(selector=".smd-DropDownItem")
			tabs = await page.query_selector_all(".smd-DropDownItem")

		tabs = [None]

		for tabIdx in range(len(tabs)):
			if tabs[tabIdx] is None:
				tabName = dropdown.text_all.lower()
			else:
				tabName = tabs[tabIdx].text.lower()
			mainProp = ""
			if tabName.endswith("milestones"):
				mainProp = tabName.split(" ")[-2].replace("strikeouts", "k").replace("runs", "r").replace("in", "rbi").replace("bases", "sb")
			elif tabName == "to win outright":
				mainProp = "world_series"
			elif tabName == "to win league":
				mainProp = "league"
			elif tabName == "to win division":
				mainProp = "division"
			elif tabName == "regular season wins":
				mainProp = "team_wins"
			elif tabName == "to make the playoffs":
				mainProp = "playoffs"
			elif tabName.startswith("player regular season"):
				mainProp = tabName.split(" ")[-1].replace("hits", "h").replace("in", "rbi").replace("runs", "hr").replace("bases", "sb")
			elif tabName.startswith("pitcher regular season"):
				mainProp = "k"
			else:
				continue

			if "milestones" in tabName or mainProp not in ["sb"]:
				#continue
				pass

			print(tabIdx, tabName, mainProp)

			if tabs[tabIdx] is not None:
				#await tabs[tabIdx].scroll_into_view()
				await tabs[tabIdx].mouse_click()
				time.sleep(2)

			reject = await page.query_selector(".ccm-CookieConsentPopup_Reject")
			if reject:
				await reject.mouse_click()

			if True:
				for c in ["src-FixtureSubGroupWithShowMore_Closed", "src-FixtureSubGroup_Closed", "src-HScrollFixtureSubGroupWithBottomBorder_Closed", "suf-CompetitionMarketGroupButton_Text[aria-expanded=false]"]:
					divs = await page.query_selector_all("."+c)

					for div in divs:
						await div.scroll_into_view()
						await div.mouse_click()
						#await el.scroll_into_view()
						#time.sleep(round(random.uniform(0.9, 1.25), 2))
				time.sleep(0.5)
				for c in ["src-FixtureSubGroupWithShowMore_Closed", "src-FixtureSubGroup_Closed", "src-HScrollFixtureSubGroupWithBottomBorder_Closed", "suf-CompetitionMarketGroupButton_Text[aria-expanded=false]"]:
					divs = await page.query_selector_all("."+c)

					for div in divs:
						await div.scroll_into_view()
						await div.mouse_click()

				time.sleep(0.5)
				for c in ["src-FixtureSubGroupWithShowMore_Closed", "src-FixtureSubGroup_Closed", "src-HScrollFixtureSubGroupWithBottomBorder_Closed", "suf-CompetitionMarketGroupButton_Text[aria-expanded=false]"]:
					divs = await page.query_selector_all("."+c)

					for div in divs:
						await div.scroll_into_view()
						await div.mouse_click()

				links = await page.query_selector_all(".msl-ShowMore_Link")

				for el in links:
					await el.scroll_into_view()
					#time.sleep(round(random.uniform(0.9, 1.25), 2))
					await el.mouse_click()
					time.sleep(round(random.uniform(0.9, 1.25), 2))

			if mainProp in ["team_wins", "playoffs"]:
				prop = mainProp
				if prop not in data:
					data[prop] = {}
				teams = await page.query_selector_all(".srb-ParticipantLabel_Name")
				markets = await page.query_selector_all(".gl-Market")
				overs = await markets[1].query_selector_all("div[role=button]")
				unders = await markets[2].query_selector_all("div[role=button]")
				for team, over, under in zip(teams, overs, unders):
					player = convertMLBTeam(team.text)
					if mainProp in ["playoffs"]:
						data[prop][player] = over.children[-1].text+"/"+under.children[-1].text
					else:
						if player not in data[prop]:
							data[prop][player] = {}
						data[prop][player][over.children[0].text] = over.children[-1].text+"/"+under.children[-1].text
			else:
				divs = await page.query_selector_all(".gl-MarketGroupPod")
				for div in divs:
					if "milestones" in tabName:
						txt = div.children[0].text_all.lower().replace("\xa0", " ")
						line = str(float(txt.split("+")[0].split(" ")[-1]) - 0.5)
						prop = txt.split("+ ")[-1].split(" - ")[0].split(" ")[-1].replace("hits", "h").replace("in", "rbi").replace("runs", "hr").replace("bases", "sb").replace("strikeouts", "k")
					else:
						prop = mainProp

					if prop not in data:
						data[prop] = {}

					btns = await div.children[-1].query_selector_all("div[role=button]")
					if "milestones" not in tabName and prop in ["k", "hr", "h", "sb", "rbi"]:
						player = div.children[0].children[0].children[0].text_all.split(" - ")[-1]
						player = parsePlayer(player)
						if player not in data[prop]:
							data[prop][player] = {}

						#print(player, btns[0].children[-1].text)
						ou = btns[0].children[-1].text+"/"+btns[1].children[-1].text
						line = btns[0].children[0].text.split(" ")[-1]
						data[prop][player][line] = ou
						continue

					for btn in btns:
						if "Show less" in btn.text_all:
							continue
						if prop in ["world_series", "league", "division"]:
							player = convertMLBTeam(btn.children[0].text)
						else:
							player = parsePlayer(btn.children[0].text)

						if "milestones" in tabName:
							data[prop].setdefault(player, {}) 
							data[prop][player][line] = btn.children[-1].text
						else:
							data[prop][player] = btn.children[-1].text

			with open(f"static/{sport}futures/bet365.json", "w") as fh:
				json.dump(data, fh, indent=4)

			dropdown = await page.query_selector(".rcl-MarketGroupButton_TextWrapper")
			if dropdown:
				await dropdown.scroll_into_view()
				await dropdown.mouse_click()
				time.sleep(0.75)
				await page.wait_for(selector=".smd-DropDownItem")
				tabs = await page.query_selector_all(".smd-DropDownItem")

	browser.stop()
	with open(f"static/{sport}futures/bet365.json", "w") as fh:
		json.dump(data, fh, indent=4)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--sport")
	parser.add_argument("--team", "-t")
	parser.add_argument("--league", "-l")
	parser.add_argument("--fd", action="store_true")
	parser.add_argument("--dk", action="store_true")
	parser.add_argument("--mgm", action="store_true")
	parser.add_argument("--espn", action="store_true")
	parser.add_argument("--bet365", action="store_true")
	parser.add_argument("--keep", action="store_true")

	args = parser.parse_args()
	sport = args.sport or "mlb"

	if args.fd:
		uc.loop().run_until_complete(writeFD(sport, args.keep))
	elif args.dk:
		uc.loop().run_until_complete(writeDK(sport, args.keep))
	elif args.mgm:
		uc.loop().run_until_complete(writeMGM(sport, args.keep))
	elif args.bet365:
		uc.loop().run_until_complete(write365(sport, args.keep))
	elif args.espn:
		uc.loop().run_until_complete(writeESPN(sport, args.keep))