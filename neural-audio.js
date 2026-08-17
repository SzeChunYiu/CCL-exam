// Neural audio adapter for CCL Exam Lab v3.
// Loaded after app.js. It replaces only the playback path; the existing bundled
// MP3 and device-speech engines remain available as fallbacks.
(() => {
  const legacyPlay = AudioEngine.prototype.play;
  AudioEngine.prototype.play = async function(id, segIndex, rate=1, onDone){
    const remote=state.remoteAudio;
    if(!remote || remote.mode!=='segments' || !remote.baseUrl){
      return legacyPlay.call(this,id,segIndex,rate,onDone);
    }
    const token=++this.stopToken;
    const url=`${remote.baseUrl.replace(/\/$/,'')}/${id}/S${String(segIndex+1).padStart(2,'0')}.mp3`;
    try{
      this.audio.pause();
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
      await new Promise(resolve=>{
        const done=()=>{cleanup();resolve()};
        const cleanup=()=>{this.audio.removeEventListener('ended',done);this.audio.removeEventListener('error',done)};
        this.audio.addEventListener('ended',done,{once:true});
        this.audio.addEventListener('error',done,{once:true});
      });
      if(token!==this.stopToken)return;
      // Neural files contain the spoken source only. Add the same two-tone exam cue
      // locally so interpretation begins after a consistent chime.
      chime(()=>onDone&&onDone());
    }catch(e){
      // Preserve the old calibrated bundle as a secondary fallback while migration
      // settles, then playSource() will still fall back to a suitable device voice.
      return legacyPlay.call(this,id,segIndex,rate,onDone);
    }
  };

  const oldAudioSettings=audioSettingsHTML;
  audioSettingsHTML=function(){
    if(!state.remoteAudio || state.remoteAudio.mode!=='segments') return oldAudioSettings();
    const ref=state.config?.audioCalibration||{};
    return `<section class="section card"><div class="section-head"><div><div class="eyebrow">Audio realism</div><h2>Neural two-speaker source audio</h2><p class="muted">The primary source audio is prerecorded as individual Supabase MP3 segments using alternating <strong>Australian-English</strong> and <strong>Hong Kong Cantonese</strong> neural voices. Delivery targets the measured reference pace of about <strong>${ref.englishTargetWpm||160} English wpm</strong> and roughly <strong>4.0 Cantonese characters/second</strong>.</p></div></div><div class="notice">Mock mode uses 1.0×. Training can use 0.9×, 1.0× or 1.08×. Legacy bundled MP3 and device speech remain fallback paths only. These are synthetic neural practice voices, not official NAATI or human recordings.</div></section>`;
  };
})();
