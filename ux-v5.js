/* UX v5 — connect each top-level feature to the next useful action. */
(function(){
  const baseDashboard=renderDashboard;
  const baseMockPicker=renderMockPicker;
  const baseQuestions=window.renderQuestions;
  const baseStudy=renderStudy;
  const baseHistory=renderHistory;

  renderDashboard=function(){
    const result=baseDashboard.apply(this,arguments);
    queueMicrotask(()=>{
      const r=state.user?.prefs?.practiceResume;
      if(!r||!state.byId[r.id]||document.getElementById('v5Resume'))return;
      const hero=document.querySelector('.v4-home-intro');if(!hero)return;
      hero.insertAdjacentHTML('afterend',`<a id="v5Resume" class="v5-resume-banner" href="/practice/?dialogue=${encodeURIComponent(r.id)}&si=${Number(r.si)||0}"><span><strong>Resume guided practice</strong><small>${r.id} · ${esc(state.byId[r.id].title)} · segment ${(Number(r.si)||0)+1}</small></span><span>Continue →</span></a>`);
    });
    return result;
  };

  window.testPracticeAudioV5=async function(){
    const d=state.dialogues[0],seg=d?.segments?.[0],status=document.getElementById('mockAudioStatus');if(!d||!seg)return;
    if(status)status.textContent='Playing audio check…';
    try{await playSource(d,seg,1,()=>{if(status)status.textContent='Audio check complete. You heard the source and chime.'})}
    catch(e){if(status)status.textContent='Audio check failed. Try the Question Bank or reload the page.'}
  };

  renderMockPicker=function(){
    const result=baseMockPicker.apply(this,arguments);
    queueMicrotask(()=>{
      const head=document.querySelector('.v4-page-head');if(!head||document.getElementById('mockPreflight'))return;
      head.insertAdjacentHTML('afterend',`<section id="mockPreflight" class="v5-preflight"><div><strong>Before a mock</strong><span id="mockAudioStatus">Check that your audio is working, then start any mock below.</span></div><button class="btn" onclick="testPracticeAudioV5()">▶ Test audio + chime</button></section>`);
    });
    return result;
  };

  window.randomVisibleQuestionV5=function(){
    const cards=[...document.querySelectorAll('.question-dialogue[data-dialogue-id]')].filter(x=>!x.hidden);if(!cards.length)return;
    const card=cards[Math.floor(Math.random()*cards.length)],id=card.dataset.dialogueId;if(id&&typeof playQuestionDialogue==='function')playQuestionDialogue(id);
  };
  function updateQuestionCountV5(){
    const n=document.querySelectorAll('.question-dialogue[data-dialogue-id]').length,el=document.getElementById('v5QuestionCount');if(el)el.textContent=`${n} dialogue${n===1?'':'s'} shown`;
  }

  if(typeof baseQuestions==='function'){
    window.renderQuestions=function(){
      const result=baseQuestions.apply(this,arguments);
      queueMicrotask(()=>{
        const tools=document.getElementById('qListTools')||document.querySelector('.question-toolbar-v3');
        if(tools&&!document.getElementById('v5QuestionRandom'))tools.insertAdjacentHTML('beforeend',`<button id="v5QuestionRandom" class="btn" onclick="randomVisibleQuestionV5()">⤨ Random question</button><span id="v5QuestionCount" class="v5-count"></span>`);
        updateQuestionCountV5();
      });
      return result;
    };
  }
  const beforeFilter=window.filterQuestions;
  if(typeof beforeFilter==='function'){
    window.filterQuestions=function(){const r=beforeFilter.apply(this,arguments);queueMicrotask(updateQuestionCountV5);return r};
  }

  renderStudy=function(slug){
    const result=baseStudy.apply(this,arguments);
    Promise.resolve(result).finally(()=>setTimeout(()=>{
      const content=document.getElementById('studyContent');if(!content||document.getElementById('v5StudyTools'))return;
      const nav=document.querySelector('.study-nav');if(nav)nav.insertAdjacentHTML('beforebegin',`<div id="v5StudyTools" class="v5-study-tools"><div><strong>Study tools</strong><span>Read a guide, then immediately practise the same skill.</span></div><div><a class="btn" href="/study/?view=vocabulary">Vocabulary</a><a class="btn" href="/practice/?mode=drill">Quick drill</a><a class="btn" href="/questions/">Question bank</a></div></div>`);
    },0));
    return result;
  };

  renderHistory=function(){
    const result=baseHistory.apply(this,arguments);
    queueMicrotask(()=>{
      const page=document.querySelector('.v4-progress-page')||document.querySelector('.hero')?.parentElement;if(!page||document.getElementById('v5ProgressActions'))return;
      const weak=state.user?.weak?.length||0;
      const bar=document.createElement('section');bar.id='v5ProgressActions';bar.className='v5-progress-actions';bar.innerHTML=`<div><strong>Turn progress into the next rep</strong><span>${weak?`${weak} weak segment${weak===1?'':'s'} are ready for review.`:'No weak segments flagged yet.'}</span></div><div><a class="btn primary" href="${weak?'/practice/?mode=weak':'/practice/?mode=topic'}">${weak?'Review weak':'Guided practice'}</a><a class="btn" href="/practice/?mode=drill">Quick drill</a><a class="btn" href="/mock/">Mock exam</a></div>`;
      const top=page.querySelector('.v4-progress-head,.hero,.section');if(top)top.insertAdjacentElement('afterend',bar);else page.prepend(bar);
    });
    return result;
  };

  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'&&!e.target?.closest?.('input,textarea,select,[contenteditable="true"]'))stopPlayback();
  });
})();
