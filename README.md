# ComfyUI-RunComfy-Helper
## Usage
- curl http://localhost:8188/runcomfy/workflows
- curl -X POST http://localhost:8188/runcomfy/workflows \
     -H "Content-Type: application/json" \
     -d '{
           "workflows": [
             {
               "file_name": "file1.json",
               "workflow": {
                 "exampleKey": "exampleValue"
               },
               "default":true
             }
           ]
         }'
## Frontend load time
`web/perf.js` measures the time from the browser starting to navigate until the
ComfyUI canvas is ready (plus a breakdown: TTFB, JS bundles, `/object_info`,
custom node extensions), and reports it to the server on every page load.
Records are appended to `<comfyui>/runcomfy/perf/frontend_load.jsonl` (size-
rotated, one previous generation kept) and logged to the server log.

- Read recent records: `curl http://localhost:8188/runcomfy/perf?limit=50`

Key fields per record:
- `canvas_ready_ms`: navigation start -> canvas ready (first painted frame
  after app setup finished and the initial workflow was loaded; if the tab is
  hidden, `painted` is false and the value is when readiness was reached)
- `graph_configured_ms`: navigation start -> first workflow loaded into the canvas
- `object_info` / `bundles` / `node_extensions`: `{count, span_ms, bytes, cached}`
  per resource group; `cached: true` means served from the browser cache

## Config
```
{
	"workflows": {
		"directory": "runcomfy/workflows",
		"default": "default.json"
	},
	"perf": {
		"directory": "runcomfy/perf"
	},
	"logging":true
}
```
