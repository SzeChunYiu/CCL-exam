/* Quick-play controls for collapsed Question Bank cards. */
(function(){
  function decorate(){
    document.querySelectorAll('.question-dialogue[data-dialogue-id]').forEach(card=>{
      const summary=card.querySelector(':scope > summary');
      if(!summary || summary.querySelector('.question-card-play')) return;
      const id=card.dataset.dialogueId;
      const button=document.createElement('button');
      button.type='button';
      button.className='question-card-play';
      button.setAttribute('aria-label',`Play ${id}`);
      button.innerHTML='<span aria-hidden="true">▶</span><span class="question-card-play-label">Play</span>';
      button.addEventListener('click',event=>{
        event.preventDefault();
        event.stopPropagation();
        if(typeof window.playQuestionDialogue==='function') window.playQuestionDialogue(id);
      });
      button.addEventListener('keydown',event=>{
        if(event.key==='Enter'||event.key===' '){
          event.preventDefault();
          event.stopPropagation();
          if(typeof window.playQuestionDialogue==='function') window.playQuestionDialogue(id);
        }
      });
      const chevron=summary.querySelector('.question-chevron');
      if(chevron) summary.insertBefore(button,chevron); else summary.appendChild(button);
    });
  }

  const observer=new MutationObserver(()=>decorate());
  function watch(){
    const list=document.getElementById('questionsList');
    if(!list)return;
    observer.disconnect();
    observer.observe(list,{childList:true,subtree:true});
    decorate();
  }

  const baseRender=window.renderQuestions;
  if(typeof baseRender==='function'){
    window.renderQuestions=function(){
      const result=baseRender.apply(this,arguments);
      queueMicrotask(watch);
      return result;
    };
  }

  const baseFilter=window.filterQuestions;
  if(typeof baseFilter==='function'){
    window.filterQuestions=function(){
      const result=baseFilter.apply(this,arguments);
      queueMicrotask(decorate);
      return result;
    };
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>setTimeout(watch,0));
  else setTimeout(watch,0);
})();