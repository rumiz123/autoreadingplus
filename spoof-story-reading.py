import requests
import json
import time
import random


def send_save_segment(segment_index, session_cookies):
    """
    Send saveSegment.json request with modified segmentIndex and random secondsTaken
    """
    url = "https://student.readingplus.com/seereader/api/sr/saveSegment.json"

    headers = {
        "Host": "student.readingplus.com",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": "\"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "Content-Type": "application/json;charset=UTF-8",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Origin": "https://student.readingplus.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://student.readingplus.com/seereader/api/sr/start",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i"
    }

    # Original payload structure
    base_payload = {
        "screenList": [
            {
                "screenIndex": 0,
                "lineCount": 12,
                "wordCount": 137,
                "secondsTaken": 365,  # Will be randomized
                "trapHi": True,
                "trapLow": False,
                "pauseSeconds": 12
            },
            {
                "screenIndex": 0,
                "lineCount": 12,
                "wordCount": 137,
                "secondsTaken": 43,  # Will be randomized
                "trapHi": False,
                "trapLow": False,
                "pauseSeconds": 53
            },
            {
                "screenIndex": 1,
                "lineCount": 12,
                "wordCount": 131,
                "secondsTaken": 346,  # Will be randomized
                "trapHi": True,
                "trapLow": False,
                "pauseSeconds": 10
            },
            {
                "screenIndex": 1,
                "lineCount": 12,
                "wordCount": 131,
                "secondsTaken": 67,  # Will be randomized
                "trapHi": False,
                "trapLow": False,
                "pauseSeconds": 2
            },
            {
                "screenIndex": 2,
                "lineCount": 3,
                "wordCount": 26,
                "secondsTaken": 74,  # Will be randomized
                "trapHi": False,
                "trapLow": False,
                "pauseSeconds": 8
            }
        ],
        "segmentIndex": segment_index
    }

    # Randomize secondsTaken for each screen entry
    for screen in base_payload["screenList"]:
        # Random value between 1-5 seconds (more realistic)
        screen["secondsTaken"] = random.randint(40, 67)

    try:
        print(f"Sending saveSegment request with segmentIndex={segment_index}...")
        response = requests.post(url, headers=headers, cookies=session_cookies, json=base_payload)

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return True
            except:
                print(f"Response: {response.text[:200]}")
                return True
        else:
            print(f"Error: {response.status_code} - {response.text[:200]}")
            return False

    except Exception as e:
        print(f"Request failed: {e}")
        return False


def send_save_rating(rating, session_cookies):
    """
    Send saveRating.json request
    """
    url = "https://student.readingplus.com/seereader/api/sr/saveRating.json"

    headers = {
        "Host": "student.readingplus.com",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": "\"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "Content-Type": "application/json;charset=UTF-8",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Origin": "https://student.readingplus.com",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://student.readingplus.com/seereader/api/sr/start",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i"
    }

    payload = {
        "rating": rating
    }

    try:
        print(f"\nSending saveRating request with rating={rating}...")
        response = requests.post(url, headers=headers, cookies=session_cookies, json=payload)

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                return True
            except:
                print(f"Response: {response.text[:200]}")
                return True
        else:
            print(f"Error: {response.status_code} - {response.text[:200]}")
            return False

    except Exception as e:
        print(f"Request failed: {e}")
        return False


def main():
    print("=" * 60)
    print("READING PLUS SEGMENT & RATING SENDER")
    print("=" * 60)

    # Cookies from your request
    session_cookies = {
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
        "AWSALB": "pVfGTvby85nZiqaExpdlb63HClo6ciAMAtmprLQZyDf5sc7nr6pHAM80GIiBvVoVpwLLoRUIuw5K8nBvwbhHxe0elUurzAafDXQydNrr/zSaOgqPtE5QDTQ/uCAh",
        "AWSALBCORS": "pVfGTvby85nZiqaExpdlb63HClo6ciAMAtmprLQZyDf5sc7nr6pHAM80GIiBvVoVpwLLoRUIuw5K8nBvwbhHxe0elUurzAafDXQydNrr/zSaOgqPtE5QDTQ/uCAh"
    }

    print("\nSending 4 saveSegment requests...")
    print("-" * 40)

    # Send 4 saveSegment requests with increasing segmentIndex
    success_count = 0
    for i in range(1, 5):  # segmentIndex 1 through 4
        success = send_save_segment(i, session_cookies)
        if success:
            success_count += 1

    print(f"\n✓ Successfully sent {success_count}/4 segment requests")

    # Wait a bit before sending rating
    print("\n" + "-" * 40)
    print("Preparing to send rating request...")
    time.sleep(random.uniform(1.0, 3.0))

    # Send saveRating request
    rating = 3  # You can change this if needed
    rating_success = send_save_rating(rating, session_cookies)

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"Segment requests: {success_count}/4 successful")
    print(f"Rating request: {'Successful' if rating_success else 'Failed'}")

    if success_count == 4 and rating_success:
        print("\n✅ All requests completed successfully!")
    else:
        print("\n⚠️  Some requests may have failed")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()