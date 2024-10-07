import threading
import time
from google.cloud import texttospeech
from datetime import datetime
import pytchat
import os
from openai import OpenAI
import sys
import json  # JSON 처리를 위해 추가
import configparser  # 설정 파일 파싱을 위해 추가

# 설정 파일 읽기
config = configparser.ConfigParser()
config.read('config.ini')  # 프로젝트 경로의 config.ini 파일 읽기

# 설정에서 값 가져오기
OPEN_AI_API_KEY = config.get('DEFAULT', 'OPEN_AI_API_KEY')
YOUTUBE_VIDEO_ID = config.get('DEFAULT', 'YOUTUBE_VIDEO_ID')

# 댓글을 저장할 리스트
comments_storage = []
comments_lock = threading.Lock()

# 전역 변수
client = OpenAI(api_key=OPEN_AI_API_KEY)  # 설정에서 가져온 API 키 사용

# TTS 클라이언트 설정
tts_client = texttospeech.TextToSpeechClient()

# MP3 파일을 저장할 경로
mp3_save_path = "C:/src/egoTuber/source_priority"

def save_gpt_response_as_audio(gpt_response_text, action):
    try:
        print("**[DEBUG] TTS 변환 시작**")
        # 현재 시간을 이용하여 파일명 생성
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{current_time}_{action}.mp3"  # 파일명에 action 값 포함
        file_path = os.path.join(mp3_save_path, file_name)  # 저장할 파일의 전체 경로

        # TTS 요청 설정
        synthesis_input = texttospeech.SynthesisInput(text=gpt_response_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Standard-B",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # TTS 요청 수행
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # MP3 파일로 저장
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
            print(f'Audio content written to file "{file_path}"')
    
    except Exception as e:
        print(f"**[ERROR] TTS 변환 중 오류 발생: {e}**")  # ERROR LOG

# 유튜브 댓글을 가져오고, 댓글을 저장하는 함수 (메인 스레드에서 실행)
def collect_comments(video_id):
    while True:
        try:
            chat = pytchat.create(video_id=video_id)
            while chat.is_alive():
                with comments_lock:
                    for c in chat.get().sync_items():
                        comment = f"{c.datetime} [{c.author.name}]- {c.message}"
                        print(comment)
                        comments_storage.append(comment)
                time.sleep(1)  # 잠시 대기 후 다음 댓글 수집
        except Exception as e:
            print(f"**[ERROR] 댓글 수집 중 오류 발생: {e}**")  # ERROR LOG
            time.sleep(5)  # 오류 발생 시 잠시 대기 후 재시도

# GPT 호출을 1초 간격으로 수행하는 스레드 함수
def call_gpt_periodically():
    wait_time_after_gpt = 10  # GPT 응답을 받은 후 기다릴 시간 (초)
    check_interval = 1  # 댓글을 체크할 기본 주기 (초)
    last_gpt_call_time = 0  # 마지막 GPT 호출 시간

    while True:
        current_time = time.time()

        with comments_lock:
            if len(comments_storage) >= 1:  # 최소 댓글 수 임계값 설정
                print("**[DEBUG] 충분한 댓글 수집됨, GPT 호출 준비**")
                if current_time - last_gpt_call_time >= wait_time_after_gpt:  # 10초가 지난 경우에만 GPT 호출
                    recent_mentions = get_recent_mentions()
                    gpt_response_text, action = send_comments_to_gpt(comments_storage, recent_mentions)
                    print(f"\nGPT 응답: {gpt_response_text}")
                    print(f"**[DEBUG] 행동(action): {action}**")  # action 출력

                    # TTS로 변환하여 저장을 별도의 스레드에서 수행
                    tts_thread = threading.Thread(target=save_gpt_response_as_audio, args=(gpt_response_text, action))
                    tts_thread.start()

                    comments_storage.clear()  # 처리된 댓글 리스트 초기화
                    last_gpt_call_time = current_time  # 마지막 GPT 호출 시간을 현재 시간으로 설정

        time.sleep(check_interval)  # 댓글을 체크할 기본 주기 동안 대기

# 최근 언급 내용 가져오기 (임시 데이터 반환)
def get_recent_mentions():
    script_dir = "C:/src/egoTuber/script"
    
    # 최근 파트 번호를 저장한 파일 경로
    recent_file_path = os.path.join(script_dir, "recent.txt")
    
    try:
        # 현재 파트 번호 읽어오기
        with open(recent_file_path, 'r') as recent_file:
            current_part = int(recent_file.read().strip())
        
        # 앞의 2개 파트와 현재 파트 번호 계산 (최소값은 1)
        part_numbers = [max(current_part - 2, 1), max(current_part - 1, 1), current_part]
        
        # 중복 제거
        part_numbers = list(dict.fromkeys(part_numbers))
        
        recent_mentions = []
        for part_number in part_numbers:
            part_file_path = os.path.join(script_dir, f"{part_number}.txt")
            if os.path.exists(part_file_path):
                with open(part_file_path, 'r', encoding="utf-8") as part_file:
                    part_content = part_file.read().strip()
                    recent_mentions.append(part_content)
            else:
                print(f"**[WARNING] {part_number}.txt 파일을 찾을 수 없습니다.**")  # WARNING LOG

        # 모든 파트 내용을 결합하여 반환
        return "\n".join(recent_mentions)
    
    except Exception as e:
        print(f"**[ERROR] 최근 언급 내용을 가져오는 중 오류 발생: {e}**")  # ERROR LOG
        return "최근 언급 내용을 가져오는 중 오류 발생."

# GPT에게 댓글과 최근 언급 내용 전달 및 응답 받기
def send_comments_to_gpt(comments, recent_mentions):
    try:
        # 메시지 내용 출력
        messages = [
            {"role": "system", "content": (
                "너는 유튜브로 방송하고 있는 사람이야. 언급한 내용과 댓글을 보고 아래 조건에 맞춰 응답해줘."
                "### 조건 ###"
                "1. 인사와 이모티콘은 생략한다."
                "2. 누구에 대한 응답인지 닉네임을 언급해준다."
                "3. 최대한 짧게, 친근감 있게, 존댓말, 대화체를 사용한다."
                "4. 응답은 'response' 키에, 행동은 'action' 키에 JSON 형식으로 제공한다."
                "5. 행동은 다음 중 하나를 선택한다: 1(기쁨), 2(슬픔), 3(분노), 4(공포), 5(혐오), 6(놀람)."
            )},
            {"role": "user", "content": (
                "언급한 내용:\n" + recent_mentions + "\n\n"
                "댓글:\n" + "\n".join(comments) + "\n\n"
            )}
        ]

        # 메시지 출력
        print(f"\nGPT 전달: {messages}")

        # GPT API 호출
        completion = client.chat.completions.create(
            model="gpt-4",  # 모델명을 실제 사용하시는 것으로 변경하세요.
            messages=messages
        )
        
        # GPT의 응답을 JSON으로 파싱
        gpt_response_content = completion.choices[0].message.content.strip()
        print(f"**[DEBUG] GPT 원본 응답: {gpt_response_content}**")

        # JSON 문자열로 변환 (따옴표 처리)
        if gpt_response_content.startswith("```json"):
            gpt_response_content = gpt_response_content.strip("```json").strip("```").strip()
        elif gpt_response_content.startswith("```"):
            gpt_response_content = gpt_response_content.strip("```").strip()
        elif gpt_response_content.startswith("{") and gpt_response_content.endswith("}"):
            pass  # 이미 JSON 형식인 경우 그대로 사용
        else:
            # JSON이 아닌 경우 예외 처리
            raise ValueError("GPT 응답이 올바른 JSON 형식이 아닙니다.")

        # JSON 파싱
        gpt_response_json = json.loads(gpt_response_content)

        # 'response'와 'action' 추출
        response_text = gpt_response_json.get('response', '')
        action = gpt_response_json.get('action', '')

        return response_text, action

    except Exception as e:
        print(f"**[ERROR] GPT API 호출 중 오류 발생: {e}**")  # ERROR LOG
        return "GPT API 호출 중 오류 발생.", None  # 오류 발생 시 기본값 반환

# Main execution
if __name__ == "__main__":
    video_id = YOUTUBE_VIDEO_ID  # 설정에서 가져온 동영상 ID 사용

    # GPT 호출 스레드 시작
    gpt_thread = threading.Thread(target=call_gpt_periodically)
    gpt_thread.start()

    # 댓글 수집 함수는 메인 스레드에서 실행
    collect_comments(video_id)

    # GPT 호출 스레드가 종료되지 않도록 메인 스레드 대기
    gpt_thread.join()
