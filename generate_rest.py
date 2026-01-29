import csv
import random

# --- CONFIGURATION ---
TARGET_COUNT = 1000
current_counts = {
    "business": 170,
    "entertainment": 170,
    "health": 160
}

# --- DATA SOURCES ---
# (Reusing and expanding topics slightly for variety)

topics_business = [
    "The S&P 500 reached a new all-time high as technology stocks rallied on strong earnings reports.",
    "The Federal Reserve decided to keep interest rates steady, citing cooling inflation data.",
    "A major tech giant announced plans to acquire a leading AI startup for $50 billion.",
    "Supply chain bottlenecks are expected to ease later this year, improving manufacturing output.",
    "Oil prices climbed above $90 a barrel amidst growing geopolitical tensions in resource-rich regions.",
    "The unemployment rate held steady at 3.7%, signaling a resilient labor market despite economic headwinds.",
    "Retail giants are closing underperforming stores as consumer spending shifts increasingly to online platforms.",
    "Venture capital funding for renewable energy startups has tripled in the last quarter compared to last year.",
    "Leading automakers are aggressively expanding their electric vehicle production lines to meet government mandates.",
    "Cryptocurrency markets remained volatile as regulators debated new frameworks for digital asset oversight.",
    "Small business optimism index showed a slight decline due to concerns over rising labor costs.",
    "Global trade volume is projected to grow by 3% this year, driven by recovery in emerging markets.",
    "Corporate profits for the fiscal year exceeded analyst expectations, boosting investor sentiment.",
    "Real estate markets in major metropolitan areas are cooling down as mortgage rates remain elevated.",
    "A leading financial institution introduced a new digital banking platform to attract younger customers.",
    "Merger talks between two large telecommunications providers have stalled over antitrust concerns.",
    "The hospitality sector is seeing a strong rebound in revenue as international travel returns to pre-pandemic levels.",
    "New tariffs on imported steel are expected to impact construction costs significantly.",
    "The company's board of directors approved a share buyback program valud at $2 billion.",
    "Investors are closely watching the upcoming central bank meeting for clues on future monetary policy."
]

topics_entertainment = [
    "The new superhero blockbuster smashed opening weekend records, earning over $300 million globally.",
    "Detailed reports confirm that the celebrity couple has officially filed for divorce after five years of marriage.",
    "A chart-topping pop star announced a surprise world tour, sending fans into a digital queue frenzy.",
    "Streaming giant Netflix announced a price hike for its premium subscription tier starting next month.",
    "The highly anticipated open-world RPG game has received universal acclaim for its storytelling and graphics.",
    "Social media is buzzing about the controversial outfit worn by the actress at the Met Gala last night.",
    "A popular sitcom has been renewed for three more seasons following a surge in viewership ratings.",
    "The legendary rock band is reuniting for a final farewell tour across Europe and North America.",
    "Award season predictions are heating up as critics release their top ten lists for the year.",
    "A viral TikTok dance challenge has propelled a classic 80s hit back to the top of the music charts.",
    "Disney+ is planning to crack down on password sharing in an effort to boost subscriber revenue.",
    "The prestigious film festival honored the indie director with the Palme d'Or for their latest drama.",
    "Reality TV star launched a new cosmetics line that sold out in minutes.",
    "Concert ticket prices have reached an all-time high, sparking a government investigation.",
    "A new documentary series exposes the dark side of the fashion industry and has sparked global debate.",
    "The actor was cast as the lead villain in the upcoming sci-fi franchise reboot.",
    "Gaming tournaments are attracting sponsorships from major luxury brands as esports grows in popularity.",
    "The late-night talk show host announced their retirement after two decades on air.",
    "K-Pop group broke YouTube streaming records with their latest music video release.",
    "A famous author's bestselling fantasy novel is being adapted into a high-budget television series."
]

topics_health = [
    "H5N1 bird flu has been detected in dairy cattle, raising concerns about potential transmission to humans.",
    "New weight-loss drugs are showing promise in reducing the risk of heart attacks and strokes.",
    "Measles cases are rising globally due to declining vaccination rates in children.",
    "Researchers have identified a new genetic marker for early-onset Alzheimer's disease.",
    "Colorectal cancer screening recommended age has been lowered to 45 following a rise in cases among younger adults.",
    "The Surgeon General issued a warning about the impact of social media on youth mental health.",
    "Climate change is increasing the spread of vector-borne diseases like dengue fever and malaria.",
    "A breakthrough in gene editing therapy offers hope for patients with sickle cell anemia.",
    "Artificial intelligence is being used to analyze medical imaging and detect tumors earlier than human radiologists.",
    "Telemedicine adoption remains high post-pandemic, improving access to care for rural populations.",
    "Gut microbiome diversity is linked to improved immune system function and mental well-being.",
    "Sleep deprivation in adolescents is associated with poor academic performance and increased anxiety.",
    "Hospitals are facing critical shortages of nursing staff, impacting patient care quality.",
    "New study suggests that ultra-processed foods are linked to a higher risk of type 2 diabetes.",
    "Researchers are developing a universal flu vaccine that could provide long-lasting protection.",
    "The FDA has approved a new treatment for postpartum depression, offering faster relief for mothers.",
    "Antibiotic resistance continues to be a major global health threat, urging the need for new drugs.",
    "Wearable health trackers are proving effective in monitoring chronic conditions like hypertension.",
    "Public health officials emphasize the importance of booster shots for maintaining immunity against COVID-19 variants.",
    "A new blood test shows potential for detecting multiple types of cancer at early stages."
]

variations = [
    "Recent reports indicate that ",
    "Experts are discussing how ",
    "Breaking news: ",
    "It is widely believed that ",
    "New data suggests ",
    "The community is reacting to news that ",
    "A significant development: ",
    "Analysts confirm that ",
    "Sources close to the matter say ",
    "In a major announcement, "
]

adjectives = ["incredible", "shocking", "unprecedented", "major", "minor", "significant", "worrying", "promising", "historic", "controversial"]

# --- GENERATOR FUNCTION ---
def generate_batch(category, current_count, topics_list):
    needed = TARGET_COUNT - current_count
    if needed <= 0:
        return []
    
    generated_rows = []
    for i in range(needed):
        topic = random.choice(topics_list)
        variation = random.choice(variations)
        adj = random.choice(adjectives)
        
        # Construct sentence
        text = f"{variation}{topic[0].lower() + topic[1:]}"
        
        # Add some random detail to ensure uniqueness
        text += f" This is considered a {adj} development by many within the {category} sector."
        
        if random.random() > 0.5:
             text += " Further updates are expected later this week."
        
        generated_rows.append([category, text])
    
    return generated_rows

# --- MAIN EXECUTION ---
all_new_data = []

print(f"Generating data to reach {TARGET_COUNT} items per category...")

# Business
business_data = generate_batch("business", current_counts["business"], topics_business)
print(f"Generated {len(business_data)} business items.")
all_new_data.extend(business_data)

# Entertainment
ent_data = generate_batch("entertainment", current_counts["entertainment"], topics_entertainment)
print(f"Generated {len(ent_data)} entertainment items.")
all_new_data.extend(ent_data)

# Health
health_data = generate_batch("health", current_counts["health"], topics_health)
print(f"Generated {len(health_data)} health items.")
all_new_data.extend(health_data)

# Append to CSV
with open('data/training_documents.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(all_new_data)

print(f"Successfully appended {len(all_new_data)} total rows to data/training_documents.csv")
