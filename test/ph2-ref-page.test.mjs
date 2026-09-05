import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import test from 'node:test'

const read = path => readFileSync(path, 'utf8')

test('ph2-ref page uses relative assets and a configurable public data URL', () => {
  const html = read('public/ph2-ref/index.html')
  const app = read('public/ph2-ref/assets/app.js')
  const config = read('public/ph2-ref/assets/config.js')

  assert.match(html, /\.\/assets\/styles\.css/)
  assert.match(html, /\.\/assets\/config\.js/)
  assert.match(html, /\.\/assets\/app\.js/)
  assert.match(app, /300_000/)
  assert.match(app, /cache: 'no-store'/)
  assert.match(app, /window\.PH2_REF_DATA_URL/)
  assert.match(config, /raw\.githubusercontent\.com/)
})

test('ph2-ref public files do not expose internal data access terms', () => {
  const files = [
    'public/ph2-ref/index.html',
    'public/ph2-ref/assets/app.js',
    'public/ph2-ref/assets/config.js',
  ]
  const text = files.map(read).join('\n').toLowerCase()

  for (const forbidden of ['mysql', 'login-path', 'customer_code', 'database host']) {
    assert.equal(text.includes(forbidden), false, `${forbidden} must not be public`)
  }
})

test('vite build includes the ph2-ref entry point after the page is added', () => {
  assert.equal(existsSync('public/ph2-ref/index.html'), true)
})
