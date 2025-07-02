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

// Check if non-empty workflow is already loaded
function hasActiveWorkflow() {
    return app.graph && app.graph.nodes && app.graph.nodes.length > 0;
}

let isSuccessfullyLoaded = false;


const originalLoadGraphData = app.loadGraphData;
app.loadGraphData = function (graph) {
    const nodeCount = graph?.nodes?.length || 0;
    const currentNodeCount = app.graph?.nodes?.length || 0;

    // status check: Prevent rgthree's empty workflow "fix" from overriding loaded workflows
    const loadEmptyWorkflow = nodeCount === 0;
    const hasExistingWorkflow = currentNodeCount > 0;
    const isLikelyRgthreeFix = loadEmptyWorkflow && hasExistingWorkflow && isSuccessfullyLoaded;

    if (isLikelyRgthreeFix) {
        console.log("[RunComfy] Prevented empty workflow override caused by rgthree link-fixer");
        return Promise.resolve();
    }

    // Track successful loads
    if (nodeCount > 0) {
        isSuccessfullyLoaded = true;
    }

    return originalLoadGraphData.apply(this, arguments);
};

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

        // NEW: Add timing protection and workflow detection
        if (!hasPreloadedWorkflow()) {
            // Check if workflow is already loaded or being loaded
            if (hasActiveWorkflow()) {
                console.log("[RunComfy] Existing workflow detected, skipping auto-load");
                localStorage.setItem('runcomfy.has_preloaded_workflow', true);
                return;
            }

            const customWorkflow = await getWorkflow();
            if (customWorkflow === null) {
                return;
            }

            if (!hasActiveWorkflow()) {
                try {
                    await app.loadGraphData(customWorkflow);
                    localStorage.setItem('runcomfy.has_preloaded_workflow', true);
                    console.log("Custom workflow loaded by runcomfy.Workflows extension");
                } catch (error) {
                    console.error("[RunComfy] Failed to load custom workflow:", error);
                }
            }
        }
    }

}); 