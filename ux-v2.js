/* UX v2: simplified information architecture informed by exam-prep and speaking-practice patterns. */
(function(){
  const baseQuestions=window.renderQuestions;
  const baseMockPicker=renderMockPicker;
  const baseStudy=renderStudy;
  const baseHistory=renderHistory;

  function lastAttempt(){
    const h=[...(state.user?.history||[])].sort((a,b)=>(b.date||0)-(a.date||0));
    return h[0]||null;
  }

  nav=function(active='dashboard'){
    const items=[
      ['dashboard','Home',"go('dashboard')"],
      ['mock','Mock',"renderMockPicker()"],
      ['questions','Questions',"renderQuestions()"],
      ['study','Study',"go('study')"],
      ['history','Progress',"go('history')"]
    ];
    return `<header class="topbar ux-topbar">
      <button class="brand ux-brand" onclick="go('dashboard')" aria-label="CCL Practice home"><span class="mark">CCL</span><span>CCL Practice</span></button>
      <nav class="nav ux-nav" aria-label="Primary navigation">${items.map(([v,l,act])=>`<button data-nav="${v}" class="${active===v?'active':''}" onclick="${act}">${l}</button>`).join('')}</nav>
    </header>`;
  };

  renderDashboard=function(){
    state.view='dashboard';
    const last=lastAttempt();
    const completed=state.user?.completed?.length||0;
    const attempts=state.user?.history?.length||0;
    const weak=state.user?.weak?.length||0;
    const score=last&&Number.isFinite(last.score)?`${last.score}%`:'—';
    const audio=state.remoteAudio?.mode==='segments'?'Neural MP3':'Fallback audio';
    $('#app').innerHTML=page(`<section class="ux-home">
      <div class="ux-hero">
        <div class="eyebrow">English ⇄ Cantonese · CCL practice</div>
        <h1>Choose one way to practise.</h1>
        <p>Use a full mock when you want exam pressure. Use the question bank when you want repetition. Use focused practice when you want to fix one skill.</p>
        <div class="ux-hero-actions">
          <button class="btn primary ux-large" onclick="startMock(0)">Start Mock Test 01</button>
          <button class="btn ux-large" onclick="renderQuestions()">Open question bank</button>
        </div>
      </div>

      <div class="ux-paths" aria-label="Practice choices">
        <article class="ux-path">
          <div class="ux-path-icon">01</div><div><h2>Mock exam</h2><p>Two dialogues, 20-minute clock, hidden scripts and repeat tracking.</p></div>
          <button class="btn" onclick="renderMockPicker()">Choose mock</button>
        </article>
        <article class="ux-path">
          <div class="ux-path-icon">02</div><div><h2>Question bank</h2><p>All 100 dialogues. Read every source, autoplay a full dialogue, then reveal models only when needed.</p></div>
          <button class="btn" onclick="renderQuestions()">Browse questions</button>
        </article>
        <article class="ux-path">
          <div class="ux-path-icon">03</div><div><h2>Focused practice</h2><p>Target one topic or run a short 10-segment retrieval drill.</p></div>
          <div class="ux-inline-actions"><button class="btn" onclick="renderPracticeSetup()">By topic</button><button class="btn" onclick="renderDrillSetup()">Quick drill</button></div>
        </article>
      </div>

      <section class="ux-progress-strip" aria-label="Practice progress">
        <div><strong>${completed}</strong><span>dialogues completed</span></div>
        <div><strong>${attempts}</strong><span>saved attempts</span></div>
        <div><strong>${weak}</strong><span>weak segments</span></div>
        <div><strong>${score}</strong><span>latest rating</span></div>
        <div><strong>${audio}</strong><span>audio source</span></div>
      </section>
      <p class="ux-footnote">Practice ratings are self-review metrics, not official NAATI scores.</p>
    </section>`,'dashboard');
  };

  renderMockPicker=function(){
    state.view='mockPicker';
    baseMockPicker();
    document.querySelectorAll('.ux-nav button').forEach(b=>b.classList.toggle('active',b.dataset.nav==='mock'));
    const head=document.querySelector('.simple-page-head h1'); if(head)head.textContent='Mock exams';
    const p=document.querySelector('.simple-page-head p'); if(p)p.textContent='Choose one two-dialogue test. Once started, scripts stay hidden until review.';
  };

  window.renderQuestions=function(){
    baseQuestions();
    state.view='questions';
    document.querySelectorAll('.ux-nav button').forEach(b=>b.classList.toggle('active',b.dataset.nav==='questions'));
    const h=document.querySelector('.questions-page h1'); if(h)h.textContent='Question bank';
    const p=document.querySelector('.questions-page .simple-page-head p'); if(p)p.textContent='Study openly here. Use autoplay for interpreting rhythm; use Mock when you want scripts hidden.';
    const status=document.getElementById('qAutoStatus'); if(status){status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.setAttribute('aria-atomic','true')}
    const bar=document.querySelector('.question-autoplay-bar'); if(bar){bar.setAttribute('role','region');bar.setAttribute('aria-label','Continuous practice player')}
    const filter=document.querySelector('.questions-filterbar'); if(filter){filter.setAttribute('role','search')}
    const list=document.getElementById('questionsList'); if(list)list.setAttribute('aria-label','Practice dialogues');
  };

  renderStudy=function(slug){
    state.view='study';
    baseStudy(slug);
    document.querySelectorAll('.ux-nav button').forEach(b=>b.classList.toggle('active',b.dataset.nav==='study'));
  };

  renderHistory=function(){
    state.view='history';
    baseHistory();
    document.querySelectorAll('.ux-nav button').forEach(b=>b.classList.toggle('active',b.dataset.nav==='history'));
  };

  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'&&state.view==='questions'&&typeof stopQuestionAutoplay==='function') stopQuestionAutoplay('Stopped');
  });
})();