
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




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="date")
    parser.add_argument("--action", action="store_true", help="Action Network")

    args = parser.parse_args()
