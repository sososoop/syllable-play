import json,glob,re,sys,collections
BLOCK=['키스','연애','애인','사귀','임신','성관계','음주','흡연','폭력','폭행','흉기','유흥','유혹','섹시','야한','변태','노출','포탄','총알','대포','폭격','전쟁','팬티','브래지어','속옷','섹스','성교','성기','강간','성폭','매춘','마약','자살','자해','살인','살해','시체','사형','학살','고문','도박','포르노','음란','불륜','간통','낙태','총살','폭탄','테러','처형','시신','죽여','죽인','담배','소주','맥주','술집','술을','술에','술이','술잔','이혼','외도']
LV={'초급':'1','중급':'2','고급':'3'}
def feats(f): 
    if isinstance(f,dict): f=[f]
    return {x['att']:x.get('val','') for x in (f or []) if isinstance(x,dict) and 'att' in x}
best={}   # sentence -> (level, headword)
types=collections.Counter()
for fn in sorted(glob.glob(sys.argv[1]+'/*.json')):
    for e in json.load(open(fn))['LexicalResource']['Lexicon']['LexicalEntry']:
        ef=feats(e.get('feat')); 
        if ef.get('lexicalUnit')!='단어': continue
        lv=LV.get(ef.get('vocabularyLevel'),'0')
        L=e['Lemma']; L=L[0] if isinstance(L,list) else L; hw=feats(L['feat']).get('writtenForm','')
        senses=e.get('Sense') or []
        if isinstance(senses,dict): senses=[senses]
        for s in senses:
            exs=s.get('SenseExample') or []
            if isinstance(exs,dict): exs=[exs]
            for x in exs:
                xf=feats(x.get('feat')); types[xf.get('type')]+=1
                if xf.get('type') not in ('구','문장'): continue
                t=re.sub(r'\s+',' ',xf.get('example','')).strip()
                if not re.fullmatch(r'[가-힣 .,?!]+',t): continue
                if any(b in t for b in BLOCK): continue
                if len(t.split(' '))>8 or len(re.sub(r'[^가-힣]','',t))<2: continue
                r=lambda v:'1230'.index(v)
                if t not in best or r(lv)<r(best[t][0]): best[t]=(lv,hw)
print(types, len(best), file=sys.stderr)
g=collections.defaultdict(lambda: collections.defaultdict(list))
for t,(lv,hw) in best.items(): g[lv][hw].append(t)
import os
for lv,d in sorted(g.items()):
    out={"src":"국립국어원 「한국어기초사전」 예문 (CC BY-SA 2.0 KR), 2026-09 전체 내려받기","source_url":"https://krdict.korean.go.kr","license":"CC BY-SA 2.0 KR","license_url":"https://creativecommons.org/licenses/by-sa/2.0/kr/",
     "notice":"기초사전 예문 중 한글·문장부호만 있고 8어절 이하인 것을 표제어 등급별로 묶었습니다(부적절 단어 제외). 이 파일도 같은 라이선스로 이용할 수 있습니다. 제작: 소소숲 : 지혜의 기록소",
     "level":lv,"s":"\n".join(hw+"\t"+"\t".join(ss) for hw,ss in d.items())}
    f=os.path.join(sys.argv[2],f"hangul-sent-{lv}.json")
    json.dump(out,open(f,'w'),ensure_ascii=False,separators=(',',':'))
    print(lv,len(d),'words',sum(len(v) for v in d.values()),'sents',os.path.getsize(f),file=sys.stderr)
