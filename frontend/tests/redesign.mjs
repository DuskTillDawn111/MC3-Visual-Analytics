import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile,writeFile } from 'node:fs/promises'

const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
const errors=[];page.on('pageerror',e=>errors.push(e.message))
const results=[]
const base=process.env.MC3_BASE_URL||'http://127.0.0.1:8000'
async function check(name,run){await run();results.push(name);console.log('PASS '+name)}
async function count(value){await page.waitForFunction(v=>document.querySelector('[data-testid="communication-count"]')?.textContent===String(v),value)}
async function reset(){await page.getByTestId('reset').click();await count(584)}
const api=async path=>(await page.request.get(base+'/api/'+path)).json()
try {
  await page.goto(base, { waitUntil: 'networkidle' })
  await page.getByTestId('workspace-patterns').click()
  await page.getByTestId('communication-count').filter({ hasText: '584' }).waitFor()
  const first = page.locator('.message-list').getByRole('button', { name: 'Event_Communication_1', exact: true })
  await first.click()
  await page.locator('.detail-pane:visible').waitFor()
  await page.getByRole('button', { name: '通信列表', exact: true }).click()
  await first.click()
  await page.locator('.detail-pane:visible').waitFor({ timeout: 2000 })
  assert.equal(await page.getByTestId('detail-id').textContent(), 'Event_Communication_1')
  console.log('PASS Reopening the same evidence returns to its visible detail')
  results.push('Reopening the same evidence returns to its visible detail')
  await check('Single-day communication opens exact source text beside the chart',async()=>{
    const glyph=page.getByTestId('daily-message').first(),id=await glyph.getAttribute('data-id')
    const original=await api('evidence/'+id)
    await glyph.focus();await page.keyboard.press('Enter')
    await page.getByTestId('detail-id').filter({hasText:id}).waitFor()
    assert.equal(await page.locator('.detail-pane .support-message p').innerText(),original.messages[0].content)
    assert.equal(await page.getByTestId('communication-count').innerText(),'584')
  })
  await check('Hour selection keeps fourteen-day context and undo restores scope',async()=>{
    const peak=page.getByTestId('peak-cell').first(),expected=Number(await peak.getAttribute('data-count'))
    await peak.click();await count(expected)
    const labels=await page.locator('.heat-chart text').allTextContents()
    assert.equal(labels.filter(t=>/^10\/\d{2}$/.test(t)).length,14)
    await page.getByTestId('undo-filters').click();await count(584)
  })
  await check('Anomaly explanation includes all fourteen same-hour observations',async()=>{
    await page.getByTestId('anomaly-marker').first().click()
    await page.getByTestId('anomaly-baseline').waitFor()
    assert.equal(await page.getByTestId('anomaly-baseline').locator('rect').count(),14)
    const values=await page.getByTestId('anomaly-baseline').locator('text').allTextContents()
    assert(values.includes('10-01')&&values.includes('10-14'))
  })
  await reset()
  await page.getByTestId('workspace-groups').click()
  await check('Directed matrix retains every source communication weight',async()=>{
    await page.getByTestId('matrix-mode').click()
    const graph=await api('graph')
    await page.waitForFunction(n=>document.querySelectorAll('[data-testid="matrix-cell"]').length===n,graph.edges.length)
    const weights=await page.getByTestId('matrix-cell').locator('text').allTextContents()
    assert.equal(weights.reduce((sum,w)=>sum+Number(w),0),584)
    const first=page.getByTestId('matrix-cell').first(),edge=graph.edges[0]
    await first.focus();await page.keyboard.press('Enter')
    await page.waitForFunction(n=>document.querySelector('[data-testid="message-total"]')?.textContent===String(n),edge.weight)
  })
  await check('Topic group cells and representative messages use original evidence',async()=>{
    await page.getByTestId('topic-matrix').waitFor()
    const cell=page.locator('[data-testid="topic-cell"]:enabled').first(),expected=Number(await cell.getAttribute('data-count'))
    await cell.click()
    await page.waitForFunction(n=>document.querySelector('[data-testid="message-total"]')?.textContent===String(n),expected)
    const sample=page.getByTestId('topic-sample').first();await sample.click()
    const id=(await sample.locator('.mono').innerText()).split(' ')[0]
    await page.getByTestId('detail-id').filter({hasText:id}).waitFor()
    const original=await api('evidence/'+id)
    assert.equal(await page.locator('.detail-pane .support-message p').innerText(),original.messages[0].content)
    await page.getByLabel('主题数量').selectOption('4')
    await page.waitForFunction(()=>document.querySelectorAll('.topic-table thead th').length===5)
  })
  await reset()
  await check('Export from a task switch never produces zero-size hidden figures',async()=>{
    const pending=page.waitForEvent('download');await page.getByRole('button',{name:'↓ 导出报告',exact:true}).click()
    const download=await pending,html=await readFile(await download.path(),'utf8'),report=await browser.newPage()
    try{await report.setContent(html);const sizes=await report.locator('.figure svg').evaluateAll(nodes=>nodes.map(n=>({width:n.viewBox.baseVal.width,height:n.viewBox.baseVal.height})));assert(sizes.length>0);assert(sizes.every(s=>s.width>0&&s.height>0),JSON.stringify(sizes));assert.equal(await report.locator('.message-record').count(),584)}finally{await report.close()}
  })
  await page.getByTestId('workspace-investigation').click()
  await check('Candidate feature comparison and Nadia event swimlanes remain auditable',async()=>{
    await page.getByTestId('alias-candidate').first().waitFor()
    assert.equal(await page.getByTestId('alias-candidate').first().locator('.feature-cells i').count(),4)
    await page.getByRole('button',{name:'调查 Nadia Conti ↗',exact:true}).click()
    await page.getByTestId('event-swimlane').waitFor()
    const expected=await api('overview?entity_id=Nadia%20Conti');await count(expected.communications)
    const event=page.getByTestId('event-swimlane').locator('g.swimlane-event').first(),id=await event.getAttribute('aria-label')
    await event.focus();await page.keyboard.press('Enter');await page.getByTestId('detail-id').filter({hasText:id}).waitFor()
  })
  await reset()
  await check('Desktop layouts keep evidence in the viewport and have no page overflow',async()=>{
    for(const width of [1920,1366]){await page.setViewportSize({width,height:width===1920?1080:768});await page.getByTestId('workspace-patterns').click();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);const reader=await page.locator('.evidence-panel').boundingBox();assert(reader&&reader.x>=0&&reader.y+reader.height<=page.viewportSize().height);await page.screenshot({path:`../docs/screenshots/redesign-overview-${width}.png`})}
  })
  assert.deepEqual(errors,[])
  await writeFile('../docs/redesign-browser-results.json',JSON.stringify({base_url:base,results,errors},null,2))
} finally {
  await browser.close()
}
