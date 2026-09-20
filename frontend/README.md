# Frontend on Lightning AI

From this `frontend/` folder, I install and start the frontend:

```bash
bash setup-lightning.sh
bash run-lightning.sh
```

My setup selects Node, installs npm dependencies, and builds the hosted UI. I keep backend setup/start separate in `../backend`, while retaining the complete project folder structure.

When Node >=22.12 is already on PATH, the equivalent install/build commands here are:

```bash
npm ci
npm run build:hosted
```

If `build:hosted` is missing, synchronize the updated `package.json`, `vite.config.ts`, `public-hosted/app-config.json`, and deployment scripts from the current project. The old source bundle does not contain later deployment edits.

Keep the frontend running and check from another terminal:

```bash
curl --fail http://127.0.0.1:5173/api/health
```

The frontend proxies `/api` to the running backend on 8000. Expose port 5173 in Lightning's Ports tool and copy its public HTTPS link. See [the complete Studio guide](../lightning/README.md).
