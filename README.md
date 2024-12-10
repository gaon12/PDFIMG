# PDF to Image Converter GUI

PDF 파일을 드래그 앤 드롭하여 손쉽게 이미지를 생성할 수 있는 Python GUI 프로그램입니다. 이 프로그램은 PDF 페이지를 이미지로 변환하며, PNG, JPEG 등 원하는 형식으로 저장할 수 있습니다.

## 주요 기능

- PDF 파일을 드래그 앤 드롭하여 변환 가능
- 변환된 이미지는 각 페이지별로 저장
- 지원 이미지 포맷: PNG, JPEG, WEBP, AVIF, BMP
- 간단하고 직관적인 GUI

## 데모 영상

아래에서 프로그램의 작동 방식을 확인할 수 있습니다:

<video controls src="./README/intro.mp4" width="600"></video>

## 사용 방법

1. 프로그램 실행:
   - Python 환경에서 `main.py`를 실행하여 GUI를 엽니다.
      - 필요한 라이브러리 설치:
      ```bash
      pip install -r requirements.txt
      ```
      - 프로그램 실행:
      ```bash
      python main.py
      ```
   - Python 실행 환경이 없는 경우, 릴리즈 페이지에서 `main.exe`을 실행합니다. 윈도우 11에서 테스트했습니다. 64비트 환경에서 동작합니다(아마도요...)

2. PDF 파일 변환:
   - 프로그램 창에 PDF 파일을 드래그 앤 드롭 하거나 메뉴에서 PDF 파일을 선택합니다.
   - 변환이 완료되면 변환된 이미지는 PDF가 있는 폴더에 PDF 파일명으로 된 폴더 안에 저장됩니다.

3. 변환 결과:
   - 변환된 이미지는 PDF 파일의 이름과 동일한 폴더 안에 저장됩니다.
   - 파일 이름은 페이지 번호에 따라 지정됩니다.

## 주의사항

- PDF 파일 크기나 페이지 수에 따라 변환 시간이 다를 수 있습니다.
- 변환 중간에 취소는 불가능합니다. 기다리시거나 작업관리자 등으로 강제종료(비권장)하시기 바랍니다.

## 기여

이 프로젝트에 기여하고 싶다면 Pull Request를 보내주시거나 이슈를 남겨주세요. 여러분의 기여를 환영합니다!

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](./LICENSE) 파일을 참조하세요.
