import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile, writeFile } from 'node:fs/promises'

const base = process.env.MC3_BASE_URL || 'http://127.0.0.1:8000'
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } })
const errors = [], results = []
page.on('pageerror', error => errors.push(error.message))
const api = async path => (await page.request.get(`${base}/api/${path}`)).json()
const sorted = ids => [...ids].sort()
const count = expected => page.waitForFunction(value =>
  document.querySelector('[data-testid="communication-count"]')?.textContent === String(value), expected)
async function download(button, format = 'json') {
  const pending = page.waitForEvent('download')
  await button.click()
  const body = await readFile(await (await pending).path(), 'utf8')
  return format === 'json' ? JSON.parse(body) : body
}
async function check(name, fn) {
  await fn()
  results.push({ name, status: 'passed' })
  console.log(`PASS ${name}`)
}
try {
  await page.goto(base, { waitUntil: 'networkidle' })
  await page.getByTestId('workspace-patterns').click()
  await count(584)
  await check('Q1: dense-hour investigation and offline report preserve direction, scope and source text', async () => {
    await page.getByTestId('peak-cell').filter({ hasText: '10-05 10:00' }).click()
    await count(24)
    const expected = await api('messages?start=2040-10-05&end=2040-10-05&hour=10&page_size=100')
    const html = await download(page.getByRole('button', { name: '↓ 导出报告', exact: true }), 'html')
    const report = await browser.newPage()
    await report.setContent(html)
    assert.deepEqual(await report.locator('.message-record h3').allTextContents(), expected.items.map(m => m.id))
    assert.deepEqual(await report.locator('.message-record > p:not(.meta)').allTextContents(), expected.items.map(m => m.content))
    assert.equal(await report.locator('script').count(), 0)
    await report.close()
    const influence = await api('evidence/Event_Communication_161')
    assert(influence.nearby_exchange.some(m => m.id === 'Event_Communication_162'))
  })
  await page.getByTestId('reset').click(); await count(584)
  await page.getByTestId('workspace-groups').click()
  await check('Q2: model details open on demand and group selection exports only the selected official records', async () => {
    await page.getByTestId('topic-matrix').waitFor()
    assert.equal(await page.getByTestId('topic-reliability').isVisible(), false)
    await page.locator('.model-note summary').click()
    assert.match(await page.getByTestId('topic-reliability').innerText(), /敏感/)
    await page.locator('.model-note summary').click()
    const data = await api('topics')
    const group = data.groups[0], topic = group.counts.findIndex(n => n > 0)
    await page.getByRole('button', { name: `社区 ${group.id + 1} 主题 ${topic + 1}，${group.counts[topic]} 条通信`, exact: true }).click()
    await page.waitForFunction(() => document.querySelectorAll('[data-testid="topic-sample"]').length > 0 &&
      !document.querySelector('.topic-view')?.getAttribute('aria-busy')?.includes('true'))
    const exported = await download(page.getByRole('button', { name: '导出模型与来源', exact: true }))
    assert.equal(exported.model.version, data.model.version)
    assert.deepEqual(sorted(exported.selected_scope.message_ids), sorted(group.message_ids[topic]))
    assert(exported.selected_scope.sample_ids.every(id => exported.selected_scope.message_ids.includes(id)))
    for (const n of [4, 8, 6]) {
      await page.getByLabel('主题数量').selectOption(String(n))
      await page.waitForFunction(expected => document.querySelectorAll('[data-testid="topic-matrix"] thead button').length === expected, n)
      const model = await download(page.getByRole('button', { name: '导出模型与来源', exact: true }))
      assert.equal(model.model.topic_count, n)
      assert.equal(model.topics.reduce((sum, t) => sum + t.count, 0) + model.unassigned, 584)
      assert.equal(model.selected_scope.group_id, null)
    }
  })
  await page.getByTestId('workspace-investigation').click()
  await check('Q3: Person/Vessel comparison preserves candidate uncertainty and original role evidence', async () => {
    await page.getByTestId('alias-select').selectOption('The Intern')
    const sam = page.getByTestId('alias-candidate').filter({ has: page.locator('span:first-child', { hasText: /^Sam$/ }) })
    await sam.click()
    const person = await download(page.getByRole('button', { name: '↓ 导出比较与人工标记', exact: true }))
    assert.equal(person.alias, 'The Intern'); assert.equal(person.candidate.candidate, 'Sam')
    assert.match(person.interpretation, /不确认身份/)
    await page.getByLabel('比较类型', { exact: true }).selectOption('Vessel')
    await page.waitForFunction(() => document.querySelectorAll('[data-testid="role-link"]').length === 4)
    const vessel = await download(page.getByRole('button', { name: '↓ 导出比较与人工标记', exact: true }))
    assert.equal(vessel.alias, 'Mako'); assert.equal(vessel.alias_type, 'Vessel')
    assert.equal(vessel.period_profiles.segments.reduce((sum, p) => sum + p.count, 0), 93)
    assert(vessel.role_links.items.some(row => row.relationship_id === 'Relationship_Operates_75' && row.all_evidence_ids.includes('Event_Communication_142')))
  })
  await check('Q4: Nadia event overview and export include every selected event with raw support and time', async () => {
    await page.getByRole('button', { name: '调查 Nadia Conti ↗', exact: true }).click()
    await count(26)
    await page.waitForFunction(() => document.querySelector('.event-panel .panel-note')?.textContent.startsWith('15 个事件'))
    assert.equal(await page.getByTestId('event-swimlane').locator('g.swimlane-event').count(), 13)
    const expected = await api('events/timeline?entity_id=Nadia%20Conti&page_size=100')
    const exported = await download(page.locator('.event-panel').getByRole('button', { name: '↓ 导出', exact: true }))
    assert.deepEqual(exported.items, expected.items)
    await page.getByRole('button', { name: '放大事件图', exact: true }).click()
    const html = await download(page.getByRole('button', { name: '↓ 导出报告', exact: true }), 'html')
    const report = await browser.newPage(); await report.setContent(html)
    assert.equal(await report.locator('.message-record').count(), 26)
    assert.equal(await report.locator('[data-testid="event-swimlane"] g.swimlane-event').count(), 13)
    assert.equal(await report.locator('.network-stage').count(), 0)
    await report.close()
    await page.screenshot({ path: new URL('../../docs/screenshots/task-nadia-1366.png', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'), fullPage: true })
  })
  await check('Event export records local controls and blocks stale-scope export while reloading', async () => {
    await page.route('**/api/events/timeline?**', async route => {
      await new Promise(resolve => setTimeout(resolve, 350))
      await route.continue()
    })
    const requested = page.waitForRequest(request => new URL(request.url()).pathname === '/api/events/timeline' &&
      new URL(request.url()).searchParams.get('event_type') === 'Assessment')
    await page.getByLabel('事件类型').selectOption('Assessment')
    await requested
    const button = page.locator('.event-panel').getByRole('button', { name: '↓ 导出', exact: true })
    assert.equal(await button.isDisabled(), true, 'New filters must not be attached to the previous event list')
    const exported = await download(button)
    assert.equal(exported.filters.event_type, 'Assessment')
    assert.equal(exported.filters.missing_only, false)
    assert.equal(exported.filters.include_outliers, false)
    assert.equal(exported.source_sha256, (await api('health')).source_sha256)
    assert(exported.items.length > 0 && exported.items.every(row => row.sub_type === 'Assessment'))
    assert.deepEqual(exported.items, (await api('events/timeline?entity_id=Nadia%20Conti&event_type=Assessment&page_size=100')).items)
    await page.getByTestId('start-date').fill('2050-01-01')
    await page.getByTestId('end-date').fill('2050-01-02')
    assert.equal(await button.isDisabled(), true)
    const empty = await download(button)
    assert.equal(empty.filters.start, '2050-01-01')
    assert.equal(empty.filters.end, '2050-01-02')
    assert.equal(empty.filters.event_type, 'Assessment')
    assert.deepEqual(empty.items, [])
  })
  assert.deepEqual(errors, [])
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
  await writeFile(new URL('../../docs/task-validation.json', import.meta.url), JSON.stringify({
    base_url: base, browser: 'Windows Microsoft Edge / Playwright',
    scope: 'Scripted official-question walkthrough; not a human usability study', results, errors,
  }, null, 2))
} finally { await browser.close() }
