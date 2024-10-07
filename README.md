
# README

## 프로젝트 설명

이 프로젝트는 OpenAI GPT-4o-mini와 Google Cloud TTS(텍스트 음성 변환) 서비스를 사용하여 유튜브 라이브 스트리밍에서 댓글을 수집하고, 이를 분석하여 음성으로 변환하는 시스템입니다. 이 시스템은 특정 액션을 트리거하는 기능도 포함하고 있습니다. 두 개의 주요 Python 스크립트가 사용됩니다.

## 파일 설명

### 1. `liveGenMain.py`

이 파일은 유튜브 채팅에서 실시간으로 댓글을 수집하고, OpenAI GPT-4o-mini API를 통해 해당 댓글을 분석한 후, Google Cloud TTS API를 사용하여 음성 파일(MP3)을 생성하는 기능을 합니다.

#### 주요 기능:

- **댓글 수집**: `pytchat` 라이브러리를 이용해 실시간으로 댓글을 수집합니다.
- **GPT-4o-mini 분석**: 수집된 댓글을 GPT-4o-mini API에 전송해 분석 결과와 관련된 액션을 추출합니다.
- **TTS 변환**: 분석 결과를 음성으로 변환하여 MP3 파일로 저장합니다.
- **액션 트리거**: GPT-4o-mini 응답에 따라 특정 행동(기쁨, 슬픔 등)을 트리거합니다.
- **에러 처리**: 예외 발생 시, 오류 메시지를 출력하고 대기 후 재시도하는 로직이 포함되어 있습니다.

### 2. `streamFlowMain.py`

이 파일은 생성된 MP3 파일을 재생하고, 특정 키 입력을 통해 액션을 트리거하는 기능을 제공합니다.

#### 주요 기능:

- **MP3 파일 재생**: `pygame` 라이브러리를 사용하여 MP3 파일을 재생합니다.
- **파일 우선순위 처리**: `source_priority` 폴더에 있는 MP3 파일을 우선적으로 처리합니다.
- **키 입력 트리거**: MP3 파일명에 포함된 액션 번호에 따라 특정 키 입력을 트리거합니다.
- **파일 이동**: 재생이 완료된 파일은 `source_priority_done` 폴더로 이동합니다.
- **파일 큐 처리**: 남은 파일을 처리하고, 새로운 파일이 있을 경우 자동으로 큐를 업데이트합니다.

## 설치 및 사용 방법

1. **필수 패키지 설치**:
   - 먼저, 다음 Python 패키지들을 설치해야 합니다:
     ```bash
     pip install google-cloud-texttospeech
     pip install pytchat
     pip install pygame
     pip install natsort
     ```

2. **구성 파일 (config.ini) 설정**:
   - `config.ini` 파일에서 OpenAI API 키와 유튜브 동영상 ID를 설정해야 합니다:
     ```
     [DEFAULT]
     OPEN_AI_API_KEY = your_openai_api_key
     YOUTUBE_VIDEO_ID = your_youtube_video_id
     ```

3. **실행**:
   - `liveGenMain.py` 파일을 실행하여 유튜브 댓글을 수집하고, 분석 및 음성 변환을 수행합니다:
     ```bash
     python liveGenMain.py
     ```
   - `streamFlowMain.py` 파일을 실행하여 MP3 파일을 재생하고, 액션을 트리거합니다:
     ```bash
     python streamFlowMain.py
     ```

## 폴더 구조

- `source`: MP3 파일이 저장되는 기본 폴더입니다.
- `source_priority`: 우선순위가 높은 MP3 파일이 저장되는 폴더입니다.
- `source_priority_done`: 재생이 완료된 MP3 파일이 이동되는 폴더입니다.
- `script`: 최근 재생된 파일 정보를 저장하는 폴더입니다.

## 주의사항

- 프로그램 실행 중 오류가 발생할 수 있으며, 이러한 경우 에러 로그가 출력되고 일정 시간 대기 후 재시도합니다.
- OpenAI 및 Google Cloud API 사용 시, 적절한 API 키 설정이 필요합니다.
