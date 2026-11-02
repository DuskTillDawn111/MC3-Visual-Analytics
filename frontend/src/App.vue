<script setup lang="ts">
import { computed, onMounted, ref, watch,nextTick } from 'vue'
import { get } from './api'
import type { Entity, Overview, Heat, GraphData, GraphEdge, Message, Page, Evidence } from './api'
import { filters, reset, selection, selectEntity, exportJson, canUndo, undoFilters, viewReadiness } from './store'
import { captureReportViews, downloadAnalysisReport } from './report'
import type { FindingContext } from './report'
import FindingsPanel from './components/FindingsPanel.vue'
import CaseStudyView from './components/CaseStudyView.vue'
import TemporalView from './components/TemporalView.vue'
import NetworkView from './components/NetworkView.vue'
import EvidencePanel from './components/EvidencePanel.vue'
import EventView from './components/EventView.vue'
import AnomalyView from './components/AnomalyView.vue'
import AliasView from './components/AliasView.vue'
import TopicView from './components/TopicView.vue'

const entities=ref<Entity[]>([]), overview=ref<Overview>(), heat=ref<Heat>(), graph=ref<GraphData>()
const busy=ref(false), error=ref(''), mode=ref('communication'), inferred=ref('all'), hops=ref(1), community=ref(''), edgeType=ref('')
const focus=ref('')
const plotScroll=ref<HTMLElement>()
const viewOptions=computed(()=>workspace.value==='patterns'
  ? [{id:'network',label:'通信关系'},{id:'temporal',label:'时间与异常'}]
  : workspace.value==='groups'
    ? [{id:'network',label:'群体关系'},{id:'topics-panel',label:'主题比较'}]
    : [{id:'alias-panel',label:'化名候选'},{id:'event-panel',label:'事件溯源'}])
function switchView(id:string){focus.value=id}
watch(focus,async()=>{await nextTick();plotScroll.value?.scrollTo({top:0})})
const findingsOpen=ref(false),activeFinding=ref<FindingContext>()
const workspace=ref('case'), readerCollapsed=ref(false), evidenceId=ref(''), selectedEdge=ref<GraphEdge>(), qualityOpen=ref(false)
const evidenceFocus=ref(0)
const searchInput=ref(''), revision=ref(0), resetKey=ref(0)
const scope=computed(()=>selection.start===selection.end ? selection.start : `${selection.start} — ${selection.end}`)
const synchronizedScope=ref(''),syncFailed=ref(false),exporting=ref(false)
const scopeKey=computed(()=>JSON.stringify({...filters.value,mode:mode.value,inferred:inferred.value,hops:hops.value,community:community.value,edge_type:edgeType.value}))
const scopeReady=computed(()=>!!overview.value&&!busy.value&&!syncFailed.value&&synchronizedScope.value===scopeKey.value)
const visibleViews=computed(()=>workspace.value==='patterns'?['temporal']:workspace.value==='groups'?['topics']:['aliases','events'])
const reportReady=computed(()=>scopeReady.value&&visibleViews.value.every(name=>viewReadiness[name]))
let requestNumber=0
async function refresh() {
  const request=++requestNumber,key=scopeKey.value; busy.value=true; error.value='';syncFailed.value=false
  try {
    const [o,t,g]=await Promise.all([get<Overview>('overview',filters.value),get<Heat>('temporal/heatmap',filters.value),get<GraphData>('graph',{...filters.value,mode:mode.value,inferred:inferred.value,hops:hops.value,community:community.value || undefined,edge_type:edgeType.value || undefined})])
    if(request!==requestNumber)return
    overview.value=o;heat.value=t;graph.value=g;synchronizedScope.value=key;revision.value++
  } catch(e) { if(request===requestNumber){error.value=(e as Error).message;syncFailed.value=true} }
  finally { if(request===requestNumber)busy.value=false }
}
function openEvidence(id:string) { evidenceId.value=id;evidenceFocus.value++;readerCollapsed.value=false }
function chooseEntity(id:string) { selectEntity(id);community.value=''; selectedEdge.value=undefined;openEvidence(id) }
function chooseEdge(edge:GraphEdge) { selectedEdge.value=edge;selection.messageIds=edge.message_ids;openEvidence(edge.source.startsWith('Event_')||edge.source.startsWith('Relationship_')?edge.source:edge.target.startsWith('Event_')||edge.target.startsWith('Relationship_')?edge.target:edge.message_ids[0]||edge.source) }
function submitSearch() { selection.q=searchInput.value.trim();selection.messageIds=[];if(selection.q.startsWith('Event_')||selection.q.startsWith('Relationship_'))openEvidence(selection.q) }
function clear() { reset();resetKey.value++;searchInput.value='';community.value='';edgeType.value='';inferred.value='all';selectedEdge.value=undefined;evidenceId.value='';mode.value='communication';activeFinding.value=undefined }
async function restoreFinding(context:FindingContext){
  clear();workspace.value=context.finding.state.workspace;focus.value='';findingsOpen.value=false
  Object.assign(selection,context.finding.state.filters)
  await nextTick()
  selection.messageIds=[...context.finding.state.message_ids];activeFinding.value=context
  const first=context.finding.state.message_ids[0];if(first)openEvidence(first)
}
async function inspectCase(context:FindingContext,id:string){await restoreFinding(context);openEvidence(id)}
async function download(format:'json'|'html'='json') {
  if(!overview.value||!reportReady.value||exporting.value)return
  exporting.value=true
  const snapshot=JSON.parse(JSON.stringify(overview.value)) as Overview
  const chartFilters={...filters.value}
  const views=format==='html'?captureReportViews():[]
  const graphSnapshot=graph.value
  const analysisSnapshot=activeFinding.value?JSON.parse(JSON.stringify(activeFinding.value)) as FindingContext:undefined
  const controls={mode:mode.value,inferred:inferred.value,hops:hops.value,community:community.value,edge_type:edgeType.value}
  const nodeId=evidenceId.value
  try {
    const selectedFilters={...chartFilters,entity_id:selection.messageIds.length?undefined:chartFilters.entity_id,ids:selection.messageIds.join(','),page_size:100}
    const first=await get<Page<Message>>('messages',{...selectedFilters,page:1})
    const messages=[...first.items]
    for(let page=2;page<=Math.ceil(first.total/100);page++)messages.push(...(await get<Page<Message>>('messages',{...selectedFilters,page})).items)
    const evidence=nodeId?await get<Evidence>(`evidence/${encodeURIComponent(nodeId)}`):null
    if(format==='html')downloadAnalysisReport({overview:snapshot,filters:selectedFilters,chartFilters,messages,evidence,views,graphControls:controls,graphDefinition:graphSnapshot?.definition||'',analysis:analysisSnapshot})
    else exportJson('mc3-selected-evidence.json',{exported_at:new Date().toISOString(),filters:selectedFilters,chart_filters:chartFilters,messages,evidence,analysis:analysisSnapshot,source_sha256:snapshot.quality.source_sha256,interpretation:'Selected records and associations, not causal or identity confirmation'})
  }catch(e){error.value=(e as Error).message}finally{exporting.value=false}
}
watch(workspace,async()=>{focus.value='';await nextTick();plotScroll.value?.scrollTo({top:0})})
watch(mode,value=>{if(value==='communication')edgeType.value=''})
watch([filters,mode,inferred,hops,community,edgeType],()=>{selection.messageIds=[];selectedEdge.value=undefined;refresh()},{deep:true})
onMounted(async()=>{try{entities.value=await get<Entity[]>('entities')}catch(e){error.value=(e as Error).message}await refresh()})
</script>

<template>
  <div class="workbench" :class="{'case-mode':workspace==='case'}"><main>
    <header class="masthead">
      <div class="identity"><svg class="brand-mark" viewBox="0 0 28 28" aria-hidden="true"><path d="M 3 8 C 9 1 19 1 25 8 M 3 15 C 9 8 19 8 25 15 M 3 22 C 9 15 19 15 25 22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg><h1>暗潮寻踪</h1></div>
      <nav class="workspace-tabs" aria-label="分析工作区">
        <button :class="{active:workspace==='case'}" @click="workspace='case'" data-testid="workspace-case">证据调查</button>
        <button :class="{active:workspace==='patterns'}" @click="workspace='patterns'" data-testid="workspace-patterns">通信模式</button>
        <button :class="{active:workspace==='groups'}" @click="workspace='groups'" data-testid="workspace-groups">群体与主题</button>
        <button :class="{active:workspace==='investigation'}" @click="workspace='investigation'" data-testid="workspace-investigation">身份与事件调查</button>
      </nav>
      <div v-if="workspace==='case'" class="header-meta"><button @click="workspace='patterns'">探索全部通信 ↗</button></div>
      <div v-else class="header-meta"><button :aria-expanded="findingsOpen" @click="findingsOpen=!findingsOpen">分析发现</button><button :disabled="!reportReady||exporting" @click="download('json')">导出证据</button><button class="primary-action" :disabled="!reportReady||exporting" @click="download('html')">↓ 导出报告</button></div>
    </header>
    <CaseStudyView v-show="workspace==='case'" @explore="restoreFinding" @inspect="inspectCase"/>
    <FindingsPanel :open="findingsOpen&&workspace!=='case'" @close="findingsOpen=false" @select="restoreFinding" @evidence="findingsOpen=false;openEvidence($event)"/>
    <div v-if="activeFinding" class="active-finding" style="font-size:12px;padding:5px 0;color:#425b70">已恢复分析：{{activeFinding.finding.title}} · 全期分析<button class="link" @click="findingsOpen=true">查看分析依据 ↗</button><button class="inline" aria-label="移除当前分析说明" @click="activeFinding=undefined">×</button></div>
    <section class="toolbar" aria-label="全局筛选">
      <label class="date-filter">观察期 <input aria-label="开始日期" data-testid="start-date" v-model="selection.start" type="date"><span>—</span><input aria-label="结束日期" data-testid="end-date" v-model="selection.end" type="date"></label>
      <label>主体 <select aria-label="分析主体" data-testid="entity-filter" v-model="selection.entity"><option value="">全部实体</option><option v-for="entity in entities" :key="entity.id" :value="entity.id">{{entity.id}} · {{entity.sub_type}}</option></select></label>
      <form class="search" @submit.prevent="submitSearch"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5"/><path d="m13 13 4 4"/></svg><input aria-label="搜索" data-testid="search" v-model="searchInput" placeholder="实体、事件 ID 或英文消息"><button type="submit">检索</button></form>
      <button class="reset" :disabled="!canUndo" @click="undoFilters" data-testid="undo-filters">撤销</button><button class="reset" data-testid="reset" @click="clear">↺ 重置</button>
    </section>
    <div v-if="error" class="error" role="alert">{{error}} <button @click="refresh">重试</button></div>
    <section class="metrics" v-if="overview" aria-label="当前筛选统计">
      <span><strong data-testid="communication-count">{{overview.communications}}</strong><span class="metric-total"> / {{overview.total_communications}}</span> 条通信</span>
      <span><strong data-testid="entity-count">{{overview.entities}}</strong> 个主体</span><span><strong>{{overview.projection_edges}}</strong> 个联系</span><span><strong>{{overview.evidence_targets}}</strong> 个证据目标</span>
      <div class="context-line" :title="'当前范围：'+scope">
        <b v-if="selection.hour!==null">{{String(selection.hour).padStart(2,'0')}}:00–{{String(selection.hour+1).padStart(2,'0')}}:00 <button class="inline" aria-label="清除小时筛选" @click="selection.hour=null">×</button></b>
        <span v-if="selection.q">检索：{{selection.q}}</span>
        <span class="sync-state" :class="{ready:reportReady}" aria-live="polite">{{busy?'正在同步…':reportReady?'已同步':scopeReady?'正在准备分析视图…':'未同步 · 请重试'}}</span>
      </div>
      <button class="link" @click="qualityOpen=!qualityOpen">数据质量 {{qualityOpen?'收起':'检查'}} ↗</button>
    </section>
    <div v-else-if="busy" class="loading">正在读取官方数据…</div>
    <div v-show="workspace!=='case'" class="analysis-grid" :class="[workspace,{'reader-collapsed':readerCollapsed}]" :inert="!scopeReady" :aria-busy="!scopeReady">
      <div class="analysis-canvas">
        <nav class="view-switcher" aria-label="图表视图">
          <button :aria-pressed="focus===''" @click="switchView('')" data-testid="view-overview">全部视图</button>
          <button v-for="view in viewOptions" :key="view.id" :aria-pressed="focus===view.id" @click="switchView(view.id)" :data-testid="'view-'+view.id">{{view.label}}</button>
        </nav>
        <div ref="plotScroll" class="plot-scroll scroll"><div class="plot-grid" :class="{'focus-mode':!!focus}">
        <section v-show="workspace!=='investigation'" class="panel network" :class="{focused:focus==='network'}"><div class="panel-heading"><button class="panel-expand" aria-label="放大关系图" @click="focus=focus==='network'?'':'network'">{{focus==='network'?'返回总览':'放大'}}</button><h2>{{workspace==='groups'?'群体关系探索':'通信关系'}}</h2><select aria-label="图模式" v-model="mode"><option value="communication">通信投影</option><option value="original">原始关系检查</option></select></div>
          <div class="graph-controls"><select aria-label="邻域" v-model.number="hops"><option :value="1">1 跳邻域</option><option :value="2">2 跳邻域</option></select><select aria-label="社区" v-model="community"><option value="">全部社区</option><option v-for="c in graph?.communities" :value="String(c.id)" :key="c.id">社区 {{c.id+1}} · {{c.size}} 实体</option></select><select aria-label="推断过滤" v-model="inferred"><option value="all">全部记录</option><option value="recorded">直接记录</option><option value="inferred">推断关联</option></select><select v-if="mode==='original'" aria-label="边类型" v-model="edgeType"><option value="">全部边类型</option><option>sent</option><option>received</option><option>evidence_for</option><option value="structural">结构关联</option></select><span>{{graph?.nodes.length || 0}} 节点 · {{graph?.edges.length || 0}} 连接</span></div>
          <NetworkView v-if="graph" :data="graph" :selected="selection.entity" :selected-message-ids="selection.messageIds" @entity="chooseEntity" @evidence="openEvidence" @edge="chooseEdge"/>
        </section>
        <section v-show="workspace==='patterns'" class="panel temporal" :class="{focused:focus==='temporal'}"><div class="panel-heading"><button class="panel-expand" aria-label="放大时间图" @click="focus=focus==='temporal'?'':'temporal'">{{focus==='temporal'?'返回总览':'放大'}}</button><h2>每日通信模式</h2></div><TemporalView v-if="heat" :data="heat" @evidence="openEvidence"/><div v-else class="empty">等待数据</div><AnomalyView :revision="revision" :reset-key="resetKey" @evidence="openEvidence"/></section>
        <section v-if="workspace==='groups'" class="panel topics-panel" :class="{focused:focus==='topics-panel'}"><div class="panel-heading"><button class="panel-expand" aria-label="放大主题图" @click="focus=focus==='topics-panel'?'':'topics-panel'">{{focus==='topics-panel'?'返回总览':'放大'}}</button><h2>群体与主题比较</h2></div><TopicView :revision="revision" @evidence="openEvidence"/></section>
        <section v-show="workspace==='investigation'" class="panel alias-panel" :class="{focused:focus==='alias-panel'}"><div class="panel-heading"><button class="panel-expand" aria-label="放大候选图" @click="focus=focus==='alias-panel'?'':'alias-panel'">{{focus==='alias-panel'?'返回总览':'放大'}}</button><h2>化名候选比较</h2></div><AliasView :revision="revision" :entities="entities" :reset-key="resetKey" @entity="chooseEntity" @evidence="openEvidence"/></section>
        <section v-show="workspace==='investigation'" class="panel event-panel" :class="{focused:focus==='event-panel'}"><div class="panel-heading"><button class="panel-expand" aria-label="放大事件图" @click="focus=focus==='event-panel'?'':'event-panel'">{{focus==='event-panel'?'返回总览':'放大'}}</button><h2>事件溯源</h2><button class="chip" @click="chooseEntity('Nadia Conti')">调查 Nadia Conti ↗</button></div><EventView :revision="revision" :reset-key="resetKey" @entity="chooseEntity" @evidence="openEvidence"/></section>
      </div></div></div>
      <section class="panel evidence-panel"><div class="panel-heading"><h2>原文与证据</h2><button class="reader-toggle" :aria-label="readerCollapsed?'展开证据栏':'收起证据栏'" @click="readerCollapsed=!readerCollapsed">{{readerCollapsed?'‹':'›'}}</button></div><EvidencePanel :revision="revision" :evidence-id="evidenceId" :focus-key="evidenceFocus" :selected-edge="selectedEdge" @entity="chooseEntity" @evidence="openEvidence"/></section>
    </div>
    <section class="quality-banner" v-if="overview&&qualityOpen"><button @click="qualityOpen=false">数据质量：{{overview.quality.missing_timestamp_count}} 个事件缺时间 · {{overview.quality.timestamp_outliers.length}} 个异常年份 · {{overview.quality.communications_without_evidence.length}} 条通信无证据连接 <span>关闭 ×</span></button><div class="quality-details"><p>原始图 {{overview.total_nodes}} 节点 / {{overview.total_edges}} 边：{{overview.quality.recorded_edges}} 条直接记录，{{overview.quality.inferred_edges}} 条推断。官方数据为合成竞赛记录，无经纬度。故事时间为 2040 年，原始记录未指定时区。</p><p v-for="o in overview.quality.timestamp_outliers" :key="o.id"><button class="link" @click="openEvidence(o.id)">{{o.id}}</button>：{{o.timestamp}}，保留原值，默认主时间分析排除。</p><p>缺失 timestamp 的事件仍保留，可在事件溯源中检查。</p><div class="quality-ids"><button v-for="id in overview.quality.missing_timestamp_ids" :key="id" class="chip" @click="openEvidence(id)">{{id}}</button></div></div></section>
  </main></div>
</template>
