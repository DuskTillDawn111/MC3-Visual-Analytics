import { chromium } from 'playwright'
import assert from 'node:assert/strict'

const browser=await chromium.launch({channel:'msedge',headless:true})
const page=await browser.newPage()
const base=process.env.MC3_BASE_URL||'http://127.0.0.1:8000'
try {
  for(const [width,height] of [[1920,1080],[1366,768]]){
    await page.setViewportSize({width,height})
    await page.goto(base,{waitUntil:'networkidle'})
    await page.getByTestId('workspace-patterns').click()
    await page.getByTestId('graph-node').first().waitFor()
    const stage=page.locator('.network-stage')
    assert((await stage.boundingBox()).width>(await page.locator('.analysis-canvas').boundingBox()).width*.94)
    assert((await stage.boundingBox()).height>=400)
    assert.equal(await page.locator('.plot-grid > section').first().getAttribute('class'),'panel network')
    const switcher=page.getByRole('navigation',{name:'图表视图',exact:true})
    assert((await switcher.boundingBox()).y<height,'View navigation stays in the first viewport')
    await page.getByTestId('view-temporal').click()
    assert(await page.locator('.temporal').isVisible())
    assert.equal(await page.locator('.network').isVisible(),false)
    assert((await page.locator('.temporal').boundingBox()).y<height/2)
    assert((await page.getByTestId('heatmap').locator('svg').boundingBox()).width>500)
    await page.getByTestId('view-network').focus();await page.keyboard.press('Enter')
    assert(await page.locator('.network').isVisible())
    await page.getByTestId('view-overview').click()
    assert(await page.locator('.temporal').isVisible())
    await page.getByTestId('workspace-groups').click()
    await page.getByTestId('view-topics-panel').click()
    assert(await page.locator('.topics-panel').isVisible())
    assert.equal(await page.locator('.network').isVisible(),false)
    await page.getByTestId('workspace-investigation').click()
    for(const view of ['event-panel','alias-panel']){
      await page.getByTestId('view-'+view).click()
      assert(await page.locator('.'+view).isVisible())
      assert((await page.locator('.'+view).boundingBox()).y<height/2)
    }
    await page.getByTestId('workspace-patterns').click()
    assert.equal(await page.getByTestId('view-overview').getAttribute('aria-pressed'),'true')
    await page.getByTestId('entity-filter').selectOption('Reef Guardian')
    await page.waitForFunction(()=>document.querySelectorAll('[data-testid="graph-node"]').length===15)
    await page.waitForTimeout(200)
    const bounds=await page.locator('.network-stage svg > g').boundingBox()
    const frame=await stage.boundingBox()
    assert(Math.abs(bounds.x+bounds.width/2-frame.x-frame.width/2)<frame.width*.1,'Filtered neighborhood should be centered in the main canvas')
    assert(bounds.height>frame.height*.65,'Filtered neighborhood should use the available graph height')
    const node=page.getByTestId('graph-node').filter({has:page.locator('path')}).first()
    await node.focus();await page.keyboard.press('Enter')
    await page.getByTestId('detail-id').waitFor()
  }
  console.log('PASS Large network, persistent view navigation, workspace restoration and keyboard source access at both desktop sizes')
} finally { await browser.close() }
