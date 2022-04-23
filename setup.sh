#!/bin/sh
apt-get install build-essential cmake pkg-config
apt-get install libx11-dev libatlas-base-dev
apt-get install libgtk-3-dev libboost-python-dev

mkdir -p ~/.streamlit/
echo "
[server]\n
headless = true\n
enableCORS=false\n
enableXsrfProtection=false\n
port = $PORT\n
\n
" > ~/.streamlit/config.toml