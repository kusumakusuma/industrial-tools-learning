# Lists and list operations
fruits = ["apple", "banana", "cherry"]

# Accessing elements
print(fruits[0])  # Output: apple (index starts at 0)

# Adding elements
fruits.append("orange")  # Adds "orange" to the end
print(fruits)  # Output: ['apple', 'banana', 'cherry', 'orange']

# Removing elements
fruits.remove("banana")  # Removes "banana"
print(fruits)  # Output: ['apple', 'cherry', 'orange']

# Slicing
print(fruits[1:3])  # Output: ['cherry', 'orange'] (elements from index 1 to 2)

# Conditionals
age = 18

if age < 18:
    print("You are a minor.")
elif age >= 18 and age < 65:
    print("You are an adult.")
else:
    print("You are a senior citizen.")

# for loop
fruits = ["apple", "banana", "cherry"]

for fruit in fruits:
    print(fruit)

# while loop
count = 1

while count <= 5:
    print(count)
    count += 1  # Increment count by 1