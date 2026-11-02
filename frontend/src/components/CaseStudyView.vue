<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { get } from '../api'
import type { Message, Overview, Page } from '../api'
import type { Finding, FindingContext } from '../report'
import { downloadAnalysisReport } from '../report'
import { exportJson } from '../store'
import { chartColors } from '../theme'

interface Collection { items:Finding[];source_sha256:string;analysis_version:string;scope:string }
const emit=defineEmits<{explore:[context:FindingContext];inspect:[context:FindingContext,id:string]}>()
const collection=ref<Collection>(),overview=ref<Overview>(),communications=ref<Message[]>([])
const busy=ref(true),error=ref(''),readerOpen=ref(false)
const stageIndex=ref(0),selectedId=ref('Event_Communication_331'),lens=ref('all'),question=ref('nadia')
const timeline=ref<SVGSVGElement>(),graph=ref<SVGSVGElement>(),graphHost=ref<HTMLElement>(),closeReaderButton=ref<HTMLButtonElement>()
const dimensions=ref({width:1000,height:490})
let resize:ResizeObserver|undefined,lastSource:HTMLElement|SVGElement|undefined
const finding=computed(()=>collection.value?.items.find(row=>row.id==='nadia'))
const stage=computed(()=>finding.value?.stages[stageIndex.value])
const selected=computed(()=>finding.value?.evidence.find(m=>m.id===selectedId.value))
const note=computed(()=>finding.value?.source_notes?.find(n=>n.id===selectedId.value))
const activeQuestion=computed(()=>collection.value?.items.find(row=>row.id===question.value))
const changes=computed(()=>(collection.value?.items.find(row=>row.id==='rhythm')?.statistics.entity_changes||[]) as {entity:string;first_count:number;second_count:number;first_median:string;second_median:string}[])
const stageNames=['取消通道','报酬与巡逻','加速与转移','请求批准']
const questions=[{id:'rhythm',number:'01',title:'节奏与影响'},{id:'groups',number:'02',title:'群体与内容'},{id:'identity',number:'03',title:'身份与假设'},{id:'nadia',number:'04',title:'行动与证据'}]
const actionNames:Record<string,string>={'331':'销毁文件','334':'时间冲突解释','529':'加倍报酬','535':'巡逻调整自述','536':'工程范围异议','575':'合法运输自述','847':'加速与转移','943':'请求最终批准'}
const shortId=(id:string)=>id.replace('Event_Communication_','#')
const actionLabel=(id:string)=>actionNames[id.replace('Event_Communication_','')]||shortId(id)
const sourceLabel=(id:string)=>finding.value?.source_notes?.find(n=>n.id===id)?.label||id
const message=(id:string)=>finding.value?.evidence.find(m=>m.id===id)
const isCounter=(id:string)=>!!finding.value?.stages.some(row=>row.counter_ids.includes(id))
const sourceStage=(id:string)=>finding.value?.stages.findIndex(row=>[...row.support_ids,...row.counter_ids].includes(id))??0
const context=(card:Finding):FindingContext=>({finding:card,source_sha256:collection.value!.source_sha256,analysis_version:collection.value!.analysis_version,scope:collection.value!.scope})
const dayCounts=computed(()=>Array.from({length:14},(_,i)=>{const date=`2040-10-${String(i+1).padStart(2,'0')}`;return {day:i+1,date,count:communications.value.filter(m=>m.date===date).length,stage:finding.value?.stages.findIndex(s=>s.date===date)??-1}}))
const maxDay=computed(()=>Math.max(1,...dayCounts.value.map(d=>d.count)))
function chooseStage(index:number){stageIndex.value=index;const row=finding.value?.stages[index];selectedId.value=(lens.value==='counter'?row?.counter_ids[0]:row?.support_ids[0])||''}
function changeLens(value:string){lens.value=value;chooseStage(stageIndex.value)}
async function chooseSource(id:string,event?:Event){
  stageIndex.value=sourceStage(id);selectedId.value=id;readerOpen.value=true
  lastSource=event?.currentTarget as HTMLElement|SVGElement|undefined
  await nextTick();closeReaderButton.value?.focus({preventScroll:window.innerWidth>1000})
}
async function closeReader(){readerOpen.value=false;await nextTick();lastSource?.focus({preventScroll:true})}
function citations(kind:'support'|'counter'){return (kind==='support'?stage.value?.support_ids:stage.value?.counter_ids)||[]}

// Fixed positions keep a person's identity stable while evidence changes.
const placement:Record<string,{x:number;y:number;lines:string[]}>={
  'Nadia Conti':{x:.43,y:.43,lines:['Nadia Conti']},
  'Haacklee Harbor':{x:.15,y:.22,lines:['Haacklee Harbor']},
  'Oceanus City Council':{x:.13,y:.64,lines:['Oceanus City Council']},
  'Liam Thorne':{x:.78,y:.08,lines:['Liam Thorne']},
  'Neptune':{x:.86,y:.40,lines:['Neptune']},
  'V. Miesel Shipping':{x:.77,y:.65,lines:['V. Miesel Shipping']},
  'Remora':{x:.44,y:.84,lines:['Remora']},
  'Mako':{x:.72,y:.91,lines:['Mako']},
  'Sentinel':{x:.93,y:.91,lines:['Sentinel']},
}
const nodes=computed(()=>[...new Set(finding.value?.evidence.flatMap(m=>[m.sender,m.receiver])||[])].map((id,i)=>{
  const p=placement[id]||{x:.1+(i%5)*.18,y:.12+Math.floor(i/5)*.18,lines:[id]}
  const active=finding.value?.evidence.some(m=>sourceStage(m.id)===stageIndex.value&&(m.sender===id||m.receiver===id))
  return {id,x:p.x*dimensions.value.width,y:36+p.y*(dimensions.value.height-96),lines:p.lines,active,central:id==='Nadia Conti'}
}))
const links=computed(()=>finding.value?.evidence.map(m=>{
  const from=nodes.value.find(n=>n.id===m.sender)!,to=nodes.value.find(n=>n.id===m.receiver)!
  const dx=to.x-from.x,dy=to.y-from.y,length=Math.max(1,Math.hypot(dx,dy)),ux=dx/length,uy=dy/length
  const bend=m.id.endsWith('_529')||m.id.endsWith('_535')?40:0
  const cx=(from.x+to.x)/2-uy*bend,cy=(from.y+to.y)/2+ux*bend
  const startR=from.central?30:13,endR=to.central?36:19
  const path=`M ${from.x+ux*startR} ${from.y+uy*startR} Q ${cx} ${cy} ${to.x-ux*endR} ${to.y-uy*endR}`
  const active=sourceStage(m.id)===stageIndex.value,counter=isCounter(m.id),dim=lens.value!=='all'&&(lens.value==='counter')!==counter
  const color=active&&!dim?(counter?chartColors.gold:chartColors.blue):chartColors.edge
  return {id:m.id,path,cx:(from.x+2*cx+to.x)/4,cy:(from.y+2*cy+to.y)/4,counter,active,dim,color,marker:active&&!dim?(counter?'counter':'support'):'context',cross:!m.sender.includes('Nadia Conti')&&!m.receiver.includes('Nadia Conti')}
})||[])
watch(graphHost,host=>{
  resize?.disconnect()
  if(!host)return
  resize=new ResizeObserver(([entry])=>{if(entry&&entry.contentRect.width>0)dimensions.value={width:Math.max(680,entry.contentRect.width),height:Math.max(400,entry.contentRect.height)}})
  resize.observe(host)
})
onUnmounted(()=>resize?.disconnect())
async function load(){
  busy.value=true;error.value=''
  try{
    const scope={entity_id:'Nadia Conti',start:'2040-10-01',end:'2040-10-14'}
    const [data,stats,records]=await Promise.all([get<Collection>('findings'),get<Overview>('overview',scope),get<Page<Message>>('messages',{...scope,page_size:100})])
    if(!data.items.find(row=>row.id==='nadia')?.stages.length)throw new Error('调查记录尚未就绪')
    collection.value=data;overview.value=stats;communications.value=records.items
  }catch(e){error.value=(e as Error).message}finally{busy.value=false}
}
function exportCase(format:'html'|'json'){
  if(!finding.value||!overview.value||busy.value||error.value)return
  const analysis=context(finding.value),messages=[...finding.value.evidence].sort((a,b)=>a.timestamp.localeCompare(b.timestamp))
  const chartFilters={start:'2040-10-01',end:'2040-10-14',entity_id:'Nadia Conti'}
  const filters={start:chartFilters.start,end:chartFilters.end,ids:messages.map(m=>m.id).join(',')}
  const readingState={stage:stageIndex.value,lens:lens.value,selected_id:selectedId.value,reader_open:readerOpen.value}
  if(format==='json'){exportJson('mc3-nadia-investigation.json',{analysis,chart_filters:chartFilters,filters,messages,reading_state:readingState,source_sha256:collection.value!.source_sha256});return}
  const views=[{source:graph.value,title:'Nadia 调查 · 引用通信关系',caption:'八条引用按原始发送与接收方向连接；实线为支持线索，虚线为竞争解释。Mako—Sentinel 为交叉引用。深色连线标记当前阶段，位置用于关系排布。'},{source:timeline.value,title:'Nadia 全期参与通信',caption:'柱高为每日唯一通信数，含发送与接收；四个调查阶段按实际日期定位。'}].flatMap(({source,title,caption})=>{
    if(!source)return []
    const svg=source.cloneNode(true) as SVGSVGElement
    svg.setAttribute('xmlns','http://www.w3.org/2000/svg');svg.setAttribute('width','100%');svg.removeAttribute('height')
    return [{title,caption,svg:new XMLSerializer().serializeToString(svg)}]
  })
  downloadAnalysisReport({overview:overview.value,chartFilters,filters,messages,evidence:null,analysis,graphControls:readingState,graphDefinition:'关系画布展示八条引用通信，时间轨道统计 Nadia 全期参与的 26 条通信。箭头为原始消息方向，节点位置用于稳定排布。',views})
}
onMounted(load)
</script>

<template>
  <div class="case-study scroll" data-testid="case-study">
    <div v-if="busy" class="case-loading" role="status"><span class="loading-orbit"></span><h2>正在连接人物与原文</h2><p>读取调查阶段、引用通信与时间记录…</p></div>
    <div v-else-if="error" class="case-loading" role="alert"><h2>调查材料暂时无法读取</h2><p>{{error}}</p><button @click="load">重新读取调查材料</button></div>
    <template v-else-if="finding&&overview">
      <section class="case-desk" :class="{'reader-is-open':readerOpen}" aria-label="Nadia 通信调查画布">
        <aside class="case-rail">
          <div class="rail-intro"><h1>Nadia Conti</h1><p>取消通道之后，<br>协调如何继续？</p></div>
          <nav class="case-stage-nav" aria-label="调查阶段">
            <button v-for="(row,index) in finding.stages" :key="row.date" :aria-pressed="stageIndex===index" :data-testid="`case-stage-${index}`" @click="chooseStage(index)"><time>{{row.date.slice(5).replace('-','.')}}</time><span><strong>{{stageNames[index]}}</strong></span><i aria-hidden="true">›</i></button>
          </nav>
          <div class="rail-evidence" aria-live="polite"><div class="rail-section-label">本阶段原文 <span>{{(stage?.support_ids.length||0)+(stage?.counter_ids.length||0)}} 条</span></div><template v-for="kind in (['support','counter'] as const)" :key="kind"><button v-for="id in citations(kind)" :key="id" class="case-source-card" :class="kind" :aria-pressed="selectedId===id&&readerOpen" :data-testid="`case-source-${id}`" @click="chooseSource(id,$event)"><span aria-hidden="true">{{kind==='support'?'●':'◇'}}</span><strong>{{actionLabel(id)}}</strong><small>{{message(id)?.timestamp.slice(11,16)}}</small></button></template><p v-if="lens==='counter'&&!stage?.counter_ids.length" class="rail-gap">这一阶段，继续寻找另一侧证据。</p></div>
          <div class="rail-bottom"><div><button @click="exportCase('html')" data-testid="case-export-html">导出 HTML <span aria-hidden="true">↓</span></button><button @click="exportCase('json')" data-testid="case-export-json">JSON <span aria-hidden="true">↓</span></button></div><a href="#case-analysis">阅读完整分析 <span aria-hidden="true">↓</span></a></div>
        </aside>
        <div class="case-canvas">
          <header class="canvas-heading"><div><h2>{{stageNames[stageIndex]}}<span>{{stage?.date.slice(5).replace('-',' / ')}}</span></h2></div><div class="canvas-counts"><span><b>{{overview.communications}}</b> 全期通信</span><span><b>8</b> 引用原文</span></div></header>
          <div class="canvas-tools"><div class="case-lenses" aria-label="证据阅读视角"><button v-for="item in [{id:'all',name:'全部引用'},{id:'support',name:'支持线索'},{id:'counter',name:'竞争解释'}]" :key="item.id" :aria-pressed="lens===item.id" @click="changeLens(item.id)">{{item.name}}</button></div></div>
          <div ref="graphHost" class="case-graph-host">
            <svg ref="graph" class="case-relation-graph" :viewBox="`0 0 ${dimensions.width} ${dimensions.height}`" role="group" aria-label="八条引用的有向通信关系，实线为支持线索，虚线为竞争解释" font-family="Segoe UI, Microsoft YaHei, sans-serif">
              <defs><marker v-for="(color,name) in {support:chartColors.blue,counter:chartColors.gold,context:chartColors.edge}" :key="name" :id="`case-arrow-${name}`" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" :stroke="color" stroke-width="1.4"/></marker></defs>
              <rect width="100%" height="100%" :fill="chartColors.canvas"/>
              <g v-for="edge in links" :key="edge.id" class="case-mark" role="button" tabindex="0" :aria-label="`${sourceLabel(edge.id)} ${shortId(edge.id)}，${message(edge.id)?.sender} 发给 ${message(edge.id)?.receiver}`" :aria-pressed="selectedId===edge.id&&readerOpen" :data-source="edge.id" :data-stage="sourceStage(edge.id)" :data-sender="message(edge.id)?.sender" :data-receiver="message(edge.id)?.receiver" @click="chooseSource(edge.id,$event)" @keydown.enter.prevent="chooseSource(edge.id,$event)" @keydown.space.prevent="chooseSource(edge.id,$event)">
                <path :d="edge.path" stroke="transparent" stroke-width="26" fill="none"/>
                <path class="relation-line" :d="edge.path" :stroke="edge.color" :stroke-width="selectedId===edge.id?2.3:1.4" :stroke-opacity="edge.dim?.24:edge.active?1:.55" :stroke-dasharray="edge.counter?'6 5':undefined" :marker-end="`url(#case-arrow-${edge.marker})`" fill="none"/>
                <g :transform="`translate(${edge.cx},${edge.cy-(edge.cross?17:0)})`"><rect class="edge-label" x="-57" y="-13" width="114" height="26" rx="5" :fill="edge.active?chartColors.panel:chartColors.canvas" :stroke="edge.active?edge.color:'#BCCBD3'" :stroke-opacity="edge.active?.55:.35"/><text y="4" text-anchor="middle" :fill="edge.active&&!edge.dim?chartColors.ink:chartColors.muted" font-size="12.5">{{actionLabel(edge.id)}}</text></g>
              </g>
              <g v-for="node in nodes" :key="node.id" :transform="`translate(${node.x},${node.y})`" class="case-person"><circle v-if="node.central" r="43" fill="#B9CDF4" fill-opacity=".3"/><circle :r="node.central?28:10" :fill="node.central?chartColors.panel:node.active?chartColors.blue:chartColors.edge" :stroke="node.central||node.active?chartColors.blue:chartColors.edge" :stroke-width="node.central?2:1.5"/><path v-if="node.central" d="M -11 10 Q -11 1 0 1 Q 11 1 11 10 M 0 -2 A 5 5 0 1 0 0 -12 A 5 5 0 1 0 0 -2" fill="none" :stroke="chartColors.blue" stroke-width="1.8" stroke-linecap="round"/><text v-for="(line,i) in node.lines" :key="line" :y="(node.central?-52:32)+i*18" text-anchor="middle" :font-size="node.central?22:14" :font-weight="node.central?600:500" :fill="node.central||node.active?chartColors.ink:chartColors.muted">{{line}}</text></g>
              
            </svg>
          </div>
          <div class="canvas-legend"><span><i class="solid-line"></i>支持线索</span><span><i class="dashed-line"></i>竞争解释</span><span>深色：当前阶段</span><details class="graph-position-note"><summary>图例说明</summary><p>箭头表示消息方向，节点位置用于关系排布。深色连线对应当前阶段；Mako 与 Sentinel 的通信为关联主体交叉引用。</p></details></div>
          <section class="case-time-track" aria-label="全期通信时间轨道"><div class="track-heading"><strong>Nadia 每日通信数</strong><span>10.01 — 10.14</span></div><svg ref="timeline" class="case-timeline" :viewBox="`0 0 ${dimensions.width} 76`" role="group" aria-label="Nadia 每日参与通信柱形图，四个调查日期可以选择" font-family="Segoe UI, Microsoft YaHei, sans-serif"><rect width="100%" height="76" fill="#D6E2F6"/><path :d="`M 26 48 H ${dimensions.width-26}`" stroke="#BECDE6"/><g v-for="(day,i) in dayCounts" :key="day.date" :data-count="day.count" :transform="`translate(${(i+.5)*dimensions.width/14},0)`"><rect v-if="day.stage===stageIndex" x="-24" y="3" width="48" height="68" rx="4" fill="#C1D4F5"/><rect x="-12" :y="46-day.count/maxDay*31" width="24" :height="day.count/maxDay*31" rx="2" :fill="day.stage===stageIndex?chartColors.blue:chartColors.edge"/><text v-if="day.count" :y="42-day.count/maxDay*31" text-anchor="middle" :fill="chartColors.muted" font-size="10">{{day.count}}</text><text y="66" text-anchor="middle" :fill="day.stage===stageIndex?chartColors.ink:chartColors.muted" font-size="11">{{String(day.day).padStart(2,'0')}}</text><g v-if="day.stage>=0" role="button" tabindex="0" :aria-label="`选择 ${day.date} 调查阶段`" :aria-pressed="day.stage===stageIndex" @click="chooseStage(day.stage)" @keydown.enter.prevent="chooseStage(day.stage)" @keydown.space.prevent="chooseStage(day.stage)" class="track-day"><rect x="-28" y="0" width="56" height="74" fill="transparent"/><path d="M -3 51 L 0 48 L 3 51 L 0 54 Z" :fill="chartColors.blue"/></g></g></svg></section>
        </div>
        <aside v-if="readerOpen" class="case-reader" aria-label="当前原文" @keydown.esc.prevent="closeReader">
          <div class="reader-top"><span>原文核查</span><button ref="closeReaderButton" aria-label="关闭原文" @click="closeReader">×</button></div>
          <div class="reader-content"><template v-if="selected"><div class="source-heading"><div class="source-meta"><span :class="{counter:isCounter(selected.id)}">{{isCounter(selected.id)?'◇ 竞争解释':'● 支持线索'}}</span><span>{{shortId(selected.id)}}</span></div><h2>{{note?.label}}</h2></div><div v-if="note" class="source-reading"><blockquote>“{{note.excerpt}}”</blockquote><p>{{note.reading}}</p></div><details open class="case-original"><summary>英文原文 · 完整通信</summary><p>{{selected.content}}</p></details><details class="source-details"><summary>通信信息与来源</summary><time>{{selected.timestamp}}</time><p class="source-provenance">{{selected.id}}<br>{{selected.evidence_ids.length}} 条关联证据 · {{selected.sender==='Nadia Conti'||selected.receiver==='Nadia Conti'?'Nadia 直接参与通信':'关联主体的交叉引用'}}</p><div class="case-participants"><span>{{selected.sender}}</span><span aria-hidden="true">↓</span><span>{{selected.receiver}}</span></div></details><button class="case-inspect" @click="emit('inspect',context(finding),selected.id)" data-testid="case-inspect">检查原始关系与来源 <span aria-hidden="true">↗</span></button></template><div v-else class="reader-empty"><h2>这一阶段，继续寻找另一侧证据。</h2><p>{{stage?.gap}}</p><button @click="changeLens('all')">查看全部引用</button></div></div>
        </aside>
      </section>
      <div id="case-analysis" class="case-analysis">
        <section class="case-conclusion"><div><h2>Nadia 的协调，<br>贯穿四个阶段。</h2><p>{{finding.claim}}</p></div><div class="conclusion-details"><div><strong>文件处置与对外说明</strong><p>10 月 5 日，Nadia 向 Harbor 要求取消通道、销毁文件；四分钟后，她向 Council 解释旅游项目的时间冲突。</p></div><div><strong>报酬与巡逻安排</strong><p>10 月 8 日，Nadia 提出双倍报酬；Liam 回复称已调整巡逻，确认次日晚间会面，并要求携带约定报酬。</p></div><div><strong>作业推进与批准请求</strong><p>10 月 12 日，Nadia 建议加速并转移作业；14 日，Remora 向她汇报准备进度，并请求水下照明的最终批准。</p></div></div></section>
        <section class="case-questions"><h2>四个调查问题</h2><nav aria-label="调查问题"><button v-for="q in questions" :key="q.id" :aria-pressed="question===q.id" @click="question=q.id" :data-testid="`case-question-${q.id}`"><span>{{q.number}}</span>{{q.title}}</button></nav><template v-if="activeQuestion"><h3>{{activeQuestion.title}}</h3><p>{{activeQuestion.claim}}</p><table v-if="question==='rhythm'" class="rhythm-comparison"><thead><tr><th>主体</th><th>第 1 周</th><th>第 2 周</th><th>参与通信中位时间</th></tr></thead><tbody><tr v-for="row in changes" :key="row.entity"><th>{{row.entity}}</th><td>{{row.first_count}} 条</td><td>{{row.second_count}} 条</td><td>{{row.first_median}} → {{row.second_median}}</td></tr></tbody></table><ol><li v-for="step in activeQuestion.reasoning_steps" :key="step.observation"><strong>{{step.observation}}</strong><p>{{step.interpretation}}</p><div><button v-for="id in step.message_ids" :key="id" class="link" @click="emit('inspect',context(activeQuestion),id)">{{shortId(id)}} ↗</button></div></li></ol><button class="case-primary" @click="emit('explore',context(activeQuestion))" data-testid="case-explore">进入对应分析工具 ↗</button></template></section>
      </div>
    </template>
  </div>
</template>

<style scoped src="./CaseStudyView.css"></style>
