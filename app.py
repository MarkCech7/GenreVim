from flask import Flask, request, render_template
from pytube import YouTube
from pydub import AudioSegment
import librosa
from transformers import pipeline
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import requests
import os

app = Flask(__name__)
# creating db model
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    print("test")
    db.create_all()

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    youtube_link = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Song {self.name}>'

def download_youtube_video(url):
    yt = YouTube(url,use_oauth=True, allow_oauth_cache=True)
    if yt.length > 7*60:  # Set a maximum video length
        raise ValueError("Video is too long. Maximum length is 7 minutes.")
    if yt.length < 30:  # Set a minimum video length 
        raise ValueError("Video is too short. Minimum length is 30 seconds.")
    stream = yt.streams.filter(only_audio=True).first()
    out_file = stream.download(output_path="download/")
    return out_file

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
    return genre_prediction[0]['label'], None

"""
@app.route("/",methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']

""" 

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=['POST'])
def predict():
    url = request.form['url']
    file = download_youtube_video(url)
    title = get_video_title(url)
    wav_file = convert_to_wav(file)
    genre, error_message = prediction(wav_file)
        
    if error_message:
        os.remove(file)
        os.remove(wav_file)
        return render_template('predict.html', genre=error_message)
    
    #genre = genre[0]['label']
    
    new_song = Song(name=title, genre=genre, youtube_link=url)
    db.session.add(new_song)
    db.session.commit()
    
    recommendations = Song.query.filter_by(genre=genre).all()
    return render_template('predict.html', genre=f"Genre of '{title}' is '{genre}'", recommendations=recommendations)


