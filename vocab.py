import requests
import json
import time
import random
from typing import Dict, List


class ReadingPlusAuto:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://student.readingplus.com"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1'
        })

        # Realistic point ranges based on your data
        self.flash_point_range = (3, 7)  # Flash activities: 3-7 points
        self.wiu_point_range = (4, 10)  # Word in use: 4-10 points
        self.selection_range = (0, 4)  # Selection index: 0-4

    def initialize_session(self, site_code: str):
        """Set initial cookies (simulates WebSocket connection)"""
        self.session.cookies.set('secure_login', 'true')
        self.session.cookies.set('school_code_4', site_code)
        self.session.cookies.set('login_form', 'student')
        return True

    def login(self, site_code: str, username: str, password: str) -> bool:
        """Login with exact browser headers"""
        login_url = f'{self.base_url}/seereader/api/j_spring_security_check'

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/seereader/api/sec/login',
            'Sec-Ch-Ua': '"Not:A-Brand";v="99", "Microsoft Edge";v="145", "Chromium";v="145"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }

        login_data = {
            'site_code': site_code,
            'j_username': username,
            'j_password': password
        }

        response = self.session.post(login_url, data=login_data, headers=headers, allow_redirects=False)
        return response.status_code == 302 and 'dash/home' in response.headers.get('Location', '')

    def load_dashboard(self) -> bool:
        """Load dashboard home - critical for session finalization"""
        url = f'{self.base_url}/seereader/api/dash/home'

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': f'{self.base_url}/seereader/api/sec/login',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }

        response = self.session.get(url, headers=headers)
        return response.status_code == 200

    def security_ping(self) -> bool:
        """Send security ping to validate session"""
        url = f'{self.base_url}/seereader/api/security/ping.json'

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/seereader/api/dash/home',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        response = self.session.get(url, headers=headers)
        return response.status_code == 200

    def start_reading_adventure(self) -> bool:
        """Start reading adventure"""
        url = f'{self.base_url}/seereader/api/ra/startRA'

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': f'{self.base_url}/seereader/api/dash/lessons',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }

        response = self.session.get(url, headers=headers)
        return response.status_code == 200

    def get_word(self) -> Dict:
        """Get vocabulary word"""
        url = f'{self.base_url}/seereader/api/ra/getWord.json'

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/seereader/api/ra/startRA',
        }

        response = self.session.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        return {}

    def save_flash(self, rar_id: int, points: int = None) -> Dict:
        """Save flash activity with realistic points"""
        if points is None:
            points = random.randint(*self.flash_point_range)

        selection_index = random.randint(*self.selection_range)
        milliseconds = random.randint(5000, 15000)  # 5-15 seconds

        url = f'{self.base_url}/seereader/api/ra/saveFlash.json'

        data = {
            "rarId": rar_id,
            "wordPoints": points,
            "flashCount": 1,
            "selectionIndex": selection_index,
            "milliseconds": milliseconds
        }

        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/seereader/api/ra/startRA',
            'Origin': self.base_url,
        }

        response = self.session.post(url, json=data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            return result
        return {}

    def save_word_in_use(self, rar_id: int, points: int = None) -> Dict:
        """Save word in use activity with realistic points"""
        if points is None:
            points = random.randint(*self.wiu_point_range)

        # Random selection list (usually 2 selections)
        selection_list = random.sample(range(5), 2)
        milliseconds = random.randint(10000, 25000)  # 10-25 seconds

        url = f'{self.base_url}/seereader/api/ra/saveWordInUse.json'

        data = {
            "rarId": rar_id,
            "wordPoints": points,
            "hintCount": random.randint(0, 1),  # Sometimes use a hint
            "selectionList": selection_list,
            "milliseconds": milliseconds,
            "finish": True
        }

        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/seereader/api/ra/startRA',
            'Origin': self.base_url,
        }

        response = self.session.post(url, json=data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            return result
        return {}

    def complete_full_setup(self, site_code: str, username: str, password: str) -> bool:
        """Complete the full authentication sequence"""
        print("🔄 Initializing session...")
        self.initialize_session(site_code)

        print("🔄 Logging in...")
        if not self.login(site_code, username, password):
            print("❌ Login failed")
            return False

        print("🔄 Loading dashboard...")
        if not self.load_dashboard():
            print("❌ Dashboard load failed")
            return False

        print("🔄 Security ping...")
        if not self.security_ping():
            print("❌ Security ping failed")
            return False

        print("🔄 Starting reading adventure...")
        if not self.start_reading_adventure():
            print("❌ Failed to start reading adventure")
            return False

        print("✅ Session ready!\n")
        return True

    def process_words(self, num_words: int = 10, fixed_points: int = None):
        """
        Process multiple words with realistic points
        If fixed_points is provided, use that value for all activities
        Otherwise use random realistic ranges
        """
        results = []
        total_flash_points = 0
        total_wiu_points = 0

        for i in range(num_words):
            print(f"\n{i + 1}/{num_words}")

            # Get word
            word_data = self.get_word()
            if not word_data or not word_data.get('ok'):
                print("❌ Failed to get word")
                break

            rar_id = word_data['rarId']
            word = word_data['word']

            word_result = {
                'word': word,
                'rar_id': rar_id,
                'flash_points': 0,
                'wiu_points': 0,
                'flash_time': 0,
                'wiu_time': 0
            }

            # Submit flash if not complete
            if not word_data.get('flashComplete', False):
                flash_points = fixed_points if fixed_points else None
                flash_result = self.save_flash(rar_id, flash_points)
                if flash_result.get('result'):
                    points = flash_result.get('wordPoints', 0)
                    word_result['flash_points'] = points
                    total_flash_points += points
                  # Random delay between activities

            # Submit word in use if not complete
            if not word_data.get('wiuComplete', False):
                wiu_points = fixed_points if fixed_points else None
                wiu_result = self.save_word_in_use(rar_id, wiu_points)
                if wiu_result.get('result'):
                    points = wiu_result.get('wordPoints', 0)
                    word_result['wiu_points'] = points
                    total_wiu_points += points

            results.append(word_result)

# MAIN EXECUTION
if __name__ == "__main__":
    rp = ReadingPlusAuto()

    # Complete setup
    if rp.complete_full_setup("RPJOHNF1", "rumnel567@fusdk12.net", "64567"):

        rp.process_words(num_words=4, fixed_points=4)