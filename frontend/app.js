// SmartTask AI - Frontend Logic
let currentFilterStatus = '';
let currentFilterCategory = '';
let currentFilterPriority = '';
let currentSearchTerm = '';
let searchDebounceTimeout = null;

// Chart references
let dailyChartCategory = null;
let weeklyChartTrend = null;
let monthlyChartCategory = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  // Telegram WebApp initialization
  if (window.Telegram && window.Telegram.WebApp) {
    try {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    } catch (e) {
      console.log("Telegram WebApp init error:", e);
    }
  }
  initDates();
  initIcons();
  loadCategories();
  loadOverviewStats();
  loadTasks();
  checkSettingsStatus();
  initNotifications();
});

function initIcons() {
  if (window.lucide) {
    lucide.createIcons();
  }
}

function getTodayString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function initDates() {
  const today = getTodayString();
  const dateInputDaily = document.getElementById('daily-report-date');
  const dateInputWeekly = document.getElementById('weekly-report-date');
  const dateInputFitness = document.getElementById('fitness-date-picker');
  const monthSelect = document.getElementById('monthly-report-month');
  const yearSelect = document.getElementById('monthly-report-year');
  const formDueDate = document.getElementById('form-due-date');

  if (dateInputDaily) dateInputDaily.value = today;
  if (dateInputWeekly) dateInputWeekly.value = today;
  if (dateInputFitness) dateInputFitness.value = today;
  if (formDueDate) formDueDate.value = today;

  const now = new Date();
  if (monthSelect) monthSelect.value = now.getMonth() + 1;
  if (yearSelect) yearSelect.value = now.getFullYear();

  // Top header formatted date display in Uzbek
  const displayEl = document.getElementById('current-date-display');
  if (displayEl) {
    const weekdays = ['Yakshanba', 'Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba'];
    const months = ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentyabr', 'Oktyabr', 'Noyabr', 'Dekabr'];
    const wName = weekdays[now.getDay()];
    const mName = months[now.getMonth()];
    displayEl.textContent = `${wName}, ${now.getDate()}-${mName}, ${now.getFullYear()}`;
  }
}

// ----------------------------------------------------
// TAB NAVIGATION
// ----------------------------------------------------
function switchTab(tabName) {
  const tabs = ['tasks', 'fitness', 'daily', 'weekly', 'monthly', 'coach'];
  
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const content = document.getElementById(`tab-content-${t}`);
    if (!btn || !content) return;

    if (t === tabName) {
      btn.className = 'tab-btn px-4 py-2.5 rounded-lg text-sm font-semibold flex items-center space-x-2 bg-indigo-50 text-indigo-700 shadow-xs';
      content.classList.remove('hidden');
    } else {
      btn.className = 'tab-btn px-4 py-2.5 rounded-lg text-sm font-semibold flex items-center space-x-2 text-slate-600 hover:bg-slate-50';
      content.classList.add('hidden');
    }
  });

  initIcons();

  if (tabName === 'tasks') {
    loadTasks();
    loadOverviewStats();
  } else if (tabName === 'fitness') {
    loadFitnessData();
  } else if (tabName === 'daily') {
    loadDailyReport();
  } else if (tabName === 'weekly') {
    loadWeeklyReport();
  } else if (tabName === 'monthly') {
    loadMonthlyReport();
  }
}

// ----------------------------------------------------
// OVERVIEW STATS
// ----------------------------------------------------
async function loadOverviewStats() {
  try {
    const res = await fetch('/api/stats/overview');
    if (!res.ok) return;
    const data = await res.json();
    
    const today = data.today;
    document.getElementById('metric-today-total').textContent = today.total_tasks || 0;
    document.getElementById('metric-today-completed').textContent = today.completed_tasks || 0;
    document.getElementById('metric-today-pending').textContent = (today.in_progress_tasks + today.pending_tasks) || 0;
    document.getElementById('metric-today-rate').textContent = `${today.completion_rate || 0}%`;
  } catch (err) {
    console.error('Stats load error:', err);
  }
}

// ----------------------------------------------------
// TASK BOARD & CRUD
// ----------------------------------------------------
function setFilter(type, val) {
  if (type === 'status') {
    currentFilterStatus = val;
    document.querySelectorAll('.filter-status-btn').forEach(btn => {
      if (btn.getAttribute('data-status') === val) {
        btn.className = 'filter-status-btn px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white';
      } else {
        btn.className = 'filter-status-btn px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200';
      }
    });
  }
  applyFilters();
}

function debounceSearch() {
  clearTimeout(searchDebounceTimeout);
  searchDebounceTimeout = setTimeout(() => {
    currentSearchTerm = document.getElementById('search-input').value.trim();
    loadTasks();
  }, 300);
}

function applyFilters() {
  currentFilterCategory = document.getElementById('filter-category').value;
  currentFilterPriority = document.getElementById('filter-priority').value;
  loadTasks();
}

async function loadTasks() {
  const container = document.getElementById('task-list-container');
  try {
    let url = '/api/tasks?';
    const params = new URLSearchParams();
    
    if (currentFilterStatus === 'today') {
      params.append('date_filter', getTodayString());
    } else if (currentFilterStatus) {
      params.append('status', currentFilterStatus);
    }

    if (currentFilterCategory) params.append('category', currentFilterCategory);
    if (currentFilterPriority) params.append('priority', currentFilterPriority);
    if (currentSearchTerm) params.append('search', currentSearchTerm);

    const res = await fetch(url + params.toString());
    const data = await res.json();
    const tasks = data.tasks || [];

    if (tasks.length === 0) {
      container.innerHTML = `
        <div class="bg-white rounded-2xl border border-dashed border-slate-200 p-12 text-center">
          <div class="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-500 flex items-center justify-center mx-auto mb-3">
            <i data-lucide="inbox" class="w-6 h-6"></i>
          </div>
          <h4 class="text-sm font-bold text-slate-700 mb-1">Hech qanday vazifa topilmadi</h4>
          <p class="text-xs text-slate-400 max-w-sm mx-auto mb-4">Ushbu parametrlar bo'yicha vazifa yo'q yoki barcha ishlar bajarilgan!</p>
          <button onclick="openTaskModal()" class="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl">
            <i data-lucide="plus" class="w-3.5 h-3.5 mr-1.5"></i>
            Yangi vazifa qo'shish
          </button>
        </div>
      `;
      initIcons();
      return;
    }

    let html = '';
    tasks.forEach(task => {
      const isDone = task.status === 'Bajarildi';
      
      // Priority badge
      let prioBadge = '';
      if (task.priority === 'Yuqori') {
        prioBadge = '<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-50 text-rose-600 border border-rose-100">Yuqori</span>';
      } else if (task.priority === 'O\'rta') {
        prioBadge = '<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-600 border border-amber-100">O\'rta</span>';
      } else {
        prioBadge = '<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">Past</span>';
      }

      // Category icon & name
      let catIcon = 'tag';
      if (task.category === 'Ish') catIcon = 'briefcase';
      else if (task.category === 'O\'qish') catIcon = 'book-open';
      else if (task.category === 'Salomatlik') catIcon = 'activity';
      else if (task.category === 'Shaxsiy') catIcon = 'user';

      const timeText = task.due_time ? `<span class="flex items-center text-slate-400 text-xs ml-2"><i data-lucide="clock" class="w-3 h-3 mr-1"></i>${task.due_time}</span>` : '';
      const overdueClass = (!isDone && task.due_date < getTodayString()) ? 'text-rose-500 font-semibold' : 'text-slate-500';

      html += `
        <div class="task-card bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between gap-3 ${isDone ? 'opacity-70 bg-slate-50/70' : ''}">
          <!-- Checkbox and Title -->
          <div class="flex items-start space-x-3.5 flex-1 min-w-0">
            <button 
              onclick="handleTaskToggle(${task.id})" 
              class="mt-0.5 w-5 h-5 rounded-lg border flex items-center justify-center transition shrink-0 ${isDone ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-slate-300 hover:border-indigo-500 text-transparent'}"
              title="${isDone ? 'Qayta ochish' : 'Bajarildi deb belgilash'}"
            >
              <i data-lucide="check" class="w-3.5 h-3.5 stroke-[3]"></i>
            </button>

            <div class="min-w-0 flex-1">
              <div class="flex items-center space-x-2 flex-wrap gap-y-1">
                <span class="text-sm font-semibold text-slate-800 ${isDone ? 'line-through text-slate-400' : ''}">${escapeHtml(task.title)}</span>
                ${prioBadge}
                <span class="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-600 flex items-center">
                  <i data-lucide="${catIcon}" class="w-3 h-3 mr-1"></i>
                  ${task.category || 'Ish'}
                </span>
              </div>
              
              ${task.description ? `<p class="text-xs text-slate-500 mt-1 line-clamp-1">${escapeHtml(task.description)}</p>` : ''}

              <div class="flex items-center mt-1.5 text-xs text-slate-400">
                <span class="flex items-center ${overdueClass}">
                  <i data-lucide="calendar" class="w-3 h-3 mr-1"></i>
                  ${task.due_date}
                </span>
                ${timeText}
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center space-x-1 shrink-0">
            ${task.due_date ? `
            <button onclick="addToGoogleCalendar(${task.id})" class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition" title="Google Calendar-ga qo'shish">
              <i data-lucide="calendar-plus" class="w-4 h-4"></i>
            </button>` : ''}
            <button onclick="openTaskModal(${task.id})" class="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-50 rounded-lg transition" title="Tahrirlash">
              <i data-lucide="edit-2" class="w-4 h-4"></i>
            </button>
            <button onclick="handleDeleteTask(${task.id})" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-50 rounded-lg transition" title="O'chirish">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          </div>
        </div>
      `;
    });

    container.innerHTML = html;
    initIcons();
  } catch (err) {
    container.innerHTML = `<div class="p-4 bg-rose-50 text-rose-600 rounded-xl text-xs font-semibold">Xatolik yuz berdi: ${err.message}</div>`;
  }
}

async function handleTaskToggle(taskId) {
  try {
    const res = await fetch(`/api/tasks/${taskId}/toggle`, { method: 'PATCH' });
    if (res.ok) {
      loadTasks();
      loadOverviewStats();
    }
  } catch (err) {
    console.error('Toggle error:', err);
  }
}

async function handleDeleteTask(taskId) {
  if (!confirm("Haqiqatan ham bu vazifani o'chirmoqchimisiz?")) return;
  try {
    const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
    if (res.ok) {
      loadTasks();
      loadOverviewStats();
    }
  } catch (err) {
    console.error('Delete error:', err);
  }
}

// ----------------------------------------------------
// NLP NATURAL LANGUAGE TASK SUBMISSION
// ----------------------------------------------------
async function handleNlpTaskSubmit() {
  const input = document.getElementById('nlp-task-input');
  const feedback = document.getElementById('nlp-feedback');
  const btn = document.getElementById('nlp-submit-btn');
  const text = input.value.trim();
  
  if (!text) return;

  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin mr-1"></i> Tahlil...`;
  initIcons();

  try {
    // 1. Parse text using AI agent
    const parseRes = await fetch('/api/ai/parse-task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const parseData = await parseRes.json();
    const parsed = parseData.parsed;

    // 2. Automatically save the parsed task
    const saveRes = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(parsed)
    });

    if (saveRes.ok) {
      input.value = '';
      feedback.className = 'text-xs mt-2 text-emerald-300 flex items-center space-x-1';
      feedback.innerHTML = `
        <i data-lucide="check" class="w-3.5 h-3.5"></i>
        <span>Vazifa AI tomonidan qo'shildi: <strong>"${escapeHtml(parsed.title)}"</strong> | Sana: ${parsed.due_date} | Ustuvorlik: ${parsed.priority}</span>
      `;
      feedback.classList.remove('hidden');
      setTimeout(() => feedback.classList.add('hidden'), 5000);

      loadTasks();
      loadOverviewStats();
    }
  } catch (err) {
    feedback.className = 'text-xs mt-2 text-rose-300';
    feedback.textContent = `Xatolik: ${err.message}`;
    feedback.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="arrow-right" class="w-4 h-4"></i> <span>Qo'shish</span>`;
    initIcons();
  }
}

// ----------------------------------------------------
// ADD / EDIT TASK MODAL
// ----------------------------------------------------
async function openTaskModal(taskId = null) {
  const modal = document.getElementById('task-modal');
  const modalTitle = document.getElementById('modal-task-title');
  const form = document.getElementById('task-form');

  form.reset();
  document.getElementById('form-due-date').value = getTodayString();
  document.getElementById('form-task-id').value = '';

  if (taskId) {
    modalTitle.textContent = "Vazifani Tahrirlash";
    try {
      const res = await fetch(`/api/tasks/${taskId}`);
      const data = await res.json();
      const task = data.task;
      document.getElementById('form-task-id').value = task.id;
      document.getElementById('form-title').value = task.title;
      document.getElementById('form-desc').value = task.description || '';
      document.getElementById('form-category').value = task.category || 'Ish';
      document.getElementById('form-priority').value = task.priority || "O'rta";
      document.getElementById('form-due-date').value = task.due_date;
      document.getElementById('form-due-time').value = task.due_time || '';
    } catch (e) {
      console.error(e);
    }
  } else {
    modalTitle.textContent = "Yangi Vazifa Qo'shish";
  }

  modal.classList.remove('hidden');
  initIcons();
}

function closeTaskModal() {
  document.getElementById('task-modal').classList.add('hidden');
}

async function handleTaskFormSubmit(event) {
  event.preventDefault();
  const taskId = document.getElementById('form-task-id').value;
  const payload = {
    title: document.getElementById('form-title').value.trim(),
    description: document.getElementById('form-desc').value.trim(),
    category: document.getElementById('form-category').value,
    priority: document.getElementById('form-priority').value,
    due_date: document.getElementById('form-due-date').value,
    due_time: document.getElementById('form-due-time').value
  };

  try {
    let res;
    if (taskId) {
      res = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeTaskModal();
      loadTasks();
      loadOverviewStats();
    }
  } catch (err) {
    alert("Xatolik: " + err.message);
  }
}

// ----------------------------------------------------
// DAILY REPORT GENERATOR & VIEWER
// ----------------------------------------------------
async function loadDailyReport() {
  const container = document.getElementById('daily-report-content');
  const targetDate = document.getElementById('daily-report-date').value || getTodayString();
  
  container.innerHTML = `
    <div class="p-12 text-center bg-white rounded-2xl border border-slate-200">
      <i data-lucide="loader" class="w-8 h-8 animate-spin mx-auto text-indigo-600 mb-3"></i>
      <p class="text-sm font-semibold text-slate-700">Kunlik tahliliy hisobot tayyorlanmoqda...</p>
    </div>
  `;
  initIcons();

  try {
    const res = await fetch(`/api/reports/daily?date=${targetDate}`);
    const data = await res.json();
    const stats = data.stats;
    const rate = stats.completion_rate;

    // Convert Markdown AI analysis to HTML
    const aiHtml = marked.parse(data.ai_analysis || '');

    // Render Completed Tasks & Pending Tasks List
    const completedTasks = stats.tasks.filter(t => t.status === 'Bajarildi');
    const pendingTasks = stats.tasks.filter(t => t.status !== 'Bajarildi');

    let completedListHtml = completedTasks.map(t => 
      `<li class="flex items-center text-xs text-slate-700 py-1">
        <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-500 mr-2 shrink-0"></i>
        <span class="font-medium">${escapeHtml(t.title)}</span>
        <span class="ml-auto text-[10px] text-slate-400">${t.category}</span>
       </li>`
    ).join('') || '<p class="text-xs text-slate-400 italic">Hali bajarilgan vazifa yo\'q</p>';

    let pendingListHtml = pendingTasks.map(t => 
      `<li class="flex items-center text-xs text-slate-700 py-1">
        <i data-lucide="circle" class="w-3.5 h-3.5 text-amber-500 mr-2 shrink-0"></i>
        <span class="font-medium">${escapeHtml(t.title)}</span>
        <span class="ml-auto text-[10px] font-bold ${t.priority === 'Yuqori' ? 'text-rose-600' : 'text-slate-400'}">${t.priority}</span>
       </li>`
    ).join('') || '<p class="text-xs text-emerald-600 font-medium">Barcha vazifalar to\'liq yakunlandi!</p>';

    container.innerHTML = `
      <!-- Report Header Banner -->
      <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-600">Kunlik Hisobot</span>
          <h2 class="text-xl font-extrabold text-slate-900 mt-2">${targetDate} sanasi hisoboti</h2>
          <p class="text-xs text-slate-500">Unumdorlik bahosi: <strong class="text-slate-700">${data.grade}</strong></p>
        </div>

        <div class="flex items-center space-x-6">
          <div class="text-right">
            <span class="text-xs text-slate-400 block font-medium">Natija</span>
            <span class="text-3xl font-black text-indigo-600">${rate}%</span>
          </div>
          <div class="h-12 w-px bg-slate-200"></div>
          <div>
            <span class="text-xs text-slate-400 block font-medium">Ko'rsatkich</span>
            <span class="text-sm font-bold text-slate-700">${stats.completed_tasks} / ${stats.total_tasks} vazifa</span>
          </div>
        </div>
      </div>

      <!-- Charts & Breakdown Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Chart: Categories -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col items-center">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 w-full">Kategoriyalar Balansi</h4>
          <div class="w-48 h-48 relative">
            <canvas id="daily-category-chart"></canvas>
          </div>
        </div>

        <!-- Completed Tasks Box -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-600 mb-3 flex items-center">
            <i data-lucide="check-check" class="w-4 h-4 mr-1.5"></i>
            Bajarilgan Ishlar (${completedTasks.length})
          </h4>
          <ul class="divide-y divide-slate-100 max-h-52 overflow-y-auto">
            ${completedListHtml}
          </ul>
        </div>

        <!-- Pending Tasks Box -->
        <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <h4 class="text-xs font-bold uppercase tracking-wider text-amber-600 mb-3 flex items-center">
            <i data-lucide="clock" class="w-4 h-4 mr-1.5"></i>
            Bajarilmagan / Kutilayotgan (${pendingTasks.length})
          </h4>
          <ul class="divide-y divide-slate-100 max-h-52 overflow-y-auto">
            ${pendingListHtml}
          </ul>
        </div>
      </div>

      <!-- AI Deep Insights Section -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 relative overflow-hidden">
        <div class="flex items-center space-x-2.5 pb-4 mb-4 border-b border-slate-100">
          <div class="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center">
            <i data-lucide="sparkles" class="w-4 h-4"></i>
          </div>
          <h3 class="text-sm font-bold text-slate-800">AI Unumdorlik Tahlili va Tavsiyalar</h3>
        </div>
        <div class="ai-markdown-content text-sm text-slate-700">
          ${aiHtml}
        </div>
      </div>
    `;

    initIcons();
    renderDailyChart(stats.by_category);
  } catch (err) {
    container.innerHTML = `<div class="p-6 bg-rose-50 text-rose-600 rounded-xl text-xs font-semibold">Hisobot yuklashda xatolik: ${err.message}</div>`;
  }
}

function renderDailyChart(byCategory) {
  const ctx = document.getElementById('daily-category-chart');
  if (!ctx) return;

  if (dailyChartCategory) dailyChartCategory.destroy();

  const labels = Object.keys(byCategory || {});
  const data = labels.map(l => byCategory[l].total);

  if (labels.length === 0) {
    labels.push("Vazifalar yo'q");
    data.push(1);
  }

  dailyChartCategory = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 10, font: { size: 10 } }
        }
      },
      cutout: '70%'
    }
  });
}

// ----------------------------------------------------
// WEEKLY REPORT GENERATOR & VIEWER
// ----------------------------------------------------
async function loadWeeklyReport() {
  const container = document.getElementById('weekly-report-content');
  const endDate = document.getElementById('weekly-report-date').value || getTodayString();

  container.innerHTML = `
    <div class="p-12 text-center bg-white rounded-2xl border border-slate-200">
      <i data-lucide="loader" class="w-8 h-8 animate-spin mx-auto text-indigo-600 mb-3"></i>
      <p class="text-sm font-semibold text-slate-700">7 kunlik chuqur tahliliy hisobot tayyorlanmoqda...</p>
    </div>
  `;
  initIcons();

  try {
    const res = await fetch(`/api/reports/weekly?end_date=${endDate}`);
    const data = await res.json();
    const stats = data.stats;
    const aiHtml = marked.parse(data.ai_analysis || '');

    container.innerHTML = `
      <!-- Weekly Header -->
      <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-purple-50 text-purple-600">Haftalik Tahlil</span>
          <h2 class="text-xl font-extrabold text-slate-900 mt-2">${data.start_date} — ${data.end_date} oralig'i</h2>
          <p class="text-xs text-slate-500">Oxirgi 7 kunlik ish maromi va tendensiyalar</p>
        </div>

        <div class="flex items-center space-x-6">
          <div>
            <span class="text-xs text-slate-400 block font-medium">Haftalik daraja</span>
            <span class="text-3xl font-black text-purple-600">${stats.completion_rate}%</span>
          </div>
          <div class="h-12 w-px bg-slate-200"></div>
          <div>
            <span class="text-xs text-slate-400 block font-medium">Jami bajarildi</span>
            <span class="text-sm font-bold text-slate-700">${stats.completed_tasks} / ${stats.total_tasks} ta</span>
          </div>
        </div>
      </div>

      <!-- Weekly Trend Bar Chart -->
      <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">Kunlik Reja va Bajarilish Dinamikasi</h4>
        <div class="h-64 w-full">
          <canvas id="weekly-trend-chart"></canvas>
        </div>
      </div>

      <!-- Weekly AI Insights -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xs p-6">
        <div class="flex items-center space-x-2.5 pb-4 mb-4 border-b border-slate-100">
          <div class="w-7 h-7 rounded-lg bg-purple-600 text-white flex items-center justify-center">
            <i data-lucide="sparkles" class="w-4 h-4"></i>
          </div>
          <h3 class="text-sm font-bold text-slate-800">AI Haftalik Strategik Xulosasi</h3>
        </div>
        <div class="ai-markdown-content text-sm text-slate-700">
          ${aiHtml}
        </div>
      </div>
    `;

    initIcons();
    renderWeeklyTrendChart(stats.by_date);
  } catch (err) {
    container.innerHTML = `<div class="p-6 bg-rose-50 text-rose-600 rounded-xl text-xs font-semibold">Xatolik: ${err.message}</div>`;
  }
}

function renderWeeklyTrendChart(byDate) {
  const ctx = document.getElementById('weekly-trend-chart');
  if (!ctx) return;

  if (weeklyChartTrend) weeklyChartTrend.destroy();

  const labels = Object.keys(byDate || {}).sort();
  const totalData = labels.map(d => byDate[d].total);
  const doneData = labels.map(d => byDate[d].completed);

  weeklyChartTrend = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Bajarilgan vazifalar',
          data: doneData,
          backgroundColor: '#4f46e5',
          borderRadius: 6
        },
        {
          label: 'Jami rejalashtirilgan',
          data: totalData,
          backgroundColor: '#e0e7ff',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1 }
        }
      },
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
      }
    }
  });
}

// ----------------------------------------------------
// MONTHLY REPORT GENERATOR & VIEWER
// ----------------------------------------------------
async function loadMonthlyReport() {
  const container = document.getElementById('monthly-report-content');
  const year = document.getElementById('monthly-report-year').value;
  const month = document.getElementById('monthly-report-month').value;

  container.innerHTML = `
    <div class="p-12 text-center bg-white rounded-2xl border border-slate-200">
      <i data-lucide="loader" class="w-8 h-8 animate-spin mx-auto text-indigo-600 mb-3"></i>
      <p class="text-sm font-semibold text-slate-700">Oylik strategik hisobot tayyorlanmoqda...</p>
    </div>
  `;
  initIcons();

  try {
    const res = await fetch(`/api/reports/monthly?year=${year}&month=${month}`);
    const data = await res.json();
    const stats = data.stats;
    const aiHtml = marked.parse(data.ai_analysis || '');

    container.innerHTML = `
      <!-- Monthly Header -->
      <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-50 text-amber-700">Oylik Strategik Hisobot</span>
          <h2 class="text-xl font-extrabold text-slate-900 mt-2">${data.year}-yil ${data.month_name} oyi natijalari</h2>
          <p class="text-xs text-slate-500">${data.start_date} dan ${data.end_date} gacha bo'lgan davr</p>
        </div>

        <div class="flex items-center space-x-6">
          <div>
            <span class="text-xs text-slate-400 block font-medium">Oylik Samaradorlik</span>
            <span class="text-3xl font-black text-amber-600">${stats.completion_rate}%</span>
          </div>
          <div class="h-12 w-px bg-slate-200"></div>
          <div>
            <span class="text-xs text-slate-400 block font-medium">Jami ishlar</span>
            <span class="text-sm font-bold text-slate-700">${stats.completed_tasks} / ${stats.total_tasks} ta</span>
          </div>
        </div>
      </div>

      <!-- Categories breakdown cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        ${Object.keys(stats.by_category || {}).map(cat => {
          const item = stats.by_category[cat];
          const pct = item.total > 0 ? Math.round(item.completed / item.total * 100) : 0;
          return `
            <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <span class="text-xs font-semibold text-slate-500">${cat}</span>
              <h4 class="text-lg font-bold text-slate-800 mt-1">${item.completed} / ${item.total}</h4>
              <div class="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
                <div class="bg-indigo-600 h-1.5 rounded-full" style="width: ${pct}%"></div>
              </div>
              <span class="text-[10px] text-slate-400 mt-1 block">${pct}% bajarildi</span>
            </div>
          `;
        }).join('')}
      </div>

      <!-- AI Monthly Insights -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-xs p-6">
        <div class="flex items-center space-x-2.5 pb-4 mb-4 border-b border-slate-100">
          <div class="w-7 h-7 rounded-lg bg-amber-500 text-white flex items-center justify-center">
            <i data-lucide="award" class="w-4 h-4"></i>
          </div>
          <h3 class="text-sm font-bold text-slate-800">Oylik Rivojlanish Xulosasi & AI Tavsiyalari</h3>
        </div>
        <div class="ai-markdown-content text-sm text-slate-700">
          ${aiHtml}
        </div>
      </div>
    `;

    initIcons();
  } catch (err) {
    container.innerHTML = `<div class="p-6 bg-rose-50 text-rose-600 rounded-xl text-xs font-semibold">Xatolik: ${err.message}</div>`;
  }
}

// ----------------------------------------------------
// AI COACH CHAT
// ----------------------------------------------------
function askPreset(promptText) {
  document.getElementById('coach-input').value = promptText;
  handleCoachSend();
}

async function handleCoachSend() {
  const input = document.getElementById('coach-input');
  const sendBtn = document.getElementById('coach-send-btn');
  const historyContainer = document.getElementById('coach-messages');
  const message = input.value.trim();

  if (!message) return;

  // Append user message
  const userBubble = `
    <div class="flex items-start justify-end space-x-3">
      <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-none p-3 text-xs leading-relaxed max-w-lg shadow-xs">
        ${escapeHtml(message)}
      </div>
    </div>
  `;
  historyContainer.insertAdjacentHTML('beforeend', userBubble);
  input.value = '';

  // Append thinking bubble
  const loadingId = 'loading-' + Date.now();
  const loadingBubble = `
    <div id="${loadingId}" class="flex items-start space-x-3 max-w-xl">
      <div class="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
        <i data-lucide="bot" class="w-4 h-4"></i>
      </div>
      <div class="bg-slate-100 text-slate-600 rounded-2xl rounded-tl-none p-3 text-xs flex items-center space-x-1.5">
        <span class="inline-block w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce"></span>
        <span class="inline-block w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce [animation-delay:0.2s]"></span>
        <span class="inline-block w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce [animation-delay:0.4s]"></span>
      </div>
    </div>
  `;
  historyContainer.insertAdjacentHTML('beforeend', loadingBubble);
  historyContainer.scrollTop = historyContainer.scrollHeight;
  initIcons();

  try {
    const res = await fetch('/api/ai/coach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    const replyHtml = marked.parse(data.reply || '');

    const loaderEl = document.getElementById(loadingId);
    if (loaderEl) loaderEl.remove();

    const aiBubble = `
      <div class="flex items-start space-x-3 max-w-xl">
        <div class="w-8 h-8 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
          <i data-lucide="bot" class="w-4 h-4"></i>
        </div>
        <div class="bg-slate-100 text-slate-800 rounded-2xl rounded-tl-none p-3.5 text-xs leading-relaxed ai-markdown-content shadow-xs">
          ${replyHtml}
        </div>
      </div>
    `;
    historyContainer.insertAdjacentHTML('beforeend', aiBubble);
    historyContainer.scrollTop = historyContainer.scrollHeight;
    initIcons();
  } catch (err) {
    const loaderEl = document.getElementById(loadingId);
    if (loaderEl) loaderEl.remove();
    alert("Xatolik: " + err.message);
  }
}

// ----------------------------------------------------
// SETTINGS MODAL & API KEY
// ----------------------------------------------------
async function checkSettingsStatus() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    const statusEl = document.getElementById('api-key-status');
    if (statusEl) {
      if (data.gemini_api_key_set) {
        statusEl.innerHTML = `<span class="text-emerald-600 font-semibold">✓ API kalit sozlangan (${data.gemini_api_key_masked})</span>`;
      } else {
        statusEl.textContent = "Hali API kalit kiritilmagan (ixtiyoriy).";
      }
    }

    const tgStatusEl = document.getElementById('telegram-token-status');
    if (tgStatusEl) {
      if (data.telegram_bot_token_set) {
        tgStatusEl.innerHTML = `<span class="text-emerald-600 font-semibold">✓ Bot tokeni sozlangan (${data.telegram_bot_token_masked})</span>`;
      } else {
        tgStatusEl.textContent = "Hali bot tokeni kiritilmagan.";
      }
    }

    const webAppUrlEl = document.getElementById('setting-webapp-url');
    if (webAppUrlEl && data.web_app_url) {
      webAppUrlEl.value = data.web_app_url;
    }
  } catch (e) {
    console.error(e);
  }
}

function openSettingsModal() {
  document.getElementById('settings-modal').classList.remove('hidden');
  checkSettingsStatus();
  initIcons();
}

function closeSettingsModal() {
  document.getElementById('settings-modal').classList.add('hidden');
}

async function saveApiKeySetting() {
  const keyInput = document.getElementById('setting-api-key');
  const tgInput = document.getElementById('setting-telegram-token');
  const webAppUrlInput = document.getElementById('setting-webapp-url');
  const geminiVal = keyInput ? keyInput.value.trim() : '';
  const tgVal = tgInput ? tgInput.value.trim() : '';
  const webAppUrlVal = webAppUrlInput ? webAppUrlInput.value.trim() : '';

  if (!geminiVal && !tgVal && !webAppUrlVal) {
    alert("Iltimos, o'zgartirish kiriting yoki oynani yoping");
    return;
  }

  try {
    if (geminiVal) {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'gemini_api_key', value: geminiVal })
      });
      keyInput.value = '';
    }

    if (tgVal) {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'telegram_bot_token', value: tgVal })
      });
      tgInput.value = '';
    }

    if (webAppUrlVal) {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'web_app_url', value: webAppUrlVal })
      });
    }

    alert("Sozlamalar muvaffaqiyatli saqlandi!");
    closeSettingsModal();
    checkSettingsStatus();
  } catch (err) {
    alert("Xatolik: " + err.message);
  }
}

// ====================================================
// CALENDAR INTEGRATION & SYNC
// ====================================================
function openCalendarModal() {
  const modal = document.getElementById('calendar-modal');
  if (!modal) return;
  modal.classList.remove('hidden');

  const subInput = document.getElementById('calendar-subscribe-url');
  if (subInput) {
    const origin = window.location.origin;
    subInput.value = `${origin}/api/calendar/tasks.ics`;
  }
  initIcons();
}

function closeCalendarModal() {
  const modal = document.getElementById('calendar-modal');
  if (modal) modal.classList.add('hidden');
}

function copyCalendarSubscribeUrl() {
  const subInput = document.getElementById('calendar-subscribe-url');
  if (!subInput) return;
  navigator.clipboard.writeText(subInput.value).then(() => {
    alert("Jonli kalendar havolasi nusxalandi! 📋\nEndi uni Google Calendar yoki iPhone Kalendaringizga obuna qilib qo'yishingiz mumkin.");
  }).catch(() => {
    subInput.select();
    document.execCommand('copy');
    alert("Havola nusxalandi!");
  });
}

async function addToGoogleCalendar(taskId) {
  try {
    const res = await fetch(`/api/calendar/task/${taskId}/google-url`);
    if (!res.ok) throw new Error("Vazifa topilmadi");
    const data = await res.json();
    if (data.google_calendar_url) {
      window.open(data.google_calendar_url, '_blank');
    }
  } catch (err) {
    alert("Google Calendar havolasini ochishda xatolik: " + err.message);
  }
}

// ====================================================
// KATEGORIYALARNI BOSHQARISH (CUSTOM CATEGORIES)
// ====================================================
let appCategories = [];

async function loadCategories() {
  try {
    const res = await fetch('/api/categories');
    if (!res.ok) return;
    const data = await res.json();
    appCategories = data.categories || [];

    // 1. Filter dropdown yangilash
    const filterSelect = document.getElementById('filter-category');
    if (filterSelect) {
      const prevVal = filterSelect.value;
      let filterHtml = '<option value="">Barcha Kategoriyalar</option>';
      appCategories.forEach(cat => {
        filterHtml += `<option value="${escapeHtml(cat.name)}">${escapeHtml(cat.name)}</option>`;
      });
      filterSelect.innerHTML = filterHtml;
      if (prevVal && appCategories.some(c => c.name === prevVal)) {
        filterSelect.value = prevVal;
      }
    }

    // 2. Vazifa qo'shish formasidagi tanlov
    const formSelect = document.getElementById('form-category');
    if (formSelect) {
      const prevFormVal = formSelect.value;
      let formHtml = '';
      appCategories.forEach(cat => {
        formHtml += `<option value="${escapeHtml(cat.name)}">${escapeHtml(cat.name)}</option>`;
      });
      formSelect.innerHTML = formHtml;
      if (prevFormVal && appCategories.some(c => c.name === prevFormVal)) {
        formSelect.value = prevFormVal;
      } else if (appCategories.length > 0) {
        formSelect.value = appCategories[0].name;
      }
    }

    // 3. Kategoriyalar modalidagi ro'yxat
    const listBox = document.getElementById('categories-list-box');
    if (listBox) {
      if (appCategories.length === 0) {
        listBox.innerHTML = '<p class="text-xs text-slate-400 py-3 text-center">Hech qanday kategoriya mavjud emas</p>';
      } else {
        listBox.innerHTML = appCategories.map(cat => `
          <div class="flex items-center justify-between py-2 px-2 hover:bg-slate-50 rounded-xl transition">
            <div class="flex items-center space-x-2.5">
              <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <i data-lucide="${cat.icon || 'tag'}" class="w-4 h-4"></i>
              </div>
              <div>
                <span class="text-xs font-semibold text-slate-800">${escapeHtml(cat.name)}</span>
              </div>
            </div>
            <button onclick="handleDeleteCategory(${cat.id}, '${escapeHtml(cat.name)}')" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition" title="Kategoriyani o'chirish">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          </div>
        `).join('');
      }
      initIcons();
    }
  } catch (err) {
    console.error('Kategoriyalarni yuklashda xatolik:', err);
  }
}

function openCategoriesModal() {
  loadCategories();
  document.getElementById('categories-modal').classList.remove('hidden');
  initIcons();
}

function closeCategoriesModal() {
  document.getElementById('categories-modal').classList.add('hidden');
}

async function handleAddCategorySubmit(event) {
  event.preventDefault();
  const nameInput = document.getElementById('new-category-name');
  const iconInput = document.getElementById('new-category-icon');
  const name = nameInput.value.trim();
  const icon = iconInput.value || 'tag';

  if (!name) return;

  try {
    const res = await fetch('/api/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, icon, color: 'indigo' })
    });

    if (res.ok) {
      nameInput.value = '';
      await loadCategories();
    } else {
      const err = await res.json();
      alert("Xatolik: " + (err.detail || "Kategoriya qo'shib bo'lmadi"));
    }
  } catch (err) {
    alert("Xatolik: " + err.message);
  }
}

async function handleDeleteCategory(id, name) {
  if (!confirm(`"${name}" kategoriyasini ro'yxatdan o'chirishni xohlaysizmi?`)) return;

  try {
    const res = await fetch(`/api/categories/${id}`, {
      method: 'DELETE'
    });

    if (res.ok) {
      await loadCategories();
    } else {
      const err = await res.json();
      alert("Xatolik: " + (err.detail || "Kategoriyani o'chirib bo'lmadi"));
    }
  } catch (err) {
    alert("Xatolik: " + err.message);
  }
}

// Helper: Escape HTML
function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ====================================================
// FITNES & KALORIYA (FITNESS & CALORIE TRACKER) LOGIC
// ====================================================
async function loadFitnessData() {
  const dateInput = document.getElementById('fitness-date-picker');
  const targetDate = dateInput ? (dateInput.value || getTodayString()) : getTodayString();

  try {
    const res = await fetch(`/api/fitness/summary?date=${targetDate}`);
    if (!res.ok) return;
    const data = await res.json();
    const profile = data.profile || {};

    // 1. Update KPI numbers
    document.getElementById('fit-consumed-cal').textContent = `${data.consumed_calories} kcal`;
    document.getElementById('fit-burned-cal').textContent = `${data.burned_calories} kcal`;
    document.getElementById('fit-net-cal').textContent = `${data.net_calories} kcal`;
    document.getElementById('fit-target-cal').textContent = `/ ${profile.target_calories || 2200}`;
    document.getElementById('fit-water-ml').textContent = data.water_ml;
    document.getElementById('fit-water-target').textContent = `/ ${profile.target_water_ml || 2500} ml`;
    document.getElementById('fit-goal-badge').textContent = profile.goal_type || "Mushak yig'ish";

    // 2. Update KBJU progress bars
    const targetProtein = profile.target_protein_g || 130;
    const proteinPct = Math.min(100, Math.round((data.total_protein / targetProtein) * 100));
    document.getElementById('fit-protein-text').textContent = `${data.total_protein}g / ${targetProtein}g`;
    document.getElementById('fit-protein-bar').style.width = `${proteinPct}%`;

    const carbsPct = Math.min(100, Math.round((data.total_carbs / 250) * 100));
    document.getElementById('fit-carbs-text').textContent = `${data.total_carbs}g`;
    document.getElementById('fit-carbs-bar').style.width = `${carbsPct}%`;

    const fatPct = Math.min(100, Math.round((data.total_fat / 70) * 100));
    document.getElementById('fit-fat-text').textContent = `${data.total_fat}g`;
    document.getElementById('fit-fat-bar').style.width = `${fatPct}%`;

    // 3. Render 4 Meal Blocks
    renderMealBlocks(data.meals_by_type || {});

    // 4. Render Workouts List
    renderWorkoutsList(data.workouts || []);

    // 5. Initial AI Fitness report
    loadFitnessAiReport(targetDate);

    initIcons();
  } catch (err) {
    console.error('Fitness data load error:', err);
  }
}

function renderMealBlocks(mealsByType) {
  const container = document.getElementById('meals-blocks-container');
  if (!container) return;

  const mealTypes = [
    { type: 'Nonushta', label: '🍳 Nonushta', color: 'amber' },
    { type: 'Tushlik', label: '🍲 Tushlik', color: 'indigo' },
    { type: 'Kechki ovqat', label: '🥗 Kechki ovqat', color: 'emerald' },
    { type: 'Gazak', label: '🍎 Gazaklar', color: 'purple' }
  ];

  let html = '';
  mealTypes.forEach(mt => {
    const list = mealsByType[mt.type] || [];
    const totalCal = Math.round(list.reduce((acc, m) => acc + m.calories, 0));
    const totalP = Math.round(list.reduce((acc, m) => acc + m.protein, 0));

    let itemsHtml = '';
    if (list.length === 0) {
      itemsHtml = `<p class="text-[11px] text-slate-400 italic py-2">Hali taom qo'shilmagan</p>`;
    } else {
      itemsHtml = list.map(item => `
        <div class="flex items-center justify-between py-1.5 border-b border-slate-100 last:border-none text-xs">
          <div class="min-w-0 flex-1 pr-2">
            <span class="font-semibold text-slate-800 block truncate">${escapeHtml(item.food_name)}</span>
            <span class="text-[10px] text-slate-400 font-medium">${item.weight_grams}g · ${item.protein}g oqsil · ${item.carbs}g uglevod · ${item.fat}g yog'</span>
          </div>
          <div class="flex items-center space-x-2 shrink-0">
            <span class="font-bold text-emerald-600 text-xs">${item.calories} kcal</span>
            <button onclick="handleDeleteFood(${item.id})" class="text-slate-300 hover:text-rose-500 transition p-1">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>
      `).join('');
    }

    html += `
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
            <span class="font-bold text-xs text-slate-800">${mt.label}</span>
            <span class="text-xs font-black text-${mt.color}-600 bg-${mt.color}-50 px-2 py-0.5 rounded-md">${totalCal} kcal · ${totalP}g P</span>
          </div>
          <div class="max-h-40 overflow-y-auto">
            ${itemsHtml}
          </div>
        </div>
        <button onclick="openAddFoodModal('${mt.type}')" class="mt-3 text-[11px] font-semibold text-slate-500 hover:text-emerald-600 flex items-center justify-center space-x-1 py-1 bg-slate-50 hover:bg-slate-100 rounded-lg transition w-full">
          <i data-lucide="plus" class="w-3 h-3"></i>
          <span>+ Taom qo'shish</span>
        </button>
      </div>
    `;
  });

  container.innerHTML = html;
  initIcons();
}

function renderWorkoutsList(workouts) {
  const container = document.getElementById('workouts-list-container');
  if (!container) return;

  if (workouts.length === 0) {
    container.innerHTML = `
      <div class="bg-white p-6 rounded-xl border border-dashed border-slate-200 text-center">
        <i data-lucide="dumbbell" class="w-6 h-6 text-slate-300 mx-auto mb-2"></i>
        <p class="text-xs text-slate-400">Bugun hali mashg'ulot yozilmagan</p>
        <button onclick="openAddWorkoutModal()" class="mt-2 text-xs font-semibold text-orange-600 hover:underline">+ Mashq qo'shish</button>
      </div>
    `;
    initIcons();
    return;
  }

  let html = '';
  workouts.forEach(w => {
    html += `
      <div class="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-9 h-9 rounded-lg bg-orange-50 text-orange-600 flex items-center justify-center shrink-0">
            <i data-lucide="flame" class="w-4 h-4"></i>
          </div>
          <div>
            <span class="text-xs font-bold text-slate-800 block">${escapeHtml(w.workout_type)}</span>
            <span class="text-[10px] text-slate-400 font-medium">${w.duration_minutes} daqiqa ${w.notes ? '· ' + escapeHtml(w.notes) : ''}</span>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-xs font-bold text-orange-600">-${w.calories_burned} kcal</span>
          <button onclick="handleDeleteWorkout(${w.id})" class="text-slate-300 hover:text-rose-500 p-1 transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  initIcons();
}

async function handleAddWater(amount) {
  const targetDate = document.getElementById('fitness-date-picker')?.value || getTodayString();
  try {
    const res = await fetch('/api/water/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_ml: amount, date: targetDate })
    });
    if (res.ok) {
      loadFitnessData();
    }
  } catch (err) {
    console.error('Water add error:', err);
  }
}

async function handleFitNlpSubmit() {
  const input = document.getElementById('fit-nlp-input');
  const typeSelect = document.getElementById('fit-nlp-type');
  const feedback = document.getElementById('fit-nlp-feedback');
  const btn = document.getElementById('fit-nlp-submit-btn');
  const text = input.value.trim();
  const nlpType = typeSelect.value;
  const targetDate = document.getElementById('fitness-date-picker')?.value || getTodayString();

  if (!text) return;

  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin mr-1"></i> Tahlil...`;
  initIcons();

  try {
    if (nlpType === 'food') {
      const parseRes = await fetch('/api/ai/parse-food', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const parseData = await parseRes.json();
      const parsed = parseData.parsed;
      parsed.date = targetDate;

      // Save food
      const saveRes = await fetch('/api/nutrition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed)
      });

      if (saveRes.ok) {
        input.value = '';
        feedback.className = 'text-xs mt-2 text-emerald-300 flex items-center space-x-1';
        feedback.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5"></i> <span>Taom qo'shildi: <strong>${escapeHtml(parsed.food_name)}</strong> (${parsed.calories} kcal, ${parsed.protein}g oqsil)</span>`;
        feedback.classList.remove('hidden');
        setTimeout(() => feedback.classList.add('hidden'), 5000);
        loadFitnessData();
      }
    } else {
      // Workout NLP
      const parseRes = await fetch('/api/ai/parse-workout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const parseData = await parseRes.json();
      const parsed = parseData.parsed;
      parsed.date = targetDate;

      const saveRes = await fetch('/api/workout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed)
      });

      if (saveRes.ok) {
        input.value = '';
        feedback.className = 'text-xs mt-2 text-emerald-300 flex items-center space-x-1';
        feedback.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5"></i> <span>Mashg'ulot yozildi: <strong>${escapeHtml(parsed.workout_type)}</strong> (${parsed.duration_minutes} daqiqa, -${parsed.calories_burned} kcal)</span>`;
        feedback.classList.remove('hidden');
        setTimeout(() => feedback.classList.add('hidden'), 5000);
        loadFitnessData();
      }
    }
  } catch (err) {
    feedback.className = 'text-xs mt-2 text-rose-300';
    feedback.textContent = `Xatolik: ${err.message}`;
    feedback.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="plus" class="w-4 h-4"></i> <span>Qo'shish</span>`;
    initIcons();
  }
}

// Food modal functions
function openAddFoodModal(mealType = 'Tushlik') {
  document.getElementById('food-form').reset();
  document.getElementById('food-meal-type').value = mealType;
  document.getElementById('add-food-modal').classList.remove('hidden');
  initIcons();
}

function closeAddFoodModal() {
  document.getElementById('add-food-modal').classList.add('hidden');
}

async function handleAddFoodSubmit(event) {
  event.preventDefault();
  const targetDate = document.getElementById('fitness-date-picker')?.value || getTodayString();
  const payload = {
    date: targetDate,
    meal_type: document.getElementById('food-meal-type').value,
    food_name: document.getElementById('food-name').value.trim(),
    weight_grams: parseFloat(document.getElementById('food-weight').value) || 100,
    calories: parseFloat(document.getElementById('food-calories').value) || 0,
    protein: parseFloat(document.getElementById('food-protein').value) || 0,
    carbs: parseFloat(document.getElementById('food-carbs').value) || 0,
    fat: parseFloat(document.getElementById('food-fat').value) || 0
  };

  try {
    const res = await fetch('/api/nutrition', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      closeAddFoodModal();
      loadFitnessData();
    }
  } catch (e) {
    alert("Xatolik: " + e.message);
  }
}

async function handleDeleteFood(id) {
  if (!confirm("Ushbu taomni o'chirmoqchimisiz?")) return;
  try {
    const res = await fetch(`/api/nutrition/${id}`, { method: 'DELETE' });
    if (res.ok) loadFitnessData();
  } catch (e) {
    console.error(e);
  }
}

// Workout modal functions
function openAddWorkoutModal() {
  document.getElementById('workout-form').reset();
  document.getElementById('add-workout-modal').classList.remove('hidden');
  initIcons();
}

function closeAddWorkoutModal() {
  document.getElementById('add-workout-modal').classList.add('hidden');
}

async function handleAddWorkoutSubmit(event) {
  event.preventDefault();
  const targetDate = document.getElementById('fitness-date-picker')?.value || getTodayString();
  const calVal = document.getElementById('workout-calories').value;
  const payload = {
    date: targetDate,
    workout_type: document.getElementById('workout-type').value,
    duration_minutes: parseInt(document.getElementById('workout-duration').value) || 45,
    calories_burned: calVal ? parseFloat(calVal) : null,
    notes: document.getElementById('workout-notes').value.trim()
  };

  try {
    const res = await fetch('/api/workout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      closeAddWorkoutModal();
      loadFitnessData();
    }
  } catch (e) {
    alert("Xatolik: " + e.message);
  }
}

async function handleDeleteWorkout(id) {
  if (!confirm("Ushbu mashg'ulotni o'chirmoqchimisiz?")) return;
  try {
    const res = await fetch(`/api/workout/${id}`, { method: 'DELETE' });
    if (res.ok) loadFitnessData();
  } catch (e) {
    console.error(e);
  }
}

// Fitness Profile modal
async function openFitnessProfileModal() {
  try {
    const res = await fetch('/api/fitness/profile');
    if (res.ok) {
      const data = await res.json();
      const p = data.profile || {};
      document.getElementById('prof-goal-type').value = p.goal_type || "Mushak massasi yig'ish";
      document.getElementById('prof-target-cal').value = p.target_calories || 2200;
      document.getElementById('prof-target-protein').value = p.target_protein_g || 130;
      document.getElementById('prof-target-water').value = p.target_water_ml || 2500;
      document.getElementById('prof-weight').value = p.current_weight_kg || 75;
    }
  } catch (e) {
    console.error(e);
  }
  document.getElementById('fitness-profile-modal').classList.remove('hidden');
  initIcons();
}

function closeFitnessProfileModal() {
  document.getElementById('fitness-profile-modal').classList.add('hidden');
}

async function handleFitnessProfileSubmit(event) {
  event.preventDefault();
  const payload = {
    goal_type: document.getElementById('prof-goal-type').value,
    target_calories: parseInt(document.getElementById('prof-target-cal').value) || 2200,
    target_protein_g: parseInt(document.getElementById('prof-target-protein').value) || 130,
    target_water_ml: parseInt(document.getElementById('prof-target-water').value) || 2500,
    current_weight_kg: parseFloat(document.getElementById('prof-weight').value) || 75
  };

  try {
    const res = await fetch('/api/fitness/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      closeFitnessProfileModal();
      loadFitnessData();
    }
  } catch (e) {
    alert("Xatolik: " + e.message);
  }
}

// Fitness AI Report
async function loadFitnessAiReport(dateStr = null) {
  const targetDate = dateStr || document.getElementById('fitness-date-picker')?.value || getTodayString();
  const box = document.getElementById('fitness-ai-report-box');
  if (!box) return;

  try {
    const res = await fetch(`/api/fitness/ai-report?date=${targetDate}`);
    if (res.ok) {
      const data = await res.json();
      box.innerHTML = marked.parse(data.report || '');
    }
  } catch (e) {
    console.error('Fitness report error:', e);
  }
}

// ====================================================
// POMODORO FOKUS TAYMERI LOGIC
// ====================================================
let pomodoroTimerInterval = null;
let pomodoroRemainingSeconds = 25 * 60;
let pomodoroIsRunning = false;
let pomodoroCurrentMode = 'work'; // 'work', 'short', 'long'
let pomodoroSessionsCompleted = 0;

function openPomodoroModal() {
  populatePomodoroTaskSelect();
  document.getElementById('pomodoro-modal').classList.remove('hidden');
  initIcons();
}

function closePomodoroModal() {
  document.getElementById('pomodoro-modal').classList.add('hidden');
}

async function populatePomodoroTaskSelect() {
  const select = document.getElementById('pomodoro-task-select');
  if (!select) return;
  try {
    const res = await fetch('/api/tasks?status=Ochiq');
    if (res.ok) {
      const data = await res.json();
      const tasks = data.tasks || [];
      select.innerHTML = '<option value="">Umumiy chuqur diqqat (Deep Work)</option>' +
        tasks.map(t => `<option value="${t.id}">${escapeHtml(t.title)} (${t.priority})</option>`).join('');
    }
  } catch (e) {
    console.error(e);
  }
}

function setPomodoroMode(mode) {
  clearInterval(pomodoroTimerInterval);
  pomodoroIsRunning = false;
  pomodoroCurrentMode = mode;

  const btnWork = document.getElementById('pomo-mode-work');
  const btnShort = document.getElementById('pomo-mode-short');
  const btnLong = document.getElementById('pomo-mode-long');
  const statusText = document.getElementById('pomodoro-status-text');

  [btnWork, btnShort, btnLong].forEach(b => {
    b.className = 'px-3 py-1.5 rounded-lg text-slate-600';
  });

  if (mode === 'work') {
    pomodoroRemainingSeconds = 25 * 60;
    btnWork.className = 'px-3 py-1.5 rounded-lg bg-white shadow-xs text-rose-600 font-bold';
    statusText.textContent = "Diqqatni bir maqsadga qarating";
  } else if (mode === 'short') {
    pomodoroRemainingSeconds = 5 * 60;
    btnShort.className = 'px-3 py-1.5 rounded-lg bg-white shadow-xs text-emerald-600 font-bold';
    statusText.textContent = "Qisqa tanaffus: ko'zlaringizga va ongingizga dam bering";
  } else if (mode === 'long') {
    pomodoroRemainingSeconds = 15 * 60;
    btnLong.className = 'px-3 py-1.5 rounded-lg bg-white shadow-xs text-indigo-600 font-bold';
    statusText.textContent = "Katta tanaffus: suv iching, harakatlaning";
  }

  updatePomodoroDisplay();
  updatePomodoroButtons();
}

function togglePomodoro() {
  if (pomodoroIsRunning) {
    clearInterval(pomodoroTimerInterval);
    pomodoroIsRunning = false;
  } else {
    pomodoroIsRunning = true;
    pomodoroTimerInterval = setInterval(() => {
      if (pomodoroRemainingSeconds > 0) {
        pomodoroRemainingSeconds--;
        updatePomodoroDisplay();
      } else {
        clearInterval(pomodoroTimerInterval);
        pomodoroIsRunning = false;
        playChimeSound();
        if (pomodoroCurrentMode === 'work') {
          pomodoroSessionsCompleted++;
          document.getElementById('pomodoro-session-count').textContent = pomodoroSessionsCompleted;
          alert("🎉 Ajoyib! 25 daqiqalik fokus seansi muvaffaqiyatli yakunlandi! 5 daqiqa dam oling.");
          setPomodoroMode('short');
        } else {
          alert("⏱️ Tanaffus yakunlandi! Yangi fokus seansiga tayyormisiz?");
          setPomodoroMode('work');
        }
      }
    }, 1000);
  }
  updatePomodoroButtons();
}

function resetPomodoro() {
  clearInterval(pomodoroTimerInterval);
  pomodoroIsRunning = false;
  setPomodoroMode(pomodoroCurrentMode);
}

function updatePomodoroDisplay() {
  const mins = Math.floor(pomodoroRemainingSeconds / 60);
  const secs = pomodoroRemainingSeconds % 60;
  const str = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  const display = document.getElementById('pomodoro-timer-display');
  if (display) display.textContent = str;
}

function updatePomodoroButtons() {
  const label = document.getElementById('pomodoro-btn-label');
  const icon = document.getElementById('pomodoro-play-icon');
  if (label && icon) {
    if (pomodoroIsRunning) {
      label.textContent = "Pauza";
      icon.setAttribute('data-lucide', 'pause');
    } else {
      label.textContent = "Boshlash";
      icon.setAttribute('data-lucide', 'play');
    }
    initIcons();
  }
}

function playChimeSound() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.2); // A5
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.8);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.8);
  } catch (e) {
    console.log("Audio play error:", e);
  }
}

// ====================================================
// WEB SPEECH API (OVOZLI MATN KIRITISH)
// ====================================================
function startVoiceRecognition(targetInputId, triggerBtn) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Kechirasiz, brauzeringiz ovozli kiritishni qo'llab-quvvatlamaydi (Google Chrome yoki Edge tavsiya etiladi).");
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'uz-UZ';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  if (triggerBtn) triggerBtn.classList.add('recording-active');

  recognition.onstart = () => {
    console.log("Ovoz yozilmoqda...");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const inputEl = document.getElementById(targetInputId);
    if (inputEl) {
      inputEl.value = transcript;
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech error:", event.error);
    if (triggerBtn) triggerBtn.classList.remove('recording-active');
  };

  recognition.onend = () => {
    if (triggerBtn) triggerBtn.classList.remove('recording-active');
  };

  recognition.start();
}

// ====================================================
// BRAUZER BILDIRISHNOMALARI (DESKTOP NOTIFICATIONS)
// ====================================================
let notificationsEnabled = false;
let notifiedTaskIds = new Set();

function initNotifications() {
  if ('Notification' in window && Notification.permission === 'granted') {
    notificationsEnabled = true;
    updateNotificationBellUI();
  }
  // Har 30 soniyada kutilayotgan vazifalarni tekshirish
  setInterval(checkUpcomingTasksNotification, 30000);
}

async function toggleBrowserNotifications() {
  if (!('Notification' in window)) {
    alert("Brauzeringiz bildirishnomalarni qo'llab-quvvatlamaydi.");
    return;
  }

  if (Notification.permission === 'granted') {
    alert("🔔 Bildirishnomalar faol! Belgilangan vaqti kelgan vazifalar haqida kompyuteringizda avtomatik xabarnoma chiqadi.");
    return;
  }

  try {
    const perm = await Notification.requestPermission();
    if (perm === 'granted') {
      notificationsEnabled = true;
      updateNotificationBellUI();
      new Notification("SmartTask AI", {
        body: "🎉 Bildirishnomalar muvaffaqiyatli yoqildi! Endi muhim vazifalaringiz esdan chiqmaydi.",
      });
      playChimeSound();
    } else {
      alert("Bildirishnomalar ruxsati berilmadi.");
    }
  } catch (e) {
    console.error("Notif permission error:", e);
  }
}

function updateNotificationBellUI() {
  const btn = document.getElementById('notification-bell-btn');
  const badge = document.getElementById('notif-badge');
  if (btn && notificationsEnabled) {
    btn.classList.add('text-indigo-600', 'bg-indigo-50');
    if (badge) badge.classList.remove('hidden');
  }
}

async function checkUpcomingTasksNotification() {
  if (!notificationsEnabled || Notification.permission !== 'granted') return;

  try {
    const res = await fetch('/api/tasks?status=Ochiq');
    if (!res.ok) return;
    const data = await res.json();
    const tasks = data.tasks || [];
    const now = new Date();
    const currentHours = now.getHours();
    const currentMins = now.getMinutes();
    const currentTotalMins = currentHours * 60 + currentMins;

    tasks.forEach(t => {
      if (!t.due_time || notifiedTaskIds.has(t.id)) return;
      const parts = t.due_time.split(':').map(Number);
      if (parts.length < 2 || isNaN(parts[0]) || isNaN(parts[1])) return;

      const taskTotalMins = parts[0] * 60 + parts[1];
      const diffMins = taskTotalMins - currentTotalMins;

      // Agar vazifaga 10 daqiqa qolgan bo'lsa yoki vaqti yetib kelgan bo'lsa
      if (diffMins >= 0 && diffMins <= 10) {
        notifiedTaskIds.add(t.id);
        const timeMsg = diffMins === 0 ? "Hozir bajarish vaqti!" : `${diffMins} daqiqadan so'ng!`;
        new Notification(`SmartTask AI: ${t.title}`, {
          body: `⏰ Vaqti: ${t.due_time} (${timeMsg})\n🎯 Ustuvorlik: ${t.priority} | 🏷️ Kategoriya: ${t.category}`,
          requireInteraction: true
        });
        playChimeSound();
      }
    });
  } catch (err) {
    console.error("Notif check error:", err);
  }
}

