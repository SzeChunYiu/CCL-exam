/* Real page routing for the static CCL site. Each top-level section has its own URL. */
(function(){
  const legacyGo=go;
  const routes={dashboard:'/',mock:'/mock/',questions:'/questions/',study:'/study/',history:'/progress/',library:'/questions/',vocabulary:'/study/?view=vocabulary',practice:'/practice/'};

  window.siteRoute=function(view,query=''){
    const base=routes[view]||'/';
    location.href=query?`${base}${base.includes('?')?'&':'?'}${query}`:base;
  };

  go=function(v){if(routes[v]){location.href=routes[v];return}legacyGo(v)};

  nav=function(active='dashboard'){
    const items=[['dashboard','Home','/'],['mock','Mock','/mock/'],['questions','Questions','/questions/'],['practice','Practice','/practice/'],['study','Study','/study/'],['history','Progress','/progress/']];
    return `<header class="topbar ux-topbar"><a class="brand ux-brand" href="/" aria-label="CCL Practice home"><span class="mark">CCL</span><span>CCL Practice</span></a><nav class="nav ux-nav" aria-label="Primary navigation">${items.map(([v,l,href])=>`<a data-nav="${v}" class="${active===v?'active':''}" href="${href}">${l}</a>`).join('')}</nav></header>`;
  };

  function lastAttempt(){const h=[...(state.user?.history||[])].sort((a,b)=>(b.date||0)-(a.date||0));return h[0]||null}

  renderDashboard=function(){
    state.view='dashboard';
    const last=lastAttempt(),completed=state.user?.completed?.length||0,attempts=state.user?.history?.length||0,weak=state.user?.weak?.length||0;
    const score=last&&Number.isFinite(last.score)?`${last.score}%`:'—';
    const audio=state.remoteAudio?.mode==='segments'?'1,412 neural MP3 segments':'Fallback audio';
    $('#app').innerHTML=page(`<section class="ux-home"><div class="ux-hero"><div class="eyebrow">English ⇄ Cantonese · CCL practice</div><h1>Listen. Interpret. Repeat.</h1><p>Use Mock for exam pressure, Questions for hands-free dialogue practice, or Practice for a focused session.</p><div class="ux-hero-actions"><a class="btn primary ux-large" href="/mock/">Start a mock</a><a class="btn ux-large" href="/questions/">Open question bank</a></div></div>
      <div class="ux-paths" aria-label="Practice choices"><article class="ux-path"><div class="ux-path-icon">01</div><div><h2>Mock exam</h2><p>Two dialogues, hidden scripts, repeat tracking and a 20-minute practice clock.</p></div><a class="btn" href="/mock/">Choose mock</a></article><article class="ux-path"><div class="ux-path-icon">02</div><div><h2>Question bank</h2><p>All 100 dialogues with a persistent player, adjustable interpreting pauses and model answers.</p></div><a class="btn" href="/questions/">Open player</a></article><article class="ux-path"><div class="ux-path-icon">03</div><div><h2>Focused practice</h2><p>Choose a topic or run a short retrieval drill without the full mock-test pressure.</p></div><a class="btn" href="/practice/">Choose practice</a></article></div>
      <section class="ux-progress-strip" aria-label="Practice progress"><div><strong>${completed}</strong><span>dialogues completed</span></div><div><strong>${attempts}</strong><span>saved attempts</span></div><div><strong>${weak}</strong><span>weak segments</span></div><div><strong>${score}</strong><span>latest rating</span></div><div><strong>${audio}</strong><span>audio library</span></div></section><p class="ux-footnote">Practice ratings are self-review metrics, not official NAATI scores.</p></section>`,'dashboard');
  };

  window.renderPracticeHub=function(){
    state.view='practice';
    const mode=new URLSearchParams(location.search).get('mode');
    if(mode==='topic'){renderPracticeSetup();return}if(mode==='drill'){renderDrillSetup();return}
    $('#app').innerHTML=page(`<section class="ux-section-page"><div class="eyebrow">Focused practice</div><h1>Choose a shorter session.</h1><p class="ux-section-lead">Use these modes when you want repetition without running a full mock.</p><div class="ux-paths ux-paths-two"><article class="ux-path"><div class="ux-path-icon">A</div><div><h2>Topic practice</h2><p>Choose a topic and difficulty, then reveal and compare after each interpretation.</p></div><a class="btn primary" href="/practice/?mode=topic">Choose topic</a></article><article class="ux-path"><div class="ux-path-icon">B</div><div><h2>Quick drill</h2><p>Ten unseen segments for fast English ⇄ Cantonese retrieval.</p></div><a class="btn" href="/practice/?mode=drill">Start drill</a></article></div></section>`,'practice');
  };

  window.renderInitialRoute=function(){
    const pageName=document.body.dataset.page||'home',params=new URLSearchParams(location.search);
    if(pageName==='mock'){renderMockPicker();return}
    if(pageName==='questions'){renderQuestions();return}
    if(pageName==='practice'){renderPracticeHub();return}
    if(pageName==='study'){if(params.get('view')==='vocabulary')renderVocabulary();else renderStudy(params.get('slug')||undefined);return}
    if(pageName==='progress'){renderHistory();return}
    renderDashboard();
  };

  // app.js starts booting before this file loads. Re-render the requested route as
  // soon as the shared data/audio engine is ready, making direct URLs refresh-safe.
  const bootRoute=()=>{if(state.summary&&state.audioEngine){renderInitialRoute();return}setTimeout(bootRoute,25)};
  setTimeout(bootRoute,0);
})();