/**
 * RSC / hydration keyword grep (second pass).
 * Does NOT return concat text. Copy to /tmp and extend KEYS.
 *   python3 ~/.cursor/skills/use-my-browser/scripts/chrome_js_bridge.py file /tmp/<site>_rsc.js
 */
(function () {
  try {
    var KEYS = [
      "edpData",
      "seatManifest",
      "itemid",
      "shopid",
      "variables",
      "authorization",
      "contentDepth",
      "hasNextPage",
      "totalCount",
      "pageProps",
      "mosaic-provider-jobcards",
      "search_items"
    ];

    var parts = [];
    var n = 0;
    var scripts = document.getElementsByTagName("script");
    for (var i = 0; i < scripts.length; i++) {
      var t = scripts[i].textContent || "";
      if (t.indexOf("self.__next_f.push") >= 0 || t.indexOf("__next_f") >= 0) {
        n += 1;
        parts.push(t);
      }
    }
    var concat = parts.join("\n");
    var hits = [];
    for (var k = 0; k < KEYS.length; k++) {
      var idx = concat.indexOf(KEYS[k]);
      hits.push({
        key: KEYS[k],
        found: idx >= 0,
        index: idx
      });
    }

    var nextEl = document.getElementById("__NEXT_DATA__");
    var nextHits = [];
    var nextLen = 0;
    if (nextEl && nextEl.textContent) {
      nextLen = nextEl.textContent.length;
      for (k = 0; k < KEYS.length; k++) {
        nextHits.push({
          key: KEYS[k],
          found: nextEl.textContent.indexOf(KEYS[k]) >= 0
        });
      }
    }

    return JSON.stringify({
      url: location.href,
      rscPushScripts: n,
      rscConcatChars: concat.length,
      nextDataChars: nextLen,
      rscHits: hits,
      nextDataHits: nextHits,
      note: "Indices only; concat not returned."
    });
  } catch (err) {
    return JSON.stringify({ error: String(err && err.message ? err.message : err) });
  }
})();
