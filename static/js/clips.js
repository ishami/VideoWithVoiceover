/* Clips helper script */
(() => {
  'use strict';

  const DEBUG = window.DEBUG ?? true;
  const log = (...a) => DEBUG && console.log(...a);

  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];

  function formatTime(sec) {
    if (!sec) return '0:00';
    const h = Math.floor(sec / 3600);
    const m = Math.floor(sec % 3600 / 60);
    const s = Math.floor(sec % 60);
    return h ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}` : `${m}:${String(s).padStart(2,'0')}`;
  }

  let currentAudio = null;

  function handleAudioClick() {
    const src = this.dataset.src;
    if (!src) return;

    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
      $$('i.fa-music').forEach(i => i.classList.remove('text-danger'));
    }

    if (this.dataset.playing === 'true') {
      this.dataset.playing = 'false';
      return;
    }

    currentAudio = new Audio(src);
    const icon = this;
    currentAudio.play().then(() => {
      icon.dataset.playing='true';
      icon.classList.add('text-danger');
    }).catch(()=>alert('Cannot play audio'));

    currentAudio.addEventListener('ended', ()=>{
      icon.dataset.playing='false';
      icon.classList.remove('text-danger');
      currentAudio=null;
    });
  }

  function showPreview(el) {
    const src = el.dataset.src || el.src;
    if (!src) return;
    let html = '';
    const ext = src.split('.').pop().toLowerCase();
    if (['mp4','webm','mov'].includes(ext)) html = `<video src="${src}" controls autoplay style="width:100%"></video>`;
    else if (['mp3','wav','ogg','m4a'].includes(ext)) html = `<audio src="${src}" controls autoplay style="width:100%"></audio>`;
    else html = `<img src="${src}" style="max-width:100%;height:auto;">`;
    openModal(html);
  }

  let modal;
  function openModal(html) {
    if (!modal) {
      modal = document.createElement('div');
      modal.className = 'modal fade';
      modal.tabIndex=-1;
      modal.innerHTML=`<div class="modal-dialog modal-lg modal-dialog-centered"><div class="modal-content"><div class="modal-body p-0"></div></div></div>`;
      document.body.appendChild(modal);
    }
    modal.querySelector('.modal-body').innerHTML=html;
    bootstrap.Modal.getOrCreateInstance(modal).show();
  }

  function initPreviews() {
    $$('img.clip-thumb[data-src]').forEach(img=>img.addEventListener('click',()=>showPreview(img)));
    $$('i.clip-play[data-src]').forEach(i=>{
      if(i.classList.contains('fa-music')) i.addEventListener('click',handleAudioClick);
      else i.addEventListener('click',()=>showPreview(i));
    });
  }

  function renderClipsTable(clips) {
    const clipBody = $('#clipBody');
    if (!clipBody || !clips) return;

    clipBody.innerHTML = ''; // clear old rows

    clips.media_clips.forEach((path, idx) => {
      const ext = path.split('.').pop().toLowerCase();
      let html = `<tr>`;
      html += `<td>${idx+1}</td>`;
      if(['mp4','mov','webm'].includes(ext)){
        html += `<td><video src="${path}" width="120" controls></video></td>`;
      } else if(['jpg','png','jpeg','gif'].includes(ext)){
        html += `<td><img class="clip-thumb" data-src="${path}" src="${path}" width="120"></td>`;
      } else {
        html += `<td>Unknown</td>`;
      }
      html += `</tr>`;
      clipBody.insertAdjacentHTML('beforeend', html);
    });

    // initialize previews after adding all rows
    initPreviews();
  }

  document.addEventListener('DOMContentLoaded',()=>{

    const clipBody = $('#clipBody');

    // Initialize Sortable once
    if (clipBody && window.Sortable) {
      new Sortable(clipBody,{
        animation:150,
        ghostClass:'bg-light',
        onEnd:()=>{ log('Reordered'); }
      });
    }

    // Load initial clips if clipsJson exists
    if (window.clipsJson) renderClipsTable(window.clipsJson);

    // Example: expose a function to update table dynamically after Save & Regenerate
    window.updateClips = function(newClipsJson) {
      renderClipsTable(newClipsJson);
    };
  });

})();
