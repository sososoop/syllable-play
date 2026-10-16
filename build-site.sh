#!/bin/bash
# 한글놀이 배포용 폴더(dist) 생성 스크립트
#
# ~/클로드/난독 폴더에는 학습자료·기획서·아동 개인자료가 함께 있어서
# 폴더째 업로드하면 전부 공개된다. 공개해도 되는 파일만 여기에 적고,
# dist/ 안의 것만 Cloudflare Pages로 올린다.
#
#   사용법:  ./build-site.sh            → dist/ 만들기
#            ./build-site.sh --deploy   → dist/ 만들고 라이브 배포까지
set -euo pipefail
cd "$(dirname "$0")"

# 공개할 파일·폴더 (여기 없는 것은 절대 올라가지 않음)
SITE_FILES=(
  index.html
  hangul-words.json
  hangul-words-std.json
  hangul-sent-1.json
  hangul-sent-2.json
  hangul-sent-3.json
  hangul-sent-0.json
  manual.html
  manual-img
  .nojekyll
)

rm -rf dist && mkdir -p dist
for f in "${SITE_FILES[@]}"; do
  [ -e "$f" ] && cp -R "$f" dist/ && echo "  + $f"
done
echo "dist/ 준비 완료 — 파일 $(find dist -type f | wc -l | tr -d ' ')개"

if [ "${1:-}" = "--deploy" ]; then
  for project in hangul-blending-board hangul-free; do
    echo "== $project 배포 =="
    npx --yes wrangler@latest pages deploy dist --project-name "$project" --branch main --commit-dirty=true
  done
fi
