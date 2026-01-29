import csv

# Simple, colloquial phrases to ensure basic vocabulary coverage
colloquial_data = [
    # Health
    ["health", "I feel sick"],
    ["health", "I am sick"],
    ["health", "I have a headache"],
    ["health", "My stomach hurts"],
    ["health", "I need a doctor"],
    ["health", "Call an ambulance"],
    ["health", "I have a fever"],
    ["health", "Taking medicine"],
    ["health", "Going to the hospital"],
    ["health", "I caught the flu"],
    ["health", "Feeling ill today"],
    ["health", "Health checkup results"],
    ["health", "Pain in my back"],
    ["health", "Symptoms of cold"],
    ["health", "Prescription drugs"],
    
    # Business
    ["business", "I want to buy stocks"],
    ["business", "How is the market doing?"],
    ["business", "Investing in apple"],
    ["business", "Price of gold"],
    ["business", "Start a new company"],
    ["business", "Sales are up"],
    ["business", "Lost money on trade"],
    ["business", "Crypto is crashing"],
    ["business", "Bitcoin price"],
    ["business", "Economy is bad"],
    ["business", "Job market"],
    ["business", "Hiring new employees"],
    ["business", "Quarterly earnings"],
    ["business", "Wall street news"],
    ["business", "Finance report"],
    
    # Entertainment
    ["entertainment", "Watch a movie"],
    ["entertainment", "Listen to music"],
    ["entertainment", "Playing video games"],
    ["entertainment", "New spiderman movie"],
    ["entertainment", "Concert tickets"],
    ["entertainment", "Celebrity gossip"],
    ["entertainment", "Best netflix series"],
    ["entertainment", "Funny viral video"],
    ["entertainment", "Streaming music"],
    ["entertainment", "Hollywood stars"],
    ["entertainment", "Cinema showtimes"],
    ["entertainment", "Reading a novel"],
    ["entertainment", "Pop culture news"],
    ["entertainment", "Award show winners"],
    ["entertainment", "TV series finale"]
]

# Append to training documents
with open('data/training_documents.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(colloquial_data)

print(f"Appended {len(colloquial_data)} colloquial items to training data.")
