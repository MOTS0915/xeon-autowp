import os
import requests
import base64
import urllib3
from google import genai
import random
import time

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASS = os.environ.get("WP_APP_PASS")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🏆 [핵심 설청]
# Pro 모델은 무료 한도가 적어 429 에러가 발생하므로,
# 성능 좋고 한도가 널널한 'Flash' 모델로 확정했습니다.
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash" 

def get_tech_topic():
    # 엔지니어링 관련 심층 주제 리스트
    topics = [
        "차세대 반도체 패키징 기술과 이종 집적(Heterogeneous Integration)", 
        "L4/L5 자율주행을 위한 LiDAR와 Radar 센서 퓨전 기술",
        "Matter 표준이 스마트홈 IoT 생태계에 미치는 영향", 
        "군집 드론 제어 알고리즘과 국방 분야 응용",
        "전고체 배터리(Solid-state Battery) 상용화의 기술적 난제", 
        "Edge AI 가속기를 활용한 실시간 임베디드 비전 시스템",
        "6G 통신을 위한 테라헤르츠(THz) 대역폭 활용 기술", 
        "금속 3D 프린팅(DED/PBF)의 항공우주 부품 적용 사례",
        "전기차 BMS의 셀 밸런싱 알고리즘과 SOH 예측 기술", 
        "양자 내성 암호(PQC)와 미래 보안 시스템의 변화"
    ]
    return random.choice(topics)

def upload_image_to_wp(image_url, title):
    print(f"📥 이미지 다운로드 중... ({image_url})")
    try:
        image_data = requests.get(image_url).content
        filename = f"tech_{int(time.time())}.png"

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
            print("✅ 미디어 라이브러리 업로드 성공!")
            return response.json()['id']
        else:
            print(f"❌ 이미지 업로드 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 이미지 처리 에러: {e}")
        return None

def auto_posting():
    print("==========================================")
    print("🚀 자동화 봇 시스템 가동 시작")
    print("==========================================")

    topic = get_tech_topic()
    print(f"📌 오늘의 주제: {topic}")
    print(f"🧠 사용하는 모델: {MODEL_NAME}")

    # 1. Gemini에게 글쓰기 요청
    print("✍️ Gemini가 글을 작성하고 있습니다...")
    
    prompt = f"""
    당신은 20년 경력의 글로벌 IT 기업 수석 엔지니어입니다.
    주제: '{topic}'에 대해 전문적인 기술 리뷰 블로그 포스팅을 작성하세요.

    [작성 지침]
    1. 제목: 기술적 전문성이 느껴지도록 작성.
    2. 내용 구성: 서론, 핵심 기술 분석(3가지), 과제 및 해결 방안, 결론.
    3. 포맷: HTML 태그(<h2>, <h3>, <p>, <ul>, <li>, <strong>) 사용.
    4. 분량: 2500자 내외로 상세하게.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        content = response.text
        
        # 제목 및 본문 분리
        title = topic
        lines = content.split('\n')
        if "제목:" in lines[0] or "# " in lines[0]:
            title = lines[0].replace("제목:", "").replace("#", "").strip()
            content = "\n".join(lines[1:])
        elif len(lines[0]) < 100 and len(lines[0]) > 5:
             title = lines[0].strip()
             content = "\n".join(lines[1:])

    except Exception as e:
        print(f"❌ 글쓰기 실패 (API 에러): {e}")
        return

    # 2. 이미지 생성
    print("🎨 테크니컬 일러스트 생성 중...")
    image_prompt = f"futuristic technology {topic}, unreal engine 5 render, 8k resolution, cinematic lighting"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1024&height=600&nologo=true&seed={int(time.time())}"
    
    featured_media_id = upload_image_to_wp(image_url, topic)

    # 3. 워드프레스 발행
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
        "categories": [1], 
    }
    
    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    print("📤 워드프레스로 발행 요청 중...")
    response = requests.post(WP_URL, headers=headers, json=post_data, verify=False)