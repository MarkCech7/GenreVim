from flask import Flask, request, render_template, jsonify
from pytube import YouTube
from pydub import AudioSegment
import librosa
from transformers import pipeline

app = Flask(__name__)

def download_youtube_video(url):
    yt = YouTube(url,use_oauth=True, allow_oauth_cache=True)
    stream = yt.streams.filter(only_audio=True).first()
    out_file = stream.download(output_path="download/")
    return out_file

def convert_to_wav(mp4_file):
    audio = AudioSegment.from_file(mp4_file, format="mp4")
    wav_file = mp4_file.replace('.mp4', '.wav')
    audio.export(wav_file, format="wav")
    return wav_file

def prediction(wav_file):
    target_sr = 16000
    data, sr = librosa.load(wav_file)
    data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)

    classifier = pipeline("audio-classification", model="MarekCech/GenreVim-HuBERT-1")
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
    file = download_youtube_video(url)
    wav_file = convert_to_wav(file)
    predict = prediction(wav_file)
    predict = predict[0]['label']
    return predict