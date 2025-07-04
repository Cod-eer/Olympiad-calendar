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


def parse_sections(raw_text: str):
    
    split_sections = re.split(r'\n\d+\.\s+(.*?)\n', raw_text)

    parsed = {}
    for i in range(1, len(split_sections), 2):
        title = split_sections[i].strip().lower()
        content = split_sections[i + 1].strip()
        lines = [line.rstrip() for line in content.split('\n') if line.strip()]

        # We'll parse lines to detect main lines and nested subitems (indented by 2 or more spaces)
        section_items = []
        current_main = None

        for line in lines:
            if re.match(r"^\s{2,}[-*]\s+", line):  # indented bullet line
                if current_main is not None:
                    # append nested item to current main's sublist
                    nested_item = re.sub(r"^\s*[-*]\s+", "", line)
                    if isinstance(current_main, dict):
                        current_main["subitems"].append(nested_item)
                    else:
                        # convert previous string item to dict with subitems
                        current_main = {"main": current_main, "subitems": [nested_item]}
                        section_items[-1] = current_main
                else:
                    # nested item without main? just add as is
                    section_items.append(line.strip())
            elif re.match(r"^[-*]\s+", line):  # main bullet line
                main_item = re.sub(r"^[-*]\s+", "", line)
                section_items.append(main_item)
                current_main = main_item
            else:
                # line without bullet, treat as continuation or a new item
                section_items.append(line.strip())
                current_main = None

        parsed[title] = section_items
    return parsed


def scrape_return_dict(url: str, token: str):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    url = transform_url(url)
    driver.get(url)
    time.sleep(3)
    html = driver.page_source
    # Optional: Clean it using BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    raw_text = soup.get_text()
    text = re.sub(r'[\u200b]', '', raw_text).strip()
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
            "1. **DATES** (e.g. registration deadlines, submission dates, awards ceremonies)\n"
            "2. **BILLING or entry fees**\n"
            "3. **PARTICIPATION REQUIREMENTS** (e.g. age, grade level, citizenship, educational background)\n"
            "4. **ORGANIZERS** and partners of the olympiad, or hosting institutions\n"
            "5. **REWARDS FOR WINNERS** (e.g. cash prizes, scholarships, publication opportunities, certificates)\n\n"
            "Respond in clearly separated sections. If any section is not mentioned in the input, say: 'Not specified'. "
            "Use this format of your answer: (number of question). (exact name of the category you are answering): then list all details of current category, each category in a separate line, starting each detail with - and a whitespace"
            "Use concise and clean formatting. Do not invent or infer details beyond the text."
        ),
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
        "dates": parsed.get("dates:", []),
        "billing": parsed.get("billing or entry fees:", []),
        "requirements": parsed.get("participation requirements:", []),
        "organizers": parsed.get("organizers and partners of the olympiad, or hosting institutions:", []),
        "rewards": parsed.get("rewards for winners:", []),
    }
    driver.quit()
    return result

