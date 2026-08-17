/* Practice Studio v5 runtime guards: route entry points and resilient play-button state. */
(function(){
  const baseHub=window.renderPracticeHub;
  if(typeof baseHub==='function'){
    window.renderPracticeHub=function(){
      const params=new URLSearchParams(location.search),mode=params.get('mode');
      if(mode==='topic'){renderPracticeSetup();return}
      if(mode==='drill'){renderDrillSetup();return}
      return baseHub.apply(this,arguments);
    };
  }

  const basePracticePlay=playPracticeSource;
  playPracticeSource=async function(){
    try{return await basePracticePlay.apply(this,arguments)}
    finally{const button=document.getElementById('practicePlayBtn');if(button)button.disabled=false}
  };
})();
