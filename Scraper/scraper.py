import asyncio
import re
from reviews_scraper import GoogleMapsAPIScraper
from flask import Flask, jsonify, request
from flask_cors import CORS
import llm
from pyppeteer import launch
import reviews_scraper as rs

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins. Adjust as necessary.


def process_reviews(reviews):
    processed_reviews = []

    for review in reviews:
        # Convert user_photos and user_reviews to integers, handling None and commas
        user_photos = review.get("user_photos")
        number_of_photos_by_reviewer = user_photos
        # int(user_photos.replace(",", "").replace(".", "")) if user_photos else 0

        user_reviews = review.get("user_reviews")
        number_of_reviews_by_reviewer = user_reviews
        # int(user_reviews.replace(",", "").replace(".", "")) if user_reviews else 0

        lk = review.get("likes")
        processed_review = {
            "rating": int(review.get("rating")),
            "review_text": review.get("text"),
            "published_at": review.get("relative_date"),
            "published_at_date": review.get("text_date"),
            "review_likes_count": 0 if lk <= -1 else lk,
            "total_number_of_reviews_by_reviewer": number_of_reviews_by_reviewer,
            "is_local_guide": 0 if review.get("user_is_local_guide") == None else review.get("user_is_local_guide"),
            # "extracted_at": review.get("retrieval_date")
        }
        processed_reviews.append(processed_review)

    return processed_reviews

def scrape_reviews(link):

    max_r = 300

    reviews_sort = "most_relevant"
    lang = "en"
    
    processed = []
    with GoogleMapsAPIScraper() as scraper:

        result = scraper.scrape_reviews(
            link,  max_r, lang, sort_by=reviews_sort
        )
        processed = process_reviews(result, )
    return processed

def get_reviews(data):

    result = scrape_reviews(link=data["url"])
    
    place_name = ""
    match = re.search(r'/maps/place/([^/]+)', data["url"])
    if match:
        place_name = match.group(1).replace('+', ' ') 
        
    if (llm.isDatavectorized(place_name)):
        return "Data already vectorized"


    avg_rating = 0
    for i in range(0, len(result)):
        avg_rating += result[i]['rating']
        result[i]['place_name'] = place_name
    avg_rating = avg_rating / len(result)

    return result, avg_rating, place_name


@app.route('/chat', methods=['POST'], )
def chat():
    data = request.json
    print(data)
    return jsonify(llm.get_inference(data['query'], data['place_name']))



@app.route('/run-script', methods=['POST'], )
def run_script():
    data = request.json
    data = get_reviews(data)
    llm.chat_manager = llm.ChatManager()
    if data == "Data already vectorized":
        return jsonify("Data already vectorized")
    else: 
        llm.start_chunking(

            [
                {
                    "chunk_type": "place_info",
                    "place_name": data[2],
                    "reviews": data[0],
                    "average_rating": data[1],
                    "total_reviews": len(data[0])
                }
            ]
        )
    return jsonify("Data Vectorized")

if __name__ == '__main__':
    app.run(debug=True)


