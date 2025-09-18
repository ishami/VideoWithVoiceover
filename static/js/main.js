/*  main.js  –  Logic for the Main tab  +  Script→Clips flow
    --------------------------------------------------------
    A. Main tab
       1) Populate voice <select> with /api/voices
       2) Play test MP3 when "Test voice" is clicked
       3) Handle "Modify keywords?" (Bootstrap modal)

    B. Script tab
       1) Intercept "Save & Regenerate"
       2) Submit via fetch → wait for JSON
       3) When status === "CLIPS_READY" → redirect to /clips
       4) Periodically check regeneration status
*/

(() => {
  /* ---------- tiny helper ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);

  /* ======================================================================
     A. MAIN TAB
     ====================================================================*/
  document.addEventListener('DOMContentLoaded', () => {
    const voiceSelect = $('#voiceSelect');
    if (voiceSelect) {                       // only on the Main page
      /* 1. populate voice list */
      fetch('/api/voices')
        .then(r => r.json())
        .then(list => {
          list.forEach(v => {
            const opt = document.createElement('option');
            opt.textContent = v;
            voiceSelect.appendChild(opt);
          });

          // Set default voice after populating the list
          if (list.includes('en-US-AvaMultilingualNeural')) {
            voiceSelect.value = 'en-US-AvaMultilingualNeural';
          } else {
            console.warn("Default voice 'en-US-AvaMultilingualNeural' not found in voice list");
          }
        })
        .catch(error => {
          console.error("Error loading voice options:", error);
        });


      /* 2. play test voice */
      $('#testVoice').addEventListener('click', () => {
        const voice = voiceSelect.value;
        if (!voice) return;
        fetch('/api/test_voice', {
          method : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body   : JSON.stringify({ voice })
        })
        .then(r => r.blob())
        .then(blob => {
          const url = URL.createObjectURL(blob);
          new Audio(url).play();
        })
        .catch(console.error);
      });

      /* 3. keyword modal + form submit */
      const form       = $('#mainForm');
      const startBtn   = $('#startBtn');
      const kwHidden   = $('#kwHidden');
      const kwModalEl  = $('#kwModal');
      const kwModal    = new bootstrap.Modal(kwModalEl);
      const kwArea     = $('#kwTextarea');

      $('#kwContinue').addEventListener('click', () => {
        kwHidden.value = kwArea.value;     // push edits into hidden field
        kwModal.hide();
        form.submit();                     // finally send the form
      });

      startBtn.addEventListener('click', e => {
        e.preventDefault();                // we will decide when to submit

        const modifyYes = $('input[name="modify_kw"][value="yes"]').checked;
        if (!modifyYes) return form.submit();   // no modal → straight off

        /* ask server for suggested keywords */
        const title  = $('input[name="video_title"]').value;
        const prompt = $('textarea[name="script"]').value;

        fetch('/api/keywords', {
          method : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body   : JSON.stringify({ title, prompt })
        })
        .then(r => r.json())
        .then(list => {
          kwArea.value = list.join(', ');
          kwModal.show();
        })
        .catch(err => {
          console.error(err);
          form.submit();                  // fall back if API fails
        });
      });
    }   // end if-voiceSelect (Main tab only)
  });

  /* ======================================================================
   B. SCRIPT TAB  –  Save & Regenerate  →  /clips
   ====================================================================*/
 document.addEventListener('DOMContentLoaded', () => {

  const saveBtn   = document.querySelector('#saveRegenerateBtn');
  const scriptFrm = document.querySelector('#scriptForm');
  if (!saveBtn || !scriptFrm) return;        // not on Script page

  const goToClips = () => {
    console.log('[main.js] Redirecting to /clips');
    window.location.assign('/clips?project_id=' + (window.currentProjectId || sessionStorage.getItem('project_id') || ''));
  };

  // Function to check regeneration status periodically
  function checkRegenerationStatus() {
    fetch('/api/regeneration-status')
      .then(response => response.text())
      .then(status => {
        // Update the status message if status container exists
        const statusMessage = $('#status-message');
        if (statusMessage) {
          statusMessage.textContent = status;
        }

        // If the status indicates completion, redirect to clips page
        if (status === 'Regeneration complete') {
          console.log('[main.js] Regeneration complete, redirecting to /clips');
          clearInterval(statusInterval);
          goToClips();
        }

        // If there was an error, show an alert
        if (status.startsWith('Error')) {
          console.error('[main.js] Regeneration error:', status);
          clearInterval(statusInterval);
          alert('There was an error during regeneration: ' + status);
        }
      })
      .catch(error => {
        console.error('[main.js] Error checking regeneration status:', error);
      });
  }

  saveBtn.addEventListener('click', async ev => {
    ev.preventDefault();

    const formData = new FormData(scriptFrm);
    let status = '';

    try {
      /*  ← notice "?ajax=1"  */
      const resp = await fetch('/script?ajax=1', {
        method  : 'POST',
        body    : formData,
        headers : {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept'          : 'application/json'
        }
      });

      const ct = resp.headers.get('content-type') || '';
      if (ct.includes('json')) {
        const data = await resp.json();
        status = (data.status || data.msg || '').toUpperCase();
      } else {
        status = (await resp.text()).trim().toUpperCase();
      }

      console.log('[main.js] Server returned status =', status);

    } catch (err) {
      console.error('[main.js] fetch error:', err);
      return alert('Network error – see console.');
    }

    if (status === 'CLIPS_READY') {
      goToClips();
    } else {
      // Create status display if it doesn't exist
      let statusContainer = $('#status-container');
      if (!statusContainer) {
        statusContainer = document.createElement('div');
        statusContainer.id = 'status-container';
        statusContainer.className = 'alert alert-info mt-3';
        scriptFrm.parentNode.insertBefore(statusContainer, scriptFrm.nextSibling);

        const statusMessage = document.createElement('p');
        statusMessage.id = 'status-message';
        statusMessage.textContent = 'Downloading content – please wait... You will be switched to Clips once finished.';
        statusContainer.appendChild(statusMessage);
      }

      // Start checking status every 2 seconds
      const statusInterval = setInterval(checkRegenerationStatus, 2000);

      // Add a timeout to prevent indefinite waiting
      setTimeout(() => {
        clearInterval(statusInterval);
        const statusMessage = $('#status-message');
        if (statusMessage) {
          statusMessage.textContent = 'Process is taking longer than expected. You can try refreshing the page or going to the Clips tab manually.';
        }
      }, 300000); // 5 minute timeout
    }
  });
 });
})();