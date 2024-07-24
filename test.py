from pytube import YouTube

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
    thumbnail_url = yt.thumbnail_url
    return out_file, thumbnail_url

url = "https://www.youtube.com/watch?v=xy3AcmW0lrQ"

file, embed_url, thumbnail_url = download_youtube_video(url)
print(thumbnail_url)
print(embed_url)