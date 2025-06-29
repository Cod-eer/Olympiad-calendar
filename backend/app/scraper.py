import os
import re
from openai import OpenAI
from dotenv import load_dotenv
import requests

def transform(url):
    if url[0] != 'h':
        url = "https://www." + url
    return url


def get_data_from_website(url):
    # 1. Fetch website content
    url = transform(url)
    html = requests.get(url).text

    # Optional: Clean it using BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()


    load_dotenv()
    # Initialize openAI model
    token = os.environ["GITHUB_KEY"]
    endpoint = "https://models.github.ai/inference"
    model = "openai/gpt-4.1-mini"

    client = OpenAI(
        base_url=endpoint,
        api_key=token,
    )

    system_msg = {
        "role": "system",
        "content": (
            "You are an intelligent extraction assistant designed to analyze and summarize academic competition webpages. "
            "Your task is to identify and return the following categories from the given text:\n\n"
            "1. All important **DATES** (e.g. registration deadlines, submission dates, awards ceremonies)\n"
            "2. Any **BILLING or entry fees**\n"
            "3. **PARTICIPATION REQUIREMENTS** (e.g. age, grade level, citizenship, educational background)\n"
            "4. **ORGANIZERS** and partners of the olympiad, or hosting institutions\n"
            "5. **REWARDS FOR WINNERS** (e.g. cash prizes, scholarships, publication opportunities, certificates)\n\n"
            "Respond in clearly separated sections. If any section is not mentioned in the input, say: 'Not specified'. "
            "Use concise and clean formatting. Do not invent or infer details beyond the text."
        )
    }

    user_msg = {
        "role": "user",
        "content": (
            "Here is the content of a competition webpage:\n\n"
            f"{text}\n\n"
            "Please extract and return:\n"
            "1. All important dates\n"
            "2. Billing or entry fee information\n"
            "3. Participation requirements\n"
            "4. Organizers and partners of the olympiad, or hosting institutions\n"
            "5. Rewards for winners"
        )
    }


    #chat request

    response = client.chat.completions.create(
        messages=[system_msg, user_msg],
        temperature=0.5,
        model=model,
    )
    extracted_data = response.choices[0].message.content


    def parse_sections(raw_text):
        # Split sections using markdown headings like **1. TITLE**
        split_sections = re.split(r"\*\*\d+\.\s+(.+?)\*\*", raw_text)

        # Create dictionary
        parsed = {}
        for i in range(1, len(split_sections), 2):
            title = split_sections[i].strip().lower()  # normalize key
            content = split_sections[i + 1].strip()
            items = re.findall(r"- (.+)", content)
            parsed[title] = items
        return parsed

    # Example usage
    parsed = parse_sections(extracted_data)

    # Access with normalized keys
    dates = parsed.get("important dates", [])
    billing = parsed.get("billing or entry fees", [])
    requirements = parsed.get("participation requirements", [])
    organizers = parsed.get("organizers or hosting institutions", [])
    rewards = parsed.get("rewards for winners", [])
    return {
        "dates" : dates,
        "billing" : billing,
        "requirements" : requirements,
        "organizers" : organizers,
    }

