# SLZ ERP Frontend Dev Server — Run Doc

## Reproduce artifacts

1. **Install dependencies** (lockfile-exact):
   ```bash
   cd erp/frontend
   npm ci
   ```

2. **Copy the environment file** from the main checkout:
   ```bash
   cp erp/frontend/.env.example erp/frontend/.env
   ```
   `.env.example` contains only `VITE_API_BASE_URL=http://localhost:8000/api/v1`.
   No secrets are needed for the frontend dev server.

3. **Allow esbuild native binaries** if blocked by npm's `allowScripts` policy:
   ```bash
   cd erp/frontend
   npx esbuild --version   # if this fails, run:
   npm rebuild esbuild
   ```

## Run the dev server

The project uses Vite on its default port 5173. To start detached (outliving this session):

```bash
cd /e/Code/Project/ERP/erp/frontend
node /e/Code/Project/ERP/.freebuff/launch.mjs
```

This spawns a detached Vite process that logs to:
- stdout: `.freebuff/preview-a3e0e531-4678-4162-9517-adbb7a728fe3.log`
- stderr: `.freebuff/preview-a3e0e531-4678-4162-9517-adbb7a728fe3.log.err`

The PID is written to `.freebuff/vite-pid.txt`.

Verify it is alive:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173   # → 200
```

## Port

Default: **5173**. If occupied, Vite auto-increments. Check the log for the actual port if the default is taken.