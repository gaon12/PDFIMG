# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('langs', 'langs'),  # JSON 파일 포함
        ('imgs', 'imgs'),    # 이미지 파일 포함
        ('C:/Users/solso/.conda/envs/2410xx/Lib/site-packages/tkinterdnd2/tkdnd', 'tkinterdnd2/tkdnd'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=['resource_path.py'],  # 추가
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,  # binaries를 포함
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='imgs/icon.png',  # 아이콘 설정
    version='version.txt',  # 버전 정보 파일 추가
    onefile=True,  # 실행 파일을 하나로 패키징
)