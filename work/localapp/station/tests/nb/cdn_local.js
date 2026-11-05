/* SMALLPAGE-v1: the station loads its PDF libraries from cdn.jsdelivr.net and its fonts from Google Fonts (both allowed in claude.ai artifacts).
   Tests serve those requests from the pinned copies in vendor/ (fonts: empty CSS), so nothing leaves the machine. */
const fs = require('fs'), path = require('path');
const V = path.join(__dirname, '..', '..', 'vendor');
const MAP = { 'pdfjs-dist@4.10.38/legacy/build/pdf.min.mjs': 'pdf.min.mjs', 'pdfjs-dist@4.10.38/legacy/build/pdf.worker.min.mjs': 'pdf.worker.min.mjs', 'pdf-lib@1.17.1/dist/pdf-lib.min.js': 'pdf-lib.min.js' };
exports.CSP = "default-src 'none'; script-src 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'unsafe-inline' https://fonts.googleapis.com; img-src data: blob:; font-src data: https://fonts.gstatic.com; worker-src 'none'; connect-src 'none'";
exports.ALLOWED = /^https:\/\/(cdn\.jsdelivr\.net\/npm\/|fonts\.(googleapis|gstatic)\.com\/)/;
exports.route = async ctx => {
  await ctx.route(exports.ALLOWED, r => {
    const u = r.request().url(), m = /cdn\.jsdelivr\.net\/npm\/([^?#]+)/.exec(u);
    if (m && MAP[m[1]]) return r.fulfill({ status: 200, contentType: 'text/javascript', headers: { 'Access-Control-Allow-Origin': '*' }, body: fs.readFileSync(path.join(V, MAP[m[1]])) });
    if (/fonts\.googleapis/.test(u)) return r.fulfill({ status: 200, contentType: 'text/css', body: '' });
    return r.abort();
  });
};
