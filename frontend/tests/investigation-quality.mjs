import { chromium } from 'playwright'
import assert from 'node:assert/strict'

const base = process.env.MC3_BASE_URL || 'http://127.0.0.1:8000'
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } })
const errors = []
page.on('pageerror', error => errors.push(error.message))
try {
  await page.goto(base, { waitUntil: 'networkidle' })
  await page.getByTestId('workspace-investigation').click()
  await page.getByTestId('alias-explanation').waitFor()
  assert((await page.getByTestId('candidate-summary').boundingBox())?.y < 500, 'Evidence summary must be visible before the long ranking')
  assert((await page.getByTestId('alias-candidate').count()) <= 4)
  await page.getByRole('button', { name: /展开全部.*候选/ }).click()
  assert((await page.getByTestId('alias-candidate').count()) > 4)
  await page.getByRole('button', { name: '收起候选', exact: true }).click()
  await page.locator('.feature-evidence summary').filter({ hasText: '文本主题' }).click()
  const term = page.getByTestId('text-feature-evidence').first()
  await term.waitFor()
  assert((await term.locator('[data-side="alias"] button').count()) > 0)
  assert((await term.locator('[data-side="candidate"] button').count()) > 0)
  assert((await term.locator('blockquote').count()) >= 2)
  console.log('PASS Candidate evidence precedes rankings and explains each side with source excerpts')

  await page.locator('.manual-analysis summary').click()
  await page.getByLabel('人工分析备注').fill('保留正在编辑的核查记录')
  await page.locator('.weights summary').click()
  const reloaded = page.waitForResponse(r => new URL(r.url()).pathname === '/api/aliases' && r.url().includes('temporal=0.6'))
  await page.getByLabel('时间模式权重').fill('0.6')
  await reloaded
  await page.getByTestId('alias-explanation').waitFor()
  assert.equal(await page.locator('.manual-analysis').getAttribute('open'), '', 'Reload must preserve the open manual note editor')
  assert.equal(await page.getByLabel('人工分析备注').inputValue(), '保留正在编辑的核查记录')
  await page.getByRole('button', { name: '保存本地标记', exact: true }).click()
  await page.getByText('已保存在本浏览器；这是人工分析标记。', { exact: true }).waitFor()
  console.log('PASS Weight reload preserves the open note editor and its unsaved text')
  const restored = page.waitForResponse(r => new URL(r.url()).pathname === '/api/aliases' && r.url().includes('temporal=0.2'))
  await page.getByLabel('时间模式权重').fill('0.2')
  await restored
  await page.getByTestId('alias-explanation').waitFor()

  await page.getByRole('button', { name: '检查权重与样本敏感性', exact: true }).click()
  await page.getByTestId('sensitivity-row').first().waitFor()
  const ablation = page.getByTestId('sensitivity-row').filter({ hasText: '移除文本主题' })
  assert.match(await ablation.innerText(), /Elise/)
  assert.match(await page.locator('.sensitivity-review').innerText(), /不等于身份正确/)
  await page.locator('.period-profiles summary').click()
  await page.getByLabel('第二时段开始日期').fill('2040-10-05')
  await page.getByRole('button', { name: '应用分界', exact: true }).click()
  await page.waitForFunction(() => document.querySelector('[data-testid="period-profile"]')?.textContent.includes('10-01 — 10-04'))
  assert.match(await page.getByTestId('period-profile').nth(1).innerText(), /10-05 — 10-14/)
  const pending = page.waitForEvent('download')
  await page.getByRole('button', { name: '↓ 导出比较与人工标记', exact: true }).click()
  const chunks = []
  for await (const chunk of await (await pending).createReadStream()) chunks.push(chunk)
  const report = JSON.parse(Buffer.concat(chunks).toString('utf8'))
  assert.equal(report.period_profiles.split_date, '2040-10-05')
  assert(report.diagnostics.scenarios.length >= 5)
  assert(report.candidate.feature_evidence.text.length > 0)
  console.log('PASS Weight/sample sensitivity and custom periods remain traceable in exports')
  assert.deepEqual(errors, [])
} finally { await browser.close() }
