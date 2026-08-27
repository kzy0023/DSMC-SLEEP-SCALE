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

RELEASE_FUNCTIONS = f"""
function sendResultsByEmail() {{
    const name = document.getElementById('patient_name').value || '환자';
    const id = document.getElementById('patient_id').value || '';
    const date = document.getElementById('eval_date').value || '';

    // CSV 데이터 생성
    const scale1 = getScale1Results();
    const scale2 = getScale2Results();
    const gender = document.getElementById('patient_gender').value || '';
    const age = document.getElementById('patient_age').value || '';
    const bmi = document.getElementById('patient_bmi').value || '';

    let headers = ['등록번호','성명','성별','나이','BMI','검사일'];
    let values = [id, name, gender, age, bmi, date];
    scale1.forEach(r => {{
        headers.push(r.title+' (점수)', r.title+' (해석)');
        values.push(r.score, r.interp);
        if (r.extra) {{ headers.push(r.title+' (근거)'); values.push(r.extra); }}
    }});
    scale2.forEach(r => {{
        headers.push(r.title+' (점수)', r.title+' (해석)');
        values.push(r.score, r.interp);
        if (r.components) {{ headers.push(r.title+' (세부점수)'); values.push(r.components); }}
        if (r.extra) {{ headers.push(r.title+' (근거)'); values.push(r.extra); }}
    }});

    const csvRow = values.map(v => {{
        const s = String(v == null ? '' : v);
        return s.includes(',') || s.includes('"') ? '"'+s.replace(/"/g,'""')+'"' : s;
    }}).join(',');
    const csvContent = headers.join(',') + '\\n' + csvRow;

    // 상세 결과 HTML
    const resultsHtml = document.getElementById('results_container').innerHTML;

    // EmailJS 전송
    if (typeof emailjs === 'undefined') {{
        console.error('EmailJS not loaded');
        return;
    }}
    emailjs.send('{EMAILJS_SERVICE_ID}', '{EMAILJS_TEMPLATE_ID}', {{
        to_email: 'nepsy@dsmc.or.kr',
        patient_name: name,
        patient_id: id,
        eval_date: date,
        csv_data: csvContent,
        results_html: resultsHtml,
        info_responses: getInfoResponses(),
        scale1_responses: getScaleResponses('scale1'),
        scale2_responses: getScaleResponses('scale2')
    }}).then(
        () => console.log('결과 전송 완료'),
        (err) => console.error('전송 실패:', err)
    );
}}
"""

EMAILJS_SCRIPT_TAG = f'<script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>\n    <script>emailjs.init("{EMAILJS_PUBLIC_KEY}")</script>'


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

        # Release 모드: calculateAll에서 결과 표시 대신 메시지 + 이메일 전송
        html = html.replace(
            '    // {{RELEASE_MODE_START}}\n    displayResults(results);\n    // {{RELEASE_MODE_END}}',
            RELEASE_CALCULATE_BLOCK
        )

        # Release 함수 삽입
        html = html.replace(
            '// {{RELEASE_FUNCTIONS_START}}\n// {{RELEASE_FUNCTIONS_END}}',
            RELEASE_FUNCTIONS
        )

        # EmailJS CDN 삽입 (첫 번째 <style> 앞에만)
        html = html.replace('<style>', EMAILJS_SCRIPT_TAG + '\n    <style>', 1)

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
