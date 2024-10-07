import os
import shutil
import time
import pygame
from natsort import natsorted 

# 폴더 경로 설정
folder_path = r'.\source'
priority_folder = r'.\source_priority'
done_folder = r'.\source_priority_done'
recent_file_path = r'.\script\recent.txt'

# 초기 pygame 설정
pygame.mixer.init()

def play_mp3(file_path):
    """MP3 파일을 재생하고 완료되면 콜백으로 처리"""
    print(f"현재 재생 중인 파일: {file_path}")  # 재생 중인 파일 출력
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)  # 파일이 끝날 때까지 대기
    pygame.mixer.music.unload()  # 재생이 끝난 후 파일에 대한 참조 해제

def log_recent_file(file_name):
    """재생된 파일명을 기록"""
    with open(recent_file_path, 'w') as f:
        f.write(file_name)

def move_file_safely(src, dst_folder):
    """파일을 안전하게 이동"""
    base_name = os.path.basename(src)
    dst = os.path.join(dst_folder, base_name)
    
    while True:
        try:
            shutil.move(src, dst)
            break
        except PermissionError:
            print(f"파일 이동 대기 중: {src}")
            time.sleep(1)  # 파일 사용이 해제될 때까지 대기

import ctypes
import time

# 가상 키 코드를 정의 (숫자 0~9)
VK_CODE = {
    '0': 0x30,
    '1': 0x31,
    '2': 0x32,
    '3': 0x33,
    '4': 0x34,
    '5': 0x35,
    '6': 0x36,
    '7': 0x37,
    '8': 0x38,
    '9': 0x39
}

def press_and_release_key(num):
    hexKeyCode = VK_CODE.get(str(num))  # 숫자에 해당하는 가상 키 코드 가져오기
    if hexKeyCode:
        # 키 누르기
        ctypes.windll.user32.keybd_event(hexKeyCode, 0, 0, 0)
        time.sleep(0.05)  # 약간의 대기
        # 키 떼기
        ctypes.windll.user32.keybd_event(hexKeyCode, 0, 2, 0)
    else:
        raise ValueError("숫자는 0에서 9 사이여야 합니다.")
    
def extract_action_number(file_name):
    """파일명에서 액션 번호를 추출"""
    base_name = os.path.splitext(file_name)[0]  # 확장자를 제거한 파일명 (시간_액션번호)
    try:
        _, action_number = base_name.split('_')  # _로 분리하여 액션 번호 추출
        
        # 액션 번호가 숫자인지 확인
        if action_number.isdigit() and 0 <= int(action_number) <= 9:
            return action_number
        else:
            raise ValueError(f"잘못된 액션 번호: {action_number}. 액션 번호는 0에서 9 사이의 숫자여야 합니다.")
    except ValueError as e:
        print(e)  # 파일명 형식이 다르거나 액션 번호가 잘못된 경우 예외 메시지 출력
        return None  # 파일명 형식이 다르면 None 반환

def process_priority_files():
    """우선 폴더의 파일을 재생하고 이동"""
    priority_files = [f for f in os.listdir(priority_folder) if f.endswith('.mp3')]
    if priority_files:
        for file_name in priority_files:
            file_path = os.path.join(priority_folder, file_name)

            # 액션 번호 추출 및 키 입력 시도
            action_number = extract_action_number(file_name)
            if action_number:
                press_and_release_key(action_number)  # 숫자에 대한 키 이벤트 실행

            # MP3 파일 재생
            play_mp3(file_path)
            move_file_safely(file_path, done_folder)  # 완료 후 done_folder로 이동
        return True
    return False


def process_regular_files(file_queue):
    """일반 폴더의 파일을 순차적으로 재생"""
    while file_queue:
        file_name = file_queue.pop(0)
        file_path = os.path.join(folder_path, file_name)
        log_recent_file(os.path.splitext(file_name)[0])
        time.sleep(0.5)
        play_mp3(file_path)
        time.sleep(0.5)
        if process_priority_files():
            return file_queue  # 우선 파일이 발견되면 남은 파일 큐를 반환
    return file_queue  # 모든 파일이 재생된 후 남은 큐를 반환 (빈 리스트)

def main():
    """메인 실행 루프"""
    # 처음에 파일 리스트를 자연 정렬하여 가져옴
    file_queue = natsorted([f for f in os.listdir(folder_path) if f.endswith('.mp3')])  
    while True:
        # 우선 폴더의 파일을 먼저 처리
        if process_priority_files():
            continue  # 우선 폴더의 파일을 재생한 후 루프를 다시 시작
        
        # 일반 파일을 순차적으로 재생
        if not file_queue:  # 큐가 비어 있으면 새로 로드
            # 자연 정렬하여 파일 리스트 갱신
            file_queue = natsorted([f for f in os.listdir(folder_path) if f.endswith('.mp3')])  
        file_queue = process_regular_files(file_queue)

        # 파일이 전혀 없을 경우 잠시 대기 후 다시 시도
        if not file_queue and not os.listdir(priority_folder):
            time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("프로그램이 종료되었습니다.")
    finally:
        pygame.mixer.quit()
