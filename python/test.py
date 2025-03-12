from os import path
str = path.expanduser("~")
print(str.replace("\\", "/"))