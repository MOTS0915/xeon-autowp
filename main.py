# -*- coding: utf-8 -*-
import os
print("------------ [1] 파이썬 스크립트 시작 ------------")

import requests
import base64
import urllib3
from google import genai
import random
import time

print("------------ [2] 라이브러리 로드 완료 ------------")

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASS = os.environ.get("WP_APP_PASS")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 모델 설정 (Gemini 2.5 Flash - 안전성 최우선)
MODEL_NAME = "gemini-2.5-flash"

def get_tech_topic():
    topics = [
        "차세대 반도체 패키징 기술", "자율주행 LiDAR 센서 기술",
        "스마트홈 Matter 표준 분석", "국방용 드론 제어 기술",
        "전고체 배터리 상용화 난제", "Edge AI와 임베디드 비전",
        "6G 통신과 테라헤르츠 기술", "금속 3D 프린팅 산업 적용",
        "전기차 BMS 핵심 알고리즘", "양자 암호 통신 기술"
    ]
    return random.choice(topics)

def upload_image_to_wp(image_url, title):
    print(f"📥 이미지 다운로드 시도... ({image_url})")
    try:
        image_data = requests.get(image_url).content
        filename = f"tech_{int(time.time())}.png"
        
        # 인증 정보 인코딩
        credentials = f"{WP_USER}:{WP_APP_PASS}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "image/png"
        }

        media_url = WP_URL.replace("/posts", "/media")
        response = requests.post(media_url, headers=headers, data=image_data, verify=False)

        if response.status_code == 201:
            print("✅ 이미지 업로드 성공!")
            return response.json()['id']
        else:
            print(f"❌ 이미지 업로드 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 이미지 처리 중 에러: {e}")
        return None

def auto_posting():
    print("------------ [3] 자동 포스팅 함수 시작 ------------")
    
    topic = get_tech_topic()
    print(f"🚀 주제 선정: {topic}")
    print(f"🧠 모델 사용: {MODEL_NAME}")

    # Gemini 클라이언트 연결
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"❌ API 키 오류: {e}")
        return

    # 글쓰기 요청
    print("✍️ Gemini에게 글쓰기 요청 중...")
    prompt = f"""
    전문 엔지니어로서 '{topic}'에 대한 기술 블로그를 작성하세요.
    - 대상: 엔지니어
    - 구성: 서론, 기술적 특징(3가지), 결론
    - 분량: 2000자 이상
    - 형식: HTML 태그(<h2>, <p>, <ul>) 사용
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        content = response.text
        title = topic # 제목 단순화 (오류 방지)
        
        # 제목 추출 시도
        first_line = content.split('\n')[0]
        if len(first_line) < 50 and "<h1>" not in first_line:
            title = first_line.replace("#", "").strip()

    except Exception as e:
        print(f"❌ 글쓰기 실패: {e}")
        return

    # 이미지 생성
    print("🎨 이미지 생성 요청 중 (Pollinations)...")
    image_prompt = f"futuristic technology {topic}, unreal engine render"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1024&height=600&nologo=true&seed={int(time.time())}"
    
    featured_media_id = upload_image_to_wp(image_url, topic)

    # 워드프레스 발행
    print("📤 워드프레스로 전송 중...")
    credentials = f"{WP_USER}:{WP_APP_PASS}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }
    
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [1]
    }
    
    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    response = requests.post(WP_URL, headers=headers, json=post_data, verify=False)
    
    if response.status_code == 201:
        print(f"🎉 성공! 글이 발행되었습니다. ID: {response.json()['id']}")
    else:
        print(f"❌ 발행 실패: {response.text}")

# [중요] 조건문 없이 바로 실행 (들여쓰기 없음)
auto_posting()