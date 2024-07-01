from flask import Flask, request, render_template, jsonify
from pytube import YouTube
from pydub import AudioSegment
import librosa
from transformers import pipeline
from flask_sqlalchemy import SQLAlchemy


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
    title = yt.title  # Get the video title
    stream = yt.streams.filter(only_audio=True).first()
    out_file = stream.download(output_path="download/")
    return out_file, title

def convert_to_wav(mp4_file):
    audio = AudioSegment.from_file(mp4_file, format="mp4")
    wav_file = mp4_file.replace('.mp4', '.wav')
    audio.export(wav_file, format="wav")
    return wav_file

def prediction(wav_file):
    target_sr = 16000
    data, sr = librosa.load(wav_file)
    data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)

    classifier = pipeline("audio-classification", model="MarekCech/GenreVim-HuBERT-3")
    return classifier(data)

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
    file, title = download_youtube_video(url)
    wav_file = convert_to_wav(file)
    genre = prediction(wav_file)
    genre = genre[0]['label']
    
    new_song = Song(name=title, genre=genre, youtube_link=url)
    db.session.add(new_song)
    db.session.commit()
    
    recommendations = Song.query.filter_by(genre=genre).all()
    return render_template('predict.html', genre=f"Genre of '{title}' is '{genre}'", recommendations=recommendations)


