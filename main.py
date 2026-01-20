# -*- coding: utf-8 -*-
import os
import requests
import base64
import urllib3
from google import genai
import time
import random

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASS = os.environ.get("WP_APP_PASS")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 모델 설정
MODEL_NAME = "gemini-2.5-flash"
client = genai.Client(api_key=GEMINI_API_KEY)

def get_search_friendly_topic():
    """
    사람들이 검색창에 실제로 입력할 법한 '고수요 키워드' 주제를 뽑습니다.
    """
    print("🕵️‍♀️ 사람들이 검색할 만한 핫 토픽 찾는 중...")
    try:
        prompt = """
        당신은 SEO(검색 최적화) 전문가이자 베테랑 블로거입니다.
        현재 시점에서 대중들이 가장 궁금해하고 검색량이 많을 법한 '생활 밀착형 정보' 또는 'IT/테크 꿀팁' 주제를 하나만 추천하세요.
        
        [필수 조건]
        1. 타겟: 20대~40대 일반인 (어려운 전문 용어 금지).
        2. 분야: 스마트폰 숨은 기능, 넷플릭스/유튜브 꿀팁, 최신 AI 활용법, 생활 속 과학 원리 중 택 1.
        3. 형식: 검색어 형태로 간결하게. (예: 아이폰 배터리 성능 100% 유지하는 법)
        4. 안전: 정치/종교/비방/성적 내용 절대 금지.
        
        군더더기 없이 '주제'만 딱 출력하세요.
        """
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        topic = response.text.strip().replace('"', '').replace("'", "")
        return topic
    except Exception as e:
        print(f"❌ 주제 선정 실패: {e}")
        return "스마트폰 속도가 느려질 때 해결하는 3가지 방법" # 비상용 주제

def upload_image_to_wp(image_url, title):
    print(f"📥 이미지 다운로드 중... ({image_url})")
    try:
        image_data = requests.get(image_url).content
        filename = f"blog_img_{int(time.time())}.png"
        
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
            print("✅ 미디어 업로드 성공!")
            return response.json()['id']
        else:
            print(f"❌ 미디어 업로드 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 이미지 처리 오류: {e}")
        return None

def auto_posting():
    print("------------ [플럭시 블로그 봇 가동] ------------")
    
    # 1. 주제 선정
    topic = get_search_friendly_topic()
    print(f"🔥 오늘의 포스팅 주제: {topic}")

    # 2. 글쓰기 (플럭시 페르소나 적용)
    print("✍️ '플럭시'가 글을 작성하고 있습니다...")
    
    prompt = f"""
    당신은 '플럭시(Fluxy)'라는 닉네임을 쓰는 친근한 IT/정보 블로거입니다.
    주제: '{topic}'에 대해 블로그 포스팅을 작성하세요.

    [페르소나: 플럭시]
    - 말투: "안녕하세요! 플럭시입니다" 같은 기계적인 인사는 하지 마세요. 대신, 실제 사람이 겪은 경험담처럼 자연스럽게 시작하세요.
    - 톤앤매너: 친한 친구나 동료에게 "이거 진짜 좋더라"라고 알려주는 듯한 '해요체' 사용. (이모지 적절히 섞어서)
    - 특징: 어려운 기술 용어는 쉽게 풀어서 설명하고, 독자의 궁금증을 긁어주는 해결사 역할.

    [글 구성]
    1. **매력적인 제목**: 검색 클릭을 유도하는 제목 (예: ~하는 방법, ~의 진실).
    2. **도입부**: "저도 처음엔 몰랐는데..." 처럼 공감대를 형성하며 시작.
    3. **본문**: 정보 전달 (핵심 포인트 3가지로 요약).
    4. **결론**: 요약 및 "다음에 더 좋은 팁으로 돌아올게요, 지금까지 플럭시였습니다!" 식의 자연스러운 마무리.

    [형식]
    - HTML 태그 사용 (<h2>, <p>, <ul>, <li>, <b> 등).
    - 가독성을 위해 문단은 짧게 끊을 것.
    - 비방, 혐오 표현 절대 금지.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        content = response.text
        
        # 제목 추출
        title = topic
        lines = content.split('\n')
        first_line = lines[0].strip()
        if "제목:" in first_line or "# " in first_line:
            title = first_line.replace("제목:", "").replace("#", "").strip()
            content = "\n".join(lines[1:])
        elif len(first_line) < 100 and len(first_line) > 5:
             title = first_line
             content = "\n".join(lines[1:])

    except Exception as e:
        print(f"❌ 글쓰기 에러: {e}")
        return

    # 3. 이미지 생성 (대중적이고 깔끔한 스타일)
    print("🎨 블로그용 대표 이미지 생성 중...")
    # 프롬프트 수정: 밝고, 깨끗하고, 감성적인 'Unsplash' 스타일의 고화질 사진
    # 주제에 따라 현대적인 데스크 셋업이나 추상적인 표현 사용
    image_prompt = f"high quality photography, realistic, bright and airy, minimalist, modern desk setup or abstract representation of {topic}, professional stock photo style, 4k, soft lighting"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1024&height=600&nologo=true&seed={int(time.time())}"
    
    featured_media_id = upload_image_to_wp(image_url, topic)

    # 4. 발행
    print("📤 워드프레스로 발행 중...")
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
        print(f"🎉 포스팅 완료! ID: {response.json()['id']}")
    else:
        print(f"❌ 발행 실패: {response.text}")

# 실행
auto_posting()
