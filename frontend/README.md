# Frontend Service

The frontend provides video selection, optional camera configuration, job status, measured metrics, artifact downloads, and an interactive Three.js reconstruction viewer. On Lightning AI it runs on port 5173 and proxies `/api` to the backend on port 8000.

## Project-layout requirement

Keep the complete repository structure intact. Frontend setup is folder-local, but the hosted runtime depends on the backend and shared deployment scripts in the parent project.

## Lightning AI installation

Run from the `frontend/` directory:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM/frontend
bash setup-lightning.sh
```

The script selects Node.js 22.12 or newer, installs the locked npm dependencies with `npm ci`, checks TypeScript, and creates the hosted build with `npm run build:hosted`. It does not install backend or native dependencies.

Equivalent commands with a compatible Node.js version already active:

```bash
npm ci
npm run build:hosted
```

## Start the frontend

```bash
bash run-lightning.sh
```

The hosted frontend listens on `0.0.0.0:5173`. Keep the terminal running.

## Proxy verification

The backend must already be running on port 8000. From another terminal:

```bash
curl --fail http://127.0.0.1:5173/api/health
```

A healthy response confirms that the frontend route and backend proxy are operational.

## Public exposure

Use the Lightning Ports tool to make port 5173 public. Port 8000 can remain private because browser API requests use the frontend origin and `/api` proxy.

## Common failures

| Error | Action |
|---|---|
| `Missing script: build:hosted` | Synchronize the current `package.json`, Vite config, hosted app config, and deployment scripts |
| Frontend reports engine unavailable | Verify the backend direct health URL and confirm port 8000 is active |
| Public URL returns 502 | Wake the Studio, restart both services, and verify port 5173 visibility |
| Port 5173 already in use | Stop the existing frontend process before restarting |

See [../lightning/README.md](../lightning/README.md) for the complete two-service deployment procedure.
