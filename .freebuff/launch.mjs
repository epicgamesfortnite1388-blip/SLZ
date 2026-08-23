import { spawn } from 'child_process';
import { writeFileSync, openSync } from 'fs';

const logFd = openSync('E:/Code/Project/ERP/.freebuff/preview-a3e0e531-4678-4162-9517-adbb7a728fe3.log', 'a');
const errFd = openSync('E:/Code/Project/ERP/.freebuff/preview-a3e0e531-4678-4162-9517-adbb7a728fe3.log.err', 'a');

const child = spawn(process.execPath, [
  'E:/Code/Project/ERP/erp/frontend/node_modules/vite/bin/vite.js',
  '--port', '5173',
  '--host', '0.0.0.0'
], {
  cwd: 'E:/Code/Project/ERP/erp/frontend',
  detached: true,
  stdio: ['ignore', logFd, errFd]
});

writeFileSync('E:/Code/Project/ERP/.freebuff/vite-pid.txt', String(child.pid));
child.unref();
console.log('PID=' + child.pid);
process.exit(0);