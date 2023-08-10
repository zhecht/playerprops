
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time


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
                prop = h2[0].innerText.toLowerCase().replace("regular season ", "").replace("rushing", "rush").replace("receiving", "rec").replace("passing", "pass").replace("yards", "yds").replace("touchdowns", "td").replace("total receptions", "rec").replaceAll(" ", "_");
                if (prop.indexOf("props") >= 0) {
                    continue;
                }
            } else if (h3.length) {
                player = h3[0].innerText.toLowerCase().split(" 2023")[0].replaceAll(".", "").replaceAll("'", "").replaceAll("-", " ").replaceAll(" jr", "").replaceAll(" ii", "");
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
    return name.replace("yards", "yds").replace("tds", "td").replace("receptions", "rec").replace("qb ints", "int").replace("ints", "int").replace(" ", "_")

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
            if prop not in ["pass_yds", "pass_td", "rec_yds", "rec_td", "rush_yds", "rush_td", "rec", "int"]:
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
   # call(["curl", "-k", url, "-o", outfile])
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="date")
    parser.add_argument("--dk", action="store_true", help="Draftkings")
    parser.add_argument("--nf", action="store_true", help="Numberfire")

    args = parser.parse_args()

    if args.dk:
        writeDK()

    if args.nf:
        writeNumberfire()
    