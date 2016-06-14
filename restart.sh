#!/bin/bash
echo "Good morning, world."
sudo ps aux | grep python | grep -v "grep python" | awk '{print $2}' | xargs kill -9
sudo service apache2 restart
python flaskapp.py
