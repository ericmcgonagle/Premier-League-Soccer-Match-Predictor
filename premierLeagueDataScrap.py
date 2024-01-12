import html
import time

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import webbrowser

standingsURL = "https://fbref.com/en/comps/9/Premier-League-Stats"

data = requests.get(standingsURL)
soup = BeautifulSoup(data.text, features="lxml")
standingsTable = soup.select('table.stats_table')[0]

# using "find_all" here to select all `a` tags
links = standingsTable.find_all('a')
links = [l.get("href") for l in links]
links = [l for l in links if '/squads/' in l]

teamURLS = [f"https://fbref.com{l}" for l in links]

teamURL = teamURLS[0]

data = requests.get(teamURL)

matches = pd.read_html(data.text, match="Scores & Fixtures")  # read all tables on page with matching string

soup = BeautifulSoup(data.text, features="lxml")

links = soup.find_all('a')
links = [l.get("href") for l in links]

# looking for any links with the specified element
links = [l for l in links if l and 'all_comps/shooting/' in l]

data = requests.get(f"https://fbref.com{links[0]}")

shooting = pd.read_html(data.text, match="Shooting")[0]

shooting.columns = shooting.columns.droplevel()

teamData = matches[0].merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")

years = list(range(2022, 2020, -1))

allMatches = []

standingsURL = "https://fbref.com/en/comps/9/Premier-League-Stats"

for year in years:
    data = requests.get(standingsURL)
    soup = BeautifulSoup(data.text, features="lxml")
    standingsTable = soup.select('table.stats_table')[0]

    # using "find_all" here to select all `a` tags
    links = [l.get("href") for l in standingsTable.find_all('a')]
    links = [l for l in links if '/squads/' in l]

    teamURLS = [f"https://fbref.com{l}" for l in links]

    previousSeason = soup.select("a.prev")[0].get("href")
    standingsURL = f"https://fbref.com{previousSeason}"

    for teamURL in teamURLS:
        teamName = teamURL.split('/')[-1].replace('-Stats', '').replace('-', ' ')

        data = requests.get(teamURL)
        matches = pd.read_html(data.text, match="Scores & Fixtures")[0]

        soup = BeautifulSoup(data.text, features="lxml")
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/shooting/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        shooting = pd.read_html(data.text, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()

        try:
            teamData = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
        except ValueError:
            continue

        #         filter out games that aren't in premier league reguar season games
        teamData = teamData[teamData['Comp'] == 'Premier League']
        teamData["Season"] = year
        teamData["Team"] = teamName
        allMatches.append(teamData)
        time.sleep(np.random.randint(1, 5))

matchDF = pd.concat(allMatches)

matchDF.columns = [c.lower() for c in matchDF.columns]
matchDF.to_csv("premierLeagueData.csv", index=False)
