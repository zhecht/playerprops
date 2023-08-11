
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time

def writeYahoo():
    js = """

    const data = {};

    function loopScript() {
        const table = document.querySelector("table");
        const headers = ["pass_yd", "pass_td", "int", "rush_att", "rush_yd", "rush_td", "rec", "rec_yd", "rec_td", "tgt", "2pt", "fumble"];

        for (const tr of table.querySelector("tbody").querySelectorAll("tr")) {
            const player = tr.querySelectorAll("a")[2].innerText.toLowerCase().replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" iii", "").replaceAll(" ii", "");
            data[player] = {};
            let idx = 0;
            for (const td of tr.querySelectorAll("td:not(:nth-child(-n+11)):nth-child(n)")) {
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
                const over = li.querySelector('[role="button"]');
                const under = li.querySelectorAll('[role="button"]')[1].querySelectorAll("span")[1].innerText;
                const line = over.querySelector("span").innerText.toLowerCase().replaceAll(" ", "");
                const odds = over.querySelectorAll("span")[1].innerText;

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

    with open(f"static/draft/draftkings.json", "w") as fh:
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

    with open("static/draft/numberfire.json", "w") as fh:
        json.dump(data, fh, indent=4)

def writeNFL():
    url = "https://fantasy.nfl.com/research/projections#researchProjections=researchProjections%2C%2Fresearch%2Fprojections%253Fposition%253DO%2526sort%253DprojectedPts%2526statCategory%253DprojectedStats%2526statSeason%253D2023%2526statType%253DseasonProjectedStats%2Creplace"

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

    with open("static/draft/fantasypros.json", "w") as fh:
        json.dump(data, fh, indent=4)

def writeCsv():
    projections = {}

    books = ["draftkings", "fanduel", "fantasypros", "yahoo"]
    for book in books:
        with open(f"static/draft/{book}.json") as fh:
            projections[book] = json.load(fh).copy()

    for pos in ["qb", "rb", "wr/te"]:
        headers = []
        if pos == "qb":
            headers = ["pass_yd", "pass_td", "int", "rush_yd", "rush_td"]
        elif pos == "wr/te":
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
                j[hdr] = [projections["fantasypros"][player][hdr]]
                #j[hdr+"_fantasypros"] = projections["fantasypros"][hdr]

                for book in ["draftkings", "fanduel", "yahoo"]:
                    if hdr in projections[book]:
                        j[hdr].append(float(projections[book][player][hdr]))
                        #j[hdr+"_"+book] = projections[book][hdr]

            for hdr in j:
                if hdr == "player":
                    continue
                j[hdr] = round(sum(j[hdr]) / len(j[hdr]), 1)

            data.append(j)

        sortKey = "pass_yd"
        if pos == "wr/te":
            sortKey = "rec_yd"
        elif pos == "rb":
            sortKey = "rush_yd"
        output = "\t".join([h.upper() for h in data[0]])+"\n"
        for row in sorted(data, key=lambda k: k[sortKey], reverse=True):
            output += "\t".join([str(row[r]) for r in row]) + "\n"

        with open(f"static/draft/{pos.replace('/', '_')}.csv", "w") as fh:
            fh.write(output)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="date")
    parser.add_argument("--dk", action="store_true", help="Draftkings")
    parser.add_argument("--nf", action="store_true", help="Numberfire")
    parser.add_argument("--fp", action="store_true", help="FantasyPros")
    parser.add_argument("-p", "--print", action="store_true", help="Print CSVs")

    args = parser.parse_args()

    if args.dk:
        writeDK()

    if args.nf:
        writeNumberfire()

    if args.fp:
        writeFantasyPros()

    if args.print:
        writeCsv()