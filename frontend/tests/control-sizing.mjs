import {chromium} from 'playwright'
import assert from 'node:assert/strict'

const browser=await chromium.launch({channel:'msedge',headless:true})
const page=await browser.newPage({viewport:{width:1440,height:1000}})
try {
  await page.goto(process.env.MC3_BASE_URL||'http://127.0.0.1:8000',{waitUntil:'networkidle'})
  await page.getByTestId('workspace-patterns').click()
  await page.getByTestId('view-temporal').click()
  const activeHours=page.getByRole('checkbox',{name:'聚焦活跃时段'})
  await activeHours.waitFor()
  const box=await activeHours.boundingBox()
  assert(box.height<=20,'Checkboxes must keep their native visual size instead of inheriting text-field height')
  const checked=await activeHours.isChecked()
  await page.locator('.day-heading label').click()
  assert.equal(await activeHours.isChecked(),!checked,'The visible label must toggle its checkbox')
  console.log('PASS Compact checkbox geometry and clickable label in the temporal toolbar')
} finally {await browser.close()}
