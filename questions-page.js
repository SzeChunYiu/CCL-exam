/* Explicit all-questions study page. Loaded after simple-ui.js. */
(function(){
  const player={running:false,token:0,timer:null,current:null};

  function pauseSeconds(){
    const n=Number($('#qPause')?.value||state.user?.prefs?.questionPause||7);
    return Math.max(5,Math.min(10,n));
  }
  function setQuestionPause(v){
    const n=Math.max(5,Math.min(10,Number(v)||7));
    state.user.prefs.questionPause=n;
    saveUser();
  }
  function setAutoStatus(text,active=false){
    const el=$('#qAutoStatus');
    if(el){el.textContent=text;el.classList.toggle('active',active)}
    const stop=$('#qStopAll');if(stop)stop.disabled=!player.running;
    const play=$('#qPlayAll');if(play)play.disabled=player.running;
  }
  function highlightQuestion(id,n){
    document.querySelectorAll('.question-segment.autoplaying').forEach(x=>x.classList.remove('autoplaying'));
    const row=document.getElementById(`question-${id}-${n}`);
    if(row){
      row.classList.add('autoplaying');
      row.scrollIntoView({behavior:'smooth',block:'center'});
      const details=row.closest('details');if(details)details.open=true;
    }
  }
  function stopQuestionAutoplay(message='Stopped'){
    player.running=false;
    player.token++;
    if(player.timer){clearTimeout(player.timer);player.timer=null}
    stopPlayback();
    document.querySelectorAll('.question-segment.autoplaying').forEach(x=>x.classList.remove('autoplaying'));
    setAutoStatus(message,false);
  }
  window.stopQuestionAutoplay=stopQuestionAutoplay;
  window.setQuestionPause=setQuestionPause;

  function sleep(ms,token){
    return new Promise(resolve=>{
      if(token!==player.token||!player.running)return resolve(false);
      player.timer=setTimeout(()=>{player.timer=null;resolve(token===player.token&&player.running)},ms);
    });
  }
  async function interpretingGap(seconds,token,label){
    for(let left=seconds;left>0;left--){
      if(token!==player.token||!player.running)return false;
      setAutoStatus(`${label} · interpret now · ${left}s`,true);
      const ok=await sleep(1000,token);if(!ok)return false;
    }
    return token===player.token&&player.running;
  }
  async function playSegmentRaw(d,seg,token){
    if(token!==player.token||!player.running)return false;
    highlightQuestion(d.id,seg.n);
    setAutoStatus(`${d.id} · S${String(seg.n).padStart(2,'0')} · playing ${seg.source_lang==='en'?'English officer':'Cantonese client'}`,true);
    try{
      await new Promise((resolve,reject)=>{
        let settled=false;
        const done=()=>{if(settled)return;settled=true;resolve()};
        Promise.resolve(state.audioEngine.play(d.id,seg.n-1,1,done)).catch(e=>{if(settled)return;settled=true;reject(e)});
      });
    }catch(e){
      try{await speakFallback(seg,1,()=>{})}
      catch(_){setAutoStatus(`${d.id} · S${seg.n} · audio unavailable`,true);return false}
    }
    return token===player.token&&player.running;
  }

  function currentFilters(){
    return {
      q:($('#qSearch')?.value||'').trim().toLowerCase(),
      topic:$('#qTopic')?.value||'All',
      dir:$('#qDir')?.value||'All'
    };
  }
  function visibleSegments(d,filters=currentFilters()){
    const segs=d.segments.filter(s=>filters.dir==='All'||s.source_lang===filters.dir);
    if(!filters.q)return segs;
    const dq=[d.id,d.title,d.topic,d.term,d.term_yue].join(' ').toLowerCase();
    if(dq.includes(filters.q))return segs;
    return segs.filter(s=>[s.source,s.model,s.en,s.yue].join(' ').toLowerCase().includes(filters.q));
  }
  function visibleDialogues(filters=currentFilters()){
    return state.dialogues.filter(d=>{
      if(filters.topic!=='All'&&d.topic!==filters.topic)return false;
      return visibleSegments(d,filters).length>0;
    });
  }

  async function runQueue(queue,label){
    stopQuestionAutoplay('Preparing…');
    player.running=true;
    const token=++player.token;
    const gap=pauseSeconds();
    setAutoStatus(`${label} · ${gap}s interpretation pause`,true);
    for(let i=0;i<queue.length;i++){
      if(token!==player.token||!player.running)return;
      const {d,seg}=queue[i];
      const ok=await playSegmentRaw(d,seg,token);if(!ok&&token===player.token&&player.running)continue;
      if(token!==player.token||!player.running)return;
      if(i<queue.length-1){
        const next=await interpretingGap(gap,token,`${d.id} · S${String(seg.n).padStart(2,'0')}`);
        if(!next)return;
      }
    }
    if(token===player.token){
      player.running=false;
      document.querySelectorAll('.question-segment.autoplaying').forEach(x=>x.classList.remove('autoplaying'));
      setAutoStatus(`${label} complete`,false);
    }
  }

  window.playQuestionDialogue=function(id,button){
    const d=state.byId[id];if(!d)return;
    const segs=visibleSegments(d);
    if(!segs.length)return;
    const queue=segs.map(seg=>({d,seg}));
    runQueue(queue,`${id} · ${d.title}`);
  };
  window.playAllVisibleQuestions=function(){
    const filters=currentFilters();
    const ds=visibleDialogues(filters);
    const queue=[];
    ds.forEach(d=>visibleSegments(d,filters).forEach(seg=>queue.push({d,seg})));
    if(!queue.length){setAutoStatus('No visible questions to play');return}
    runQueue(queue,`${ds.length} visible dialogue${ds.length===1?'':'s'}`);
  };

  nav=function(active='dashboard'){
    const items=[
      ['dashboard','Practice'],
      ['questions','Questions'],
      ['library','Library'],
      ['study','Study'],
      ['history','Results']
    ];
    return `<header class="topbar">
      <div class="brand" onclick="go('dashboard')" style="cursor:pointer"><div class="mark">CCL</div><div>CCL Practice</div></div>
      <nav class="nav">${items.map(([v,l])=>`<button class="${active===v?'active':''}" onclick="${v==='questions'?'renderQuestions()':`go('${v}')`}">${l}</button>`).join('')}</nav>
    </header>`;
  };

  const baseDashboard=renderDashboard;
  renderDashboard=function(){
    baseDashboard();
    const list=document.querySelector('.mode-list');
    if(list && !document.querySelector('[data-mode="questions"]')){
      list.insertAdjacentHTML('beforeend',`<div class="mode-row" data-mode="questions" onclick="renderQuestions()"><div class="mode-num">05</div><div><strong>Practice questions</strong><span>Open all dialogues, autoplay full conversations, and reveal model interpretations</span></div><div class="mode-arrow">›</div></div>`);
    }
  };

  window.renderQuestions=function(){
    stopAll();
    stopQuestionAutoplay('Ready');
    state.view='questions';
    const stored=Math.max(5,Math.min(10,Number(state.user?.prefs?.questionPause||7)));
    $('#app').innerHTML=page(`<section class="simple-page questions-page">
      <div class="simple-page-head"><div><div class="eyebrow">Open practice bank</div><h1>All practice questions</h1><p>Press one button for hands-free practice: source segment → beep → silent interpreting time → next segment.</p></div><button class="btn" onclick="renderPracticeSetup()">Hidden-script practice</button></div>
      <div class="question-autoplay-bar">
        <button id="qPlayAll" class="btn primary" onclick="playAllVisibleQuestions()">▶ Play all visible</button>
        <label>Interpretation pause
          <select id="qPause" class="select" onchange="setQuestionPause(this.value)">${[5,6,7,8,9,10].map(n=>`<option value="${n}" ${n===stored?'selected':''}>${n} seconds</option>`).join('')}</select>
        </label>
        <button id="qStopAll" class="btn" onclick="stopQuestionAutoplay()" disabled>■ Stop</button>
        <div id="qAutoStatus" class="question-auto-status">Ready</div>
      </div>
      <div class="question-summary"><strong>${state.dialogues.length}</strong> dialogues <span>·</span> <strong>${state.dialogues.reduce((n,d)=>n+d.segments.length,0)}</strong> source segments</div>
      <div class="questions-filterbar">
        <input id="qSearch" class="input" placeholder="Search question, topic, ABN, Medicare, tenancy…" oninput="filterQuestions()">
        <select id="qTopic" class="select" onchange="filterQuestions()"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select>
        <select id="qDir" class="select" onchange="filterQuestions()"><option value="All">Both directions</option><option value="en">English officer</option><option value="yue">Cantonese client</option></select>
      </div>
      <div id="questionsList" class="questions-list"></div>
    </section>`,'questions');
    filterQuestions();
  };

  window.filterQuestions=function(){
    if(player.running)stopQuestionAutoplay('Filters changed · ready');
    const filters=currentFilters();
    const list=$('#questionsList'); if(!list)return;
    const ds=visibleDialogues(filters);
    list.innerHTML=ds.length?ds.map(d=>questionDialogueHTML(d,filters)).join(''):`<div class="empty card">No questions match those filters.</div>`;
  };

  function questionDialogueHTML(d,filters){
    const shown=visibleSegments(d,filters);
    return `<details class="question-dialogue">
      <summary><div><span class="question-id">${d.id}</span><strong>${esc(d.title)}</strong><small>${esc(d.topic)} · ${d.difficulty} · ${shown.length} segments</small></div><span class="question-chevron">⌄</span></summary>
      <div class="dialogue-autoplay"><button class="btn primary" onclick="playQuestionDialogue('${d.id}',this)">▶ Play full dialogue</button><span>Uses the ${pauseSeconds()}s interpretation pause selected above.</span></div>
      <div class="question-segments">${shown.map(s=>questionSegmentHTML(d,s)).join('')}</div>
    </details>`;
  }

  function questionSegmentHTML(d,s){
    const key=`${d.id}-${s.n}`;
    return `<article class="question-segment" id="question-${key}">
      <div class="question-seg-meta"><span>S${String(s.n).padStart(2,'0')}</span><span>${s.source_lang==='en'?'English officer → Cantonese':'Cantonese client → English'}</span></div>
      <div class="question-source" data-lang="${s.source_lang}" lang="${s.source_lang==='yue'?'zh-HK':'en-AU'}">${esc(s.source)}</div>
      <div class="question-actions">
        <button class="btn primary question-play" onclick="playVisibleQuestion('${d.id}',${s.n},this)">▶ Play</button>
        <button class="btn" onclick="toggleQuestionAnswer('${key}',this)">Reveal answer</button>
      </div>
      <div class="question-answer" id="answer-${key}" hidden><div class="kicker">Model interpretation</div><div>${esc(s.model)}</div></div>
    </article>`;
  }

  window.toggleQuestionAnswer=function(key,button){
    const el=document.getElementById(`answer-${key}`); if(!el)return;
    el.hidden=!el.hidden;
    button.textContent=el.hidden?'Reveal answer':'Hide answer';
  };

  window.playVisibleQuestion=async function(id,n,button){
    stopQuestionAutoplay('Ready');
    const d=state.byId[id],seg=d?.segments?.[n-1]; if(!d||!seg)return;
    stopPlayback();
    document.querySelectorAll('.question-segment.playing').forEach(x=>x.classList.remove('playing'));
    const row=document.getElementById(`question-${id}-${n}`);
    if(row)row.classList.add('playing');
    const old=button.textContent; button.disabled=true; button.textContent='Playing…';
    try{
      await new Promise((resolve,reject)=>{
        let settled=false;
        const done=()=>{if(settled)return;settled=true;resolve()};
        Promise.resolve(state.audioEngine.play(id,n-1,1,done)).catch(e=>{if(settled)return;settled=true;reject(e)});
      });
    }catch(e){
      try{await speakFallback(seg,1,()=>{})}
      catch(_){button.textContent='Audio unavailable'}
    }finally{
      if(row)row.classList.remove('playing');
      button.disabled=false;
      if(button.textContent!=='Audio unavailable')button.textContent=old;
    }
  };
})();
