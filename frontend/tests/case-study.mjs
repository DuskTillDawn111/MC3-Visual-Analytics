import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const base=process.env.MC3_BASE_URL||'http://127.0.0.1:8000'
const browser=await chromium.launch({channel:'msedge',headless:true})
const page=await browser.newPage({viewport:{width:1366,height:768}})
const errors=[];page.on('pageerror',error=>errors.push(error.message))
async function download(id){const pending=page.waitForEvent('download');await page.getByTestId(id).click();return readFile(await(await pending).path(),'utf8')}
try{
  await page.goto(base,{waitUntil:'networkidle'})
  await page.getByTestId('case-stage-0').waitFor()
  assert(await page.getByTestId('workspace-case').getAttribute('class')==='active')
  const data=await(await page.request.get(`${base}/api/findings`)).json()
  const finding=data.items.find(row=>row.id==='nadia')
  assert.equal(await page.locator('.case-mark').count(),8)
  for(const [index,stage] of finding.stages.entries()){
    await page.getByTestId(`case-stage-${index}`).click()
    for(const id of [...stage.support_ids,...stage.counter_ids]){
      await page.locator(`.case-mark[data-source="${id}"]`).focus();await page.keyboard.press('Enter')
      const original=finding.evidence.find(row=>row.id===id)
      assert.equal(await page.locator('.case-original p').innerText(),original.content)
      if (!await page.locator('.source-details').evaluate(el=>el.open)) {
        assert.equal(await page.locator('.source-provenance').isVisible(),false)
        await page.locator('.source-details summary').click()
      }
      assert.match(await page.locator('.source-provenance').innerText(),new RegExp(id))
      assert(original.content.includes((await page.locator('.source-reading blockquote').innerText()).slice(1,-1)))
    }
  }
  console.log('PASS Four investigation stages and all eight keyboard-accessible nodes expose exact original messages')
  await page.getByRole('button',{name:'竞争解释',exact:true}).click()
  assert.match(await page.locator('.reader-empty').innerText(),/继续寻找另一侧证据/)
  await page.getByTestId('case-stage-1').click()
  await page.locator('.source-details summary').click()
  assert.match(await page.locator('.source-provenance').innerText(),/Event_Communication_536/)
  await page.getByTestId('case-source-Event_Communication_575').click()
  assert.match(await page.locator('.source-provenance').innerText(),/关联主体的交叉引用/)
  const json=JSON.parse(await download('case-export-json'))
  assert.equal(json.reading_state.stage,1);assert.equal(json.reading_state.lens,'counter')
  assert.equal(json.reading_state.selected_id,'Event_Communication_575')
  assert.deepEqual(json.messages.map(m=>m.id).sort(),finding.state.message_ids.toSorted())
  assert.equal(json.source_sha256,data.source_sha256)
  const html=await download('case-export-html'),report=await browser.newPage()
  await report.setContent(html)
  assert.equal(await report.locator('.message-record').count(),8)
  assert.equal(await report.locator('.case-mark').count(),8)
  assert.match(await report.locator('.report-scope').innerText(),/7 条为 Nadia Conti/)
  const reasoning=await report.locator('.analysis-reasoning').innerText()
  for(const step of finding.reasoning_steps)assert(reasoning.includes(step.interpretation))
  await report.close()
  console.log('PASS Counterevidence, missing-evidence states and the complete offline dossier preserve scope and reading state')
  for(const card of data.items){
    await page.getByTestId(`case-question-${card.id}`).click()
    assert.equal(await page.locator('.case-questions ol li').count(),card.reasoning_steps.length)
  }
  await page.getByTestId('case-question-rhythm').click()
  const nadia=page.locator('.rhythm-comparison tr').filter({hasText:'Nadia Conti'})
  assert.match(await nadia.innerText(),/6 条\s+20 条/)
  for(const width of [1366,1920]){await page.setViewportSize({width,height:width===1366?768:1080});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false)}
  await page.getByTestId('case-explore').click()
  await page.waitForFunction(()=>document.querySelector('[data-testid="workspace-patterns"]')?.classList.contains('active'))
  await page.waitForFunction(()=>document.querySelector('[data-testid="message-total"]')?.textContent==='2')
  await page.getByTestId('workspace-case').click();await page.getByTestId('case-stage-0').waitFor()
  assert.match(await page.locator('.source-provenance').innerText(),/Event_Communication_575/,'Returning from analysis must preserve the selected stage and source')
  await page.getByTestId('case-inspect').click()
  await page.waitForFunction(()=>document.querySelector('[data-testid="detail-id"]')?.textContent==='Event_Communication_575')
  console.log('PASS All four answers expose their reasoning and restore the matching analysis tools and source inspector')
  await page.route('**/api/findings',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{message:'调查材料暂时不可用'}})}))
  await page.reload({waitUntil:'networkidle'})
  await page.getByTestId('case-study').getByRole('alert').waitFor()
  assert.equal(await page.getByTestId('case-export-html').count(),0)
  await page.unroute('**/api/findings')
  await page.getByRole('button',{name:'重新读取调查材料',exact:true}).click()
  await page.getByTestId('case-stage-0').waitFor()
  assert.equal(await page.locator('.case-mark').count(),8)
  console.log('PASS A failed case load shows a retry state and recovers the original evidence without a stale export')
  assert.deepEqual(errors,[])
}finally{await browser.close()}
