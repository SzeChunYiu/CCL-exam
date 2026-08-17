/* UX v4 — atomic interaction polish across every top-level CCL page. */
(function(){
  const baseQuestions=window.renderQuestions;
  const basePractice=renderPractice;
  const baseStudy=renderStudy;
  const baseHistory=renderHistory;

  const routePage=()=>document.body.dataset.page||'home';
  const activeForRoute=()=>({home:'dashboard',mock:'mock',questions:'questions',practice:'practice',study:'study',progress:'history'}[routePage()]||'dashboard');

  nav=function(){
    const active=activeForRoute();
    const items=[['dashboard','Home','/'],['mock','Mock','/mock/'],['questions','Questions','/questions/'],['practice','Practice','/practice/'],['study','Study','/study/'],['history','Progress','/progress/']];
    return `<header class="topbar ux-topbar v4-topbar">
      <a class="brand ux-brand" href="/" aria-label="CCL Practice home"><span class="mark">CCL</span><span class="v4-brand-copy"><strong>CCL Practice</strong><small>English ⇄ Cantonese</small></span></a>
      <nav class="nav ux-nav" aria-label="Primary navigation">${items.map(([v,l,href])=>`<a data-nav="${v}" class="${active===v?'active':''}" href="${href}" ${active===v?'aria-current="page"':''}>${l}</a>`).join('')}</nav>
    </header>`;
  };

  page=function(inner){
    return `<main class="shell v4-shell">${nav()}${inner}<footer class="v4-footer"><span>Independent CCL-style practice · not an official NAATI interface</span><span>Scripts: officer English · client Cantonese</span></footer></main>`;
  };

  function lastAttempt(){return [...(state.user?.history||[])].sort((a,b)=>(b.date||0)-(a.date||0))[0]||null}
  function avgScore(){const s=(state.user?.history||[]).filter(x=>Number.isFinite(x.score));return s.length?Math.round(s.reduce((a,x)=>a+x.score,0)/s.length):null}

  renderDashboard=function(){
    state.view='dashboard';
    const last=lastAttempt(),avg=avgScore(),completed=state.user?.completed?.length||0,attempts=state.user?.history?.length||0,weak=state.user?.weak?.length||0;
    $('#app').innerHTML=page(`<section class="v4-home">
      <div class="v4-home-intro"><div class="eyebrow">English ⇄ Cantonese interpreting</div><h1>Practise one thing at a time.</h1><p>Mock the exam, run the question bank hands-free, or focus on one weak area. Everything else stays out of the way.</p><div class="v4-primary-actions"><a class="btn primary v4-cta" href="/questions/">Open question bank</a><a class="btn v4-cta" href="/mock/">Choose a mock</a></div></div>
      <section class="v4-quick-grid" aria-label="Main practice modes">
        <a class="v4-mode-card" href="/questions/"><span class="v4-mode-num">01</span><div><strong>Question bank</strong><p>100 dialogues · continuous player · previous/next · shuffle · model answers</p></div><span class="v4-arrow">›</span></a>
        <a class="v4-mode-card" href="/mock/"><span class="v4-mode-num">02</span><div><strong>Mock exam</strong><p>Two dialogues · hidden scripts · 20-minute clock · repeat tracking</p></div><span class="v4-arrow">›</span></a>
        <a class="v4-mode-card" href="/practice/"><span class="v4-mode-num">03</span><div><strong>Focused practice</strong><p>Topic practice and short retrieval drills when you do not want a full mock</p></div><span class="v4-arrow">›</span></a>
      </section>
      <section class="v4-summary" aria-label="Practice summary">
        <div><strong>${completed}</strong><span>dialogues completed</span></div><div><strong>${attempts}</strong><span>saved attempts</span></div><div><strong>${weak}</strong><span>weak segments</span></div><div><strong>${avg==null?'—':avg+'%'}</strong><span>average rating</span></div>
      </section>
      ${last?`<a class="v4-continue" href="/progress/"><span><strong>Continue from your latest review</strong><small>${new Date(last.date).toLocaleDateString()} · ${labelMode(last.mode)}${Number.isFinite(last.score)?` · ${last.score}%`:''}</small></span><span>View progress →</span></a>`:''}
    </section>`);
  };

  window.filterMockList=function(){
    const q=(document.getElementById('mockSearch')?.value||'').trim().toLowerCase();
    const topic=document.getElementById('mockTopic')?.value||'All';
    let shown=0;
    document.querySelectorAll('.v4-mock-row').forEach(row=>{
      const ok=(!q||row.dataset.search.includes(q))&&(topic==='All'||row.dataset.topics.split('|').includes(topic));
      row.hidden=!ok;if(ok)shown++;
    });
    const count=document.getElementById('mockCount');if(count)count.textContent=`${shown} mock${shown===1?'':'s'}`;
  };

  renderMockPicker=function(){
    state.view='mockPicker';
    const pairs=testPairs();
    $('#app').innerHTML=page(`<section class="v4-page">
      <header class="v4-page-head"><div><div class="eyebrow">Strict mode</div><h1>Mock exams</h1><p>Pick any two-dialogue test. Scripts stay hidden until review.</p></div><button class="btn" onclick="randomMock()">Shuffle me a mock</button></header>
      <div class="v4-controlbar"><input id="mockSearch" class="input" placeholder="Search a topic or scenario" oninput="filterMockList()"><select id="mockTopic" class="select" onchange="filterMockList()"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select><span id="mockCount" class="v4-count">${pairs.length} mocks</span></div>
      <div class="v4-mock-list">${pairs.map((p,i)=>{
        const segs=p.reduce((n,d)=>n+d.segments.length,0),search=`${p[0].title} ${p[1].title} ${p[0].topic} ${p[1].topic}`.toLowerCase();
        return `<article class="v4-mock-row" data-search="${esc(search)}" data-topics="${esc(p[0].topic)}|${esc(p[1].topic)}"><div class="v4-mock-id"><span>MOCK</span><strong>${String(i+1).padStart(2,'0')}</strong></div><div class="v4-mock-copy"><strong>${esc(p[0].title)}</strong><span>${esc(p[0].topic)} · ${p[0].difficulty}</span><strong>${esc(p[1].title)}</strong><span>${esc(p[1].topic)} · ${p[1].difficulty}</span></div><div class="v4-mock-meta"><span>${segs} segments</span><span>2 dialogues</span></div><button class="btn primary" onclick="startMock(${i})" aria-label="Start mock ${i+1}">Start</button></article>`;
      }).join('')}</div>
    </section>`);
  };

  window.renderPracticeHub=function(){
    state.view='practice';
    const mode=new URLSearchParams(location.search).get('mode');
    if(mode==='topic'){renderPracticeSetup();return}if(mode==='drill'){renderDrillSetup();return}
    $('#app').innerHTML=page(`<section class="v4-page v4-narrow"><header class="v4-page-head"><div><div class="eyebrow">Focused practice</div><h1>Shorter sessions</h1><p>Choose the kind of repetition you need today.</p></div></header><div class="v4-choice-grid"><a class="v4-choice" href="/practice/?mode=topic"><span class="v4-choice-icon">T</span><div><strong>Topic practice</strong><p>Choose a topic and difficulty, then work through a complete dialogue.</p></div><span>Choose topic →</span></a><a class="v4-choice" href="/practice/?mode=drill"><span class="v4-choice-icon">10</span><div><strong>Quick drill</strong><p>Ten unseen segments for fast retrieval and direction switching.</p></div><span>Start drill →</span></a></div></section>`);
  };

  renderPracticeSetup=function(){
    state.view='practiceSetup';
    $('#app').innerHTML=page(`<section class="v4-page v4-form-page"><a class="v4-back" href="/practice/">← Focused practice</a><header class="v4-page-head"><div><div class="eyebrow">Topic practice</div><h1>Choose a dialogue</h1><p>Listen first. Reveal the script only after you have interpreted.</p></div></header><div class="v4-form-card"><label><span>Topic</span><select id="pTopic" class="select"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select></label><label><span>Difficulty</span><select id="pDiff" class="select"><option value="All">All levels</option><option>Easy</option><option>Medium</option><option>Hard</option></select></label><div class="v4-form-help"><strong>What happens next?</strong><span>You hear one source segment at a time, interpret it, then reveal the model answer when you are ready.</span></div><div class="v4-form-actions"><button class="btn primary v4-cta" onclick="randomPracticeFromSetup()">Start random dialogue</button><a class="btn" href="/questions/">Browse all questions</a></div></div></section>`);
  };

  renderDrillSetup=function(){
    state.view='drillSetup';
    $('#app').innerHTML=page(`<section class="v4-page v4-form-page"><a class="v4-back" href="/practice/">← Focused practice</a><header class="v4-page-head"><div><div class="eyebrow">Quick drill</div><h1>Ten fast segments</h1><p>A short session for retrieval speed, numbers and terminology.</p></div></header><div class="v4-form-card"><label><span>Topic</span><select id="dTopic" class="select"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select></label><label><span>Speaker</span><select id="dDir" class="select"><option value="All">Both speakers</option><option value="en">English officer → Cantonese</option><option value="yue">Cantonese client → English</option></select></label><div class="v4-form-help"><strong>Session size</strong><span>10 source segments · scripts hidden until review.</span></div><div class="v4-form-actions"><button class="btn primary v4-cta" onclick="startDrill()">Start 10 segments</button></div></div></section>`);
  };

  renderMock=function(){
    const s=state.session,{d,seg}=currentMock();
    const total=s.dialogueIds.reduce((a,id)=>a+state.byId[id].segments.length,0),done=s.dialogueIds.slice(0,s.di).reduce((a,id)=>a+state.byId[id].segments.length,0)+s.si;
    const key=sessionKey(d.id,seg.n),played=s.played[key]||0,repeats=s.repeats[d.id]||0,isOfficer=seg.source_lang==='en';
    $('#app').innerHTML=`<div class="meeting-exam v4-exam"><header class="meeting-top v4-exam-top"><div class="meeting-title"><span class="meeting-dot"></span><div><strong>CCL mock practice</strong><small>Dialogue ${s.di+1}/2 · Segment ${seg.n}/${d.segments.length}</small></div></div><div id="timer" class="meeting-timer">${fmtTime(s.timeLeft)}</div><button class="meeting-exit" onclick="finishSession()" aria-label="End mock practice">End practice</button></header><div class="meeting-progress"><span style="width:${Math.max(2,done/total*100)}%"></span></div><div class="exam-disclaimer">Mock ${String(s.testIndex+1).padStart(2,'0')} · ${esc(d.topic)}</div><div class="repeat-counter">Repeat: <strong>${repeats}</strong>${repeats===0?' · one allowance available':repeats===1?' · allowance used':' · extra repeat'}</div><main class="meeting-stage"><section id="sourceTile" class="source-tile ${isOfficer?'speaker-en':'speaker-yue'}"><div class="source-center"><div class="audio-avatar">${isOfficer?'O':'C'}</div><div class="source-label">${isOfficer?'Officer · English':'Client · Cantonese'}</div><div id="audioStatus" class="source-sub">Press Start. After the chime, interpret in first person.</div><div class="source-direction">${isOfficer?'Interpret into Cantonese':'Interpret into English'}</div><div id="interpretCount" class="interpret-count"></div></div><div class="tile-name">Test audio</div></section><aside class="self-tile"><div class="self-avatar">YOU</div><div class="self-name">Candidate</div></aside><div class="meeting-context"><strong>${esc(d.title)}</strong>Use pen and loose paper for notes.</div></main><div class="meeting-controls"><button id="playBtn" class="call-control primary" onclick="playSessionSegment(false)" ${played?'disabled':''} title="Play source segment">▶<span>Start</span></button><button id="repeatBtn" class="call-control repeat ${repeats?'used':''}" onclick="playSessionSegment(true)" ${played?'':'disabled'} title="Repeat this source segment">↻<span>Repeat</span></button><button id="recordBtn" class="call-control" onclick="toggleRecord()" title="Record your interpretation">●<span>Record</span></button><button id="finishBtn" class="call-control finish" onclick="nextMock()" ${played?'':'disabled'} title="Finish this interpretation and continue">✓<span>${s.di===1&&s.si===d.segments.length-1?'Finish exam':'Next segment'}</span></button></div><div id="recStatus" class="v4-rec-status" aria-live="polite"></div></div>`;
  };

  renderPractice=function(){
    basePractice();
    state.view='practice';
    const s=state.session,{d,seg}=currentPractice();
    const head=document.querySelector('.simple-practice-head');
    if(head){head.classList.add('v4-practice-head');const exit=head.querySelector('.btn');if(exit){exit.textContent='Back to questions';exit.onclick=()=>location.href='/questions/'}}
    const card=document.querySelector('.simple-practice-card');if(card){card.classList.add('v4-practice-card');card.insertAdjacentHTML('afterbegin',`<div class="v4-mini-progress"><span>Dialogue ${d.id}</span><strong>Segment ${seg.n}/${d.segments.length}</strong><span>${seg.source_lang==='en'?'Officer · English':'Client · Cantonese'}</span></div><div class="v4-progress-track"><span style="width:${seg.n/d.segments.length*100}%"></span></div>`)}
  };

  window.renderQuestions=function(){
    baseQuestions();
    const toolbar=document.querySelector('.question-toolbar-v3');
    if(toolbar&&!document.getElementById('qListTools'))toolbar.insertAdjacentHTML('beforeend',`<div id="qListTools" class="v4-question-tools"><button class="btn" onclick="collapseAllQuestions()">Collapse all</button><button class="btn" onclick="expandAllQuestions()">Expand all</button><button class="btn" onclick="resetQuestionFilters()">Reset filters</button></div>`);
    const summary=document.querySelector('.question-summary');if(summary)summary.classList.add('v4-question-summary');
  };
  window.collapseAllQuestions=function(){document.querySelectorAll('.question-dialogue').forEach(x=>x.open=false)};
  window.expandAllQuestions=function(){document.querySelectorAll('.question-dialogue').forEach(x=>x.open=true)};
  window.resetQuestionFilters=function(){const s=document.getElementById('qSearch'),t=document.getElementById('qTopic'),d=document.getElementById('qDir');if(s)s.value='';if(t)t.value='All';if(d)d.value='All';filterQuestions()};

  renderStudy=function(slug){
    const result=baseStudy(slug);state.view='study';
    const enhance=()=>{const pageEl=document.querySelector('.section');if(pageEl)pageEl.classList.add('v4-study-page');const h=document.querySelector('.section-head h2');if(h)h.textContent='Study';const navEl=document.querySelector('.study-nav');if(navEl){navEl.classList.add('v4-study-nav');navEl.setAttribute('aria-label','Study sections')}const content=document.getElementById('studyContent');if(content)content.classList.add('v4-study-content');};
    enhance();setTimeout(enhance,250);return result;
  };

  renderHistory=function(){
    baseHistory();state.view='history';
    const hero=document.querySelector('.hero');if(hero)hero.classList.add('v4-progress-hero');
    const heading=document.querySelector('.hero h1');if(heading){heading.textContent='Progress';heading.removeAttribute('style')}
    const lead=document.querySelector('.hero p');if(lead)lead.textContent='Use your saved attempts to spot recurring errors and decide what to practise next.';
    document.querySelectorAll('.history-row').forEach(x=>x.classList.add('v4-history-row'));
  };

  document.addEventListener('keydown',e=>{
    if(routePage()!=='mock'||!state.session||state.session.mode!=='mock'||e.target?.closest?.('input,textarea,select,[contenteditable="true"]'))return;
    if(e.code==='Space'&&!document.getElementById('playBtn')?.disabled){e.preventDefault();playSessionSegment(false)}
    else if(e.key.toLowerCase()==='r'&&!document.getElementById('repeatBtn')?.disabled){e.preventDefault();playSessionSegment(true)}
    else if(e.key==='Enter'&&!document.getElementById('finishBtn')?.disabled){e.preventDefault();nextMock()}
  });
})();