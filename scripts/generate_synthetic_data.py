# Synthetic Cybercrime Complaint Generator
# Generates 50+ realistic cybercrime complaints for testing and demo

import random
import uuid
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import create_complaint, get_db, init_db

# Crime type templates with variations
CRIME_TEMPLATES = {
    "UPI Fraud": [
        "I received a call from someone claiming to be from {bank} customer care. They said my account was blocked and asked me to share OTP to verify. I shared the OTP and ₹{amount} was debited from my account.",
        "A person posing as a {bank} executive called me saying my KYC was pending. They took remote access of my phone using {app} and transferred ₹{amount}.",
        "I received an SMS with a link claiming I won ₹50,000. When I clicked and entered my details, ₹{amount} was stolen from my UPI account.",
        "Someone contacted me on {platform} selling {item} at a very low price. They sent a QR code for payment, but when I scanned it, ₹{amount} was debited instead.",
        "I got a call from someone claiming to be from {company} offering a refund of ₹{small_amount}. They sent a link to my phone and when I clicked it, they stole ₹{amount}."
    ],
    "Phishing Attack": [
        "I received an email that looked exactly like it was from {bank}. It asked me to update my password urgently. After I entered my credentials on their fake website, my account was compromised and ₹{amount} was stolen.",
        "Got a message on {platform} from someone pretending to be {government} asking for PAN/Aadhaar link update. They collected my banking details and withdrew ₹{amount}.",
        "Received a WhatsApp message with a link claiming to be a {festival} offer from {company}. After clicking, all my saved passwords were compromised.",
        "I clicked on a fake {bank} website from Google search results. The website looked identical to the real one. Lost ₹{amount} after entering login credentials.",
        "Received an email about my {service} subscription expiring. Clicked the 'renew' button which took me to a phishing site that stole my card details."
    ],
    "Investment Fraud": [
        "I was added to a WhatsApp group called '{group_name}' where they showed fake profit screenshots. I invested ₹{amount} in their 'guaranteed returns' scheme and lost everything.",
        "Found an investment platform called {fake_platform} through Instagram ads. Invested ₹{amount} showing daily 5% returns. When I tried to withdraw, they asked for more money and blocked me.",
        "Someone on LinkedIn claimed to be from {company} and offered insider trading tips. I invested ₹{amount} through their app and all money was lost.",
        "Joined a Telegram group for cryptocurrency trading signals. Deposited ₹{amount} on their recommended exchange which turned out to be fake.",
        "Met someone on {dating_app} who convinced me to invest in their forex trading platform. Lost ₹{amount} in this romance-investment scam."
    ],
    "Job Fraud": [
        "Applied for work-from-home data entry job. They asked me to pay ₹{amount} for registration and training kit. Never received any job or materials.",
        "Got selected for {company} through a fake HR email. Asked to pay ₹{amount} for laptop security deposit. Later found the interview was conducted by fraudsters.",
        "Saw job posting on {platform} for {position} at ₹{salary}/month. After paying ₹{amount} for background verification, they stopped all communication.",
        "Received call claiming I was selected for government job. Asked to pay ₹{amount} for appointment letter and joining fee. It was all fake.",
        "Applied through {website} for international job. Paid ₹{amount} for visa processing. The agency disappeared after taking money."
    ],
    "Online Shopping Fraud": [
        "Ordered {item} from {platform} but received an empty box / completely different product. Seller disappeared and platform refused refund. Lost ₹{amount}.",
        "Found {item} at 70% discount on Instagram shop. Paid ₹{amount} via UPI but never received the product. Seller blocked me.",
        "Purchased {item} from a fake website that looked like {brand}'s official site. Paid ₹{amount} and received nothing.",
        "Saw ad for branded {item} on Facebook. Paid ₹{amount} through payment link. Received low-quality fake product.",
        "Bought {item} from WhatsApp seller who showed videos of genuine products. Paid ₹{amount} and received cheap counterfeit."
    ],
    "Social Engineering": [
        "Someone called pretending to be my {relative} saying they had an accident and urgently needed ₹{amount}. I transferred the money before realizing it was a scam.",
        "Received call from 'Police Station' saying my Aadhaar was misused for crime. They demanded ₹{amount} to clear my name, threatening arrest.",
        "Got video call from person who recorded me without consent and started blackmailing. Paid ₹{amount} out of fear before blocking them.",
        "Someone impersonating as {bank} relationship manager convinced me to share screen. They transferred ₹{amount} from my account.",
        "Person claiming to be from Electricity Board said my connection was about to be cut. Paid ₹{amount} to 'keep it active'."
    ],
    "Identity Theft": [
        "Someone created a fake Aadhaar using my photo and took a loan of ₹{amount} in my name from {bank}. My CIBIL score is now affected.",
        "Found out my PAN details were used to file fake ITR and claim refund of ₹{amount}. The money went to a fraudster's account.",
        "Multiple credit cards were issued using my forged documents. Total fraud amount is ₹{amount}. I never applied for these cards.",
        "My social media account was hacked and used to ask friends for money. They collected ₹{amount} before I regained access.",
        "My delivery address was used to purchase expensive electronics worth ₹{amount}. Now I'm receiving collection calls."
    ],
    "Cyber Extortion": [
        "Received email claiming they have my private photos/videos and demanding ₹{amount} in Bitcoin. Threatening to send to all contacts.",
        "My computer was infected with ransomware. All files are encrypted and they're demanding ₹{amount} to decrypt.",
        "Someone is threatening to reveal my browsing history to my employer unless I pay ₹{amount}.",
        "After online dating, person is threatening to share our private chats unless I pay ₹{amount}.",
        "Received threat message saying they have installed spyware on my laptop and demanding ₹{amount}."
    ]
}

# Variables for template filling
BANKS = ["SBI", "HDFC", "ICICI", "Axis Bank", "Bank of Baroda", "PNB", "Kotak", "Yes Bank"]
PLATFORMS = ["WhatsApp", "Telegram", "Instagram", "Facebook", "LinkedIn", "Twitter"]
APPS = ["AnyDesk", "TeamViewer", "Quick Support"]
COMPANIES = ["Amazon", "Flipkart", "Google", "Microsoft", "Paytm", "PhonePe", "IRCTC", "Zomato"]
ITEMS = ["iPhone", "laptop", "TV", "gold jewelry", "gaming console", "camera", "watch", "shoes", "furniture", "air conditioner"]
GOVERNMENT = ["Income Tax", "EPFO", "Passport Seva", "RTO", "Electricity Board"]
FESTIVALS = ["Diwali", "Holi", "New Year", "Independence Day"]
SERVICES = ["Netflix", "Amazon Prime", "Hotstar", "Spotify"]
GROUP_NAMES = ["Profit Makers Elite", "10X Returns Daily", "Crypto Millionaires", "Stock Market Genius", "Binary Options VIP"]
FAKE_PLATFORMS = ["CryptoMax", "TradePro", "InvestSure", "MoneyTree", "FastReturns"]
DATING_APPS = ["Tinder", "Bumble", "Hinge", "OkCupid"]
JOB_PLATFORMS = ["Naukri", "LinkedIn", "Indeed", "Monster"]
JOB_POSITIONS = ["Data Entry Operator", "Customer Support Executive", "Social Media Manager", "Content Writer"]
RELATIVES = ["son", "daughter", "nephew", "niece", "cousin", "friend"]
BRANDS = ["Nike", "Adidas", "Apple", "Samsung", "Sony"]

def generate_synthetic_complaint():
    """Generate a single random complaint."""
    
    # Pick random crime type and template
    crime_type = random.choice(list(CRIME_TEMPLATES.keys()))
    template = random.choice(CRIME_TEMPLATES[crime_type])
    
    # Generate random amount based on crime type
    if crime_type in ["Investment Fraud", "Identity Theft"]:
        amount = random.choice([50000, 75000, 100000, 150000, 200000, 300000, 500000])
    elif crime_type in ["UPI Fraud", "Phishing Attack"]:
        amount = random.choice([5000, 10000, 15000, 25000, 35000, 50000, 75000, 100000])
    else:
        amount = random.choice([2000, 5000, 10000, 20000, 30000, 50000])
    
    # Fill template
    complaint_text = template.format(
        bank=random.choice(BANKS),
        platform=random.choice(PLATFORMS),
        app=random.choice(APPS),
        company=random.choice(COMPANIES),
        item=random.choice(ITEMS),
        government=random.choice(GOVERNMENT),
        festival=random.choice(FESTIVALS),
        service=random.choice(SERVICES),
        group_name=random.choice(GROUP_NAMES),
        fake_platform=random.choice(FAKE_PLATFORMS),
        dating_app=random.choice(DATING_APPS),
        website=random.choice(JOB_PLATFORMS),
        position=random.choice(JOB_POSITIONS),
        salary=random.choice([15000, 25000, 35000, 50000]),
        relative=random.choice(RELATIVES),
        brand=random.choice(BRANDS),
        amount=f"{amount:,}",
        small_amount=random.choice([500, 1000, 1500])
    )
    
    # Generate severity score (1-5 based on amount)
    if amount >= 200000:
        severity = round(random.uniform(4.0, 5.0), 1)
    elif amount >= 100000:
        severity = round(random.uniform(3.5, 4.5), 1)
    elif amount >= 50000:
        severity = round(random.uniform(2.5, 3.5), 1)
    elif amount >= 20000:
        severity = round(random.uniform(2.0, 3.0), 1)
    else:
        severity = round(random.uniform(1.0, 2.5), 1)
    
    return {
        "crime_type": crime_type,
        "complaint_text": complaint_text,
        "financial_loss": amount,
        "severity_score": severity
    }


def generate_narrative_summary(complaint_text: str, crime_type: str) -> str:
    """Generate a brief summary of the complaint."""
    # Simple summarization (in production, use AI)
    words = complaint_text.split()
    if len(words) > 30:
        summary = " ".join(words[:30]) + "..."
    else:
        summary = complaint_text
    return f"{crime_type}: {summary}"


def get_severity_color(score: float) -> str:
    """Get color based on severity score."""
    if score >= 4:
        return "red"
    elif score >= 3:
        return "orange"
    elif score >= 2:
        return "yellow"
    else:
        return "green"


def generate_all_synthetic_data(count: int = 60):
    """Generate and save synthetic complaints to database."""
    
    print(f"Generating {count} synthetic complaints...")
    init_db()  # Ensure database is initialized
    
    # Generate test user IDs
    test_user_ids = [str(uuid.uuid4()) for _ in range(10)]
    
    statuses = ["pending", "ongoing", "solved"]
    status_weights = [0.4, 0.3, 0.3]  # 40% pending, 30% ongoing, 30% solved
    
    generated = 0
    
    for i in range(count):
        complaint = generate_synthetic_complaint()
        user_id = random.choice(test_user_ids)
        status = random.choices(statuses, weights=status_weights)[0]
        
        # Generate narrative summary
        narrative = generate_narrative_summary(
            complaint["complaint_text"],
            complaint["crime_type"]
        )
        
        try:
            complaint_id = create_complaint(
                user_id=user_id,
                complaint_text=complaint["complaint_text"],
                narrative_summary=narrative,
                crime_type=complaint["crime_type"],
                financial_loss=complaint["financial_loss"],
                severity_score=complaint["severity_score"],
                severity_color=get_severity_color(complaint["severity_score"])
            )
            
            # Update status if not pending
            if status != "pending":
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE complaints SET status=? WHERE complaint_id=?",
                    (status, complaint_id)
                )
                conn.commit()
                conn.close()
            
            generated += 1
            print(f"  [{generated}/{count}] Created: {complaint_id} - {complaint['crime_type']}")
            
        except Exception as e:
            print(f"  Error creating complaint: {e}")
    
    print(f"\n✅ Generated {generated} synthetic complaints!")
    
    # Generate embeddings for all complaints
    print("\nGenerating embeddings for similarity search...")
    try:
        from api.similarity import process_all_complaints, SENTENCE_TRANSFORMER_AVAILABLE
        
        if SENTENCE_TRANSFORMER_AVAILABLE:
            conn = get_db()
            count = process_all_complaints(conn)
            conn.close()
            print(f"✅ Generated embeddings for {count} complaints")
        else:
            print("⚠️ sentence-transformers not installed. Skipping embeddings.")
            print("   Install with: pip install sentence-transformers")
    except ImportError as e:
        print(f"⚠️ Could not generate embeddings: {e}")
    
    return generated


if __name__ == "__main__":
    import sys
    
    count = 60
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    
    generate_all_synthetic_data(count)
