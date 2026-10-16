/**
 * 음절놀이 온라인 사전 중계(프록시) Worker
 * - 한국어기초사전 API 키를 Cloudflare Secret(KRDICT_KEY)에 숨김
 * - 앱은 이 Worker만 호출 → 키가 브라우저/소스에 노출되지 않음
 * - 단어 등재 여부(사실)만 판별용으로 중계. 뜻풀이는 저장/가공하지 않음.
 *   출처: 국립국어원 「한국어기초사전」 (CC BY-SA 2.0 KR)
 */
// 호출 허용 사이트: 소소숲·한글놀이 단독판·로컬 테스트만 (API 하루 한도 50,000건 보호)
const ALLOWED_ORIGIN = /^https:\/\/((www\.|hangul\.)?sososoop\.com|([a-z0-9-]+\.)?(hangul-blending-board|hangul-free)\.pages\.dev)$|^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    if (!ALLOWED_ORIGIN.test(origin)) {
      return new Response('forbidden', { status: 403 });
    }
    const cors = {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Vary': 'Origin',
    };
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: cors });
    }

    const url = new URL(request.url);
    const q = (url.searchParams.get('q') || '').trim();
    if (!q || q.length > 30) {   // 검색어 길이 제한 — 긴 임의 문자열로 상위 API 한도를 소모하지 못하게
      return new Response('bad q', { status: 400, headers: cors });
    }
    // 표준국어대사전 상세 검색 (/std) — 키는 Secret STDICT_KEY
    if (url.pathname === '/std') {
      if (!env.STDICT_KEY) {
        return new Response('server not configured', { status: 500, headers: cors });
      }
      const STD = {
        method: /^(exact|include|start|end)$/,
        letter_s: /^[1-9]$/,
        letter_e: /^[1-9]$/,
        pos: /^[0-9]{1,2}(,[0-9]{1,2})*$/,
        type1: /^(all|word|phrase|idiom|proverb)$/,
        type2: /^(all|native|chinese|loanword|hybrid)(,(native|chinese|loanword|hybrid))*$/,
        cat: /^[0-9]{1,2}(,[0-9]{1,2})*$/,
        start: /^([1-9][0-9]{0,2}|1000)$/,
        num: /^([1-9][0-9]?|100)$/,
      };
      let std = 'https://stdict.korean.go.kr/api/search.do'
        + '?key=' + encodeURIComponent(env.STDICT_KEY)
        + '&q=' + encodeURIComponent(q)
        + '&req_type=xml&advanced=y';
      for (const k in STD) {
        const v = url.searchParams.get(k);
        if (v !== null) {
          if (!STD[k].test(v)) return new Response('bad ' + k, { status: 400, headers: cors });
          std += '&' + k + '=' + encodeURIComponent(v);
        }
      }
      try {
        const r = await fetch(std, { cf: { cacheTtlByStatus: { '200-299': 86400, '400-599': 0 } } });
        return new Response(await r.text(), {
          status: r.status,
          headers: { ...cors, 'Content-Type': 'application/xml; charset=utf-8', 'Cache-Control': r.ok ? 'public, max-age=86400' : 'no-store' },
        });
      } catch (e) {
        return new Response('upstream error', { status: 502, headers: cors });
      }
    }

    if (!env.KRDICT_KEY) {
      return new Response('server not configured', { status: 500, headers: cors });
    }

    let api = 'https://krdict.korean.go.kr/api/search'
      + '?key=' + encodeURIComponent(env.KRDICT_KEY)
      + '&q=' + encodeURIComponent(q)
      + '&part=' + (url.searchParams.get('part') === 'exam' ? 'exam' : 'word')
      + '&sort=dict';

    // 상세 검색(단어 목록 만들기용): 허용된 값만 그대로 넘김
    const ADV = {
      method: /^(exact|include|start|end)$/,
      letter_s: /^[1-9]$/,
      letter_e: /^[1-9]$/,
      level: /^(all|level1|level2|level3)$/,
      pos: /^(all|[0-9]{1,2})(,[0-9]{1,2})*$/,
      type1: /^(all|word|phrase|expression)$/,
      start: /^([1-9][0-9]{0,2}|1000)$/,
      num: /^([1-9][0-9]?|100)$/,
    };
    const adv = [...url.searchParams.keys()].some(k => k in ADV) && url.searchParams.get('part') !== 'exam';
    if (adv) {
      api += '&advanced=y';
      for (const k in ADV) {
        const v = url.searchParams.get(k);
        if (v !== null) {
          if (!ADV[k].test(v)) return new Response('bad ' + k, { status: 400, headers: cors });
          api += '&' + k + '=' + encodeURIComponent(v);
        }
      }
      if (!url.searchParams.has('num')) api += '&num=100';
    } else if (url.searchParams.get('part') === 'exam') {
      // 용례 검색: start(페이지)·num만 허용
      for (const k of ['start', 'num']) {
        const v = url.searchParams.get(k);
        if (v !== null) {
          if (!ADV[k].test(v)) return new Response('bad ' + k, { status: 400, headers: cors });
          api += '&' + k + '=' + encodeURIComponent(v);
        }
      }
      if (!url.searchParams.has('num')) api += '&num=100';
    } else {
      api += '&num=20';
    }

    try {
      const r = await fetch(api, { cf: { cacheTtlByStatus: { '200-299': 86400, '400-599': 0 } } });
      const body = await r.text();
      return new Response(body, {
        status: r.status,
        headers: {
          ...cors,
          'Content-Type': 'application/xml; charset=utf-8',
          'Cache-Control': r.ok ? 'public, max-age=86400' : 'no-store',
        },
      });
    } catch (e) {
      return new Response('upstream error', { status: 502, headers: cors });
    }
  },
};
