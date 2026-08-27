"""
DSMC Sleep Scale HTML 빌드 스크립트

사용법:
    python3 build.py           # 테스터모드 포함 버전
    python3 build.py --no-test # 테스터모드 제외 버전 (배포용)
    python3 build.py --both    # 둘 다 생성

결과:
    ../sleep_scale.html           (테스터모드 포함)
    ../sleep_scale_release.html   (테스터모드 제외, 배포용)

수정 방법:
    1. template.html 을 수정 (로고 자리는 {{LOGO_DATA_URI}} 로 표시됨)
    2. python3 build.py --both 실행
    3. 상위 폴더에 html 파일이 업데이트됨
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, 'template.html')
LOGO_PATH = os.path.join(SCRIPT_DIR, 'logo_base64.txt')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, '..', 'sleep_scale.html')
OUTPUT_RELEASE_PATH = os.path.join(SCRIPT_DIR, '..', 'sleep_scale_release.html')


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
        # fillTestData 함수 제거
        html = re.sub(
            r'\nfunction fillTestData\(\) \{.*?\n\}',
            '', html, flags=re.DOTALL
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
