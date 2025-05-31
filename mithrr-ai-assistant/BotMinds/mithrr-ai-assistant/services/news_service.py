# services/news_service.py
import requests
from bs4 import BeautifulSoup
from config import HEADERS

def fetch_flash_news():
    url = "https://kmit.in/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        flash_news = []
        marquee_selectors = [{"id": "scroller"}, {"class_": "marquee-scroll-RL scroll2"}]
        for selector in marquee_selectors:
            marquee = soup.find("marquee", **selector)
            if marquee:
                title = marquee.get_text(separator=" ", strip=True)
                links = {link.get_text(strip=True): link['href'] for link in marquee.find_all("a") if link.get('href')}
                parts = [title] + [f"{k}: {v}" for k, v in links.items()]
                flash_news.append(". ".join(parts))
        return flash_news
    except requests.exceptions.RequestException:
        return []

def fetch_news_bulletins():
    url = "https://kmit.in/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        bulletins = []
        section = soup.find("div", class_="tab-content newsandbulletinstabcontent border")
        if not section:
            return []
        for news in section.find_all("li", class_="news-item"):
            text = news.get_text(strip=True)
            link_tag = news.find("a")
            link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
            bulletins.append(f"{text} - {link}" if link else text)
        print(bulletins)    
        return bulletins

    except requests.exceptions.RequestException:
        return []

def fetch_exam_notifications():
    url = "https://kmit.in/examination/exam.php"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        notifications = []
        section = soup.find("div", id="Examnotification")
        if not section:
            return []
        table = section.find("table", class_="table-striped")
        if not table:
            return []
        rows = table.find("tbody").find_all("tr")[:10]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            link_tag = cols[0].find("a")
            text = link_tag.get_text(strip=True) if link_tag else cols[0].get_text(strip=True)
            href = (link_tag.get('data-whatever') or link_tag.get('href')) if link_tag else None
            pdf_link = f"https://kmit.in{href}" if href else None
            date_posted = cols[1].get_text(strip=True)
            entry = f"{text} (Posted on {date_posted})"
            if pdf_link:
                entry += f" - {pdf_link}"
            notifications.append(entry)
        print(notifications)
        return notifications
    except requests.exceptions.RequestException:
        return []

def fetch_exam_timetables():
    BASE_URL = "https://kmit.in"
    url = f"{BASE_URL}/examination/exam.php"
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        timetables = []

        section = soup.find("div", id="Examtimetable")
        if not section:
            return []

        table = section.find("table", class_="table-striped")
        if not table:
            return []

        rows = table.find("tbody").find_all("tr")[:10]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            link_tag = cols[0].find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            href = link_tag['href']
            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            date_posted = cols[1].get_text(strip=True)

            timetables.append(f"{title} – {full_url} (Posted on {date_posted})")

        print(timetables)
        return timetables

    except requests.exceptions.RequestException as e:
        print(f"Error fetching timetables: {e}")
        return []