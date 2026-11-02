<script setup lang="ts">
import { chartColors } from '../theme'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { HeatmapChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { SVGRenderer } from 'echarts/renderers'
import { get } from '../api'
import type { Heat,Message,Page } from '../api'
import { selectCell, selection,useViewReadiness } from '../store'

echarts.use([HeatmapChart,LineChart,GridComponent,TooltipComponent,VisualMapComponent,SVGRenderer])
const props=defineProps<{data:Heat}>()
const emit=defineEmits<{evidence:[id:string]}>()
const heatEl=ref<HTMLElement>(),trendEl=ref<HTMLElement>()
const overview=ref<Heat>(props.data),messages=ref<Message[]>([]),detailError=ref(''),detailBusy=ref(false),activeHours=ref(true)
const focusDay=ref(selection.start)
const overviewBusy=ref(true),overviewError=ref('')
useViewReadiness('temporal',()=>!detailBusy.value&&!overviewBusy.value&&!detailError.value&&!overviewError.value)
let chart:echarts.ECharts|undefined,trend:echarts.ECharts|undefined,observer:ResizeObserver|undefined,request=0,overviewRequest=0
const peaks=computed(()=>[...overview.value.cells].filter(c=>c.count>0).sort((a,b)=>b.count-a.count||a.date.localeCompare(b.date)||a.hour-b.hour).slice(0,3))
const lanes=computed(()=>[...new Set(messages.value.flatMap(m=>[m.sender,m.receiver]))].sort())
const highlightedCount=computed(()=>messages.value.filter(m=>m.hour===selection.hour).length)
const timeDomain=computed(()=>{if(!activeHours.value||!messages.value.length)return [0,24];const values=messages.value.map(m=>minute(m.timestamp)/60);return [Math.max(0,Math.floor(Math.min(...values))),Math.min(24,Math.ceil(Math.max(...values))||1)]})
function minute(timestamp:string){return Number(timestamp.slice(11,13))*60+Number(timestamp.slice(14,16))+Number(timestamp.slice(17,19)||0)/60}
function x(m:Message){return 156+(minute(m.timestamp)/60-timeDomain.value[0]!)/Math.max(1,timeDomain.value[1]!-timeDomain.value[0]!)*624}
function y(id:string){return 34+lanes.value.indexOf(id)*27}
const ticks=computed(()=>Array.from({length:timeDomain.value[1]!-timeDomain.value[0]!+1},(_,i)=>timeDomain.value[0]!+i))
function tickX(hour:number){return 156+(hour-timeDomain.value[0]!)/Math.max(1,timeDomain.value[1]!-timeDomain.value[0]!)*624}
function chooseMessage(m:Message){selection.messageIds=[m.id];emit('evidence',m.id)}
function chooseDay(){selection.start=focusDay.value;selection.end=focusDay.value;selection.hour=null}
async function loadDetails(){const current=++request;detailBusy.value=true;detailError.value='';try{const first=await get<Page<Message>>('messages',{start:focusDay.value,end:focusDay.value,entity_id:selection.entity,q:selection.q,page_size:100});let records=[...first.items];for(let page=2;page<=Math.ceil(first.total/100);page++)records.push(...(await get<Page<Message>>('messages',{start:focusDay.value,end:focusDay.value,entity_id:selection.entity,q:selection.q,page,page_size:100})).items);if(current===request)messages.value=records}catch(e){if(current===request){messages.value=[];detailError.value=(e as Error).message}}finally{if(current===request)detailBusy.value=false}}
async function loadOverview(){const current=++overviewRequest;overviewBusy.value=true;overviewError.value='';try{const result=await get<Heat>('temporal/heatmap',{start:'2040-10-01',end:'2040-10-14',entity_id:selection.entity,q:selection.q});if(current===overviewRequest){overview.value=result;draw()}}catch(e){if(current===overviewRequest)overviewError.value=(e as Error).message}finally{if(current===overviewRequest)overviewBusy.value=false}}
function draw(){
 if(!chart||!trend||!heatEl.value?.clientWidth)return
 const source=overview.value,max=Math.max(1,...source.cells.map(c=>c.count))
 chart.setOption({animation:false,grid:{left:48,right:18,top:12,bottom:48},tooltip:{position:'top',backgroundColor:chartColors.panel,borderColor:chartColors.line,textStyle:{color:chartColors.ink,fontSize:12},formatter:(p:unknown)=>{const v=(p as {value:number[]}).value;const c=source.cells.find(c=>c.date===source.days[v[1]!]&&c.hour===v[0]);return c?`${c.date} ${String(c.hour).padStart(2,'0')}:00<br/>通信 ${c.count} 条 · 其他日期同小时均值 ${c.baseline}`:''}},xAxis:{type:'category',data:Array.from({length:24},(_,i)=>i),axisLine:{show:false},axisTick:{show:false},axisLabel:{color:chartColors.muted,fontSize:12,interval:5,formatter:(v:string)=>v.padStart(2,'0')+':00'}},yAxis:{type:'category',data:source.days,inverse:true,axisLine:{show:false},axisTick:{show:false},axisLabel:{color:chartColors.muted,fontSize:12,formatter:(v:string)=>v.slice(5).replace('-','/')}},visualMap:{min:0,max,orient:'horizontal',left:'center',bottom:2,itemWidth:9,itemHeight:95,text:[String(max)+' 条','0'],textStyle:{color:chartColors.muted,fontSize:11},inRange:{color:chartColors.heat}},series:[{type:'heatmap',data:source.cells.map(c=>({value:[c.hour,source.days.indexOf(c.date),c.count],itemStyle:{opacity:c.date>=selection.start&&c.date<=selection.end?1:.3,borderColor:selection.hour===c.hour&&c.date===selection.start?chartColors.gold:chartColors.panel,borderWidth:selection.hour===c.hour&&c.date===selection.start?2:1}})),emphasis:{itemStyle:{borderColor:chartColors.blue,borderWidth:2}}}]},true)
 trend.setOption({animation:false,grid:{left:42,right:18,top:10,bottom:24},tooltip:{trigger:'axis',backgroundColor:chartColors.panel,borderColor:chartColors.line,textStyle:{color:chartColors.ink,fontSize:12}},xAxis:{type:'category',data:source.daily.map(d=>d.date.slice(5)),boundaryGap:false,axisLine:{lineStyle:{color:chartColors.line}},axisTick:{show:false},axisLabel:{color:chartColors.muted,fontSize:11,interval:2}},yAxis:{type:'value',min:0,splitNumber:2,axisLabel:{color:chartColors.muted,fontSize:11},splitLine:{lineStyle:{color:chartColors.line,type:'dashed'}}},series:[{name:'通信量',type:'line',data:source.daily.map(d=>d.count),symbol:'circle',symbolSize:5,lineStyle:{color:chartColors.blue,width:2},itemStyle:{color:chartColors.blue},areaStyle:{color:chartColors.blue,opacity:.07}}]},true)
}
onMounted(()=>{chart=echarts.init(heatEl.value!,undefined,{renderer:'svg'});trend=echarts.init(trendEl.value!,undefined,{renderer:'svg'});chart.on('click',p=>{const v=p.value as number[];selectCell(overview.value.days[v[1]!]!,v[0]!)});trend.on('click',p=>{const day=overview.value.daily[p.dataIndex];if(day){focusDay.value=day.date;chooseDay()}});observer=new ResizeObserver(()=>{if(heatEl.value?.clientWidth){chart?.resize();trend?.resize();draw()}});observer.observe(heatEl.value!);draw();loadOverview()})
watch(()=>props.data,draw)
watch(()=>selection.start,day=>{focusDay.value=day;draw()})
watch(()=>selection.end,draw)
watch(()=>selection.hour,draw)
watch([()=>selection.entity,()=>selection.q],loadOverview)
watch([focusDay,()=>selection.entity,()=>selection.q],loadDetails,{immediate:true})
onBeforeUnmount(()=>{observer?.disconnect();chart?.dispose();trend?.dispose()})
</script>
<template>
 <div class="temporal-view"><div ref="heatEl" class="heat-chart" data-testid="heatmap" aria-label="通信日期小时热力图"></div><h3 class="chart-caption">每日通信量</h3><div ref="trendEl" class="trend-chart" aria-label="每日通信量"></div><div class="peak-row"><span>密集时段</span><button v-for="c in peaks" :key="c.date+c.hour" class="chip" data-testid="peak-cell" :data-count="c.count" @click="selectCell(c.date,c.hour)">{{c.date.slice(5)}} {{String(c.hour).padStart(2,'0')}}:00 · {{c.count}} 条</button></div>
 <div class="day-heading"><h3>单日通信细节</h3><select aria-label="展开日期" v-model="focusDay" @change="chooseDay"><option v-for="day in overview.days" :key="day">{{day}}</option></select><label><input type="checkbox" v-model="activeHours">聚焦活跃时段</label></div>
 
 <div v-if="detailError||overviewError" class="error">{{detailError||overviewError}}</div><div class="daily-scroll scroll" :aria-busy="detailBusy"><svg v-if="messages.length" class="daily-detail" data-testid="daily-detail" :viewBox="`0 0 804 ${Math.max(100,lanes.length*27+50)}`" role="img" aria-label="单日主体通信泳道"><defs><marker id="daily-arrow" viewBox="0 -3 6 6" refX="4" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,-3L6,0L0,3" fill="#286a86"/></marker></defs><g v-for="hour in ticks" :key="hour"><line :x1="tickX(hour)" :x2="tickX(hour)" y1="26" :y2="lanes.length*27+24" stroke="#e0e8ed"/><text :x="tickX(hour)" y="15" text-anchor="middle" fill="#5c6c76" font-size="11">{{String(hour).padStart(2,'0')}}:00</text></g><g v-for="lane in lanes" :key="lane"><line x1="151" x2="790" :y1="y(lane)" :y2="y(lane)" stroke="#cedae1"/><text x="143" :y="y(lane)+4" text-anchor="end" fill="#243541" font-size="12">{{lane}}</text></g><g v-for="m in messages" :key="m.id" class="daily-message" data-testid="daily-message" :data-id="m.id" role="button" tabindex="0" :aria-label="`${m.timestamp} ${m.sender} 到 ${m.receiver}`" @click="chooseMessage(m)" @keydown.enter.prevent="chooseMessage(m)" :opacity="selection.hour===null||m.hour===selection.hour?1:.15"><path :d="`M ${x(m)} ${y(m.sender)} Q ${x(m)+9} ${(y(m.sender)+y(m.receiver))/2} ${x(m)} ${y(m.receiver)}`" stroke="#286a86" stroke-width="1.6" fill="none" marker-end="url(#daily-arrow)"/><circle :cx="x(m)" :cy="y(m.sender)" r="2.5" fill="#f8fafb" stroke="#286a86"/><title>{{m.id}} · {{m.timestamp}}&#10;{{m.sender}} → {{m.receiver}}&#10;{{m.content}}</title></g></svg><div v-else class="empty">{{detailBusy?'正在读取通信…':'该日没有匹配通信'}}</div></div>
 <details class="day-reading"><summary>单日图说明</summary><p class="day-caption"><strong>{{focusDay}} 全天背景</strong> · {{messages.length}} 条消息 · {{lanes.length}} 个主体。<span v-if="selection.hour!==null">当前 {{selection.hour}} 时高亮 {{highlightedCount}} 条，其他时段淡化显示。</span><span v-else>显示该日全部匹配通信。</span>沿用主体与检索条件；横轴为时间，连线从发送方指向接收方。点击连线查看原文。</p></details>
 </div>
</template>
<style scoped>
.chart-caption{font-size:13px;font-weight:600;color:var(--ink);padding:12px 14px 0;margin:0}.heat-chart{height:312px;width:100%}.chart-caption{border-top:1px solid var(--selected)}.trend-chart{height:93px}.peak-row{display:flex;gap:6px;align-items:center;padding:0 14px 12px;font-size:12px;color:var(--muted);flex-wrap:wrap}.peak-row .chip{font-size:12px}.day-heading{display:flex;align-items:center;gap:10px;border-top:1px solid var(--selected);padding:12px 14px 0}.day-heading h3{font-size:13px;font-weight:600;margin:0;margin-right:auto}.day-heading select{font-size:12px;padding:4px}.day-heading label{font-size:12px;color:var(--muted);white-space:nowrap}.day-heading input{margin:0 3px 0 0}.day-reading{margin:12px 14px;font-size:13px;color:var(--ink)}.day-reading summary{cursor:pointer}.day-caption{font-size:13px;line-height:1.8;margin:10px 0}.daily-scroll{max-height:285px;min-height:100px;padding:0 10px 10px}.daily-detail{display:block;width:100%;min-width:550px}.daily-message{cursor:pointer}.daily-message:hover path,.daily-message:focus path{stroke:#d39437;stroke-width:3}.daily-message:hover circle{fill:#d39437}.daily-message:focus{outline:none}@media(max-width:1450px){.heat-chart{height:290px}.daily-scroll{max-height:220px}}
</style>
