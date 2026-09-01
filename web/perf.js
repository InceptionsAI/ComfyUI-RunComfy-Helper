import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

// The default resource timing buffer (250 entries) can overflow on installs
// with many custom node scripts, dropping the entries we want to report.
performance.setResourceTimingBufferSize(4096);

// Aggregate the resource timing entries whose URL matches `match` into a
// single {count, span_ms, bytes, cached} summary. span_ms is the wall time
// from the first matching request starting to the last one finishing.
function agg(entries, match) {
	const list = entries.filter((e) => match(e.name));
	if (!list.length) return null;
	const start = Math.min(...list.map((e) => e.startTime));
	const end = Math.max(...list.map((e) => e.responseEnd));
	return {
		count: list.length,
		span_ms: Math.round(end - start),
		bytes: list.reduce((s, e) => s + (e.transferSize || 0), 0),
		// transferSize === 0 means the response came from the browser cache
		cached: list.every((e) => e.transferSize === 0),
	};
}

let graphConfiguredMs = null;

app.registerExtension({
	name: "runcomfy.Perf",
	afterConfigureGraph() {
		// First workflow actually loaded into the canvas
		if (graphConfiguredMs === null) {
			graphConfiguredMs = Math.round(performance.now());
		}
	},
	setup() {
		// setup() runs at the end of app startup: canvas created, node types
		// registered, initial workflow loaded. Double rAF waits until the
		// first frame after that is actually painted. performance.now() is
		// relative to navigation start, so it directly measures
		// "browser navigates -> canvas visible".
		// rAF never fires in a hidden/background tab, so race it against a
		// timeout fallback and record whether the frame was actually painted.
		// On the fallback path, use the time setup() was entered so the
		// fallback delay itself is not counted.
		const setupMs = Math.round(performance.now());
		let reported = false;
		const report = (painted) => {
			if (reported) return;
			reported = true;
			const canvasReadyMs = painted ? Math.round(performance.now()) : setupMs;
			const nav = performance.getEntriesByType("navigation")[0];
			const res = performance.getEntriesByType("resource");

			const payload = {
				canvas_ready_ms: canvasReadyMs,
				setup_ms: setupMs,
				graph_configured_ms: graphConfiguredMs,
				painted: painted,
				visibility: document.visibilityState,
				ttfb_ms: nav ? Math.round(nav.responseStart) : null,
				html_ms: nav ? Math.round(nav.responseEnd) : null,
				dom_content_loaded_ms: nav ? Math.round(nav.domContentLoadedEventEnd) : null,
				// Node definitions JSON, usually the biggest single item
				object_info: agg(res, (n) => n.includes("/object_info")),
				// Frontend JS/CSS bundles from comfyui_frontend_package
				bundles: agg(res, (n) => n.includes("/assets/")),
				// Custom node web extensions
				node_extensions: agg(res, (n) => n.includes("/extensions/")),
				api_misc: agg(res, (n) => /\/api\/(settings|userdata|users|i18n)/.test(n)),
				templates: agg(res, (n) => n.includes("/templates")),
				resources_total: agg(res, () => true),
				page: location.pathname,
			};

			console.log("[RunComfy] frontend load", payload);
			api.fetchApi("/runcomfy/perf", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(payload),
			}).catch((e) => console.warn("[RunComfy] perf beacon failed", e));
		};

		requestAnimationFrame(() => requestAnimationFrame(() => report(true)));
		setTimeout(() => report(false), 3000);
	},
});
