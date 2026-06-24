/* ===================================================

   HAIST Issue Tracker — Frontend Logic

   v2.0 | 완전 무료 아키텍처 대시보드

   =================================================== */



// ──�const MOCK_DATA = [];

// ─── State Management ───

let appState = {

  theme: localStorage.getItem('haist-theme') || 'light',

  mode: 'live', // 'demo' or 'live'

  data: [],

  filteredData: [],

  activeCategory: 'hot',

  activeSource: null,

  searchQuery: '',

  sortBy: 'score',

  currentPage: 1,

  pageSize: 6,

  bookmarks: JSON.parse(localStorage.getItem('haist-bookmarks') || '[]')

};



// ─── Google Sheets ID ───

// .env에 입력된 값이 없으면 우선 빈 문자열로 설정하며 사용자가 실시간 모드 선택 시 입력받도록 지원

let GOOGLE_SHEETS_ID = "1aNG0wUWxGfkxrqPutZpPVj5GO8qE0ImX368IkyYxuZ4"; 



// ─── DOM Elements ───

const elements = {

  themeToggle: document.getElementById('themeToggle'),

  themeIcon: document.getElementById('themeIcon'),

  categoryNav: document.getElementById('categoryNav'),



  searchInput: document.getElementById('searchInput'),

  sortSelect: document.getElementById('sortSelect'),

  issuesList: document.getElementById('issuesList'),

  hotIssuesGrid: document.getElementById('hotIssuesGrid'),

  loadMoreBtn: document.getElementById('loadMoreBtn'),

  listCount: document.getElementById('listCount'),

  contentTitle: document.getElementById('contentTitle'),

  mobileMenuBtn: document.getElementById('mobileMenuBtn'),

  sidebar: document.getElementById('sidebar'),

  sidebarOverlay: document.getElementById('sidebarOverlay'),

  kpiTotal: document.getElementById('kpiTotal'),

  kpiAcademic: document.getElementById('kpiAcademic'),

  kpiHot: document.getElementById('kpiHot'),

  kpiBookmarks: document.getElementById('kpiBookmarks'),

  heroSubDate: document.getElementById('heroSubDate'),

  syncStatus: document.getElementById('syncStatus'),

  lastUpdated: document.getElementById('lastUpdated')

};



// ─── Init App ───

document.addEventListener('DOMContentLoaded', () => {

  setTheme(appState.theme);

  setMode(appState.mode);

  setupEventListeners();

  updateDateInfo();

});



// ─── Date Formatter ───

function updateDateInfo() {

  const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };

  const todayStr = new Date().toLocaleDateString('ko-KR', options);

  elements.heroSubDate.innerText = `${todayStr} — 글로벌 12개 소스 자동 수집 · AI 분석`;

}



// ─── Theme Manager ───

function setTheme(theme) {

  document.documentElement.setAttribute('data-theme', theme);

  appState.theme = theme;

  localStorage.setItem('haist-theme', theme);

  

  if (theme === 'dark') {

    elements.themeIcon.className = 'ti ti-moon';

  } else {

    elements.themeIcon.className = 'ti ti-sun';

  }

}



// ─── Mode Manager (Demo / Live Sheets) ───

function setMode(mode) {

  appState.mode = mode;

  

  if (mode === 'demo') {

    elements.syncStatus.innerText = "데모 시뮬레이션";

    elements.lastUpdated.innerText = "마지막 업데이트: 방금 전";

    appState.data = [...MOCK_DATA];

    processAndRender();

  } else {

    elements.syncStatus.innerText = "구글 시트 연동 중...";

    loadLiveSheetsData();

  }

}



// ─── Load Live Google Sheets Data ───

async function loadLiveSheetsData() {

  if (!GOOGLE_SHEETS_ID) {

    const sheetIdInput = prompt("구글 스프레드시트 ID를 입력해 주세요 (주소창의 /d/ 와 /edit 사이 문자열):");

    if (!sheetIdInput) {

      alert("시트 ID가 필요합니다. 데모 모드로 돌아갑니다.");

      setMode('demo');

      return;

    }

    GOOGLE_SHEETS_ID = sheetIdInput;

  }

  

  try {

    // Google Sheets Visualization API (JSON Endpoint) - CORS 없이 퍼블릭 시트 읽기

    const url = `https://docs.google.com/spreadsheets/d/${GOOGLE_SHEETS_ID}/gviz/tq?tqx=out:json&sheet=issues`;

    const response = await fetch(url);

    const text = await response.text();

    

    // JSONP 형태의 응답을 JSON 객체로 파싱

    const jsonStr = text.match(/google\.visualization\.Query\.setResponse\(([\s\S\w\W]*)\)/);

    if (!jsonStr || jsonStr.length < 2) {

      throw new Error("올바른 Google Sheets 응답 형태가 아닙니다. 시트가 '웹에 게시' 상태인지 확인하세요.");

    }

    

    const json = JSON.parse(jsonStr[1]);

    const rows = json.table.rows;

    

    // Rows 파싱

    const parsedData = rows.map((row, idx) => {

      const cells = row.c;

      // 시트 컬럼 순서: id, date, title, source, url, category, summary, ai_reason, content_score, trend_score, youtube_title, thumbnail_text, internal_title

      const getCellVal = (cellIndex) => cells[cellIndex] ? cells[cellIndex].v : null;

      

      const score = parseInt(getCellVal(8)) || 50;

      const trend = parseInt(getCellVal(9)) || 0;

      

      return {

        id: getCellVal(0) || `id-${idx}`,

        date: getCellVal(1) || new Date().toISOString(),

        title: getCellVal(2) || "제목 없음",

        source: getCellVal(3) || "네이버 뉴스",

        url: getCellVal(4) || "#",

        category: getCellVal(5) || "일반",

        summary: getCellVal(6) || "",

        ai_reason: getCellVal(7) || "",

        content_score: score,

        trend_score: trend,

        is_hot: score >= 80,

        is_academic: ["PubMed", "arXiv"].includes(getCellVal(3)),

        youtube_title: getCellVal(10) || "",

        thumbnail_text: getCellVal(11) || "",

        internal_title: getCellVal(12) || ""

      };

    });

    

    appState.data = parsedData;

    elements.syncStatus.innerText = "실시간 구글 시트 연동 완료";

    elements.lastUpdated.innerText = `마지막 업데이트: ${new Date().toLocaleTimeString('ko-KR')}`;

    processAndRender();

    

  } catch (error) {

    console.error("Live Data Load Error:", error);

    alert("구글 시트 로드 중 에러가 발생했습니다. 시트 설정(웹 게시 등)을 확인하세요.\n" + error.message);

    setMode('demo');

  }

}



// ─── Event Listeners ───

function setupEventListeners() {

  // Theme Toggle

  elements.themeToggle.addEventListener('click', () => {

    setTheme(appState.theme === 'light' ? 'dark' : 'light');

  });

  

  // Mode Selection

  

  // Category Filter Navigation

  elements.categoryNav.addEventListener('click', (e) => {

    const navItem = e.target.closest('.nav-item');

    if (!navItem) return;

    

    document.querySelectorAll('#categoryNav .nav-item').forEach(item => item.classList.remove('active'));

    navItem.classList.add('active');

    

    appState.activeCategory = navItem.dataset.category;

    appState.activeSource = null; // 카테고리 클릭 시 소스 필터 초기화

    document.querySelectorAll('.source-nav .nav-item').forEach(item => item.classList.remove('active'));

    

    appState.currentPage = 1;

    processAndRender();

    closeMobileSidebar();

  });

  

  // Source Filter Navigation
  document.querySelectorAll('.source-nav').forEach(nav => {
    nav.addEventListener('click', (e) => {
      const navItem = e.target.closest('.nav-item');
      if (!navItem) return;
      document.querySelectorAll('.source-nav .nav-item').forEach(item => item.classList.remove('active'));
      navItem.classList.add('active');
      appState.activeSource = navItem.dataset.source;
      appState.activeCategory = 'all';
      document.querySelectorAll('#categoryNav .nav-item').forEach(item => item.classList.remove('active'));
      appState.currentPage = 1;
      processAndRender();
      closeMobileSidebar();
    });
  });

  

  // Search Input

  elements.searchInput.addEventListener('input', (e) => {

    appState.searchQuery = e.target.value.toLowerCase();

    appState.currentPage = 1;

    processAndRender();

  });

  

  // Sort Dropdown

  elements.sortSelect.addEventListener('change', (e) => {

    appState.sortBy = e.target.value;

    processAndRender();

  });

  

  // Load More Button

  elements.loadMoreBtn.addEventListener('click', () => {

    appState.currentPage++;

    renderFeedList(true); // append mode

  });

  

  // Mobile Sidebar Toggle

  elements.mobileMenuBtn.addEventListener('click', () => {

    elements.sidebar.classList.add('mobile-open');

    elements.sidebarOverlay.classList.add('active');

  });

  

  elements.sidebarOverlay.addEventListener('click', closeMobileSidebar);

}



function closeMobileSidebar() {

  elements.sidebar.classList.remove('mobile-open');

  elements.sidebarOverlay.classList.remove('active');

}



// ─── Data Pipeline (Filter, Sort, Render) ───

function processAndRender() {

  filterData();

  sortData();

  updateKPIs();

  updateNavCounts();

  renderHotIssues();

  renderFeedList(false); // start fresh

}



function filterData() {

  let temp = [...appState.data];

  

  // 1. Category Filter

  if (appState.activeCategory !== 'all') {

    if (appState.activeCategory === 'hot') {

      temp = temp.filter(item => item.is_hot);

    } else if (appState.activeCategory === 'academic') {

      temp = temp.filter(item => item.is_academic);

    } else {

      temp = temp.filter(item => item.category === appState.activeCategory);

    }

  }

  

  // 2. Source Filter

  if (appState.activeSource) {

    temp = temp.filter(item => item.source === appState.activeSource);

  }

  

  // 3. Search Query Filter

  if (appState.searchQuery) {

    const q = appState.searchQuery;

    temp = temp.filter(item => 

      item.title.toLowerCase().includes(q) || 

      item.summary.toLowerCase().includes(q) || 

      item.category.toLowerCase().includes(q) ||

      item.source.toLowerCase().includes(q)

    );

  }

  

  appState.filteredData = temp;

}



function sortData() {

  if (appState.sortBy === 'score') {

    appState.filteredData.sort((a, b) => b.content_score - a.content_score);

  } else if (appState.sortBy === 'trend') {

    appState.filteredData.sort((a, b) => b.trend_score - a.trend_score);

  } else if (appState.sortBy === 'latest') {

    appState.filteredData.sort((a, b) => new Date(b.date) - new Date(a.date));

  }

}



// ─── Update Metrics ───

function updateKPIs() {

  const total = appState.data.length;

  const academic = appState.data.filter(item => item.is_academic).length;

  const hot = appState.data.filter(item => item.is_hot).length;

  const bookmarks = appState.bookmarks.length;

  

  elements.kpiTotal.innerText = total;

  elements.kpiAcademic.innerText = academic;

  elements.kpiHot.innerText = hot;

  elements.kpiBookmarks.innerText = bookmarks;

}



function updateNavCounts() {

  document.getElementById('countAll').innerText = appState.data.length;

  document.getElementById('countHot').innerText = appState.data.filter(item => item.is_hot).length;

  document.getElementById('countAcademic').innerText = appState.data.filter(item => item.is_academic).length;

  

  // 카테고리별 개수 업데이트

  const categories = ["확대수술", "발기부전", "보형물 수술", "여유증", "음경 보톡스", "정관수술", "전립선", "조루"];

  categories.forEach(cat => {

    const navItem = document.querySelector(`#categoryNav .nav-item[data-category="${cat}"]`);

    if (navItem) {

      const count = appState.data.filter(item => item.category === cat).length;

      const countSpan = navItem.querySelector('.nav-count');

      if (countSpan) countSpan.innerText = count;

    }

  });

}



// ─── Render Hot Issues (AI Picks) ───

function renderHotIssues() {

  const hotItems = appState.data.filter(item => item.is_hot).slice(0, 3);

  

  if (hotItems.length === 0) {

    elements.hotIssuesGrid.innerHTML = `

      <div class="empty-state" style="grid-column: 1/-1;">

        <i class="ti ti-flame-off"></i>

        <h3>AI 선정 핫이슈가 없습니다.</h3>

        <p>콘텐츠 추천 기준 점수(80점)를 만족하는 수집 항목이 부족합니다.</p>

      </div>`;

    return;

  }

  

  let html = "";

  

  // 1. 메인 핫이슈 (#1)

  const m = hotItems[0];

  const relativeTime = getRelativeTime(m.date);

  

  const mYoutubeHtml = m.youtube_title ? `

    <div class="youtube-plan-box" style="margin-top: 8px; background: rgba(255, 255, 255, 0.08); border-left: 3px solid #ff4b5a;">

      <div class="youtube-plan-title" style="color: #ff4b5a;"><i class="ti ti-brand-youtube"></i> 유튜브 기획안</div>

      <div class="youtube-plan-item" style="color: rgba(255,255,255,0.85);"><strong style="color: #fff;">영상 제목:</strong> ${m.youtube_title}</div>

      <div class="youtube-plan-item" style="color: rgba(255,255,255,0.85);"><strong style="color: #fff;">썸네일 카피:</strong> ${m.thumbnail_text}</div>

      <div class="youtube-plan-item" style="color: rgba(255,255,255,0.85);"><strong style="color: #fff;">기획 의도:</strong> ${m.internal_title}</div>

    </div>

  ` : '';



  html += `

    <div class="hot-main" onclick="window.open('${m.url}', '_blank')">

      <div class="hot-rank">

        <span class="rank-num">#1 핫이슈</span>

        <span>· ${m.source} · ${relativeTime}</span>

      </div>

      <span class="hot-main-tag">${m.category} ${m.is_academic ? '· 학술논문' : ''}</span>

      <h3 class="hot-main-title">${m.title}</h3>

      <p class="hot-main-summary">${m.summary}</p>

      

      <div class="ai-reason-box">

        <div class="ai-reason-label"><i class="ti ti-robot"></i> AI 선정 이유</div>

        <p>${m.ai_reason}</p>

      </div>



      ${mYoutubeHtml}

      

      <div class="hot-main-footer" style="margin-top: 14px;">

        <div class="hot-main-meta">콘텐츠 가치 점수</div>

        <div class="content-score">

          <div class="score-bar-wrap"><div class="score-bar" style="width:${m.content_score}%;"></div></div>

          <span class="score-pct">${m.content_score}점</span>

        </div>

      </div>

    </div>

  `;

  

  // 2. 서브 핫이슈들 (#2, #3)

  for (let i = 1; i < 3; i++) {

    const s = hotItems[i];

    if (!s) {

      // 3개 미만인 경우 빈 슬롯 렌더링 생략

      continue;

    }

    const scoreClass = s.content_score >= 90 ? 's-high' : 's-mid';

    const sTime = getRelativeTime(s.date);

    

    const sYoutubeHtml = s.youtube_title ? `

      <div class="youtube-plan-box" style="margin-top: 8px;">

        <div class="youtube-plan-title"><i class="ti ti-brand-youtube"></i> 유튜브 기획안</div>

        <div class="youtube-plan-item" style="font-size: 10.5px;"><strong>영상 제목:</strong> ${s.youtube_title}</div>

        <div class="youtube-plan-item" style="font-size: 10.5px;"><strong>썸네일 카피:</strong> ${s.thumbnail_text}</div>

        <div class="youtube-plan-item" style="font-size: 10.5px;"><strong>기획 의도:</strong> ${s.internal_title}</div>

      </div>

    ` : '';



    html += `

      <div class="hot-sub" onclick="window.open('${s.url}', '_blank')">

        <div class="hot-sub-rank">

          <span class="rank-badge r${i+1}">#${i+1}</span>

          <span class="hot-sub-source">${s.source} · ${sTime}</span>

        </div>

        <div>

          <span class="hot-sub-tag">${s.category}</span>

        </div>

        <h4 class="hot-sub-title">${s.title}</h4>

        <p class="hot-sub-reason">${s.summary.substring(0, 85)}...</p>

        

        <div class="ai-reason-box" style="margin-top:auto;">

          <div class="ai-reason-label"><i class="ti ti-robot"></i> AI 한줄평</div>

          <p style="font-size: 10.5px;">${s.ai_reason}</p>

        </div>



        ${sYoutubeHtml}



        <div class="hot-sub-footer">

          <span class="sub-score ${scoreClass}">추천도 ${s.content_score}점</span>

          <span class="hot-sub-time">트렌드 ${s.trend_score}%</span>

        </div>

      </div>

    `;

  }

  

  elements.hotIssuesGrid.innerHTML = html;

}



// ─── Render Main Issue Feed List ───

function renderFeedList(append = false) {

  const listContainer = elements.issuesList;

  

  if (appState.filteredData.length === 0) {

    listContainer.innerHTML = `

      <div class="empty-state">

        <i class="ti ti-search-off"></i>

        <h3>검색 또는 필터 결과가 없습니다.</h3>

        <p>다른 키워드나 필터 옵션을 선택해 보세요.</p>

      </div>`;

    elements.listCount.innerText = "0건";

    elements.loadMoreBtn.style.display = "none";

    return;

  }

  

  elements.listCount.innerText = `${appState.filteredData.length}건`;

  

  // 페이지네이션 처리

  const startIndex = 0;

  const endIndex = appState.currentPage * appState.pageSize;

  const visibleItems = appState.filteredData.slice(startIndex, endIndex);

  

  let html = "";

  visibleItems.forEach(item => {

    const isBookmarked = appState.bookmarks.some(b => b.id === item.id);

    const scoreColorClass = item.content_score >= 85 ? 'hot' : (item.content_score >= 70 ? 'warm' : '');

    const trendColorClass = item.trend_score >= 80 ? 'tc-high' : (item.trend_score >= 60 ? 'tc-mid' : 'tc-low');

    

    const youtubeHtml = item.youtube_title ? `

      <div class="youtube-plan-box" style="margin-top: 8px;">

        <div class="youtube-plan-title"><i class="ti ti-brand-youtube"></i> 유튜브 기획안</div>

        <div class="youtube-plan-item"><strong>영상 제목:</strong> ${item.youtube_title}</div>

        <div class="youtube-plan-item"><strong>썸네일 카피:</strong> ${item.thumbnail_text}</div>

        <div class="youtube-plan-item"><strong>기획 의도:</strong> ${item.internal_title}</div>

      </div>

    ` : '';



    html += `

      <div class="card" id="card-${item.id}">

        <div>

          <div class="card-meta">

            <span class="src-badge s-${getSrcCode(item.source)}">${item.source}</span>

            ${item.is_academic ? '<span class="academic-tag">학술 논문</span>' : ''}

            <span class="cat-tag">${item.category}</span>

          </div>

          <h3 class="card-title" onclick="window.open('${item.url}', '_blank')">${item.title}</h3>

          <p class="card-summary">${item.summary}</p>

          

          <!-- AI Comments inline inside list -->

          <div class="ai-reason-box" style="margin-top: 8px; border-left: 3px solid var(--color-ai);">

            <div class="ai-reason-label" style="margin-bottom: 2px;"><i class="ti ti-robot"></i> AI 요약평</div>

            <p style="font-size: 11px; color: var(--text-secondary);">${item.ai_reason}</p>

          </div>



          ${youtubeHtml}



          <div class="card-footer">

            <span class="card-time">${getRelativeTime(item.date)}</span>

            <span class="trend-chip ${trendColorClass}">급상승 +${item.trend_score}%</span>

            ${item.is_hot ? '<span class="trend-chip tc-ai">AI 추천 #1</span>' : ''}

          </div>

        </div>

        

        <div class="card-actions">

          <div class="score-ring ${scoreColorClass}" data-tooltip="콘텐츠화 가치 점수">

            <span class="score-n ${scoreColorClass}">${item.content_score}</span>

            <span class="score-l">VAL</span>

          </div>

          <button class="bm-btn ${isBookmarked ? 'bookmarked' : ''}" 

                  onclick="toggleBookmark('${item.id}')" 

                  aria-label="북마크" 

                  data-tooltip="${isBookmarked ? '북마크 제거' : '소재로 저장'}">

            <i class="ti ${isBookmarked ? 'ti-bookmark-filled' : 'ti-bookmark'}"></i>

          </button>

        </div>

      </div>

    `;

  });

  

  listContainer.innerHTML = html;

  

  // 더 보기 버튼 표시 여부

  if (endIndex >= appState.filteredData.length) {

    elements.loadMoreBtn.style.display = "none";

  } else {

    elements.loadMoreBtn.style.display = "inline-block";

  }

}



// ─── Bookmark Manager ───

window.toggleBookmark = function(itemId) {

  const itemIndex = appState.bookmarks.findIndex(b => b.id === itemId);

  const matchedItem = appState.data.find(d => d.id === itemId);

  

  if (!matchedItem) return;

  

  if (itemIndex > -1) {

    // 북마크 삭제

    appState.bookmarks.splice(itemIndex, 1);

  } else {

    // 북마크 추가

    appState.bookmarks.push(matchedItem);

  }

  

  // 로컬스토리지 저장

  localStorage.setItem('haist-bookmarks', JSON.stringify(appState.bookmarks));

  

  // 리렌더링 및 통계 반영

  updateKPIs();

  

  // 카드 내 북마크 아이콘 실시간 업데이트

  const card = document.getElementById(`card-${itemId}`);

  if (card) {

    const btn = card.querySelector('.bm-btn');

    const isNowBookmarked = itemIndex === -1;

    btn.classList.toggle('bookmarked', isNowBookmarked);

    

    const icon = btn.querySelector('i');

    icon.className = isNowBookmarked ? 'ti ti-bookmark-filled' : 'ti ti-bookmark';

    btn.setAttribute('data-tooltip', isNowBookmarked ? '북마크 제거' : '소재로 저장');

  }

};



// ─── Helpers ───

function getSrcCode(source) {
  const map = {
    "BBC Health": "bbc",
    "PubMed": "pub",
    "네이버 뉴스": "nav",
    "arXiv": "arx",
    "Reddit Urology": "red",
    "Reddit Sex": "red",
    "Reddit Sexual Health": "red",
    "Reddit Tinder": "red",
    "Reddit STD": "red",
    "Reddit Sex Education": "red",
    "CNN Health": "bbc",
    "NYT Health": "yon",
    "헬스조선": "pub",
    "Yahoo Japan Life": "yon",
    "연합뉴스 헬스": "yon"
  };
  return map[source] || "nav";
}



function getRelativeTime(dateStr) {

  const parsed = new Date(dateStr);

  const now = new Date();

  const diffMs = now - parsed;

  const diffMin = Math.floor(diffMs / 1000 / 60);

  

  if (diffMin < 1) return "방금 전";

  if (diffMin < 60) return `${diffMin}분 전`;

  

  const diffHours = Math.floor(diffMin / 60);

  if (diffHours < 24) return `${diffHours}시간 전`;

  

  const diffDays = Math.floor(diffHours / 24);

  if (diffDays === 1) return "어제";

  return `${diffDays}일 전`;

}

