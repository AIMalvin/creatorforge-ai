#upload.py

import os
import json
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload  # Important !
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import streamlit as st



config = {
    "implicit_wait": 10,
    "explicit_wait": 10,
    "add_hashtag_wait": 1.5,
    "selectors": {
        "upload": {
            "description": '//div[contains(@class, "public-DraftEditor-content") and @contenteditable="true"]',
            "mention_box": '//div[@role="listbox"]',
            "mention_box_user_id": '//div[@role="listbox"]//span'
        }
    }
}



def _clear(element):
    """Efface le texte d’un élément input ou textarea."""
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.BACKSPACE)

def _set_description(driver, description: str, config: dict) -> None:
    """
    Ajoute une description avec gestion des #hashtags et @mentions.
    """
    if not description:
        return

    print("[+] Ajout de la description...")

    description = description.encode("utf-8", "ignore").decode("utf-8")
    saved_description = description

    WebDriverWait(driver, config["implicit_wait"]).until(
        EC.presence_of_element_located((By.XPATH, config["selectors"]["upload"]["description"]))
    )
    desc_elem = driver.find_element(By.XPATH, config["selectors"]["upload"]["description"])
    desc_elem.click()

    WebDriverWait(driver, config["explicit_wait"]).until(lambda d: desc_elem.text != "")
    _clear(desc_elem)
    WebDriverWait(driver, config["explicit_wait"]).until(lambda d: desc_elem.text == "")
    desc_elem.click()
    time.sleep(1)

    try:
        for word in description.split(" "):
            if word.startswith("#"):
                desc_elem.send_keys(word)
                desc_elem.send_keys(" " + Keys.BACKSPACE)
                WebDriverWait(driver, config["implicit_wait"]).until(
                    EC.presence_of_element_located((By.XPATH, config["selectors"]["upload"]["mention_box"]))
                )
                time.sleep(config["add_hashtag_wait"])
                desc_elem.send_keys(Keys.ENTER)

            elif word.startswith("@"):
                print(f"[+] Ajout de la mention : {word}")
                desc_elem.send_keys(word)
                desc_elem.send_keys(" ")
                time.sleep(1)
                desc_elem.send_keys(Keys.BACKSPACE)

                WebDriverWait(driver, config["explicit_wait"]).until(
                    EC.presence_of_element_located((By.XPATH, config["selectors"]["upload"]["mention_box_user_id"]))
                )

                found = False
                timeout = 5
                start_time = time.time()

                while not found and (time.time() - start_time < timeout):
                    user_elements = driver.find_elements(By.XPATH, config["selectors"]["upload"]["mention_box_user_id"])
                    for i, el in enumerate(user_elements):
                        if el and el.is_enabled:
                            username = el.text.split(" ")[0]
                            if username.lower() == word[1:].lower():
                                found = True
                                for _ in range(i):
                                    desc_elem.send_keys(Keys.DOWN)
                                desc_elem.send_keys(Keys.ENTER)
                                break
                    if not found:
                        time.sleep(0.5)
            else:
                desc_elem.send_keys(word + " ")

    except Exception as e:
        print("Erreur lors de l'ajout de la description :", e)
        _clear(desc_elem)
        desc_elem.send_keys(saved_description)


def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
    driver = uc.Chrome(options=options)
    return driver




def upload_to_tiktok(driver, video_path, title, description):
    caption = f"{title}\n{description}"
    cookie_file = "./config/tiktok_cookies.json"

    driver = get_driver()
    driver.get("https://www.tiktok.com")
    time.sleep(3)

    # Cookies TikTok
    if os.path.exists(cookie_file):
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
        print("🔑 Cookies TikTok injectés.")
    else:
        print("⚠️ Connecte-toi à TikTok dans Chrome (60s)...")
        time.sleep(60)
        cookies = driver.get_cookies()
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        print("✅ Cookies TikTok sauvegardés.")

    driver.get("https://www.tiktok.com/upload")
    wait = WebDriverWait(driver, 30)

    try:
        upload_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        upload_input.send_keys(os.path.abspath(video_path))
        print("📄 Vidéo envoyée.")
    except Exception as e:
        print(f"❌ Erreur upload : {str(e)}")
        return

    try:
        time.sleep(5)
        _set_description(driver, caption, config)
        print("🖋️ Description ajoutée.")
    except Exception as e:
        print(f"❌ Erreur description : {str(e)}")
        return

    try:
        time.sleep(300)
        publish_xpath = '/html/body/div[1]/div/div/div[2]/div[2]/div/div/div/div[4]/div/button[1]'
        publish_btn = wait.until(EC.element_to_be_clickable((By.XPATH, publish_xpath)))

        while "loading-true" in publish_btn.get_attribute("class"):
            time.sleep(1)
            publish_btn = driver.find_element(By.XPATH, publish_xpath)

        publish_btn.click()
        print("✅ Vidéo publiée.")
        time.sleep(10)
        driver.execute_script("window.close();")

    except Exception as e:
        print(f"❌ Erreur publication : {str(e)}")
        time.sleep(10)
        driver.execute_script("window.close();")











def upload_video(video_file, title, description, tags):
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "./config/client_secret.json"
    token_file = "./config/token.json"

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print("\n⚠️ Erreur de rafraîchissement des tokens:", e)
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_local_server(port=0)
        # Sauvegarde des nouveaux tokens
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=creds)

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28" # "Science & Technology"
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False
        }
    }

    media_file = MediaFileUpload(video_file, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )

    response = request.execute()
    video_id = response['id']
    print(f"✅ Upload YouTube terminé. Video ID : {video_id}")
    return f"https://youtube.com/shorts/{video_id}"
