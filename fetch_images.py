import requests
import json

crops = [
    "rice", "maize", "chickpea", "kidney bean", "pigeon pea", "moth bean", "mung bean", 
    "Vigna mungo", "lentil", "pomegranate", "banana", "mango", "grape", "watermelon", 
    "muskmelon", "apple", "orange (fruit)", "papaya", "coconut", "cotton", "jute", "coffee"
]

crop_map = {
    "kidney bean": "kidneybeans",
    "pigeon pea": "pigeonpeas",
    "moth bean": "mothbeans",
    "mung bean": "mungbean",
    "Vigna mungo": "blackgram",
    "grape": "grapes",
    "orange (fruit)": "orange"
}

image_map = {}
headers = {'User-Agent': 'SwamitraBot/1.0 (dev@swamitra.com)'}

for crop in crops:
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={crop}&prop=pageimages&format=json&pithumbsize=800"
    res = requests.get(url, headers=headers)
    try:
        data = res.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if "thumbnail" in page_data:
                img_url = page_data["thumbnail"]["source"]
                key = crop_map.get(crop, crop)
                image_map[key] = img_url
                break
    except Exception as e:
        print(f"Error fetching {crop}: {e}")

print(json.dumps(image_map, indent=2))
