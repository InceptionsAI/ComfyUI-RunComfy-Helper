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

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
// Double rAF: resolves after the next frame is actually painted.
const doublePaint = () => new Promise((resolve) =>
	requestAnimationFrame(() => requestAnimationFrame(resolve)));

let graphConfiguredMs = null;
let resolveGraphConfigured;
const graphConfigured = new Promise((resolve) => { resolveGraphConfigured = resolve; });

// How long to wait for the initial workflow configuration. Generous, so that
// genuinely slow loads are still reported with their true readiness time;
// only a load whose graph never configures at all becomes an incomplete
// record, explicitly marked instead of under-reported as a fast load.
const GRAPH_WAIT_MAX_MS = 120000;

async function measureAndReport(setupMs) {
	// On newer frontends the initial workflow is configured asynchronously
	// after setup(), so wait for that signal before reporting.
	const graphArrived = await Promise.race([
		graphConfigured.then(() => true),
		delay(GRAPH_WAIT_MAX_MS).then(() => false),
	]);

	// Wait until a frame after both signals is painted. rAF never fires in a
	// hidden/background tab, so race it against a timeout fallback and record
	// which path fired.
	const painted = await Promise.race([
		doublePaint().then(() => true),
		delay(3000).then(() => false),
	]);

	// On the fallback paths, fall back to the readiness timestamps so the
	// fallback delays themselves are not counted. An incomplete load gets
	// null rather than a fake early value.
	let canvasReadyMs = null;
	if (graphArrived) {
		canvasReadyMs = painted
			? Math.round(performance.now())
			: Math.max(setupMs, graphConfiguredMs);
	}

	const nav = performance.getEntriesByType("navigation")[0];
	const res = performance.getEntriesByType("resource");

	const payload = {
		canvas_ready_ms: canvasReadyMs,
		// true = the graph never configured within GRAPH_WAIT_MAX_MS
		incomplete: !graphArrived,
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
}

app.registerExtension({
	name: "runcomfy.Perf",
	afterConfigureGraph() {
		// First workflow actually loaded into the canvas
		if (graphConfiguredMs === null) {
			graphConfiguredMs = Math.round(performance.now());
			resolveGraphConfigured();
		}
	},
	setup() {
		// setup() runs at the end of app startup: canvas created, node types
		// registered. performance.now() is relative to navigation start, so it
		// directly measures "browser navigates -> canvas ready". Deliberately
		// not awaited: the app may await setup hooks, and the measurement
		// waits for signals that can arrive after them.
		measureAndReport(Math.round(performance.now()));
	},
});
