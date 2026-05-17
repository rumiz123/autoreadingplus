import requests
import json
import time
import random
import sys
import os
from itertools import combinations
from typing import Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv

load_dotenv()


class ReadingPlusCLI:
    def __init__(self, site_code: str, username: str, password: str):
        self.session = requests.Session()
        self.base_url = "https://student.readingplus.com"
        self.content_url = "https://content.readingplus.com/rp-content"
        self.site_code = site_code
        self.username = username
        self.password = password
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1'
        })
        self.story_data = None
        self.total_segments = 0
        self.question_map = {}  # questionId → question text

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
            print("  ✗ Login failed")
            return False

        self.session.get(f'{self.base_url}/seereader/api/dash/home')
        self.session.get(f'{self.base_url}/seereader/api/security/ping.json',
                         headers={'X-Requested-With': 'XMLHttpRequest'})
        print("  ✓ Logged in")
        return True

    # ─── API HELPERS ──────────────────────────────────────

    def _api_get(self, path: str) -> dict:
        r = self.session.get(
            f'{self.base_url}/seereader/api/sr/{path}',
            headers={'X-Requested-With': 'XMLHttpRequest', 'Accept': '*/*',
                     'Referer': f'{self.base_url}/seereader/api/sr/start'}
        )
        return r.json() if r.status_code == 200 else {}

    def _api_post(self, path: str, payload: dict) -> dict:
        r = self.session.post(
            f'{self.base_url}/seereader/api/sr/{path}',
            json=payload,
            headers={'X-Requested-With': 'XMLHttpRequest',
                     'Content-Type': 'application/json;charset=UTF-8',
                     'Origin': self.base_url,
                     'Referer': f'{self.base_url}/seereader/api/sr/start'}
        )
        return r.json() if r.status_code == 200 else {}

    def fetch_story_content(self, story_id) -> None:
        """Fetch story content from CDN to get question texts and clue excerpts."""
        if not story_id:
            return
        try:
            r = requests.get(f'{self.content_url}/ssr/{story_id}.json')
            if r.status_code == 200:
                data = r.json()
                self.question_map = {}
                self.question_clues = {}
                self.story_text = ""

                # Build full story text from segments
                segments = []
                for seg in data.get('segmentList', []):
                    for section in seg.get('sectionList', []):
                        for para in section.get('paragraphList', []):
                            for sent in para.get('sentenceList', []):
                                words = sent.get('words', [])
                                segments.append(' '.join(words))
                self.story_text = ' '.join(segments)

                # Build question map with clue excerpts
                for q in data.get('questionList', []):
                    qid = q.get('id')
                    text = q.get('question', '')
                    if qid and text:
                        self.question_map[qid] = text

                    # Extract clue sentences from excerpts
                    clues = []
                    for excerpt in q.get('excerptList', []):
                        for section in excerpt.get('sectionList', []):
                            for para in section.get('paragraphList', []):
                                for sent in para.get('sentenceList', []):
                                    if sent.get('clue'):
                                        clues.append(' '.join(sent.get('words', [])))

                    # Also check reRead for clue context
                    if not clues:
                        for rr in q.get('reRead', []):
                            words = rr.get('words', [])
                            if words:
                                clues.append(' '.join(words))

                    if qid and clues:
                        self.question_clues[qid] = clues

                print(f"  Loaded {len(self.question_map)} questions, {len(self.question_clues)} with clues")
        except Exception as e:
            print(f"  ⚠ Could not fetch story content: {e}")

    # ─── STORY SELECTION ─────────────────────────────────

    def select_story(self, section_data: dict) -> Optional[dict]:
        """Handle the story selection screen. Auto-picks the first story."""
        # Try common field names for the story list
        story_list = (section_data.get('stories') or
                      section_data.get('storyList') or
                      section_data.get('selectList') or [])

        # If no list found, dump the keys so we can debug
        if not story_list:
            print(f"  [DEBUG] storyselect data keys: {list(section_data.keys())}")
            # Check if there's a storyId directly in section_data
            if section_data.get('storyId'):
                print(f"  → Direct storyId found: {section_data['storyId']}")
                story_id = section_data['storyId']
                self._api_get('getSessionId.json')
                result = self._api_post('saveStorySelect.json', {
                    "section": "storyselect",
                    "storyId": story_id
                })
                return self._api_get('getNext.json')
            print("  ✗ No stories found in response")
            print(f"  [DEBUG] Full section data: {json.dumps(section_data)[:2000]}")
            return None

        # Display available stories
        print("\n  Available stories:")
        for i, story in enumerate(story_list, 1):
            title = story.get('storyTitle', story.get('title', 'Unknown'))
            print(f"    {i}. {title}")
        
        # Let user select
        while True:
            try:
                choice = input(f"\n  Select story (1-{len(story_list)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(story_list):
                    selected = story_list[idx]
                    break
                print(f"  Invalid choice. Please enter 1-{len(story_list)}")
            except ValueError:
                print(f"  Please enter a number between 1 and {len(story_list)}")
        
        story_id = selected.get('storyId')
        title = selected.get('storyTitle', selected.get('title', 'Unknown'))
        print(f"  → Selected: {title} (ID: {story_id})")

        # Get session ID first, then save selection (matches browser behavior)
        self._api_get('getSessionId.json')
        result = self._api_post('saveStorySelect.json', {
            "section": "storyselect",
            "storyId": story_id
        })

        ok = result.get('status', {}).get('result', False)
        if not ok:
            print(f"  ✗ Story selection failed")
            return None

        # After selection, poll getNext until state changes from storyselect
        for attempt in range(5):
            time.sleep(1)
            data = self._api_get('getNext.json')
            section = data.get('section', {})
            section_data = section.get('data', {})
            name = section_data.get('name', section.get('name', ''))
            if name != 'storyselect':
                print(f"  → State: {name}")
                return data

        # If still storyselect, build a fake reading response with the info we have
        print(f"  → Server still in storyselect, starting reading with known storyId")
        # Fetch story content to get segment count
        try:
            r = requests.get(f'{self.content_url}/ssr/{story_id}.json')
            if r.status_code == 200:
                content = r.json()
                seg_count = len(content.get('segmentList', []))
            else:
                seg_count = 4
        except:
            seg_count = 4

        return {
            "section": {
                "name": "reading",
                "data": {
                    "name": "reading",
                    "storyId": story_id,
                    "storyTitle": title,
                    "totalSegmentCount": seg_count
                }
            }
        }

    # ─── READING (AUTO) ──────────────────────────────────

    def start_reading(self) -> Optional[dict]:
        data = self._api_get('getNext.json')
        section = data.get('section', {})
        section_data = section.get('data', {})
        name = section_data.get('name', section.get('name', ''))

        # 'result' means the previous lesson's results are still showing.
        # Must call saveResult to dismiss it before advancing to story selection.
        if name == 'result':
            print("  → Previous lesson result screen, dismissing...")
            self._api_post('saveResult', {"key": "rate-fast"})
            time.sleep(0.5)
            data = self._api_get('getNext.json')
            section = data.get('section', {})
            section_data = section.get('data', {})
            name = section_data.get('name', section.get('name', ''))
            print(f"  → Advanced to: {name}")

        # Handle story selection if needed
        if name == 'storyselect':
            print("  → Story selection screen")
            data = self.select_story(section_data)
            if not data:
                return None
            section = data.get('section', {})
            section_data = section.get('data', {})
            name = section_data.get('name', section.get('name', ''))

        story_id = section_data.get('storyId')
        title = section_data.get('storyTitle', 'Unknown')
        self.total_segments = section_data.get('totalSegmentCount', 4)

        print(f"  Story: {title} (ID: {story_id})")
        print(f"  Section: {name}, Segments: {self.total_segments}")

        # Fetch question texts from CDN
        self.fetch_story_content(story_id)

        return data

    def read_segments(self) -> bool:
        """Auto-read all segments (no user interaction needed)."""
        self._api_get('getSessionId.json')
        
        input("\n  Press Enter to start reading segments...")
        
        for seg in range(1, self.total_segments + 1):
            input(f"\n  Press Enter for segment {seg}/{self.total_segments}...")
            screens = self._make_screens(seg)
            result = self._api_post('saveSegment.json', {
                "screenList": screens,
                "segmentIndex": seg
            })
            ok = result.get('status', {}).get('result', False)
            print(f"    Segment {seg}/{self.total_segments}: {'✓' if ok else '✗'}")
            if not ok:
                return False
        return True

    def save_rating(self, rating: int = 3) -> bool:
        result = self._api_post('saveRating.json', {"rating": rating})
        ok = result.get('status', {}).get('result', False)
        print(f"  Rating ({rating}★): {'✓' if ok else '✗'}")
        return ok

    def _make_screens(self, segment_index: int) -> list:
        base_screens = [
            {"lineCount": 10, "wordCount": 120, "trapHi": False, "trapLow": False, "pauseSeconds": 5},
            {"lineCount": 10, "wordCount": 120, "trapHi": True, "trapLow": False, "pauseSeconds": 3},
            {"lineCount": 11, "wordCount": 130, "trapHi": False, "trapLow": False, "pauseSeconds": 2},
            {"lineCount": 11, "wordCount": 130, "trapHi": False, "trapLow": True, "pauseSeconds": 4},
        ]
        if segment_index % 2 == 1:
            base_screens.append({"lineCount": 3, "wordCount": 26, "trapHi": False, "trapLow": False, "pauseSeconds": 3})

        for i, s in enumerate(base_screens):
            s["screenIndex"] = i
            s["secondsTaken"] = random.randint(40, 65)
        return base_screens

    # ─── USER SELECTION FOR ANSWERS ─────────────────────────

    def get_user_answers(self, question_text: str, choice_list: list, num_answers: int) -> list:
        """Prompt user to select answer(s)."""
        print(f"\n  Question: {question_text}")
        print(f"\n  Options:")
        
        # Display choices with letters
        for i, choice in enumerate(choice_list):
            letter = chr(65 + i)
            text = choice.get('text', '(no text)')
            print(f"    {letter}) {text}")
        
        if num_answers > 1:
            print(f"\n  Select {num_answers} answers (e.g., 'A,C' or 'A C'):")
        else:
            print(f"\n  Select answer (A-{chr(65 + len(choice_list) - 1)}):")
        
        while True:
            user_input = input("  > ").strip().upper()
            
            # Parse letters
            selected = []
            for char in user_input.replace(',', ' ').split():
                if len(char) == 1 and 'A' <= char <= chr(64 + len(choice_list)):
                    idx = ord(char) - 65
                    if idx not in selected:
                        selected.append(idx)
            
            if len(selected) == num_answers:
                return selected
            elif len(selected) < num_answers:
                print(f"  Please select exactly {num_answers} answer(s). You selected {len(selected)}.")
            else:
                print(f"  Too many answers. Please select exactly {num_answers} answer(s).")

    # ─── QUESTIONS (MANUAL ANSWER) ─────────────────────────

    def answer_questions(self) -> bool:
        """Let user manually answer all questions."""
        question_num = 0

        while True:
            data = self._api_get('getNext.json')
            section_data = data.get('section', {}).get('data', {})
            name = section_data.get('name', data.get('section', {}).get('name', ''))

            # Done?
            if name in ('complete', 'result', 'select', 'start', 'reading', 'storyselect', ''):
                print(f"\n  ✓ All questions done! ({question_num} answered)")
                return True
            if name != 'question':
                print(f"  Section changed to: {name}")
                return True

            question_id = section_data.get('questionId')
            choice_list = section_data.get('choiceList', [])
            progress = section_data.get('questionProgress', [])
            total_qs = len(progress)
            go_on = section_data.get('goOn', False)

            # goOn / already-answered state — send acknowledgment to advance
            has_correct = any(
                c.get('status', {}).get('status') == 'correct' for c in choice_list
            )
            if go_on or has_correct:
                self._api_post('saveQuestion.json', {
                    "questionId": question_id,
                    "goOn": True
                })
                continue

            # Fresh question
            question_num += 1
            answered_so_far = len([p for p in progress if p.get('status') in ('correct', 'incorrect')])
            question_text = self.question_map.get(question_id, '')
            clues = self.question_clues.get(question_id, [])
            num_answers = section_data.get('correctAnswerCount', 1)

            print(f"\n{'─'*60}")
            print(f"  Question {answered_so_far + 1}/{total_qs}" +
                  (f"  (select {num_answers})" if num_answers > 1 else ""))
            print(f"{'─'*60}")
            
            # Show clue if available
            if clues:
                print(f"\n  📖 Clue: \"{clues[0][:120]}\"")
            
            # Show story snippet if available (optional)
            show_story = input("\n  Show story excerpt? (y/n): ").strip().lower()
            if show_story == 'y' and self.story_text:
                print(f"\n  📖 Story excerpt:\n  {self.story_text[:500]}...\n")
            
            # Get user's answer
            selected_indices = self.get_user_answers(question_text, choice_list, num_answers)
            
            # Submit answer
            result = self._api_post('saveQuestion.json', {
                "questionId": question_id,
                "clue": False,
                "excerpts": 0,
                "reread": False,
                "secondsTaken": random.randint(10, 30),
                "choiceList": selected_indices
            })
            
            # Check if answer was correct
            res_data = result.get('section', {}).get('data', {})
            res_choices = res_data.get('choiceList', [])
            
            # Show which answers were correct
            print("\n  Results:")
            for i, choice in enumerate(choice_list):
                letter = chr(65 + i)
                text = choice.get('text', '(no text)')
                status = res_choices[i].get('status', {}).get('status', 'unknown') if i < len(res_choices) else 'unknown'
                
                if status == 'correct':
                    print(f"  ✓ {letter}) {text} (CORRECT)")
                elif status == 'incorrect' and i in selected_indices:
                    print(f"  ✗ {letter}) {text} (INCORRECT)")
                elif status == 'incorrect':
                    print(f"    {letter}) {text}")
                else:
                    print(f"    {letter}) {text}")
            
            # If incorrect, give option to retry or continue
            if not res_data.get('goOn', False) and res_data.get('questionId') == question_id:
                retry = input("\n  Answer was incorrect. Try again? (y/n): ").strip().lower()
                if retry == 'y':
                    # Continue the loop to retry the same question
                    continue
                else:
                    # Force move on by using goOn
                    self._api_post('saveQuestion.json', {
                        "questionId": question_id,
                        "goOn": True
                    })
            
            # Small pause before next question
            time.sleep(1)

        return True

    # ─── FULL LESSON FLOW ─────────────────────────────────

    def complete_one_lesson(self, lesson_num: int) -> bool:
        print(f"\n{'='*60}")
        print(f"  LESSON {lesson_num}")
        print(f"{'='*60}")

        # Start reading session
        print("\n  [1/3] Starting reading...")
        start_data = self.start_reading()
        if not start_data:
            print("  ✗ Failed to start")
            return False

        section_name = start_data.get('section', {}).get('data', {}).get('name', '')

        if section_name == 'question':
            print("  → Already in questions phase, skipping reading")
        elif section_name in ('complete', ''):
            print(f"  → Section is '{section_name}', nothing to do")
            return True
        else:
            # Manual reading segments
            print("\n  [2/3] Reading segments...")
            if not self.read_segments():
                print("  ✗ Reading failed")
                return False
            
            # Ask for rating
            while True:
                try:
                    rating = int(input("\n  Rate this story (1-5 stars): ").strip())
                    if 1 <= rating <= 5:
                        break
                    print("  Please enter a number between 1 and 5")
                except ValueError:
                    print("  Please enter a number between 1 and 5")
            self.save_rating(rating)

        # Manual questions
        print("\n  [3/3] Answering questions...")
        if not self.answer_questions():
            print("  ✗ Questions failed")
            return False

        # Check completion — may be 'result' screen with score
        final = self._api_get('getNext.json')
        section = final.get('section', {})
        section_data = section.get('data', {})
        section_name = section_data.get('name', section.get('name', ''))

        if section_name == 'result':
            profile = section_data.get('profile', {})
            story = profile.get('story', {})
            score = story.get('scorePercent', '?')
            status = story.get('status', '')
            print(f"\n  ✅ LESSON {lesson_num} COMPLETE — Score: {score}% ({status})")
            # Dismiss the result screen for the next lesson
            input("\n  Press Enter to continue to next lesson...")
            self._api_post('saveResult', {"key": "rate-fast"})
            time.sleep(0.5)
        elif section_name == 'complete':
            score = section_data.get('score', '?')
            print(f"\n  ✅ LESSON {lesson_num} COMPLETE — Score: {score}%")
        else:
            print(f"\n  ✅ LESSON {lesson_num} finished (section: {section_name})")

        return True

    def run(self, count: int = 8):
        """Main entry: login then loop through lessons."""
        print("=" * 60)
        print(f"  READING PLUS CLI — {count} LESSONS")
        print("  📝 Manual answer mode")
        print("=" * 60)

        print("\n  Logging in...")
        if not self.login():
            return

        for i in range(1, count + 1):
            try:
                success = self.complete_one_lesson(i)
                if not success:
                    print(f"\n  ⚠️  Lesson {i} failed, stopping")
                    break
                if i < count:
                    cont = input(f"\n  Lesson {i} complete! Start next lesson? (y/n): ").strip().lower()
                    if cont != 'y':
                        print(f"\n  Stopped after {i} lessons.")
                        break
                    pause = random.randint(2, 5)
                    print(f"\n  ⏱️  Pausing {pause}s before next lesson...")
                    time.sleep(pause)
            except KeyboardInterrupt:
                print(f"\n\n  Stopped after {i-1} lessons.")
                return
            except Exception as e:
                print(f"\n  💥 CRASH on lesson {i}: {type(e).__name__}: {e}")
                break

        print("\n" + "=" * 60)
        print("  DONE")
        print("=" * 60)


if __name__ == "__main__":
    # How many lessons to run (default 8, or pass as arg)
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 8

    site_code = os.environ.get('RP_SITE_CODE', '')
    username = os.environ.get('RP_USERNAME', '')
    password = os.environ.get('RP_PASSWORD', '')

    cli = ReadingPlusCLI(site_code, username, password)
    cli.run(num)