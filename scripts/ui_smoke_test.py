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
required_scripts=['/app.js','/neural-audio.js','/simple-ui.js','/questions-page.js','/ux-v2.js','/practice-player-v3.js','/route-pages.js']
required_css=['/styles.css','/simple.css','/questions.css','/ux-v2.css','/practice-player-v3.css']

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

css=(ROOT/'practice-player-v3.css').read_text()
for selector in ['.question-player-v3','.question-dialogue.active-dialogue','.q-player-main','.ux-nav a']:
    assert selector in css, f'missing CSS selector {selector}'

print('UI route/player smoke checks passed')
