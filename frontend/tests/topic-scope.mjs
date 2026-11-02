import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const base = process.env.MC3_BASE_URL || 'http://127.0.0.1:8000'
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
const errors = []
page.on('pageerror', error => errors.push(error.message))
const api = async path => (await page.request.get(`${base}/api/${path}`)).json()
const sorted = values => [...values].sort()
const samples = () => page.getByTestId('topic-sample').locator('.mono').allTextContents()
const sampleIds = async () => (await samples()).map(text => text.split(' ')[0])
const waitCount = value => page.waitForFunction(expected =>
  document.querySelector('[data-testid="message-total"]')?.textContent === String(expected), value)
const cell = (group, topic) => page.getByRole('button', {
  name: `社区 ${group.id + 1} 主题 ${topic.id + 1}，${group.counts[topic.id]} 条通信`, exact: true,
})
async function download(button) {
  const pending = page.waitForEvent('download')
  await button.click()
  return JSON.parse(await readFile(await (await pending).path(), 'utf8'))
}

try {
  const data = await api('topics')
  const fixture = data.groups.flatMap(group => data.topics.map(topic => ({ group, topic })))
    .find(({ group, topic }) => group.counts[topic.id] > 0 &&
      topic.representatives.every(message => !group.message_ids[topic.id].includes(message.id)))
  assert(fixture, 'The official corpus must expose a group whose global representatives are outside its cell')
  const { group, topic } = fixture
  const ids = group.message_ids[topic.id]
  const expectedSamples = data.assignments.filter(row => ids.includes(row.message_id))
    .sort((a, b) => b.weights[topic.id] - a.weights[topic.id] || a.message_id.localeCompare(b.message_id))
    .slice(0, 3).map(row => row.message_id)

  await page.goto(base, { waitUntil: 'networkidle' })
  await page.getByTestId('workspace-groups').click()
  await page.getByTestId('topic-matrix').waitFor()
  await cell(group, topic).click()
  await waitCount(ids.length)
  assert.match(await page.locator('.topic-name').innerText(), new RegExp(`\\b${ids.length} 条$`),
    'The topic explanation must use the selected group count, not the global topic count')
  await page.waitForFunction(expected => {
    const actual = [...document.querySelectorAll('[data-testid="topic-sample"] .mono')]
      .map(node => node.textContent.split(' ')[0])
    return JSON.stringify(actual) === JSON.stringify(expected)
  }, expectedSamples)
  assert.deepEqual(await sampleIds(), expectedSamples)
  assert.match(await page.getByTestId('topic-selection-scope').innerText(), new RegExp(`社区 ${group.id + 1}`))
  console.log('PASS Selected group count and ranked samples belong to the same official message set')

  const evidence = await download(page.getByRole('button', { name: '导出证据', exact: true }))
  assert.deepEqual(sorted(evidence.messages.map(message => message.id)), sorted(ids))
  const model = await download(page.getByRole('button', { name: '导出模型与来源', exact: true }))
  assert.equal(model.selected_scope.group_id, group.id)
  assert.equal(model.selected_scope.topic_id, topic.id)
  assert.deepEqual(sorted(model.selected_scope.message_ids), sorted(ids))
  assert.deepEqual(model.selected_scope.sample_ids, expectedSamples)
  console.log('PASS Evidence and topic exports preserve the selected group scope')

  await page.getByTestId('topic-matrix').locator('thead button').nth(topic.id).click()
  await waitCount(topic.count)
  assert.match(await page.locator('.topic-name').innerText(), new RegExp(`\\b${topic.count} 条$`))
  assert.doesNotMatch(await page.getByTestId('topic-selection-scope').innerText(), /社区/)
  assert.deepEqual(await sampleIds(), topic.representatives.map(message => message.id))
  console.log('PASS Selecting a topic header returns to all groups in the current filter')

  const otherGroup = data.groups.find(row => row.id !== group.id && row.counts[topic.id] > 0)
  assert(otherGroup)
  const otherIds = otherGroup.message_ids[topic.id]
  const otherSamples = data.assignments.filter(row => otherIds.includes(row.message_id))
    .sort((a, b) => b.weights[topic.id] - a.weights[topic.id] || a.message_id.localeCompare(b.message_id))
    .slice(0, 3).map(row => row.message_id)
  const delayed = page.waitForResponse(response => {
    const url = new URL(response.url())
    return url.pathname === '/api/messages' && url.searchParams.get('ids') === expectedSamples.join(',')
  })
  await page.route('**/api/messages?**', async route => {
    const url = new URL(route.request().url())
    if (url.searchParams.get('ids') === expectedSamples.join(',') && url.searchParams.get('page_size') === '3')
      await new Promise(resolve => setTimeout(resolve, 250))
    await route.continue()
  })
  await cell(group, topic).click()
  await cell(otherGroup, topic).click()
  await (await delayed).finished()
  await page.waitForFunction(expected => JSON.stringify([...document.querySelectorAll('[data-testid="topic-sample"] .mono')]
    .map(node => node.textContent.split(' ')[0])) === JSON.stringify(expected), otherSamples)
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
  assert.deepEqual(await sampleIds(), otherSamples)
  await waitCount(otherIds.length)
  await page.unroute('**/api/messages?**')
  console.log('PASS A delayed previous group request cannot overwrite a newer group selection')

  await cell(group, topic).click()
  await waitCount(ids.length)
  await page.getByLabel('主题数量').selectOption('4')
  await page.waitForFunction(() => document.querySelectorAll('.topic-table thead th').length === 5)
  await waitCount(584)
  assert.doesNotMatch(await page.getByTestId('topic-selection-scope').innerText(), /社区/)
  console.log('PASS Changing the topic model clears the previous model selection')

  await page.getByLabel('主题数量').selectOption('6')
  await page.waitForFunction(() => document.querySelectorAll('.topic-table thead th').length === 7)
  await cell(group, topic).click()
  await waitCount(ids.length)
  const filtered = await api('topics?start=2040-10-14&end=2040-10-14')
  await page.getByTestId('start-date').fill('2040-10-14')
  await page.waitForFunction(expected => document.querySelector('[data-testid="communication-count"]')?.textContent === String(expected), filtered.total)
  await waitCount(filtered.total)
  await page.waitForFunction(() => !document.querySelector('[data-testid="topic-selection-scope"]')?.textContent.includes('社区'))
  await page.waitForFunction(expected => JSON.stringify([...document.querySelectorAll('[data-testid="topic-sample"] .mono')]
    .map(node => node.textContent.split(' ')[0])) === JSON.stringify(expected), filtered.topics[topic.id].representatives.map(message => message.id))
  assert.deepEqual(await sampleIds(), filtered.topics[topic.id].representatives.map(message => message.id))
  console.log('PASS Date filtering clears obsolete group membership and reloads scoped samples')

  await page.getByTestId('search').fill('no-such-official-message-9a46')
  await page.getByRole('button', { name: '检索', exact: true }).click()
  await waitCount(0)
  await page.waitForFunction(() => document.querySelectorAll('[data-testid="topic-sample"]').length === 0)
  assert.match(await page.locator('.topic-name').innerText(), /\b0 条$/)
  console.log('PASS Empty scopes do not retain old representatives')
  assert.deepEqual(errors, [])
} finally {
  await browser.close()
}
