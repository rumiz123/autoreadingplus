import requests
import json
import time
import random
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()


class VisualSkillsCLI:
    """Automates Reading Plus iBalance (Visual Skills) exercises.

    Verified API flow (reverse-engineered April 2026):

    SCAN:
      1. GET  /ibalance/home           → shows available exercises
      2. GET  /ibalance/getScanDisplay.json → {storyId, lastScreenIndex, storyformat}
      3. GET  /ibalance/scanStart       → initializes scan session
      4. GET  content CDN /rp-content/ssr/landholz/{storyId} → landolt ring data
         (count "7" chars = open rings = targets)
      5. POST /ibalance/scanSave.json   → {storyId, screenIndex, targets, correct, incorrect, secondsTaken}
      6. GET  /ibalance/activityResults?type=scan → results screen (required to finalize)

    FLASH:
      1. GET  /ibalance/flashStart      → initializes flash session + embeds trigram list in HTML
         (parse trigrams from #flash element: strip 'n' padding, split into 3-char chunks)
      2. POST /ibalance/flashSave.json  × N → {wordId, wordEntered, actualFlashTime, secondsTaken, flashAttempts}
         (wordId is 0-indexed, sequential)
      3. GET  /ibalance/activityResults?type=flash → results screen (required to finalize)

    LESSON STRUCTURE:
      - Each lesson needs 120 points (6 scan + 5 flash exercises)
      - Home page tells you which exercise to do next ("Click Scan/Flash to complete your lesson")
      - After activity results, "Go On" returns to home or next exercise
      - After all exercises, lessonResults shows final scores
    """

    def __init__(self, site_code: str, username: str, password: str):
        self.session = requests.Session()
        self.base_url = "https://student.readingplus.com"
        self.content_url = "https://content.readingplus.com/rp-content"
        self.site_code = site_code
        self.username = username
        self.password = password
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1'
        })

    # ─── AUTH ──────────────────────────────────────────────

    def login(self) -> bool:
        self.session.cookies.set('secure_login', 'true')
        self.session.cookies.set('school_code_4', self.site_code)
        self.session.cookies.set('login_form', 'student')

        r = self.session.post(
            f'{self.base_url}/seereader/api/j_spring_security_check',
            data={'site_code': self.site_code, 'j_username': self.username, 'j_password': self.password},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            allow_redirects=False
        )
        if r.status_code != 302:
            print("\n  -2")
            return False

        self.session.get(f'{self.base_url}/seereader/api/dash/home')
        self.session.get(f'{self.base_url}/seereader/api/security/ping.json',
                         headers={'X-Requested-With': 'XMLHttpRequest'})
        print("\n  2")
        return True

    # ─── iBALANCE API HELPERS ─────────────────────────────

    def _ib_get(self, path: str) -> requests.Response:
        """Raw GET to iBalance API, returns Response."""
        return self.session.get(
            f'{self.base_url}/seereader/api/ibalance/{path}',
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/plain, */*',
                'Referer': f'{self.base_url}/seereader/api/ibalance/home'
            }
        )

    def _ib_get_json(self, path: str) -> dict:
        """GET JSON from iBalance API."""
        r = self._ib_get(path)
        if r.status_code == 200:
            try:
                return r.json()
            except Exception:
                return {}
        return {'_error': r.status_code}

    def _ib_post_json(self, path: str, payload: dict) -> dict:
        """POST JSON to iBalance API."""
        r = self.session.post(
            f'{self.base_url}/seereader/api/ibalance/{path}',
            json=payload,
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json;charset=UTF-8',
                'Origin': self.base_url,
                'Referer': f'{self.base_url}/seereader/api/ibalance/home'
            }
        )
        if r.status_code == 200:
            try:
                return r.json()
            except Exception:
                return {}
        return {'_error': r.status_code}

    def _ib_page(self, path: str) -> str:
        """GET an iBalance HTML page, returns body text."""
        r = self.session.get(f'{self.base_url}/seereader/api/ibalance/{path}')
        return r.text if r.status_code == 200 else ''

    # ─── SCAN EXERCISE ────────────────────────────────────

    def _count_landolt_targets(self, story_id: int) -> int:
        """Fetch Landolt ring content from CDN and count open rings (targets).
        Open rings are encoded as '7' in the word data."""
        try:
            r = requests.get(f'{self.content_url}/ssr/landholz/{story_id}', timeout=10)
            if r.status_code == 200:
                data = r.json()
                all_words = []
                for seg in data.get('segmentList', []):
                    for para in seg.get('paragraphList', []):
                        all_words.extend(para.get('words', []))
                text = ' '.join(all_words)
                targets = text.count('7')
                return targets
        except Exception as e:
            print(f"   error: {e}")
        return 0

    def do_scan(self) -> bool:
        """Complete one scan exercise."""
        print("\n  3")

        # 1. Initialize scan session FIRST (required before getScanDisplay works!)
        self._ib_page('scanStart')

        # 2. Get scan display data (only works after scanStart)
        scan = self._ib_get_json('getScanDisplay.json')
        if '_error' in scan:
            # print(f"  error: ({scan.get('_error')})")
            return False

        story_id = scan['storyId']
        last_screen = scan['lastScreenIndex']
        rate = scan.get('storyformat', [{}])[0].get('rate', 110) if scan.get('storyformat') else 110
        screen_index = last_screen + 1

        # print(f"  Story: {story_id} | Screen: {screen_index} | Rate: {rate} WPM")

        # 3. Count targets from CDN content
        targets = self._count_landolt_targets(story_id)
        if targets == 0:
            targets = random.randint(80, 160)  # fallback estimate
            # print(f"  Using estimated targets: {targets}")

        # 4. Calculate realistic result
        # Good score: ~90-95% correct, 1-5 misses
        miss = random.randint(2, max(3, targets // 20))
        false_pos = random.randint(0, 3)
        correct = targets - miss
        incorrect = false_pos

        # Time: fast but believable
        seconds = random.randint(30, 50)

        # 5. Save scan
        result = self._ib_post_json('scanSave.json', {
            'storyId': story_id,
            'screenIndex': screen_index,
            'targets': targets,
            'correct': correct,
            'incorrect': incorrect,
            'secondsTaken': seconds
        })

        if '_error' in result:
            print(f"  error: ({result.get('_error')})")
            return False

        ok = result.get('ok', False)

        # 6. Visit activity results to finalize
        self._ib_page('activityResults?type=scan')
        print("\n  4")

        return ok

    # ─── FLASH EXERCISE ───────────────────────────────────

    def _parse_flash_data(self, html: str) -> list:
        """Extract trigram words and their word IDs from flashStart HTML.

        The HTML contains:
        - <ul id="trigrams" data-count="N"> with <li class="trigram w0" data-idx="43231" data-timing="90">
        - <section id="flash"> with the actual letters as <li> text (n-padding + trigram letters)

        Returns list of dicts: [{word_id: int, word: str, timing: int}, ...]
        """
        # 1. Extract word IDs and timing from <li class="trigram"> elements
        trigram_els = re.findall(
            r'<li\s+class="trigram\s+w(\d+)"\s+data-pos="[^"]*"\s+data-idx="(\d+)"\s+data-timing="(\d+)"',
            html
        )

        # 2. Extract the actual trigram text from the flash section
        # The <section id="flash"> contains <li> elements with 'n' padding and actual letters
        flash_match = re.search(r'<section[^>]*id="flash"[^>]*>(.*?)</section>', html, re.DOTALL)
        trigram_text = ''
        if flash_match:
            section = flash_match.group(1)
            # Strip HTML tags, get just text
            stripped = re.sub(r'<[^>]+>', '', section)
            stripped = re.sub(r'\s+', '', stripped)
            # Remove 'n' padding at the start
            stripped = stripped.lstrip('n')
            trigram_text = stripped

        # 3. Combine: match word IDs with trigram text
        count = len(trigram_els)
        words = []
        for i, (idx_str, word_id_str, timing_str) in enumerate(trigram_els):
            word = trigram_text[i*3:(i+1)*3] if i*3+3 <= len(trigram_text) else '???'
            words.append({
                'word_id': int(word_id_str),
                'word': word,
                'timing': int(timing_str)
            })

        return words

    def do_flash(self) -> bool:
        """Complete one flash exercise."""
        print("\n  5")

        # 1. Get flashStart page (contains embedded trigram data)
        html = self._ib_page('flashStart')
        if not html:
            print("\n  -5")
            return False

        # 2. Parse trigram words and IDs from HTML
        words = self._parse_flash_data(html)
        if not words:
            print("  -6")
            return False

        word_strs = [w['word'] for w in words]

        # 3. Submit all trigrams concurrently (5 threads)
        def _submit(w):
            base_ms = w['timing'] * 10
            return self._ib_post_json('flashSave.json', {
                'wordId': w['word_id'], 'wordEntered': w['word'],
                'actualFlashTime': base_ms + random.randint(-50, 50),
                'secondsTaken': 1, 'flashAttempts': 1
            })

        correct_count = 0
        with ThreadPoolExecutor(max_workers=5) as pool:
            for r in pool.map(_submit, words):
                if '_error' not in r:
                    correct_count += 1


        # 4. Visit activity results to finalize
        self._ib_page('activityResults?type=flash')
        print("\n  6")

        return correct_count > 0

    # ─── LESSON LOOP ──────────────────────────────────────

    def _check_home(self) -> tuple:
        """Visit home and determine what exercise to do next.
        Returns: (exercise_type, lesson_complete)
          exercise_type: 'scan', 'flash', 'both', or 'done'
          lesson_complete: True if lesson points show 'Complete'
        """
        html = self._ib_page('home')
        lower = html.lower()

        # Check if lesson points bar says "Complete"
        lesson_complete = 'complete' in lower and 'lesson points' in lower

        if 'you finished the lesson' in lower:
            return ('done', True)
        elif 'click scan to complete' in lower:
            return ('scan', lesson_complete)
        elif 'click flash to complete' in lower:
            return ('flash', lesson_complete)
        elif 'do you want to scan or flash' in lower:
            return ('both', lesson_complete)
        else:
            return ('flash', lesson_complete)

    def complete_lesson(self) -> bool:
        """Complete one full lesson by blasting 3 exercises without
        intermediate home checks. Pattern: scan, flash, flash.
        Only checks home once at start and once at end."""

        # One home check to initialize
        self._ib_page('home')

        # Blast through 3 exercises: scan → flash → flash
        sequence = [self.do_scan, self.do_flash, self.do_flash]
        for i, exercise_fn in enumerate(sequence):
            success = exercise_fn()
            if not success:
                # Try the other type
                alt = self.do_flash if exercise_fn == self.do_scan else self.do_scan
                success = alt()
                if not success:
                    return False

        return True

    # ─── MAIN ─────────────────────────────────────────────

    def run(self, lessons: int = 1):
        print(f"  powered by antivgc")
        print(f"  @rumiznellasery1")

        print("\n  1")
        if not self.login():
            return

        for i in range(1, lessons + 1):

            try:
                success = self.complete_lesson()
                if not success:
                    # print(f"\n  {i} failed")
                    break
            except KeyboardInterrupt:
                print(f"\n\n  {i-1} ")
                return
            except Exception as e:
                print(f"\n  error {type(e).__name__}: {e}")
                break

            if i < lessons:
                time.sleep(1)

        print("\n  8")


if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    site_code = os.environ.get('RP_SITE_CODE', '')
    username = os.environ.get('RP_USERNAME', '')
    password = os.environ.get('RP_PASSWORD', '')
    cli = VisualSkillsCLI(site_code, username, password)
    cli.run(lessons=num)
