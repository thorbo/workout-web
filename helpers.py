import os
import requests
import urllib.parse

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
        and time >= {START}
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
            print(userIdx)
            print(userIdx == len(USERS))

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
    print(data)
    return data

def addgoal(data, goal):

    data[0].insert(1, "Goal")
    data[1].insert(1, goal)

    if len(data) > 2:
        data[-1].insert(1, goal)
        for i in range(2, len(data) - 1):
            data[i].insert(1, None)
    print(data)
    return data