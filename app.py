from flask import Flask, request, render_template
from pytube import YouTube
from pydub import AudioSegment
import librosa
from transformers import pipeline
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import requests
import os
from datetime import datetime

app = Flask(__name__)
# creating db model
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    youtube_link = db.Column(db.String(200), nullable=False, unique=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, nullable=False)
    thumbnail_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Song {self.name}>'
    
with app.app_context():
    db.create_all()

def download_youtube_video(url):
    try:
        yt = YouTube(url, use_oauth=True, allow_oauth_cache=True)
    except Exception as e:
        raise ValueError("Invalid YouTube URL.")
       
    if yt.length > 7*60:  # Set a maximum video length
        raise ValueError("Video is too long. Maximum length is 7 minutes.")
    if yt.length < 30:  # Set a minimum video length 
        raise ValueError("Video is too short. Minimum length is 30 seconds.")
    
    stream = yt.streams.filter(only_audio=True).first()
    out_file = stream.download(output_path="download/")
    #embed_url = yt.embed_url
    thumbnail_url = yt.thumbnail_url
    return out_file, thumbnail_url

def get_video_title(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('meta', property='og:title')
    return title['content'] if title else 'Unknown Title'

def convert_to_wav(mp4_file):
    audio = AudioSegment.from_file(mp4_file, format="mp4")
    wav_file = mp4_file.replace('.mp4', '.wav')
    audio.export(wav_file, format="wav")
    return wav_file

def prediction(wav_file):
    target_sr = 16000
    data, sr = librosa.load(wav_file)
    data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
    
    music_classifier = pipeline("audio-classification", model="MarekCech/GenreVim-Music-Detection-DistilHuBERT")
    music_prediction = music_classifier(data, sampling_rate=target_sr)
    if music_prediction[0]['label'] == 'Non Music':
        return None, "The provided video does not contain music. Please try another video."
    
    genre_classifier = pipeline("audio-classification", model="MarekCech/GenreVim-HuBERT-3")
    genre_prediction = genre_classifier(data, sampling_rate=target_sr)
    return genre_prediction[0], None

"""
@app.route("/",methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']

""" 

@app.route("/")
def index():
    recent_songs = Song.query.order_by(Song.date.desc()).limit(6).all()
    return render_template("index.html", recent_songs=recent_songs)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/predict", methods=['POST'])
def predict():
    url = request.form['url']
    
    try:
        existing_song = Song.query.filter_by(youtube_link=url).first()
        if existing_song:
            recommendations = Song.query.filter(
                Song.genre == existing_song.genre,
                Song.youtube_link != url
            ).order_by(Song.score.desc()).limit(3).all()
            return render_template('predict.html', genre=f"Genre of '{existing_song.name}' is '{existing_song.genre}'", recommendations=recommendations, thumbnail_url=existing_song.thumbnail_url)
        
        file, thumbnail_url = download_youtube_video(url)
        title = get_video_title(url)
        wav_file = convert_to_wav(file)
        result, error_message = prediction(wav_file)
        
        genre = result['label']
        score = result['score']
        
        if error_message:
            return render_template('error.html', message=error_message)
    
        new_song = Song(name=title, genre=genre, youtube_link=url, date=datetime.utcnow(), score=score, thumbnail_url=thumbnail_url)
        db.session.add(new_song)
        db.session.commit()
    
        recommendations = Song.query.filter(
            Song.genre==genre, 
            Song.youtube_link!=url
            ).order_by(Song.score.desc()).limit(3).all()
        
        os.remove(file)  
        os.remove(wav_file)

        return render_template('predict.html', genre=f"Genre of {title}'is {genre}", recommendations=recommendations, thumbnail_url=thumbnail_url)
    except ValueError as ve:
        return render_template('error.html', message=str(ve))
    except Exception as e:
        return render_template('error.html', message=str(e))


