(function () {
  var box = document.getElementById('q');
  var out = document.getElementById('results');
  if (!box || !out) return;
  var base = (location.pathname.match(/\/(sources|genes|topics)\//) ? '../' : '');
  var params = new URLSearchParams(location.search);
  if (params.get('q')) box.value = params.get('q');
  var data = null;
  function render() {
    var q = box.value.trim().toLowerCase();
    if (!data) return;
    if (!q) { out.innerHTML = ''; return; }
    var terms = q.split(/\s+/);
    var hits = data.filter(function (d) {
      var hay = (d.title + ' ' + d.author + ' ' + d.text + ' ' + d.id).toLowerCase();
      return terms.every(function (t) { return hay.indexOf(t) >= 0; });
    }).slice(0, 100);
    out.innerHTML = hits.length ? hits.map(function (d) {
      return '<div class="hit"><a href="' + base + 'sources/' + d.id + '.html">' + esc(d.title) + '</a>' +
        '<span class="muted">' + esc(d.author) + ' · ' + d.year + ' · ' + esc(d.type) + ' · ' + esc(d.site) + '</span></div>';
    }).join('') : '<p class="muted">No sources match.</p>';
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  fetch(base + 'search.json').then(function (r) { return r.json(); }).then(function (d) { data = d; render(); });
  box.addEventListener('input', render);
})();
