# Defining and calling a function
def greet(name):
    return f"Hello, {name}!"

# Calling the function
message = greet("Alice")
print(message)  # Output: Hello, Alice!

# Dictionaries
student = {
    "name": "Alice",
    "age": 25,
    "is_student": True
}

# Accessing values
print(student["name"])  # Output: Alice

# Adding a new key-value pair
student["grade"] = "A"
print(student)  # Output: {'name': 'Alice', 'age': 25, 'is_student': True, 'grade': 'A'}

# Updating a value
student["age"] = 26
print(student)  # Output: {'name': 'Alice', 'age': 26, 'is_student': True, 'grade': 'A'}