import json
from datetime import datetime
import os
import glob
import openai
from dotenv import load_dotenv
import time
import sys
import threading

# 환경 설정
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# JSON 변환을 위한 예시 프롬프트
EXAMPLE_PROMPT = """다음은 보험 상담 결과를 JSON 형식으로 변환하는 예시입니다:

[예시 1: 보장항목이 있는 경우]
입력 데이터:
{
    "설정값": {
        "custom_name": "홍길동",
        "insu_age": 45,
        "sex": 1,
        "product_type": "nr",
        "expiry_year": "20y_100",
        "company_id": null
    },
    "결과": [
        {"보험사명": "삼성생명", "상품명": null, "보장항목명": null, "보험료": "150000"},
        {"보험사명": "삼성생명", "상품명": "종신보험", "보장항목명": "사망보장", "보험료": "100000"},
        {"보험사명": "삼성생명", "상품명": "종신보험", "보장항목명": "암진단금", "보험료": "50000"}
    ]
}

출력 형식:
{
    "설정값": {
        "이름": "홍길동",
        "나이": 45,
        "성별": "남자",
        "상품유형": "무해지형",
        "보험기간": "20y_100",
        "보험사ID": null
    },
    "보험사": [
        {
            "이름": "삼성생명",
            "보험료합계": 150000,
            "상품": [
                {
                    "상품명": "종신보험",
                    "보장항목": {
                        "사망보장": 100000,
                        "암진단금": 50000
                    }
                }
            ]
        }
    ]
}

[예시 2: 보험사별 합계만 있는 경우]
입력 데이터:
{
    "설정값": {
        "custom_name": "홍길동",
        "insu_age": 45,
        "sex": 1,
        "product_type": "nr",
        "expiry_year": "20y_100",
        "company_id": null
    },
    "결과": [
        {"보험사명": "DB손해보험", "상품명": "무)참좋은훼밀리더블플러스종합보험2404", "보험료합계": "188427"},
        {"보험사명": "KB손해보험", "상품명": "무)닥터플러스건강보험2501", "보험료합계": "191875"}
    ]
}

출력 형식:
{
    "설정값": {
        "이름": "홍길동",
        "나이": 45,
        "성별": "남자",
        "상품유형": "무해지형",
        "보험기간": "20y_100",
        "보험사ID": null
    },
    "보험사": [
        {
            "이름": "DB손해보험",
            "상품명": "무)참좋은훼밀리더블플러스종합보험2404",
            "보험료합계": 188427
        },
        {
            "이름": "KB손해보험",
            "상품명": "무)닥터플러스건강보험2501",
            "보험료합계": 191875
        }
    ]
}

[예시 3: 연령대별 보험료 총액이 있는 경우]
입력 데이터:
{
    "설정값": {
        "custom_name": "홍길동",
        "insu_age": 50,
        "sex": 1,
        "product_type": "nr",
        "expiry_year": "20y_100",
        "company_id": "02"
    },
    "결과": [
        {"보험사명": "한화손해보험", "나이": 45, "보험료총액": "385493"},
        {"보험사명": "한화손해보험", "나이": 46, "보험료총액": "397796"},
        {"보험사명": "한화손해보험", "나이": 47, "보험료총액": "410779"}
    ]
}

출력 형식:
{
    "설정값": {
        "이름": "홍길동",
        "나이": 50,
        "성별": "남자",
        "상품유형": "무해지형",
        "보험기간": "20y_100",
        "보험사ID": "02"
    },
    "보험사": [
        {
            "이름": "한화손해보험",
            "연령별보험료": [
                {"나이": 45, "보험료": 385493},
                {"나이": 46, "보험료": 397796},
                {"나이": 47, "보험료": 410779}
            ]
        }
    ]
}

입력 데이터의 구조를 확인하여 적절한 출력 형식을 선택하세요:
1. "구분" 필드가 있고 "상세" 데이터가 있는 경우 -> 예시 1 형식으로 출력
2. "구분" 필드가 없고 "상품명"과 "보험료합계"가 있는 경우 -> 예시 2 형식으로 출력
3. "나이"와 "보험료총액" 필드가 있는 경우 -> 예시 3 형식으로 출력

위 규칙에 따라 다음 데이터를 변환해주세요:
"""

class Spinner:
    def __init__(self, message="처리중"):
        self.spinner = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        self.message = message
        self.busy = False
        self.spinner_visible = False

    def write_next(self):
        with self._screen_lock:
            if not self.spinner_visible:
                sys.stdout.write(f'\r{self.message} {self.spinner[self.spinner_index]} ')
                self.spinner_index = (self.spinner_index + 1) % len(self.spinner)
                sys.stdout.flush()

    def __enter__(self):
        self._screen_lock = threading.Lock()
        self.busy = True
        self.spinner_index = 0
        self.spinner_visible = True
        sys.stdout.write(f'\r{self.message} ')
        sys.stdout.flush()
        threading.Thread(target=self.spinner_task).start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.busy = False
        time.sleep(0.1)
        with self._screen_lock:
            sys.stdout.write('\r')
            sys.stdout.write(f'\r{self.message} 완료!\n')
            sys.stdout.flush()

    def spinner_task(self):
        while self.busy:
            self.write_next()
            time.sleep(0.1)

def convert_to_json():
    try:
        print("\n=== JSON 변환 시작 ===")
        
        with Spinner("디렉토리 확인 중"):
            if not os.path.exists('query_results'):
                print("query_results 디렉토리가 없습니다.")
                return

            temp_files = glob.glob('query_results/temp_result*.json')
            if not temp_files:
                print("임시 결과 파일을 찾을 수 없습니다.")
                return
                
            latest_temp_file = max(temp_files, key=os.path.getctime)
        
        with Spinner("임시 파일 읽는 중"):
            try:
                with open(latest_temp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"JSON 파일 읽기 오류: {str(e)}")
                return
            except Exception as e:
                print(f"파일 읽기 오류: {str(e)}")
                return

        # GPT API를 사용하여 JSON 변환
        try:
            with Spinner("GPT API 요청 준비 중"):
                client = openai.OpenAI()
                prompt = EXAMPLE_PROMPT + json.dumps(data, ensure_ascii=False, indent=2)
            
            print("\nGPT API 호출 중... (시간이 다소 걸릴 수 있습니다)")
            start_time = time.time()
            
            with Spinner("GPT API 처리 중"):
                response = client.chat.completions.create(
                    model="gpt-4-0125-preview",
                    messages=[
                        {"role": "system", "content": "당신은 JSON 데이터 변환 전문가입니다. 주어진 예시 형식에 맞게 데이터를 변환해주세요."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0
                )
            
            elapsed_time = time.time() - start_time
            print(f"GPT API 처리 완료! (소요시간: {elapsed_time:.1f}초)")
            
            with Spinner("응답 데이터 처리 중"):
                response_text = response.choices[0].message.content
                # 디버깅을 위한 출력 추가
                print("\n=== GPT 응답 내용 ===")
                print(response_text)
                print("\n=== 응답 내용 끝 ===")
                
                # JSON 문자열 정제 과정 추가
                json_str = response_text.replace('```json', '').replace('```', '').strip()
                try:
                    converted_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"\nJSON 파싱 오류 위치: {str(e)}")
                    print("문제의 JSON 문자열:")
                    print(json_str)
                    return
            
            with Spinner("결과 파일 저장 중"):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'query_results/query_result_{timestamp}.json'
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(converted_data, f, ensure_ascii=False, indent=2)
                print(f"\n결과가 다음 파일에 저장되었습니다: {filename}")
            
            with Spinner("임시 파일 정리 중"):
                for temp_file in temp_files:
                    os.remove(temp_file)
                print("임시 파일들이 정리되었습니다.")
            
        except Exception as e:
            print(f"GPT API 또는 JSON 변환 오류: {str(e)}")
            return
            
    except Exception as e:
        print(f"\n❌ 전체 처리 오류: {str(e)}")

if __name__ == "__main__":
    convert_to_json()