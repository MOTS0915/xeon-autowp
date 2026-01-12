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

# 🏆 [핵심] 로그에서 찾은 '최고 성능' 모델 적용
# Flash(속도) 대신 Pro(지능) 모델을 사용하여 글의 깊이를 높였습니다.
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3-pro-preview" 

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
    print(f"📥 고해상도 이미지 다운로드 중... ({image_url})")
    try:
        image_data = requests.get(image_url).content
        filename = f"tech_pro_{int(time.time())}.png"

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
    topic = get_tech_topic()
    print(f"🚀 오늘의 주제: {topic}")
    print(f"🧠 두뇌 가동: {MODEL_NAME} (최고 성능 모델)")

    # 1. Gemini 3 Pro에게 글쓰기 요청
    print("✍️ 수석 엔지니어가 글을 작성하고 있습니다... (시간이 좀 걸립니다)")
    
    prompt = f"""
    당신은 20년 경력의 글로벌 IT 기업 수석 엔지니어(Principal Engineer)입니다.
    주제: '{topic}'에 대해 심도 있는 기술 분석 블로그 포스팅을 작성하세요.

    [작성 지침]
    1. 제목: 클릭을 유도하되 기술적 전문성이 느껴지도록 작성 (예: '...의 현주소와 미래 전망').
    2. 독자 타겟: 현직 엔지니어 및 공학 전공자.
    3. 구성:
       - **서론 (Introduction)**: 기술의 배경과 중요성
       - **핵심 기술 분석 (Core Technology)**: 3가지 주요 기술적 특징을 상세히 서술
       - **기술적 과제 및 해결 방안 (Challenges & Solutions)**: 현재의 한계점과 극복 방안
       - **시장 전망 (Market Outlook)**: 향후 5년 내 변화 예측
       - **결론 (Conclusion)**: 엔지니어로서의 인사이트 요약
    4. 포맷: HTML 태그(<h2>, <h3>, <p>, <ul>, <li>, <strong>, <blockquote>)를 적절히 사용하여 가독성 최적화.
    5. 분량: 3000자 내외로 아주 상세하게 작성할 것.
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
        # 첫 줄에 제목이 있을 경우 추출
        if "제목:" in lines[0] or "# " in lines[0]:
            title = lines[0].replace("제목:", "").replace("#", "").strip()
            content = "\n".join(lines[1:])
        elif len(lines[0]) < 100 and len(lines[0]) > 5:
             title = lines[0].strip()
             content = "\n".join(lines[1:])

    except Exception as e:
        print(f"❌ 글쓰기 실패 (API 에러): {e}")
        return

    # 2. 고품질 이미지 생성 (Pollinations 활용)
    print("🎨 주제에 맞는 테크니컬 일러스트 생성 중...")
    # 프롬프트 강화: 4K, 언리얼 엔진 렌더링 스타일
    image_prompt = f"hyper-realistic futuristic technology {topic}, unreal engine 5 render, 8k resolution, cinematic lighting, cyberpunk atmosphere, highly detailed circuits and machinery"
    image_url = f"https://image.pollinations.ai/prompt/{image_prompt}?width=1200&height=630&nologo=true&seed={int(time.time())}"
    
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
    
    if response.status_code == 201:
        print(f"✅ 포스팅 발행 성공! [ID: {response.json()['id']}]")
        print("🎉 축하합니다! 블로그 봇이 완벽하게 작동했습니다.")
    else:
        print(f"❌ 발행 실패: {response.text}")

if __name__ == "__main__":
    auto_posting()