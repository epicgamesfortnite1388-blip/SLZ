// Launch Django backend server detached, print PID
import { spawn } from 'child_process';
import { resolve } from 'path';
import { writeFileSync } from 'fs';

const backendDir = resolve('E:/Code/Project/ERP/erp/backend');
const logFile = 'E:/Code/Project/ERP/.freebuff/backend-preview.log';
const errLog = 'E:/Code/Project/ERP/.freebuff/backend-preview.err.log';
const pidFile = 'E:/Code/Project/ERP/.freebuff/backend-pid.txt';

const child = spawn(
  process.platform === 'win32' ? 'python.exe' : 'python',
  ['manage.py', 'runserver', '0.0.0.0:8000', '--noreload'],
  {
    cwd: backendDir,
    env: {
      ...process.env,
      DJANGO_SETTINGS_MODULE: 'config.settings.local',
    },
    detached: true,
    stdio: ['ignore', 'ignore', 'ignore'],
  }
);

writeFileSync(pidFile, String(child.pid));
console.log(`BACKEND_PID=${child.pid}`);

writeFileSync(logFile, `Backend started PID=${child.pid}\n`);
writeFileSync(errLog, '');

child.unref();