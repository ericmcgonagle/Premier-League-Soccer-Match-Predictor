import pandas as pd
import webbrowser

matches = pd.read_csv("premierLeagueData.csv")
matches.to_html("premierLeagueData.html", index=False)
# need to convert object data types to respective types for machine learning algorithms

matches["date"] = pd.to_datetime(matches["date"])

# first predictor to create; indicate whether home/away game numerically
matches["venue_code"] = matches["venue"].astype("category").cat.codes
matches["opp_code"] = matches["opponent"].astype("category").cat.codes
matches["hour"] = matches["time"].str.replace(":.+", "", regex=True).astype("int")
matches["day_code"] = matches["date"].dt.dayofweek
matches["target"] = (matches["result"] == "W").astype("int")

from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)

# subsetting match datafram training using past dates and testing using current dates/season
train = matches[matches["date"] < '2022-01-01']
test = matches[matches["date"] >= '2022-01-01']
predictors = ["venue_code", "opp_code", "hour", "day_code"]
rf.fit(train[predictors], train["target"])
preds = rf.predict(test[predictors])

from sklearn.metrics import accuracy_score

acc = accuracy_score(test["target"], preds)

# look into which predictions were high vs low
combined = pd.DataFrame(dict(actual=test["target"], prediction=preds))
pd.crosstab(index=combined["actual"], columns=combined["prediction"])

from sklearn.metrics import precision_score

precision_score(test["target"], preds)

groupedMatches = matches.groupby("team")


def rollingAverages(group, cols, newCols):
    group = group.sort_values("date")  # sort by date
    rollingStats = group[cols].rolling(3, closed='left').mean()
    group[newCols] = rollingStats
    group = group.dropna(subset=newCols)
    return group


cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
newCols = [f"{c}_rolling" for c in cols]

matchesRolling = matches.groupby("team").apply(lambda x: rollingAverages(x, cols, newCols))

matchesRolling = matchesRolling.droplevel('team')

matchesRolling.index = range(matchesRolling.shape[0])


def makePredictions(data, predictors):
    train = data[data["date"] < '2022-01-01']
    test = data[data["date"] >= '2022-01-01']
    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], prediction=preds), index=test.index)
    precision = precision_score(test["target"], preds)
    return combined, precision


combined, precision = makePredictions(matchesRolling, predictors + newCols)

combined = combined.merge(matchesRolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)


class MissingDict(dict):
    __missing__ = lambda self, key: key


mapValues = {
    "Brighton & Hove Albion": "Brighton",
    "Manchester United": "Manchester Utd",
    "Newcastle Untied": "Newcastle utd",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",

}
mapping = MissingDict(mapValues)

combined["newTeam"] = combined["team"].map(mapping)

merged = combined.merge(combined, left_on=["date", "newTeam"], right_on=["date", "opponent"])

print(matches.columns)
