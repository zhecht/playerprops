#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime
from datetime import timedelta

from itertools import zip_longest
import argparse
import time
import glob
import json
import math
import operator
import os
import subprocess
import re
import csv
import unicodedata

mlbprops_blueprint = Blueprint('mlbprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def convertDKTeam(team):
	if team == "cws":
		return "chw"
	elif team in ["was", "wsn"]:
		return "wsh"
	elif team in ["sfg", "sdp", "kcr", "tbr"]:
		return team[:2]
	elif team == "az":
		return "ari"
	return team

def addNumSuffix(val):
	if not val:
		return "-"
	a = val % 10;
	b = val % 100;
	if val == 0:
		return ""
	if a == 1 and b != 11:
		return f"{val}st"
	elif a == 2 and b != 12:
		return f"{val}nd"
	elif a == 3 and b != 13:
		return f"{val}rd"
	else:
		return f"{val}th"

def convertDKProp(mainCat, prop):
	prop = prop.replace(" o/u", "")
	if prop == "home runs":
		return "hr"
	elif prop == "total bases":
		return "tb"
	elif prop in ["hits"]:
		return "h"
	elif prop == "hits allowed":
		return "h_allowed"
	elif prop == "rbis":
		return "rbi"
	elif prop == "runs scored":
		return "r"
	elif prop == "earned runs allowed":
		return "er"
	elif prop == "stolen bases":
		return "sb"
	elif prop == "outs recorded":
		return "outs"
	elif prop == "hits + runs + rbis":
		return "h+r+rbi"
	elif prop == "strikeouts" or prop == "strikeouts thrown":
		if mainCat == "batter":
			return "so"
		return "k"
	elif prop == "walks" or prop == "walks allowed":
		if mainCat == "batter":
			return "bb"
		return "bb_allowed"
	elif prop == "singles":
		return "1b"
	elif prop == "doubles":
		return "2b"
	elif prop == "to record a win":
		return "w"
	
	return "_".join(prop.split(" "))

def writeProps(date, propArg):

	props = {}
	if os.path.exists(f"{prefix}static/mlbprops/dates/{date}.json"):
		with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
			props = json.load(fh)

	mainCats = {
		"batter": 743,
		"pitcher": 1031 
	}

	for mainCat in mainCats:
		time.sleep(0.4)
		url = f"https://sportsbook-nash-usmi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/84240/categories/{mainCats[mainCat]}?format=json"
		outfile = "outmlb2"
		cookie = "-H 'Cookie: hgg=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2aWQiOiIxODU4ODA5NTUwIiwiZGtzLTYwIjoiMjg1IiwiZGtlLTEyNiI6IjM3NCIsImRrcy0xNzkiOiI1NjkiLCJka2UtMjA0IjoiNzA5IiwiZGtlLTI4OCI6IjExMjgiLCJka2UtMzE4IjoiMTI2MSIsImRrZS0zNDUiOiIxMzUzIiwiZGtlLTM0NiI6IjEzNTYiLCJka2UtNDI5IjoiMTcwNSIsImRrZS03MDAiOiIyOTkyIiwiZGtlLTczOSI6IjMxNDAiLCJka2UtNzU3IjoiMzIxMiIsImRraC03NjgiOiJxU2NDRWNxaSIsImRrZS03NjgiOiIwIiwiZGtlLTgwNiI6IjM0MjYiLCJka2UtODA3IjoiMzQzNyIsImRrZS04MjQiOiIzNTExIiwiZGtlLTgyNSI6IjM1MTQiLCJka3MtODM0IjoiMzU1NyIsImRrZS04MzYiOiIzNTcwIiwiZGtoLTg5NSI6IjhlU3ZaRG8wIiwiZGtlLTg5NSI6IjAiLCJka2UtOTAzIjoiMzg0OCIsImRrZS05MTciOiIzOTEzIiwiZGtlLTk0NyI6IjQwNDIiLCJka2UtOTc2IjoiNDE3MSIsImRrcy0xMTcyIjoiNDk2NCIsImRrcy0xMTc0IjoiNDk3MCIsImRrcy0xMjU1IjoiNTMyNiIsImRrcy0xMjU5IjoiNTMzOSIsImRrZS0xMjc3IjoiNTQxMSIsImRrZS0xMzI4IjoiNTY1MyIsImRraC0xNDYxIjoiTjZYQmZ6S1EiLCJka3MtMTQ2MSI6IjAiLCJka2UtMTU2MSI6IjY3MzMiLCJka2UtMTY1MyI6IjcxMzEiLCJka2UtMTY1NiI6IjcxNTEiLCJka2UtMTY4NiI6IjcyNzEiLCJka2UtMTcwOSI6IjczODMiLCJka3MtMTcxMSI6IjczOTUiLCJka2UtMTc0MCI6Ijc1MjciLCJka2UtMTc1NCI6Ijc2MDUiLCJka3MtMTc1NiI6Ijc2MTkiLCJka3MtMTc1OSI6Ijc2MzYiLCJka2UtMTc2MCI6Ijc2NDkiLCJka2UtMTc2NiI6Ijc2NzUiLCJka2gtMTc3NCI6IjJTY3BrTWF1IiwiZGtlLTE3NzQiOiIwIiwiZGtlLTE3NzAiOiI3NjkyIiwiZGtlLTE3ODAiOiI3NzMxIiwiZGtlLTE2ODkiOiI3Mjg3IiwiZGtlLTE2OTUiOiI3MzI5IiwiZGtlLTE3OTQiOiI3ODAxIiwiZGtlLTE4MDEiOiI3ODM4IiwiZGtoLTE4MDUiOiJPR2tibGtIeCIsImRrZS0xODA1IjoiMCIsImRrcy0xODE0IjoiNzkwMSIsImRraC0xNjQxIjoiUjBrX2xta0ciLCJka2UtMTY0MSI6IjAiLCJka2UtMTgyOCI6Ijc5NTYiLCJka2gtMTgzMiI6ImFfdEFzODZmIiwiZGtlLTE4MzIiOiIwIiwiZGtzLTE4NDciOiI4MDU0IiwiZGtzLTE3ODYiOiI3NzU4IiwiZGtlLTE4NTEiOiI4MDk3IiwiZGtlLTE4NTgiOiI4MTQ3IiwiZGtlLTE4NjEiOiI4MTU3IiwiZGtlLTE4NjAiOiI4MTUyIiwiZGtlLTE4NjgiOiI4MTg4IiwiZGtoLTE4NzUiOiJZRFJaX3NoSiIsImRrcy0xODc1IjoiMCIsImRrcy0xODc2IjoiODIxMSIsImRraC0xODc5IjoidmI5WWl6bE4iLCJka2UtMTg3OSI6IjAiLCJka2UtMTg0MSI6IjgwMjQiLCJka3MtMTg4MiI6IjgyMzkiLCJka2UtMTg4MSI6IjgyMzYiLCJka2UtMTg4MyI6IjgyNDMiLCJka2UtMTg4MCI6IjgyMzIiLCJka2UtMTg4NyI6IjgyNjQiLCJka2UtMTg5MCI6IjgyNzYiLCJka2UtMTkwMSI6IjgzMjYiLCJka2UtMTg5NSI6IjgzMDAiLCJka2gtMTg2NCI6IlNWbjFNRjc5IiwiZGtlLTE4NjQiOiIwIiwibmJmIjoxNzIyNDQyMjc0LCJleHAiOjE3MjI0NDI1NzQsImlhdCI6MTcyMjQ0MjI3NCwiaXNzIjoiZGsifQ.jA0OxjKzxkyuAktWmqFbJHkI6SWik-T-DyZuLjL9ZKM; STE=\"2024-07-31T16:43:12.166175Z\"; STIDN=eyJDIjoxMjIzNTQ4NTIzLCJTIjo3MTU0NjgxMTM5NCwiU1MiOjc1Mjc3OTAxMDAyLCJWIjoxODU4ODA5NTUwLCJMIjoxLCJFIjoiMjAyNC0wNy0zMVQxNjo0MToxNC42ODc5Mzk4WiIsIlNFIjoiVVMtREsiLCJVQSI6IngxcVNUYXJVNVFRRlo3TDNxcUlCbWpxWFozazhKVmt2OGFvaCttT1ZpWFE9IiwiREsiOiIzMTQyYjRkMy0yNjU2LTRhNDMtYTBjNi00MTEyM2Y5OTEyNmUiLCJESSI6IjEzNTBmMGM0LWQ3MDItNDUwZC1hOWVmLTJlZjRjZjcxOTY3NyIsIkREIjo0NDg3NTQ0MDk4OH0=; STH=3a3368e54afc8e4c0a5c91094077f5cd1ce31d692aaaf5432b67972b5c3eb6fc; _abck=56D0C7A07377CFD1419CD432549CD1DB~0~YAAQJdbOF6Bzr+SQAQAAsmCPCQykOCRLV67pZ3Dd/613rD8UDsL5x/r+Q6G6jXCECjlRwzW7ESOMYaoy0fhStB3jiEPLialxs/UD9kkWAWPhuOq/RRxzYkX+QY0wZ/Uf8WSSap57OIQdRC3k3jlI6z2G8PKs4IyyQ/bRZfS2Wo6yO0x/icRKUAUeESKrgv6XrNaZCr14SjDVxBBt3Qk4aqJPKbWIbaj+1PewAcP+y/bFEVCmbcrAruJ4TiyqMTEHbRtM9y2O0WsTg79IZu52bpOI2jFjEUXZNRlz2WVhxbApaKY09QQbbZ3euFMffJ25/bXgiFpt7YFwfYh1v+4jrIvbwBwoCDiHn+xy17v6CXq5hIEyO4Bra6QT1sDzil+lQZPgqrPBE0xwoHxSWnhVr60EK1X5IVfypMHUcTvLKFcEP2eqwSZ67Luc/ompWuxooaOVNYrgvH/Vvs5UbyVOEsDcAXoyGt0BW3ZVMVPHXS/30dP3Rw==~-1~-1~1722445877; PRV=3P=0&V=1858809550&E=1720639388; ss-pid=4CNl0TGg6ki1ygGONs5g; ab.storage.deviceId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%22fe7382ec-2564-85bf-d7c4-3eea92cb7c3e%22%2C%22c%22%3A1709950180242%2C%22l%22%3A1709950180242%7D; ab.storage.userId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%2228afffab-27db-4805-85ca-bc8af84ecb98%22%2C%22c%22%3A1712278087074%2C%22l%22%3A1712278087074%7D; ab.storage.sessionId.b543cb99-2762-451f-9b3e-91b2b1538a42=%7B%22g%22%3A%223eff9525-6179-dc9c-ce88-9e51fca24c58%22%2C%22e%22%3A1722444192818%2C%22c%22%3A1722442278923%2C%22l%22%3A1722442392818%7D; _gcl_au=1.1.386764008.1720096930; _ga_QG8WHJSQMJ=GS1.1.1722442278.7.1.1722442393.19.0.0; _ga=GA1.2.2079166597.1720096930; _dpm_id.16f4=b3163c2a-8640-4fb7-8d66-2162123e163e.1720096930.7.1722442393.1722178863.1f3bf842-66c7-446c-95e3-d3d5049471a9; _tgpc=78b6db99-db5f-5ce5-848f-0d7e4938d8f2; _tglksd=eyJzIjoiYjRkNjE4MWYtMTJjZS01ZDJkLTgwNTYtZWQ2NzIxM2MzMzM2Iiwic3QiOjE3MjI0NDIyNzgyNzEsInNvZCI6IihkaXJlY3QpIiwic29kdCI6MTcyMTg3ODUxOTY5OCwic29kcyI6Im8iLCJzb2RzdCI6MTcyMTg3ODUxOTY5OH0=; _sp_srt_id.16f4=55c32e85-f32f-42ac-a0e8-b1e37c9d3bc6.1720096930.6.1722442279.1722178650.6d45df5a-aea8-4a66-a4ba-0ef841197d1d.cdc2d898-fa3f-4430-a4e4-b34e1909bb05...0; _scid=e6437688-491e-4800-b4b2-e46e81b2816c; _ga_M8T3LWXCC5=GS1.2.1722442279.7.1.1722442288.51.0.0; _svsid=9d0929120b67695ad6ee074ccfd583b7; _sctr=1%7C1722398400000; _hjSessionUser_2150570=eyJpZCI6ImNmMDA3YTA2LTFiNmMtNTFkYS05Y2M4LWNmNTAyY2RjMWM0ZCIsImNyZWF0ZWQiOjE3MjA1NTMwMDE4OTMsImV4aXN0aW5nIjp0cnVlfQ==; _csrf=ba945d1a-57c4-4b50-a4b2-1edea5014b72; ss-id=x8zwcqe0hExjZeHXAKPK; ak_bmsc=F8F9B7ED0366DC4EB63B2DD6D078134C~000000000000000000000000000000~YAAQJdbOF3hzr+SQAQAAp1uPCRjLBiubHwSBX74Dd/8hmIdve4Tnb++KpwPtaGp+NN2ZcEf+LtxC0PWwzhZQ1one2MxGFFw1J6BXg+qiFAoQ6+I3JExoHz4r+gqodWq7y5Iri7+3aBFQRDtn17JMd1PTEEuN8EckzKIidL3ggrEPS+h1qtof3aHJUdx/jkCUjkaN/phWSvohlUGscny8dJvRz76e3F20koI5UsjJ/rQV7dUn6HNw1b5H1tDeL7UR1mbBrCLz6YPDx4XCjybvteRQpyLGI0o9L6xhXqv12exVAbZ15vpuNJalhR6eB4/PVwCmfVniFcr/xc8hivkuBBMOj1lN7ADykNA60jFaIRAY2BD2yj27Aedr7ETAFnvac0L0ITfH20LkA2cFhGUxmzOJN0JQ6iTU7VGgk19FzV+oeUxNmMPX; bm_sz=D7ABF43D4A5671594F842F6C403AB281~YAAQJdbOF3lzr+SQAQAAp1uPCRgFgps3gN3zvxvZ+vbm5t9IRWYlb7as+myjQOyHzYhriG6n+oxyoRdQbE6wLz996sfM/6r99tfwOLP2K8ULgA2nXfOPvqk6BwofdTsUd7KP7EnKhcCjhADO18uKB/QvIJgyS3IFBROxP2XFzS15m/DrRbF7lQDRscWtVo8oOITxNTBlwg0g4fI3gzjG6A4uHYxjeCegxSrHFHGFr4KZXgOnsJhmZe0lqIRWUFcIKC/gfsDd+jfyUnprMso1Flsv9blGlvycOoWTHPdEQvUudpOZlZ3JYz9H5y+dU94wBD9ejxIlRKP26giQISjun829Kt7CuKxJXYAcSJeiomZFh5Abj+Mkv0wi6ZcRcmOVFt49eywPazFHpGM8DVcUkVEFMcpNCeiJ/CtC60U9SoJy+ermF1hTqiAq~3622209~4408134; bm_sv=6618DE86472CB31D7B7F16DAE6689651~YAAQJdbOF96Lr+SQAQAA4iSRCRjfwGUmEhVBbE3y/2VDAAvuPyI2gX7io7CQCPfcdMOnBnNhxHIKYt9PFr7Y1TADQHFUC9kqXu7Nbj9d1BrLlfi1rPbv/YKPqhqSTLkbNSWbeKhKM4HfOu7C+RLV383VzGeyDhc2zOuBKBVNivHMTF9njS3vK6RKeSPFCfxOJdDHgNlIYykf0Ke2WJvflHflTUykwWUaYIlqoB52Ixb9opHQVTptWjetGdYjuOO2S2ZPkw==~1; _dpm_ses.16f4=*; _tgidts=eyJzaCI6ImQ0MWQ4Y2Q5OGYwMGIyMDRlOTgwMDk5OGVjZjg0MjdlIiwiY2kiOiIxZDMxOGRlZC0yOWYwLTUzYjItYjFkNy0yMDlmODEwNDdlZGYiLCJzaSI6ImI0ZDYxODFmLTEyY2UtNWQyZC04MDU2LWVkNjcyMTNjMzMzNiJ9; _tguatd=eyJzYyI6IihkaXJlY3QpIn0=; _tgsid=eyJscGQiOiJ7XCJscHVcIjpcImh0dHBzOi8vc3BvcnRzYm9vay5kcmFmdGtpbmdzLmNvbSUyRmxlYWd1ZXMlMkZiYXNlYmFsbCUyRm1sYlwiLFwibHB0XCI6XCJNTEIlMjBCZXR0aW5nJTIwT2RkcyUyMCUyNiUyMExpbmVzJTIwJTdDJTIwRHJhZnRLaW5ncyUyMFNwb3J0c2Jvb2tcIixcImxwclwiOlwiXCJ9IiwicHMiOiJkOTY4OTkxNy03ZTAxLTQ2NTktYmUyOS1mZThlNmI4ODY3MzgiLCJwdmMiOiIxIiwic2MiOiJiNGQ2MTgxZi0xMmNlLTVkMmQtODA1Ni1lZDY3MjEzYzMzMzY6LTEiLCJlYyI6IjUiLCJwdiI6IjEiLCJ0aW0iOiJiNGQ2MTgxZi0xMmNlLTVkMmQtODA1Ni1lZDY3MjEzYzMzMzY6MTcyMjQ0MjI4MjA3NDotMSJ9; _sp_srt_ses.16f4=*; _gid=GA1.2.150403708.1722442279; _scid_r=e6437688-491e-4800-b4b2-e46e81b2816c; _uetsid=85e6d8504f5711efbe6337917e0e834a; _uetvid=d50156603a0211efbb275bc348d5d48b; _hjSession_2150570=eyJpZCI6ImQxMTAyZTZjLTkyYzItNGMwNy1hNzMzLTcxNDhiODBhOTI4MyIsImMiOjE3MjI0NDIyODE2NDUsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; _rdt_uuid=1720096930967.9d40f035-a394-4136-b9ce-2cf3bb298115'"
		os.system(f"curl {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' {cookie} -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		seen = {}
		for event in data["eventGroup"]["events"]:
			start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
			startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=5)
			if startDt.day != int(date[-2:]):
				continue
				pass
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
				continue

			if game in seen:
				game += " gm2"
			seen[game] = True
			if game not in props:
				props[game] = {}

			events[event["eventId"]] = game

		subCats = {}
		for catRow in data["eventGroup"]["offerCategories"]:
			if catRow["offerCategoryId"] != mainCats[mainCat]:
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["name"].startswith("1st") or cRow["name"].startswith("H2H"):
					continue
				#print(mainCat, cRow["name"])
				prop = convertDKProp(mainCat, cRow["name"].lower())
				subCats[prop] = cRow["subcategoryId"]

		for prop in subCats:
			if propArg and prop not in propArg.split(","):
				continue
			time.sleep(0.4)
			url = f"https://sportsbook-nash-usmi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/84240/categories/{mainCats[mainCat]}/subcategories/{subCats[prop]}?format=json"
			outfile = "outmlb2"
			#print(url)
			os.system(f"curl {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' {cookie} -o {outfile}")

			with open("outmlb2") as fh:
				data = json.load(fh)

			for catRow in data["eventGroup"]["offerCategories"]:
				if "offerSubcategoryDescriptors" not in catRow:
					continue
				for cRow in catRow["offerSubcategoryDescriptors"]:
					if "offerSubcategory" not in cRow:
						continue
					for offerRow in cRow["offerSubcategory"]["offers"]:
						for row in offerRow:
							try:
								game = events[row["eventId"]]
							except:
								continue
							
							if "participant" not in row["outcomes"][0]:
								continue
							player = strip_accents(row["outcomes"][0]["participant"]).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "").replace("kike", "enrique").split(" (")[0].strip()
							odds = ["+0","0"]
							try:
								line = row["outcomes"][0]["line"]
							except:
								line = 0
							for outcome in row["outcomes"]:
								if outcome["label"].lower() == "over" or (prop == "w" and outcome["label"].lower() == "yes"):
									odds[0] = outcome["oddsAmerican"]
								else:
									odds[1] = outcome["oddsAmerican"]

							if player not in props[game]:
								props[game][player] = {}
							if prop not in props[game][player]:
								props[game][player][prop] = {}
							props[game][player][prop] = {
								"line": line,
								"over": odds[0].replace("\u2212", "-"),
								"under": odds[1].replace("\u2212", "-")
							}

	with open(f"{prefix}static/mlbprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)


def writeCsvs(props):
	csvs = {}
	splitProps = {"full": []}
	headerList = ["NAME","OVER","POS","R/L","Batting #","B. AVG","TEAM","A/H","OPP","OPP RANK","OPP RANK LYR","PROP","LINE","LAST (old ➡️ new)","AVG","% OVER","L10 % OVER","CAREER % OVER","% OVER VS TEAM","VS TEAM","PITCHER","THROWS","VS PITCHER","UNDER"]
	headers = "\t".join(headerList)
	reddit = "|".join(headers.split("\t"))
	reddit += "\n"+"|".join([":--"]*len(headerList))

	for row in props:
		if row["prop"] not in splitProps:
			splitProps[row["prop"]] = []

		if row["overOdds"] == '-inf':
			continue

		splitProps[row["prop"]].append(row)
		splitProps["full"].append(row)

	for prop in splitProps:
		if prop in ["k", "outs", "win", "h_allowed", "bb_allowed", "er"]:
			csvs[prop] = "\t".join(["NAME","OVER","POS","R/L","TEAM","A/H","OPP","OPP RANK","OPP RANK LYR","PROP","LINE","LAST (old ➡️ new)","AVG","% OVER","L10 % OVER","CAREER % OVER","% OVER VS TEAM","VS TEAM","UNDER"])
		else:
			csvs[prop] = headers
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOver"], k["careerTotalOver"]), reverse=True)
		for row in rows:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			avg = row["avg"]
			if underOdds == '-inf':
				underOdds = 0
			if int(overOdds) > 0:
				overOdds = "'"+overOdds
			if int(underOdds) > 0:
				underOdds = "'"+underOdds
			#if avg >= row["line"]:
			#	avg = f"**{avg}**"

			if prop in ["k", "outs", "win", "h_allowed", "bb_allowed", "er"]:
				csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], overOdds, row["pos"], row["bats"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"].replace("'", ""), row["avg"], f"{row['totalOver']}%", f"{row['last10Over']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", underOdds]])
			else:
				csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], overOdds, row["pos"], row["bats"], row["battingNumber"], row["battingAvg"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"].replace("'", ""), row["avg"], f"{row['totalOver']}%", f"{row['last10Over']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", row["pitcher"], row["pitcherThrows"], row["againstPitcherStats"], underOdds]])

	# add full rows
	csvs["full"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		avg = row["avg"]
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		#if avg >= row["line"]:
		#	avg = f"**{avg}**"
		csvs["full"] += "\n" + "\t".join([str(x) for x in [row["player"], overOdds, row["pos"], row["bats"], row["battingNumber"], row["battingAvg"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), addNumSuffix(row["oppRankLastYear"]), row["prop"], row["line"], row["lastDisplay"].replace("'", ""), row["avg"], f"{row['totalOver']}%", f"{row['last10Over']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", row["pitcher"], row["pitcherThrows"], row["againstPitcherStats"], underOdds]])


	# add top 4 to reddit
	headerList = ["NAME","Batting #","B. AVG","TEAM","A/H","OPP","OPP RANK","PROP","LINE","LAST (old ➡️ new)","AVG","% OVER", "CAREER % OVER", "% OVER VS TEAM", "VS TEAM", "PITCHER", "VS PITCHER", "OVER","UNDER"]
	headers = "\t".join(headerList)
	reddit = "|".join(headers.split("\t"))
	reddit += "\n"+"|".join([":--"]*len(headerList))

	for prop in ["h", "h+r+rbi", "hr", "tb"]:
		if prop in splitProps:
			rows = sorted(splitProps[prop], key=lambda k: (k["totalOver"], k["careerTotalOver"]), reverse=True)
			for row in [r for r in rows if r["gamesPlayed"] >= 7 and int(str(r["battingNumber"]).replace('-', '10')) <= 6][:3]:
				overOdds = row["overOdds"]
				underOdds = row["underOdds"]
				avg = row["lastYearAvg"]
				reddit += "\n" + "|".join([str(x) for x in [row["player"], row["battingNumber"], row["battingAvg"], row["team"], row["awayHome"], row["opponent"], addNumSuffix(row["oppRank"]), row["prop"], row["line"], row["lastDisplay"].replace("'", ""), row["avg"], f"{row['totalOver']}%", f"{row['careerTotalOver']}%", f"{row['againstTeamTotalOver']}%", f"{row['againstTeamStats']}", row["pitcher"], row["againstPitcherStats"], overOdds, underOdds]])
			reddit += "\n"+"|".join(["-"]*len(headerList))

	with open(f"{prefix}static/mlbprops/csvs/reddit", "w") as fh:
		fh.write(reddit)

	for prop in csvs:
		with open(f"{prefix}static/mlbprops/csvs/{prop}.csv", "w") as fh:
			fh.write(csvs[prop])

def writeStaticProps(date=None):
	props = getPropData(date)

	writeCsvs(props)

	with open(f"{prefix}static/betting/mlb.json", "w") as fh:
		json.dump(props, fh, indent=4)
	for prop in ["h", "hr", "bb_allowed", "k", "outs", "wins", "h_allowed", "bb", "er"]:
		filteredProps = [p for p in props if p["prop"] == prop]
		with open(f"{prefix}static/betting/mlb_{prop}.json", "w") as fh:
			json.dump(filteredProps, fh, indent=4)

def convertRankingsProp(prop):
	if prop in ["r"]:
		return "er"
	elif prop == "rbi":
		return "opp_rbi"
	elif prop == "er":
		return "r"
	elif prop == "sb":
		return "opp_sb"
	elif prop == "tb":
		return "opp_tb"
	elif prop == "k":
		return "so"
	elif prop == "bb":
		return "bb_allowed"
	elif prop == "bb_allowed":
		return "bb"
	elif prop == "hr_allowed":
		return "hr"
	elif prop == "hr":
		return "hr_allowed"
	elif prop == "h_allowed":
		return "h"
	elif prop == "h":
		return "h_allowed"
	elif prop == "h+r+rbi_allowed":
		return "h+r+rbi"
	elif prop == "h+r+rbi":
		return "h+r+rbi_allowed"
	return prop

def sumStat(header, target, source):
	if header not in target:
		target[header] = 0

	if header == "ip":
		ip = target["ip"]+source["ip"]
		remainder = int(str(round(ip, 1)).split(".")[-1])

		if remainder >= 3:
			ip += remainder // 3
			ip = int(ip) + (remainder%3)*0.1
		target["ip"] = ip
	else:
		try:
			target[header] += source[header]
		except:
			pass

def getPropData(date = None, playersArg = [], teamsArg = "", pitchers=False, lineArg=""):
	
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/baseballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/baseballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/baseballreference/expected.json") as fh:
		expected = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerIds.json") as fh:
		playerIds = json.load(fh)
	with open(f"{prefix}static/baseballreference/expectedHR.json") as fh:
		expectedHR = json.load(fh)
	with open(f"{prefix}static/baseballreference/parkfactors.json") as fh:
		parkFactors = json.load(fh)
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/baseballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerRankings.json") as fh:
		playerRankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)
	try:
		with open(f"{prefix}static/mlbprops/projections/{date}.json") as fh:
			projections = json.load(fh)
	except:
		projections = {}
	with open(f"{prefix}static/baseballreference/numberfireProjections.json") as fh:
		numberfireProjections = json.load(fh)
	with open(f"{prefix}static/baseballreference/bvp.json") as fh:
		bvp = json.load(fh)
	with open(f"{prefix}static/baseballreference/BPPlayerProps.json") as fh:
		ballparkPalProps = json.load(fh)
	with open(f"{prefix}static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)
	with open(f"{prefix}static/baseballreference/advancedLastYear.json") as fh:
		advancedLastYear = json.load(fh)
	with open(f"{prefix}static/baseballreference/sortedRankings.json") as fh:
		sortedRankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)
	with open(f"{prefix}static/baseballreference/leftRightSplits.json") as fh:
		leftRightSplits = json.load(fh)
	with open(f"{prefix}static/baseballreference/pitching.json") as fh:
		pitching = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerHRFactors.json") as fh:
		playerHRFactors = json.load(fh)
	with open(f"{prefix}static/baseballreference/statsVsTeam.json") as fh:
		statsVsTeam = json.load(fh)
	with open(f"{prefix}static/baseballreference/splits.json") as fh:
		splits = json.load(fh)
	with open(f"{prefix}static/baseballreference/battingPitches.json") as fh:
		battingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/pitchingPitches.json") as fh:
		pitchingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerBattingPitches.json") as fh:
		playerBattingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/playerPitchingPitches.json") as fh:
		playerPitchingPitches = json.load(fh)
	with open(f"{prefix}static/baseballreference/statsVsTeamCurrYear.json") as fh:
		statsVsTeamCurrYear = json.load(fh)
	with open(f"{prefix}static/baseballreference/statsVsTeamLastYear.json") as fh:
		statsVsTeamLastYear = json.load(fh)
	with open(f"{prefix}static/baseballreference/trades.json") as fh:
		trades = json.load(fh)
	with open(f"{prefix}static/mlbprops/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/mlbprops/stats/2023.json") as fh:
		lastYearStats = json.load(fh)
	yearStats = {}
	for yr in os.listdir(f"{prefix}static/mlbprops/stats/"):
		with open(f"{prefix}static/mlbprops/stats/{yr}") as fh:
			s = json.load(fh)
		yearStats[yr[:4]] = s

	props = []
	for game in propData:
		awayTeam, homeTeam = map(str, game.split(" @ "))

		for player in propData[game]:

			if player in roster[awayTeam]:
				team = awayTeam
				opp = homeTeam
			else:
				team = homeTeam
				opp = awayTeam

			try:
				pos = roster[team][player]
			except:
				print(game, team, player)
				continue

			try:
				playerId = playerIds[team][player]
			except:
				playerId = 0

			if teamsArg and team not in teamsArg:
				continue

			for propName in propData[game][player]:
				prop = propName
				convertedProp = prop
				if "P" in pos:
					convertedProp = prop.replace("_allowed", "")
				lastYearAvg = lastYearTotalOver = gamesPlayed = battingNumber = 0
				hit = False
				pitcher = pitcherThrows = awayHomeSplits = ""

				bats = leftOrRight[team].get(player, "")
				hip = bbip = hrip = hpg = kip = 0
				try:
					pitcher = lineups[opp]["pitching"]
					pitcherThrows = leftOrRight[opp][pitcher]
					hip = round(stats[opp][pitcher]["h_allowed"] / stats[opp][pitcher]["ip"], 2)
					hpg = round(stats[opp][pitcher]["h_allowed"] / stats[opp][pitcher]["gamesPlayed"], 1)

					hip = round(averages[opp][pitcher]["tot"]["h"] / averages[opp][pitcher]["tot"]["ip"], 2)
					hrip = round(averages[opp][pitcher]["tot"]["hr"] / averages[opp][pitcher]["tot"]["ip"], 2)
					kip = round(averages[opp][pitcher]["tot"]["k"] / averages[opp][pitcher]["tot"]["ip"], 2)
					bbip = round(averages[opp][pitcher]["tot"]["bb"] / averages[opp][pitcher]["tot"]["ip"], 2)
				except:
					pass


				line = propData[game][player][propName]["line"]
				if line == "-":
					line = 0

				if lineArg:
					line = float(lineArg)

				if prop == "w":
					line = 0.5

				# projection
				projIP = 0
				try:
					proj = round(projections[team][player][prop], 2)

					if "P" in pos:
						projIP = round(projections[team][player]["ip"], 2)
				except:
					proj = 0

				#numberfire projection
				numberfireProj = numberfireProjIP = 0
				try:
					numberfireProj = round(numberfireProjections[team][player].get(prop, 0), 2)
					if "P" in pos:
						numberfireProjIP = round(numberfireProjections[team][player]["ip"], 2)
					elif prop == "so":
						numberfireProj = round(numberfireProjections[team][player].get("k", 0), 2)
				except:
					pass

				# pitcher Projection
				try:
					pitcherProj = round(projections[opp][pitcher]["h_allowed"], 2)
				except:
					pitcherProj = 0

				kPerBB = pitchesPerPlate = "-"

				# advanced
				era = savantId = ""
				try:
					p = pitcher
					if "P" in pos and ("ohtani" not in player or prop in ["w", "k", "h_allowed", "bb_allowed", "er"]):
						p = player

					advancedPitcher = advanced[p].copy()
					advancedPitcherLastYear = advancedLastYear[p].copy()
					era = advancedPitcher["p_era"]
					savantId = advancedPitcher["player_id"]
				except:
					advancedPitcher = {}
					advancedPitcherLastYear = {}

				# pitches
				try:
					if "P" in pos and ("ohtani" not in player or prop in ["w", "k", "h_allowed", "bb_allowed", "er"]):
						playerPitches = playerPitchingPitches[team][player].copy()
					else:
						playerPitches = playerPitchingPitches[opp][pitcher].copy()
				except:
					playerPitches = {}

				try:
					oppTeamBattingPitches = battingPitches[opp].copy()
				except:
					oppTeamBattingPitches = {}

				if "P" in pos and ("ohtani" not in player or prop in ["w", "k", "h_allowed", "bb_allowed", "er"]):
					try:
						hip = round(averages[team][player]["tot"]["h"] / averages[team][player]["tot"]["ip"], 2)
						bbip = round(averages[team][player]["tot"]["bb"] / averages[team][player]["tot"]["ip"], 2)
					except:
						pass

					# player rankings
					try:
						kPerBB = playerRankings[team][player]["k/bb"]["val"]
					except:
						pass

					try:
						pitchesPerPlate = playerPitchingPitches[team][player]["pit/pa"]
						strikePercent = playerPitchingPitches[team][player]["str%"]
					except:
						pass
				try:
					battingNumber = lineups[team]["batting"].index(player)+1
				except:
					battingNumber = "-"

				overOdds = propData[game][player][propName]["over"]
				underOdds = propData[game][player][propName]["under"]

				tradeFrom = tradeTo = ""
				if player in trades:
					tradeFrom = trades[player]["from"]
					tradeTo = trades[player]["to"]

				bp = bpDiff = bpOdds = 0

				lastYrGamesPlayed = 0
				prevMatchup = []
				lastTotalGames = careerTotalGames = careerTotalOver = careerAvg = againstTeamTotalOver = 0
				lastYrAwayHomeSplits = [[], []]
				lastYrLast20 = []
				againstTeamLastYearStats = {"ab": 0, "h": 0, "hr": 0, "rbi": 0, "bb": 0, "so": 0}
				againstTeamStats = {}
				if team in statsVsTeam and player in statsVsTeam[team]:
					againstTeamStats = dict(statsVsTeam[team][player].get(opp, {}))
					for hdr in againstTeamStats:
						if type(againstTeamStats[hdr]) is dict:
							againstTeamStats[hdr] = dict(againstTeamStats[hdr])

				teams = [team]
				if tradeFrom:
					teams.append(tradeFrom)
				for t in teams:
					if t in statsVsTeamCurrYear and opp in statsVsTeamCurrYear[t] and player in statsVsTeamCurrYear[t][opp]:
						for hdr in statsVsTeamCurrYear[t][opp][player]:
							if hdr not in againstTeamStats:
								againstTeamStats[hdr] = statsVsTeamCurrYear[t][opp][player][hdr]
							elif hdr.endswith("Overs"):
								for over in statsVsTeamCurrYear[t][opp][player][hdr]:
									if over not in againstTeamStats[hdr]:
										againstTeamStats[hdr][over] = 0
									againstTeamStats[hdr][over] += statsVsTeamCurrYear[t][opp][player][hdr][over]
							else:
								sumStat(hdr, againstTeamStats, statsVsTeamCurrYear[t][opp][player])
				try:
					overs = againstTeamStats[convertedProp+"Overs"][str(math.ceil(line))]
				except:
					overs = 0

				played = againstTeamStats.get("gamesPlayed", 0)
				if played:
					againstTeamTotalOver = round(overs * 100 / played)

				if team in statsVsTeamLastYear and player in statsVsTeamLastYear[team]:
					againstTeamLastYearStats = dict(statsVsTeamLastYear[team][player].get(opp, {}))
					for hdr in againstTeamLastYearStats:
						if type(againstTeamLastYearStats[hdr]) is dict:
							againstTeamLastYearStats[hdr] = dict(againstTeamLastYearStats[hdr])

				if team in averages and player in averages[team]:
					overLine = math.ceil(line)
					try:
						over = averages[team][player]["tot"][f"{convertedProp}Overs"][str(overLine)]
						careerTotalGames = averages[team][player]["tot"]["gamesPlayed"]
						careerTotalOver = round(over * 100 / careerTotalGames)
					except:
						pass

				lastYearTeamMatchupOver = lastYearTotalOver = 0
				awayGames = homeGames = 0
				for t in teams:
					if t in lastYearStats and player in lastYearStats[t]:

						try:
							propArr = lastYearStats[t][player]["splits"][convertedProp].split(",")
						except:
							#print(player, prop, "skipping lastYrStats")
							continue
						oppArr = lastYearStats[t][player]["splits"]["opp"].split(",")
						awayHomeArr = lastYearStats[t][player]["splits"]["awayHome"].split(",")
						try:
							lastYearTotalOver = round(lastYearStats[t][player]["tot"][convertedProp+"Overs"][str(int(math.ceil(line)))] * 100 / lastYearStats[t][player]["tot"]["gamesPlayed"])
						except:
							pass

						lastYrLast20 = [int(x) for x in propArr[-20:]]
						totAwayGames = len([x for x in awayHomeArr if x == "A"])
						if totAwayGames:
							awayGames = len([x for x, ah in zip(propArr, awayHomeArr) if ah == "A" and float(x) > line]) * 100 / totAwayGames
						totHomeGames = len([x for x in awayHomeArr if x == "H"])
						if totHomeGames:
							homeGames = len([x for x, ah in zip(propArr, awayHomeArr) if ah == "H" and float(x) > line]) * 100 / totHomeGames
						try:
							lastYearTeamMatchupOver = round(len([x for x, o in zip(propArr, oppArr) if o == opp and float(x) > line]) * 100 / len([x for x in oppArr if x == opp]))
						except:
							pass

				lastYrAwayHomeSplits = f"{round(awayGames)}% - {round(homeGames)}%"

				# current year stats
				lastAll = []
				awayHomeSplits = [[], []]
				winLossSplits = [[], []]
				totalOver = battingAvg = avg = hitter_babip = babip = babipLastYear = bbpg = 0
				
				playerStats = {}
				if team in stats and player in stats[team] or (tradeFrom and player in stats[tradeFrom]):
					try:
						playerStats = stats[team][player].copy()
					except:
						playerStats = {}
					if tradeFrom and player in stats[tradeFrom]:
						for p in stats[tradeFrom][player]:
							if p not in playerStats:
								playerStats[p] = 0
							playerStats[p] += stats[tradeFrom][player][p]

					gamesPlayed = playerStats["gamesPlayed"]

					if gamesPlayed:
						bbpg = round(playerStats.get("bb", 0) / gamesPlayed, 2)
					val = 0
					if player in stats[team]:
						val = stats[team][player].get(prop, 0)
					avg = round(val / gamesPlayed, 2)

					p = pitcher
					if "P" in pos and ("ohtani" not in player or prop in ["w", "k", "h_allowed", "bb_allowed", "er"]):
						p = player
					else:
						if playerStats["ab"]:
							battingAvg = str(format(round(playerStats['h']/playerStats['ab'], 3), '.3f'))[1:]
							dem = playerStats["ab"]-playerStats["so"]-playerStats["hr"]+playerStats.get("sf", 0)
							if dem:
								hitter_babip = format((playerStats["h"] - playerStats["hr"]) / dem, '.3f')[1:]

					if p in advanced:
						dem = int(advanced[p]["ab"])-int(advanced[p]["strikeout"])-int(advanced[p]["home_run"])+int(advanced[p]["p_sac_fly"])
						if dem:
							babip = format((int(advanced[p]["hit"]) - int(advanced[p]["home_run"])) / dem, '.3f')[1:]

					if p in advancedLastYear:
						dem = int(advancedLastYear[p]["ab"])-int(advancedLastYear[p]["strikeout"])-int(advancedLastYear[p]["home_run"])+int(advancedLastYear[p]["p_sac_fly"])
						if dem:
							babipLastYear = format((int(advancedLastYear[p]["hit"]) - int(advancedLastYear[p]["home_run"])) / dem, '.3f')[1:]
					
				pitcherSummary = pitcherSummaryLastYear = strikePercent = p = ""
				if "P" in pos and ("ohtani" not in player or prop in ["w", "k", "h_allowed", "bb_allowed", "er"]):
					p = player
				else:
					p = pitcher

				if p and p in advanced:
					pitcherSummary = f"{advanced[p]['p_era']} ERA, {advanced[p]['batting_avg']} AVG, {advanced[p]['xba']} xAVG, {babip} BABIP, {advanced[p]['slg_percent']} SLG, {advanced[p]['xslg']} xSLG, {advanced[p]['woba']} WOBA, {advanced[p]['xwoba']} xWOBA, {advanced[p]['barrel_batted_rate']}% Barrel Batted"
				if p and p in advancedLastYear:
					pitcherSummaryLastYear = f"{advancedLastYear[p]['p_era']} ERA, {advancedLastYear[p]['batting_avg']} AVG, {advancedLastYear[p]['xba']} xAVG, {babipLastYear} BABIP, {advancedLastYear[p]['slg_percent']} SLG, {advancedLastYear[p]['xslg']} xSLG, {advancedLastYear[p]['woba']} WOBA, {advancedLastYear[p]['xwoba']} xWOBA, {advancedLastYear[p]['barrel_batted_rate']}% Barrel Batted"

				over5Innings = []
				playerSplits = {}
				if tradeFrom:
					for hdr in splits[tradeFrom][player]:
						playerSplits[hdr] = splits[tradeFrom][player][hdr]
					for hdr in splits[team][player]:
						playerSplits[hdr] += ","+splits[team][player][hdr]
				else:
					playerSplits = splits[team].get(player, {})

				awayHomeSplits = ""
				if prop in playerSplits:
					oppArr = playerSplits["opp"].split(",")
					winLossArr = playerSplits["winLoss"].split(",")
					awayHomeArr = playerSplits["awayHome"].split(",")
					lastAll = playerSplits[prop].split(",")

					totalOver = round(len([x for x in playerSplits[prop].split(",") if int(x) > float(line)]) * 100 / len(oppArr))
					if "P" in pos:
						over5Innings = round(len([x for x in playerSplits["ip"].split(",") if float(x) >= 5]) * 100 / len(oppArr))

					awayGames = len([x for x in awayHomeArr if x == "A"])
					if awayGames:
						awayGames = round(len([x for x, wl in zip(playerSplits[prop].split(","), awayHomeArr) if wl == "A" and int(x) > float(line)]) * 100 / awayGames)

					homeGames = len([x for x in awayHomeArr if x == "H"])
					if homeGames:
						homeGames = round(len([x for x, wl in zip(playerSplits[prop].split(","), awayHomeArr) if wl == "H" and int(x) > float(line)]) * 100 / homeGames)

					awayHomeSplits = f"{awayGames}% - {homeGames}%"


				oppRank = oppRankVal = oppABRank = ""
				oppRankLastYear = oppRankLast3 = ""
				rankingsProp = convertRankingsProp(propName)
				
				if rankingsProp in rankings[opp]:
					oppRankVal = str(rankings[opp][rankingsProp]["season"])
					oppRank = rankings[opp][rankingsProp]['rank']
					oppRankLastYear = rankings[opp][rankingsProp].get('lastYearRank', 0)
					if rankingsProp in ["so"]:
						oppRankLastYear = 30 - oppRankLastYear
					oppRankLast3 = rankings[opp][rankingsProp].get('last3', 0)
					oppABRank = rankings[opp]["opp_ab"]["rank"]

				hitRateOdds = diff = 0
				if lastYearTotalOver != 100:
					hitRateOdds = int((100 * lastYearTotalOver) / (-100 + lastYearTotalOver))
					diff = -1 * (hitRateOdds - int(overOdds))

				againstPitcherStats = ""
				againstPitcherStatsPerAB = ""
				try:
					bvpStats = bvp[team][player+' v '+pitcher]
					againstPitcherStats = f"{str(format(round(bvpStats['h']/bvpStats['ab'], 3), '.3f'))[1:]} {int(bvpStats['h'])}-{int(bvpStats['ab'])}, {int(bvpStats['hr'])} HR, {int(bvpStats['rbi'])} RBI, {int(bvpStats['bb'])} BB, {int(bvpStats['so'])} SO"
					againstPitcherStatsPerAB = f"{str(format(round(bvpStats['h']/bvpStats['ab'], 3), '.3f'))[1:]} {int(bvpStats['h'])}-{bvpStats['ab']}, {round(bvpStats['hr'] / bvpStats['ab'], 2)} HR, {round(bvpStats['rbi'] / bvpStats['ab'], 2)} RBI, {round(bvpStats['bb'] / bvpStats['ab'], 2)} BB, {round(bvpStats['so'] / bvpStats['ab'], 2)} SO"
				except:
					pass

				try:
					if againstTeamLastYearStats.get("ab", 0):
						againstTeamLastYearStatsDisplay = f"{str(format(round(againstTeamLastYearStats['h']/againstTeamLastYearStats['ab'], 3), '.3f'))[1:]} {int(againstTeamLastYearStats['h'])}-{int(againstTeamLastYearStats['ab'])}, {int(againstTeamLastYearStats['hr'])} HR, {int(againstTeamLastYearStats['rbi'])} RBI, {int(againstTeamLastYearStats['bb'])} BB, {int(againstTeamLastYearStats['so'])} SO"
						againstTeamLastYearStatsPerAB = f"{str(format(round(againstTeamLastYearStats['h']/againstTeamLastYearStats['ab'], 3), '.3f'))[1:]} {int(againstTeamLastYearStats['h'])}-{int(againstTeamLastYearStats['ab'])}, {round(againstTeamLastYearStats['hr'] / againstTeamLastYearStats['ab'], 2)} HR, {round(againstTeamLastYearStats['rbi'] / againstTeamLastYearStats['ab'], 2)} RBI, {round(againstTeamLastYearStats['bb'] / againstTeamLastYearStats['ab'], 2)} BB, {round(againstTeamLastYearStats['so'] / againstTeamLastYearStats['ab'], 2)} SO"
					elif againstTeamLastYearStats.get("ip"):
						againstTeamLastYearStatsDisplay = f"{round(againstTeamLastYearStats['ip'], 1)} IP {int(againstTeamLastYearStats['k'])} K, {int(againstTeamLastYearStats['h'])} H, {int(againstTeamLastYearStats['bb'])} BB"
						againstTeamLastYearStats = f"{round(againstTeamLastYearStats['ip'], 1)} IP {round(againstTeamLastYearStats['k'] / againstTeamLastYearStats['ip'], 2)} K, {round(againstTeamLastYearStats['h'] / againstTeamLastYearStats['ip'], 2)} H, {round(againstTeamLastYearStats['bb'] / againstTeamLastYearStats['ip'], 2)} BB"
					else:
						againstTeamLastYearStatsDisplay = ""
						againstTeamLastYearStatsPerAB = ""
				except:
					againstTeamLastYearStatsDisplay = ""
					againstTeamLastYearStatsPerAB = ""

				#try:
				againstTeamStatsPerAB = ""
				if againstTeamStats.get("ab", 0):
					againstTeamStatsDisplay = f"{str(format(round(againstTeamStats['h']/againstTeamStats['ab'], 3), '.3f'))[1:]} {int(againstTeamStats['h'])}-{int(againstTeamStats['ab'])}, {int(againstTeamStats['hr'])} HR, {int(againstTeamStats['rbi'])} RBI, {int(againstTeamStats['bb'])} BB, {int(againstTeamStats['so'])} SO"
					againstTeamStatsPerAB = f"{str(format(round(againstTeamStats['h']/againstTeamStats['ab'], 3), '.3f'))[1:]} {int(againstTeamStats['h'])}-{int(againstTeamStats['ab'])}, {round(againstTeamStats['hr'] / againstTeamStats['ab'], 2)} HR, {round(againstTeamStats['rbi'] / againstTeamStats['ab'], 2)} RBI, {round(againstTeamStats['bb'] / againstTeamStats['ab'], 2)} BB, {round(againstTeamStats['so'] / againstTeamStats['ab'], 2)} SO"
				elif againstTeamStats.get("ip"):
					againstTeamStatsDisplay = f"{round(againstTeamStats['ip'], 1)} IP {int(againstTeamStats['k'])} K, {int(againstTeamStats.get('h', 0))} H, {int(againstTeamStats.get('bb', 0))} BB"
					againstTeamStatsPerAB = f"{round(againstTeamStats['ip'], 1)} IP {round(againstTeamStats['k'] / againstTeamStats['ip'], 2)} K, {round(againstTeamStats.get('h', 0) / againstTeamStats['ip'], 2)} H, {round(againstTeamStats.get('bb', 0) / againstTeamStats['ip'], 2)} BB"
				else:
					againstTeamStatsDisplay = ""
					againstTeamStatsPerAB = ""
				

				last20Over = last10Over = 0
				arr = lastAll.copy()
				if len(arr) < 10:
					arr = lastYrLast20
					arr.extend(lastAll)
				if arr:
					last10Over = round(len([x for x in arr[-10:] if float(str(x).replace("'", "")) > line]) * 100 / len(arr[-10:]))
				arr = lastAll.copy()
				if len(arr) < 20:
					arr = lastYrLast20
					arr.extend(lastAll)
				if arr:
					last20Over = round(len([x for x in arr[-20:] if float(str(x).replace("'", "")) > line]) * 100 / len(arr[-20:]))

				projDiff = 0
				if proj:
					projDiff = round((proj - line) / proj, 3)

				# savant
				xHR = 0
				try:
					xHR = expectedHR[team][player]["xhr_diff"]
				except:
					pass
				pitcherXBA = xBA = oba = 0
				try:
					xBA = format(expected[team][player]["est_ba"], '.3f')[1:]
					if "P" in pos and ("ohtani" not in player or prop in ["w", "k", "h_allowed", "bb_allowed", "er"]):
						battingAvg = format(expected[team][player]["ba"], '.3f')[1:]
					else:
						pitcherXBA = format(expected[opp][pitcher]["est_ba"], '.3f')[1:]
				except:
					pass
				try:
					oba = f"{expected[team][player]['woba']} wOBA -- {expected[team][player]['est_woba']} XwOBA -- {expected[team][player]['wobacon']} wOBAcon -- {expected[team][player]['est_wobacon']} XwOBAcon"
				except:
					pass

				stadiumHitsRank = parkFactors[homeTeam]["hitsRank"]
				stadiumHrRank = parkFactors[homeTeam]["hrRank"]

				# fangraphs
				leftRightAvg = 0
				try:
					leftRightAvg = format(leftRightSplits[team][player][f"{pitcherThrows}HP"]["avg"], '.3f')[1:]
				except:
					pass

				myProj = 0
				if projIP:
					avgIP = projIP
					if numberfireProjIP:
						avgIP = (projIP + numberfireProjIP) / 2

					myProj = (avgIP * 3) + ((avgIP-1) * hip) + ((avgIP-1) * bbip)

					if propName == "bb_allowed":
						myProj *= float(advancedPitcher.get("bb_percent", 0)) * 0.01
					elif propName == "k":
						myProj *= float(advancedPitcher.get("k_percent", 0)) * 0.01
					elif propName == "h_allowed":
						myProj = avgIP * hip
						
					myProj = round(myProj, 2)

				props.append({
					"game": game,
					"playerId": playerId,
					"savantId": savantId,
					"player": player.title(),
					"team": team.upper(),
					"opponent": opp.upper(),
					"hit": hit,
					"awayHome": "@" if awayTeam == team else "v",
					"awayHomeSplits": awayHomeSplits,
					"lastYearAwayHomeSplits": lastYrAwayHomeSplits,
					"playerPitches": playerPitches,
					"oppTeamBattingPitches": oppTeamBattingPitches,
					#"winLossSplits": winLossSplits,
					"bats": bats,
					"battingNumber": battingNumber,
					"hrFactor": stadiumHrRank,
					"bp": bp,
					"bpOdds": bpOdds,
					"babip": babip,
					"hitter_babip": hitter_babip,
					"bbpg": bbpg,
					"xBA": xBA,
					"xHR": xHR,
					"oba": oba,
					"pitcherXBA": pitcherXBA,
					"leftRightAvg": leftRightAvg,
					"stadiumHitsRank": stadiumHitsRank,
					"stadiumHrRank": stadiumHrRank,
					"pos": pos,
					"advancedPitcher": advancedPitcher,
					"againstPitcherStats": againstPitcherStats,
					"againstPitcherStatsPerAB": againstPitcherStatsPerAB,
					"againstTeamStats": againstTeamStatsDisplay,
					"againstTeamStatsPerAB": againstTeamStatsPerAB,
					"againstTeamLastYearStats": againstTeamLastYearStatsDisplay,
					"againstTeamLastYearStatsPerAB": againstTeamLastYearStatsPerAB,
					"pitcherSummary": pitcherSummary,
					"pitcherSummaryLastYear": pitcherSummaryLastYear,
					"pitcher": pitcher.split(" ")[-1].title(),
					"era": era,
					"pitcherThrows": pitcherThrows,
					"pitcherProj": pitcherProj,
					"over5Innings": over5Innings,
					"k/bb": kPerBB,
					"pitchesPerPlate": pitchesPerPlate,
					"hip": hip,
					"hpg": hpg,
					"bbip": bbip,
					"hrip": hrip,
					"kip": kip,
					"prop": propName,
					"displayProp": convertedProp,
					"gamesPlayed": gamesPlayed,
					"matchups": len(prevMatchup),
					"line": line or 0,
					"numberfireProj": numberfireProj,
					"myProj": myProj,
					"proj": proj,
					"numberfireProjIP": numberfireProjIP,
					"projIP": projIP,
					"projDiff": projDiff,
					"bpDiff": bpDiff,
					"battingAvg": battingAvg,
					"avg": avg,
					"diff": diff,
					"hitRateOdds": hitRateOdds,
					"careerTotalOver": careerTotalOver,
					"againstTeamTotalOver": againstTeamTotalOver,
					"totalOver": totalOver,
					"last10Over": last10Over,
					"last20Over": last20Over,
					"lastYearAvg": lastYearAvg,
					"lastYearTotalOver": lastYearTotalOver,
					"lastYearTeamMatchupOver": lastYearTeamMatchupOver,
					"lastDisplay": ",".join([str(x) for x in lastAll[-10:]]),
					"lastAll": ",".join([str(x) for x in lastAll]),
					"oppABRank": oppABRank,
					"oppRankLastYear": oppRankLastYear,
					"oppRank": oppRank,
					"oppRankLast3": oppRankLast3,
					"oppRankVal": oppRankVal,
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	return props

def writeLineups(date):
	url = f"https://www.rotowire.com/baseball/daily-lineups.php"

	if int(date[-2:]) > datetime.now().day or datetime.now().hour > 21 or datetime.now().hour < 3:
		url += "?date=tomorrow"

	outfile = "outmlb2"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)

	lineups = {}
	for box in soup.find_all("div", class_="lineup"):
		if "is-tools" in box.get("class") or "is-ad" in box.get("class"):
			continue

		away = convertDKTeam(box.find_all("div", class_="lineup__abbr")[0].text.lower())
		home = convertDKTeam(box.find_all("div", class_="lineup__abbr")[1].text.lower())

		for idx, lineupList in enumerate(box.find_all("ul", class_="lineup__list")):
			team = away if idx == 0 else home

			if team not in leftOrRight:
				leftOrRight[team] = {}

			status = "confirmed" if "is-green" in lineupList.find("div", class_="dot").get("class") else "expected"
			try:
				startingPitcher = " ".join(lineupList.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
			except:
				startingPitcher = ""
			try:
				leftOrRight[team][startingPitcher] = lineupList.find("span", class_="lineup__throws").text
			except:
				pass

			lineupTeam = team
			if team in lineups:
				lineupTeam += " gm2"
			lineups[lineupTeam] = {
				"batting": [],
				"pitching": startingPitcher
			}
			for li in lineupList.find_all("li")[2:]:
				try:
					player = " ".join(li.find("a").get("href").lower().split("/")[-1].split("-")[:-1])
					lineups[lineupTeam]["batting"].append(player)
					leftOrRight[team][player] = li.find("span", class_="lineup__bats").text
				except:
					pass

	with open(f"{prefix}static/mlbprops/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)
	with open(f"{prefix}static/baseballreference/leftOrRight.json", "w") as fh:
		json.dump(leftOrRight, fh, indent=4)

def writeLeftRightSplits():
	url = "https://www.fangraphs.com/leaders/splits-leaderboards?splitArr=1&splitArrPitch=&position=B&autoPt=false&splitTeams=false&statType=player&statgroup=1&startDate=2023-03-01&endDate=2023-11-01&players=&filter=PA%7Cgt%7C10&groupBy=season&wxTemperature=&wxPressure=&wxAirDensity=&wxElevation=&wxWindSpeed=&sort=22,1&pg=0"

	leftRightSplits = {}

	for throws in ["LHP", "RHP"]:
		with open(f"{prefix}Splits Leaderboard Data vs {throws}.csv", newline="") as fh:
			reader = csv.reader(fh)

			headers = []
			for idx, row in enumerate(reader):
				if idx == 0:
					headers = [x.lower() for x in row]
				else:
					player = strip_accents(row[1]).lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
					team = convertDKTeam(row[2].lower())
					if team not in leftRightSplits:
						leftRightSplits[team] = {}
					if player not in leftRightSplits[team]:
						leftRightSplits[team][player] = {}
					if throws not in leftRightSplits[team][player]:
						leftRightSplits[team][player][throws] = {}

					for hdr, col in zip(headers, row):
						try:
							leftRightSplits[team][player][throws][f"{hdr}"] = float(col)
						except:
							leftRightSplits[team][player][throws][f"{hdr}"] = col

	with open(f"{prefix}static/baseballreference/leftRightSplits.json", "w") as fh:
		json.dump(leftRightSplits, fh, indent=4)


def write_numberfire_projections():
	projections = {}
	for t in ["batters", "pitchers"]:
		url = f"https://www.fanduel.com/research/mlb/fantasy/dfs-projections/{t}"

		outfile = "outmlb2"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		try:
			rows = soup.find("table", class_="stat-table").find("tbody").find_all("tr")
		except:
			continue
		for row in rows:
			try:
				team = row.find("span", class_="team-player__team active").text.strip().lower()
			except:
				continue
			#player = row.find("a", class_="full").get("href").split("/")[-1].lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "").replace("c j ", "cj ").replace("jd ", "jd ").replace("j p ", "jp ")
			player = row.find("a", class_="full").text.strip().lower().replace("'", "").replace(".", "").replace("-", " ").replace(" jr", "").replace(" ii", "").replace("c j ", "cj ").replace("jd ", "jd ").replace("j p ", "jp ")
			
			if team not in projections:
				projections[team] = {}
			projections[team][player] = {}

			cutoff = 5 if t == "batters" else 4
			for td in row.find_all("td")[cutoff:]:
				hdr = td.get("class")[0]
				if hdr == "wl":
					w,l = map(float, td.text.strip().split("-"))
					projections[team][player]["w"] = w
					projections[team][player]["l"] = l
				else:
					val = float(td.text.strip())
					projections[team][player][hdr] = val

			if t == "batters":
				projections[team][player]["h"] = projections[team][player]["1b"]+projections[team][player]["2b"]+projections[team][player]["3b"]+projections[team][player]["hr"]
				projections[team][player]["h+r+rbi"] = projections[team][player]["h"]+projections[team][player]["r"]+projections[team][player]["rbi"]
				projections[team][player]["tb"] = projections[team][player]["1b"]+2*projections[team][player]["2b"]+3*projections[team][player]["3b"]+4*projections[team][player]["hr"]

	with open(f"{prefix}static/baseballreference/numberfireProjections.json", "w") as fh:
		json.dump(projections, fh, indent=4)

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "").replace(" iv", "")

def write_projections(date):
	write_numberfire_projections()
	year = datetime.now().year

	projections = {}
	for HP in ["H", "P"]:
		with open(f"{prefix}FantasyPros_{year}_Projections_{HP}.csv", newline="") as fh:
			reader = csv.reader(fh)
			#data = fh.readlines()

			headers = []
			for idx, row in enumerate(reader):
				if idx == 0:
					headers = [x.lower() for x in row[5:-1]]
				else:
					if len(row) < 2:
						continue
					player = parsePlayer(row[1].lower().split(" (")[0])
					team = row[2].lower()
					if team == "cws":
						team = "chw"

					if player.startswith("shohei") and row[3] != "SP,DH":
						continue

					if team not in projections:
						projections[team] = {}
					if player not in projections[team]:
						projections[team][player] = {}
						

					for hdr, col in zip(headers, row[5:-1]):
						suffix = ""
						if HP == "P" and hdr in ["h", "bb", "hr"]:
							suffix = "_allowed"
						projections[team][player][f"{hdr}{suffix}"] = float(col)

					if "rbi" in projections[team][player]:
						projections[team][player]["h+r+rbi"] = round(projections[team][player]["h"]+projections[team][player]["r"]+projections[team][player]["rbi"], 2)
						projections[team][player]["1b"] = projections[team][player]["h"] - (projections[team][player]["hr"] + projections[team][player]["3b"] + projections[team][player]["2b"])
						projections[team][player]["tb"] = round(projections[team][player]["hr"]*4 + projections[team][player]["3b"]*3 + projections[team][player]["2b"]*2 + projections[team][player]["1b"], 2)
	with open(f"{prefix}static/mlbprops/projections/{date}.json", "w") as fh:
		json.dump(projections, fh, indent=4)

def getSlateData(date = None, teams=""):
	res = []

	if teams:
		teams = teams.lower().split(",")

	if not date:
		date = datetime.now()
		date = str(date)[:10]

	with open(f"{prefix}static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)
	with open(f"{prefix}static/baseballreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/baseballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/baseballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)
	with open(f"{prefix}static/baseballreference/teamTotals.json") as fh:
		teamTotals = json.load(fh)
	with open(f"{prefix}static/mlbprops/lineups.json") as fh:
		lineups = json.load(fh)
	with open(f"{prefix}static/mlb/draftkings.json") as fh:
		gameLines = json.load(fh)

	for game in schedule[date]:
		gameSp = game.split(" @ ")
		isAway = True
		for idx, team in enumerate(gameSp):
			opp = gameSp[0] if idx == 1 else gameSp[1]
			if idx == 1:
				isAway = False

			if game not in gameLines or "spread" not in gameLines[game]:
				continue

			runline = float(list(gameLines[game]["spread"].keys())[0])
			totalLine = list(gameLines[game]["total"].keys())[0]
			if idx == 1:
				runline *= -1

			runlineSpread = runline

			if runline > 0:
				runline = f"+{runline}"

			pitcherStats = {}
			pitcherRecord = pitcher = pitcherThrows = ""
			try:
				pitcher = lineups[team]["pitching"]
				pitcherThrows = leftOrRight[team][pitcher]
				pitcherStats = stats[team][pitcher]
				pitcherRecord = f"{pitcherStats.get('w', 0)}W-{pitcherStats.get('l', 0)}L"
				pitcherStats["era"] = round(9 * pitcherStats["er"] / pitcherStats["ip"], 2)
				pitcherStats["whip"] = round((pitcherStats["h_allowed"]+pitcherStats["bb_allowed"]) / pitcherStats["ip"], 2)
				pitcherStats["hip"] = round((pitcherStats["h_allowed"]) / pitcherStats["ip"], 2)
				pitcherStats["kip"] = round((pitcherStats["k"]) / pitcherStats["ip"], 2)
				pitcherStats["bbip"] = round((pitcherStats["bb_allowed"]) / pitcherStats["ip"], 2)
			except:
				pass

			odds = gameLines[game]['spread'][list(gameLines[game]["spread"].keys())[0]].split('/')[idx]
			runline = f"{runline} ({odds})"
			moneyline = gameLines[game]["ml"].split("/")[idx]
			odds = odds = gameLines[game]['total'][list(gameLines[game]["total"].keys())[0]].split('/')[idx]
			total = f"{'o' if idx == 0 else 'u'}{totalLine} ({odds})"

			prevMatchup = []
			totals = {"rpg": [], "rpga": [], "hpg": [], "hpga": [], "overs": [], "diff": []}
			for dt in sorted(schedule, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
				if dt == date or datetime.strptime(dt, "%Y-%m-%d") > datetime.strptime(date, "%Y-%m-%d"):
					continue
				for g in schedule[dt]:
					gSp = g.split(" @ ")
					if gSp[0] in scores[dt] and team in gSp:
						score1 = scores[dt][gSp[0]]
						score2 = scores[dt][gSp[1]]
						wonLost = "Won"
						currPitcher = []
						score = f"{score1}-{score2}"
						file = f"{prefix}static/baseballreference/{team}/{dt}.json"
						with open(file) as fh:
							gameStats = json.load(fh)

						if score2 > score1:
							score = f"{score2}-{score1}"
							if team == gSp[0]:
								wonLost = "Lost"
						elif team == gSp[1]:
							wonLost = "Lost"

						if opp in gSp:
							decision = "-"
							for p in gameStats:
								if "ip" in gameStats[p]:
									currPitcher.append(p)
									if "w" in gameStats[p]:
										decision = "W"
									elif "l" in gameStats[p]:
										decision = "L"
									break
							p = ""
							if currPitcher:
								p = currPitcher[0].title()
							prevMatchup.append(f"{dt} {wonLost} {score} (SP: {p} {decision})")

						teamScore = score1
						oppScore = score2
						if team == gSp[1]:
							teamScore, oppScore = oppScore, teamScore
						totals["rpg"].append(teamScore)
						totals["rpga"].append(oppScore)
						totals["overs"].append(teamScore+oppScore)
						totals["diff"].append(teamScore-oppScore)


			if len(totals["overs"]):
				totals["oversL10"] = ",".join([str(x) for x in totals["overs"][:10]])
				totals["ttL10"] = ",".join([str(x) for x in totals["rpg"][:10]])
				totals["totalOver"] = round(len([x for x in totals["overs"] if x > float(totalLine)]) * 100 / len(totals["overs"]))
				totals["runlineOver"] = round(len([x for x in totals["diff"] if x+runlineSpread > 0]) * 100 / len(totals["diff"]))
				totals["teamOver"] = f"{round(len([x for x in totals['overs'] if int(x) > float(totalLine)]) * 100 / len(totals['overs']))}% SZN • {round(len([x for x in totals['overs'][:15] if int(x) > float(totalLine)]) * 100 / len(totals['overs'][:15]))}% L15 • {round(len([x for x in totals['overs'][:5] if int(x) > float(totalLine)]) * 100 / len(totals['overs'][:5]))}% L5 • {round(len([x for x in totals['overs'][:3] if int(x) > float(totalLine)]) * 100 / len(totals['overs'][:3]))}% L3"

			for p in ["h", "r"]:
				totals[f"{p}pg"] = rankings[team][f"{p}"]["season"]
				totals[f"{p}pgL3"] = rankings[team][f"{p}"]["last3"]
				totals[f"{p}pgRank"] = rankings[team][f"{p}"]["rank"]
				totals[f"{p}pga"] = rankings[team][f"{p}_allowed"]["season"]
				totals[f"{p}pgaRank"] = rankings[team][f"{p}_allowed"]["rank"]
			for key in ["overs"]:
				if len(totals[key]):
					totals[key] = round(sum(totals[key]) / len(totals[key]), 1)
				else:
					totals[key] = 0

			try:
				advancedPitcher = advanced[pitcher].copy()
			except:
				advancedPitcher = {}

			res.append({
				"game": game,
				"team": team,
				"opp": opp,
				"awayHome": "A" if isAway else "H",
				"prevMatchup": " • ".join(prevMatchup),
				"prevMatchupList": prevMatchup,
				"runline": runline,
				"moneylineOdds": moneyline,
				"total": total,
				"totals": totals,
				"pitcher": pitcher,
				"rankings": rankings[team],
				"advancedPitcher": advancedPitcher,
				"pitcherStats": pitcherStats,
				"pitcherThrows": pitcherThrows,
				"pitcherRecord": pitcherRecord,
			})

	return res

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def writeBPPlayerProps(date):
	url = f"https://www.ballparkpal.com/PlayerProps.php?date={date}"

	playerProps = {}
	outfile = "outmlb2"
	time.sleep(0.2)
	call(["curl", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	bps = {}
	for row in soup.find("table", id="table_id").find_all("tr")[1:]:
		prop = row.find_all("td")[6].text.lower().split(" ")[1]
		if prop == "bases":
			prop = "tb"
		elif prop == "ks":
			prop = "k"
		elif prop == "hits":
			prop = "h"

		if prop == "k":
			line = row.find_all("td")[6].text.split(" ")[-1]
			prop = f"{line}k"

		if prop not in bps:
			bps[prop] = []

		try:
			bps[prop].append(int(row.find_all("td")[7].text))
		except:
			continue

	for prop in bps:
		bps[prop] = sorted(bps[prop])

	for row in soup.find("table", id="table_id").find_all("tr")[1:]:
		team = row.find("td").text.lower().replace("was", "wsh")
		player = row.find_all("td")[1].text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
		if player == "nicholas castellanos":
			player = "nick castellanos"
		elif player == "nate lowe":
			player = "nathaniel lowe"
		pa = float(row.find_all("td")[5].text)
		prop = row.find_all("td")[6].text.lower().split(" ")[1]
		if prop == "bases":
			prop = "tb"
		elif prop == "ks":
			prop = "k"
		elif prop == "hits":
			prop = "h"

		try:
			bp = int(row.find_all("td")[7].text)
		except:
			continue

		line = 0
		if prop == "k":
			line = row.find_all("td")[6].text.split(" ")[-1]
			prop = f"{line}k"

		if team not in playerProps:
			playerProps[team] = {}

		if player not in playerProps[team]:
			playerProps[team][player] = {}

		if prop not in playerProps[team][player]:
			playerProps[team][player][prop] = {}

		playerProps[team][player][prop] = {
			"pa": pa, "bp": bp, "bpRank": bps[prop].index(int(bp))
		}

	with open(f"{prefix}static/baseballreference/BPPlayerProps.json", "w") as fh:
		json.dump(playerProps, fh, indent=4)

def writeBallparks(date):
	url = f"https://ballparkpal.com/ParkFactors.php?date={date}"

	ballparks = {}
	playerHRFactors = {}
	outfile = "outmlb2"
	time.sleep(0.2)
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	for row in soup.find("table", class_="parkFactorsTable").find_all("tr")[1:]:
		game = row.find("div", class_="matchupText").text.strip().lower().replace("was", "wsh")
		hr = row.find("td", class_="projectionText").text

		ballparks[game] = hr

	for row in soup.find("table", id="table_id").find_all("tr")[1:]:
		team = row.find("td").text.lower().replace("was", "wsh")
		player = row.find_all("td")[1].text.lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
		if player == "nicholas castellanos":
			player = "nick castellanos"
		elif player == "nate lowe":
			player = "nathaniel lowe"
		hr = float(row.find_all("td")[3].text)

		if team not in playerHRFactors:
			playerHRFactors[team] = {}
		playerHRFactors[team][player] = hr

	with open(f"{prefix}static/baseballreference/ballparks.json", "w") as fh:
		json.dump(ballparks, fh, indent=4)

	with open(f"{prefix}static/baseballreference/playerHRFactors.json", "w") as fh:
		json.dump(playerHRFactors, fh, indent=4)

@mlbprops_blueprint.route('/slatemlb')
def slate_route():
	date = None
	if request.args.get("date"):
		date = request.args.get("date")
	data = getSlateData(date=date)
	grouped = {}
	for row in data:
		if row["game"] not in grouped:
			grouped[row["game"]] = {}
		grouped[row["game"]][row["awayHome"]] = row

	return render_template("slatemlb.html", data=grouped)

@mlbprops_blueprint.route('/getMLBProps')
def getProps_route():
	pitchers = False
	if request.args.get("pitchers"):
		pitchers = True
	if request.args.get("players") or request.args.get("date") or request.args.get("line"):
		players = ""
		if request.args.get("players"):
			players = request.args.get("players").lower().split(",")
		props = getPropData(date=request.args.get("date"), playersArg=players, teamsArg="", pitchers=pitchers, lineArg=request.args.get("line") or "")
	elif request.args.get("prop"):
		path = f"{prefix}static/betting/mlb_{request.args.get('prop')}.json"
		if not os.path.exists(path):
			with open(f"{prefix}static/betting/mlb.json") as fh:
				props = json.load(fh)
		else:
			with open(path) as fh:
				props = json.load(fh)
	else:
		with open(f"{prefix}static/betting/mlb.json") as fh:
			props = json.load(fh)

	if request.args.get("teams"):
		arr = []
		teams = request.args.get("teams").lower().split(",")
		for row in props:
			team1, team2 = map(str, row["game"].split(" @ "))
			if team1 in teams or team2 in teams:
				arr.append(row)
		props = arr

	if request.args.get("bet"):
		arr = []
		for row in props:
			if "P" in row["pos"]:
				arr.append(row)
			else:
				if int(str(row["battingNumber"]).replace("-", "10")) <= 6:
					arr.append(row)
		props = arr

	if request.args.get("pitchers"):
		arr = []
		for row in props:
			if "P" in row["pos"]:
				arr.append(row)
		props = arr

	return jsonify(props)

@mlbprops_blueprint.route('/hedge')
def hedge_route():
	return render_template("hedge.html")

@mlbprops_blueprint.route('/mlbprops')
def props_route():
	prop = date = teams = players = bet = pitchers = line = ""
	if request.args.get("prop"):
		prop = request.args.get("prop").replace(" ", "+")

	if request.args.get("date"):
		date = request.args.get("date")
		if date == "yesterday":
			date = str(datetime.now() - timedelta(days=1))[:10]
		elif date == "today":
			date = str(datetime.now())[:10]
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("players"):
		players = request.args.get("players")
	if request.args.get("bet"):
		bet = request.args.get("bet")
	if request.args.get("line"):
		line = request.args.get("line")
	if request.args.get("pitchers"):
		pitchers = request.args.get("pitchers")

	with open(f"{prefix}bets") as fh:
		bets = json.load(fh)

	if prop in bets:
		bets = bets[prop]
	else:
		bets = []
		
	bets = ",".join(bets)
	return render_template("mlbprops.html", prop=prop, date=date, teams=teams, bets=bets, players=players, bet=bet, line=line, pitchers=pitchers)


def quartiles(arr):
	arr = sorted(arr)
	size = len(arr)
	mLen, qLen = int(size/2), int(size/4)
	q1, q3 = arr[qLen], arr[qLen*3]

	if size % 2 == 0:
		q1 = round((arr[qLen - 1] + arr[qLen]) / 2, 1)
		q3 = round((arr[3*qLen - 1] + arr[3*qLen]) / 2, 1)
		mid = round((arr[mLen-1] + arr[mLen]) / 2, 1)
	else:
		mid = arr[mLen]
	return q1, mid, q3

def convertFDTeam(team):
	team = team.replace("pittsburgh pirates", "pit").replace("detroit tigers", "det").replace("cincinnati reds", "cin").replace("colorado rockies", "col").replace("minnesota twins", "min").replace("los angeles dodgers", "lad").replace("arizona diamondbacks", "ari").replace("oakland athletics", "ath").replace("philadelphia phillies", "phi").replace("san francisco giants", "sf").replace("kansas city royals", "kc").replace("san diego padres", "sd").replace("los angeles angels", "laa").replace("baltimore orioles", "bal").replace("washington nationals", "wsh").replace("miami marlins", "mia").replace("new york yankees", "nyy").replace("toronto blue jays", "tor").replace("seattle mariners", "sea").replace("boston red sox", "bos").replace("tampa bay rays", "tb").replace("new york mets", "nym").replace("milwaukee brewers", "mil").replace("st. louis cardinals", "stl").replace("atlanta braves", "atl").replace("texas rangers", "tex").replace("cleveland guardians", "cle").replace("chicago white sox", "chw").replace("chicago cubs", "chc").replace("houston astros", "hou")
	return team

def writeBovada(date):

	url = "https://www.bovada.lv/services/sports/event/coupon/events/A/description/baseball/mlb?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"
	outfile = "outmlb2"
	call(["curl", "-k", url, "-o", outfile])

	with open(outfile) as fh:
		data = json.load(fh)

	if not data:
		return

	lines = {}

	for event in data[0]["events"]:
		game = convertFDTeam(event["description"].lower())
		gameLink = event["link"]

		propUrl = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description/{gameLink}"

		time.sleep(0.3)
		outfile = "outmlb2"
		call(["curl", "-k", propUrl, "-o", outfile])

		with open(outfile) as fh:
			propData = json.load(fh)

		lines[game] = {}
		for group in propData[0]["events"][0]["displayGroups"]:
			if group["description"] == "Player Props":
				for market in group["markets"]:
					desc = strip_accents(market["description"])
					if not desc.startswith("Total Hits, Runs and RBI"):
						continue
					player = desc.lower().split(" - ")[-1].split(" (")[0].replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" ii", "")
					ou = ["", ""]
					for outcome in market["outcomes"]:
						idx = 0 if outcome["type"] == "O" else 1
						ou[idx] = outcome["price"]["american"].replace("EVEN", "+100")

					lines[game][player] = f"{ou[0]}/{ou[1]}"

	with open(f"{prefix}static/mlbprops/bovada.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def hrrEV(date):

	with open(f"{prefix}static/mlbprops/dates/{date}.json") as fh:
		lines = json.load(fh)

	with open(f"{prefix}static/mlbprops/bovada.json") as fh:
		bovada = json.load(fh)

	data = []
	for game in lines:
		if game not in bovada:
			continue
		for player in lines[game]:
			if player not in bovada[game]:
				continue

			ou = lines[game][player]["h+r+rbi"]["line"]
			over = lines[game][player]["h+r+rbi"]["over"]
			bovadaOver = bovada[game][player].split("/")[0]

			if int(over) > int(bovadaOver):
				diff = (int(over) - int(bovadaOver)) / int(over)
				data.append((diff, game, player, over, bovadaOver))

	for row in sorted(data, reverse=True):
		print(row)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("--lineups", help="Lineups", action="store_true")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("-p", "--props", action="store_true", help="Props")
	parser.add_argument("--prop")
	parser.add_argument("-b", "--bovada", action="store_true", help="Bovada")
	parser.add_argument("--projections", help="Projections", action="store_true")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.lineups:
		writeLineups(date)
	elif args.lines:
		writeProps(date, args.prop)
	elif args.props:
		writeStaticProps(date)
	elif args.bovada:
		writeBovada(date)
		#hrrEV(date)
	elif args.projections:
		write_projections(date)
		writeLeftRightSplits()
		writeStaticProps()
	elif args.cron:
		writeLineups(date)
		writeProps(date, args.prop)
		#writeBallparks(date)
		#writeBPPlayerProps(date)
		#writeGameLines(date)

		write_projections(date)
		writeLeftRightSplits()
		writeStaticProps(date)

	#writeBPPlayerProps(date)
	#writeGameLines(date)
	write_numberfire_projections()
	#write_projections(date)
	#writeBallparks(date)
	#Walks Allowed (Proj) = (FantasyPros Projection) * (Pitches per Plate Appearance) * (Opponent BB Rank) * (K/BB) / (Season Average) * (Career Walk Average)

	#writeStaticProps()
	#writeBallparks()

	if False:
		for dt in os.listdir("static/baseballreference/nyy"):
			with open(f"static/baseballreference/nyy/{dt}") as fh:
				stats = json.load(fh)

			if "dj lemahieu" in stats:
				print(dt, stats["dj lemahieu"]["h"])

	if False:
		with open(f"{prefix}static/baseballreference/schedule.json") as fh:
			schedule = json.load(fh)

		print("[", end="")
		print(", ".join([f"'{x}'" for x in schedule[date]]), end="")
		print("]")


	if False:
		with open(f"{prefix}static/baseballreference/schedule.json") as fh:
			schedule = json.load(fh)

		with open(f"{prefix}static/baseballreference/rankings.json") as fh:
			rankings = json.load(fh)

		with open(f"{prefix}static/baseballreference/ballparks.json") as fh:
			ballparks = json.load(fh)

		with open(f"{prefix}static/baseballreference/advanced.json") as fh:
			advanced = json.load(fh)

		with open(f"{prefix}static/mlbprops/lineups.json") as fh:
			lineups = json.load(fh)

		with open(f"{prefix}static/baseballreference/parkfactors.json") as fh:
			savantRank = json.load(fh)

		print("Rankings Source: [Team Rankings](https://www.teamrankings.com/mlb/stat/home-runs-per-game)  ")
		print("Park Factor % Source: [Ballparkpal](https://ballparkpal.com/ParkFactors.php)  ")
		print("Park Factor Rank Source: [baseball savant](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors)")
		print("\n")

		headers = ["Game", "Park Factor Rank", "Park Factor %", "Away", "Away HR/G", "Away Rank", "Away Opp HR/G", "Away Opp HR/G Rank", "Away A-H Splits", "Home", "Home HR/G", "Home Rank", "Home Opp HR/G", "Home Opp HR/G Rank", "Home A-H Splits"]

		print("|".join(headers))
		print("|".join([":--"]*len(headers)))
		seen = {}
		for game in schedule[date]:
			if game in seen:
				continue
			seen[game] = True
			away, home = map(str, game.split(" @ "))
			awayRank, awayVal = addNumSuffix(rankings[away]["hr"]["rank"]), rankings[away]["hr"]["season"]
			awayOppRank, awayOppVal = addNumSuffix(rankings[away]["hr_allowed"]["rank"]), rankings[away]["hr_allowed"]["season"]
			awaySplits = f"**{rankings[away]['hr']['away']}** - {rankings[away]['hr']['home']}"
			homeRank, homeVal = addNumSuffix(rankings[home]["hr"]["rank"]), rankings[home]["hr"]["season"]
			homeOppRank, homeOppVal = addNumSuffix(rankings[home]["hr_allowed"]["rank"]), rankings[home]["hr_allowed"]["season"]
			homeSplits = f"{rankings[home]['hr']['away']} - **{rankings[home]['hr']['home']}**"
			print(f"{game.upper()}|{addNumSuffix(savantRank[home]['hrRank'])}|{ballparks[game]}|{away.upper()}|{awayVal}|{awayRank}|{awayOppVal}|{awayOppRank}|{awaySplits}|{home.upper()}|{homeVal}|{homeRank}|{homeOppVal}|{homeOppRank}|{homeSplits}")

		print("\n")
		headers = ["Team", "Opp", "Opp Pitcher", "Sweet Spot %", "Hard Hit %", "Barrel Batted %", "Out of Zone %", "In Zone Contact %"]
		print("|".join(headers))
		print("|".join([":--"]*len(headers)))
		for game in schedule[date]:
			away, home = map(str, game.split(" @ "))
			awayPitcher, homePitcher = lineups[away]["pitching"], lineups[home]["pitching"]
			try:
				print(f"{away.upper()}|{home.upper()}|{homePitcher.title()}|{advanced[home][homePitcher]['sweet_spot_percent']}%|{advanced[home][homePitcher]['hard_hit_percent']}%|{advanced[home][homePitcher]['barrel_batted_rate']}%|{advanced[home][homePitcher]['out_zone_percent']}%|{advanced[home][homePitcher]['iz_contact_percent']}%")
				print(f"{home.upper()}|{away.upper()}|{awayPitcher.title()}|{advanced[away][awayPitcher]['sweet_spot_percent']}%|{advanced[away][awayPitcher]['hard_hit_percent']}%|{advanced[away][awayPitcher]['barrel_batted_rate']}%|{advanced[away][awayPitcher]['out_zone_percent']}%|{advanced[away][awayPitcher]['iz_contact_percent']}%")
			except:
				continue

	if False:

		totHits = {}
		games = {}
		for team in os.listdir("static/baseballreference/"):
			if team.endswith("json"):
				continue

			for dt in os.listdir(f"static/baseballreference/{team}/"):
				with open(f"static/baseballreference/{team}/{dt}") as fh:
					stats = json.load(fh)

				if not stats:
					continue

				dt = dt[:-5].replace("-gm2", "")
				if dt not in totHits:
					totHits[dt] = {"h": 0, "hr": 0, "r": 0}
				if dt not in games:
					games[dt] = 0

				games[dt] += 1

				for player in stats:
					if "ip" not in stats[player]:
						for hdr in totHits[dt]:
							totHits[dt][hdr] += stats[player][hdr]


		for p in ["h", "hr", "r"]:
			for dt in sorted(totHits, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
				for prop in totHits[dt]:
					if p != prop:
						continue
					avg = round(totHits[dt][prop] / (games[dt] / 2), 2)
					print(dt, prop, avg)
			print("\n")

		hrs = []
		for dt in totHits:
			hrs.append(totHits[dt]["hr"] / (games[dt] / 2))
		print(sum(hrs) / len(hrs))


	# Analyze pitchers
	if False:
		with open(f"{prefix}static/baseballreference/schedule.json") as fh:
			schedule = json.load(fh)
		with open(f"{prefix}static/baseballreference/roster.json") as fh:
			roster = json.load(fh)
		with open(f"{prefix}static/baseballreference/advanced.json") as fh:
			advanced = json.load(fh)

		analysis = {}
		dts = schedule.keys()
		#dts = ["2023-04-26"]
		for dt in sorted(dts, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):

			path = f"{prefix}static/mlbprops/dates/{dt}.json"
			if not os.path.exists(path):
				continue

			with open(path) as fh:
				props = json.load(fh)

			if datetime.strptime(dt, "%Y-%m-%d") >= datetime.strptime(str(datetime.now())[:10], "%Y-%m-%d"):
				continue

			for game in schedule[dt]:
				away, home = map(str, game.split(" @ "))

				for teamIdx, team in enumerate([away, home]):

					path = f"{prefix}static/baseballreference/{team}/{dt}.json"
					if not os.path.exists(path):
						continue

					with open(path) as fh:
						stats = json.load(fh)

					for player in stats:

						try:
							if "P" not in roster[team][player]:
								continue
						except:
							continue

						if game not in props or player not in props[game]:
							continue

						for prop in ["k", "bb_allowed", "h_allowed"]:
							if prop not in props[game][player] or prop not in stats[player]:
								continue

							if prop not in analysis:
								analysis[prop] = {}

							if player not in advanced:
								continue

							hit = "miss"
							line = props[game][player][prop]["line"]
							if stats[player][prop] >= line:
								hit = "hit"

							for hdr in ["out_zone_percent", "z_swing_percent", "oz_swing_percent", "iz_contact_percent", "oz_contact_percent", "whiff_percent", "f_strike_percent", "swing_percent", "z_swing_miss_percent", "oz_swing_miss_percent"]:

								if hdr not in analysis[prop]:
									analysis[prop][hdr] = {"hit": [], "miss": []}
								
								analysis[prop][hdr][hit].append(advanced[player][hdr])
			
		for prop in analysis:
			print(prop)
			for hdr in analysis[prop]:
				arr = []
				for hit in analysis[prop][hdr]:
					arr.append(quartiles(analysis[prop][hdr][hit]))
				print("\t", hdr, arr)