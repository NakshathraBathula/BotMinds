# utils/helpers.py
import re

def clean_response(raw_response):
    return re.sub(r'\*(\w+)\*', r'\1', raw_response)