/* AJG Tracker PC: stand-in for the claude.ai artifact runtime. Injected by server.py before the page's own scripts.
   window.claude.use('db')        -> storage in the folder, through the local server
   window.claude.use('downloads') -> a normal browser download
   window.claude.use('sample'|'mcp') -> not available: rejects like a runtime without that capability (the page catches it) */
(function () {
  'use strict';
  if (window.claude && window.claude.__local) return;
  var API = '/_local/api/';
  var POLL_MS = 1500;

  function fail(code, message) { var e = new Error(message || code); e.code = code; return e; }
  function enc(s) { return encodeURIComponent(s); }

  function http(method, url, body) {
    var opt = { method: method, cache: 'no-store', headers: { 'X-Local-Token': window.__LOCAL_TOKEN || '' } };
    if (body !== undefined) { opt.body = JSON.stringify(body); opt.headers['Content-Type'] = 'application/json'; }
    return fetch(url, opt).then(function (r) {
      return r.text().then(function (t) {
        var j = null; try { j = t ? JSON.parse(t) : null; } catch (e) {}
        if (!r.ok) throw fail(r.status === 404 ? 'not_found' : 'storage_error', (j && j.error) || ('HTTP ' + r.status));
        return j;
      });
    }, function () { throw fail('unavailable', 'The tracker server is not reachable.'); });
  }

  /* ---- snapshots ---- */
  function makeDoc(row) {
    return { id: row.id, exists: true, data: function () { return row.data; }, ref: null };
  }
  function makeSnap(rows) {
    var docs = rows.map(makeDoc);
    return { docs: docs, size: docs.length, empty: !docs.length,
             forEach: function (f) { docs.forEach(f); },
             docChanges: function () { return docs.map(function (d) { return { type: 'added', doc: d }; }); } };
  }

  var subs = {};          /* collection -> {ver, cbs:[{cb, err}], busy} */
  var timer = null;

  function fetchCol(c) {
    return http('GET', API + enc(c)).then(function (j) { return { ver: j.version, snap: makeSnap(j.docs || []) }; });
  }
  function fire(c, res) {
    var s = subs[c]; if (!s) return;
    s.ver = res.ver;
    s.cbs.slice().forEach(function (h) { try { h.cb(res.snap); } catch (e) { console.error(e); } });
  }
  function refresh(c) {
    var s = subs[c]; if (!s || s.busy) { if (s) s.again = true; return Promise.resolve(); }
    s.busy = true;
    return fetchCol(c).then(function (res) { fire(c, res); }, function () {}).then(function () {
      s.busy = false; if (s.again) { s.again = false; return refresh(c); }
    });
  }
  function tick() {
    var names = Object.keys(subs); if (!names.length) { timer = null; return; }
    http('GET', API + '_versions?c=' + names.map(enc).join(',')).then(function (j) {
      var v = (j && j.versions) || {};
      names.forEach(function (c) { var s = subs[c]; if (s && v[c] !== undefined && v[c] !== s.ver) refresh(c); });
    }, function () {}).then(function () { timer = setTimeout(tick, POLL_MS); });
  }
  function subscribe(c, cb, err) {
    var s = subs[c] || (subs[c] = { ver: null, cbs: [], busy: false, again: false });
    var h = { cb: cb, err: err };
    s.cbs.push(h);
    /* first snapshot for this listener: the full current collection */
    fetchCol(c).then(function (res) {
      if (s.ver === null) s.ver = res.ver;
      if (s.cbs.indexOf(h) >= 0) { try { cb(res.snap); } catch (e) { console.error(e); } }
    }, function (e) {
      if (s.ver === null) s.ver = '';   /* retry on the next poll */
      if (err && s.cbs.indexOf(h) >= 0) { try { err(e); } catch (x) { console.error(x); } }
    });
    if (!timer) timer = setTimeout(tick, POLL_MS);
    return function unsubscribe() {
      var i = s.cbs.indexOf(h); if (i >= 0) s.cbs.splice(i, 1);
      if (!s.cbs.length) delete subs[c];
    };
  }

  /* ---- db ---- */
  function collection(c) {
    return {
      id: c,
      doc: function (id) {
        id = String(id);
        return {
          id: id,
          set: function (obj) {
            if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return Promise.reject(fail('invalid', 'A document must be an object.'));
            return http('PUT', API + enc(c) + '/' + enc(id), obj).then(function () { refresh(c); });
          },
          delete: function () {
            return http('DELETE', API + enc(c) + '/' + enc(id)).then(function () { refresh(c); });
          },
          get: function () {
            return http('GET', API + enc(c) + '/' + enc(id)).then(
              function (j) { return makeDoc({ id: id, data: j.data }); },
              function (e) { if (e.code === 'not_found') return { id: id, exists: false, data: function () { return undefined; } }; throw e; });
          }
        };
      },
      get: function () { return fetchCol(c).then(function (r) { return r.snap; }); },
      onSnapshot: function (cb, err) { return subscribe(c, cb, err); }
    };
  }
  var db = { collection: collection };

  /* ---- downloads ---- */
  var downloads = {
    save: function (o) {
      return new Promise(function (resolve, reject) {
        try {
          var data = o && o.data, name = (o && o.filename) || 'download';
          var blob = data instanceof Blob ? data : new Blob([data == null ? '' : data]);
          var u = URL.createObjectURL(blob), a = document.createElement('a');
          a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove();
          setTimeout(function () { URL.revokeObjectURL(u); }, 10000);
          resolve({ saved: true, filename: name });
        } catch (e) { reject(e); }
      });
    }
  };

  /* ---- runtime ---- */
  window.claude = {
    __local: true,
    use: function (name) {
      if (name === 'db') return Promise.resolve(db);
      if (name === 'downloads') return Promise.resolve(downloads);
      /* sample, mcp, and anything else: this PC tracker never goes online */
      return Promise.reject(fail('not_declared', 'The capability "' + name + '" is not available in the PC tracker.'));
    }
  };
})();
