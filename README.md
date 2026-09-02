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
Each record is written to the ComfyUI server log as a single line:

```
[RunComfy perf] frontend load: {"canvas_ready_ms": 1187, ...}
```

Key fields per record:
- `canvas_ready_ms`: navigation start -> canvas ready (first painted frame
  after app setup finished and the initial workflow was loaded; if the tab is
  hidden, `painted` is false and the value is when readiness was reached).
  `null` with `incomplete: true` means the workflow had not finished loading
  within 5 minutes — treat it as a failed/extremely slow load, not a fast one.
  If it does finish later, a corrected record follows with `late: true`
- `load_id`: random id shared by all records of one page load, for joining
  and dedup. `abandoned: true` records are sent via `sendBeacon` when the
  page is torn down (refresh/close/navigation) before a final record went
  out; `abandoned_ms` is how long the user waited before giving up
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
	"logging":true
}
```
