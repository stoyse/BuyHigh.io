#!/bin/bash

lsof -ti:9876 | xargs kill -9

pkill gunicorn

gunicorn -k eventlet -w 2 --bind 127.0.0.1:9876 app:app