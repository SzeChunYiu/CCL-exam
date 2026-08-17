/* Simplified CCL interface layered on top of the existing exam engine. */
(function(){
  const originalRenderStudy=renderStudy;
  const originalRenderHistory=renderHistory;

  nav = function(active='dashboard'){
    const items=[
      ['dashboard','Practice'],
      ['library','Library'],
      ['study','Study'],
      ['history','Results']
    ];
    return `<header class="topbar">
      <div class="brand" onclick="go('dashboard')" style="cursor:pointer"><div class="mark">CCL</div><div>CCL Practice</div></div>
      <nav class="nav">${items.map(([v,l])=>`<button class="${active===v?'active':''}" onclick="go('${v}')">${l}</button>`).join('')}</nav>
    </header>`;
  };

  page = function(inner,active='dashboard'){
    return `<main class="shell">${nav(active)}${inner}<div class="footer">Independent CCL-style practice. Not an official NAATI test interface.</div></main>`;
  };

  renderDashboard = function(){
    const completed=state.user.completed.length;
    const attempts=state.user.history.length;
    const audioReady=state.remoteAudio?.mode==='segments';
    $('#app').innerHTML=page(`
      <section class="simple-home">
        <div class="eyebrow">English ⇄ Cantonese</div>
        <h1>Practise the exam.<br>Nothing else.</h1>
        <p class="lead">Start with a strict two-dialogue mock, or practise one topic at a time. The exam screen is intentionally quiet and meeting-like so you focus on listening, notes on paper, and interpreting.</p>
        <div class="simple-actions">
          <button class="btn primary" onclick="startMock(0)">Start Mock Test 01</button>
          <button class="btn" onclick="randomMock()">Random mock</button>
        </div>

        <div class="simple-section-title"><h2>Practice modes</h2></div>
        <div class="mode-list">
          <div class="mode-row" onclick="renderMockPicker()"><div class="mode-num">01</div><div><strong>Mock exam</strong><span>Two dialogues · 20-minute performance clock · hidden scripts · repeat tracking</span></div><div class="mode-arrow">›</div></div>
          <div class="mode-row" onclick="renderPracticeSetup()"><div class="mode-num">02</div><div><strong>Topic practice</strong><span>Choose a topic and compare your interpretation after each segment</span></div><div class="mode-arrow">›</div></div>
          <div class="mode-row" onclick="renderDrillSetup()"><div class="mode-num">03</div><div><strong>Quick drill</strong><span>Ten unseen segments for fast English ⇄ Cantonese switching</span></div><div class="mode-arrow">›</div></div>
          <div class="mode-row" onclick="go('library')"><div class="mode-num">04</div><div><strong>100-dialogue library</strong><span>Search all Australian community scenarios</span></div><div class="mode-arrow">›</div></div>
        </div>
        <div class="home-meta"><span>${state.summary?.dialogues||100} dialogues</span><span>${state.summary?.mock_tests||50} mock tests</span><span>${completed} completed</span><span>${attempts} saved attempts</span><span>${audioReady?'Neural MP3 enabled':'Audio fallback enabled'}</span></div>
      </section>`,'dashboard');
  };

  renderMockPicker = function(){
    const pairs=testPairs();
    $('#app').innerHTML=page(`<section class="simple-page">
      <div class="simple-page-head"><div><div class="eyebrow">Strict mode</div><h1>Mock exams</h1><p>Pick one pair. Scripts stay hidden until review.</p></div><button class="btn" onclick="randomMock()">Random mock</button></div>
      <div class="mock-list">${pairs.map((p,i)=>`<div class="mock-row">
        <div class="mock-id">TEST ${String(i+1).padStart(2,'0')}</div>
        <div class="mock-main"><strong>${esc(p[0].title)} · ${esc(p[1].title)}</strong><span>${esc(p[0].topic)} + ${esc(p[1].topic)}</span></div>
        <button class="btn primary" onclick="startMock(${i})">Start</button>
      </div>`).join('')}</div>
    </section>`,'dashboard');
  };

  renderPracticeSetup = function(){
    $('#app').innerHTML=page(`<section class="simple-setup">
      <div class="eyebrow">Training mode</div><h1>Topic practice</h1>
      <p>Listen first. Interpret without seeing the script. Reveal the source and model only after you finish.</p>
      <div class="setup-panel">
        <label><div class="kicker">Topic</div><select id="pTopic" class="select"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select></label>
        <label><div class="kicker">Difficulty</div><select id="pDiff" class="select"><option value="All">All levels</option><option>Easy</option><option>Medium</option><option>Hard</option></select></label>
        <div class="actions"><button class="btn primary" onclick="randomPracticeFromSetup()">Start random dialogue</button><button class="btn" onclick="go('library')">Browse library</button></div>
      </div>
    </section>`,'dashboard');
  };

  renderDrillSetup = function(){
    $('#app').innerHTML=page(`<section class="simple-setup">
      <div class="eyebrow">Retrieval training</div><h1>Quick drill</h1>
      <p>Ten unseen segments. Use this when you want a short session focused on speed, numbers and terminology.</p>
      <div class="setup-panel">
        <label><div class="kicker">Topic</div><select id="dTopic" class="select"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select></label>
        <label><div class="kicker">Direction</div><select id="dDir" class="select"><option value="All">Both directions</option><option value="en">English → Cantonese</option><option value="yue">Cantonese → English</option></select></label>
        <div class="actions"><button class="btn primary" onclick="startDrill()">Start 10 segments</button></div>
      </div>
    </section>`,'dashboard');
  };

  renderMock = function(){
    const s=state.session,{d,seg}=currentMock();
    const total=s.dialogueIds.reduce((a,id)=>a+state.byId[id].segments.length,0);
    const done=s.dialogueIds.slice(0,s.di).reduce((a,id)=>a+state.byId[id].segments.length,0)+s.si;
    const key=sessionKey(d.id,seg.n), played=s.played[key]||0, repeats=s.repeats[d.id]||0;
    const isEnglish=seg.source_lang==='en';
    $('#app').innerHTML=`<div class="meeting-exam">
      <header class="meeting-top">
        <div class="meeting-title"><span class="meeting-dot"></span><div>CCL mock exam<small>Dialogue ${s.di+1} of 2 · Segment ${seg.n} of ${d.segments.length}</small></div></div>
        <div id="timer" class="meeting-timer">${fmtTime(s.timeLeft)}</div>
        <button class="meeting-exit" onclick="finishSession()">End practice</button>
      </header>
      <div class="meeting-progress"><span style="width:${done/total*100}%"></span></div>
      <div class="exam-disclaimer">Meeting-style practice · not the official NAATI interface</div>
      <div class="repeat-counter">Repeats this dialogue: <strong>${repeats}</strong>${repeats===0?' · 1 allowance':repeats===1?' · allowance used':' · extra repeat'}</div>
      <main class="meeting-stage">
        <section id="sourceTile" class="source-tile ${isEnglish?'speaker-en':'speaker-yue'}">
          <div class="source-center">
            <div class="audio-avatar">${isEnglish?'E':'粵'}</div>
            <div class="source-label">Source audio</div>
            <div id="audioStatus" class="source-sub">Press Start. After the chime, begin interpreting promptly.</div>
            <div class="source-direction">${isEnglish?'English source':'Cantonese source'}</div>
            <div id="interpretCount" class="interpret-count"></div>
          </div>
          <div class="tile-name">CCL test audio</div>
        </section>
        <aside class="self-tile"><div class="self-avatar">YOU</div><div class="self-name">Candidate · camera on</div></aside>
        <div class="meeting-context"><strong>${esc(d.topic)}</strong>${esc(d.title)}<br>Use pen and loose paper for notes.</div>
      </main>
      <div class="meeting-controls">
        <button id="playBtn" class="call-control primary" onclick="playSessionSegment(false)" ${played?'disabled':''}>▶<span>Start</span></button>
        <button id="repeatBtn" class="call-control repeat ${repeats?'used':''}" onclick="playSessionSegment(true)" ${played?'':'disabled'}>↻<span>Repeat segment</span></button>
        <button id="recordBtn" class="call-control" onclick="toggleRecord()">●<span>Practice record</span></button>
        <button id="finishBtn" class="call-control finish" onclick="nextMock()" ${played?'':'disabled'}>✓<span>${s.di===1&&s.si===d.segments.length-1?'Finish exam':'Finish attempt'}</span></button>
      </div>
      <div id="recStatus" style="display:none"></div>
    </div>`;
  };

  playSessionSegment = async function(repeat){
    const {d,seg}=currentMock();
    if(repeat)state.session.repeats[d.id]=(state.session.repeats[d.id]||0)+1;
    state.session.played[sessionKey(d.id,seg.n)]=(state.session.played[sessionKey(d.id,seg.n)]||0)+1;
    renderRepeatOnly();
    const tile=$('#sourceTile'),start=$('#playBtn'),finish=$('#finishBtn');
    if(tile)tile.classList.add('active');
    if(start)start.disabled=true;
    if(finish)finish.disabled=true;
    await playSource(d,seg,1,()=>{
      if(tile)tile.classList.remove('active');
      if(finish)finish.disabled=false;
      startInterpretCountdown();
    });
  };

  renderRepeatOnly = function(){
    const box=$('.repeat-counter'); if(!box||!state.session)return;
    const {d}=currentMock(),n=state.session.repeats[d.id]||0;
    box.innerHTML=`Repeats this dialogue: <strong>${n}</strong>${n===0?' · 1 allowance':n===1?' · allowance used':' · extra repeat'}`;
    const repeat=$('#repeatBtn'); if(repeat){repeat.disabled=false;repeat.classList.toggle('used',n>0)}
  };

  startInterpretCountdown = function(){
    clearInterval(state.session?.interpretTimer);
    let n=5; const el=$('#interpretCount'),finish=$('#finishBtn');
    if(finish)finish.disabled=false;
    if(!el)return;
    el.textContent=`Interpret now · ${n}`;
    state.session.interpretTimer=setInterval(()=>{
      n--;
      const current=$('#interpretCount');
      if(!current){clearInterval(state.session.interpretTimer);return}
      current.textContent=n>0?`Interpret now · ${n}`:'Interpret now';
      if(n<=0)clearInterval(state.session.interpretTimer);
    },1000);
  };

  renderPractice = function(){
    const s=state.session,{d,seg}=currentPractice(),k=sessionKey(d.id,seg.n),revealed=!!s.revealed[k],m=s.marks[k]||{rating:null,tags:[]};
    $('#app').innerHTML=page(`<section class="simple-page">
      <div class="simple-practice-head"><div><div class="eyebrow">${esc(d.topic)} · ${d.difficulty}</div><h2>${esc(d.title)}</h2><div class="muted">Segment ${seg.n} of ${d.segments.length} · ${seg.source_lang==='en'?'English → Cantonese':'Cantonese → English'}</div></div><button class="btn" onclick="go('library')">Exit</button></div>
      <section class="card simple-practice-card">
        <div class="listen-icon">◖))</div><div id="audioStatus" class="prompt-hidden">Listen first. Keep the script hidden until you have interpreted.</div>
        <div style="margin:16px 0"><select class="select" id="practiceRate" onchange="setRate(this.value)"><option value="0.9" ${state.user.prefs.practiceRate==.9?'selected':''}>0.9×</option><option value="1" ${state.user.prefs.practiceRate==1?'selected':''}>1.0× sample pace</option><option value="1.08" ${state.user.prefs.practiceRate==1.08?'selected':''}>1.08×</option></select></div>
        <div class="actions" style="justify-content:center"><button class="btn primary" onclick="playPracticeSource()">Play source</button><button id="recordBtn" class="btn" onclick="toggleRecord()">Record mine</button></div><div id="recStatus" class="muted" style="margin-top:8px"></div>
        <div class="actions" style="justify-content:center;margin-top:18px">${revealed?'':'<button class="btn secondary" onclick="revealPractice()">Reveal & compare</button>'}</div>
        ${revealed?compareBlock(d,seg,m,'practice'):''}
      </section>
    </section>`,'library');
  };

  renderLibrary = function(){
    $('#app').innerHTML=page(`<section class="simple-page">
      <div class="simple-page-head"><div><div class="eyebrow">Practice bank</div><h1>100 dialogues</h1><p>Search by topic or Australian term.</p></div><button class="btn primary" onclick="renderPracticeSetup()">Random practice</button></div>
      <div class="simple-filterbar"><input id="libSearch" class="input" placeholder="Search ABN, Medicare, tenancy…" oninput="filterLibrary()"><select id="libTopic" class="select" onchange="filterLibrary()"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select><select id="libDiff" class="select" onchange="filterLibrary()"><option value="All">All levels</option><option>Easy</option><option>Medium</option><option>Hard</option></select><select id="libStatus" class="select" onchange="filterLibrary()"><option value="All">All status</option><option value="New">Not completed</option><option value="Done">Completed</option><option value="Fav">Favourites</option></select></div>
      <div id="libraryGrid" class="library-list"></div>
    </section>`,'library');
    filterLibrary();
  };

  filterLibrary = function(){
    const q=($('#libSearch')?.value||'').toLowerCase(),t=$('#libTopic')?.value||'All',df=$('#libDiff')?.value||'All',st=$('#libStatus')?.value||'All',done=completedSet();
    const ds=state.dialogues.filter(d=>(!q||`${d.id} ${d.title} ${d.term} ${d.term_yue} ${d.topic}`.toLowerCase().includes(q))&&(t==='All'||d.topic===t)&&(df==='All'||d.difficulty===df)&&(st==='All'||(st==='New'&&!done.has(d.id))||(st==='Done'&&done.has(d.id))||(st==='Fav'&&isFav(d.id))));
    const el=$('#libraryGrid'); if(!el)return;
    el.innerHTML=ds.length?ds.map(d=>`<div class="library-row"><div class="mock-id">${d.id} · ${d.difficulty}</div><div class="mock-main"><strong>${esc(d.title)}</strong><span>${esc(d.term)}</span></div><div class="library-topic">${esc(d.topic)}</div><div class="actions"><button class="star ${isFav(d.id)?'on':''}" onclick="toggleFav('${d.id}')">★</button><button class="btn primary" onclick="startPractice('${d.id}')">Practice</button></div></div>`).join(''):'<div class="card" style="padding:20px">No matching dialogues.</div>';
  };

  renderStudy = function(slug){ return originalRenderStudy(slug); };
  renderHistory = function(){ return originalRenderHistory(); };

  // Re-render after this layer loads if the data boot already completed.
  if(state?.summary && state.view==='dashboard')renderDashboard();
})();
