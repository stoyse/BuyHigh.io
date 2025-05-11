lsof -ti:9876 | xargs kill -9

gunicorn -k eventlet -w 2 --bind 127.0.0.1:9876 app:app