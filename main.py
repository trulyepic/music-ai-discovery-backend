import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

# from flask_cors import CORS

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MUSIC_API_KEY = os.getenv("MUSIC_API_KEY")

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (use a specific frontend URL in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# OpenAI client
openai.api_key = OPENAI_API_KEY


class MusicRequest(BaseModel):
    genre: str
    num_recommendations: int  # User can specify how many recommendations they want


class TrackRequest(BaseModel):
    tracks: list[str]  # List of tracks (max 10)
    num_recommendations: int


# Fetch music data from Last.fm API
def fetch_music_data(genre):
    url = f"http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={genre}&api_key={MUSIC_API_KEY}&format=json"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    tracks = data.get("tracks", {}).get("track", [])
    return [f"{track['name']} - {track['artist']['name']}" for track in tracks][:10]  # Limit to 10 songs


# Generate recommendations with OpenAI
def generate_recommendation(prompt):
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a music recommendation assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Generate recommendations using OpenAI
# def generate_recommendation(genre, songs, num_recommendations):
#     top_song = songs[0] if songs else "No top song available"
#     prompt = f"""
#     A user loves {genre} music. Based on these top songs of {genre}:
#     {', '.join(songs)}
#
#     Suggest {num_recommendations} personalized music recommendations, ensuring they align with {genre} and the top
#     song: {top_song}.
#     Explain why you chose them.
#     """
#     client = openai.OpenAI()
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a music recommendation assistant."},
#             {"role": "user", "content": prompt}
#         ]
#     )
#
#     return response.choices[0].message.content


@app.post("/recommend")
def recommend_music(request: MusicRequest):
    genre = request.genre.lower()
    songs = fetch_music_data(genre)
    num_recommendations = request.num_recommendations

    if not songs:
        raise HTTPException(status_code=404, detail="No songs found for this genre.")

    prompt = f"A user loves {genre} music. Based on these top songs: {', '.join(songs)}, suggest {num_recommendations} songs with explanations."

    recommendations = generate_recommendation(prompt)

    return {
        f"Top 10 Songs Based on {genre.capitalize()}": songs,
        f"Song Recommendations": recommendations
    }

    # return {f"Top 10 Songs Based on {genre.capitalize()}": songs, f"Song Recommendations Based on {
    # genre.capitalize()} and Top Song of {genre.capitalize()}": recommendations }
