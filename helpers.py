import os
import requests
import urllib.parse
import numpy as np
from datetime import datetime

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def datatable(db, USERS, START, typ):
    userIds = ','.join(str(user["user_id"]) for user in USERS)
    myData = db.execute(
        f"""
        select user_id, value, time
        from data
        where type = {typ}
        and time >= '{START}'
        and user_id in ({userIds})
        ORDER BY time, user_id
        """)

    headers = ["Day"]
    for user in USERS:
        headers.append(user["name"])

    dataPresent = []
    for user in USERS:
        dataPresent.append(False)

    data = []
    data.append(headers)

    day = START
    userIdx = 0
    numUsers = len(USERS)
    dayOfData = [day]
    for row in myData:
        # if it's a new day
        if row["time"] != day:
            # finish the rest of the users for the day
            while userIdx < numUsers:
                dayOfData.append(None)
                userIdx += 1
            # append the day's data
            data.append(dayOfData)
            # reset userIdx
            userIdx = 0
            # set the new day
            day = row["time"]
            # reset the day's data for the next day
            dayOfData = [day]
            # DEBUG
            # print(myData)
            # print(len(USERS))
            # print(row["user_id"])
            # print(USERS[userIdx])
            # print(USERS[userIdx]["user_id"])

        while USERS[userIdx]["user_id"] != row["user_id"]:
            dayOfData.append(None)
            userIdx += 1

        dayOfData.append(row["value"])
        dataPresent[userIdx] = True
        userIdx += 1

    # finish the rest of the users
    while userIdx < numUsers:
        dayOfData.append(None)
        userIdx += 1

    # append the day's data
    data.append(dayOfData)

    # remove users with no data
    for i, isDataPresent in reversed(list(enumerate(dataPresent))):
        # if that user does not have data, remove their column
        if not isDataPresent:
            # add one because the first element is a date
            idx = i + 1
            for day in data:
                del day[idx]

    """ CONVERT SQL QUERY DICTS INTO TABLE FOR GOOGLE CHART API USE

                    TABLE FORMAT:

                    'Day'       |   'user#1'    |   ...
                    -----------------------------------
                    YYYY-MM-DD  |   INT         |   ...
                    -----------------------------------
                    .
                    .
                    .
    """
    return data

def addgoal(data, goal):
    # Add "Goal" as 1st user
    # Set Goal's values in first and last data rows = goal
    data[0].insert(1, "Goal")
    data[1].insert(1, goal)

    if len(data) > 2:
        data[-1].insert(1, goal)
        for i in range(2, len(data) - 1):
            data[i].insert(1, None)
    return data

def projectwin(data, typ):

    if len(data[0]) > 2:
        # Transpose table:
        # 0th row is dates.
        # Subsequent rows are values for each user.
        # Ignore 1st column (user names etc)
        dataT = np.transpose(data)
        DAYS = dataT[0][1:]
        winner = ""
        winnerp = []
        initial = 0 if typ == "1" else 100
        winning = initial

        # DAYS values represent numerical day values
        for i, day in enumerate(DAYS):
            day = datetime.fromisoformat(day).timestamp()
            DAYS[i] = int(day)

        # x = day number
        # y = user data
        # For each user, clean up x,y data by removing None values.
        # Ignore 1st row (goal values).
        for user in dataT[2:]:
            y = user[1:]
            x = DAYS
            for i, datum in reversed(list(enumerate(y))):
                if datum == None:
                    x = np.delete(x, i)
                    y = np.delete(y, i)

            # Check polyfit with degree number of terms. Save polyfit and user info if this is winning user so far.
            if len(x) > 1:
                degree = 3
                c = np.polynomial.polynomial.polyfit(x.astype(float), y.astype(float),degree)

                # Evaluate each user at last day for apples to apples comparison
                check = np.polynomial.polynomial.polyval(DAYS[-1], c)

                if (typ=="1" and check > winning) or (typ=="2" and check < winning):
                    winner = user[0]
                    winnerp = c
                    winning = check

        if winning != initial:
            data[0].append(f"go {winner} go!")
            # data[1].append(np.polynomial.polynomial.polyval(datetime.fromisoformat(data[1][0]).timestamp(), winnerp))
            # data[-1].append(np.polynomial.polynomial.polyval(datetime.fromisoformat(data[-1][0]).timestamp(), winnerp))
            for i in range(1, len(data)):
                data[i].append(np.polynomial.polynomial.polyval(datetime.fromisoformat(data[i][0]).timestamp(), winnerp))
        return data
    else:
        return data