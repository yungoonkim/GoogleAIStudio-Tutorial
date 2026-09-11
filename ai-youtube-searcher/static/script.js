// ================= Tailwind CSS 테마 커스텀 설정 =================
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        yt: {
          bg: 'var(--color-bg)',
          card: 'var(--color-card)',
          hover: 'var(--color-hover)',
          border: 'var(--color-border)',
          red: 'var(--color-primary)',
          text: 'var(--color-text)',
          subtext: 'var(--color-subtext)',
        }
      }
    }
  }
};

// ================= 테마 관리 시스템 (Dark / Sage / Amber) =================
const THEMES = {
  dark: { name: 'Dark', icon: '🌙', desc: 'YouTube Dark' },
  sage: { name: 'Modern Sage', icon: '🌿', desc: '세이지 & 펄 그레이' },
  amber: { name: 'Warm Earth', icon: '🌅', desc: '에스프레소 & 앰버 골드' }
};

let currentTheme = 'dark';
let isThemeDropdownOpen = false;

function toggleThemeDropdown(event) {
  if (event) event.stopPropagation();
  const dropdown = document.getElementById('themeDropdown');
  const chevron = document.getElementById('themeChevron');
  isThemeDropdownOpen = !isThemeDropdownOpen;
  
  if (isThemeDropdownOpen) {
    if (dropdown) dropdown.classList.remove('hidden');
    if (chevron) chevron.classList.add('rotate-180');
  } else {
    closeThemeDropdown();
  }
}

function closeThemeDropdown() {
  const dropdown = document.getElementById('themeDropdown');
  const chevron = document.getElementById('themeChevron');
  if (dropdown) dropdown.classList.add('hidden');
  if (chevron) chevron.classList.remove('rotate-180');
  isThemeDropdownOpen = false;
}

function setTheme(theme) {
  if (!THEMES[theme]) theme = 'dark';
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  try {
    localStorage.setItem('yt_ai_theme', theme);
  } catch (e) {}

  // 헤더 버튼 텍스트 및 아이콘 갱신
  const iconEl = document.getElementById('currentThemeIcon');
  const nameEl = document.getElementById('currentThemeName');
  if (iconEl) iconEl.textContent = THEMES[theme].icon;
  if (nameEl) nameEl.textContent = THEMES[theme].name;

  // 드롭다운 옵션 체크마크 갱신
  ['dark', 'sage', 'amber'].forEach(t => {
    const opt = document.getElementById(`themeOpt-${t}`);
    if (opt) {
      const check = opt.querySelector('.check-icon');
      if (t === theme) {
        opt.classList.add('bg-yt-hover', 'font-bold');
        if (check) check.classList.remove('hidden');
      } else {
        opt.classList.remove('bg-yt-hover', 'font-bold');
        if (check) check.classList.add('hidden');
      }
    }
  });

  // 프로그레스바 색상 갱신
  const progressBar = document.getElementById('progressBar');
  if (progressBar) {
    progressBar.style.backgroundColor = `var(--color-progress-bar)`;
  }

  closeThemeDropdown();
}

function initTheme() {
  let savedTheme = 'dark';
  try {
    savedTheme = localStorage.getItem('yt_ai_theme') || 'dark';
  } catch (e) {}
  setTheme(savedTheme);
}

// 초기 테마 로드 실행
initTheme();
document.addEventListener('DOMContentLoaded', initTheme);

// ESC 및 바깥 클릭 시 테마 드롭다운 닫기
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && isThemeDropdownOpen) {
    closeThemeDropdown();
  }
});

document.addEventListener('click', (e) => {
  const menu = document.getElementById('themeDropdown');
  const btn = document.getElementById('themeToggleBtn');
  if (isThemeDropdownOpen && menu && !menu.contains(e.target) && !btn?.contains(e.target)) {
    closeThemeDropdown();
  }
});

// ================= 전역 상태 변수 =================
let player = null;
let isPlayerReady = false;
let currentVideoId = '';
let currentSegments = [];
let currentVideoTitle = '';
let timeUpdateInterval = null;

// YouTube IFrame API 준비 완료 콜백
function onYouTubeIframeAPIReady() {
  console.log("YouTube IFrame API Ready");
}

function initPlayer(videoId) {
  if (player) {
    player.loadVideoById(videoId);
    return;
  }

  player = new YT.Player('player', {
    videoId: videoId,
    playerVars: {
      autoplay: 1,
      controls: 0,
      autohide: 1,
      enablejsapi: 1,
      disablekb: 1,
      fs: 0,
      iv_load_policy: 3,
      modestbranding: 1,
      playsinline: 1,
      rel: 0
    },
    events: {
      'onReady': onPlayerReady,
      'onStateChange': onPlayerStateChange
    }
  });
}

function onPlayerReady(event) {
  isPlayerReady = true;
  event.target.playVideo();
  startTimeTracker();
}

function onPlayerStateChange(event) {
  const playIcon = document.getElementById('playIcon');
  if (event.data === YT.PlayerState.PLAYING) {
    if (playIcon) playIcon.className = "fa-solid fa-pause text-xs";
  } else {
    if (playIcon) playIcon.className = "fa-solid fa-play text-xs";
  }
}

function startTimeTracker() {
  if (timeUpdateInterval) clearInterval(timeUpdateInterval);
  timeUpdateInterval = setInterval(() => {
    if (!player || !isPlayerReady) return;
    try {
      const current = Math.floor(player.getCurrentTime() || 0);
      const total = Math.floor(player.getDuration() || 0);
      const timeDisp = document.getElementById('timeDisplay');
      if (timeDisp) timeDisp.textContent = `${formatTime(current)} / ${formatTime(total)}`;
      
      // 커스텀 프로그레스바 너비 업데이트
      const progressBar = document.getElementById('progressBar');
      if (progressBar && total > 0) {
        const pct = Math.min(100, Math.max(0, (current / total) * 100));
        progressBar.style.width = `${pct}%`;
      }

      highlightCurrentSegment(current);
    } catch (e) {}
  }, 300);
}

function formatTime(secs) {
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
}

// 재생 및 일시정지 토글
function togglePlay() {
  if (!player || !isPlayerReady) return;
  const state = player.getPlayerState();
  if (state === YT.PlayerState.PLAYING) {
    player.pauseVideo();
  } else {
    player.playVideo();
  }
}

// 프로그레스바 클릭 시 원하는 위치로 이동 (Seek)
function handleProgressClick(e) {
  if (!player || !isPlayerReady) return;
  const container = document.getElementById('progressBarContainer');
  const rect = container.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const width = rect.width;
  const total = player.getDuration() || 0;
  if (width > 0 && total > 0) {
    const seekTime = (clickX / width) * total;
    player.seekTo(seekTime, true);
    player.playVideo();
  }
}

// 전체화면 토글
function toggleFullscreen() {
  const container = document.getElementById('videoContainer');
  const icon = document.getElementById('fullscreenIcon');
  if (!document.fullscreenElement) {
    if (container.requestFullscreen) {
      container.requestFullscreen();
    } else if (container.webkitRequestFullscreen) {
      container.webkitRequestFullscreen();
    }
    if (icon) icon.className = "fa-solid fa-compress text-xs";
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
    if (icon) icon.className = "fa-solid fa-expand text-xs";
  }
}

// ================= 자막(CC) 토글 로직 =================
let isCaptionsOn = false;
function toggleCaptions() {
  if (!player || !isPlayerReady) return;
  isCaptionsOn = !isCaptionsOn;
  const btn = document.getElementById('captionsBtn');
  try {
    if (isCaptionsOn) {
      player.loadModule("captions");
      player.setOption("captions", "track", {"languageCode": "ko"});
      if (btn) {
        btn.classList.add('theme-primary-bg');
        btn.classList.remove('text-yt-subtext', 'bg-white/10');
      }
    } else {
      player.setOption("captions", "track", {});
      player.unloadModule("captions");
      if (btn) {
        btn.classList.remove('theme-primary-bg');
        btn.classList.add('text-yt-subtext', 'bg-white/10');
      }
    }
  } catch (e) {
    console.log("Captions toggle error:", e);
  }
}

// ================= 톱니바퀴 설정 메뉴 로직 (ESC 및 바깥 클릭 닫기) =================
let isSettingsOpen = false;

function toggleSettingsMenu(event) {
  if (event) event.stopPropagation();
  const menu = document.getElementById('settingsMenu');
  const gear = document.getElementById('gearIcon');
  isSettingsOpen = !isSettingsOpen;
  
  if (isSettingsOpen) {
    if (menu) menu.classList.remove('hidden');
    if (gear) gear.classList.add('rotate-90', 'theme-primary-text');
    showOverlayBar();
    if (overlayTimeout) clearTimeout(overlayTimeout);
  } else {
    closeSettingsMenu();
  }
}

function closeSettingsMenu() {
  const menu = document.getElementById('settingsMenu');
  const gear = document.getElementById('gearIcon');
  if (menu) menu.classList.add('hidden');
  if (gear) gear.classList.remove('rotate-90', 'theme-primary-text');
  isSettingsOpen = false;
  scheduleHideOverlay();
}

function setSpeed(rate) {
  if (player && isPlayerReady) {
    player.setPlaybackRate(rate);
  }
  const label = document.getElementById('currentSpeedLabel');
  if (label) label.textContent = `${rate}x ${rate === 1.0 ? '(기본)' : ''}`;
  
  document.querySelectorAll('.speed-btn').forEach(btn => {
    if (btn.textContent.trim() === `${rate}x`) {
      btn.className = "speed-btn py-1.5 rounded-lg theme-primary-bg font-bold text-[11px] transition-colors shadow-sm";
    } else {
      btn.className = "speed-btn py-1.5 rounded-lg bg-yt-hover hover:bg-yt-border text-yt-text text-[11px] font-medium transition-colors";
    }
  });
}

function toggleLoop(isLoop) {
  if (player && isPlayerReady) {
    player.setLoop(isLoop);
  }
}

// ESC 및 바깥 클릭 리스너
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && isSettingsOpen) {
    closeSettingsMenu();
  }
});

document.addEventListener('click', (e) => {
  const menu = document.getElementById('settingsMenu');
  const btn = document.getElementById('settingsBtn');
  if (isSettingsOpen && menu && !menu.contains(e.target) && !btn.contains(e.target)) {
    closeSettingsMenu();
  }
});

// ================= 비디오 화면 호버 시에만 오버레이 표시 로직 =================
let overlayTimeout = null;
let isMouseInsideBar = false;

function showOverlayBar() {
  const bar = document.getElementById('videoOverlayBar');
  if (bar) {
    bar.classList.remove('opacity-0', 'pointer-events-none', 'translate-y-2');
    bar.classList.add('opacity-100', 'pointer-events-auto', 'translate-y-0');
  }
}

function hideOverlayBar() {
  if (isSettingsOpen || isMouseInsideBar) return;
  const bar = document.getElementById('videoOverlayBar');
  if (bar) {
    bar.classList.remove('opacity-100', 'pointer-events-auto', 'translate-y-0');
    bar.classList.add('opacity-0', 'pointer-events-none', 'translate-y-2');
  }
}

function handleVideoMouseEnter() {
  showOverlayBar();
  scheduleHideOverlay();
}

function handleVideoMouseMove() {
  showOverlayBar();
  scheduleHideOverlay();
}

function handleVideoMouseLeave() {
  if (!isMouseInsideBar && !isSettingsOpen) {
    hideOverlayBar();
  }
}

function handleBarMouseEnter() {
  isMouseInsideBar = true;
  showOverlayBar();
  if (overlayTimeout) clearTimeout(overlayTimeout);
}

function handleBarMouseLeave() {
  isMouseInsideBar = false;
  scheduleHideOverlay();
}

function scheduleHideOverlay() {
  if (overlayTimeout) clearTimeout(overlayTimeout);
  overlayTimeout = setTimeout(() => {
    if (!isSettingsOpen && !isMouseInsideBar) {
      hideOverlayBar();
    }
  }, 2500);
}

// ================= 타임라인 스크립트 사이드바 열기/닫기 토글 =================
let isSidebarOpen = true;
function toggleSidebar() {
  isSidebarOpen = !isSidebarOpen;
  const sidebarCol = document.getElementById('sidebarCol');
  const videoCol = document.getElementById('videoCol');
  const toggleBtn = document.getElementById('toggleSidebarBtn');
  const toggleText = document.getElementById('toggleSidebarText');
  const toggleIcon = document.getElementById('toggleSidebarIcon');

  if (isSidebarOpen) {
    sidebarCol.classList.remove('hidden');
    videoCol.className = "lg:col-span-8 space-y-4 transition-all duration-300";
    toggleBtn.className = "px-3 py-2 rounded-xl theme-primary-bg flex items-center space-x-1.5 transition-colors cursor-pointer text-xs font-semibold shadow-sm";
    toggleText.textContent = "스크립트창 닫기";
    toggleIcon.className = "fa-solid fa-list-ul";
  } else {
    sidebarCol.classList.add('hidden');
    videoCol.className = "lg:col-span-12 space-y-4 transition-all duration-300";
    toggleBtn.className = "px-3 py-2 rounded-xl bg-yt-hover hover:bg-yt-border text-yt-text border border-yt-border flex items-center space-x-1.5 transition-colors cursor-pointer text-xs font-semibold";
    toggleText.textContent = "스크립트창 열기";
    toggleIcon.className = "fa-solid fa-bars-staggered";
  }
}

// 특정 시간으로 점프하고 영상 자동 재생
function jumpToTime(seconds) {
  if (!player || !isPlayerReady) return;
  player.seekTo(seconds, true);
  player.playVideo();
  console.log(`Jump to: ${seconds}s and auto-playing`);
}

// 클립보드 붙여넣기
async function pasteUrl() {
  try {
    const text = await navigator.clipboard.readText();
    if (text) document.getElementById('urlInput').value = text;
  } catch (err) {
    alert('클립보드 접근 권한이 필요합니다.');
  }
}

// 샘플 링크 로드
function loadSampleVideo(sampleUrl) {
  document.getElementById('urlInput').value = sampleUrl;
  handleSearch(new Event('submit'));
}

// 검색 실행 (오디오 다운로드 + STT 전사 파이프라인)
async function handleSearch(e) {
  if (e) e.preventDefault();
  const url = document.getElementById('urlInput').value.trim();
  if (!url) return;

  const statusAlert = document.getElementById('statusAlert');
  const emptyPlaceholder = document.getElementById('emptyPlaceholder');
  const contentLayout = document.getElementById('contentLayout');
  const searchBtn = document.getElementById('searchBtn');

  searchBtn.disabled = true;
  statusAlert.classList.remove('hidden');

  try {
    const res = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "영상 분석에 실패했습니다.");

    emptyPlaceholder.classList.add('hidden');
    contentLayout.classList.remove('hidden');

    currentVideoId = data.video.id;
    currentVideoTitle = data.video.title;
    currentSegments = data.segments || [];

    // 영상 메타 세팅
    document.getElementById('videoTitle').textContent = data.video.title;
    document.getElementById('videoUploader').innerHTML = `<i class="fa-regular fa-circle-user mr-1.5 theme-primary-text"></i>${data.video.uploader}`;
    document.getElementById('videoDuration').textContent = `재생시간: ${data.video.duration_str}`;

    // 유튜브 플레이어 생성/로드
    initPlayer(currentVideoId);

    // 스크립트 렌더링
    renderTranscript(currentSegments, data.from_cache);

    statusAlert.classList.add('hidden');
  } catch (err) {
    alert(err.message);
    statusAlert.classList.add('hidden');
  } finally {
    searchBtn.disabled = false;
  }
}

// 트랜스크립트 렌더링
function renderTranscript(segments, fromCache = false) {
  const container = document.getElementById('transcriptList');
  const countEl = document.getElementById('segmentCount');
  
  if (fromCache) {
    countEl.innerHTML = `<span class="text-emerald-500 mr-1.5"><i class="fa-solid fa-bolt"></i> CSV 캐시 로드</span>${segments.length}개`;
  } else {
    countEl.textContent = `${segments.length}개`;
  }

  if (!segments || segments.length === 0) {
    container.innerHTML = '<div class="text-center py-8 text-yt-subtext text-xs">추출된 발화 내용이 없습니다.</div>';
    return;
  }

  container.innerHTML = segments.map((seg, idx) => `
    <div 
      id="seg-${seg.start}" 
      onclick="jumpToTime(${seg.start})" 
      class="segment-item p-2.5 rounded-xl hover:bg-yt-hover transition-all cursor-pointer flex items-start space-x-2.5 group border border-transparent hover:border-yt-border"
    >
      <span class="px-2 py-0.5 rounded theme-time-badge font-mono text-xs font-semibold select-none flex-shrink-0 transition-colors">
        ${seg.time}
      </span>
      <p class="text-xs text-yt-text leading-relaxed line-clamp-3">
        ${escapeHtml(seg.text)}
      </p>
    </div>
  `).join('');
}

// 현재 시간에 맞춘 세그먼트 하이라이트
let lastHighlightedSec = -1;
function highlightCurrentSegment(currentSec) {
  if (!currentSegments || currentSegments.length === 0) return;
  let targetSec = -1;
  for (let i = 0; i < currentSegments.length; i++) {
    if (currentSegments[i].start <= currentSec) {
      targetSec = currentSegments[i].start;
    } else {
      break;
    }
  }

  if (targetSec !== -1 && targetSec !== lastHighlightedSec) {
    document.querySelectorAll('.segment-item').forEach(el => el.classList.remove('theme-active-seg'));
    const el = document.getElementById(`seg-${targetSec}`);
    if (el) {
      el.classList.add('theme-active-seg');
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    lastHighlightedSec = targetSec;
  }
}

// 탭 전환
function switchTab(tab) {
  const tabScriptBtn = document.getElementById('tabScriptBtn');
  const tabQaBtn = document.getElementById('tabQaBtn');
  const scriptPanel = document.getElementById('scriptPanel');
  const qaPanel = document.getElementById('qaPanel');

  if (tab === 'script') {
    tabScriptBtn.className = "flex-1 py-3 text-xs font-bold border-b-2 theme-primary-border theme-primary-text flex items-center justify-center space-x-1.5 transition-colors cursor-pointer";
    tabQaBtn.className = "flex-1 py-3 text-xs font-semibold border-b-2 border-transparent text-yt-subtext hover:text-yt-text flex items-center justify-center space-x-1.5 transition-colors cursor-pointer";
    scriptPanel.classList.remove('hidden');
    qaPanel.classList.add('hidden');
  } else {
    tabQaBtn.className = "flex-1 py-3 text-xs font-bold border-b-2 theme-primary-border theme-primary-text flex items-center justify-center space-x-1.5 transition-colors cursor-pointer";
    tabScriptBtn.className = "flex-1 py-3 text-xs font-semibold border-b-2 border-transparent text-yt-subtext hover:text-yt-text flex items-center justify-center space-x-1.5 transition-colors cursor-pointer";
    qaPanel.classList.remove('hidden');
    scriptPanel.classList.add('hidden');
  }
}

// Gemini 3.8 Flash Q&A 전송 처리
async function handleQaSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('qaInput');
  const query = input.value.trim();
  if (!query || currentSegments.length === 0) return;

  const chatContainer = document.getElementById('chatMessages');
  const sendBtn = document.getElementById('qaSendBtn');

  // 사용자 말풍선 추가
  chatContainer.innerHTML += `
    <div class="flex justify-end">
      <div class="theme-chat-user p-3 rounded-xl text-xs max-w-[85%] leading-relaxed shadow">
        ${escapeHtml(query)}
      </div>
    </div>
  `;
  input.value = '';
  sendBtn.disabled = true;
  chatContainer.scrollTop = chatContainer.scrollHeight;

  // AI 로딩 말풍선
  const loadingId = 'loading-' + Date.now();
  chatContainer.innerHTML += `
    <div id="${loadingId}" class="flex justify-start">
      <div class="theme-chat-ai border text-yt-subtext p-3 rounded-xl text-xs flex items-center space-x-2">
        <div class="w-3.5 h-3.5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
        <span>Gemini 3.8 Flash가 생각 중입니다...</span>
      </div>
    </div>
  `;
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    const res = await fetch('/api/qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        video_title: currentVideoTitle,
        segments: currentSegments
      })
    });

    const data = await res.json();
    document.getElementById(loadingId).remove();

    if (!res.ok) throw new Error(data.detail || "답변을 가져오지 못했습니다.");

    const answer = data.data.answer;
    const jumpSec = data.data.jump_sec;

    // [MM:SS] 타임스탬프를 클릭 가능한 점프 버튼으로 파싱
    const formattedAnswer = answer.replace(/\[?(\d{1,2}):(\d{2})\]?/g, (match, m, s) => {
      const sec = parseInt(m) * 60 + parseInt(s);
      return `<button onclick="jumpToTime(${sec})" class="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded theme-time-badge font-mono text-[11px] font-semibold cursor-pointer select-none">▶ ${m}:${s}</button>`;
    });

    chatContainer.innerHTML += `
      <div class="flex justify-start">
        <div class="theme-chat-ai border text-yt-text p-3 rounded-xl text-xs max-w-[90%] leading-relaxed space-y-2 shadow-sm">
          <div class="flex items-center space-x-1.5 text-emerald-500 font-semibold text-[11px] mb-1">
            <i class="fa-solid fa-wand-magic-sparkles"></i>
            <span>Gemini 3.8 Flash</span>
          </div>
          <div>${formattedAnswer}</div>
          ${jumpSec !== null ? `
            <div class="pt-2 border-t border-yt-border">
              <button onclick="jumpToTime(${jumpSec})" class="w-full py-1.5 theme-primary-bg rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors cursor-pointer shadow-sm">
                <i class="fa-solid fa-play text-[10px]"></i>
                <span>해당 장면으로 바로 이동 (${data.data.jump_time})</span>
              </button>
            </div>
          ` : ''}
        </div>
      </div>
    `;
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // 만약 AI가 시간대를 찾았다면 바로 이동 안내
    if (jumpSec !== null) {
      jumpToTime(jumpSec);
    }

  } catch (err) {
    document.getElementById(loadingId).remove();
    chatContainer.innerHTML += `
      <div class="flex justify-start">
        <div class="bg-red-950/60 border border-red-800 text-red-300 p-3 rounded-xl text-xs max-w-[85%]">
          ❌ 오류: ${escapeHtml(err.message)}
        </div>
      </div>
    `;
  } finally {
    sendBtn.disabled = false;
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
