import requests
import subprocess
import re


def get_next_question():
    url = "https://student.readingplus.com/seereader/api/sr/getNext.json"

    headers = {
        "Host": "student.readingplus.com",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": "\"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Sec-Ch-Ua-Mobile": "?0",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://student.readingplus.com/seereader/api/sr/start",
        "Priority": "u=1, i"
    }

    cookies = {
        "events_identify_sent": "true",
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
        "login_form": "student",
        "SESSION": "ZDlmYjRjOWYtMjI5NS00MmNhLTk4MzAtNzViY2I2ZmRhNTY0",
        "AWSALB": "Ffc/2K3S/l/IHwbWyLs2toKmcIsjddjedSq0TQTk82klTBRNUkH1T15T5VAEv0rhm3sl2v+QQ7T4eY4ehy9mhzuYExeZX6UADyT78YECAIbmfvuf5HUeSOZ8dtip",
        "AWSALBCORS": "Ffc/2K3S/l/IHwbWyLs2toKmcIsjddjedSq0TQTk82klTBRNUkH1T15T5VAEv0rhm3sl2v+QQ7T4eY4ehy9mhzuYExeZX6UADyT78YECAIbmfvuf5HUeSOZ8dtip"
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
        return response.json()
    except:
        return None


def get_story_content(story_id):
    url = f"https://content.readingplus.com/rp-content/ssr/{story_id}.json"

    headers = {
        "Host": "content.readingplus.com",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": "\"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Sec-Ch-Ua-Mobile": "?0",
        "Accept": "*/*",
        "Origin": "https://student.readingplus.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://student.readingplus.com/",
        "Priority": "u=1, i"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except:
        return None


def extract_question_and_passage(story_data, question_id):
    if not story_data or 'questionList' not in story_data:
        return None, None

    for question in story_data['questionList']:
        if question.get('id') == question_id:
            question_text = question.get('question', '')
            passage_text = ""

            if 'reRead' in question and question['reRead']:
                for passage in question['reRead']:
                    if 'words' in passage:
                        passage_text += ' '.join(passage['words']) + '\n'

            elif 'excerptList' in question and question['excerptList']:
                for excerpt in question['excerptList']:
                    if 'sectionList' in excerpt:
                        for section in excerpt['sectionList']:
                            if 'paragraphList' in section:
                                for paragraph in section['paragraphList']:
                                    if 'sentenceList' in paragraph:
                                        for sentence in paragraph['sentenceList']:
                                            if 'words' in sentence:
                                                passage_text += ' '.join(sentence['words']) + '\n'

            if not passage_text and 'segmentList' in story_data:
                for segment in story_data['segmentList'][:2]:
                    if 'paragraphList' in segment:
                        for paragraph in segment['paragraphList'][:3]:
                            if 'words' in paragraph:
                                passage_text += ' '.join(paragraph['words']) + '\n'

            return question_text.strip(), passage_text.strip()

    return None, None


def main():
    # Get question
    question_data = get_next_question()
    if not question_data:
        print("Failed to get question")
        return

    # Extract data
    section_data = question_data.get('section', {}).get('data', {})
    story_id = section_data.get('storyId')
    question_id = section_data.get('questionId')

    if not story_id or not question_id:
        print("Failed to extract IDs")
        return

    # Get choices
    choices_data = section_data.get('choiceList', [])
    choices = [choice.get('text', '').strip() for choice in choices_data]

    # Get story content
    story_data = get_story_content(story_id)
    question_text = ""
    passage_text = ""

    if story_data:
        question_text, passage_text = extract_question_and_passage(story_data, question_id)
    print("Question:")
    print(question_text + "?")
    print("Passage:")
    print(passage_text)
    print("Choices:")
    print(choices)

if __name__ == "__main__":
    main()