/* AJG Tracker preview: stand-in for the runtime the tracker page expects (window.claude).
   Read-only preview: nothing is saved to a file, nothing goes online. Saved views (collection "views") are kept in this
   browser's own storage when it allows it; every other collection starts empty and lives only while the page is open. */
(function () {
  'use strict';
  var MANIFEST = {};
  try { MANIFEST = JSON.parse(document.getElementById('prev-manifest').textContent || '{}'); } catch (e) {}
  var KEEP = { views: 'ajgpreview.views.v1' };
  function fail(code, msg) { var e = new Error(msg || code); e.code = code; return e; }

  /* the page asks for files next to it (saved copies, photos, release texts, the spreadsheet); a single file:// page has none */
  var realFetch = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function (url, opt) {
    var u = typeof url === 'string' ? url : (url && url.url) || '';
    if (/^(https?:|data:|blob:)/i.test(u) && realFetch) return realFetch(url, opt);
    if (/(^|\/)articles\/manifest\.json(\?|$)/.test(u)) return Promise.resolve(new Response(JSON.stringify(MANIFEST), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    return Promise.resolve(new Response('{}', { status: 404, statusText: 'Not in this preview' }));
  };

  var store = {};
  function load(c) {
    if (store[c]) return store[c];
    var m = {};
    if (KEEP[c]) { try { var j = JSON.parse(localStorage.getItem(KEEP[c]) || '{}'); if (j && typeof j === 'object') m = j; } catch (e) {} }
    return (store[c] = m);
  }
  function persist(c) { if (!KEEP[c]) return; try { localStorage.setItem(KEEP[c], JSON.stringify(store[c])); } catch (e) {} }
  function makeDoc(id, data) { return { id: id, exists: true, data: function () { return data; }, ref: null }; }
  function snap(c) {
    var m = load(c), docs = Object.keys(m).map(function (k) { return makeDoc(k, m[k]); });
    return { docs: docs, size: docs.length, empty: !docs.length, forEach: function (f) { docs.forEach(f); },
             docChanges: function () { return docs.map(function (d) { return { type: 'added', doc: d }; }); } };
  }
  var subs = {};
  function fire(c) { (subs[c] || []).slice().forEach(function (cb) { try { cb(snap(c)); } catch (e) { console.error(e); } }); }
  function collection(c) {
    return {
      id: c,
      doc: function (id) {
        id = String(id);
        return {
          id: id,
          set: function (o) {
            if (!o || typeof o !== 'object' || Array.isArray(o)) return Promise.reject(fail('invalid', 'A document must be an object.'));
            load(c)[id] = JSON.parse(JSON.stringify(o)); persist(c); setTimeout(function () { fire(c); }, 0); return Promise.resolve();
          },
          delete: function () { delete load(c)[id]; persist(c); setTimeout(function () { fire(c); }, 0); return Promise.resolve(); },
          get: function () { var m = load(c); return Promise.resolve(id in m ? makeDoc(id, m[id]) : { id: id, exists: false, data: function () { return undefined; } }); }
        };
      },
      get: function () { return Promise.resolve(snap(c)); },
      onSnapshot: function (cb) {
        (subs[c] = subs[c] || []).push(cb);
        setTimeout(function () { try { cb(snap(c)); } catch (e) { console.error(e); } }, 0);
        return function () { var i = (subs[c] || []).indexOf(cb); if (i >= 0) subs[c].splice(i, 1); };
      }
    };
  }
  var db = { collection: collection };
  /* a normal browser download (the list the viewer is looking at, as the page builds it; nothing is read from files) */
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
  window.claude = {
    __preview: true,
    use: function (name) {
      if (name === 'db') return Promise.resolve(db);
      if (name === 'downloads') return Promise.resolve(downloads);
      return Promise.reject(fail('not_declared', 'The capability "' + name + '" is not available in the preview.'));
    }
  };
})();
