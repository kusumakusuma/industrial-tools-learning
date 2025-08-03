# What Are Lambda Functions?
# Lambda functions are small, anonymous (unnamed) functions defined using the lambda keyword. 
# They are useful for short, one-off operations without needing a full function definition.

# Example 1: Convert sensor readings to millivolts
# Sensor readings from multiple sensors (in volts)
# Imagine you have sensor readings from multiple sensors, and you need to process them.
sensor_readings = [3.5, 4.2, 2.8, 5.1, 3.9]

# Lambda Function: Convert readings to millivolts (multiply by 1000)
millivolts = list(map(lambda x: x * 1000, sensor_readings))
print("Sensor Readings in Millivolts:", millivolts)

# Filter: Remove readings below 3.0 volts
filtered_readings = list(filter(lambda x: x >= 3.0, sensor_readings))
print("Filtered Readings (>= 3.0V):", filtered_readings)

# Reduce: Calculate the total voltage
from functools import reduce
total_voltage = reduce(lambda x, y: x + y, sensor_readings)
print("Total Voltage:", total_voltage)