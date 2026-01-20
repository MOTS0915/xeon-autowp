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

client = genai.Client(api_key=GEMINI_API_KEY)

# 🚀 모델 설정 (안정성 위주)

MODELS_TO_TRY = ["gemini-flash-latest", "gemini-2.5-flash","gemini-2.0-flash-lite"]

def generate_content_with_retry(prompt):
    """
    에러가 나면 다음 모델로 바꿔가며 끝까지 시도하는 좀비 함수
    """
    for model in MODELS_TO_TRY:
        try:
            print(f"📡 연결 시도 중... (Model: {model})")
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"⚠️ {model} 에러 발생: {e}")
            print("⏳ 3초 후 다른 모델로 재시도합니다...")
            time.sleep(3)
            continue
            
    raise Exception("❌ 모든 AI 모델이 응답하지 않습니다.")

def get_recent_posts():
    """
    워드프레스에서 최근 작성한 글들의 제목을 가져옵니다. (중복 방지용)
    """
    print("📚 기존에 작성한 글 목록을 조회합니다...")
    try:
        # 최근 10개 글만 가져옴
        response = requests.get(WP_URL, params={'per_page': 10}, verify=False)
        if response.status_code == 200:
            posts = response.json()
            titles = [post['title']['rendered'] for post in posts]
            print(f"✅ 최근 글 {len(titles)}개를 확인했습니다.")
            return titles
        else:
            print("⚠️ 글 목록 조회 실패 (무시하고 진행)")
            return []
    except Exception as e:
        print(f"⚠️ 글 목록 조회 중 에러: {e}")
        return []

def get_search_friendly_topic(existing_titles):
    print("🕵️‍♀️ 사람들이 검색할 만한 핫 토픽 찾는 중...")
    
    # 이미 쓴 글 목록을 텍스트로 변환
    exclude_list = ", ".join(existing_titles)
    
    try:
        prompt = f"""
        당신은 트렌드 분석가이자 베테랑 블로거입니다.
        대중들이 궁금해할 만한 '생활/IT 꿀팁' 주제를 하나만 추천하세요.
        
        [필수 조건]
        1. 타겟: 2040 일반인 (쉬운 내용).
        2. 분야: 스마트폰/PC 꿀팁, 최신 앱 활용법, 생활 속 과학/상식.
        3. 형식: 검색어 형태 (예: 배터리 수명 늘리는 법).
        
        [⛔ 제외할 주제 (절대 중복 금지)]
        이미 다음 주제들은 작성했습니다. 이와 비슷하거나 겹치는 내용은 절대 추천하지 마세요:
        {exclude_list}
        
        새롭고 신선한 주제 딱 한 줄만 출력하세요.
        """
        topic = generate_content_with_retry(prompt).strip().replace('"', '').replace("'", "")
        return topic
    except Exception as e:
        print(f"❌ 주제 선정 실패: {e}")
        return "스마트폰 저장공간 확보하는 확실한 방법" # 비상용 주제

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
            return None
    except Exception as e:
        print(f"❌ 이미지 처리 오류: {e}")
        return None

def auto_posting():
    print("------------ [플럭시 블로그 봇 V3.0 (중복 방지 & 인간미 탑재)] ------------")
    
    # 1. 기존 글 확인 및 주제 선정
    recent_titles = get_recent_posts()
    topic = get_search_friendly_topic(recent_titles)
    print(f"🔥 확정된 주제: {topic}")

    # 2. 글쓰기 (플럭시 페르소나 강화)
    print("✍️ '플럭시'가 글을 작성하고 있습니다...")
    
    prompt = f"""
    당신은 블로거 '플럭시(Fluxy)'입니다.
    주제: '{topic}'에 대해 블로그 글을 쓰세요.

    [⚠️ 절대 금지 (AI 티 내지 않기)]
    - "안녕하세요 플럭시입니다" 처럼 기계적인 인사 금지.
    - "본론으로 들어가겠습니다", "결론적으로" 같은 딱딱한 접속사 금지.
    - 문장 끝마다 이모티콘 붙이지 말 것. (문단 당 1~2개만 사용).
    - "전반적으로", "살펴보겠습니다" 같은 번역투 금지.

    [😊 페르소나 설정: 진짜 사람처럼]
    - 시작: 친구에게 말하듯 자연스럽게 경험담으로 시작. (예: "어제 카페 갔는데...", "저도 이거 때문에 고생했거든요.")
    - 말투: ~해요, ~하더라구요, ~거든요 (부드러운 구어체).
    - 내용: 너무 전문적인 용어는 빼고, 초등학생도 이해하게 쉽게.
    - 마무리: "도움 되셨으면 좋겠네요! 다음에 또 꿀팁 가져올게요."

    [형식]
    - HTML 태그 사용 (<h2>, <p>, <ul>, <li>, <b>).
    - 가독성을 위해 문단은 2~3줄로 짧게 끊을 것.
    """

    try:
        content = generate_content_with_retry(prompt)
        
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

    # 3. 이미지 생성 (Unsplash 스타일)
    print("🎨 블로그용 감성 이미지 생성 중...")
    image_prompt = f"minimalist clean photography, bright aesthetic workspace or daily life object related to {topic}, high resolution, soft lighting, instagram style"
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

if __name__ == "__main__":
    auto_posting()
