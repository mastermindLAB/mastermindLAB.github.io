(()=>{
  // ---- Live GitHub repo data ----
  const setText = (id,v) => { const el = document.getElementById(id); if(el) el.textContent = v; };
  function loadRepo(repo, prefix, useDescription){
    fetch('https://api.github.com/repos/' + repo, {signal: AbortSignal.timeout(10000)})
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if(!d) return;
        if(useDescription && d.description) setText(prefix + '-desc', d.description);
        setText(prefix + '-stars', d.stargazers_count);
        setText(prefix + '-forks', d.forks_count);
        setText(prefix + '-lang', d.language || 'Code');
        setText(prefix + '-updated', new Date(d.pushed_at).toLocaleDateString('en-CA', { year:'numeric', month:'short' }));
      }).catch(()=>{});
  }
  loadRepo('mastermindlab/mastermindlab.github.io', 'repo2', false);

  // ---- GitHub activity: contribution heatmap + stats ----
  const GH_USER = 'mastermindlab';
  const CAL_COLORS = ['#161923','#2A3560','#40519B','#5B74DB','#8FA3FF'];

  fetch('https://api.github.com/users/' + GH_USER, {signal: AbortSignal.timeout(10000)})
    .then(r => r.ok ? r.json() : null)
    .then(d => { if(d) setText('gh-repos', d.public_repos); })
    .catch(()=>{});

  function calFail(){
    const note = document.getElementById('gh-cal-note');
    if(note){
      note.innerHTML = '';
      const a = document.createElement('a');
      a.href = 'https://github.com/' + GH_USER; a.target = '_blank'; a.rel = 'noopener';
      a.textContent = 'Contribution graph unavailable right now — view it on GitHub ↗';
      a.style.color = 'var(--muted)';
      note.appendChild(a);
    }
  }

  function renderCal(data){
    const days = data.contributions;
    const grid = document.getElementById('gh-grid');
    const monthsEl = document.getElementById('gh-months');
    if(!grid || !days || !days.length){ calFail(); return; }

    // Pad the first week so columns align to Sun–Sat.
    const firstDow = new Date(days[0].date + 'T00:00:00Z').getUTCDay();
    for(let p = 0; p < firstDow; p++){
      const pad = document.createElement('span');
      pad.className = 'gh-cal__cell'; pad.style.visibility = 'hidden';
      grid.appendChild(pad);
    }

    let total = 0, best = 0, activeDays = 0;
    const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const monthMarks = [];
    let lastMonth = -1;

    days.forEach((d, i) => {
      total += d.count;
      if(d.count > best) best = d.count;
      if(d.count > 0) activeDays++;
      const dt = new Date(d.date + 'T00:00:00Z');
      const week = Math.floor((i + firstDow) / 7);
      if(dt.getUTCDate() <= 7 && dt.getUTCMonth() !== lastMonth){
        lastMonth = dt.getUTCMonth();
        monthMarks.push({ week, label: monthNames[lastMonth] });
      }
      const cell = document.createElement('span');
      cell.className = 'gh-cal__cell';
      cell.dataset.l = Math.min(4, Math.max(0, d.level));
      cell.dataset.tip = d.count + ' contribution' + (d.count === 1 ? '' : 's') + ' · ' +
        dt.toLocaleDateString('en-CA', { timeZone:'UTC', month:'short', day:'numeric', year:'numeric' });
      grid.appendChild(cell);
    });

    const weeks = Math.ceil((days.length + firstDow) / 7);
    if(monthsEl){
      monthsEl.style.gridTemplateColumns = 'repeat(' + weeks + ', 13px)';
      monthsEl.style.gap = '3px';
      monthMarks.forEach(m => {
        const s = document.createElement('span');
        s.textContent = m.label;
        s.style.gridColumnStart = m.week + 1;
        s.style.gridRow = '1';
        monthsEl.appendChild(s);
      });
    }

    const yearTotal = (data.total && (data.total.lastYear || data.total.lastYear === 0)) ? data.total.lastYear : total;
    setText('gh-total', yearTotal.toLocaleString('en-CA'));
    setText('gh-week', (yearTotal / 52).toFixed(1));
    setText('gh-best', best);
    setText('gh-cal-note', activeDays + ' active days in the last year');

    // Hover tooltip
    const tip = document.createElement('div');
    tip.className = 'gh-tip'; tip.setAttribute('aria-hidden','true');
    document.body.appendChild(tip);
    grid.addEventListener('pointerover', e => {
      const c = e.target.closest('.gh-cal__cell');
      if(!c || !c.dataset.tip) return;
      const r = c.getBoundingClientRect();
      tip.textContent = '';
      const parts = c.dataset.tip.split(' · ');
      const b = document.createElement('b'); b.textContent = parts[0];
      tip.appendChild(b); tip.appendChild(document.createTextNode(' · ' + parts[1]));
      tip.style.left = (r.left + r.width/2) + 'px';
      tip.style.top = r.top + 'px';
      tip.classList.add('is-on');
    });
    grid.addEventListener('pointerout', () => tip.classList.remove('is-on'));
  }

  fetch('https://github-contributions-api.jogruber.de/v4/' + GH_USER + '?y=last', {signal: AbortSignal.timeout(10000)})
    .then(r => r.ok ? r.json() : null)
    .then(d => { if(d && d.contributions) renderCal(d); else calFail(); })
    .catch(calFail);

  // ---- Latest public commits ----
  function relTime(iso){
    const s = Math.max(1, (Date.now() - new Date(iso).getTime()) / 1000);
    if(s < 3600) return Math.round(s/60) + ' min ago';
    if(s < 86400) return Math.round(s/3600) + ' hr ago';
    if(s < 2592000) return Math.round(s/86400) + ' d ago';
    return new Date(iso).toLocaleDateString('en-CA', { month:'short', day:'numeric' });
  }

  fetch('https://api.github.com/users/' + GH_USER + '/events/public?per_page=100', {signal: AbortSignal.timeout(10000)})
    .then(r => r.ok ? r.json() : null)
    .then(events => {
      const list = document.getElementById('gh-commit-list');
      if(!list) return;
      const rows = [];
      (events || []).forEach(ev => {
        if(ev.type !== 'PushEvent' || !ev.payload || !ev.payload.commits) return;
        ev.payload.commits.slice().reverse().forEach(c => {
          if(rows.length < 6) rows.push({ repo: ev.repo.name, sha: c.sha, msg: c.message.split('\n')[0], when: ev.created_at });
        });
      });
      if(!rows.length){
        list.innerHTML = '';
        const d = document.createElement('div'); d.className = 'gh-empty';
        d.textContent = 'No recent public commits — see the full history on GitHub.';
        list.appendChild(d);
        return;
      }
      list.innerHTML = '';
      rows.forEach(row => {
        const a = document.createElement('a');
        a.className = 'gh-commit';
        a.href = 'https://github.com/' + row.repo + '/commit/' + row.sha;
        a.target = '_blank'; a.rel = 'noopener';
        const repo = document.createElement('span'); repo.className = 'repo'; repo.textContent = row.repo.replace(/^mastermindlab\//i, '');
        const msg = document.createElement('span'); msg.className = 'msg'; msg.textContent = row.msg;
        const when = document.createElement('span'); when.className = 'when'; when.textContent = relTime(row.when);
        a.appendChild(repo); a.appendChild(msg); a.appendChild(when);
        list.appendChild(a);
      });
    })
    .catch(() => {
      const list = document.getElementById('gh-commit-list');
      if(list) list.querySelectorAll('.gh-empty').forEach(el => el.textContent = 'Commit feed unavailable — view activity on GitHub.');
    });


})();