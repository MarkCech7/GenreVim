# GenreVim
Music Genre classification based on DistilHuBERT

Pytube fix: In cipher.py replace line 195 with: 'pattern = r"%s=function\(\w\){[a-z=\.\(\"\)]*;((\w+\.\w+\([\w\"\'\[\]\(\)\.\,\s]*\);)+)(?:.+)}" % name' and insert'r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)', after line 274 in "function_patterns". This is fixed in Dockerfile where cipher.py from patches folder is copied into /usr/local/lib/python3.11/site-packages/pytube.

To run the application using Flask, use the following command:
flask --app app run --debug

To run the application via Docker, use following command:
docker compose up