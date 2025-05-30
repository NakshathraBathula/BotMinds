# services/scraper_service.py
import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from utils.async_utils import get_percentage
from config import LOGIN_URL, TIME_TABLE_URL, RESULTS_URL  # Add this import

async def fetch_results_data(mobile_number, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("🔐 Logging in...")
        await page.goto(LOGIN_URL)
        await page.fill(".ant-input", mobile_number)
        await page.fill(".ant-input-password input", password)
        await page.click(".ant-btn-primary")
        await page.wait_for_load_state("networkidle")
        print("✅ Login successful")
        print("🚀 Navigating to results page...")
        await page.goto(RESULTS_URL)
        await page.wait_for_selector('iframe[title="Results"]', timeout=10000)
        print("✅ Results page loaded")
        print("📊 Fetching results...")
        results = await fetch_results(page)
        await browser.close()
        return results

async def fetch_results(page):
    """Extract student results from all academic period blocks within the iframe."""
    iframe_selector = 'iframe[title="Results"]'
    print("🔍 Looking for iframe...")
    await page.wait_for_selector(iframe_selector, timeout=10000)
    iframe_element = await page.query_selector(iframe_selector)
    if not iframe_element:
        print("❌ Results iframe not found")
        raise Exception("Results iframe not found")
    print("✅ Iframe found")
    frame = await iframe_element.content_frame()
    if not frame:
        print("❌ Could not switch to iframe context")
        raise Exception("Could not switch to iframe context")
    print("✅ Switched to iframe context")
    print("🔍 Waiting for .year-container...")
    await frame.wait_for_selector('.year-container', timeout=10000)
    print("✅ .year-container found")
    await frame.wait_for_timeout(3000)
    html_content = await frame.content()
    print("📜 HTML Content of the iframe fetched.")
    soup = BeautifulSoup(html_content, 'html.parser')
    results_data = []
    print("🔍 Processing all result blocks...")
    for block in soup.find_all('div', class_='box-body no-padding'):
        header = block.find('h2')
        if not header:
            print("⚠ No header found in this result block; skipping.")
            continue
        academic_info = header.get_text(strip=True)
        print(f"📚 Processing academic period: {academic_info}")
        table = block.find('table', class_='table-condensed')
        if not table:
            print(f"⚠ No table found in block for {academic_info}; skipping.")
            continue
        subjects = []
        tbody = table.find('tbody')
        if not tbody:
            print(f"⚠ No tbody found in table for {academic_info}; skipping.")
            continue
        rows = tbody.find_all('tr')
        print(f"🔍 Found {len(rows)} rows in table for {academic_info}")
        data_found = False
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 8:
                keys = ['Subject', 'Type', 'Assignment', 'Subjective', 'Quiz', 'DTD', 'Test', 'Total']
                subject_data = {}
                for i, key in enumerate(keys):
                    subject_data[key] = cols[i].get_text(strip=True)
                subjects.append(subject_data)
                data_found = True
            elif len(cols) == 1:
                value = cols[0].get_text(strip=True)
                if value == "NA":
                    if not data_found:
                        subject_data = {key: "NA" for key in ['Subject', 'Type', 'Assignment', 'Subjective', 'Quiz', 'DTD', 'Test', 'Total']}
                        subjects.append(subject_data)
                    else:
                        print(f"⚠ Skipping trailing NA row in {academic_info}")
                else:
                    print(f"⚠ Unexpected single column row in {academic_info}: {value}")
            else:
                print(f"⚠ Skipping row with {len(cols)} columns in {academic_info}")
        if subjects:
            print(f"✅ Found {len(subjects)} subjects for {academic_info}")
            results_data.append({
                'Academic Period': academic_info,
                'Subjects': subjects
            })
        else:
            print(f"⚠ No subjects found for {academic_info}")
    print(results_data)
    return results_data
async def fetch_attendance(mobile_number, password):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(LOGIN_URL)
        await page.fill(".ant-input", mobile_number)
        await page.fill(".ant-input-password input", password)
        await page.click(".ant-btn-primary")
        try:
            await page.wait_for_selector("span.ninjadash-nav-actions__author--name, div.profile-header", timeout=30000)
        except Exception as e:
            print("Login might have failed or took too long:", e)
            await browser.close()
            return {"error": "Login failed or timed out."}
        await page.goto("http://kmit-netra.teleuniv.in/student/attendance")
        await page.wait_for_timeout(5000)
        overall_header = page.locator('h4:has-text("Overall")')
        if await overall_header.count():
            await overall_header.click()
            await page.wait_for_timeout(3000)
        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        student_name = soup.find("span", class_="ninjadash-nav-actions__author--name")
        if student_name:
            print(f"\n✅ Student: {student_name.text.strip()}")
        attendance_data = []
        attendance_table = soup.find('table')
        if attendance_table:
            tbody = attendance_table.find('tbody', class_='ant-table-tbody')
            if tbody:
                rows = tbody.find_all('tr', class_='ant-table-row')
                for row in rows:
                    cells = row.find_all('td', class_='ant-table-cell')
                    if len(cells) >= 3:
                        subject = cells[0].get_text(strip=True)
                        theory = await get_percentage(cells[1])
                        practical = await get_percentage(cells[2])
                        attendance_data.append({
                            'subject': subject,
                            'theory': theory,
                            'practical': practical
                        })
        overall_progress = soup.find('div', class_='ant-progress-bg')
        overall_percent = None
        if overall_progress:
            overall_style = overall_progress.get('style', '')
            try:
                overall_percent = overall_style.split('width:')[-1].split('%')[0].strip()
            except IndexError:
                print("❌ Could not extract overall attendance percentage.")
        await browser.close()
        return {
            "student_name": student_name.text.strip() if student_name else "Unknown",
            "attendance_data": attendance_data,
            "overall_percent": overall_percent
        }

async def fetch_timetable(page):
    """Extract timetable data from the page"""
    await page.wait_for_selector('.ant-table-row')
    html_content = await page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    timetable = []
    rows = soup.select('.ant-table-row')
    for row in rows:
        cells = row.select('.ant-table-cell')
        if len(cells) >= 3:
            timetable.append({
                "Day": cells[0].get_text(strip=True),
                "Period": cells[1].get_text(strip=True),
                "Subject": cells[2].get_text(strip=True)
            })
    return timetable

async def fetch_timetable_data(mobile_number, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(LOGIN_URL)
        await page.fill(".ant-input", mobile_number)
        await page.fill(".ant-input-password input", password)
        await page.click(".ant-btn-primary")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)
        await page.goto(TIME_TABLE_URL)
        await page.wait_for_timeout(5000)
        timetable = await fetch_timetable(page)
        await browser.close()
        grouped_timetable = {}
        for entry in timetable:
            day = entry['Day']
            if day not in grouped_timetable:
                grouped_timetable[day] = []
            grouped_timetable[day].append({
                "Period": entry["Period"],
                "Subject": entry["Subject"]
            })
        days_array = []
        for day, data in grouped_timetable.items():
            days_array.append({
                "Day": day,
                "DayData": data
            })
        return days_array