/* Practice Studio v5 — deliberate, repeatable CCL training loops. */
(function(){
  const legacyRenderPerformance=renderPerformance;

  function prefs(){
    state.user.prefs=state.user.prefs||{};
    const p=state.user.prefs;
    if(!Number.isFinite(Number(p.practiceRate)))p.practiceRate=1;
    if(!Number.isFinite(Number(p.practiceTimer)))p.practiceTimer=7;
    if(typeof p.practiceAutoPlay!=='boolean')p.practiceAutoPlay=false;
    if(typeof p.practiceAutoAdvance!=='boolean')p.practiceAutoAdvance=false;
    if(!p.practiceLastSetup)p.practiceLastSetup={topic:'All',difficulty:'All',start:'beginning'};
    return p;
  }
  const currentKey=()=>{const {d,seg}=currentPractice();return sessionKey(d.id,seg.n)};
  const isFavV5=id=>state.user.favorites.includes(id);
  const weakCount=()=>state.user.weak.length;
  const rateLabel=r=>({strong:'Strong',minor:'Minor issue',needs:'Needs work'}[r]||'Not rated');

  function savePrefs(){saveUser()}
  function setResume(d,si){prefs().practiceResume={id:d.id,si,updatedAt:Date.now()};saveUser()}
  function clearResume(){delete prefs().practiceResume;saveUser()}
  function validResume(){const r=prefs().practiceResume;return r&&state.byId[r.id]&&Number.isInteger(r.si)&&r.si>=0&&r.si<state.byId[r.id].segments.length?r:null}

  function practiceStatus(message,tone=''){
    const el=document.getElementById('practiceSetupStatus');if(!el)return;
    el.textContent=message;el.dataset.tone=tone;
  }

  window.setPracticeDefaultV5=function(name,value){
    const p=prefs();
    if(name==='practiceRate')p.practiceRate=Number(value)||1;
    else if(name==='practiceTimer')p.practiceTimer=Math.max(0,Math.min(10,Number(value)||0));
    else if(name==='practiceAutoPlay'||name==='practiceAutoAdvance')p[name]=!!value;
    savePrefs();
    if(state.session?.mode==='practice')renderPractice();
  };

  window.renderPracticeHub=function(){
    state.view='practiceHub';
    const resume=validResume(),weak=weakCount(),last=(state.user.history||[]).filter(x=>x.mode==='practice'||x.mode==='drill').sort((a,b)=>b.date-a.date)[0];
    $('#app').innerHTML=page(`<section class="ps-page ps-hub">
      <header class="ps-hero"><div><div class="eyebrow">Focused practice</div><h1>Practice studio</h1><p>Keep the loop short: listen, interpret, compare, rate, move on. Use a full dialogue for context or a drill when you need repetition.</p></div>${resume?`<button class="btn primary ps-resume" onclick="resumePracticeV5()"><span>Resume</span><strong>${resume.id} · segment ${resume.si+1}</strong></button>`:''}</header>
      <div class="ps-mode-grid">
        <a class="ps-mode-card primary" href="/practice/?mode=topic"><span class="ps-mode-icon">D</span><div><strong>Guided dialogue</strong><p>Work through one complete immigrant-life scenario, one turn at a time.</p><small>Best for context + meaning transfer</small></div><span>Start →</span></a>
        <button class="ps-mode-card" onclick="startWeakReviewV5()" ${weak?'':'disabled'}><span class="ps-mode-icon">W</span><div><strong>Weak review</strong><p>${weak?`${weak} flagged segment${weak===1?'':'s'} ready for targeted repetition.`:'Flag difficult segments during practice and they will appear here.'}</p><small>Prioritises what needs work</small></div><span>${weak?'Review →':'Nothing flagged'}</span></button>
        <a class="ps-mode-card" href="/practice/?mode=drill"><span class="ps-mode-icon">10</span><div><strong>Quick drill</strong><p>Mix short unseen segments by topic and speaker direction.</p><small>Best for speed + retrieval</small></div><span>Configure →</span></a>
        <a class="ps-mode-card" href="/questions/"><span class="ps-mode-icon">▶</span><div><strong>Hands-free player</strong><p>Run whole dialogues automatically with adjustable interpreting pauses.</p><small>Best for uninterrupted reps</small></div><span>Open →</span></a>
      </div>
      <section class="ps-defaults" aria-label="Practice defaults"><div><strong>Your defaults</strong><span>Saved on this device</span></div>${practiceDefaultsHTML()}</section>
      ${last?`<a class="ps-last" href="/progress/"><span><strong>Latest focused session</strong><small>${new Date(last.date).toLocaleDateString()} · ${labelMode(last.mode)}${Number.isFinite(last.score)?` · ${last.score}%`:''}</small></span><span>Review progress →</span></a>`:''}
    </section>`);
  };

  function practiceDefaultsHTML(){
    const p=prefs();
    return `<label>Speed<select class="select" onchange="setPracticeDefaultV5('practiceRate',this.value)">${[[.9,'0.9×'],[1,'1.0×'],[1.05,'1.05×'],[1.1,'1.10×'],[1.15,'1.15×']].map(([v,l])=>`<option value="${v}" ${Number(p.practiceRate)===v?'selected':''}>${l}</option>`).join('')}</select></label><label>Interpret timer<select class="select" onchange="setPracticeDefaultV5('practiceTimer',this.value)">${[[0,'Off'],[5,'5 sec'],[7,'7 sec'],[10,'10 sec']].map(([v,l])=>`<option value="${v}" ${Number(p.practiceTimer)===v?'selected':''}>${l}</option>`).join('')}</select></label><label class="ps-switch"><input type="checkbox" ${p.practiceAutoPlay?'checked':''} onchange="setPracticeDefaultV5('practiceAutoPlay',this.checked)"><span>Auto-play next</span></label><label class="ps-switch"><input type="checkbox" ${p.practiceAutoAdvance?'checked':''} onchange="setPracticeDefaultV5('practiceAutoAdvance',this.checked)"><span>Advance after rating</span></label>`;
  }

  window.resumePracticeV5=function(){const r=validResume();if(r)startPractice(r.id,r.si)};

  renderPracticeSetup=function(){
    state.view='practiceSetup';const p=prefs(),last=p.practiceLastSetup||{},t=last.topic||'All',diff=last.difficulty||'All',start=last.start||'beginning';
    $('#app').innerHTML=page(`<section class="ps-page ps-setup"><a class="v4-back" href="/practice/">← Practice studio</a><header class="ps-setup-head"><div><div class="eyebrow">Guided dialogue</div><h1>Choose the kind of dialogue you need.</h1><p>Whole-dialogue practice preserves the conversation context. The source stays hidden until you reveal it.</p></div><div class="ps-setup-count"><strong id="practiceMatchCount">—</strong><span>matching dialogues</span></div></header>
      <div class="ps-setup-grid"><section class="ps-panel"><h2>Dialogue</h2><label><span>Topic</span><select id="pTopic" class="select" onchange="updatePracticeMatchV5()"><option value="All">All topics</option>${topics().map(x=>`<option ${x===t?'selected':''}>${esc(x)}</option>`).join('')}</select></label><label><span>Difficulty</span><select id="pDiff" class="select" onchange="updatePracticeMatchV5()"><option value="All">All levels</option>${['Easy','Medium','Hard'].map(x=>`<option ${x===diff?'selected':''}>${x}</option>`).join('')}</select></label><label><span>Start position</span><select id="pStart" class="select"><option value="beginning" ${start==='beginning'?'selected':''}>From the beginning</option><option value="random" ${start==='random'?'selected':''}>Random segment</option></select></label><div id="practiceSetupStatus" class="ps-status" role="status" aria-live="polite"></div><button class="btn primary ps-wide" onclick="startGuidedPracticeV5()">Start guided dialogue</button><button class="btn ps-wide" onclick="surprisePracticeV5()">Surprise me</button></section>
      <section class="ps-panel"><h2>Session defaults</h2>${practiceDefaultsHTML()}<div class="ps-tip"><strong>Recommended</strong><p>Use 1.0× and a 7-second timer for normal practice. Turn on auto-play only when you want a faster rhythm.</p></div><div class="ps-shortcuts"><strong>Keyboard in a session</strong><span><kbd>Space</kbd> play/replay</span><span><kbd>←</kbd>/<kbd>→</kbd> previous/next</span><span><kbd>Enter</kbd> reveal/next</span><span><kbd>1</kbd>/<kbd>2</kbd>/<kbd>3</kbd> self-rate</span><span><kbd>W</kbd> flag weak</span></div></section></div>
    </section>`);updatePracticeMatchV5();
  };

  window.updatePracticeMatchV5=function(){
    const t=document.getElementById('pTopic')?.value||'All',d=document.getElementById('pDiff')?.value||'All';
    const n=state.dialogues.filter(x=>(t==='All'||x.topic===t)&&(d==='All'||x.difficulty===d)).length;
    const el=document.getElementById('practiceMatchCount');if(el)el.textContent=n;
    practiceStatus(n?'Ready to start.':'No dialogues match those filters.',n?'':'warn');
  };

  window.startGuidedPracticeV5=function(){
    const t=document.getElementById('pTopic')?.value||'All',d=document.getElementById('pDiff')?.value||'All',start=document.getElementById('pStart')?.value||'beginning';
    const pool=state.dialogues.filter(x=>(t==='All'||x.topic===t)&&(d==='All'||x.difficulty===d));
    if(!pool.length){practiceStatus('No dialogues match those filters. Try a broader topic or level.','warn');return}
    prefs().practiceLastSetup={topic:t,difficulty:d,start};savePrefs();
    const chosen=pool[Math.floor(Math.random()*pool.length)],si=start==='random'?Math.floor(Math.random()*chosen.segments.length):0;startPractice(chosen.id,si);
  };
  window.surprisePracticeV5=function(){
    const d=state.dialogues[Math.floor(Math.random()*state.dialogues.length)];if(d)startPractice(d.id,0);
  };

  startPractice=function(id,si=0){
    if(document.body.dataset.page!=='practice'){location.href=`/practice/?dialogue=${encodeURIComponent(id)}&si=${Math.max(0,Number(si)||0)}`;return}
    const d=state.byId[id];if(!d)return;
    stopAll();state.recordings={};
    state.session={id:uid(),mode:'practice',dialogueIds:[id],di:0,si:Math.max(0,Math.min(si,d.segments.length-1)),notes:{},marks:{},revealed:{},played:{},startedAt:Date.now(),endedAt:null,practiceTimerInterval:null};
    state.view='practice';setResume(d,state.session.si);renderPractice();
    if(prefs().practiceAutoPlay)setTimeout(()=>playPracticeSource(),100);
  };

  function segmentStepper(d,s){
    return `<div class="ps-stepper" aria-label="Dialogue segments">${d.segments.map((x,i)=>{const k=sessionKey(d.id,x.n),mark=s.marks[k]?.rating,cls=i===s.si?'current':mark?'rated '+mark:isWeak(d.id,x.n)?'weak':'';return `<button class="${cls}" onclick="jumpPracticeV5(${i})" aria-label="Segment ${i+1}${mark?`, ${rateLabel(mark)}`:''}" ${i===s.si?'aria-current="step"':''}>${i+1}</button>`}).join('')}</div>`;
  }

  function practiceMeta(d,seg){
    return `<div class="ps-meta"><span class="ps-speaker ${seg.source_lang==='en'?'officer':'client'}">${seg.source_lang==='en'?'Officer · English':'Client · Cantonese'}</span><span>${seg.source_lang==='en'?'Interpret into Cantonese':'Interpret into English'}</span><span>${esc(d.topic)} · ${d.difficulty}</span></div>`;
  }

  renderPractice=function(){
    const s=state.session;if(!s||s.mode!=='practice')return;
    const {d,seg}=currentPractice(),k=sessionKey(d.id,seg.n),revealed=!!s.revealed[k],m=s.marks[k]||{rating:null,tags:[]},p=prefs(),played=s.played[k]||0;
    setResume(d,s.si);
    $('#app').innerHTML=page(`<section class="ps-session"><header class="ps-session-head"><div><a class="v4-back" href="/practice/">← Practice studio</a><div class="eyebrow">${d.id} · guided dialogue</div><h1>${esc(d.title)}</h1>${practiceMeta(d,seg)}</div><div class="ps-session-progress"><strong>${seg.n}/${d.segments.length}</strong><span>${Math.round(seg.n/d.segments.length*100)}% through dialogue</span></div></header>${segmentStepper(d,s)}
      <div class="ps-session-layout"><main class="ps-focus-card"><div class="ps-focus-top"><div><span class="kicker">Source segment ${seg.n}</span><strong>${revealed?'Compare your interpretation':'Listen without reading'}</strong></div><div class="ps-quick-flags"><button class="ps-icon-btn ${isWeak(d.id,seg.n)?'on':''}" onclick="togglePracticeWeakV5()" aria-pressed="${isWeak(d.id,seg.n)}" title="Flag as weak">⚑</button><button class="ps-icon-btn ${isFavV5(d.id)?'on':''}" onclick="togglePracticeFavoriteV5()" aria-pressed="${isFavV5(d.id)}" title="Favourite dialogue">★</button></div></div>
        <div class="ps-audio-zone"><div id="audioStatus" class="ps-audio-status" role="status" aria-live="polite">${played?`Played ${played} time${played===1?'':'s'}. Replay when ready.`:'Press play and listen for the chime.'}</div><div id="practiceTimerLive" class="ps-timer-live">${p.practiceTimer?`${p.practiceTimer}s interpretation timer`:'Timer off'}</div><button id="practicePlayBtn" class="ps-play-big" onclick="playPracticeSource()" aria-label="${played?'Replay':'Play'} source segment">${played?'↻':'▶'}<span>${played?'Replay':'Play source'}</span></button></div>
        ${revealed?`<div class="ps-compare"><section><span class="kicker">Source</span><p>${esc(seg.source)}</p></section><section><span class="kicker">Model interpretation</span><p>${esc(seg.model)}</p></section></div>${assessmentHTML(m,k,'practice')}`:`<div class="ps-reveal"><p>Interpret first. Reveal only when you have finished speaking.</p><button class="btn secondary ps-wide" onclick="revealPractice()">Reveal source + model</button></div>`}
        <div class="ps-nav-row"><button class="btn" onclick="previousPracticeV5()" ${s.si===0?'disabled':''}>← Previous</button><span>${revealed?(m.rating?`Rated: ${rateLabel(m.rating)}`:'Rate this segment when useful'):'You can skip without revealing'}</span><button class="btn ${revealed?'primary':''}" onclick="nextPractice()">${s.si===d.segments.length-1?'Finish dialogue':revealed?'Next segment →':'Skip →'}</button></div>
      </main><aside class="ps-side"><section class="ps-side-card"><h2>Session</h2>${practiceDefaultsHTML()}</section><details class="ps-side-card"><summary>Record your interpretation</summary><div class="ps-details-body"><div id="recStatus" class="muted" aria-live="polite">Optional. Recording stays in this browser session.</div><div class="ps-stack-actions"><button id="recordBtn" class="btn" onclick="toggleRecord()">● Record</button><button class="btn" onclick="playMyRecording('${d.id}',${seg.n})" ${state.recordings[k]?'':'disabled'}>Listen to mine</button></div></div></details><details class="ps-side-card"><summary>Notes / shorthand</summary><div class="ps-details-body"><textarea class="notes" placeholder="Optional notes…" oninput="state.session.notes['${k}']=this.value">${esc(s.notes[k]||'')}</textarea></div></details><div class="ps-keyhint"><kbd>Space</kbd> play · <kbd>Enter</kbd> ${revealed?'next':'reveal'} · <kbd>W</kbd> weak</div></aside></div>
    </section>`);
  };

  function assessmentHTML(m,k,ctx){
    return `<section class="ps-assess"><div><span class="kicker">Meaning transfer</span><div class="ps-rating">${[['strong','Strong'],['minor','Minor issue'],['needs','Needs work']].map(([v,l],i)=>`<button class="${m.rating===v?'on '+v:''}" onclick="rateFocusedV5('${ctx}','${v}')"><span>${i+1}</span>${l}</button>`).join('')}</div></div><details ${m.tags?.length?'open':''}><summary>Tag specific issues${m.tags?.length?` · ${m.tags.length} selected`:''}</summary><div class="ps-tags">${ERROR_TAGS.map(t=>`<button class="${(m.tags||[]).includes(t)?'on':''}" onclick="tagFocusedV5('${ctx}','${esc(t)}')">${esc(t)}</button>`).join('')}</div></details></section>`;
  }

  window.rateFocusedV5=function(ctx,value){
    const s=state.session,{d,seg}=ctx==='practice'?currentPractice():currentDrill(),k=sessionKey(d.id,seg.n);s.marks[k]=s.marks[k]||{rating:null,tags:[]};s.marks[k].rating=value;toggleWeak(d.id,seg.n,value==='needs');
    if(ctx==='practice'){renderPractice();if(prefs().practiceAutoAdvance)setTimeout(()=>nextPractice(),500)}else{renderDrill();if(prefs().practiceAutoAdvance)setTimeout(()=>nextDrill(),500)}
  };
  window.tagFocusedV5=function(ctx,tag){
    const s=state.session,{d,seg}=ctx==='practice'?currentPractice():currentDrill(),k=sessionKey(d.id,seg.n);s.marks[k]=s.marks[k]||{rating:null,tags:[]};const a=s.marks[k].tags||[];s.marks[k].tags=a.includes(tag)?a.filter(x=>x!==tag):[...a,tag];ctx==='practice'?renderPractice():renderDrill();
  };

  window.togglePracticeWeakV5=function(){const {d,seg}=currentPractice();toggleWeak(d.id,seg.n,!isWeak(d.id,seg.n));renderPractice()};
  window.togglePracticeFavoriteV5=function(){const {d}=currentPractice();state.user.favorites=isFavV5(d.id)?state.user.favorites.filter(x=>x!==d.id):[...state.user.favorites,d.id];saveUser();renderPractice()};

  revealPractice=function(){const {d,seg}=currentPractice();state.session.revealed[sessionKey(d.id,seg.n)]=true;renderPractice()};

  function clearPracticeTimer(){if(state.session?.practiceTimerInterval){clearInterval(state.session.practiceTimerInterval);state.session.practiceTimerInterval=null}}
  function startInterpretTimerV5(){
    clearPracticeTimer();const seconds=Number(prefs().practiceTimer)||0,el=document.getElementById('practiceTimerLive');if(!el)return;
    if(!seconds){el.textContent='Interpret now · timer off';el.classList.add('active');return}
    let left=seconds;el.textContent=`Interpret now · ${left}s`;el.classList.add('active');
    state.session.practiceTimerInterval=setInterval(()=>{left--;const now=document.getElementById('practiceTimerLive');if(!now){clearPracticeTimer();return}now.textContent=left>0?`Interpret now · ${left}s`:'Keep interpreting';if(left<=0)clearPracticeTimer()},1000);
  }

  playPracticeSource=async function(){
    const {d,seg}=currentPractice(),k=sessionKey(d.id,seg.n);state.session.played=state.session.played||{};state.session.played[k]=(state.session.played[k]||0)+1;
    const btn=document.getElementById('practicePlayBtn');if(btn)btn.disabled=true;
    await playSource(d,seg,prefs().practiceRate||1,()=>{const el=document.getElementById('audioStatus');if(el)el.textContent='Chime finished. Interpret now.';if(btn)btn.disabled=false;startInterpretTimerV5()});
  };

  window.previousPracticeV5=async function(){
    const s=state.session;if(!s||s.mode!=='practice'||s.si<=0)return;stopPlayback();clearPracticeTimer();await stopRecordingIfNeeded();s.si--;renderPractice();
  };
  window.jumpPracticeV5=async function(i){
    const s=state.session,d=state.byId[s.dialogueIds[0]];if(!s||s.mode!=='practice'||i<0||i>=d.segments.length||i===s.si)return;stopPlayback();clearPracticeTimer();await stopRecordingIfNeeded();s.si=i;renderPractice();
  };

  nextPractice=async function(){
    stopPlayback();clearPracticeTimer();await stopRecordingIfNeeded();const s=state.session,{d}=currentPractice();
    if(s.si<d.segments.length-1){s.si++;renderPractice();if(prefs().practiceAutoPlay)setTimeout(()=>playPracticeSource(),120);return}
    markCompleted(d.id);clearResume();s.endedAt=Date.now();saveSessionToHistory(s);renderFocusedCompletionV5(s,'Dialogue complete');
  };

  function completionStats(s){
    const marks=Object.values(s.marks||{}),rated=marks.filter(x=>x.rating),needs=rated.filter(x=>x.rating==='needs').length,strong=rated.filter(x=>x.rating==='strong').length;
    return {rated:rated.length,strong,needs,score:sessionMetrics(s).score};
  }
  function renderFocusedCompletionV5(s,title){
    const st=completionStats(s),ids=s.dialogueIds||[...new Set((s.queue||[]).map(x=>x.did))],primary=ids[0];
    $('#app').innerHTML=page(`<section class="ps-page ps-complete"><div class="ps-complete-mark">✓</div><div class="eyebrow">Focused practice</div><h1>${title}</h1><p>You completed this practice session. Keep the next action small and specific.</p><div class="ps-complete-stats"><div><strong>${st.score==null?'—':st.score+'%'}</strong><span>self-rating</span></div><div><strong>${st.rated}</strong><span>segments rated</span></div><div><strong>${st.strong}</strong><span>strong</span></div><div><strong>${st.needs}</strong><span>needs work</span></div></div><div class="ps-complete-actions">${primary&&state.byId[primary]?`<button class="btn primary" onclick="startPractice('${primary}',0)">Repeat dialogue</button>`:''}<button class="btn" onclick="startWeakReviewV5()" ${weakCount()?'':'disabled'}>Review weak segments</button><button class="btn" onclick="openPracticeReviewV5()">Detailed review</button><a class="btn" href="/practice/">Practice studio</a></div></section>`);
  }
  window.openPracticeReviewV5=function(){legacyRenderPerformance(state.session)};

  renderDrillSetup=function(){
    state.view='drillSetup';
    $('#app').innerHTML=page(`<section class="ps-page ps-setup"><a class="v4-back" href="/practice/">← Practice studio</a><header class="ps-setup-head"><div><div class="eyebrow">Quick drill</div><h1>Build a short retrieval set.</h1><p>Use random segments when you want speed and direction switching rather than dialogue context.</p></div></header><div class="ps-setup-grid"><section class="ps-panel"><h2>Drill</h2><label><span>Topic</span><select id="dTopic" class="select"><option value="All">All topics</option>${topics().map(x=>`<option>${esc(x)}</option>`).join('')}</select></label><label><span>Source speaker</span><select id="dDir" class="select"><option value="All">Both speakers</option><option value="en">English officer</option><option value="yue">Cantonese client</option></select></label><label><span>Number of segments</span><select id="drillSize" class="select"><option>5</option><option selected>10</option><option>20</option></select></label><div id="practiceSetupStatus" class="ps-status" role="status" aria-live="polite"></div><button class="btn primary ps-wide" onclick="startDrill()">Start drill</button></section><section class="ps-panel"><h2>Session defaults</h2>${practiceDefaultsHTML()}<div class="ps-tip"><strong>Drill rule</strong><p>One segment is enough. Speak your interpretation, reveal, self-rate, then move on.</p></div></section></div></section>`);
  };

  startDrill=function(){
    const t=document.getElementById('dTopic')?.value||'All',dir=document.getElementById('dDir')?.value||'All',size=Math.max(1,Number(document.getElementById('drillSize')?.value||10));let pool=[];
    state.dialogues.filter(d=>t==='All'||d.topic===t).forEach(d=>d.segments.filter(s=>dir==='All'||s.source_lang===dir).forEach(seg=>pool.push({did:d.id,n:seg.n})));
    if(!pool.length){practiceStatus('No segments match those filters.','warn');return}
    pool=shuffle(pool).slice(0,Math.min(size,pool.length));state.session={id:uid(),mode:'drill',queue:pool,qi:0,marks:{},notes:{},revealed:{},played:{},startedAt:Date.now(),endedAt:null,subtype:'quick',practiceTimerInterval:null};state.recordings={};state.view='drill';renderDrill();if(prefs().practiceAutoPlay)setTimeout(()=>playDrillSource(),100);
  };

  window.startWeakReviewV5=function(){
    if(document.body.dataset.page!=='practice'){location.href='/practice/?mode=weak';return}
    const queue=state.user.weak.map(k=>{const [did,n]=splitKey(k);return state.byId[did]?.segments?.[n-1]?{did,n}:null}).filter(Boolean);
    if(!queue.length){$('#app').innerHTML=page(`<section class="ps-page ps-empty-state"><div class="ps-complete-mark">⚑</div><div class="eyebrow">Weak review</div><h1>No weak segments yet.</h1><p>Flag a difficult segment with the flag button during guided practice. It will appear here automatically.</p><div class="ps-complete-actions"><a class="btn primary" href="/practice/?mode=topic">Start guided practice</a><a class="btn" href="/questions/">Open question bank</a></div></section>`);return}
    state.session={id:uid(),mode:'drill',queue:shuffle(queue),qi:0,marks:{},notes:{},revealed:{},played:{},startedAt:Date.now(),endedAt:null,subtype:'weak',practiceTimerInterval:null};state.recordings={};state.view='drill';renderDrill();if(prefs().practiceAutoPlay)setTimeout(()=>playDrillSource(),100);
  };

  renderDrill=function(){
    const s=state.session;if(!s||s.mode!=='drill')return;const {d,seg}=currentDrill(),k=sessionKey(d.id,seg.n),rev=!!s.revealed[k],m=s.marks[k]||{rating:null,tags:[]},p=prefs(),played=s.played?.[k]||0,total=s.queue.length;
    $('#app').innerHTML=page(`<section class="ps-session ps-drill"><header class="ps-session-head"><div><a class="v4-back" href="/practice/">← Practice studio</a><div class="eyebrow">${s.subtype==='weak'?'Weak review':'Quick drill'}</div><h1>${s.subtype==='weak'?'Target flagged segments':'Fast retrieval'}</h1>${practiceMeta(d,seg)}</div><div class="ps-session-progress"><strong>${s.qi+1}/${total}</strong><span>${Math.round((s.qi+1)/total*100)}% through set</span></div></header><div class="ps-drill-track"><span style="width:${(s.qi+1)/total*100}%"></span></div><div class="ps-session-layout"><main class="ps-focus-card"><div class="ps-focus-top"><div><span class="kicker">${d.id} · segment ${seg.n}</span><strong>${esc(d.title)}</strong></div><button class="ps-icon-btn ${isWeak(d.id,seg.n)?'on':''}" onclick="toggleDrillWeakV5()" aria-pressed="${isWeak(d.id,seg.n)}">⚑</button></div><div class="ps-audio-zone"><div id="audioStatus" class="ps-audio-status" role="status" aria-live="polite">${played?'Replay when ready.':'Listen, interpret, then reveal.'}</div><div id="practiceTimerLive" class="ps-timer-live">${p.practiceTimer?`${p.practiceTimer}s interpretation timer`:'Timer off'}</div><button id="practicePlayBtn" class="ps-play-big" onclick="playDrillSource()">${played?'↻':'▶'}<span>${played?'Replay':'Play source'}</span></button></div>${rev?`<div class="ps-compare"><section><span class="kicker">Source</span><p>${esc(seg.source)}</p></section><section><span class="kicker">Model interpretation</span><p>${esc(seg.model)}</p></section></div>${assessmentHTML(m,k,'drill')}`:`<div class="ps-reveal"><p>Interpret first, then compare.</p><button class="btn secondary ps-wide" onclick="revealDrillV5()">Reveal source + model</button></div>`}<div class="ps-nav-row"><button class="btn" onclick="previousDrillV5()" ${s.qi===0?'disabled':''}>← Previous</button><span>${rev?(m.rating?`Rated: ${rateLabel(m.rating)}`:'Self-rate when useful'):'You can skip this segment'}</span><button class="btn ${rev?'primary':''}" onclick="nextDrill()">${s.qi===total-1?'Finish set':rev?'Next →':'Skip →'}</button></div></main><aside class="ps-side"><section class="ps-side-card"><h2>Session</h2>${practiceDefaultsHTML()}</section><details class="ps-side-card"><summary>Record</summary><div class="ps-details-body"><div id="recStatus" class="muted" aria-live="polite">Optional.</div><div class="ps-stack-actions"><button id="recordBtn" class="btn" onclick="toggleRecord()">● Record</button><button class="btn" onclick="playMyRecording('${d.id}',${seg.n})" ${state.recordings[k]?'':'disabled'}>Listen to mine</button></div></div></details><div class="ps-keyhint"><kbd>Space</kbd> play · <kbd>Enter</kbd> ${rev?'next':'reveal'} · <kbd>W</kbd> weak</div></aside></div></section>`);
  };

  window.revealDrillV5=function(){const {d,seg}=currentDrill();state.session.revealed[sessionKey(d.id,seg.n)]=true;renderDrill()};
  window.toggleDrillWeakV5=function(){const {d,seg}=currentDrill();toggleWeak(d.id,seg.n,!isWeak(d.id,seg.n));renderDrill()};
  window.previousDrillV5=async function(){const s=state.session;if(!s||s.mode!=='drill'||s.qi<=0)return;stopPlayback();clearPracticeTimer();await stopRecordingIfNeeded();s.qi--;renderDrill()};
  playDrillSource=async function(){const {d,seg}=currentDrill(),k=sessionKey(d.id,seg.n);state.session.played=state.session.played||{};state.session.played[k]=(state.session.played[k]||0)+1;await playSource(d,seg,prefs().practiceRate||1,()=>{const e=document.getElementById('audioStatus');if(e)e.textContent='Chime finished. Interpret now.';startInterpretTimerV5()})};
  nextDrill=async function(){stopPlayback();clearPracticeTimer();await stopRecordingIfNeeded();const s=state.session;if(s.qi<s.queue.length-1){s.qi++;renderDrill();if(prefs().practiceAutoPlay)setTimeout(()=>playDrillSource(),120);return}s.endedAt=Date.now();saveSessionToHistory(s);renderFocusedCompletionV5(s,s.subtype==='weak'?'Weak review complete':'Drill complete')};

  function handlePracticeKeys(e){
    if(!state.session||!['practice','drill'].includes(state.session.mode)||e.target?.closest?.('input,textarea,select,[contenteditable="true"]'))return;
    const ctx=state.session.mode;
    if(e.code==='Space'){e.preventDefault();ctx==='practice'?playPracticeSource():playDrillSource();return}
    if(e.key==='ArrowLeft'){e.preventDefault();ctx==='practice'?previousPracticeV5():previousDrillV5();return}
    if(e.key==='ArrowRight'){e.preventDefault();ctx==='practice'?nextPractice():nextDrill();return}
    if(e.key==='Enter'){e.preventDefault();if(ctx==='practice'){const {d,seg}=currentPractice(),rev=state.session.revealed[sessionKey(d.id,seg.n)];rev?nextPractice():revealPractice()}else{const {d,seg}=currentDrill(),rev=state.session.revealed[sessionKey(d.id,seg.n)];rev?nextDrill():revealDrillV5()}return}
    if(['1','2','3'].includes(e.key)){e.preventDefault();rateFocusedV5(ctx,({1:'strong',2:'minor',3:'needs'})[e.key]);return}
    if(e.key.toLowerCase()==='w'){e.preventDefault();ctx==='practice'?togglePracticeWeakV5():toggleDrillWeakV5()}
  }
  document.addEventListener('keydown',handlePracticeKeys);

  const priorHub=window.renderPracticeHub;
  window.renderPracticeHub=function(){const params=new URLSearchParams(location.search),mode=params.get('mode'),dialogue=params.get('dialogue');if(dialogue&&state.byId[dialogue]){startPractice(dialogue,Number(params.get('si')||0));return}if(mode==='weak'){startWeakReviewV5();return}priorHub()};
})();
