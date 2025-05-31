# utils/async_utils.py
from bs4 import BeautifulSoup
import re

async def get_percentage(cell):
    svg = cell.find('svg', class_='ant-progress-circle')
    if not svg:
        return None
    circles = svg.find_all('circle', class_='ant-progress-circle-path')
    if not circles:
        return None
    for circle in circles:
        style = circle.get('style', '')
        dasharray_match = re.search(r'stroke-dasharray:\s*([\d.]+)', style)
        dashoffset_match = re.search(r'stroke-dashoffset:\s*([\d.]+)', style)
        if dasharray_match and dashoffset_match:
            try:
                dasharray = float(dasharray_match.group(1))
                dashoffset = float(dashoffset_match.group(1))
                if dasharray > 0:
                    return round((1 - (dashoffset / dasharray)) * 100, 1)
            except Exception as e:
                print(f"Error parsing circle: {e}")
                return None
    return None