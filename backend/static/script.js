// script.js
// Place in same folder as your index.html; expects /litro POST endpoint to exist.

const inputText = document.getElementById('inputText');
const btnBrowser = document.getElementById('btnBrowser');
const btnServer = document.getElementById('btnServer');
const btnPreview = document.getElementById('btnPreviewProcessed');
const statusText = document.getElementById('statusText');
const processedTextPre = document.getElementById('processedText');
const voiceSelect = document.getElementById('voiceSelect');

function setStatus(s) {
  statusText.innerText = s;
}

// --- Browser voices / SpeechSynthesis setup ---
let voices = [];
function loadVoices() {
  voices = speechSynthesis.getVoices();
  // Populate select with Tamil-capable voices first
  voiceSelect.innerHTML = '<option value="">— Select browser voice (optional) —</option>';
  voices.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.name;
    opt.textContent = `${v.name} — ${v.lang}`;
    voiceSelect.appendChild(opt);
  });
}
if ('speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = loadVoices;
  loadVoices();
} else {
  setStatus('Browser does not support SpeechSynthesis — use Server TTS.');
  btnBrowser.disabled = true;
}

// Helper to find a Tamil voice (best guess)
function findTamilVoice() {
  // prefer exact ta or ta-IN
  let v = voices.find(x => x.lang && (x.lang.startsWith('ta')));
  if (v) return v;
  // else pick any voice containing "Tamil" in name
  v = voices.find(x => x.name && x.name.toLowerCase().includes('tamil'));
  return v || null;
}

// Browser TTS playback
async function playBrowserTTS(text) {
  if (!('speechSynthesis' in window)) {
    alert('Browser does not support speechSynthesis.');
    return;
  }
  speechSynthesis.cancel();

  const utter = new SpeechSynthesisUtterance(text);
  // use selected voice if picked
  const chosen = voiceSelect.value ? voices.find(v => v.name === voiceSelect.value) : findTamilVoice();
  if (chosen) {
    utter.voice = chosen;
    utter.lang = chosen.lang || 'ta-IN';
  } else {
    // try ta-IN by default (some browsers will map to best available)
    utter.lang = 'ta-IN';
  }
  // adjust rate/pitch for better naturalness if desired
  utter.rate = 0.95; // 0.8-1.1 is normal range
  utter.pitch = 1.0;

  setStatus('Playing (browser TTS)...');
  utter.onend = () => setStatus('idle');
  utter.onerror = (e) => { setStatus('Browser TTS error'); console.error(e); };
  speechSynthesis.speak(utter);
}

// Server TTS: call your /litro endpoint which returns JSON { answer, audio_url, meta }
async function playServerTTS(text) {
  try {
    setStatus('Requesting server TTS...');
    const res = await fetch('/litro', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text })
    });
    if (!res.ok) {
      const err = await res.json().catch(()=>({}));
      setStatus('Server error: ' + (err.answer || res.statusText));
      return;
    }
    const data = await res.json();
    // Show processed text
    processedTextPre.innerText = data.answer || '—';
    setStatus('Playing server audio (gTTS)...');

    if (data.audio_url) {
      const audio = new Audio(data.audio_url);
      audio.onended = () => setStatus('idle');
      audio.onerror = () => setStatus('Audio playback failed');
      audio.play().catch(e => {
        setStatus('Audio play blocked by browser. Click to allow.');
        console.error(e);
      });
    } else {
      setStatus('No audio URL from server; check server logs.');
    }
  } catch (e) {
    console.error(e);
    setStatus('Network error or server unreachable.');
  }
}

// Preview processed text only (doesn't auto-play)
async function previewProcessed(text) {
  try {
    setStatus('Requesting processed text...');
    const res = await fetch('/preprocess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    const data = await res.json();
    processedTextPre.innerText = data.processed || '—';
    setStatus('idle');
  } catch (e) {
    console.error(e);
    setStatus('Failed to get processed text');
  }
}

// Bind buttons
btnBrowser.addEventListener('click', async () => {
  const t = inputText.value.trim();
  if (!t) return alert('Please enter Tamil text.');
  // Get preprocessed text from server for natural pronunciation
  setStatus('Preprocessing text...');
  try {
    const res = await fetch('/preprocess', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: t })
    });
    const data = await res.json();
    const processed = data.processed || t;
    processedTextPre.innerText = processed;
    // If no Tamil browser voice, ask whether to use server TTS
    const tamilVoice = findTamilVoice() || (voiceSelect.value ? voices.find(v => v.name === voiceSelect.value) : null);
    if (!tamilVoice) {
      if (!confirm('No Tamil browser voice detected. Browser TTS may sound incorrect. Use server TTS instead? Click Cancel to still try browser TTS.')) {
        playBrowserTTS(processed);
        return;
      } else {
        // use server TTS (speak endpoint)
        setStatus('Requesting server TTS...');
        const sres = await fetch('/speak', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: processed }) });
        if (!sres.ok) { setStatus('Server TTS failed'); return; }
        const sdata = await sres.json();
        if (sdata.audio_url) {
          const audio = new Audio(sdata.audio_url);
          setStatus('Playing server audio...');
          audio.onended = () => setStatus('idle');
          audio.play();
        } else {
          setStatus('No audio available');
        }
        return;
      }
    }
    playBrowserTTS(processed);
  } catch (e) {
    console.error(e);
    setStatus('Preprocess request failed. Falling back to raw text.');
    playBrowserTTS(t);
  }
});

btnServer.addEventListener('click', async () => {
  const t = inputText.value.trim();
  if (!t) return alert('Please enter Tamil text.');
  // Use speak endpoint to preprocess and get server audio
  try {
    setStatus('Requesting server TTS...');
    const res = await fetch('/speak', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: t }) });
    if (!res.ok) { const err = await res.json().catch(()=>({})); setStatus('Server TTS failed: '+(err.error||res.statusText)); return; }
    const data = await res.json();
    processedTextPre.innerText = data.processed || '';
    if (data.audio_url) {
      const audio = new Audio(data.audio_url);
      setStatus('Playing server audio...');
      audio.onended = () => setStatus('idle');
      audio.play().catch(e=>setStatus('Audio play blocked'));
    } else {
      setStatus('No audio from server');
    }
  } catch (e) {
    console.error(e);
    setStatus('Server unreachable');
  }
});

btnPreview.addEventListener('click', () => {
  const t = inputText.value.trim();
  if (!t) return alert('Please enter Tamil text.');
  previewProcessed(t);
});
