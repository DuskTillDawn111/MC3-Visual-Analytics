import { chromium } from 'playwright'
import assert from 'node:assert/strict'

const base=process.env.MC3_BASE_URL||'http://127.0.0.1:8000'
const browser=await chromium.launch({channel:'msedge',headless:true})
const page=await browser.newPage({viewport:{width:1366,height:768}})
const failures=[],errors=[]
page.on('pageerror',error=>errors.push(error.message))
async function ready(){await page.waitForFunction(()=>Array.from(document.querySelectorAll('button')).some(b=>b.textContent==='↓ 导出报告'&&!b.disabled))}
async function check(name,fn){try{await fn();console.log(`PASS ${name}`)}catch(error){failures.push(name);console.error(`FAIL ${name}: ${error.message}`)}}
try{
  await page.goto(base,{waitUntil:'networkidle'})
  await page.getByTestId('workspace-patterns').click()
  await page.getByTestId('peak-cell').first().click()
  await ready()
  await check('Hourly selection explains the full-day context beside its actual counts',async()=>{
    const daily=await(await page.request.get(`${base}/api/messages?start=2040-10-05&end=2040-10-05&page_size=100`)).json()
    const hourly=daily.items.filter(m=>m.hour===10)
    assert.equal(daily.total,45);assert.equal(hourly.length,24)
    assert.equal(await page.locator('.day-caption').isVisible(),false)
    await page.locator('.day-reading summary').click()
    const caption=await page.locator('.day-caption').innerText()
    assert.match(caption,/2040-10-05 全天背景/)
    assert(caption.includes(`${daily.total} 条消息`))
    assert.match(caption,/10 时高亮 24 条/)
    assert.equal(await page.getByTestId('daily-message').count(),45)
    assert.equal(await page.getByTestId('daily-message').evaluateAll(nodes=>nodes.filter(n=>n.getAttribute('opacity')==='1').length),24)
    await page.getByRole('button',{name:'清除小时筛选',exact:true}).click();await ready()
    assert.doesNotMatch(await page.locator('.day-caption').innerText(),/高亮 24 条/)
    assert.equal(await page.getByTestId('daily-message').evaluateAll(nodes=>nodes.filter(n=>n.getAttribute('opacity')==='1').length),45)
  })
  await page.getByTestId('reset').click();await ready()
  await page.getByTestId('workspace-investigation').click();await ready()
  await check('Candidate score calculation opens on demand and the numeric ranking is preserved',async()=>{
    assert.match(await page.locator('.ranking-head').innerText(),/相似分/)
    assert.equal(await page.locator('.weights p').isVisible(),false)
    await page.locator('.weights summary').click()
    assert.match(await page.locator('.weights p').innerText(),/原分 × 100/)
    const table=page.locator('.feature-table')
    assert.match(await table.locator('thead').innerText(),/特征值.*加权贡献/s)
    const api=await(await page.request.get(`${base}/api/aliases?alias=Boss`)).json()
    assert.equal(await page.getByTestId('alias-candidate').first().locator('b').innerText(),(api.items[0].score*100).toFixed(1))
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false)
  })
  await page.getByRole('button',{name:'分析发现',exact:true}).click()
  await page.getByTestId('finding-nadia').click()
  await page.getByTestId('restore-finding').click();await ready()
  await check('Restored findings and exports distinguish chart filters from cross-entity citations',async()=>{
    assert.match(await page.locator('.active-finding').innerText(),/已恢复分析：.*全期分析/)
    async function download(label){const pending=page.waitForEvent('download');await page.getByRole('button',{name:label,exact:true}).click();const chunks=[];for await(const chunk of await(await pending).createReadStream())chunks.push(chunk);return Buffer.concat(chunks).toString('utf8')}
    const json=JSON.parse(await download('导出证据'))
    assert.equal(json.chart_filters.entity_id,'Nadia Conti')
    assert.equal(json.filters.entity_id,undefined)
    assert.equal(json.messages.length,8)
    const others=json.messages.filter(m=>m.sender!=='Nadia Conti'&&m.receiver!=='Nadia Conti')
    assert(others.some(m=>m.id==='Event_Communication_575'))
    const html=await download('↓ 导出报告')
    const report=await browser.newPage()
    try{
      await report.setContent(html)
      const scope=await report.locator('.report-scope').innerText()
      assert.match(scope,/图表范围：Nadia Conti/)
      assert.match(scope,/26 条通信/)
      assert.match(scope,/8 条选中原文/)
      assert(scope.includes(`${others.length} 条其他主体通信`))
      assert.match(scope,/Event_Communication_575/)
      assert(await report.locator('.report-scope').evaluate(el=>Boolean(el.compareDocumentPosition(document.querySelector('.analysis-finding'))&Node.DOCUMENT_POSITION_FOLLOWING)))
      const record=report.locator('.message-record').filter({has:report.getByRole('heading',{name:'Event_Communication_575',exact:true})})
      assert.match(await record.innerText(),/跨主体引用/)
      assert.equal(await report.locator('.message-record').count(),8)
    }finally{await report.close()}
  })
  assert.deepEqual(errors,[])
  assert.deepEqual(failures,[])
}finally{await browser.close()}
