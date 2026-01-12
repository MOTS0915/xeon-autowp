import os
import requests
import base64
import urllib3
import google.generativeai as genai
import random
import time

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 환경변수 로드
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASS = os.environ.get("WP_APP_PASS")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 구글 제미나이 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash')

def get_tech_topic():
    # 매번 다른 주제를 선정하기 위한 리스트
    topics = [
        "차세대 반도체 기술 동향", "자율주행 자동차의 미래 센서 기술",
        "스마트홈 IoT 보안 이슈와 해결책", "최신 드론 기술과 국방 응용",
        "웨어러블 디바이스의 배터리 혁신", "AI가 바꾸는 임베디드 시스템",
        "6G 통신 기술의 핵심 전망", "3D 프린팅 기술의 산업 적용 사례",
        "전기차 배터리 관리 시스템(BMS) 분석", "양자 컴퓨터가 가져올 변화"
    ]
    return random.choice(topics)

def upload_image_to_wp(image_url, title):
    """무료 AI 이미지(Pollinations)를 워드프레스에 업로드"""
    print(f"📥 이미지 다운로드 중... ({image_url})")
    try:
        image_data = requests.get(image_url).content
        filename = f"tech_review_{int(time.time())}.png"

        credentials = f"{WP_USER}:{WP_APP_PASS}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "image/png"
        }

        # 미디어 엔드포인트 설정
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

    # 1. Gemini에게 글쓰기 요청
    print("🧠 Gemini가 생각하는 중...")
    prompt = f"""
    당신은 20년 경력의 수석 엔지니어입니다.
    주제: '{topic}'에 대해 전문적인 기술 리뷰 블로그 포스팅을 작성하세요.

    [필수 조건]
    1. 제목은 매력적이고 기술적으로 작성할 것.
    2. 내용은 서론, 기술적 특징(3가지), 장단점 분석, 결론으로 구성할 것.
    3. HTML 태그(<h2>, <h3>, <p>, <ul>, <li>, <strong>)를 사용하여 가독성을 높일 것.
    4. 말투는 "~입니다", "~합니다" 등 격식 있는 엔지니어 톤을 유지할 것.
    5. 글의 길이는 충분히 길고 상세하게 작성할 것.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # 제목 추출 (Gemini가 제목을 첫 줄에 쓸 경우를 대비)
        title = topic
        if "제목:" in content.split('\n')[0]:
            title = content.split('\n')[0].replace("제목:", "").strip()
            content = "\n".join(content.split('\n')[1:]) # 본문에서 제목 제거

    except Exception as e:
        print(f"❌ Gemini 글쓰기 실패: {e}")
        return

    # 2. 무료 AI 이미지 생성 (Pollinations.ai 활용)
    print("🎨 AI 이미지 생성 중...")
    image_prompt = f"futuristic technology {topic} cyberpunk style high quality"
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

    print("📤 워드프레스로 전송 중...")
    response = requests.post(WP_URL, headers=headers, json=post_data, verify=False)
    
    if response.status_code == 201:
        print(f"✅ 포스팅 발행 완료! 글 ID: {response.json()['id']}")
    else:
        print(f"❌ 발행 실패: {response.text}")

if __name__ == "__main__":
    auto_posting()
