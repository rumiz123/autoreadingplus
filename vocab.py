import requests
import subprocess
import re
import json
import zlib


def get_vocab_word():
    """
    Get vocabulary word from Reading Plus API
    """
    url = "https://student.readingplus.com/seereader/api/ra/getWord.json"

    headers = {
        "Host": "student.readingplus.com",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Sec-Ch-Ua": "\"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://student.readingplus.com/seereader/api/ra/startRA",
        # REMOVE Accept-Encoding to let requests handle decompression automatically
        "Priority": "u=1, i"
    }

    cookies = {
        "_biz_uid": "fe09ffed8d0c4a7db425184e68795413",
        "htjs_anonymous_id": "a25a6de7-796e-43e2-b942-b46bbad167b1",
        "_mkto_trk": "id:063-SDC-839&token:_mch-readingplus.com-c9a3b466b489bc1285a0965834a47e1",
        "_biz_flagsA": "%7B%22Version%22%3A1%2C%22XDomain%22%3A%221%22%2C%22ViewThrough%22%3A%221%22%2C%22Mkto%22%3A%221%22%7D",
        "ht-cm-preferences": "{%22version%22:1%2C%22destination%22:{}%2C%22custom%22:{%22Performance%20Cookies%22:true%2C%22Functional%20Cookies%22:true%2C%22Targeting%20Cookies%22:true}}",
        "tracking_consent_preferences": "Preferences Selected",
        "_biz_nA": "3",
        "_biz_pendingA": "%5B%5D",
        "de_anonymous_id": "a25a6de7-796e-43e2-b942-b46bbad167b1",
        "htjs_sesh": "{%22id%22:1770077512489%2C%22expiresAt%22:1770079317387%2C%22timeout%22:1800000%2C%22sessionStart%22:false%2C%22autoTrack%22:true}",
        "secure_login": "true",
        "school_code_4": "RPJOHNF1",
        "SESSION": "",
        "AWSALB": "Ffc/2K3S/l/IHwbWyLs2toKmcIsjddjedSq0TQTk82klTBRNUkH1T15T5VAEv0rhm3sl2v+QQ7T4eY4ehy9mhzuYExeZX6UADyT78YECAIbmfvuf5HUeSOZ8dtip",
        "AWSALBCORS": "Ffc/2K3S/l/IHwbWyLs2toKmcIsjddjedSq0TQTk82klTBRNUkH1T15T5VAEv0rhm3sl2v+QQ7T4eY4ehy9mhzuYExeZX6UADyT78YECAIbmfvuf5HUeSOZ8dtip"
    }

    try:
        print(f"📡 Requesting vocabulary word from: {url}")

        # Make request WITHOUT custom Accept-Encoding header
        # Let requests handle decompression automatically
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)

        print(f"✅ Status Code: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('content-type', 'Not specified')}")
        print(f"🔤 Content-Encoding: {response.headers.get('content-encoding', 'None')}")
        print(f"📏 Response size: {len(response.content)} bytes")

        # Check if response looks like JSON
        if response.text and response.text.strip().startswith('{'):
            try:
                data = response.json()
                print(f"🎯 Success! Got vocabulary data")
                return data
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"First 200 chars of response: {response.text[:200]}")

                # Check if it's HTML error page
                if '<!DOCTYPE' in response.text or '<html' in response.text.lower():
                    print("⚠️  Response appears to be HTML (likely login page or error)")
                    if 'login' in response.text.lower():
                        print("   Contains 'login' - session likely expired")
                return None
        else:
            print(f"❌ Response doesn't look like JSON")
            print(f"First 100 chars: {response.text[:100]}")
            return None

    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def check_ollama():
    """
    Check if Ollama is available
    """
    try:
        result = subprocess.run(['ollama', 'list'],
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='ignore',
                                timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'llama3.2' in line:
                    return 'llama3.2:latest'
                elif 'llama' in line:
                    parts = line.split()
                    if parts:
                        return parts[0]
        return None
    except:
        return None


def ask_ollama_similar_words(word, word_definition, flash_list, model_name):
    """
    Ask Ollama to find the most similar word from flashList
    """
    # Format the flash list options
    options_text = "\n".join([f"{i + 1}. {word_option}" for i, word_option in enumerate(flash_list)])

    prompt = f"""Word: {word}
Definition: {word_definition}

Find the word that is most similar in meaning to "{word}".

Options:
{options_text}

Which word is most similar? Answer with only the number (1, 2, 3, 4, or 5)."""

    print(f"\n🤖 Asking Ollama for similar word...")

    try:
        process = subprocess.Popen(
            ['ollama', 'run', model_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        stdout, stderr = process.communicate(input=prompt, timeout=20)

        if stdout:
            response = stdout.strip()
            print(f"Ollama response: '{response}'")

            # Extract any number from response
            numbers = re.findall(r'\d+', response)
            if numbers:
                num = int(numbers[0])
                # Validate it's in the correct range
                if 1 <= num <= len(flash_list):
                    return num - 1  # Return index (0-based)

            # Also check for single digit
            for char in response:
                if char.isdigit():
                    num = int(char)
                    if 1 <= num <= len(flash_list):
                        return num - 1

        # Default to first option
        return 0

    except Exception as e:
        print(f"Ollama error: {e}")
        return 0


def ask_ollama_two_correct_sentences(word, word_definition, sentence_list, model_name):
    """
    Ask Ollama to find TWO sentences that use the word correctly
    """
    # Format the sentence list options
    options_text = "\n".join([f"{i + 1}. {sentence}" for i, sentence in enumerate(sentence_list)])

    prompt = f"""Word: {word}
Definition: {word_definition}

Find TWO sentences that use the word "{word}" correctly according to its definition.

There are exactly 2 correct sentences. The other 3 are incorrect.

Options:
{options_text}

Answer with TWO numbers (like "2 3" or "1 5").
Example: If sentences 2 and 3 are correct, answer "2 3".
Example: If sentences 1 and 5 are correct, answer "1 5".

Which TWO sentences are correct? Answer with two numbers:"""

    print(f"\n🤖 Asking Ollama for 2 correct sentences...")

    try:
        process = subprocess.Popen(
            ['ollama', 'run', model_name],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        stdout, stderr = process.communicate(input=prompt, timeout=25)

        if stdout:
            response = stdout.strip()
            print(f"Ollama response: '{response}'")

            # Extract all numbers from response
            numbers = re.findall(r'\d+', response)
            if numbers:
                # Convert to integers and validate
                num_list = []
                for num_str in numbers:
                    num = int(num_str)
                    if 1 <= num <= len(sentence_list) and num not in num_list:
                        num_list.append(num)

                # If we have at least 2 numbers, return first 2
                if len(num_list) >= 2:
                    return [num_list[0] - 1, num_list[1] - 1]  # Convert to 0-based
                elif len(num_list) == 1:
                    # If only one number found, guess the second one
                    first = num_list[0] - 1
                    # Try to pick a different number
                    second = (first + 1) % len(sentence_list)
                    return [first, second]

            # Try to find patterns like "2 and 3" or "1, 5"
            patterns = [
                r'(\d+)\s+and\s+(\d+)',
                r'(\d+),\s*(\d+)',
                r'(\d+)\s+(\d+)',
                r'sentences?\s+(\d+)\s+and\s+(\d+)',
                r'(\d+)\s+&\s+(\d+)'
            ]

            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    try:
                        num1 = int(match.group(1))
                        num2 = int(match.group(2))
                        if 1 <= num1 <= len(sentence_list) and 1 <= num2 <= len(sentence_list):
                            return [num1 - 1, num2 - 1]
                    except:
                        continue

        # Default to first two options
        return [0, 1]

    except Exception as e:
        print(f"Ollama error: {e}")
        return [0, 1]


def test_connection():
    """
    Test if we can connect to Reading Plus
    """
    print("\n" + "=" * 60)
    print("🔗 CONNECTION TEST")
    print("=" * 60)

    test_url = "https://student.readingplus.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"✅ Can connect to Reading Plus (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Cannot connect to Reading Plus: {e}")
        return False


def get_fresh_cookies_instructions():
    """
    Show instructions for getting fresh cookies
    """
    print("\n" + "=" * 60)
    print("🔄 HOW TO GET FRESH COOKIES")
    print("=" * 60)
    print("""
1. Open Chrome/Edge browser
2. Go to https://student.readingplus.com
3. Log in with your credentials
4. Press F12 to open Developer Tools
5. Go to Network tab
6. Refresh the page (F5)
7. Look for any request to readingplus.com
8. Click on the request, scroll to 'Request Headers'
9. Find the 'Cookie:' header
10. Copy the entire cookie string
11. Update the cookies dictionary in this script

Most important cookies to update:
- SESSION (most important!)
- AWSALB
- AWSALBCORS
    """)


def main():
    print("=" * 60)
    print("📚 READING PLUS VOCABULARY HELPER")
    print("=" * 60)

    # First test connection
    if not test_connection():
        print("\n❌ Cannot connect to Reading Plus. Check your internet connection.")
        return

    # Check Ollama
    model_name = check_ollama()
    if not model_name:
        print("\n❌ Ollama not found. Please install and run Ollama first.")
        print("   Visit: https://ollama.com")
        print("   Then run: ollama pull llama3.2")
        return

    print(f"\n✅ Ollama model: {model_name}")

    # Get vocabulary data
    print("\n" + "=" * 60)
    print("📥 FETCHING VOCABULARY WORD")
    print("=" * 60)

    vocab_data = get_vocab_word()

    if not vocab_data:
        print("\n❌ Failed to get vocabulary data.")
        print("\nPossible issues:")
        print("1. 🍪 Cookies have expired (most likely)")
        print("2. 🔐 Not logged into Reading Plus")
        print("3. 📍 Wrong API endpoint")
        print("4. 🌐 Network issue")

        get_fresh_cookies_instructions()
        return

    # Check if we got valid data
    if 'result' not in vocab_data:
        print("\n❌ Invalid response structure")
        print("Response keys:", list(vocab_data.keys()))
        return

    if not vocab_data['result']:
        print(f"\n❌ Server returned error: {vocab_data.get('message', 'Unknown error')}")
        return

    print("✅ Successfully got vocabulary data!")

    # Extract data from response
    target_word = vocab_data.get('word', '')
    word_definition = vocab_data.get('about', '')

    if not target_word:
        print("❌ No word found in response")
        return

    # Extract flashList words
    flash_list = []
    if 'flashList' in vocab_data and vocab_data['flashList']:
        for flash_item in vocab_data['flashList']:
            if 'word' in flash_item:
                flash_list.append(flash_item['word'])

    # Extract sentenceList
    sentence_list = []
    if 'sentenceList' in vocab_data and vocab_data['sentenceList']:
        for sentence_item in vocab_data['sentenceList']:
            if 'sentence' in sentence_item:
                sentence_list.append(sentence_item['sentence'])

    # Display information
    print("\n" + "=" * 60)
    print("📖 VOCABULARY WORD")
    print("=" * 60)
    print(f"\n🎯 Word: {target_word}")
    print(f"📚 Definition: {word_definition}")

    # Display flash words
    if flash_list:
        print(f"\n📋 Similar Word Options ({len(flash_list)}):")
        for i, word in enumerate(flash_list):
            print(f"  {i + 1}. {word}")
    else:
        print("\n⚠️  No flash words found")
        return

    # Display sentences
    if sentence_list:
        print(f"\n📝 Sentence Options ({len(sentence_list)}):")
        for i, sentence in enumerate(sentence_list):
            # Highlight the target word in the sentence
            highlighted = sentence.replace(target_word, f"**{target_word}**")
            print(f"  {i + 1}. {highlighted}")
    else:
        print("\n⚠️  No sentences found")
        return

    # Ask Ollama for similar word
    print("\n" + "=" * 60)
    print("🤖 ANALYZING SIMILAR WORDS")
    print("=" * 60)

    similar_word_idx = ask_ollama_similar_words(target_word, word_definition, flash_list, model_name)

    # Ask Ollama for TWO correct sentences
    print("\n" + "=" * 60)
    print("🤖 ANALYZING CORRECT SENTENCES (NEED 2)")
    print("=" * 60)

    correct_sentence_indices = ask_ollama_two_correct_sentences(target_word, word_definition, sentence_list, model_name)

    # Display answers
    print("\n" + "=" * 60)
    print("✅ ANSWERS")
    print("=" * 60)

    # Similar word answer
    print(f"\n🎯 WORD SIMILARITY QUESTION:")
    print(f"   Target word: {target_word}")
    print(f"   ✅ Select: Option {similar_word_idx + 1}")
    print(f"   Word: {flash_list[similar_word_idx]}")

    # Two sentence answers
    print(f"\n📝 SENTENCE USAGE QUESTION (SELECT 2):")
    print(f"   Target word: {target_word}")

    # Sort indices for consistent display
    sorted_indices = sorted(correct_sentence_indices)

    print(f"   ✅ Select: Options {sorted_indices[0] + 1} and {sorted_indices[1] + 1}")

    print(f"\n   Selected Sentences:")
    for idx in sorted_indices:
        sentence = sentence_list[idx]
        highlighted = sentence.replace(target_word, f"**{target_word}**")
        print(f"   {idx + 1}. {highlighted}")

    # Show which ones to avoid
    all_indices = set(range(len(sentence_list)))
    selected_set = set(sorted_indices)
    avoid_indices = sorted(list(all_indices - selected_set))

    if avoid_indices:
        print(f"\n   ❌ Avoid these sentences:")
        for idx in avoid_indices:
            sentence = sentence_list[idx]
            highlighted = sentence.replace(target_word, f"**{target_word}**")
            print(f"   {idx + 1}. {highlighted}")

    # Quick reference
    print("\n" + "=" * 60)
    print("📋 QUICK REFERENCE")
    print("=" * 60)

    print(f"\nFor similar word to '{target_word}':")
    print(f"  ➡️  Select: {similar_word_idx + 1}")

    print(f"\nFor correct sentences with '{target_word}' (select 2):")
    print(f"  ➡️  Select: {sorted_indices[0] + 1} and {sorted_indices[1] + 1}")

    if avoid_indices:
        avoid_text = ", ".join([str(idx + 1) for idx in avoid_indices])
        print(f"  ❌ Avoid: {avoid_text}")

    print("\n" + "=" * 60)
    print("💡 TIP: Make sure you're on a vocabulary exercise in Reading Plus")
    print("       before running this script!")
    print("=" * 60)


if __name__ == "__main__":
    main()