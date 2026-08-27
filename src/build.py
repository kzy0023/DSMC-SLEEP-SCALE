"""
DSMC Sleep Scale HTML 빌드 스크립트

사용법:
    python3 build.py           # 테스터모드 포함 버전 (개발용)
    python3 build.py --no-test # 테스터모드 제외 버전 (배포용)
    python3 build.py --both    # 둘 다 생성

결과:
    ../sleep_scale.html           (테스터모드 포함)
    ../sleep_scale_release.html   (테스터모드 제외, 배포용 - 결과 이메일 전송)

수정 방법:
    1. template.html 을 수정 (로고 자리는 {{LOGO_DATA_URI}} 로 표시됨)
    2. python3 build.py --both 실행
    3. 상위 폴더에 html 파일이 업데이트됨

EmailJS 설정:
    release 버전에서 결과를 이메일로 보내려면 EmailJS 설정이 필요합니다.
    1. https://www.emailjs.com 에서 무료 계정 생성
    2. Email Service 추가 (Gmail 등 연결)
    3. Email Template 생성 (변수: patient_name, patient_id, eval_date, csv_data, results_html)
    4. 아래 EMAILJS_* 상수를 발급받은 값으로 교체
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, 'template.html')
LOGO_PATH = os.path.join(SCRIPT_DIR, 'logo_base64.txt')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, '..', 'sleep_scale.html')
OUTPUT_RELEASE_PATH = os.path.join(SCRIPT_DIR, '..', 'sleep_scale_release.html')

# === EmailJS 설정 (배포용) ===
EMAILJS_PUBLIC_KEY = 'j7XUM9AJQWbg7NJT3'
EMAILJS_SERVICE_ID = 'service_0i8loiq'
EMAILJS_TEMPLATE_ID = 'template_3x4sqpi'

RELEASE_CALCULATE_BLOCK = """
    displayResults(results);
    sendResultsByEmail();
    setTimeout(() => {
        document.getElementById('results_container').innerHTML =
            '<div style="text-align:center;padding:40px 20px">' +
            '<h2 style="color:#1e3a5f;margin-bottom:15px">검사가 완료되었습니다</h2>' +
            '<p style="font-size:1.1em;color:#475569">최종 결과는 외래진료시 알려드립니다.</p>' +
            '<p style="font-size:1.1em;color:#475569;margin-top:10px">수고하셨습니다.</p>' +
            '</div>';
        document.querySelector('#results .print-btn').style.display = 'none';
        document.querySelector('#results .print-btn:last-of-type').style.display = 'none';
    }, 100);
"""


def build(include_test=True, output_path=None):
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()

    with open(LOGO_PATH, 'r', encoding='utf-8') as f:
        logo_data_uri = f.read().strip()

    html = template.replace('{{LOGO_DATA_URI}}', logo_data_uri)

    if not include_test:
        # 테스터모드 버튼 제거
        html = re.sub(
            r'[ \t]*<button[^>]*onclick="fillTestData\(\)"[^>]*>.*?</button>\n?',
            '', html
        )
        # 이메일 전송 버튼 제거 (release에서는 자동 전송)
        html = re.sub(
            r'[ \t]*<button[^>]*onclick="sendEmailManual\(\)"[^>]*>.*?</button>\n?',
            '', html
        )
        # fillTestData 함수 제거
        html = re.sub(
            r'\nfunction fillTestData\(\) \{.*?\n\}',
            '', html, flags=re.DOTALL
        )
        # sendEmailManual 함수 제거
        html = re.sub(
            r'\nfunction sendEmailManual\(\) \{.*?\n\}',
            '', html, flags=re.DOTALL
        )

        # Release 모드: calculateAll에서 결과 표시 후 메시지 교체
        html = html.replace(
            '    // {{RELEASE_MODE_START}}\n    displayResults(results);\n    sendResultsByEmail();\n    // {{RELEASE_MODE_END}}',
            RELEASE_CALCULATE_BLOCK
        )

    if output_path is None:
        output_path = OUTPUT_PATH if include_test else OUTPUT_RELEASE_PATH

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize(output_path) // 1024
    label = '테스터모드 포함' if include_test else '배포용 (테스터모드 제외)'
    filename = os.path.basename(output_path)
    print(f'✅ {filename} 생성 완료 ({size_kb} KB) - {label}')


if __name__ == '__main__':
    args = sys.argv[1:]

    if '--both' in args:
        build(include_test=True)
        build(include_test=False)
    elif '--no-test' in args:
        build(include_test=False)
    else:
        build(include_test=True)
