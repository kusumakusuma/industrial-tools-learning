# What Are with Statements?
# The with statement is used to simplify resource management, such as opening and closing files or database connections. 
# It ensures that resources are properly cleaned up after use, even if an error occurs.

# What Are Context Managers?
# A context manager is an object that defines the methods __enter__ and __exit__, which handle setup and cleanup tasks.


file_path = "daily-exercises/reliability_report1.txt"


with open(file_path, "r") as file:
    for line in file:
        parts = line.strip().split(" - ")
        equipment = parts[0].strip("[]")
        date = parts[1]
        issue = parts[2]
        print(f"{equipment} had an issue on {date}: {issue}")      