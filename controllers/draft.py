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

def writeYahooPitchers():
    url = "https://baseball.fantasysports.yahoo.com/b1/76488/players?&sort=PTS&sdir=1&status=A&pos=P&stat1=S_S_2024&jsenabled=1"

    js = """

    const data = {};

    function loopScript() {
        const table = document.querySelector("table");
        const headers = ["ip", "w", "l", "sho", "sv", "er", "bb", "k", "nh", "pg", "qs", "bsv"];

        let start = 0;
        for (const th of table.querySelector("thead").querySelectorAll("tr")[1].querySelectorAll("th")) {
            if (th.innerText === "IP") {
                break;
            }
            start += 1;
        }

        for (const tr of table.querySelector("tbody").querySelectorAll("tr")) {
            const player = tr.querySelectorAll("a")[1].innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
            data[player] = {};
            let idx = 0;
            for (const td of tr.querySelectorAll("td:not(:nth-child(-n+"+start+")):nth-child(n)")) {
                if (headers[idx] && headers[idx] != "pg") {
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

    with open(f"{prefix}static/nflfutures/fpros.json", "w") as fh:
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
    for col in rows[5].split(","):
        headers.append(col.lower())

    data = {}
    for row in rows[6:]:
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

    #books = ["fantasypros", "draftkings", "fanduel", "caesars", "bet365", "kambi", "mgm", "yahoo"]
    books = ["fpros", "draftkings", "fanduel", "cz", "bet365", "kambi", "mgm"]
    for book in books:
        with open(f"{prefix}static/nflfutures/{book}.json") as fh:
            projections[book] = json.load(fh).copy()

    allHeaders = ["pass_yd", "pass_td", "int", "rush_att", "rush_yd", "rush_td", "rec", "rec_yd", "rec_td"]
    allData = []
    allDataBooks = []
    for pos in ["qb", "rb", "wr", "te"]:
        headers = []
        if pos == "qb":
            headers = ["pass_yd", "pass_td", "int", "rush_yd", "rush_td"]
        elif pos == "wr" or pos == "te":
            headers = ["rec", "rec_yd", "rec_td"]
        elif pos == "rb":
            headers = ["rush_att", "rush_yd", "rush_td", "rec", "rec_yd", "rec_td"]

        data = []
        for player in projections["fpros"]:
            if projections["fpros"][player]["pos"] not in pos:
                continue
            j = {
                "player": player.title()
            }
            booksJ = j.copy()
            for hdr in headers:
                booksJ[hdr] = []
                if booksOnly:
                    j[hdr] = []
                else:
                    j[hdr] = [projections["fpros"][player][hdr]]
                j[hdr+"_book_fpros"] = projections["fpros"][player][hdr]
                j[hdr+"_book_odds_fpros"] = projections["fpros"][player][hdr]

                for book in ["draftkings", "fanduel", "cz", "bet365", "kambi", "mgm"]:
                    if hdr in projections[book] and player in projections[book][hdr]:
                        val = list(projections[book][hdr][player].keys())[0]

                        if book != "yahoo":
                            booksJ[hdr].append(float(val))
                        if not booksOnly or book != "yahoo":
                            j[hdr].append(float(val))
                        j[hdr+"_book_"+book] = val
                        j[hdr+"_book_odds_"+book] = f"o{val} {projections[book][hdr][player][val]}"
                        booksJ[hdr+"_book_"+book] = val
                        booksJ[hdr+"_book_odds_"+book] = projections[book][hdr][player]

            for hdr in j:
                if hdr == "player" or "book" in hdr:
                    continue
                if not len(booksJ[hdr]):
                    booksJ[hdr] = 0
                else:
                    booksJ[hdr] = round(sum(booksJ[hdr]) / len(booksJ[hdr]), 1)

                if not len(j[hdr]):
                    j[hdr] = 0
                else:
                    j[hdr] = round(sum(j[hdr]) / len(j[hdr]), 1)

            calculateFantasyPoints(j, ppr, qbTd)
            calculateFantasyPoints(booksJ, ppr, qbTd)
            data.append(j)
            jj = j.copy()
            jj["pos"] = pos
            booksJ["pos"] = pos
            allData.append(jj)
            allDataBooks.append(booksJ)

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

        #books = ["draftkings", "fanduel", "cz", "bet365", "kambi", "mgm", "fpros", "yahoo"]
        books = ["draftkings", "fanduel", "cz", "bet365", "kambi", "mgm", "fpros", "yahoo"]
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
            player = row["player"]
            output += f"{player}\n"
            for prop in headers:
                if projections["fpros"][player.lower()]["pos"] == "qb" and player.lower() in ecrData:
                    if prop == "pass_yd":
                        output += f"{row['points']} FPTS"
                    elif prop == "pass_td":
                        output += f"{ecrData[player.lower()]['adp']} ADP"
                elif projections["fpros"][player.lower()]["pos"] == "rb" and player.lower() in ecrData:
                    if prop == "rush_att":
                        output += f"{row['points']} FPTS"
                    elif prop == "rush_yd":
                        output += f"{ecrData[player.lower()]['adp']} ADP"
                elif projections["fpros"][player.lower()]["pos"] in ["wr", "te"] and player.lower() in ecrData:
                    if prop == "rec":
                        output += f"{row['points']} FPTS"
                    elif prop == "rec_yd":
                        output += f"{ecrData[player.lower()]['adp']} ADP"
                output += f"\t{prop}\t{row[prop]}\t"
                a = []
                for book in books:
                    try:
                        a.append(row[prop+"_book_odds_"+book])
                    except:
                        a.append("-")
                output += "\t".join([str(x) for x in a]) + "\n"
            output += "\n"
        with open(f"{prefix}static/draft/{pos.replace('/', '_')}_all.csv", "w") as fh:
            fh.write(output)

    h = ["Player", "ECR / ADP"]
    h.extend([x.upper() for x in allHeaders])
    h.append("Points")
    output = "\t".join(h)+"\n"
    for row in sorted(allData, key=lambda k: k["points"], reverse=True):
        a = []
        for hdr in h:
            if hdr.lower() in row:
                a.append(str(row[hdr.lower()]))
            elif "ECR" in hdr and row["player"].lower() in ecrData:
                ecr = ecrData[row["player"].lower()]["ecr"]
                adp = ecrData[row["player"].lower()]["adp"]
                a.append(f"{ecr} / {adp}")
            else:
                a.append("-")
        output += "\t".join(a)+"\n"

    with open(f"{prefix}static/draft/all.csv", "w") as fh:
        fh.write(output)

    with open(f"{prefix}static/draft/all.json", "w") as fh:
        json.dump(allData, fh, indent=4)

    with open(f"{prefix}static/draft/allBooks.json", "w") as fh:
        json.dump(allDataBooks, fh, indent=4)

@draft_blueprint.route('/getProjections')
def projections_route():
    books = request.args.get("books")

    with open(f"{prefix}static/draft/all.json") as fh:
        res = json.load(fh)

    if books != "None":
        with open(f"{prefix}static/draft/allBooks.json") as fh:
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
    books = request.args.get("books")
    return render_template("draft.html", pos="all", books=books)

def calcPoints(j, lastYear="", newModel=False):
    val = 0
    if newModel:
        val += int(j.get("ip"+lastYear, 0))*1.5
        #val += (j.get("ip", 0) % 10) * 10
        val += (j.get("w"+lastYear, 0)*3)
        val += (j.get("l"+lastYear, 0)*-1)
    else:
        val += int(j.get("ip"+lastYear, 0))
        #val += (j.get("ip", 0) % 10) * 10
        val += (j.get("w"+lastYear, 0)*7.5)
        val += (j.get("l"+lastYear, 0)*-3)
    val += (j.get("sho"+lastYear, 0)*3)
    val += (j.get("sv"+lastYear, 0)*6)
    val += (j.get("er"+lastYear, 0)*-1)
    val += (j.get("bb"+lastYear, 0)*-0.25)
    val += (j.get("k"+lastYear, 0))
    val += (j.get("qs"+lastYear, 0)*4)
    val += (j.get("bsv"+lastYear, 0)*-2)
    return val

@draft_blueprint.route('/getPitchers')
def pitchers_route():
    with open("julian.json") as fh:
        data = json.load(fh)

    csv = []
    hdrs = ["player","ip", "w", "l", "sho", "sv", "er", "bb", "k", "nh", "qs", "bsv", "war", "points", "new_points"]
    csv.append(",".join(hdrs))

    for player in data:
        output = [player]
        j = {}
        for hdr in hdrs[1:-2]:
            if hdr in data[player]["lyr"]:
                j[hdr] = data[player]["lyr"][hdr]
                output.append(str(j[hdr]))
            else:
                output.append("0")

        output.append(str(calcPoints(j)))
        output.append(str(calcPoints(j, newModel=True)))

        csv.append(",".join(output))

    with open("julian.csv", "w") as fh:
        fh.write("\n".join(csv))

    res = []
    for player in data:
        j = {"player": player.title()}
        for hdr in data[player]["szn"]:
            j[hdr] = data[player]["szn"][hdr]

        for hdr in data[player]["lyr"]:
            j[hdr+"_lyr"] = data[player]["lyr"][hdr]

        if "war" not in j:
            j["war"] = 0

        if "war_lyr" not in j:
            j["war_lyr"] = 0

        j["points"] = calcPoints(j)
        j["points_lyr"] = calcPoints(j, lastYear="_lyr")

        j["pointsNewModel"] = calcPoints(j, newModel=True)
        j["points_lyrNewModel"] = calcPoints(j, lastYear="_lyr", newModel=True)

        res.append(j)

    for idx, row in enumerate(sorted(res, key=lambda kv: kv["points"], reverse=True)):
        row["pointsRank"] = idx+1

    for idx, row in enumerate(sorted(res, key=lambda kv: kv["points_lyr"], reverse=True)):
        row["pointsRank_lyr"] = idx+1

    for idx, row in enumerate(sorted(res, key=lambda kv: kv["pointsNewModel"], reverse=True)):
        row["pointsRankNewModel"] = idx+1

    for idx, row in enumerate(sorted(res, key=lambda kv: kv["points_lyrNewModel"], reverse=True)):
        row["pointsRankNewModel_lyr"] = idx+1

    for idx, row in enumerate(sorted(res, key=lambda kv: kv["war"], reverse=True)):
        row["warRank"] = idx+1

    for idx, row in enumerate(sorted(res, key=lambda kv: kv["war_lyr"], reverse=True)):
        row["warRank_lyr"] = idx+1

    return jsonify(res)

@draft_blueprint.route('/julian')
def julian_route():
    return render_template("julian.html")

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
    parser.add_argument("-u", "--update", action="store_true", help="Update")
    parser.add_argument("--ppr", help="PPR", type=float)
    parser.add_argument("--qbTd", help="PPR", type=int)

    args = parser.parse_args()

    if args.update:
        writeECR()
        writeADP()
        writeBoris()
        writeDepthCharts()
        writeFantasyPros()

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

    if args.print:
        writeCsv(args.ppr, args.qbTd, args.booksOnly)

    js = """

    /* Hide the bottom nightmare */
    let divs = document.querySelectorAll("#draft > div");
    divs[divs.length-1].style.display = "none";

    /* Expand Player List to bottom */
    const playerListing = document.querySelector("#player-listing").parentElement.parentElement;
    let inset = playerListing.style.inset.split(" ");
    inset[2] = "0px";
    playerListing.style.inset = inset.join(" ");

    /* Expand Draft Order to bottom */
    document.querySelector("#draft-order").parentElement.parentElement.style.bottom = "0px";

    /* Expand Chat to bottom */
    document.querySelector("#chat").parentElement.parentElement.parentElement.style.bottom = "0px";

"""