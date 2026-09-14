
## 2026-09-14 — Public exposure: erp.slz.dpdns.org + superuser (Buffy)
**Discovery:** VPS public IP 208.72.218.131 (matches user's DNS A record; zone slz.dpdns.org is on Cloudflare NS).
External TCP probes (check-host.net multi-node): inbound 22/80/443/8080 ALL filtered → provider NAT blocks all inbound ports. Hairpin NAT also fails from the VPS itself.
**Decision:** publish via Cloudflare Tunnel (outbound-only), which is also the architecture the repo's own nginx.conf documents ("fronted by the Cloudflare Tunnel connector").
**Changes:**
- erp/.env (gitignored): DJANGO_ALLOWED_HOSTS += erp.slz.dpdns.org; CORS_ALLOWED_ORIGINS += https://erp.slz.dpdns.org
- docker-compose.prod.yml (local edit, to commit): frontend ports 127.0.0.1:80:80 → 127.0.0.1:8080:80 (loopback; tunnel ingress targets 8080)
- Host nginx installed; phase-1 vhost erp.slz.dpdns.org (80: ACME + 301→https) — kept as fallback if provider opens ports later; no certbot needed while TLS terminates at Cloudflare edge
- cloudflared 2026.9.1 installed from pkg.cloudflare.com; /etc/cloudflared/config.yml + systemd unit staged (awaits account authorization for cert.pem)
- Superuser created: username abystral / email abystral@slz.local (login key: EMAIL abystral@slz.local; password set as requested) — verified via live API login (access token issued)
**Verification:** /ready/ green via 127.0.0.1:8080; SPA 200 incl. deep links; API 401 on anon login POST (correct).

## 2026-09-14 — Browser E2E (Playwright) + P0 fix: baked-in dev API base URL (Buffy)
- Installed Playwright + headless Chromium on the VPS; provisioned scoped E2E user (e2e@slz.local, role `e2e_role`, view/manage master-data+org perms, company A only).
- **P0 found live:** built SPA called `http://localhost:8000/api/v1` (dev default in `src/api/client.ts`, no VITE_API_BASE_URL in image build) → every API call blocked by the app's own CSP `connect-src 'self'`. UI was dead-on-arrival in the real deployment; unit tests never caught it (jsdom mocks fetch).
- **Fix (d310a41):** DEFAULT_BASE_URL → same-origin `/api/v1` (nginx already proxies /api/), Vite dev proxy added for dev parity, .env.example override commented. Rebuilt frontend image; gates: typecheck ✓ lint ✓ 109/109 ✓.
- **E2E results: 18/18 PASS, no page errors** — login UI, fa default + dir=rtl, sidebar collapse + localStorage persistence, no overflow, re-expand, en/ltr switch, UoM list→edit→save→backend persistence (verified via API), mobile hamburger/drawer/Escape, mobile RTL.

## 2026-09-14 — Public access delivered via interim Cloudflare quick tunnel (Buffy)
- cloudflared login cert hand-off fails deterministically on this headless host ("Failed to fetch resource" x2 after user authorized — known limitation: callback delivers cert to the browser's machine).
- Workaround: transient `systemd-run` unit cfquick2 running `cloudflared tunnel --url http://127.0.0.1:8080` (no credentials needed) → https://accompanied-sussex-shopzilla-ericsson.trycloudflare.com
- Interim gotcha fixed: /etc/cloudflared/config.yml.staged-for-erp moved aside (it was auto-loaded and 404ing all paths); .trycloudflare.com added to DJANGO_ALLOWED_HOSTS for the interim URL only.
- Verified through real public edge: SPA 200, deep links 200, /ready/ green, superuser login issues token, headless-browser UI login OK (RTL, zero page errors).
- Caveats: quick-tunnel hostname is ephemeral (changes on restart; unit has no restart policy — reboot kills it). Permanent erp.slz.dpdns.org still needs cert.pem / tunnel token / API token from the user; ingress config staged and ready.
