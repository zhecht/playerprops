from flask import *
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time

try:
    from controllers.functions import *
except:
    from functions import *

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
    # if on linux aka prod
    prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
    # if on linux aka prod
    prefix = "/home/playerprops/playerprops/"

draft_blueprint = Blueprint('draft', __name__, template_folder='views')

def writeBoris():
    url = f"http://www.borischen.co/p/half-ppr-draft-tiers.html"
    outfile = "outnfl"
    #call(["curl", "-k", url, "-o", outfile])
    soup = BS(open(outfile, 'rb').read(), "lxml")

    tiers = {}
    base = "https://s3-us-west-1.amazonaws.com/fftiers/out/text_ALL-HALF-PPR-adjust"
    for i in range(3):
        url = f"{base}{i}.txt"
        time.sleep(0.2)
        call(["curl", "-k", url, "-o", outfile])
        
        with open(outfile) as fh:
            rows = [row.strip() for row in fh.readlines()]

        for row in rows:
            tier = row.split(": ")[0].split(" ")[-1]
            for player in row.split(": ")[1].split(", "):
                player = parsePlayer(player)
                tiers[player] = tier

    posTiers = {}
    base = "https://s3-us-west-1.amazonaws.com/fftiers/out/text_"
    for pos in ["qb", "rb", "wr", "te"]:
        if pos == "qb":
            url = f"{base}{pos.upper()}.txt"
        else:
            url = f"{base}{pos.upper()}-HALF.txt"
        time.sleep(0.2)
        call(["curl", "-k", url, "-o", outfile])
        
        with open(outfile) as fh:
            rows = [row.strip() for row in fh.readlines()]

        for row in rows:
            tier = row.split(": ")[0].split(" ")[-1]
            for player in row.split(": ")[1].split(", "):
                player = parsePlayer(player)
                posTiers[player] = tier

    with open(f"{prefix}static/draft/tiers.json", "w") as fh:
        json.dump(tiers, fh, indent=4)

    with open(f"{prefix}static/draft/posTiers.json", "w") as fh:
        json.dump(posTiers, fh, indent=4)

def writeDepthCharts():
    data = {}
    for team in SNAP_LINKS:
        if team == "was":
            team = "wsh"

        data[team] = {}

        time.sleep(0.2)
        url = f"https://www.espn.com/nfl/team/depth/_/name/"+team
        outfile = "outnfl"
        call(["curl", "-k", url, "-o", outfile])
        soup = BS(open(outfile, 'rb').read(), "lxml")

        pos = []
        for row in soup.find("tbody").findAll("tr"):
            p = row.text.strip().lower()
            if p == "wr":
                if "wr1" not in pos:
                    p = "wr1"
                elif "wr2" not in pos:
                    p = "wr2"
                else:
                    p = "wr3"
            pos.append(p)

        for row, p in zip(soup.findAll("tbody")[1].findAll("tr"), pos):
            data[team][p] = []
            for a in row.findAll("a"):
                player = parsePlayer(a.text)
                data[team][p].append(player)

    with open(f"{prefix}static/draft/depthChart.json", "w") as fh:
        json.dump(data, fh, indent=4)

def parsePlayer(player):
    return player.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "").replace("\u00a0", " ")


def writeMGM():
    url = "https://sports.mi.betmgm.com/en/sports/events/2023-24-nfl-regular-season-stats-14351210"

    js = """

const data = {};

async function f() {
    const main = document.querySelector("#main-view");
    for (const a1 of main.querySelectorAll(".tab-bar-container")[0].querySelectorAll("a")) {
        if (a1.innerText === "All") {
            continue;
        }
        a1.click();
        await new Promise(resolve => setTimeout(resolve, 1000));

        for (const a of main.querySelectorAll(".tab-bar-container")[1].querySelectorAll("a")) {
            a.click();
            await new Promise(resolve => setTimeout(resolve, 1000));
            const btn = main.querySelector(".show-more-less-button");
            if (btn.innerText === "Show More") {
                btn.click();
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
            const header = a.innerText.toLowerCase().replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yd").replace("touchdowns", "td").replace("interceptions thrown", "int").replace(" ", "_");
            
            for (const playerDiv of main.querySelectorAll(".player-props-player-name")) {
                const player = playerDiv.innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
                if (!data[player]) {
                    data[player] = {};
                }
                const overEl = playerDiv.parentElement.nextElementSibling;
                const over = overEl.querySelector(".name").innerText.toLowerCase().replace("over ", "o") + " " +overEl.querySelector(".value").innerText;
                const under = overEl.nextElementSibling.querySelector(".value").innerText;
                data[player][header] = over+"/"+under;
            }
        }
    }
}

f();

console.log(data);

"""

def writeKambi():
    url = "https://c3-static.kambi.com/client/pivuslarl-lbr/index-retail-barcode.html#sports-hub/american_football/nfl"

    url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/american_football/nfl/all/all/competitions.json?lang=en_US&market=US"

    #continue until after 1019484336 (wsh commanders markets)
    outfile = "outnfl"
    call(["curl", "-k", url, "-o", outfile])

    with open(outfile) as fh:
        events = json.load(fh)

    ids = {}
    start = False
    for idx, event in enumerate(events["events"]):
        #print(idx)
        player = parsePlayer(event["event"]["name"])
        if "markets" in player and " vs " not in player:
            player = player.split(" markets")[0].split(" (")[0]
            if event["event"]["id"] == 1019484336:
                start = True
            elif start:
                ids[player] = event["event"]["id"]


    rodgersId = "1019465825"
    mahomesId = "1019869514"
    data = {}
    for player in ids:
        time.sleep(0.3)
        url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{ids[player]}.json?lang=en_US&market=US"
        call(["curl", "-k", url, "-o", outfile])

        with open(outfile) as fh:
            events = json.load(fh)

        for row in events["betOffers"]:
            header = row["criterion"]["label"].lower()
            hdr = ""
            if "&" in header:
                continue
            if "passing yards" in header:
                hdr = "pass_yd"
            elif "rushing yards" in header:
                hdr = "rush_yd"
            elif "receiving yards" in header:
                hdr = "rec_yd"
            elif "passing touchdowns" in header:
                hdr = "pass_td"
            elif "receiving touchdowns" in header:
                hdr = "rec_td"
            elif "rushing touchdowns" in header:
                hdr = "rush_td"
            elif "receptions" in header:
                hdr = "rec"
            elif "interceptions thrown" in header:
                hdr = "int"

            if not hdr:
                continue

            if player not in data:
                data[player] = {}

            line = row["outcomes"][0]["line"] / 1000
            data[player][hdr] = f"o{line} {row['outcomes'][0]['oddsAmerican']}/{row['outcomes'][1]['oddsAmerican']}"

    with open(f"{prefix}static/draft/kambi.json", "w") as fh:
        json.dump(data, fh, indent=4)



def write365():
    url = "https://www.oh.bet365.com/?_h=GY_bcYP5idsD_IzQUsW36w%3D%3D#/AC/B12/C20865512/D1/E89363498/F2/"
    
    js = """

    const data = {}

    {
        let header = document.querySelector(".rcl-MarketGroupButton_MarketTitle").innerText.toLowerCase().replace("player ", "").replace(" regular season", "").replace("passing", "pass").replace("yards", "yd").replace("rushing", "rush").replace("receiving", "rec").replace("touchdowns", "td").replace("receptions", "rec").replace(" ", "_");

        if (header.indexOf("_td") >= 0) {
            for (const row of document.querySelectorAll(".src-FixtureSubGroupWithShowMore")) {

                if (row.className.indexOf("src-FixtureSubGroupWithShowMore_Closed") >= 0) {
                    row.click();
                }
                const player = row.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");

                if (!data[player]) {
                    data[player] = {};
                }
                const over = row.querySelector(".gl-ParticipantBorderless_Name").innerText.replace("Over ", "o");
                const odds = row.querySelector(".gl-ParticipantBorderless_Odds").innerText;
                const under = row.querySelectorAll(".gl-ParticipantBorderless_Odds")[1].innerText;
                data[player][header] = over+" "+odds+"/"+under;
            }

        } else if (header.indexOf("_yd") >= 0) {
            const players = [];
            for (const row of document.querySelectorAll(".srb-ParticipantLabel_Name")) {
                const player = row.innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
                if (!data[player]) {
                    data[player] = {};
                }
                players.push(player);
            }

            let idx = 0;
            for (const row of document.querySelectorAll(".gl-Market")[1].querySelectorAll(".gl-Participant_General")) {
                const player = players[idx];
                const over = row.querySelector(".gl-ParticipantCenteredStacked_Name").innerText.replace("Over ", "o");
                const odds = row.querySelector(".gl-ParticipantCenteredStacked_Odds").innerText;
                data[player][header] = over+" "+odds;
                idx += 1;
            }

            idx = 0;
            for (const row of document.querySelectorAll(".gl-Market")[2].querySelectorAll(".gl-Participant_General")) {
                const player = players[idx];
                const odds = row.querySelector(".gl-ParticipantCenteredStacked_Odds").innerText;
                data[player][header] += "/"+odds;
                idx += 1;
            }
        }
    }

    console.log(data)

"""

def writeCZ():
    url = 'https://sportsbook.caesars.com/us/mi/bet/americanfootball/futures?id=007d7c61-07a7-4e18-bb40-15104b6eac92'

    js = """

    const data = {};

    {
        const headers = document.querySelectorAll(".expanderHeader");
        for (const div of headers) {
            if (div.innerText.indexOf("Total Regular Season") === 0) {

                if (div.className.indexOf("collapsed") >= 0) {
                    div.click();
                }

                const hdr = div.innerText.toLowerCase().replace("passing", "pass").replace("yards", "yd").replace("rushing", "rush").replace("receiving", "rec").replace("touchdowns", "td").replace("receptions", "rec");
                let hdr1 = hdr.split(" ")[3];
                if (hdr.split(" ").length > 4) {
                    hdr1 += "_"+hdr.split(" ")[4];
                }
                
                if (hdr1 === "sacks") {
                    continue;
                }
                if (hdr1 === "touchdown_passes") {
                    hdr1 = "pass_td";
                }              

                for (const row of div.parentNode.querySelectorAll(".EventCard")) {
                    const player = row.querySelector(".marketTemplateTitle").innerText.split(" 2023")[0].toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
                    
                    if (!data[player]) {
                        data[player] = {};
                    }
                    const btns = row.querySelectorAll("button");
                    const line = parseFloat(btns[0].querySelector("span").innerText.replace(",", ""));
                    const odds = btns[0].querySelectorAll("span")[1].innerText+"/"+btns[1].querySelectorAll("span")[1].innerText;

                    data[player][hdr1] = "o"+line+" "+odds;
                }
            }
        }
    }
    console.log(data);

"""

def writeYahoo():
    url = "https://football.fantasysports.yahoo.com/f1/471322/players?&sort=AR&sdir=1&status=A&pos=O&stat1=S_PS_2023&jsenabled=1"

    js = """

    const data = {};

    function loopScript() {
        const table = document.querySelector("table");
        const headers = ["pass_yd", "pass_td", "int", "rush_att", "rush_yd", "rush_td", "rec", "rec_yd", "rec_td", "tgt", "2pt", "fumble"];

        let start = 0;
        for (const th of table.querySelector("thead").querySelectorAll("tr")[1].querySelectorAll("th")) {
            if (th.innerText === "Yds") {
                break;
            }
            start += 1;
        }

        for (const tr of table.querySelector("tbody").querySelectorAll("tr")) {
            const player = tr.querySelectorAll("a")[2].innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
            data[player] = {};
            let idx = 0;
            for (const td of tr.querySelectorAll("td:not(:nth-child(-n+"+start+")):nth-child(n)")) {
                if (headers[idx]) {
                    data[player][headers[idx]] = parseFloat(td.innerText);
                }
                idx += 1;
            }
        }
    }

    async function main(){
        let loop = true;
        while (loop) {
            loopScript();
            await new Promise(resolve => setTimeout(resolve, 2000));

            let found = false;
            for (const a of document.querySelector(".pagingnavlist").querySelectorAll("a")) {
                if (a.innerText == "Next 25") {
                    found = true;
                    a.click();
                }
            }

            if (!found) {
                loop = false;
            }
        }
    }

    main();
"""

def writeFanduel():
    url = "https://mi.sportsbook.fanduel.com/navigation/nfl?tab=passing-props"

    js = """

    const data = {};

    {
        let prop = "";
        let player = "";
        for (const li of document.getElementById("main").getElementsByTagName("li")) {
            if (!li.innerText) {
                continue;
            }
            const h2 = li.getElementsByTagName("h2");
            const h3 = li.getElementsByTagName("h3");
            const arrow = li.querySelector('[data-test-id="ArrowAction"]');
            
            if (arrow) {
                const path = li.querySelector("path");
                if (path && path.getAttribute("d").indexOf("M8") === 0) {
                    li.querySelector("svg").parentElement.click();
                }
            } else if (h2.length) {
                prop = h2[0].innerText.toLowerCase().replace("regular season ", "").replace("rushing", "rush").replace("receiving", "rec").replace("passing", "pass").replace("yards", "yd").replace("touchdowns", "td").replace("total receptions", "rec").replaceAll(" ", "_");
                if (prop.indexOf("props") >= 0) {
                    continue;
                }
            } else if (h3.length) {
                player = h3[0].innerText.toLowerCase().split(" 2023")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
            } else if (prop && player) {
                if (prop.indexOf("props") >= 0) {
                    continue;
                } else if (player.indexOf("most regular") === 0) {
                    continue;
                } else if (player.indexOf("to throw") === 0) {
                    continue;
                } else if (player.split(" ")[0].indexOf("+") >= 0) {
                    continue;
                }

                let line = odds = under = over = "";
                try {
                    over = li.querySelector('[role="button"]');
                    under = li.querySelectorAll('[role="button"]')[1].querySelectorAll("span")[1].innerText;
                    line = over.querySelector("span").innerText.toLowerCase().replaceAll(" ", "");
                    odds = over.querySelectorAll("span")[1].innerText;
                } catch {
                    continue;
                }

                if (!data[player]) {
                    data[player] = {};
                }
                data[player][prop] = line+" "+odds+"/"+under;
            }
        }
    }

    console.log(data);

"""

def convertDKProp(name):
    return name.replace("yards", "yd").replace("tds", "td").replace("receptions", "rec").replace("qb ints", "int").replace("ints", "int").replace(" ", "_")

def writeDK():
    url = f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/88808/categories/782?format=json"
    outfile = "outnfl"
    call(["curl", "-k", url, "-o", outfile])

    with open(outfile) as fh:
        data = json.load(fh)

    if "eventGroup" not in data:
        return

    props = {}
    subCats = {}
    for catRow in data["eventGroup"]["offerCategories"]:
        if catRow["offerCategoryId"] != 782:
            continue
        for cRow in catRow["offerSubcategoryDescriptors"]:
            prop = convertDKProp(cRow["name"].lower())
            if prop not in ["pass_yd", "pass_td", "rec_yd", "rec_td", "rush_yd", "rush_td", "rec", "int"]:
                continue
            subCats[prop] = cRow["subcategoryId"]

    for prop in subCats:
        time.sleep(0.4)
        url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/88808/categories/782/subcategories/{subCats[prop]}?format=json"
        call(["curl", "-k", url, "-o", outfile])

        with open(outfile) as fh:
            data = json.load(fh)

        events = {}
        for event in data["eventGroup"]["events"]:
            events[event["eventId"]] = event["name"].lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")
    
        for catRow in data["eventGroup"]["offerCategories"]:
            if "offerSubcategoryDescriptors" not in catRow:
                continue
            for cRow in catRow["offerSubcategoryDescriptors"]:
                if "offerSubcategory" not in cRow:
                    continue
                for offerRow in cRow["offerSubcategory"]["offers"]:
                    for row in offerRow:
                        player = events[row["eventId"]]
                        if player not in props:
                            props[player] = {}

                        props[player][prop] = row["outcomes"][0]["label"].replace("Over ", "o") + " " + row["outcomes"][0]["oddsAmerican"] + "/" + row["outcomes"][1]["oddsAmerican"]

    with open(f"{prefix}static/draft/draftkings.json", "w") as fh:
        json.dump(props, fh, indent=4)

def writeNumberfire():
    url = "https://www.numberfire.com/nfl/fantasy/remaining-projections"
    outfile = "outnfl"
    time.sleep(0.2)
    call(["curl", "-k", url, "-o", outfile])
    soup = BS(open(outfile, 'rb').read(), "lxml")

    players = []
    for row in soup.find("table", class_="projection-table").find("tbody").findAll("tr"):
        player = row.find("span").text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")
        players.append(player)

    data = {}
    statTable = soup.findAll("table", class_="projection-table")[1]
    for row, player in zip(statTable.find("tbody").findAll("tr"), players):
        data[player] = {}
        for td in row.findAll("td")[4:]:
            hdr = td.get("class")[0]
            data[player][hdr] = td.text.strip()

    with open(f"{prefix}static/draft/numberfire.json", "w") as fh:
        json.dump(data, fh, indent=4)

def writeNFL():
    url = "https://fantasy.nfl.com/research/projections#researchProjections=researchProjections%2C%2Fresearch%2Fprojections%253Fposition%253DO%2526sort%253DprojectedPts%2526statCategory%253DprojectedStats%2526statSeason%253D2023%2526statType%253DseasonProjectedStats%2Creplace"

def writeADP():
    url = "https://www.fantasypros.com/nfl/adp/half-point-ppr-overall.php"
    outfile = "outnfl"
    time.sleep(0.3)
    call(["curl", "-k", url, "-o", outfile])
    soup = BS(open(outfile, 'rb').read(), "lxml")

    adp = {}
    for row in soup.find("table", id="data").findAll("tr")[1:]:
        player = parsePlayer(row.find("a").text)
        adp[player] = {}
        for idx, book in zip([3,4,5], ["yahoo", "sleeper", "rtsports"]):
            adp[player][book] = row.findAll("td")[idx].text

    with open(f"{prefix}static/draft/adp.json", "w") as fh:
        json.dump(adp, fh, indent=4)


def writeFantasyPros():

    # avg between numberfire, nfl.com, fantasypros, cbs, fftoday, espn
    data = {}
    for pos in ["qb", "rb", "wr", "te", "k", "dst"]:
        url = f"https://www.fantasypros.com/nfl/projections/{pos}.php?week=draft"
        outfile = "outnfl"
        time.sleep(0.3)
        call(["curl", "-k", url, "-o", outfile])
        soup = BS(open(outfile, 'rb').read(), "lxml")

        table = soup.find("table", id="data")

        headers = []
        mainHeader = []
        for td in table.find("tr").findAll("td")[1:]:
            mainHeader.extend([td.find("b").text.lower().replace("rushing", "rush").replace("receiving", "rec").replace("passing", "pass")] * int(td.get("colspan")))

        i = 1
        if pos in ["k", "dst"]:
            i = 0
        for idx, th in enumerate(table.findAll("tr")[i].findAll("th")[1:]):
            hdr = th.text.strip().lower()
            if mainHeader:
                hdr = mainHeader[idx]+"_"+hdr
            headers.append(hdr.replace("_yds", "_yd").replace("_tds", "_td").replace("rec_rec", "rec").replace("pass_ints", "int"))

        for row in table.findAll("tr")[2:]:
            player = row.find("td").find("a").text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")
            if player not in data:
                data[player] = {
                    "pos": pos
                }
            for col, hdr in zip(row.findAll("td")[1:], headers):
                data[player][hdr] = float(col.text.strip().replace(",", ""))

    with open(f"{prefix}static/draft/fantasypros.json", "w") as fh:
        json.dump(data, fh, indent=4)

# 0.5ppr, 4pt QB TD
def calculateFantasyPoints(j, ppr=0.5, qbTd = 4):
    j["points"] = 0
    for hdr in j:
        if hdr == "player" or "book" in hdr:
            continue
        if "yd" in hdr:
            if hdr == "pass_yd":
                j["points"] += j[hdr] / 25
            else:
                j["points"] += j[hdr] / 10
        elif "td" in hdr:
            if hdr == "pass_td":
                j["points"] += j[hdr] * qbTd
            else:
                j["points"] += j[hdr] * 6
        elif hdr == "rec":
            j["points"] += j[hdr] * ppr
        elif hdr == "int":
            j["points"] += j[hdr] * -2

    j["points"] = round(j["points"], 2)

def writeECR():

    with open("ecr.csv") as fh:
        rows = [row.strip() for row in fh.readlines()]

    headers = []
    for col in rows[4].split(","):
        headers.append(col.lower())

    data = {}
    for row in rows[5:]:
        row = row.split(",")
        player = ""
        for col, hdr in zip(row, headers):
            if not col or not hdr:
                continue
            if hdr == "name":
                player = parsePlayer(col)
                data[player] = {}
            else:
                data[player][hdr] = col

    with open(f"{prefix}static/draft/ecr.json", "w") as fh:
        json.dump(data, fh, indent=4)


def writeCsv(ppr=None, qbTd=None, booksOnly=False):
    if ppr == None:
        ppr = 0.5
    if not qbTd:
        qbTd = 4

    with open(f"{prefix}static/draft/ecr.json") as fh:
        ecrData = json.load(fh)

    projections = {}

    books = ["fantasypros", "draftkings", "fanduel", "caesars", "bet365", "kambi", "mgm", "yahoo"]
    for book in books:
        with open(f"{prefix}static/draft/{book}.json") as fh:
            projections[book] = json.load(fh).copy()

    allHeaders = ["pass_yd", "pass_td", "int", "rush_att", "rush_yd", "rush_td", "rec", "rec_yd", "rec_td"]
    allData = []
    for pos in ["qb", "rb", "wr", "te"]:
        headers = []
        if pos == "qb":
            headers = ["pass_yd", "pass_td", "int", "rush_yd", "rush_td"]
        elif pos == "wr" or pos == "te":
            headers = ["rec", "rec_yd", "rec_td"]
        elif pos == "rb":
            headers = ["rush_att", "rush_yd", "rush_td", "rec", "rec_yd", "rec_td"]

        data = []
        for player in projections["fantasypros"]:
            if projections["fantasypros"][player]["pos"] not in pos:
                continue
            j = {
                "player": player.title()
            }
            for hdr in headers:
                if booksOnly:
                    j[hdr] = []
                else:
                    j[hdr] = [projections["fantasypros"][player][hdr]]
                j[hdr+"_book_fantasypros"] = projections["fantasypros"][player][hdr]
                j[hdr+"_book_odds_fantasypros"] = projections["fantasypros"][player][hdr]

                for book in ["draftkings", "fanduel", "caesars", "bet365", "kambi", "mgm", "yahoo"]:
                    if player in projections[book] and hdr in projections[book][player]:
                        val = projections[book][player][hdr]
                        if "o" in str(val):
                            val = val.split(" ")[0][1:]

                        if not booksOnly or book != "yahoo":
                            j[hdr].append(float(val))
                        j[hdr+"_book_"+book] = val
                        j[hdr+"_book_odds_"+book] = projections[book][player][hdr]

            for hdr in j:
                if hdr == "player" or "book" in hdr:
                    continue
                if not len(j[hdr]):
                    j[hdr] = 0
                else:
                    j[hdr] = round(sum(j[hdr]) / len(j[hdr]), 1)

            calculateFantasyPoints(j, ppr, qbTd)
            data.append(j)
            jj = j.copy()
            jj["pos"] = pos
            allData.append(jj)

        arr = [h.upper() for h in data[0] if "book" not in h]
        arr.insert(1, "ECR / ADP")
        output = "\t".join(arr)+"\n"
        for row in sorted(data, key=lambda k: k["points"], reverse=True):
            player = row["player"].lower()
            arr = [str(row[r]) for r in row if "book" not in r]
            books = [x for x in row if "_book_" in x and "_book_odds_" not in x]

            noLines = 0
            for idx, hdr in enumerate(headers):
                a = len([x for x in books if f"{hdr}_book_" in x and "_book_odds_" not in x])
                if a <= 2:
                    noLines += 1
                    #arr[idx+1] = f"*{arr[idx+1]}"

            if noLines == len(arr) - 2:
                arr[0] = f"*{arr[0]}"
            ecr = adp = ""
            if player in ecrData:
                ecr = ecrData[player]["ecr"]
                adp = ecrData[player]["adp"]
            arr.insert(1, f"{ecr} / {adp}")
            output += "\t".join(arr) + "\n"

        with open(f"{prefix}static/draft/{pos.replace('/', '_')}.csv", "w") as fh:
            fh.write(output)

        books = ["draftkings", "fanduel", "caesars", "bet365", "kambi", "mgm", "fantasypros", "yahoo"]
        for prop in headers:
            h = ["Player", "AVG"]
            h.extend(books)
            output = "\t".join(h)+"\n"

            for row in sorted(data, key=lambda k: k[prop], reverse=True):
                a = []
                for book in books:
                    try:
                        a.append(row[prop+"_book_"+book])
                    except:
                        a.append("-")

                player = row["player"].lower()
                if player in ecrData:
                    ecr = ecrData[player]["ecr"]
                    adp = ecrData[player]["adp"]
                h = [row["player"], row[prop]]
                h.extend(a)
                output += "\t".join([str(x) for x in h]) + "\n"
            with open(f"{prefix}static/draft/{pos.replace('/', '_')}_{prop}.csv", "w") as fh:
                fh.write(output)

        h = ["Player", "Prop", "AVG"]
        h.extend(books)
        output = "\t".join(h)+"\n"
        for row in sorted(data, key=lambda k: k["points"], reverse=True):
            output += f"{row['player']}\n"
            for prop in headers:
                output += f"\t{prop}\t{row[prop]}\t"
                a = []
                for book in books:
                    try:
                        a.append(row[prop+"_book_odds_"+book])
                    except:
                        a.append("-")
                output += "\t".join([str(x) for x in a]) + "\n"
        with open(f"{prefix}static/draft/{pos.replace('/', '_')}_all.csv", "w") as fh:
            fh.write(output)

    h = ["Player"]
    h.extend([x.upper() for x in allHeaders])
    h.append("Points")
    output = "\t".join(h)+"\n"
    for row in sorted(allData, key=lambda k: k["points"], reverse=True):
        a = [row['player']]
        for hdr in h:
            if hdr.lower() in row:
                a.append(str(row[hdr.lower()]))
            else:
                a.append("-")
        output += "\t".join(a)+f"\t{row['points']}\n"

    with open(f"{prefix}static/draft/all.csv", "w") as fh:
        fh.write(output)

    with open(f"{prefix}static/draft/all.json", "w") as fh:
        json.dump(allData, fh, indent=4)

@draft_blueprint.route('/getProjections')
def projections_route():
    with open(f"{prefix}static/draft/all.json") as fh:
        res = json.load(fh)

    with open(f"{prefix}static/draft/posTiers.json") as fh:
        posTiers = json.load(fh)

    with open(f"{prefix}static/draft/tiers.json") as fh:
        tiers = json.load(fh)

    with open(f"{prefix}static/draft/ecr.json") as fh:
        ecrData = json.load(fh)

    for row in res:
        tier = posTier = "50"
        player = row["player"].lower()
        if player in tiers:
            tier = tiers[player]

        if player in posTiers:
            posTier = posTiers[player]

        row["tier"] = tier
        row["posTier"] = posTier
        row["val"] = 0
        row["ecr"] = row["adp"] = 50
        if player in ecrData:
            for k in ["val", "ecr", "adp"]:
                row[k] = ecrData[player][k]

    return jsonify(res)

@draft_blueprint.route('/getDepthChart')
def depthChart_route():
    with open(f"{prefix}static/draft/depthChart.json") as fh:
        depthChart = json.load(fh)
    res = []
    for team in depthChart:
        j = {"team": team}
        for pos in ["qb", "rb", "wr1", "wr2", "wr3", "te"]:
            j[pos] = "\n".join(depthChart[team][pos])
        res.append(j)
    return jsonify(res)

@draft_blueprint.route('/draft')
def draft_route():
    return render_template("draft.html", pos="all")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="date")
    parser.add_argument("--dk", action="store_true", help="Draftkings")
    parser.add_argument("--nf", action="store_true", help="Numberfire")
    parser.add_argument("--fp", action="store_true", help="FantasyPros")
    parser.add_argument("--booksOnly", action="store_true", help="Books Only")
    parser.add_argument("-p", "--print", action="store_true", help="Print CSVs")
    parser.add_argument("--boris", action="store_true", help="BorisChen")
    parser.add_argument("--kambi", action="store_true", help="Kambi")
    parser.add_argument("--mgm", action="store_true", help="MGM")
    parser.add_argument("--ecr", action="store_true", help="ECR")
    parser.add_argument("--adp", action="store_true", help="ADP")
    parser.add_argument("--depth", action="store_true", help="Depth Chart")
    parser.add_argument("--ppr", help="PPR", type=float)
    parser.add_argument("--qbTd", help="PPR", type=int)

    args = parser.parse_args()

    if args.dk:
        writeDK()

    if args.ecr:
        writeECR()

    if args.adp:
        writeADP()

    if args.nf:
        writeNumberfire()

    if args.fp:
        writeFantasyPros()

    if args.boris:
        writeBoris()

    if args.depth:
        writeDepthCharts()

    if args.kambi:
        writeKambi()

    if args.print:
        writeCsv(args.ppr, args.qbTd, args.booksOnly)

    js = """

    // Hide the bottom nightmare
    let divs = document.querySelectorAll("#draft > div");
    divs[divs.length-1].style.display = "none";

    // Expand Player List to bottom
    const playerListing = document.querySelector("#player-listing").parentElement.parentElement;
    let inset = playerListing.style.inset.split(" ");
    inset[2] = "0px";
    playerListing.style.inset = inset.join(" ");

    // Expand Draft Order to bottom
    document.querySelector("#draft-order").parentElement.parentElement.style.bottom = "0px";

    // Expand Chat to bottom
    document.querySelector("#chat").parentElement.parentElement.parentElement.style.bottom = "0px";

"""