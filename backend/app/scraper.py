import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from playwright.sync_api import sync_playwright
from openai import OpenAI
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
import time
from pprint import pprint


def transform_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://www." + url
    return url


import re


def parse_sections(raw_text: str):
    # Split using headers like NAME:, DATES:, etc.
    split_sections = re.split(r'\n?([A-Z ]+):\s*\n', raw_text.strip())
    pprint(split_sections)
    print("/n")
    parsed = {}
    for i in range(1, len(split_sections), 2):
        title = split_sections[i].strip().lower()
        content = split_sections[i + 1].strip()
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        section_items = []

        for line in lines:
            line = re.sub(r"^[-*]\s+", "", line)  # Remove leading bullet
            section_items.append(line)

        parsed[title] = section_items

    return parsed


def scrape_return_dict(url: str, token: str):
    options = Options()
    options.add_argument("--headless=new")  # Old headless mode (compatible)
    options.add_argument("--disable-gpu")  # Needed for some systems
    options.add_argument("--no-sandbox")  # For Linux servers
    options.add_argument("--window-size=1920,1080")  # Optional: set window size

    driver = webdriver.Chrome(options=options)
    url = transform_url(url)
    driver.get(url)
    time.sleep(3)
    html = driver.page_source
    # Optional: Clean it using BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    raw_text = soup.get_text()
    text = re.sub(r"[\u200b]", "", raw_text).strip()
    endpoint = "https://models.github.ai/inference"
    model = "openai/gpt-4.1-mini"
    client = OpenAI(
        base_url=endpoint,
        api_key=token,
    )
    system_msg = {
        "role": "system",
        "content": (
            """You are an intelligent extraction assistant designed to analyze and summarize academic competition webpages.

Your task is to extract and return the following categories from the provided text:

1. **NAME**
- Return only a single line with the name of the competition.

2. **DATES**
- Extract all relevant dates (e.g. registration deadlines, submission deadlines, result announcements, ceremonies).
- Return each as: dd-mm-yyyy – event description.
- If the date is in a different format, convert it to dd-mm-yyyy. If only a month/year is available, use 01 for the day.

3. **BILLING OR ENTRY FEES**
- Include any mention of costs, registration fees, or if participation is free.

4. **PARTICIPATION REQUIREMENTS**
- Include age, grade level, nationality, school level, or other restrictions.

5. **ORGANIZERS**
- Include any organizing bodies, institutional partners, sponsors, or hosts.
- Write down only the names of organizations.

6. **REWARDS FOR WINNERS**
- Include scholarships, cash prizes, certificates, publications, internships, or other awards.

Respond in clearly separated sections, using the following format:

CATEGORY_NAME (exact name):
- item 1
- item 2

If an item has subitems, shift them with a tab:
- item 1
    - item 1.1
    - item 1.2

ANSWER ONLY IN ENGLISH.

If any section is not mentioned in the text, respond with:
Not specified

Use concise and factual formatting. Do not invent or infer details not clearly stated.
"""
        ),
    }
    user_msg = {
        "role": "user",
        "content": (
            "Here is the content of a competition webpage:\n\n"
            f"{text}\n\n"
            "Please extract and return:\n"
            "1. Name of the olympiad\n"
            "2. All important dates\n"
            "3. Billing or entry fees\n"
            "4. Participation requirements\n"
            "5. Organizers and partners of the olympiad, or hosting institutions\n"
            "6. Rewards for winners"
        ),
    }
    # chat request
    response = client.chat.completions.create(
        messages=[system_msg, user_msg],
        temperature=0.5,
        model=model,
    )
    extracted_data = response.choices[0].message.content
    extracted_data = "\n" + extracted_data
    parsed = parse_sections(extracted_data)
    result = {
        "name": parsed.get("name", []),
        "dates": parsed.get("dates", []),
        "billing": parsed.get("billing or entry fees", []),
        "requirements": parsed.get("participation requirements", []),
        "organizers": parsed.get("organizers", []),
        "rewards": parsed.get("rewards for winners", []),
        "url": url,
    }
    driver.quit()
    return result

