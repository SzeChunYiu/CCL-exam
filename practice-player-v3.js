/* Question Bank player v3 — persistent, queue-based, keyboard/media-key friendly. */
(function(){
  const player={
    running:false,paused:false,token:0,queue:[],di:0,si:0,
    current:null,abortSegment:null,abortGap:null,shuffle:false,scope:'all'
  };

  const byId=id=>document.getElementById(id);
  const clampPause=n=>Math.max(5,Math.min(10,Number(n)||7));
  const pauseSeconds=()=>clampPause(byId('qPause')?.value||state.user?.prefs?.questionPause||7);
  const isTypingTarget=t=>!!t?.closest?.('input,textarea,select,[contenteditable="true"]');

  function savePause(v){
    state.user.prefs.questionPause=clampPause(v);saveUser();updatePlayerUI();
  }
  window.setQuestionPause=savePause;

  function filters(){
    return {q:(byId('qSearch')?.value||'').trim().toLowerCase(),topic:byId('qTopic')?.value||'All',dir:byId('qDir')?.value||'All'};
  }
  function segmentsFor(d,f=filters()){
    let segs=d.segments.filter(s=>f.dir==='All'||s.source_lang===f.dir);
    if(!f.q)return segs;
    const dialogueText=[d.id,d.title,d.topic,d.term,d.term_yue].join(' ').toLowerCase();
    if(dialogueText.includes(f.q))return segs;
    return segs.filter(s=>[s.source,s.model,s.en,s.yue].join(' ').toLowerCase().includes(f.q));
  }
  function dialoguesFor(f=filters()){
    return state.dialogues.filter(d=>(f.topic==='All'||d.topic===f.topic)&&segmentsFor(d,f).length);
  }
  function shuffled(a){
    a=[...a];for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a;
  }
  function queueFromVisible(startId=null,single=false){
    const f=filters();let ds=dialoguesFor(f);
    if(player.shuffle)ds=shuffled(ds);
    if(single&&startId){const d=state.byId[startId];return d?[{d,segs:segmentsFor(d,f)}]:[]}
    const q=ds.map(d=>({d,segs:segmentsFor(d,f)}));
    if(startId){const i=q.findIndex(x=>x.d.id===startId);if(i>0){const [hit]=q.splice(i,1);q.unshift(hit)}}
    return q;
  }

  function currentEntry(){return player.queue[player.di]||null}
  function currentSeg(){const e=currentEntry();return e?.segs?.[player.si]||null}

  function clearHighlights(){
    document.querySelectorAll('.question-dialogue.active-dialogue').forEach(x=>x.classList.remove('active-dialogue'));
    document.querySelectorAll('.question-segment.autoplaying,.question-segment.playing').forEach(x=>x.classList.remove('autoplaying','playing'));
  }
  function highlight(d,seg){
    clearHighlights();
    const dialogue=document.querySelector(`[data-dialogue-id="${d.id}"]`);
    if(dialogue){
      dialogue.classList.add('active-dialogue');
      if(player.current?.dialogueId!==d.id) dialogue.scrollIntoView({behavior:'smooth',block:'center'});
    }
    const row=byId(`question-${d.id}-${seg.n}`);if(row)row.classList.add('autoplaying');
    player.current={dialogueId:d.id,segmentNo:seg.n};
  }

  function statusText(){
    const e=currentEntry(),seg=currentSeg();
    if(!e||!seg)return 'Choose a dialogue or play all visible questions.';
    if(player.paused)return `Paused · ${e.d.id} · S${String(seg.n).padStart(2,'0')}`;
    return `${e.d.id} · S${String(seg.n).padStart(2,'0')} · ${seg.source_lang==='en'?'English officer':'Cantonese client'}`;
  }
  function updateMediaSession(){
    if(!('mediaSession' in navigator))return;
    const e=currentEntry(),seg=currentSeg();
    try{
      navigator.mediaSession.playbackState=player.running?(player.paused?'paused':'playing'):'none';
      if(e&&seg&&'MediaMetadata' in window){navigator.mediaSession.metadata=new MediaMetadata({title:e.d.title,artist:`${e.d.id} · Segment ${seg.n}/${e.segs.length}`,album:'CCL Question Bank'})}
    }catch{}
  }
  function updatePlayerUI(message=null){
    const e=currentEntry(),seg=currentSeg();
    const title=byId('qNowTitle'),sub=byId('qNowSub'),progress=byId('qQueueProgress'),play=byId('qPlayPause'),shuffle=byId('qShuffle'),stop=byId('qStopPlayer');
    if(title)title.textContent=e?`${e.d.id} · ${e.d.title}`:'Question Bank player';
    if(sub)sub.textContent=message||statusText();
    if(progress)progress.textContent=e&&seg?`Question ${player.di+1}/${player.queue.length} · Segment ${player.si+1}/${e.segs.length} · ${pauseSeconds()}s pause`:`${pauseSeconds()}s interpretation pause`;
    if(play){play.textContent=player.running&&!player.paused?'❚❚':'▶';play.setAttribute('aria-label',player.running&&!player.paused?'Pause':'Play')}
    if(shuffle){shuffle.classList.toggle('active',player.shuffle);shuffle.setAttribute('aria-pressed',String(player.shuffle))}
    if(stop)stop.disabled=!player.running;
    updateMediaSession();
  }

  function abortCurrent(reason='abort'){
    stopPlayback();
    try{player.abortSegment?.(reason)}catch{}
    try{player.abortGap?.(reason)}catch{}
    player.abortSegment=null;player.abortGap=null;
  }

  function stopPlayer(message='Stopped'){
    player.running=false;player.paused=false;player.token++;abortCurrent('stop');clearHighlights();updatePlayerUI(message);
  }
  window.stopQuestionAutoplay=stopPlayer;

  function setPaused(paused){
    if(!player.running)return;
    player.paused=paused;
    const a=state.audioEngine?.audio;
    try{
      if(paused){a?.pause();if('speechSynthesis'in window)speechSynthesis.pause()}
      else {if(a?.src&&a.paused)a.play().catch(()=>{});if('speechSynthesis'in window)speechSynthesis.resume()}
    }catch{}
    updatePlayerUI();
  }
  window.toggleQuestionPlayer=function(){
    if(!player.running){playAllVisibleQuestions();return}
    setPaused(!player.paused);
  };

  async function waitUntilResumed(token){
    while(player.running&&token===player.token&&player.paused){await new Promise(r=>setTimeout(r,100))}
    return player.running&&token===player.token;
  }
  async function interpretationGap(seconds,token){
    let remaining=seconds*1000,last=performance.now();
    return await new Promise(resolve=>{
      let finished=false;
      const finish=value=>{if(finished)return;finished=true;player.abortGap=null;resolve(value)};
      player.abortGap=()=>finish(false);
      const tick=()=>{
        if(finished)return;
        if(!player.running||token!==player.token){finish(false);return}
        const now=performance.now();
        if(!player.paused)remaining-=now-last;
        last=now;
        const sec=Math.max(0,Math.ceil(remaining/1000));
        updatePlayerUI(player.paused?`Paused · interpretation time ${sec}s`:`Interpret now · ${sec}s`);
        if(remaining<=0){finish(true);return}
        setTimeout(tick,100);
      };
      tick();
    });
  }

  async function playSegment(d,seg,token){
    if(!await waitUntilResumed(token))return false;
    highlight(d,seg);updatePlayerUI();
    return await new Promise(resolve=>{
      let settled=false;
      const finish=value=>{if(settled)return;settled=true;player.abortSegment=null;resolve(value)};
      player.abortSegment=()=>finish(false);
      const done=()=>finish(true);
      try{
        Promise.resolve(state.audioEngine.play(d.id,seg.n-1,1,done)).catch(async()=>{
          if(settled)return;
          try{await speakFallback(seg,1,done)}catch{finish(false)}
        });
      }catch{finish(false)}
    });
  }

  async function runQueue(){
    const token=++player.token;player.running=true;player.paused=false;updatePlayerUI();
    while(player.running&&token===player.token&&player.di<player.queue.length){
      const entry=currentEntry();
      if(!entry||!entry.segs.length){player.di++;player.si=0;continue}
      while(player.running&&token===player.token&&player.si<entry.segs.length){
        const seg=currentSeg();
        const played=await playSegment(entry.d,seg,token);
        if(!played||!player.running||token!==player.token)return;
        const isLastSegment=player.si===entry.segs.length-1;
        const isLastDialogue=player.di===player.queue.length-1;
        if(!(isLastSegment&&isLastDialogue)){
          const gap=await interpretationGap(pauseSeconds(),token);if(!gap)return;
        }
        player.si++;
      }
      player.di++;player.si=0;
    }
    if(player.running&&token===player.token){player.running=false;player.paused=false;clearHighlights();updatePlayerUI('Queue complete')}
  }

  function startQueue(queue,di=0){
    stopPlayer('Loading…');
    player.queue=queue;player.di=Math.max(0,Math.min(di,Math.max(0,queue.length-1)));player.si=0;
    if(!queue.length){updatePlayerUI('No questions match the current filters.');return}
    runQueue();
  }

  window.playAllVisibleQuestions=function(){startQueue(queueFromVisible())};
  window.playQuestionDialogue=function(id){
    const q=queueFromVisible(null,false);const i=q.findIndex(x=>x.d.id===id);startQueue(q,i<0?0:i);
  };
  window.previousQuestion=function(){
    const visible=queueFromVisible();if(!visible.length)return;
    const id=currentEntry()?.d?.id;let i=visible.findIndex(x=>x.d.id===id);if(i<0)i=0;else i=(i-1+visible.length)%visible.length;startQueue(visible,i);
  };
  window.nextQuestion=function(){
    const visible=queueFromVisible();if(!visible.length)return;
    const id=currentEntry()?.d?.id;let i=visible.findIndex(x=>x.d.id===id);i=i<0?0:(i+1)%visible.length;startQueue(visible,i);
  };
  window.toggleQuestionShuffle=function(){
    player.shuffle=!player.shuffle;state.user.prefs.questionShuffle=player.shuffle;saveUser();
    if(player.running){
      const currentId=currentEntry()?.d?.id;
      let q=queueFromVisible();const i=q.findIndex(x=>x.d.id===currentId);
      if(i>0){const [hit]=q.splice(i,1);q.unshift(hit)}
      player.queue=q;player.di=0;
    }
    updatePlayerUI(player.shuffle?'Shuffle on':'Shuffle off');
  };

  window.filterQuestions=function(){
    if(player.running)stopPlayer('Filters changed');
    renderQuestionList();
  };
  window.toggleQuestionAnswer=function(key,button){
    const el=byId(`answer-${key}`);if(!el)return;el.hidden=!el.hidden;button.textContent=el.hidden?'Reveal answer':'Hide answer';
  };
  window.playVisibleQuestion=function(id,n,button){
    const d=state.byId[id],seg=d?.segments?.[n-1];if(!d||!seg)return;
    stopPlayer('Ready');clearHighlights();
    const row=byId(`question-${id}-${n}`);if(row)row.classList.add('playing');
    const old=button.textContent;button.disabled=true;button.textContent='Playing…';
    let done=false;
    const finish=()=>{if(done)return;done=true;if(row)row.classList.remove('playing');button.disabled=false;button.textContent=old};
    Promise.resolve(state.audioEngine.play(id,n-1,1,finish)).catch(async()=>{try{await speakFallback(seg,1,finish)}catch{button.textContent='Audio unavailable';button.disabled=false}});
  };

  function segmentHTML(d,s){
    const key=`${d.id}-${s.n}`;
    return `<article class="question-segment" id="question-${key}">
      <div class="question-seg-meta"><span>S${String(s.n).padStart(2,'0')}</span><span>${s.source_lang==='en'?'English officer → Cantonese':'Cantonese client → English'}</span></div>
      <div class="question-source">${esc(s.source)}</div>
      <div class="question-actions"><button class="btn primary question-play" onclick="playVisibleQuestion('${d.id}',${s.n},this)">▶ Play segment</button><button class="btn" onclick="toggleQuestionAnswer('${key}',this)">Reveal answer</button></div>
      <div class="question-answer" id="answer-${key}" hidden><div class="kicker">Model interpretation</div><div>${esc(s.model)}</div></div>
    </article>`;
  }
  function dialogueHTML(d,f){
    const segs=segmentsFor(d,f);
    return `<details class="question-dialogue" data-dialogue-id="${d.id}">
      <summary><div><span class="question-id">${d.id}</span><strong>${esc(d.title)}</strong><small>${esc(d.topic)} · ${d.difficulty} · ${segs.length} segments</small></div><span class="question-chevron">⌄</span></summary>
      <div class="dialogue-autoplay"><button class="btn primary" onclick="playQuestionDialogue('${d.id}')">▶ Play from this question</button><span>Then use previous/next in the player to move between questions.</span></div>
      <div class="question-segments">${segs.map(s=>segmentHTML(d,s)).join('')}</div>
    </details>`;
  }
  function renderQuestionList(){
    const f=filters(),ds=dialoguesFor(f),list=byId('questionsList');if(!list)return;
    list.innerHTML=ds.length?ds.map(d=>dialogueHTML(d,f)).join(''):`<div class="empty card">No questions match those filters.</div>`;
  }

  window.renderQuestions=function(){
    stopPlayer('Ready');state.view='questions';player.shuffle=!!state.user?.prefs?.questionShuffle;
    const stored=clampPause(state.user?.prefs?.questionPause||7);
    document.body.classList.add('has-question-player');
    $('#app').innerHTML=page(`<section class="simple-page questions-page player-v3-page">
      <div class="simple-page-head"><div><div class="eyebrow">Open practice bank</div><h1>Question bank</h1><p>Choose a filter, press Play all, and practise hands-free. Each question stays highlighted even when collapsed.</p></div><a class="btn" href="/practice/">Focused practice</a></div>
      <div class="question-toolbar-v3" role="region" aria-label="Question bank controls">
        <button class="btn primary" onclick="playAllVisibleQuestions()">▶ Play all visible</button>
        <label>Interpretation pause <select id="qPause" class="select" onchange="setQuestionPause(this.value)">${[5,6,7,8,9,10].map(n=>`<option value="${n}" ${n===stored?'selected':''}>${n}s</option>`).join('')}</select></label>
        <span class="question-hint">Keyboard: Space play/pause · ←/→ previous/next · S shuffle · Esc stop</span>
      </div>
      <div class="question-summary"><strong>${state.dialogues.length}</strong> dialogues <span>·</span> <strong>${state.dialogues.reduce((n,d)=>n+d.segments.length,0)}</strong> source segments</div>
      <div class="questions-filterbar" role="search"><input id="qSearch" class="input" placeholder="Search topic, ABN, Medicare, tenancy…" oninput="filterQuestions()"><select id="qTopic" class="select" onchange="filterQuestions()"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select><select id="qDir" class="select" onchange="filterQuestions()"><option value="All">Both speakers</option><option value="en">English officer</option><option value="yue">Cantonese client</option></select></div>
      <div id="questionsList" class="questions-list" aria-label="Practice questions"></div>
    </section>
    <section class="question-player-v3" aria-label="Practice player">
      <div class="q-player-now"><span class="q-player-kicker">NOW PRACTISING</span><strong id="qNowTitle">Question Bank player</strong><span id="qNowSub" role="status" aria-live="polite">Choose a dialogue or play all visible questions.</span></div>
      <div class="q-player-controls">
        <button id="qShuffle" class="q-player-icon" onclick="toggleQuestionShuffle()" aria-label="Shuffle questions" aria-pressed="false">⤨</button>
        <button class="q-player-icon" onclick="previousQuestion()" aria-label="Previous question">⏮</button>
        <button id="qPlayPause" class="q-player-main" onclick="toggleQuestionPlayer()" aria-label="Play">▶</button>
        <button class="q-player-icon" onclick="nextQuestion()" aria-label="Next question">⏭</button>
        <button id="qStopPlayer" class="q-player-icon" onclick="stopQuestionAutoplay()" aria-label="Stop" disabled>■</button>
      </div>
      <div class="q-player-meta"><span id="qQueueProgress">${stored}s interpretation pause</span><a href="/mock/">Mock mode</a></div>
    </section>`,'questions');
    renderQuestionList();updatePlayerUI();initMediaHandlers();
  };

  let handlersReady=false;
  function initMediaHandlers(){
    if(handlersReady||!('mediaSession' in navigator))return;handlersReady=true;
    for(const [action,fn] of [['play',()=>setPaused(false)],['pause',()=>setPaused(true)],['previoustrack',previousQuestion],['nexttrack',nextQuestion],['stop',()=>stopPlayer('Stopped')]]){
      try{navigator.mediaSession.setActionHandler(action,fn)}catch{}
    }
  }

  document.addEventListener('keydown',e=>{
    if(document.body.dataset.page!=='questions'||isTypingTarget(e.target))return;
    if(e.code==='Space'){e.preventDefault();toggleQuestionPlayer()}
    else if(e.key==='ArrowLeft'){e.preventDefault();previousQuestion()}
    else if(e.key==='ArrowRight'){e.preventDefault();nextQuestion()}
    else if(e.key.toLowerCase()==='s'){e.preventDefault();toggleQuestionShuffle()}
    else if(e.key==='Escape'){e.preventDefault();stopPlayer('Stopped')}
  });
})();