from cs50 import SQL
from datetime import datetime

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


x = '2021-03-29'
# day = datetime.strptime(x,"%Y-%m-%d")
day = datetime.fromisoformat(x)
print(day)
day = datetime.timestamp(day)
print(day)