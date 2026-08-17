/* Explicit all-questions study page. Loaded after simple-ui.js. */
(function(){
  const baseNav=nav;
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
      list.insertAdjacentHTML('beforeend',`<div class="mode-row" data-mode="questions" onclick="renderQuestions()"><div class="mode-num">05</div><div><strong>Practice questions</strong><span>See every dialogue and source segment, play the audio, and reveal model interpretations</span></div><div class="mode-arrow">›</div></div>`);
    }
  };

  window.renderQuestions=function(){
    stopAll();
    state.view='questions';
    $('#app').innerHTML=page(`<section class="simple-page questions-page">
      <div class="simple-page-head"><div><div class="eyebrow">Open practice bank</div><h1>All practice questions</h1><p>All 100 dialogues and every source segment are visible here. Play a segment, interpret it, then reveal the model answer.</p></div><button class="btn" onclick="renderPracticeSetup()">Hidden-script practice</button></div>
      <div class="question-summary"><strong>${state.dialogues.length}</strong> dialogues <span>·</span> <strong>${state.dialogues.reduce((n,d)=>n+d.segments.length,0)}</strong> source segments</div>
      <div class="questions-filterbar">
        <input id="qSearch" class="input" placeholder="Search question, topic, ABN, Medicare, tenancy…" oninput="filterQuestions()">
        <select id="qTopic" class="select" onchange="filterQuestions()"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select>
        <select id="qDir" class="select" onchange="filterQuestions()"><option value="All">Both directions</option><option value="en">English → Cantonese</option><option value="yue">Cantonese → English</option></select>
      </div>
      <div id="questionsList" class="questions-list"></div>
    </section>`,'questions');
    filterQuestions();
  };

  window.filterQuestions=function(){
    const q=($('#qSearch')?.value||'').trim().toLowerCase();
    const topic=$('#qTopic')?.value||'All';
    const dir=$('#qDir')?.value||'All';
    const list=$('#questionsList'); if(!list)return;
    const ds=state.dialogues.filter(d=>{
      if(topic!=='All' && d.topic!==topic)return false;
      const segs=d.segments.filter(s=>dir==='All'||s.source_lang===dir);
      if(!segs.length)return false;
      if(!q)return true;
      const hay=[d.id,d.title,d.topic,d.term,d.term_yue,...segs.flatMap(s=>[s.source,s.model,s.en,s.yue])].join(' ').toLowerCase();
      return hay.includes(q);
    });
    list.innerHTML=ds.length?ds.map(d=>questionDialogueHTML(d,dir,q)).join(''):`<div class="empty card">No questions match those filters.</div>`;
  };

  function questionDialogueHTML(d,dir,q){
    const segs=d.segments.filter(s=>dir==='All'||s.source_lang===dir).filter(s=>!q||[s.source,s.model,s.en,s.yue,d.title,d.term,d.term_yue].join(' ').toLowerCase().includes(q));
    if(!segs.length && q) return '';
    const shown=segs.length?segs:d.segments.filter(s=>dir==='All'||s.source_lang===dir);
    return `<details class="question-dialogue">
      <summary><div><span class="question-id">${d.id}</span><strong>${esc(d.title)}</strong><small>${esc(d.topic)} · ${d.difficulty} · ${shown.length} segments</small></div><span class="question-chevron">⌄</span></summary>
      <div class="question-segments">${shown.map(s=>questionSegmentHTML(d,s)).join('')}</div>
    </details>`;
  }

  function questionSegmentHTML(d,s){
    const key=`${d.id}-${s.n}`;
    return `<article class="question-segment" id="question-${key}">
      <div class="question-seg-meta"><span>S${String(s.n).padStart(2,'0')}</span><span>${s.source_lang==='en'?'English → Cantonese':'Cantonese → English'}</span></div>
      <div class="question-source">${esc(s.source)}</div>
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
      try{
        await speakFallback(seg,1,()=>{});
      }catch(_){
        button.textContent='Audio unavailable';
      }
    }finally{
      if(row)row.classList.remove('playing');
      button.disabled=false;
      if(button.textContent!=='Audio unavailable')button.textContent=old;
    }
  };
})();
