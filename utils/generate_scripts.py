import openai
import yaml
import re
import json
import os 
from dotenv import load_dotenv

load_dotenv()

def load_config():
    with open('./config/settings.yaml', 'r') as f:
        return yaml.safe_load(f)


def generate_script(user_topic):
    """
    Génère un script PARLÉ pour une vidéo Short de 20 secondes MAXIMUM ABSOLUMENT (60 mots), éducatif, fluide et engageant, conforme aux règles TikTok/YouTube Shorts.
    """
    import openai
    config = load_config()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = """
    Agis comme un expert en création de vidéos virales TikTok et YouTube Shorts, spécialisé en finance et intelligence artificielle.

    Ta mission : écrire un **script parlé**, fluide et spontané, comme si tu t’adressais à un pote. Ce script doit durer **max 20 secondes**, soit environ **60 mots**.

    🎯 Sujet : {user_topic}

    Structure du script :
    1. Commence directement avec un **hook fort** :
    - Stat choquante
    - Question ultra ciblée
    - Observation étrange ou contre-intuitive
    (Pas d’intro type “salut” ou “dans cette vidéo”, on attaque direct)

    2. Glisse subtilement cette phrase (et adapte-la au ton de la vidéo) :
    **"Si tu veux accéder aux mêmes outils que j'utilise — cashback, placements, ou crypto — j'ai mis les liens avec bonus en bio."**
    (Tu peux reformuler tant que ça reste naturel, non commercial et orienté partage d'astuces)

    3. Apporte **1 info/action concrète** ou **peu connue** liée au sujet (pas de généralités)

    4. Termine avec une **phrase intrigante** qui pousse au rewatch ou à l’exploration :
    - “Et personne t’explique pourquoi.”
    - “C’est là que ça devient bizarre…”
    - “Mais ça, personne ne l’utilise.”
    - “Et c’est là que l’IA change tout.”

    Contraintes de ton :
    - Aucune formule marketing (“clique en bio”, “abonne-toi”, etc.)
    - Aucun ton vendeur
    - Pas de promesse magique
    - Rythme rapide, ton naturel, impact immédiat

    🎥 Rappelle-toi : ce script sera utilisé en vidéo verticale courte. Il doit **capturer l’attention dès la 1ère seconde**, **donner une vraie valeur**, et **générer de la curiosité passive**.
    """.format(user_topic=user_topic)


    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Tu écris des scripts TikTok/Shorts courts, percutants, éducatifs et viraux, optimisés pour watch time et clics."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=350
    )

    return response.choices[0].message["content"]


def one_word(query: str) -> str:
    """
    Utilise GPT pour extraire le thème central du texte,
    et renvoie un mot-clé propre (en anglais), utilisable pour une API.
    """
    config = load_config()
    openai.api_key = config['openai_api_key']

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": (
                "Donne-moi UNIQUEMENT le thème central de ce texte "
                "en anglais, au format JSON comme ceci : {\"keyword\": \"impact\"}. "
                f"Texte : {query}"
            )
        }],
        max_tokens=30,
        temperature=0.4
    )

    content = response.choices[0].message['content'].strip()

    try:
        keyword_json = json.loads(content)
        keyword = keyword_json.get("keyword", "")
    except json.JSONDecodeError:
        keyword_match = re.findall(r'\b[a-zA-Z]{3,}\b', content)
        keyword = keyword_match[0] if keyword_match else ""

    return keyword.lower()

def generate_title(text):
    config = load_config()
    openai.api_key = config['openai_api_key']

    prompt = f"""
    Génère uniquement le Titre d'une vidéo YouTube Short à partir du contenu suivant : {text}

    Objectifs :
    - Titre engageant et informatif, sans promesse exagérée.
    - Maximum 100 caractères.
    - N'utilise **aucun emoji** dans le titre.
    - Ne retourne que le titre. Pas d'introduction ni d'explication.

    Langue : Français.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0.9
    )

    return response.choices[0].message['content'].strip()


def generate_description(text): 
    config = load_config()
    openai.api_key = config['openai_api_key']

    prompt = f"""
    Génère uniquement la description YouTube pour cette vidéo : {text}

    Format attendu :
    1. Une phrase d'accroche informative.
    2. Un résumé clair de la vidéo (max 3 lignes).
    3. Un appel à l'action discret (abonne-toi, like...).
    4. Termine par 3 hashtags pertinents.
    5. N'utilise **aucun emoji**.

    Seulement la description, pas d'intro ou d'explication.
    Langue : Français
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].message['content'].strip()


def generate_tags(text):
    config = load_config()
    openai.api_key = config['openai_api_key']

    prompt = f"""
    Donne uniquement les mots-clés importants pour cette vidéo YouTube, séparés par des virgules. 
    Pas de phrase, uniquement la liste de mots-clés (maximum 10). Voici le contexte : {text}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.5
    )

    content = response.choices[0].message['content'].strip()

    keywords = [word.strip() for word in content.split(",") if word.strip()]

    return keywords
