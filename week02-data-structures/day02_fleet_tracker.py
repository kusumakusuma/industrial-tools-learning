"""
Day 2: Fleet Reliability Tracker
Goal: Track multiple equipment using lists and dictionaries
New concepts: Data structures, CSV handling, validation
"""

import csv
import datetime
from typing import Dict, List

# Color codes for better visualization
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# LESSON 1: Dictionaries - Organizing equipment data
def create_equipment_record() -> Dict:
    """Create a new equipment record with user input"""
    print(f"\n{BLUE}=== Add New Equipment ==={RESET}")
    
    # Get equipment details
    name = input("Equipment name: ").strip()
    if not name:
        print(f"{RED}Error: Equipment name cannot be empty!{RESET}")
        return None
    
    try:
        # LESSON: Data validation
        total_hours = float(input("Total operating hours: "))
        uptime_hours = float(input("Uptime hours: "))
        
        # Validate uptime <= total hours
        if uptime_hours > total_hours:
            print(f"{RED}Error: Uptime cannot exceed total hours!{RESET}")
            return None
            
        failures = int(input("Number of failures: "))
        if failures < 0:
            print(f"{RED}Error: Failures cannot be negative!{RESET}")
            return None
            
    except ValueError:
        print(f"{RED}Error: Please enter valid numbers!{RESET}")
        return None
    
    # Calculate metrics
    downtime = total_hours - uptime_hours
    availability = (uptime_hours / total_hours * 100) if total_hours > 0 else 0
    mtbf = uptime_hours / failures if failures > 0 else float('inf')
    mttr = downtime / failures if failures > 0 else 0
    
    # LESSON 2: Dictionary - Store related data together
    equipment = {
        'name': name,
        'total_hours': total_hours,
        'uptime_hours': uptime_hours,
        'failures': failures,
        'downtime': downtime,
        'availability': availability,
        'mtbf': mtbf,
        'mttr': mttr,
        'date_added': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    return equipment

# LESSON 3: Lists - Store multiple equipment
def display_fleet_summary(fleet: List[Dict]):
    """Display summary of all equipment in fleet"""
    if not fleet:
        print(f"\n{YELLOW}No equipment in fleet yet!{RESET}")
        return
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}FLEET RELIABILITY SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{'Equipment':<20} {'Availability':<15} {'MTBF':<15} {'Status':<15}")
    print("-" * 70)
    
    # Calculate fleet-wide metrics
    total_uptime = 0
    total_hours = 0
    total_failures = 0
    
    for eq in fleet:
        # Status based on availability
        if eq['availability'] >= 95:
            status = f"{GREEN}GOOD{RESET}"
        elif eq['availability'] >= 90:
            status = f"{YELLOW}FAIR{RESET}"
        else:
            status = f"{RED}POOR{RESET}"
        
        # Display each equipment
        mtbf_display = f"{eq['mtbf']:.1f}h" if eq['mtbf'] != float('inf') else "No failures"
        print(f"{eq['name']:<20} {eq['availability']:<15.2f}% {mtbf_display:<15} {status}")
        
        # Accumulate for fleet metrics
        total_uptime += eq['uptime_hours']
        total_hours += eq['total_hours']
        total_failures += eq['failures']
    
    # Fleet-wide statistics
    fleet_availability = (total_uptime / total_hours * 100) if total_hours > 0 else 0
    fleet_mtbf = total_uptime / total_failures if total_failures > 0 else float('inf')
    
    print("-" * 70)
    print(f"{BLUE}Fleet Average:{RESET}")
    print(f"  Overall Availability: {fleet_availability:.2f}%")
    print(f"  Fleet MTBF: {fleet_mtbf:.1f} hours" if fleet_mtbf != float('inf') else "  Fleet MTBF: No failures")
    print(f"  Total Equipment: {len(fleet)}")

# LESSON 4: File I/O with CSV
def save_fleet_to_csv(fleet: List[Dict], filename: str = 'fleet_data.csv'):
    """Save fleet data to CSV file"""
    if not fleet:
        print(f"{YELLOW}No data to save!{RESET}")
        return
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            # Define CSV columns
            fieldnames = ['name', 'total_hours', 'uptime_hours', 'failures', 
                         'availability', 'mtbf', 'mttr', 'date_added']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write each equipment record
            for equipment in fleet:
                writer.writerow({
                    'name': equipment['name'],
                    'total_hours': equipment['total_hours'],
                    'uptime_hours': equipment['uptime_hours'],
                    'failures': equipment['failures'],
                    'availability': f"{equipment['availability']:.2f}",
                    'mtbf': f"{equipment['mtbf']:.2f}" if equipment['mtbf'] != float('inf') else 'inf',
                    'mttr': f"{equipment['mttr']:.2f}",
                    'date_added': equipment['date_added']
                })
        
        print(f"{GREEN}✓ Fleet data saved to {filename}{RESET}")
        
    except Exception as e:
        print(f"{RED}Error saving file: {e}{RESET}")

def load_fleet_from_csv(filename: str = 'fleet_data.csv') -> List[Dict]:
    """Load fleet data from CSV file"""
    fleet = []
    
    try:
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                equipment = {
                    'name': row['name'],
                    'total_hours': float(row['total_hours']),
                    'uptime_hours': float(row['uptime_hours']),
                    'failures': int(row['failures']),
                    'downtime': float(row['total_hours']) - float(row['uptime_hours']),
                    'availability': float(row['availability']),
                    'mtbf': float(row['mtbf']) if row['mtbf'] != 'inf' else float('inf'),
                    'mttr': float(row['mttr']),
                    'date_added': row['date_added']
                }
                fleet.append(equipment)
        
        print(f"{GREEN}✓ Loaded {len(fleet)} equipment records from {filename}{RESET}")
        
    except FileNotFoundError:
        print(f"{YELLOW}No saved data found. Starting fresh!{RESET}")
    except Exception as e:
        print(f"{RED}Error loading file: {e}{RESET}")
    
    return fleet

# LESSON 5: Main program with menu system
def main():
    """Main program loop"""
    print(f"{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}Fleet Reliability Tracker - Day 2{RESET}")
    print(f"{BLUE}{'='*50}{RESET}")
    
    # Load existing data
    fleet = load_fleet_from_csv()
    
    while True:
        print(f"\n{YELLOW}=== MENU ==={RESET}")
        print("1. Add new equipment")
        print("2. View fleet summary")
        print("3. Save fleet data")
        print("4. Find worst performer")
        print("5. Exit")
        print("6. Best Performer")
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            equipment = create_equipment_record()
            if equipment:
                fleet.append(equipment)
                print(f"{GREEN}✓ Equipment '{equipment['name']}' added to fleet!{RESET}")
                
        elif choice == '2':
            display_fleet_summary(fleet)
            
        elif choice == '3':
            save_fleet_to_csv(fleet)
            
        elif choice == '4':
            # BONUS: Find worst performer
            if fleet:
                worst = min(fleet, key=lambda x: x['availability'])
                print(f"\n{RED}Worst Performer: {worst['name']}{RESET}")
                print(f"Availability: {worst['availability']:.2f}%")
                print(f"Failures: {worst['failures']}")
                print(f"MTTR: {worst['mttr']:.2f} hours")
            else:
                print(f"{YELLOW}No equipment in fleet!{RESET}")
                
        elif choice == '5':
            # Auto-save on exit
            if fleet and input("\nSave before exit? (y/n): ").lower() == 'y':
                save_fleet_to_csv(fleet)
            print(f"\n{GREEN}Thank you for using Fleet Tracker!{RESET}")
            break
        elif choice == '6':
            if fleet:
                best = max(fleet, key=lambda x: x['availability'])
                print(f"\n{GREEN}Best Performer: {best['name']}{RESET}")
                print(f"Availability: {best['availability']:.2f}%")    
        else:
            print(f"{RED}Invalid option! Please try again.{RESET}")

# Key Learning Points:
# 1. Dictionaries store related data together (equipment record)
# 2. Lists hold multiple items (fleet of equipment)
# 3. CSV files provide persistent storage
# 4. Data validation prevents errors
# 5. Functions organize code into reusable blocks

if __name__ == "__main__":
    main()