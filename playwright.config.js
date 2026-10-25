const { defineConfig } = require('@playwright/test');
const { existsSync } = require('node:fs');
const python = process.env.DESPENSA_PYTHON || (existsSync('.venv/bin/python') ? '.venv/bin/python' : 'python3');
module.exports = defineConfig({
  testDir: './tests/browser',
  workers: 1,
  use: {baseURL: 'http://127.0.0.1:38108', locale: 'pt-PT', viewport: {width: 390, height: 844}},
  webServer: {command: `${python} tests/serve.py`, url: 'http://127.0.0.1:38108/api/health', reuseExistingServer: false},
});
