from cs50 import SQL

# x = 4
# y = 9
# x=x^y
# y=x^y
# x=x^y
# print(x)
# print(y)

# nums = [2, 3, 5, 4, 2, 4, 5]
# single = nums[0]
# for i in range(1, len(nums)):
#     single ^= nums[i]
# print(single)


db = SQL("sqlite:///workout.db")
user = 3

GROUPS = db.execute("SELECT group_name, group_num, type, start FROM groups WHERE group_num IN (SELECT group_num FROM registry WHERE user_id = ?)", user)
GROUP = GROUPS[2]
USERS = db.execute("SELECT user_id, name FROM registry JOIN users ON registry.user_id = users.id WHERE group_num = ?", GROUP['group_num'])
print(GROUP, USERS)
# TODO
# fix format of start dates recorded in groups DB table to be YYYY-MM-DD
START = GROUP['start']
START = START[:10]
data = [["Day"], [START]]

for USER in USERS:
    DATA = db.execute("SELECT value, time FROM data WHERE (user_id, type) = (?, ?) AND time >= (?) ORDER BY time", USER['user_id'], GROUP['type'], START)
    if len(DATA) == 0:
        continue

    data[0].append(USER['name']) # add username to column title
    i = 1
    for item in DATA:
        # item is a later date than everything else in data
        if i == len(data):
            newrow = [item['time']]
            for j in range(1, len(data[0]) - 1):
                newrow.append(None)
            newrow.append(item['value'])
            data.insert(i+1,newrow)
            i += 1

        while i < len(data):
            if item['time'] > data[i][0] and i+1 == len(data) or (item['time'] > data[i][0] and item['time'] < data[i+1][0]):
                # Insert new row (new date)
                # sets value for all other users to null
                # no user data for this row (need to check if it has been done already)
                newrow = [item['time']]
                for j in range(1, len(data[0]) - 1):
                    newrow.append(None)
                newrow.append(item['value'])
                data.insert(i+1,newrow)
                if len(data[i]) < len(data[0]):
                    data[i].append(None)
                i += 1
                break
            if item['time'] == data[i][0]:
                #add user data into existing row
                data[i].append(item['value'])
                i += 1
                break
            else:
                # no user data for this row (need to check if it has been done already)
                if len(data[i]) < len(data[0]):
                    data[i].append(None)
                i += 1
    # if you run out of data, set None user data for rest of the rows (need to check if it has been done already)
    while i < len(data):
        if len(data[i]) < len(data[0]):
            data[i].append(None)
        i += 1

print(data)