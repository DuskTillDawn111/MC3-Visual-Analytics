import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const base=process.env.MC3_BASE_URL||'http://127.0.0.1:8000'
const browser=await chromium.launch({channel:'msedge',headless:true})
const page=await browser.newPage({viewport:{width:1920,height:1080}})
const sampleIds=()=>page.getByTestId('topic-sample').locator(':scope > .mono').allTextContents().then(rows=>rows.map(row=>row.split(' ')[0]))
const waitIds=ids=>page.waitForFunction(expected=>JSON.stringify([...document.querySelectorAll('[data-testid="topic-sample"] > .mono')].map(node=>node.textContent.split(' ')[0]))===JSON.stringify(expected),ids)
try{
  const api=await(await page.request.get(`${base}/api/topics?topic_count=6`)).json()
  const reviewed=JSON.parse(await readFile(new URL('../../docs/TOPIC_SAMPLE_REVIEW.json',import.meta.url),'utf8'))
  assert.equal(reviewed.model.version,api.model.version)
  await page.goto(base,{waitUntil:'networkidle'})
  await page.getByTestId('workspace-groups').click()
  await page.getByTestId('topic-matrix').waitFor()
  for(const topic of api.topics){
    await page.getByTestId('topic-matrix').locator('thead button').nth(topic.id).click()
    await page.getByLabel('原文抽样方式').selectOption('boundary')
    const ids=new Set(topic.message_ids)
    const gap=row=>{const sorted=[...row.weights].sort((a,b)=>b-a);return sorted[0]-sorted[1]}
    const expected=api.assignments.filter(row=>ids.has(row.message_id)).sort((a,b)=>gap(a)-gap(b)||a.message_id.localeCompare(b.message_id)).slice(0,3).map(row=>row.message_id)
    await waitIds(expected)
    await page.getByLabel('原文抽样方式').selectOption('random')
    await page.waitForFunction(()=>!document.querySelector('[data-testid="topic-matrix"]')?.closest('.topic-view')?.textContent.includes('正在读取所选群体的原文样本'))
    const first=await sampleIds()
    assert.deepEqual(first.slice(0,2),reviewed.samples.filter(row=>row.topic_id===topic.id&&row.mode==='fixed_seed').map(row=>row.message.id))
    assert(first.every(id=>ids.has(id)))
    await page.getByLabel('原文抽样方式').selectOption('boundary')
    await waitIds(expected)
    await page.getByLabel('原文抽样方式').selectOption('random')
    await waitIds(first)
  }
  console.log('PASS All six topics show mathematically closest boundary samples and reproducible reviewed samples within scope')
}finally{await browser.close()}
