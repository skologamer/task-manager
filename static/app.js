async function fetchTasks(){
  const res = await fetch(API_BASE_URL + '/tasks');
  return await res.json();
}

async function updateTask(id, data){
  await fetch(API_BASE_URL + '/tasks/' + id, {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(data)
  });
}

async function deleteTask(id){
  await fetch(API_BASE_URL + '/tasks/' + id, { method: 'DELETE' });
}

function isoLocalString(dt){
  if(!dt) return null;
  const d = new Date(dt);
  return d.toLocaleString();
}

function scheduleNotification(task){
  if(!('Notification' in window)) return;
  if(!task.due_date || !task.notify) return;
  const due = new Date(task.due_date);
  const msBefore = (task.remind_before || 15) * 60 * 1000;
  const notifyTime = due.getTime() - msBefore;
  const now = Date.now();
  const delay = notifyTime - now;
  if(delay <= 0) return; // missed or immediate
  setTimeout(()=>{
    Notification.requestPermission().then(perm=>{
      if(perm === 'granted'){
        new Notification('Task Reminder', { body: task.title + (task.description? ': '+task.description : '') });
      }
    });
  }, delay);
}

function renderTasks(tasks){
  const ul = document.getElementById('task-list');
  ul.innerHTML='';
  tasks.forEach(t=>{
    const li = document.createElement('li');

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = !!t.completed;
    checkbox.addEventListener('change', async ()=>{
      await updateTask(t.id, { completed: checkbox.checked });
      await refreshAll(window.calendarRef, window.chartRef);
    });

    const titleSpan = document.createElement('span');
    titleSpan.textContent = ' ' + t.title + (t.due_date? ' — '+isoLocalString(t.due_date): '');

    const del = document.createElement('button');
    del.textContent = 'Delete';
    del.style.marginLeft = '8px';
    del.addEventListener('click', async ()=>{
      if(!confirm('Delete this task?')) return;
      await deleteTask(t.id);
      await refreshAll(window.calendarRef, window.chartRef);
    });

    const edit = document.createElement('button');
    edit.textContent = 'Edit';
    edit.style.marginLeft = '8px';
    edit.addEventListener('click', async ()=>{
      openEditModal(t);
    });

    li.appendChild(checkbox);
    li.appendChild(titleSpan);
    li.appendChild(edit);
    li.appendChild(del);
    ul.appendChild(li);
    scheduleNotification(t);
  });
}

function openEditModal(task){
  const modal = document.getElementById('editModal');
  document.getElementById('editTitle').value = task.title || '';
  document.getElementById('editDescription').value = task.description || '';
  document.getElementById('editDue').value = task.due_date ? task.due_date.substring(0,16) : '';
  document.getElementById('editRemind').value = task.remind_before || 15;
  document.getElementById('editNotify').checked = !!task.notify;
  document.getElementById('editError').textContent = '';
  modal.style.display = 'flex';
  window.currentEditingTaskId = task.id;
}

function closeEditModal(){
  const modal = document.getElementById('editModal');
  modal.style.display = 'none';
  window.currentEditingTaskId = null;
}

async function refreshAll(calendar, chart){
  const tasks = await fetchTasks();
  renderTasks(tasks);
  const events = tasks.filter(t=>t.due_date).map(t=>({ title: t.title, start: t.due_date, id: t.id }));
  calendar.removeAllEvents();
  events.forEach(e=>calendar.addEvent(e));

  // Chart: completed vs pending
  const completed = tasks.filter(t=>t.completed).length;
  const pending = tasks.length - completed;
  chart.data.datasets[0].data = [completed, pending];
  chart.update();
}

document.addEventListener('DOMContentLoaded', async ()=>{
  const calendarEl = document.getElementById('calendar');
  const calendar = new FullCalendar.Calendar(calendarEl, { initialView:'dayGridMonth' });
  calendar.render();
  
  // keep refs for refresh callbacks
  window.calendarRef = calendar;

  const ctx = document.getElementById('progressChart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'doughnut',
    data: { labels: ['Completed','Pending'], datasets:[{ data: [0,1], backgroundColor:['#4caf50','#ff9800'] }] }
  });

  window.chartRef = chart;

  // Edit modal buttons
  const saveBtn = document.getElementById('editSave');
  const cancelBtn = document.getElementById('editCancel');
  saveBtn.addEventListener('click', async ()=>{
    const id = window.currentEditingTaskId;
    if(!id) return closeEditModal();
    const payload = {
      title: document.getElementById('editTitle').value.trim(),
      description: document.getElementById('editDescription').value.trim(),
      due_date: document.getElementById('editDue').value || null,
      remind_before: parseInt(document.getElementById('editRemind').value || '15', 10),
      notify: document.getElementById('editNotify').checked
    };
    const editErr = document.getElementById('editError');
    editErr.textContent = '';
    if(!payload.title){ editErr.textContent = 'Title required'; return; }
    if(isNaN(payload.remind_before) || payload.remind_before < 0){ editErr.textContent = 'Remind must be a non-negative number'; return; }
    await updateTask(id, payload);
    closeEditModal();
    await refreshAll(window.calendarRef, window.chartRef);
  });
  cancelBtn.addEventListener('click', ()=>{ closeEditModal(); });

  await refreshAll(calendar, chart);

  document.getElementById('task-form').addEventListener('submit', async (e)=>{
    e.preventDefault();
    const taskError = document.getElementById('taskError');
    const title = document.getElementById('title').value.trim();
    const description = document.getElementById('description').value.trim();
    const due = document.getElementById('due').value;
    const remind = parseInt(document.getElementById('remind').value || '15', 10);
    const notify = document.getElementById('notify').checked;
    taskError.textContent = '';
    if(!title){ taskError.textContent = 'Task title required'; return; }
    if(isNaN(remind) || remind < 0){ taskError.textContent = 'Reminder must be a non-negative number'; return; }
    try {
      const res = await fetch(API_BASE_URL + '/tasks', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ title, description, due_date: due || null, remind_before: remind, notify }) });
      const data = await res.json().catch(()=>({}));
      if(!res.ok){ throw new Error(data.error || 'Could not create task'); }
      document.getElementById('task-form').reset();
      await refreshAll(calendar, chart);
    } catch (err) {
      taskError.textContent = err.message || 'Unable to create task';
    }
  });

  document.getElementById('ics-file').addEventListener('change', async (e)=>{
    const f = e.target.files[0];
    const importError = document.getElementById('importError');
    importError.textContent = '';
    if(!f) return;
    const fd = new FormData();
    fd.append('ics', f);
    try {
      const res = await fetch(API_BASE_URL + '/import_ics', { method:'POST', body: fd });
      const data = await res.json().catch(()=>({}));
      if(!res.ok){ throw new Error(data.error || 'Unable to import calendar'); }
      await refreshAll(calendar, chart);
    } catch (err) {
      importError.textContent = err.message || 'Unable to import calendar';
    }
  });
});
