# -*- coding: utf-8 -*-
import os
import requests
import base64
import urllib3
from google import genai
import time

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASS = os.environ.get("WP_APP_PASS")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 모델 설정 (가성비 최강 2.5 Flash)
MODEL_NAME = "gemini-2.5-flash"
client = genai.Client(api_key=GEMINI_API_KEY)

def get_viral_topic():
    """
    Gemini에게 '오늘 사람들이 클릭할 만한 대중적인 주제'를 물어봅니다.
    """
    print("🕵️‍♀️ Gemini가 실시간 트렌드 주제를 탐색 중...")
    try:
        prompt = """
        당신은 100만 유튜버이자 트렌드 분석가입니다.
        오늘 블로그에 올리면 조회수가 폭발할 만한 '대중적인 호기심 주제' 하나만 추천해주세요.
        
        [주제 선정 조건]
        1. 분야: IT 기술, 미래 사회, 생활 꿀팁, 미스터리 과학 중 하나.
        2. 난이도: 초등학생도 이해할 수 있는 쉬운 주제.
        3. 흥미: "어? 진짜?" 소리가 나오는 호기심 자극 소재.
        4. 안전: 정치/종교/비방/혐오/성적 내용은 절대 금지.
        
        대답은 군더더기 없이 '주제' 딱 한 문장만 출력하세요.
        예시: 스마트폰 배터리를 2배 오래 쓰는 숨겨진 설정
        """
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        topic = response.text.strip()
        # 혹시 모를 따옴표 제
        return topic.replace('"', '').replace("'", "")
    except Exception as e:
        print(f"❌ 주제 선정 실패: {e}")
        return "인공지능이 인간을 대체할 수 없는 3가지 이유" # 비상용 기본 주제

def upload_image_to_wp(image_url, title):
    print(f"📥 썸네일 다운로드 중... ({image_url})")
    try:
        image_data = requests.get(image_url).content
        filename = f"viral_{int(time.time())}.png"
        
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
            print("✅ 썸네일 업로드 성공!")
            return response.json()['id']
        else:
            print(f"❌ 썸네일 업로드 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 이미지 처리 중 에러: {e}")
        return None

def auto_posting():
    print("------------ [트렌드 헌터 봇 가동] ------------")
    
    # 1. 핫한 주제 선정
    topic = get_viral_topic()
    print(f"🔥 오늘의 핫 토픽: {topic}")

    # 2. 글쓰기 요청 (조회수 중심)
    print("✍️ 인기 작가가 글을 작성하는 중...")
    
    prompt = f"""
    당신은 월 방문자 100만 명의 인기 테크/생활 블로거입니다.
    주제: '{topic}'에 대해 독자의 이목을 집중시키는 글을 작성하세요.

    [작성 법칙: 3초 안에 사로잡아라]
    1. 제목: 클릭을 부르는 어그로성 제목 (하지만 내용은 진실되게). 물음표나 느낌표 활용.
       (예: 지금 당장 설정을 끄지 않으면 후회하는 이유?)
    2. 어조: 옆집 형/오빠가 알려주듯 친근하고 재미있게. (~해요, ~거든요, 대박이죠?)
    3. 구성:
       - **충격적인 도입부**: 독자의 공감을 사거나 궁금증 유발.
       - **본문 (팩트 체크)**: 쉽고 명쾌한 설명 (어려운 용어 금지).
       - **반전/결론**: 실생활에 도움 되는 꿀팁으로 마무리.
    4. 안전 수칙 (절대 준수):
       - 특정 인물, 기업, 단체를 비방하거나 깎아내리지 말 것.
       - 혐오 표현이나 사회적 갈등을 조장하지 말 것.
    5. 형식: HTML 태그(<h2>, <p>, <ul>, <strong>)를 써서 모바일에서 보기 편하게.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        content = response.text
        
        # 제목 추출 로직
        title = topic
        lines = content.split('\n')
        if "제목:" in lines[0] or "# " in lines[0]:
            title = lines[0].replace("제목:", "").replace("#", "").strip()
            content = "\n".join(lines[1:])
        elif len(lines[0]) < 100:
             title = lines[0].strip()
             content = "\n".join(lines[1:])

    except Exception as e:
        print(f"❌ 글쓰기 실패: {e}")
        return

    # 3. 이미지 생성 (눈에 띄는 스타일)
    print("🎨 썸네일 생성 중...")
    # 프롬프트: 사이버펑크보다는 좀 더 밝고 팝아트적인 느낌으로 변경
    image_prompt = f"pop art style, vivid colors, interesting illustration about {topic}, 4k, trending on artstation"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1024&height=600&nologo=true&seed={int(time.time())}"
    
    featured_media_id = upload_image_to_wp(image_url, topic)

    # 4. 워드프레스 발행
    print("📤 블로그 발행 중...")
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
        print(f"🎉 대박 예감! 포스팅 발행 완료. ID: {response.json()['id']}")
    else:
        print(f"❌ 발행 실패: {response.text}")

# 무조건 실행
auto_posting()
