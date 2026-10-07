# Open the file in read mode
with open("/Users/adityavikramkirtania/Desktop/PythonDataAnalytics/ImageGames/HandWritingReplicator/README.txt", "r") as file:
    # Read the entire content
    content = file.read()

# Convert the content (string) into a list of characters
char_array = list(content)

# Print the result
print(char_array)
