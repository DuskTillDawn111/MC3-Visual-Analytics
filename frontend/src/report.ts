import type { Evidence, Message, Overview, Params } from './api'

export interface ReportView { title:string; svg:string; caption?:string }
export interface Finding { id:string;title:string;level:string;claim:string;competing_explanation:string;limitation:string;statistics:Record<string,unknown>;evidence:Message[];source_notes?:{id:string;label:string;excerpt:string;reading:string}[];reasoning_steps?:{observation:string;interpretation:string;message_ids:string[]}[];stages:{date:string;claim:string;support_ids:string[];counter_ids:string[];gap:string}[];state:{workspace:string;filters:{start:string;end:string;hour:number|null;q:string;entity:string};message_ids:string[];alias:string|null} }
export interface FindingContext { finding:Finding;source_sha256:string;analysis_version:string;scope:string }
export interface AnalysisReport {
  overview:Overview; filters:Params; chartFilters:Params; messages:Message[]; evidence:Evidence|null;
  views:ReportView[]; graphDefinition:string; graphControls:Params;
  analysis?:FindingContext;
}

const escapeHtml=(value:unknown)=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]!))

export function captureReportViews():ReportView[] {
  return [ ['通信日期 × 小时热力图','.heat-chart svg'], ['每日通信量','.trend-chart svg'], ['单日通信细节','.daily-detail'], ['当前关系图 / 有向邻接矩阵','.network-stage svg'], ['主题随时间变化','.topic-timeline'], ['当前范围事件日期分布','[data-testid="event-day-overview"]'], ['当前范围完整主体—事件泳道','[data-testid="event-swimlane"]'] ]
    .flatMap(([title,selector])=>{
      const source=document.querySelector<SVGSVGElement>(selector!)
      if(!source||!source.getBoundingClientRect().width||!source.getBoundingClientRect().height)return []
      const clone=source.cloneNode(true) as SVGSVGElement
      // ECharts roots use absolute positioning in the live renderer; offline figures use normal flow.
      clone.removeAttribute('style')
      clone.setAttribute('xmlns','http://www.w3.org/2000/svg')
      clone.setAttribute('viewBox',source.getAttribute('viewBox')||`0 0 ${source.clientWidth} ${source.clientHeight}`)
      clone.setAttribute('width','100%');clone.setAttribute('height',String(source.clientHeight))
      return [{title:title!,svg:new XMLSerializer().serializeToString(clone),caption:selector==='.daily-detail'?document.querySelector('.day-caption')?.textContent||'':selector==='.network-stage svg'?'通信图颜色为社区、大小为唯一消息数（自环计一次），环形边表示自环、箭头为发送方向。原图实线为直接记录、虚线为文本推断。':undefined}]
    })
}

export function createAnalysisReport(report:AnalysisReport):string {
  const {overview,messages,evidence}=report
  const raw=(value:unknown)=>escapeHtml(JSON.stringify(value,null,2))
  const finding=report.analysis?.finding
  const entity=String(report.chartFilters.entity_id||'')
  const otherMessages=entity?messages.filter(m=>m.sender!==entity&&m.receiver!==entity):[]
  const citationScope=entity?`其中 ${messages.length-otherMessages.length} 条为 ${escapeHtml(entity)} 直接参与的通信，${otherMessages.length} 条其他主体通信。${otherMessages.length?`跨主体引用：${otherMessages.map(m=>escapeHtml(m.id)).join('、')}；用于核对关联线索与竞争解释。`:''}`:'引用原文覆盖当前选中的通信主体。'
  const scope=`<section class="report-scope"><h2>筛选与记录范围</h2><p>图表范围：${escapeHtml(entity||'全部主体')} · ${escapeHtml(report.chartFilters.start)} — ${escapeHtml(report.chartFilters.end)}${report.chartFilters.hour!==null&&report.chartFilters.hour!==undefined?` · ${escapeHtml(report.chartFilters.hour)} 时`:''}${report.chartFilters.q?` · 检索：${escapeHtml(report.chartFilters.q)}`:''}。当前工作台包含 <b>${overview.communications}</b> 条通信、<b>${overview.entities}</b> 个通信主体；图中标明的全天背景保留整日上下文。</p><p>引用附录：<b>${messages.length} 条选中原文</b>。${citationScope} 图表统计按主体与时间条件计算，附录按选中消息 ID 汇集。${finding?'分析结论基于完整 14 天语料，引用用于逐条核查论证。':''}</p><h3>图表条件</h3><pre>${raw(report.chartFilters)}</pre><h3>附录条件与消息 ID</h3><pre>${raw(report.filters)}</pre><p class="meta">原始 ZIP SHA-256：${escapeHtml(overview.quality.source_sha256)}<br>来源：data/raw/MC3_release.zip → MC3_release/MC3_graph.json。所有消息 ID、原始时间和英文内容均保留。</p></section>`
  const analysis=finding?`<section class="analysis-finding"><h2>${escapeHtml(finding.title)}</h2><p>${escapeHtml(finding.claim)}</p><h3>关联记录</h3><p>${escapeHtml(finding.competing_explanation)}</p><h3>分析口径</h3><p>${escapeHtml(finding.limitation)}</p>${finding.stages.map(stage=>`<article><h3>${escapeHtml(stage.date)} · ${escapeHtml(stage.claim)}</h3><p>支持：${escapeHtml(stage.support_ids.join('、'))}${stage.counter_ids.length?`<br>相关引用：${escapeHtml(stage.counter_ids.join('、'))}`:''}<br>${escapeHtml(stage.gap)}</p></article>`).join('')}<div class="analysis-reasoning"><h3>发现与依据</h3><ol>${(finding.reasoning_steps||[]).map(step=>`<li><strong>${escapeHtml(step.observation)}</strong><p>${escapeHtml(step.interpretation)}</p><p class="meta">${escapeHtml(step.message_ids.join('、'))}</p></li>`).join('')}</ol></div><details><summary>来源与恢复参数</summary><pre>${raw(report.analysis)}</pre></details></section>`:''
  const sources=evidence?`<section><h2>所选节点的完整原始证据</h2><p>${escapeHtml(evidence.node.id)} · ${escapeHtml(evidence.status)}。完整节点及关联原文如下。</p><pre>${raw(evidence)}</pre></section>`:''
  const records=messages.map(m=>`<article class="message-record"><h3>${escapeHtml(m.id)}</h3><p class="meta">${escapeHtml(m.timestamp)} · ${escapeHtml(m.sender)} → ${escapeHtml(m.receiver)}${entity?` · ${m.sender===entity||m.receiver===entity?'主体直接通信':'跨主体引用'}`:''}</p><p>${escapeHtml(m.content)}</p><p class="meta">evidence_for：${m.evidence_ids.length?m.evidence_ids.map(escapeHtml).join('、'):'无证据连接，原始通信保留'}</p></article>`).join('')
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>暗潮寻踪 · 可追溯分析报告</title><style>
    *{box-sizing:border-box}body{max-width:1200px;margin:0 auto;padding:30px 24px;color:#243541;background:#eaf0f4;font:14px/1.8 "Segoe UI","Microsoft YaHei",sans-serif}h1{font-size:27px}h2{font-size:19px}h3{font-size:13px;margin:0;color:#286a86}section{background:#f8fafb;border:1px solid #cedae1;border-radius:6px;padding:20px;margin:18px 0}.meta{color:#5c6c76;font-size:12px}.figure{background:#f8fafb;padding:12px;border:1px solid #cedae1;border-radius:5px;margin:16px 0;color:#243541;overflow:hidden}.figure h3{color:#286a86;margin-bottom:9px}.figure svg{display:block;width:100%;max-width:100%}.message-record{padding:13px 0;border-bottom:1px solid #cedae1;break-inside:avoid}.message-record p{white-space:pre-wrap;overflow-wrap:anywhere;margin:7px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11px/1.7 Consolas,monospace}b{font-weight:600}@page{size:A4;margin:15mm}@media print{body{max-width:none;padding:0;background:white}.figure{-webkit-print-color-adjust:exact;print-color-adjust:exact;break-inside:avoid}section{border:0;padding:0}h1,h2,h3{break-after:avoid}}
  </style></head><body><h1>暗潮寻踪 · 可追溯分析报告</h1><p class="meta">导出时间 ${escapeHtml(new Date().toISOString())}</p>
  ${scope}${analysis}
  <section><h2>导出开始时的可视图表</h2><p class="meta">${escapeHtml(report.graphDefinition)}</p><pre>${raw(report.graphControls)}</pre>${report.views.map(v=>`<div class="figure"><h3>${escapeHtml(v.title)}</h3>${v.caption?`<p>${escapeHtml(v.caption)}</p>`:''}${v.svg}</div>`).join('')}<p class="meta">此 HTML 自包含 SVG，可离线打开、保存图表或通过浏览器打印为 PDF。</p></section>
  <section><h2>数据质量与排除记录</h2><p>${overview.quality.missing_timestamp_count} 个事件缺少 timestamp；${overview.quality.timestamp_outliers.length} 个异常年份；${overview.quality.communications_without_evidence.length} 条通信无 evidence_for。缺失记录保留可查，异常年份没有改写。</p><pre>${raw({timestamp_outliers:overview.quality.timestamp_outliers,outside_observation_events:overview.quality.outside_observation_events})}</pre></section>${sources}<section><h2>原始通信附录</h2>${records||'<p>当前筛选没有通信。</p>'}</section></body></html>`
}

export function downloadAnalysisReport(report:AnalysisReport){
  const url=URL.createObjectURL(new Blob([createAnalysisReport(report)],{type:'text/html;charset=utf-8'}))
  const link=document.createElement('a');link.href=url;link.download='mc3-analysis-report.html';link.click()
  window.setTimeout(()=>URL.revokeObjectURL(url),1000)
}
