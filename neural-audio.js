// Neural audio adapter for CCL Exam Lab v3.
// Loaded after app.js. It replaces only the playback path. If a neural segment
// fails, callers fall back to current-text device speech rather than the legacy
// pre-normalisation MP3 bundles, which may contain obsolete speaker languages.
(() => {
  const legacyPlay = AudioEngine.prototype.play;
  AudioEngine.prototype.play = async function(id, segIndex, rate=1, onDone){
    const remote=state.remoteAudio;
    if(!remote || remote.mode!=='segments' || !remote.baseUrl){
      return legacyPlay.call(this,id,segIndex,rate,onDone);
    }
    const token=++this.stopToken;
    const version=encodeURIComponent(remote.cacheVersion||remote.version||'v3');
    const url=`${remote.baseUrl.replace(/\/$/,'')}/${id}/S${String(segIndex+1).padStart(2,'0')}.mp3?v=${version}`;
    try{
      this.audio.pause();
      this.audio.removeAttribute('src');
      this.audio.load();
      this.audio.src=url;
      this.audio.preload='auto';
      this.audio.playbackRate=rate;
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
      // Neural files contain spoken source only. Add the two-tone interpretation cue locally.
      chime(()=>onDone&&onDone());
    }catch(e){
      // Do not use legacy bundles here: speaker-language assignments changed during
      // the final bank normalisation. Throw so playSource()/Questions use current
      // segment text and language via device speech fallback instead.
      throw e;
    }
  };

  const oldAudioSettings=audioSettingsHTML;
  audioSettingsHTML=function(){
    if(!state.remoteAudio || state.remoteAudio.mode!=='segments') return oldAudioSettings();
    const ref=state.config?.audioCalibration||{};
    return `<section class="section card"><div class="section-head"><div><div class="eyebrow">Audio realism</div><h2>Neural two-speaker source audio</h2><p class="muted">The primary source audio is prerecorded as individual Supabase MP3 segments. The Australian professional/officer speaks <strong>English</strong>; the immigrant/community client speaks <strong>Cantonese</strong>. English targets about <strong>${ref.englishTargetWpm||160} wpm</strong>, while Cantonese uses the faster regenerated +10% neural rate.</p></div></div><div class="notice">Mock mode uses 1.0× playback. Training can use 0.9×, 1.0× or 1.08×. If a neural file cannot load, the app falls back to current-text device speech rather than obsolete bundled audio.</div></section>`;
  };
})();
