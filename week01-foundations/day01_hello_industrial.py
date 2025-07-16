# My First Python Program

"""
Day 1 Exercise: Basic Python and Simple Reliability Calculator
Goal: Learn variables, input/output, and basic calculations
Time: 1 hour
"""

# Your first Python program for industrial tools!
print("=" * 50)
print("Industrial Tools Learning Journey - Day 1")
print("Simple Reliability Calculator")
print("=" * 50)

# At the top of file
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'



# LESSON 1: Variables and Data Types (10 minutes)
# Variables store data that we can use later
equipment_name = "Pump-101"  # String (text)
total_hours = 720.0          # Float (decimal number)
uptime_hours = 695.5         # Float
failures = 3                 # Integer (whole number)

# Print variable values
print(f"\nEquipment: {equipment_name}")
print(f"Total Operating Hours: {total_hours}")
print(f"Uptime Hours: {uptime_hours}")
print(f"Number of Failures: {failures}")

# LESSON 2: Functions (15 minutes)
# Functions are reusable blocks of code
def calculate_mtbf(total_operating_hours, number_of_failures):
    """Calculate Mean Time Between Failures"""
    if number_of_failures == 0:
        return float('inf')  # Infinite MTBF if no failures
    return total_operating_hours / number_of_failures

def calculate_availability(uptime_hours, total_hours):
    """Calculate equipment availability percentage"""
    if total_hours == 0:
        return 0
    return (uptime_hours / total_hours) * 100

def calculate_downtime(total_hours, uptime_hours):
    """Calculate total downtime"""
    return total_hours - uptime_hours

def calculate_mttr(downtime_hours, number_of_failures):
    if number_of_failures == 0:
        return 0
    return downtime_hours / number_of_failures
    

# LESSON 3: Using Functions (10 minutes)
# Call our functions with the data
mtbf = calculate_mtbf(uptime_hours, failures)
availability = calculate_availability(uptime_hours, total_hours)
downtime = calculate_downtime(total_hours, uptime_hours)
mttr = calculate_mttr(downtime, failures)

# Use like this:
if availability >= 95:
    print(f"{GREEN}GOOD{RESET}")

# Display results
print("\n" + "-" * 30)
print("RELIABILITY METRICS:")
print("-" * 30)
print(f"MTBF: {mtbf:.2f} hours")
print(f"Availability: {availability:.2f}%")
print(f"Downtime: {downtime:.2f} hours")
print(f"MTTR: {mttr:.2f} hours")


# LESSON 4: User Input (15 minutes)
# Make it interactive!
print("\n" + "=" * 50)
print("INTERACTIVE MODE - Enter Your Equipment Data")
print("=" * 50)

# Get user input
try:
    user_equipment = input("\nEnter equipment name: ")
    user_total_hours = float(input("Enter total hours in period: "))
    user_uptime = float(input("Enter uptime hours: "))
    user_failures = int(input("Enter number of failures: "))
    
    # Calculate metrics for user input
    user_mtbf = calculate_mtbf(user_uptime, user_failures)
    user_availability = calculate_availability(user_uptime, user_total_hours)
    user_downtime = calculate_downtime(user_total_hours, user_uptime)
    user_mttr = calculate_mttr(user_downtime, user_failures)

    # Display user results
    print("\n" + "=" * 50)
    print(f"RELIABILITY REPORT FOR: {user_equipment.upper()}")
    print("=" * 50)
    print(f"Total Hours: {user_total_hours:.2f}")
    print(f"Uptime Hours: {user_uptime:.2f}")
    print(f"Downtime Hours: {user_downtime:.2f}")
    print(f"Number of Failures: {user_failures}")
    print("-" * 50)
    print(f"MTBF: {user_mtbf:.2f} hours")
    print(f"MTTR: {user_mttr:.2f} hours")
    print(f"Availability: {user_availability:.2f}%")
    print(f"Reliability Grade: ", end="")
    
    
    # Simple grading system
    if user_availability >= 99:
        print("EXCELLENT ⭐⭐⭐⭐⭐")
    elif user_availability >= 95:
        print("GOOD ⭐⭐⭐⭐")
    elif user_availability >= 90:
        print("FAIR ⭐⭐⭐")
    else:
        print("NEEDS IMPROVEMENT ⭐⭐")

    # Use like this:
    if user_availability >= 95:
        print(f"{GREEN}GOOD{RESET}")
        
except ValueError:
    print("\nError: Please enter valid numbers!")
except Exception as e:
    print(f"\nAn error occurred: {e}")

# LESSON 5: Save Results (10 minutes)
# Let's save our results to a file
print("\n" + "-" * 50)
save_choice = input("Save this report to file? (y/n): ").lower()

if save_choice == 'y':
    try:
        with open('reliability_report.txt', 'w') as file:
            file.write(f"Reliability Report\n")
            file.write(f"Equipment: {user_equipment}\n")
            file.write(f"Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            file.write(f"MTBF: {user_mtbf:.2f} hours\n")
            file.write(f"Availability: {user_availability:.2f}%\n")
        print("Report saved to 'reliability_report.txt'!")
    except:
        print("Could not save file.")

print("\n✅ Day 1 Complete! You've built your first industrial tool!")
print("📚 Tomorrow: We'll add data validation and multiple equipment tracking.")
