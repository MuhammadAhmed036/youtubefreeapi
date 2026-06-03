const videoUrl = document.getElementById('videoUrl');
const resolutionSelect = document.getElementById('resolution');
const loadBtn = document.getElementById('loadBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusBox = document.getElementById('status');
const titleBox = document.getElementById('title');
const authorBox = document.getElementById('author');
const lengthBox = document.getElementById('length');
const availableBox = document.getElementById('available');

function setStatus(message, type = '') {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`.trim();
}

function setInfo({ title = '-', author = '-', length = '-', available = '-' } = {}) {
  titleBox.textContent = title;
  authorBox.textContent = author;
  lengthBox.textContent = length;
  availableBox.textContent = available;
}

function formatLength(seconds) {
  if (!seconds && seconds !== 0) return '-';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  if (hrs > 0) {
    return `${hrs}h ${remMins}m ${secs}s`;
  }
  return `${mins}m ${secs}s`;
}

function populateResolutions(values) {
  const existing = new Set();
  Array.from(resolutionSelect.options).forEach((option) => existing.add(option.value));

  values.forEach((value) => {
    if (!existing.has(value)) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      resolutionSelect.appendChild(option);
    }
  });

  if (values.includes('1080p')) {
    resolutionSelect.value = '1080p';
  } else if (values.includes('720p')) {
    resolutionSelect.value = '720p';
  } else if (values.length > 0) {
    resolutionSelect.value = values[0];
  }
}

async function fetchResolutions() {
  const url = videoUrl.value.trim();
  if (!url) {
    setStatus('Paste a YouTube link first.', 'error');
    return;
  }

  setStatus('Loading available resolutions...', '');
  downloadBtn.disabled = true;

  try {
    const response = await fetch('/available_resolutions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Unable to load resolutions.');
    }

    const combined = Array.from(new Set([...(data.progressive || []), ...(data.all || [])]))
      .filter(Boolean)
      .sort((a, b) => Number.parseInt(a) - Number.parseInt(b));

    if (combined.length > 0) {
      populateResolutions(combined);
    }

    setInfo({
      available: combined.length ? combined.join(', ') : 'No resolutions found'
    });

    const infoResponse = await fetch('/video_info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    const infoData = await infoResponse.json();
    if (infoResponse.ok) {
      setInfo({
        title: infoData.title || '-',
        author: infoData.author || '-',
        length: formatLength(infoData.length),
        available: combined.length ? combined.join(', ') : 'No resolutions found'
      });
    }

    setStatus('Resolutions loaded. Pick one and download.', 'success');
    downloadBtn.disabled = false;
  } catch (error) {
    setStatus(error.message, 'error');
    downloadBtn.disabled = false;
  }
}

async function downloadVideo() {
  const url = videoUrl.value.trim();
  const resolution = resolutionSelect.value;

  if (!url) {
    setStatus('Paste a YouTube link first.', 'error');
    return;
  }

  if (!resolution) {
    setStatus('Choose a resolution first.', 'error');
    return;
  }

  setStatus('Preparing file download...', '');
  downloadBtn.disabled = true;

  try {
    const response = await fetch(`/download_file/${encodeURIComponent(resolution)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || 'Download failed.');
    }

    const blob = await response.blob();
    const objectUrl = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = objectUrl;
    anchor.download = `youtube_${resolution}.mp4`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(objectUrl);

    setStatus('Download started in your browser.', 'success');
  } catch (error) {
    setStatus(error.message, 'error');
  } finally {
    downloadBtn.disabled = false;
  }
}

loadBtn.addEventListener('click', fetchResolutions);
downloadBtn.addEventListener('click', downloadVideo);
videoUrl.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    fetchResolutions();
  }
});

setInfo();
