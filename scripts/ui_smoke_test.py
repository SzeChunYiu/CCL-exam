from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
routes={
    'home':ROOT/'index.html',
    'mock':ROOT/'mock/index.html',
    'questions':ROOT/'questions/index.html',
    'practice':ROOT/'practice/index.html',
    'study':ROOT/'study/index.html',
    'progress':ROOT/'progress/index.html',
}
required_scripts=['/app.js','/neural-audio.js','/simple-ui.js','/questions-page.js','/ux-v2.js','/practice-player-v3.js','/route-pages.js','/ux-v4.js','/practice-studio-v5.js','/ux-v5.js']
required_css=['/styles.css','/simple.css','/questions.css','/ux-v2.css','/practice-player-v3.css','/ux-v4.css','/practice-studio-v5.css','/ux-v5.css']

for name,path in routes.items():
    assert path.exists(), f'missing route page: {path}'
    text=path.read_text()
    assert f'data-page="{name}"' in text, f'{name}: wrong/missing data-page'
    for asset in required_scripts:
        assert f'src="{asset}"' in text, f'{name}: missing script {asset}'
    for asset in required_css:
        assert f'href="{asset}"' in text, f'{name}: missing stylesheet {asset}'

route_js=(ROOT/'route-pages.js').read_text()
for url in ['/mock/','/questions/','/practice/','/study/','/progress/']:
    assert url in route_js, f'missing route URL {url}'
assert 'renderInitialRoute' in route_js
assert 'setTimeout(bootRoute' in route_js

player=(ROOT/'practice-player-v3.js').read_text()
for fn in ['playAllVisibleQuestions','playQuestionDialogue','previousQuestion','nextQuestion','toggleQuestionPlayer','toggleQuestionShuffle','stopQuestionAutoplay']:
    assert re.search(rf'window\.{fn}\s*=',player), f'missing player function {fn}'
for control in ['qShuffle','qPlayPause','qStopPlayer','qNowTitle','qNowSub','qQueueProgress']:
    assert control in player, f'missing player control {control}'
assert 'mediaSession.setActionHandler' in player
assert "e.code==='Space'" in player
assert "e.key==='ArrowLeft'" in player and "e.key==='ArrowRight'" in player
assert 'data-dialogue-id' in player and 'active-dialogue' in player

v4=(ROOT/'ux-v4.js').read_text()
for fn in ['filterMockList','collapseAllQuestions','expandAllQuestions','resetQuestionFilters']:
    assert re.search(rf'window\.{fn}\s*=',v4), f'missing v4 control {fn}'
for token in ['Officer · English','Client · Cantonese','Next segment','Shuffle me a mock','Shorter sessions']:
    assert token in v4, f'missing v4 UX token: {token}'
assert "e.code==='Space'" in v4 and "e.key.toLowerCase()==='r'" in v4 and "e.key==='Enter'" in v4

practice=(ROOT/'practice-studio-v5.js').read_text()
for fn in ['setPracticeDefaultV5','resumePracticeV5','updatePracticeMatchV5','startGuidedPracticeV5','surprisePracticeV5','previousPracticeV5','jumpPracticeV5','rateFocusedV5','tagFocusedV5','togglePracticeWeakV5','togglePracticeFavoriteV5','startWeakReviewV5','revealDrillV5','previousDrillV5']:
    assert re.search(rf'window\.{fn}\s*=',practice), f'missing Practice Studio control {fn}'
for token in ['Practice studio','Guided dialogue','Weak review','Hands-free player','practiceResume','Auto-play next','Advance after rating','5</option><option selected>10</option><option>20','Officer · English','Client · Cantonese']:
    assert token in practice, f'missing Practice Studio UX token: {token}'
assert "e.code==='Space'" in practice
assert "e.key==='ArrowLeft'" in practice and "e.key==='ArrowRight'" in practice
assert "['1','2','3'].includes(e.key)" in practice and "e.key.toLowerCase()==='w'" in practice
assert '/practice/?dialogue=' in practice and '/practice/?mode=weak' in practice

v5=(ROOT/'ux-v5.js').read_text()
for fn in ['testPracticeAudioV5','randomVisibleQuestionV5']:
    assert re.search(rf'window\.{fn}\s*=',v5), f'missing UX v5 control {fn}'
for token in ['Resume guided practice','Test audio + chime','Random question','Turn progress into the next rep','Study tools']:
    assert token in v5, f'missing UX v5 token: {token}'

css=(ROOT/'practice-player-v3.css').read_text()+(ROOT/'ux-v4.css').read_text()+(ROOT/'practice-studio-v5.css').read_text()+(ROOT/'ux-v5.css').read_text()
for selector in ['.question-player-v3','.question-dialogue.active-dialogue','.q-player-main','.ux-nav a','.v4-mock-row','.v4-form-card','.v4-study-content','.v4-progress-hero','.ps-mode-card','.ps-focus-card','.ps-stepper','.ps-play-big','.ps-rating','.v5-preflight','.v5-progress-actions']:
    assert selector in css, f'missing CSS selector {selector}'

# Catch the most common broken-button regression: an inline handler references a
# function that is not globally defined by any classic script loaded by the site.
js_files=[ROOT/p.lstrip('/') for p in required_scripts]
js_text='\n'.join(p.read_text() for p in js_files)
html_and_templates='\n'.join(p.read_text() for p in routes.values())+'\n'+js_text
attrs=re.findall(r'on(?:click|change|input)="([^"]+)"',html_and_templates)
called=set()
for attr in attrs:
    called.update(re.findall(r'(?<![.\w$])([A-Za-z_$][\w$]*)\s*\(',attr))
known={'if','for','while','switch','Math','Number','String','Object','Array','Date','JSON','Promise','setTimeout','clearTimeout','setInterval','clearInterval','confirm','alert'}
called-=known

def global_def(name):
    patterns=[
        rf'\bfunction\s+{re.escape(name)}\s*\(',
        rf'\bwindow\.{re.escape(name)}\s*=',
        rf'(?:^|[;\n])\s*{re.escape(name)}\s*=\s*function\b',
        rf'(?:^|[;\n])\s*(?:const|let|var)\s+{re.escape(name)}\s*=\s*(?:async\s*)?(?:function|\([^\n]*?\)\s*=>|[A-Za-z_$][\w$]*\s*=>)',
    ]
    return any(re.search(p,js_text,re.M) for p in patterns)

missing=sorted(name for name in called if not global_def(name))
assert not missing, f'inline UI handlers reference missing globals: {missing}'

print(f'UI v5 route/player/practice smoke checks passed; {len(called)} inline handler functions resolved')
