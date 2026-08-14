/**
 * Generic page probe for website-page-research.
 * Copy to /tmp/<site>_probe.js, optionally edit EXTRA_KEYS, then:
 *   python3 ~/.cursor/skills/use-my-browser/scripts/chrome_js_bridge.py file /tmp/<site>_probe.js
 * Must evaluate to a string. Bounded. No cookie values. No full hydration blobs.
 */
(function () {
  try {
    var EXTRA_KEYS = [
      "edpData",
      "seatManifest",
      "itemid",
      "shopid",
      "pageProps",
      "mosaic-provider-jobcards"
    ];

    function cap(arr, n) {
      n = n || 40;
      if (!arr) return [];
      var a = Array.prototype.slice.call(arr, 0, n);
      return a;
    }

    function uniq(arr) {
      var o = {}, out = [];
      for (var i = 0; i < arr.length; i++) {
        var k = String(arr[i] || "");
        if (!k || o[k]) continue;
        o[k] = 1;
        out.push(k);
      }
      return out;
    }

    function topKeys(obj, n) {
      if (!obj || typeof obj !== "object") return [];
      return cap(Object.keys(obj), n || 40);
    }

    function scriptKw(hay) {
      var words = [
        "next", "apollo", "graphql", "urql", "redux", "relay",
        "captcha", "cloudflare", "challenge", "datadome", "kasada",
        "akamai", "bot", "turnstile", "recaptcha", "hcaptcha",
        "__NEXT_DATA__", "__next_f", "__NUXT__", "page-data.json",
        "pcmall", "mosaic"
      ];
      var hits = [];
      var low = hay.toLowerCase();
      for (var i = 0; i < words.length; i++) {
        if (low.indexOf(words[i].toLowerCase()) >= 0) hits.push(words[i]);
      }
      return hits;
    }

    var html = document.documentElement ? document.documentElement.innerHTML : "";
    var htmlLen = html.length;
    var htmlHead = html.slice(0, 400000);

    var nextEl = document.getElementById("__NEXT_DATA__");
    var nextInfo = { present: !!nextEl, textLen: 0, pagePropsKeys: [], siblingHint: [] };
    if (nextEl && nextEl.textContent) {
      nextInfo.textLen = nextEl.textContent.length;
      try {
        var nd = JSON.parse(nextEl.textContent);
        var pp = nd && nd.props && nd.props.pageProps;
        if (pp && typeof pp === "object") {
          nextInfo.pagePropsKeys = topKeys(pp, 50);
          nextInfo.siblingHint = nextInfo.pagePropsKeys.slice();
        } else {
          nextInfo.pagePropsKeys = topKeys(nd, 30);
        }
      } catch (e) {
        nextInfo.parseError = String(e.message || e);
      }
    }

    var rscScripts = 0;
    var rscConcat = 0;
    var scripts = document.getElementsByTagName("script");
    var i;
    for (i = 0; i < scripts.length; i++) {
      var t = scripts[i].textContent || "";
      if (t.indexOf("self.__next_f.push") >= 0) {
        rscScripts += 1;
        rscConcat += t.length;
      }
    }

    var ld = [];
    var ldNodes = document.querySelectorAll('script[type="application/ld+json"]');
    for (i = 0; i < Math.min(ldNodes.length, 12); i++) {
      try {
        var parsed = JSON.parse(ldNodes[i].textContent || "null");
        var types = [];
        function walkType(x, depth) {
          if (!x || depth > 4) return;
          if (Array.isArray(x)) {
            for (var j = 0; j < Math.min(x.length, 8); j++) walkType(x[j], depth + 1);
            return;
          }
          if (typeof x === "object") {
            if (x["@type"]) types.push(x["@type"]);
            var ks = Object.keys(x);
            for (var k = 0; k < Math.min(ks.length, 20); k++) {
              if (ks[k].indexOf("@") === 0) continue;
              var v = x[ks[k]];
              if (v && typeof v === "object") walkType(v, depth + 1);
            }
          }
        }
        walkType(parsed, 0);
        ld.push({
          types: cap(uniq(types), 12),
          topKeys: topKeys(Array.isArray(parsed) ? { arr: true, len: parsed.length } : parsed, 20),
          arrayDepthHint: Array.isArray(parsed)
        });
      } catch (e) {
        ld.push({ parseError: String(e.message || e) });
      }
    }

    function attrList(sel, attr, n) {
      var nodes = document.querySelectorAll(sel);
      var vals = [];
      for (var j = 0; j < Math.min(nodes.length, n || 80); j++) {
        var v = nodes[j].getAttribute(attr);
        if (v) vals.push(v);
      }
      return { count: document.querySelectorAll(sel).length, sample: cap(uniq(vals), 40) };
    }

    var testid = attrList("[data-testid]", "data-testid", 80);
    var datatest = attrList("[data-test]", "data-test", 80);
    var itemprop = attrList("[itemprop]", "itemprop", 40);

    var classStems = [];
    var clsNodes = document.querySelectorAll("[class]");
    for (i = 0; i < Math.min(clsNodes.length, 120); i++) {
      var parts = String(clsNodes[i].className || "").split(/\s+/);
      for (var p = 0; p < parts.length; p++) {
        var stem = parts[p].replace(/__[\w-]+$/g, "").replace(/_[a-zA-Z0-9]{5,}$/g, "");
        if (stem && stem.length > 2 && stem.length < 40) classStems.push(stem);
      }
    }
    classStems = cap(uniq(classStems), 30);

    var controls = {
      relNext: !!document.querySelector("a[rel='next']"),
      loadMoreText: !!document.querySelector(
        "button, a, [role='button']"
      ),
      loadMoreHint: (function () {
        var els = document.querySelectorAll("button, a, [role='button']");
        var hits = [];
        for (var j = 0; j < Math.min(els.length, 80); j++) {
          var tx = (els[j].innerText || els[j].getAttribute("aria-label") || "").toLowerCase();
          if (/load more|show more|next|更多|下一/.test(tx)) {
            hits.push((els[j].getAttribute("data-test") || els[j].getAttribute("data-testid") || tx.slice(0, 40)));
          }
        }
        return cap(uniq(hits), 10);
      })()
    };

    var h1 = "";
    var h1el = document.querySelector("h1");
    if (h1el) h1 = String(h1el.innerText || "").slice(0, 120);

    var extraHits = {};
    var searchHay = htmlHead;
    if (nextEl && nextEl.textContent) searchHay += "\n" + nextEl.textContent.slice(0, 200000);
    for (i = 0; i < EXTRA_KEYS.length; i++) {
      var key = EXTRA_KEYS[i];
      extraHits[key] = searchHay.indexOf(key) >= 0;
    }

    var cookieNames = [];
    try {
      var cs = document.cookie ? document.cookie.split(";") : [];
      for (i = 0; i < cs.length; i++) {
        var nm = cs[i].split("=")[0].trim();
        if (nm) cookieNames.push(nm);
      }
    } catch (e) {}

    var gateRe = /sign in to unlock|please log in|login required|verify\/traffic|access denied|are you a robot|unusual traffic|enable javascript/i;
    var bodyText = document.body ? String(document.body.innerText || "").slice(0, 8000) : "";
    var gateHits = [];
    var gm = bodyText.match(gateRe);
    if (gm) gateHits.push(gm[0]);
    if (/\/verify\//i.test(location.href)) gateHits.push("url:/verify/");
    if (/identify/i.test(bodyText.slice(0, 400))) gateHits.push("body:identify");

    var iframes = document.getElementsByTagName("iframe");
    var captchaIframes = 0;
    for (i = 0; i < iframes.length; i++) {
      var src = (iframes[i].src || "") + (iframes[i].title || "");
      if (/captcha|recaptcha|hcaptcha|turnstile|challenge/i.test(src)) captchaIframes += 1;
    }

    var resources = [];
    try {
      var entries = performance.getEntriesByType("resource") || [];
      var byHost = {};
      for (i = 0; i < entries.length; i++) {
        var e = entries[i];
        var name = e.name || "";
        var host = "";
        var path = "";
        try {
          var u = new URL(name, location.href);
          host = u.host;
          path = u.pathname.split("/").slice(0, 4).join("/");
        } catch (err) {
          continue;
        }
        var bucket = host + " " + path;
        if (!byHost[bucket]) byHost[bucket] = { host: host, pathPrefix: path, initiator: e.initiatorType, n: 0 };
        byHost[bucket].n += 1;
      }
      var buckets = [];
      for (var b in byHost) buckets.push(byHost[b]);
      buckets.sort(function (a, c) { return c.n - a.n; });
      resources = cap(buckets, 35);
    } catch (e) {
      resources = [{ error: String(e.message || e) }];
    }

    var assetPrefixes = [];
    for (i = 0; i < Math.min(scripts.length, 40); i++) {
      var ssrc = scripts[i].src || "";
      if (!ssrc) continue;
      try {
        var su = new URL(ssrc, location.href);
        assetPrefixes.push(su.pathname.split("/").slice(0, 3).join("/"));
      } catch (err) {}
    }

    var winNames = [];
    try {
      for (var w in window) {
        if (w.indexOf("__") === 0) winNames.push(w);
      }
    } catch (e) {}

    var out = {
      url: location.href,
      title: String(document.title || "").slice(0, 180),
      h1: h1,
      ready: document.readyState,
      bodyLen: document.body ? (document.body.innerText || "").length : 0,
      htmlLen: htmlLen,
      canonical: (function () {
        var l = document.querySelector("link[rel='canonical']");
        return l ? l.href : null;
      })(),
      render: {
        nextData: nextInfo,
        rscPushScripts: rscScripts,
        rscConcatChars: rscConcat,
        nuxt: typeof window.__NUXT__ !== "undefined",
        gatsbyHint: htmlHead.indexOf("page-data.json") >= 0,
        assetPathPrefixes: cap(uniq(assetPrefixes), 15)
      },
      jsonld: ld,
      extraKeyHits: extraHits,
      dom: {
        dataTestid: testid,
        dataTest: datatest,
        itemprop: itemprop,
        classStems: classStems,
        controls: controls
      },
      resources: resources,
      scriptKeywords: scriptKw(htmlHead),
      cookieNames: cap(uniq(cookieNames), 40),
      gateHits: cap(uniq(gateHits), 10),
      captchaIframes: captchaIframes,
      iframeCount: iframes.length,
      windowDunder: cap(uniq(winNames), 25),
      note: "No cookie values; no full blobs. Sibling keys listed under render.nextData.pagePropsKeys."
    };
    return JSON.stringify(out);
  } catch (err) {
    return JSON.stringify({ error: String(err && err.message ? err.message : err) });
  }
})();
