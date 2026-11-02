import { chromium } from 'playwright'
import assert from 'node:assert/strict'

const base = process.env.MC3_BASE_URL || 'http://127.0.0.1:8000'
const browser = await chromium.launch({ channel:'msedge', headless:true })
const page = await browser.newPage({ viewport:{width:1366,height:768} })
const errors=[]
page.on('pageerror',error=>errors.push(error.message))
try {
  await page.goto(base,{waitUntil:'networkidle'})
  await page.getByTestId('workspace-patterns').click()
  const result=await (await page.request.get(`${base}/api/findings`)).json()
  for(const card of result.items){
    await page.getByRole('button',{name:'分析发现',exact:true}).click()
    await page.getByTestId(`finding-${card.id}`).click()
    const text=await page.getByTestId('findings-panel').innerText()
    assert.match(text,/关联记录/)
    assert(text.includes(card.claim))
    assert.doesNotMatch(text,/不能证明|不能视作|不能把首名|不证明这些|未证实|免责证明/)
    await page.getByTestId('restore-finding').click()
    await page.waitForFunction(workspace=>document.querySelector(`[data-testid="workspace-${workspace}"]`)?.classList.contains('active'),card.state.workspace)
    await page.waitForFunction(total=>document.querySelector('[data-testid="message-total"]')?.textContent===String(total),card.evidence.length)
    const pending=page.waitForEvent('download')
    await page.getByRole('button',{name:'导出证据',exact:true}).click()
    const chunks=[]
    for await(const chunk of await (await pending).createReadStream())chunks.push(chunk)
    const exported=JSON.parse(Buffer.concat(chunks).toString('utf8'))
    assert.equal(exported.analysis.finding.id,card.id)
    assert.equal(exported.analysis.source_sha256,result.source_sha256)
    assert.deepEqual(exported.messages.map(m=>m.id).sort(),card.state.message_ids.toSorted())
    assert.equal(exported.analysis.finding.limitation,card.limitation)
  }
  const pending=page.waitForEvent('download')
  await page.getByRole('button',{name:'↓ 导出报告',exact:true}).click()
  const chunks=[]
  for await(const chunk of await (await pending).createReadStream())chunks.push(chunk)
  const report=await browser.newPage()
  await report.setContent(Buffer.concat(chunks).toString('utf8'))
  const finding=await report.locator('.analysis-finding').innerText()
  assert(finding.includes(result.items.find(card=>card.id==='nadia').claim))
  assert.doesNotMatch(finding,/不能证明|不能视作|不证明这些|未证实|免责证明/)
  assert.equal(await report.locator('.notice').count(),0)
  assert.match(finding,/Event_Communication_847/)
  assert.match(finding,/关联记录/)
  assert.equal(await report.locator('.message-record').count(),8)
  await report.close()
  assert.deepEqual(errors,[])
  console.log('PASS All four findings restore their scope, retain original messages and export the same evidence-grounded narrative')
} finally {await browser.close()}
