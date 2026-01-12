import os
import requests
import base64
import urllib3
from google import genai # 새로운 라이브러리 임포트
import random
import time

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASS = os.environ.get("WP_APP_PASS")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 1. 신형 엔진 구동 (Google GenAI Client)
# 모델 변경하고 싶으면 'gemini-2.0-flash' 부분을 수정하면 됩니다.
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.0-flash" 

def get_tech_topic():
    topics = [
        "차세대 반도체 기술 동향", "자율주행 자동차의 미래 센서 기술",
        "스마트홈 IoT 보안 이슈와 해결책", "최신 드론 기술과 국방 응용",
        "웨어러블 디바이스의 배터리 혁신", "AI가 바꾸는 임베디드 시스템",
        "6G 통신 기술의 핵심 전망", "3D 프린팅 기술의 산업 적용 사례",
        "전기차 배터리 관리 시스템(BMS) 분석", "양자 컴퓨터가 가져올 변화"
    ]
    return random.choice(topics)

def upload_image_to_wp(image_url, title):
    """Pollinations AI 이미지 업로드"""
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
            print("✅ 이미지 업로드 성공!")
            return response.json()['id']
        else:
            print(f"❌ 이미지 업로드 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 이미지 처리 중 에러: {e}")
        return None

def auto_posting():
    topic = get_tech_topic()
    print(f"🚀 오늘의 주제: {topic}")
    print(f"🤖 사용하는 모델: {MODEL_NAME}")

    # 2. Gemini에게 글쓰기 요청 (새로운 방식)
    print("🧠 Gemini가 생각하는 중...")
    
    prompt = f"""
    당신은 20년 경력의 수석 엔지니어입니다.
    주제: '{topic}'에 대해 전문적인 기술 리뷰 블로그 포스팅을 작성하세요.

    [필수 조건]
    1. 제목은 매력적이고 기술적으로 작성할 것.
    2. 내용은 서론, 기술적 특징(3가지), 장단점 분석, 결론으로 구성할 것.
    3. HTML 태그(<h2>, <h3>, <p>, <ul>, <li>, <strong>)를 사용하여 가독성을 높일 것.
    4. 말투는 "~입니다", "~합니다" 등 격식 있는 엔지니어 톤을 유지할 것.
    5. 글자 수는 2000자 이상으로 아주 상세하게 작성할 것.
    """

    try:
        # 새로운 API 호출 방식
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        content = response.text
        
        # 제목 추출 로직
        title = topic
        lines = content.split('\n')
        if "제목:" in lines[0]:
            title = lines[0].replace("제목:", "").strip()
            content = "\n".join(lines[1:])
        elif "<h1>" not in lines[0] and len(lines[0]) < 50: # 첫줄이 짧으면 제목으로 추정
             title = lines[0].strip()
             content = "\n".join(lines[1:])

    except Exception as e:
        print(f"❌ Gemini 글쓰기 실패: {e}")
        return

    # 3. 이미지 생성 (Pollinations)
    print("🎨 AI 이미지 생성 중...")
    image_prompt = f"futuristic technology {topic} cyberpunk style high quality"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1024&height=600&nologo=true&seed={int(time.time())}"
    
    featured_media_id = upload_image_to_wp(image_url, topic)

    # 4. 워드프레스 발행
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

    print("📤 워드프레스로 전송 중...")
    response = requests.post(WP_URL, headers=headers, json=post_data, verify=False)
    
    if response.status_code == 201:
        print(f"✅ 포스팅 발행 완료! 글 ID: {response.json()['id']}")
    else:
        print(f"❌ 발행 실패: {response.text}")

if __name__ == "__main__":
    auto_posting()