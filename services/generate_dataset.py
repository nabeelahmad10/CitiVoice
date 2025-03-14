import csv
import random

# Sample data for each domain
legal_inputs = [
    "I need help with a rental agreement dispute.",
    "What are my rights as a consumer?",
    "How do I file a complaint against a contractor?",
    "Can you explain the terms of my lease?",
    "What legal action can I take for breach of contract?"
]
legal_responses = [
    "Based on your situation, please review your rental agreement and consult a lawyer. This is not legal advice.",
    "As a consumer, you have rights under the Consumer Protection Act, but please verify your case specifics.",
    "To file a complaint, gather your documents and contact your local consumer court.",
    "I can provide general legal information, but consult a qualified attorney for personalized advice.",
    "There might be grounds for legal action. Please review the contract and seek professional advice."
]

medical_inputs = [
    "I have a headache and fever.",
    "What should I do if I experience chest pain?",
    "I feel anxious and stressed.",
    "My stomach hurts after eating.",
    "I'm feeling extremely tired."
]
medical_responses = [
    "It sounds like a mild infection; please rest, stay hydrated, and monitor your symptoms.",
    "Chest pain can be serious. Please seek emergency care immediately.",
    "Consider relaxation techniques; if anxiety persists, consult a mental health professional.",
    "If your stomach pain continues, please see a doctor for further evaluation.",
    "Fatigue can be caused by many factors. Please consult a physician if it worsens."
]

gov_inputs = [
    "How do I apply for a passport?",
    "Where can I check my voter registration status?",
    "I want to file a grievance about public services.",
    "How do I update my address on my driving license?",
    "What documents do I need for an income certificate?"
]
gov_responses = [
    "To apply for a passport, fill out the online application and schedule an appointment at your local office.",
    "You can check your voter registration status on the Election Commission website or at your local election office.",
    "Please provide detailed information about your grievance so that we can guide you through the filing process.",
    "To update your address, submit the required documents with an application at your local RTO.",
    "For an income certificate, you'll need proof of income, address proof, and a completed application form."
]

domains = ["Legal", "Medical", "Government"]

# Open file for writing
with open("chatbot_dataset.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    # Write header row
    writer.writerow(["domain", "user_input", "bot_response"])
    # Generate 10,000 rows of data
    for _ in range(10000):
        domain = random.choice(domains)
        if domain == "Legal":
            user_input = random.choice(legal_inputs)
            bot_response = random.choice(legal_responses)
        elif domain == "Medical":
            user_input = random.choice(medical_inputs)
            bot_response = random.choice(medical_responses)
        elif domain == "Government":
            user_input = random.choice(gov_inputs)
            bot_response = random.choice(gov_responses)
        writer.writerow([domain, user_input, bot_response])

print("Dataset generated: chatbot_dataset.csv")
