// Neural audio adapter for the final CCL Exam Lab release.
// Loaded after app.js. It replaces only the playback path. If a neural segment
// fails, callers fall back to current-text device speech rather than legacy MP3
// bundles whose speaker assignments may no longer match the release bank.
(() => {
  const legacyPlay = AudioEngine.prototype.play;
  const LEARNER_BASE_RATE = 0.88;
  AudioEngine.prototype.play = async function(id, segIndex, rate=1, onDone){
    const remote=state.remoteAudio;
    if(!remote || remote.mode!=='segments' || !remote.baseUrl){
      return legacyPlay.call(this,id,segIndex,rate,onDone);
    }
    const token=++this.stopToken;
    const version=encodeURIComponent(remote.cacheVersion||remote.version||'native500');
    const url=`${remote.baseUrl.replace(/\/$/,'')}/${id}/S${String(segIndex+1).padStart(2,'0')}.mp3?v=${version}`;
    try{
      this.audio.pause();
      this.audio.removeAttribute('src');
      this.audio.load();
      this.audio.src=url;
      this.audio.preload='auto';
      // The stored files match the fast official-style reference pace, but that
      // proved too quick for repeated learner practice. Slow every neural segment
      // consistently while preserving voice pitch. Existing training rate controls
      // still work, but are applied on top of this learner-friendly baseline.
      if('preservesPitch' in this.audio) this.audio.preservesPitch=true;
      if('webkitPreservesPitch' in this.audio) this.audio.webkitPreservesPitch=true;
      this.audio.playbackRate=Math.max(0.75,Math.min(1.0,rate*LEARNER_BASE_RATE));
      await new Promise((resolve,reject)=>{
        const ok=()=>{cleanup();resolve()};
        const bad=()=>{cleanup();reject(new Error('Neural MP3 metadata failed'))};
        const cleanup=()=>{this.audio.removeEventListener('canplay',ok);this.audio.removeEventListener('error',bad)};
        if(this.audio.readyState>=3)return resolve();
        this.audio.addEventListener('canplay',ok,{once:true});
        this.audio.addEventListener('error',bad,{once:true});
        this.audio.load();
      });
      if(token!==this.stopToken)return;
      await this.audio.play();
      await new Promise((resolve,reject)=>{
        const done=()=>{cleanup();resolve()};
        const bad=()=>{cleanup();reject(new Error('Neural MP3 playback failed'))};
        const cleanup=()=>{this.audio.removeEventListener('ended',done);this.audio.removeEventListener('error',bad)};
        this.audio.addEventListener('ended',done,{once:true});
        this.audio.addEventListener('error',bad,{once:true});
      });
      if(token!==this.stopToken)return;
      chime(()=>onDone&&onDone());
    }catch(e){
      throw e;
    }
  };

  const oldAudioSettings=audioSettingsHTML;
  audioSettingsHTML=function(){
    if(!state.remoteAudio || state.remoteAudio.mode!=='segments') return oldAudioSettings();
    return `<section class="section card"><div class="section-head"><div><div class="eyebrow">Audio realism</div><h2>Neural two-speaker source audio</h2><p class="muted">The primary source audio is prerecorded as individual Supabase MP3 segments. The Australian professional/officer speaks <strong>English</strong>; the immigrant/community client speaks <strong>Cantonese</strong>. After listener review, neural playback now uses a <strong>0.88× learner baseline</strong> with pitch preservation, so normal practice is roughly <strong>145–150 English wpm</strong> and <strong>3.5–3.7 Cantonese Han/s</strong> instead of the faster reference-recording pace.</p></div></div><div class="notice">The speed buttons still adjust playback, but they now sit on top of the learner baseline. If a neural file cannot load, the app falls back to current-text device speech rather than obsolete bundled audio.</div></section>`;
  };

  // app.js historically named this card "100-dialogue Library" and hard-coded a
  // vocabulary count. Keep the core renderer stable but make those labels derive
  // from the actual loaded release data so future bank changes cannot stale them.
  const oldModeCard=modeCard;
  modeCard=function(n,t,p,act){
    if(t==='100-dialogue Library'){
      const count=state.summary?.dialogues||state.dialogues?.length||0;
      t=`${count}-dialogue Library`;
    }
    if(t==='Study & Vocabulary'){
      const count=state.glossary?.length||0;
      p=p.replace(/\b198 Australian bilingual terms\b/,`${count} Australian bilingual terms`);
    }
    return oldModeCard(n,t,p,act);
  };
})();
