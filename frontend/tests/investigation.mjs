import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const base = process.env.MC3_BASE_URL || 'http://127.0.0.1:8000'
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } })
const errors = []
page.on('pageerror', error => errors.push(error.message))
try {
  await page.goto(base, { waitUntil: 'networkidle' })
  await page.getByTestId('workspace-investigation').click()
  assert.equal(await page.getByLabel('比较类型', { exact: true }).count(), 1)
  await page.getByLabel('比较类型', { exact: true }).selectOption('Vessel')
  await page.waitForFunction(() => document.querySelector('[data-testid="alias-select"]')?.value === 'Mako')
  await page.waitForFunction(() => document.querySelectorAll('[data-testid="role-link"]').length === 4)
  const api = await (await page.request.get(`${base}/api/aliases?alias=Mako`)).json()
  assert.equal(await page.getByTestId('alias-candidate').count(), Math.min(3, api.items.length))
  if (api.items.length > 3) await page.getByRole('button', { name: /展开全部.*候选/ }).click()
  assert.deepEqual(await page.getByTestId('alias-candidate').locator(':scope > span:first-child').allTextContents(),
    api.items.map(row => row.candidate))
  await page.locator('.role-links summary').click()
  await page.getByRole('button', { name: 'Relationship_Operates_75', exact: true }).click()
  await page.getByTestId('detail-id').filter({ hasText: 'Relationship_Operates_75' }).waitFor()
  assert.match(await page.locator('.detail-pane').innerText(), /Event_Communication_142/)
  const pending = page.waitForEvent('download')
  await page.getByRole('button', { name: '↓ 导出比较与人工标记', exact: true }).click()
  const data = JSON.parse(await readFile(await (await pending).path(), 'utf8'))
  assert.equal(data.alias_type, 'Vessel')
  assert.equal(data.role_links.items.length, 4)
  assert(data.role_links.items.every(row => !('score' in row)))
  assert.equal(data.period_profiles.segments.reduce((sum, row) => sum + row.count, 0), 93)
  await page.locator('.period-profiles summary').click()
  assert.equal(await page.getByTestId('period-profile').count(), 2)
  const period = data.period_profiles.segments[0]
  await page.getByTestId('period-messages').first().click()
  await page.waitForFunction(expected => document.querySelector('[data-testid="message-total"]')?.textContent === String(expected), period.count)
  console.log('PASS Vessel candidates, original operator roles, evidence and export agree')

  await page.getByLabel('候选集合').selectOption(api.items[0].candidate)
  await page.getByLabel('比较类型', { exact: true }).selectOption('Person')
  await page.waitForFunction(() => document.querySelector('[data-testid="alias-select"]')?.value === 'Boss' &&
    document.querySelector('[data-testid="alias-candidate"]')?.textContent.includes('Nadia Conti'))
  assert.equal(await page.getByLabel('候选集合').inputValue(), '')
  assert.equal(await page.locator('.alias-panel .error').count(), 0)
  console.log('PASS Switching types clears incompatible candidates and restores Person comparisons')

  await page.getByLabel('比较类型', { exact: true }).selectOption('Vessel')
  await page.waitForFunction(() => document.querySelectorAll('[data-testid="role-link"]').length === 4)
  await page.getByTestId('start-date').fill('2050-01-01')
  await page.getByTestId('end-date').fill('2050-01-02')
  await page.waitForFunction(() => document.querySelector('[data-testid="communication-count"]')?.textContent === '0')
  await page.waitForFunction(() => document.querySelectorAll('[data-testid="alias-candidate"]').length === 0 &&
    document.querySelectorAll('[data-testid="role-link"]').length === 0)
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
  assert.deepEqual(errors, [])
  console.log('PASS Empty filters clear both candidates and roles without page overflow')
  await page.getByTestId('reset').click()
  await page.getByTestId('search').fill('Event_Communication_805')
  await page.getByRole('button', { name: '检索', exact: true }).click()
  await page.getByTestId('detail-id').filter({ hasText: 'Event_Communication_805' }).waitFor()
  assert.equal(await page.locator('.message-checks').count(), 1)
  assert.match(await page.locator('.message-checks').innerText(), /自称 Davis/)
  await page.locator('.message-checks').getByRole('button', { name: 'Event_Communication_804', exact: true }).click()
  await page.getByTestId('detail-id').filter({ hasText: 'Event_Communication_804' }).waitFor()
  await page.getByTestId('reset').click()
  await page.getByTestId('search').fill('Event_Communication_161')
  await page.getByRole('button', { name: '检索', exact: true }).click()
  await page.getByTestId('detail-id').filter({ hasText: 'Event_Communication_161' }).waitFor()
  await page.locator('.nearby-exchange summary').click()
  await page.locator('.nearby-exchange').getByRole('button', { name: 'Event_Communication_162', exact: true }).click()
  await page.getByTestId('detail-id').filter({ hasText: 'Event_Communication_162' }).waitFor()
  console.log('PASS Source conflicts and duplicate/nearby communication links retain original evidence')
} finally {
  await browser.close()
}
