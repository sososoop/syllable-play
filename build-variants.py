#!/usr/bin/env python3
"""한글놀이 index.html 하나로 세 가지 파일을 만든다.

  full  정식판(소소숲 /hangul/app, 로그인+이용권)   — 모든 구간 그대로
  trial 체험판(hangul.sososoop.com)                 — @cut trial 구간을 뺌 + window.__TRIAL__
  home  보호자용(소소숲 /hangul/home, 공개)          — @cut home 구간을 뺌 + window.__HW_ONLY__

표시는 한 줄을 통째로 차지해야 한다(겹쳐 써도 됨):
  /*@cut trial home*/ … /*@end*/      (JS·CSS)
  <!--@cut home--> … <!--@end-->       (HTML)

체험판·보호자용은 화면에서 잠그는 것만으로는 코드가 그대로 내려가서 누구나 정식판을 꺼내 쓸 수 있었다
(2026-10-26 보안 점검). 그래서 공개 파일에서는 유료 코드를 아예 빼고 낸다.

  사용법:  python3 build-variants.py trial dist/index.html
           python3 build-variants.py sososoop "<소소숲 폴더>"   → app-html.json(full)·home-html.json(home)
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'index.html'
VARIANTS = ('full', 'trial', 'home')
FLAGS = {'trial': '__TRIAL__', 'home': '__HW_ONLY__'}

CUT = re.compile(r'^\s*(?:/\*|<!--)@cut((?:\s+(?:trial|home))+)\s*(?:\*/|-->)\s*$')
END = re.compile(r'^\s*(?:/\*|<!--)@end\s*(?:\*/|-->)\s*$')
ANY_MARK = re.compile(r'@(?:cut|end)\b')

# 빠진 게 맞는지 확인하는 표지 — 이 이름이 남아 있으면 빌드를 멈춘다
MUST_NOT_CONTAIN = {
    # DEX_ANIMAL 등: 정식판 전용 그림 도감 주제 자료(이름 목록) — 체험판에는 공룡만
    'trial': ['function encodeHw', 'exportedAt:', 'openNameModal(\'새 프로필', 'const DEX_ANIMAL'],
    'home': ['function encodeHw', 'function generate(', 'function genPairs', 'function genSentencesOnline',
             'function newStage', 'function exportProfiles', 'function importProfiles', 'SENT_BLOCK',
             'id="genPanel"', 'id="gamePanel"', 'id="progPanel"', 'const SENTENCES',
             'id="dexPanel"', 'const DEX=', 'const DEX_DINO'],
}
MUST_CONTAIN = {
    'trial': ['id="dexPanel"', 'const DEX_DINO'],   # 체험판 그림 도감은 공룡 주제
    'home': ['function applyLockModeIfNeeded', 'function decodeHw', 'id="playPanel"', 'function randomWord',
             'function openHandwriting'],
}


def build(variant: str) -> str:
    assert variant in VARIANTS
    out, stack = [], []
    for n, line in enumerate(SRC.read_text(encoding='utf-8').splitlines(keepends=True), 1):
        m = CUT.match(line)
        if m:
            stack.append((n, set(m.group(1).split())))
            continue
        if END.match(line):
            if not stack:
                sys.exit(f'index.html:{n}: 짝 없는 @end')
            stack.pop()
            continue
        if ANY_MARK.search(line) and ('/*@' in line or '<!--@' in line):
            sys.exit(f'index.html:{n}: 표시는 한 줄을 통째로 써야 해요 — {line.strip()[:80]}')
        if any(variant in vs for _, vs in stack):
            continue
        out.append(line)
    if stack:
        sys.exit(f'index.html:{stack[-1][0]}: @cut 이 @end 없이 끝남')
    html = ''.join(out)
    if variant in FLAGS:
        assert html.count('<head>') == 1
        html = html.replace('<head>', f'<head><script>window.{FLAGS[variant]}=true</script>', 1)
    for s in MUST_NOT_CONTAIN.get(variant, []):
        if s in html:
            sys.exit(f'{variant}: 빠져야 할 코드가 남아 있어요 — {s}')
    for s in MUST_CONTAIN.get(variant, []):
        if s not in html:
            sys.exit(f'{variant}: 꼭 있어야 할 코드가 없어요 — {s}')
    return html


def main(argv):
    if len(argv) == 3 and argv[1] in VARIANTS:
        html = build(argv[1])
        Path(argv[2]).write_text(html, encoding='utf-8')
        print(f'  {argv[1]} → {argv[2]} ({len(html):,}자)')
    elif len(argv) == 3 and argv[1] == 'sososoop':
        dest = Path(argv[2]) / 'src/app/hangul'
        if not dest.is_dir():
            sys.exit(f'소소숲 폴더가 아니에요: {argv[2]}')
        for variant, name in (('full', 'app-html.json'), ('home', 'home-html.json')):
            html = build(variant)
            (dest / name).write_text(json.dumps(html, ensure_ascii=False), encoding='utf-8')
            print(f'  {variant} → {dest / name} ({len(html):,}자)')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
