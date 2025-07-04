import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

async function getWorkflow(name) {
	try {
		const response = await api.fetchApi(`/runcomfy/workflows?name=${name}`, { cache: "no-store" });
		if (response.status != 200) {
			return null;
		}
		return await response.json();
	} catch (error) {
		// Handle other errors
		console.error(error);
		return null;
	}
}

function hasPreloadedWorkflow() {
	var loaded = localStorage.getItem('runcomfy.has_preloaded_workflow');
	if (loaded) {
		return true
	} else {
		return false
	}
}

// ComfyUI version comparison helper function
function compareVersions(version1, version2) {
	const v1parts = version1.split('.').map(Number);
	const v2parts = version2.split('.').map(Number);

	for (let i = 0; i < Math.max(v1parts.length, v2parts.length); i++) {
		const v1part = v1parts[i] || 0;
		const v2part = v2parts[i] || 0;

		if (v1part > v2part) return 1;
		if (v1part < v2part) return -1;
	}
	return 0;
}

// Apply rgthree workaround only for ComfyUI version >= x.x.x
const frontendVersion = window.__COMFYUI_FRONTEND_VERSION__;
const useRgthreeWorkaround = frontendVersion && compareVersions(frontendVersion, "1.20.1") >= 0;
console.log(`[RunComfy] Frontend version: ${frontendVersion || 'unknown'}, using ${useRgthreeWorkaround ? 'rgthree workaround' : 'original implementation'}`);

if (useRgthreeWorkaround) {
	let isSuccessfullyLoaded = false;
	let lastSuccessfulLoadTime = 0;

	// backup original function
	const originalLoadGraphData = app.loadGraphData;
	app.loadGraphData = function (graph) {
		const incomingNodeCount = graph?.nodes?.length || 0;
		const currentNodeCount = app.graph?.nodes?.length || 0;
		const now = Date.now();

		// status check: Prevent rgthree's empty workflow "fix" from overriding loaded workflows
		const isRgthreeAutoFix = now - lastSuccessfulLoadTime < 1000;
		const isRgthreeOverride = incomingNodeCount === 0 &&
			currentNodeCount > 0 &&
			isSuccessfullyLoaded &&
			isRgthreeAutoFix;

		if (isRgthreeOverride) {
			console.log("[RunComfy] Prevented empty workflow override caused by rgthree link-fixer");
			return Promise.resolve();
		}

		// Track successful loads
		if (incomingNodeCount > 0) {
			isSuccessfullyLoaded = true;
			lastSuccessfulLoadTime = now;
		}

		return originalLoadGraphData.apply(this, arguments);
	};
}

app.registerExtension({
	name: "runcomfy.Workflows",
	async setup() {
		window.addEventListener('message', async (event) => {
			// Determine the target origin
			const targetOrigin = event.origin !== "null" && event.origin !== "" ? event.origin : "*";
			// if the event data is runcomfy.get_current_workflow, then send the graph data back to the parent
			if (event.data == "runcomfy.get_current_workflow") {
				const json = app.graph.serialize();
				console.log("helper got workflow", json)
				// Send response back to parent
				// wrap this json into a json object {event: "runcomfy.get_current_workflow", data: json}
				event.source.postMessage({ type: "workflow", event: "runcomfy.get_current_workflow", data: json }, targetOrigin);
			}
		});

		if (!hasPreloadedWorkflow()) {
			const customWorkflow = await getWorkflow();
			if (customWorkflow === null) {
				return;
			}
			await app.loadGraphData(customWorkflow);
			localStorage.setItem('runcomfy.has_preloaded_workflow', true);
			console.log("Custom workflow loaded by runcomfy.Workflows extension");
		}
	}

}); 
