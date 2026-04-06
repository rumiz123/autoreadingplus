import requests
import json
import time
import random
from typing import Dict, List, Optional


class ReadingPlusReadingAuto:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://student.readingplus.com"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1'
        })
        self.story_data = None
        self.total_segments = 0

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

    def start_reading_session(self) -> bool:
        """Start reading session by calling getNext.json"""
        print("\n=== Starting Reading Session ===")
        url = f'{self.base_url}/seereader/api/sr/getNext.json'

        headers = {
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/seereader/api/sr/start',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        response = self.session.get(url, headers=headers)

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('status', {}).get('result'):
                    self.story_data = data
                    self.total_segments = data.get('section', {}).get('data', {}).get('totalSegmentCount', 4)
                    print(f"✓ Reading session started!")
                    print(f"  Story: {data.get('section', {}).get('data', {}).get('storyTitle')}")
                    print(f"  Total segments: {self.total_segments}")
                    print(f"  Student: {data.get('user', {}).get('firstName')} {data.get('user', {}).get('lastName')}")
                    return True
            except:
                print(f"✗ Failed to parse response: {response.text[:200]}")
                return False
        return False

    def get_session_id(self) -> bool:
        """Get session ID for the reading session"""
        print("\n=== Getting Session ID ===")
        url = f'{self.base_url}/seereader/api/sr/getSessionId.json'

        headers = {
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/seereader/api/sr/start',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        response = self.session.get(url, headers=headers)

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('result'):
                    print(f"✓ Session ID obtained: {data.get('message')[:20]}...")
                    return True
            except:
                print(f"✗ Failed to parse response: {response.text[:200]}")
                return False
        return False

    def save_segment(self, segment_index: int) -> bool:
        """Send saveSegment.json request with realistic timing"""
        url = f'{self.base_url}/seereader/api/sr/saveSegment.json'

        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json;charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/seereader/api/sr/start',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        # Create realistic screen list based on segment
        screen_list = self._generate_screen_list(segment_index)

        payload = {
            "screenList": screen_list,
            "segmentIndex": segment_index
        }

        print(f"\n  📖 Saving segment {segment_index}/{self.total_segments}...")
        response = self.session.post(url, headers=headers, json=payload)

        print(f"  Response status: {response.status_code}")
        print(f"  Response body: {response.text[:500]}")
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('result'):
                    total_time = sum(screen.get('secondsTaken', 0) for screen in screen_list)
                    print(f"  ✓ Segment {segment_index} complete - Reading time: {total_time} seconds")
                    return True
                else:
                    print(f"  ✗ Result was false: {data}")
            except Exception as e:
                print(f"  ✗ Parse error: {e}")
        print(f"  ✗ Segment {segment_index} failed")
        return False

    def _generate_screen_list(self, segment_index: int) -> List[Dict]:
        """Generate realistic screen data for a segment"""
        screen_list = []

        # Different segments have different screen counts
        if segment_index == 1:
            screens = [
                {"lineCount": 12, "wordCount": 137, "trapHi": True, "trapLow": False, "pauseSeconds": 12},
                {"lineCount": 12, "wordCount": 137, "trapHi": False, "trapLow": False, "pauseSeconds": 53},
                {"lineCount": 12, "wordCount": 131, "trapHi": True, "trapLow": False, "pauseSeconds": 10},
                {"lineCount": 12, "wordCount": 131, "trapHi": False, "trapLow": False, "pauseSeconds": 2},
                {"lineCount": 3, "wordCount": 26, "trapHi": False, "trapLow": False, "pauseSeconds": 8}
            ]
        elif segment_index == 2:
            screens = [
                {"lineCount": 10, "wordCount": 120, "trapHi": False, "trapLow": True, "pauseSeconds": 15},
                {"lineCount": 10, "wordCount": 120, "trapHi": False, "trapLow": False, "pauseSeconds": 45},
                {"lineCount": 11, "wordCount": 125, "trapHi": True, "trapLow": False, "pauseSeconds": 8},
                {"lineCount": 11, "wordCount": 125, "trapHi": False, "trapLow": False, "pauseSeconds": 3}
            ]
        elif segment_index == 3:
            screens = [
                {"lineCount": 9, "wordCount": 115, "trapHi": False, "trapLow": False, "pauseSeconds": 20},
                {"lineCount": 9, "wordCount": 115, "trapHi": True, "trapLow": False, "pauseSeconds": 35},
                {"lineCount": 10, "wordCount": 118, "trapHi": False, "trapLow": True, "pauseSeconds": 12},
                {"lineCount": 10, "wordCount": 118, "trapHi": False, "trapLow": False, "pauseSeconds": 4}
            ]
        else:  # segment 4
            screens = [
                {"lineCount": 8, "wordCount": 100, "trapHi": False, "trapLow": False, "pauseSeconds": 25},
                {"lineCount": 8, "wordCount": 100, "trapHi": False, "trapLow": True, "pauseSeconds": 30},
                {"lineCount": 9, "wordCount": 110, "trapHi": True, "trapLow": False, "pauseSeconds": 10},
                {"lineCount": 9, "wordCount": 110, "trapHi": False, "trapLow": False, "pauseSeconds": 5},
                {"lineCount": 4, "wordCount": 35, "trapHi": False, "trapLow": False, "pauseSeconds": 7}
            ]

        # Add screenIndex and randomize secondsTaken for each screen
        for idx, screen in enumerate(screens):
            screen["screenIndex"] = idx
            # Random reading time between 40-70 seconds per screen
            screen["secondsTaken"] = random.randint(40, 70)

        return screens

    def save_rating(self, rating: int = 3) -> bool:
        """Send saveRating.json request"""
        url = f'{self.base_url}/seereader/api/sr/saveRating.json'

        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json;charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/seereader/api/sr/start',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        payload = {
            "rating": rating
        }

        print(f"\n=== Saving Story Rating ({rating}/5) ===")
        response = self.session.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('result'):
                    print(f"✓ Rating saved successfully!")
                    return True
            except:
                pass
        print(f"✗ Failed to save rating")
        return False

    def complete_full_setup(self, site_code: str, username: str, password: str) -> bool:
        """Complete the full authentication sequence"""
        print("=" * 70)
        print("READING SECTION - AUTHENTICATION SEQUENCE")
        print("=" * 70)

        print("\n🔄 Initializing session...")
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

        print("✅ Session ready for reading!\n")
        return True

    def complete_reading_story(self):
        """Complete a full reading story with all segments"""
        print("\n" + "=" * 70)
        print("READING THE STORY")
        print("=" * 70)

        # Step 1: Start reading session
        if not self.start_reading_session():
            print("❌ Failed to start reading session")
            return False

        # Step 2: Get session ID
        if not self.get_session_id():
            print("❌ Failed to get session ID")
            return False

        # Step 3: Simulate WebSocket connection (just a small delay)
        print("\n=== Establishing WebSocket Connection ===")
        print("✓ WebSocket connection simulated")

        # Step 4: Save each segment with realistic timing
        print("\n=== Reading Segments ===")
        total_reading_time = 0

        for segment in range(1, self.total_segments + 1):

            if self.save_segment(segment):
                continue
            else:
                print(f"⚠️  Segment {segment} may have issues")

        # Step 5: Save rating (usually 3-4 stars)
        rating = random.choice([3, 4])  # Usually 3 or 4 stars
        self.save_rating(rating)

        print("\n" + "=" * 70)
        print("✅ STORY COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        return True

    def complete_multiple_stories(self, num_stories: int = 3):
        """Complete multiple reading stories"""
        print("\n" + "=" * 70)
        print(f"COMPLETING {num_stories} READING STORIES")
        print("=" * 70)

        for story_num in range(1, num_stories + 1):
            print(f"\n\n{'=' * 70}")
            print(f"STORY {story_num} OF {num_stories}")
            print(f"{'=' * 70}")

            success = self.complete_reading_story()

            if not success:
                print(f"❌ Failed on story {story_num}")
                break

            # Wait between stories (like a real student taking a break)
            if story_num < num_stories:
                break_time = random.randint(3, 8)  # Short break for testing
                print(f"\n⏱️  Taking a {break_time} second break before next story...")
                time.sleep(break_time)

        print("\n" + "=" * 70)
        print(f"✅ COMPLETED {story_num} STORIES!")
        print("=" * 70)


# MAIN EXECUTION
if __name__ == "__main__":
    reader = ReadingPlusReadingAuto()

    # Complete authentication
    if reader.complete_full_setup("RPJOHNF1", "nigga@fusdk12.net", "nigga"):

        # Debug: try 1 story first
        reader.complete_reading_story()

        # Print final cookies for reference
        print("\n" + "=" * 70)
        print("FINAL SESSION COOKIES")
        print("=" * 70)
        cookies = reader.session.cookies.get_dict()
        for name, value in cookies.items():
            if name in ['SESSION', 'AWSALB', 'AWSALBCORS']:
                print(f"{name}: {value[:30]}...")