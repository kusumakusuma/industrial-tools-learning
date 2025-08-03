file_path = "/home/hsk/industrial-tools-learning/daily-exercises/reliability_report1.txt"

class FailureEvent:
    def __init__(self, equipment, date, issue):
        self.equipment = equipment
        self.date = date
        self.issue = issue

    def is_critical(self):
        keywords = ["explosion", "fire", "overheat", "rupture"]
        return any(word in self.issue.lower() for word in keywords)

    def summary(self):
        return f"{self.equipment} failed on {self.date}: {self.issue}"


events = []

with open(file_path, "r") as file:
    for line in file:
        parts = line.strip().split(" - ")
        if len(parts) == 3:
            equipment = parts[0].strip("[]")
            date = parts[1]
            issue = parts[2]
            event = FailureEvent(equipment, date, issue)
            events.append(event)

# Show summaries of only critical failures
print("\n🔴 Critical Failures:")
for event in events:
    if event.is_critical():
        print(event.summary())
