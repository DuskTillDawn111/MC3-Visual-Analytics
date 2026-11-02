<script setup lang="ts">
import { chartColors } from '../theme'
import { computed,ref,watch } from 'vue'
import { get } from '../api'
import type { Message,Page,TopicData } from '../api'
import { filters,palette,topicPalette,selection,exportJson,useViewReadiness } from '../store'
const props=defineProps<{revision:number}>()
const emit=defineEmits<{evidence:[id:string]}>()
type TopicModelData=TopicData & {assignments:{message_id:string;weights:number[]}[]}
const data=ref<TopicModelData>(),topicCount=ref(6),chosen=ref(0),busy=ref(false),error=ref('')
const chosenGroup=ref<number|null>(null),groupSamples=ref<Message[]>([]),samplesBusy=ref(false)
const metric=ref('count'),sampleMode=ref('representative')
let request=0,sampleRequest=0
const selected=computed(()=>data.value?.topics[chosen.value])
const selectedGroup=computed(()=>data.value?.groups.find(group=>group.id===chosenGroup.value))
const selectedIds=computed(()=>selectedGroup.value?.message_ids[chosen.value]||selected.value?.message_ids||[])
const selectedSamples=computed(()=>selectedGroup.value||sampleMode.value!=='representative'?groupSamples.value:selected.value?.representatives||[])
const selectedScope=computed(()=>({topic_id:chosen.value,group_id:selectedGroup.value?.id??null,
  members:selectedGroup.value?.members||[],message_ids:selectedIds.value,sample_ids:selectedSamples.value.map(m=>m.id)}))
const maxCell=computed(()=>Math.max(1,...(data.value?.groups.flatMap(g=>g.counts)||[])))
const maxDay=computed(()=>Math.max(1,...(data.value?.daily.map(d=>d.counts.reduce((a,b)=>a+b,0))||[])))
useViewReadiness('topics',()=>!!data.value&&!busy.value&&!samplesBusy.value&&!error.value)
const assignmentById=computed(()=>new Map(data.value?.assignments.map(row=>[row.message_id,row])||[]))
function topWeights(id:string){return (assignmentById.value.get(id)?.weights||[]).map((weight,topic)=>({weight,topic})).sort((a,b)=>b.weight-a.weight||a.topic-b.topic).slice(0,2)}
function margin(id:string){const top=topWeights(id);return (top[0]?.weight||0)-(top[1]?.weight||0)}
function randomKey(id:string){let hash=42;for(const c of id)hash=Math.imul(hash^c.charCodeAt(0),16777619);return hash>>>0}
function rowShare(counts:number[],index:number){const total=counts.reduce((a,b)=>a+b,0);return total?counts[index]!/total:0}
function intensity(counts:number[],index:number){return metric.value==='share'?rowShare(counts,index):counts[index]!/maxCell.value}
async function load(){
 const current=++request
 ++sampleRequest;chosenGroup.value=null;groupSamples.value=[];samplesBusy.value=false
 busy.value=true;error.value=''
 try{const result=await get<TopicModelData>('topics',{...filters.value,topic_count:topicCount.value});if(current===request){data.value=result;if(chosen.value>=result.topics.length)chosen.value=0;await loadSamples()}}
 catch(e){if(current===request)error.value=(e as Error).message}
 finally{if(current===request)busy.value=false}
}
watch(()=>props.revision,load,{immediate:true})
watch(topicCount,()=>{selection.messageIds=[];load()})
async function selectTopic(index:number,groupId:number|null=null){
 chosen.value=index;chosenGroup.value=groupId
 const ids=[...selectedIds.value]
 selection.messageIds=ids
 if(ids[0])emit('evidence',ids[0])
 await loadSamples()
}
async function loadSamples(){
 const current=++sampleRequest
 groupSamples.value=[];samplesBusy.value=false;error.value=''
 const ids=[...selectedIds.value],index=chosen.value
 if(!data.value||!ids.length||(!selectedGroup.value&&sampleMode.value==='representative'))return
 const allowed=new Set(ids)
 const ranked=data.value!.assignments.filter(row=>allowed.has(row.message_id))
  .sort((a,b)=>(sampleMode.value==='boundary'?margin(a.message_id)-margin(b.message_id):sampleMode.value==='random'?randomKey(a.message_id)-randomKey(b.message_id):(b.weights[index]||0)-(a.weights[index]||0))||a.message_id.localeCompare(b.message_id))
  .slice(0,3).map(row=>row.message_id)
 samplesBusy.value=true
 try{
  const records=await get<Page<Message>>('messages',{...filters.value,ids:ranked.join(','),page_size:3})
  if(current===sampleRequest){
   const byId=new Map(records.items.map(message=>[message.id,message]))
   groupSamples.value=ranked.flatMap(id=>byId.has(id)?[byId.get(id)!]:[])
  }
 }catch(e){if(current===sampleRequest)error.value=(e as Error).message}
 finally{if(current===sampleRequest)samplesBusy.value=false}
}
watch(sampleMode,loadSamples)
function exportModel(){if(data.value&&!busy.value&&!samplesBusy.value&&!error.value)exportJson('mc3-topics.json',{...data.value,selected_scope:selectedScope.value,view_encoding:{metric:metric.value,denominator:'Each group row: unique related assigned messages; cross-group messages occur in both rows',sample_mode:sampleMode.value,sample_seed:sampleMode.value==='random'?42:null,ambiguity:'Top-two relative factor weights and their gap; not identity or classification probability'}})}
function chooseDay(day:string){selection.start=day;selection.end=day;selection.hour=null}
function barY(counts:number[],i:number){return 98-counts.slice(0,i+1).reduce((a,b)=>a+b,0)/maxDay.value*82}
</script>
<template><div class="topic-view" :aria-busy="busy"><div class="topic-toolbar"><label>主题数 <select aria-label="主题数量" v-model.number="topicCount"><option v-for="n in [4,6,8]" :key="n" :value="n">{{n}}</option></select></label><label>比较口径<select aria-label="主题矩阵度量" v-model="metric"><option value="count">消息数量</option><option value="share">群体内占比</option></select></label><span>{{data?.total||0}} 条通信<span v-if="data?.unassigned"> · {{data.unassigned}} 条未归类</span></span><button class="chip" :disabled="!data||busy||samplesBusy||!!error" @click="exportModel">导出模型与来源</button></div><div v-if="error" class="error" role="alert">{{error}}</div><div v-if="busy&&!data" class="empty">正在计算官方通信主题…</div><template v-if="data"><div class="topic-layout"><div><div class="topic-table scroll"><table data-testid="topic-matrix"><thead><tr><th>当前窗口群体</th><th v-for="t in data.topics" :key="t.id"><button :disabled="busy" @click="selectTopic(t.id)" :title="t.keywords.join(' / ')"><i :style="{background:topicPalette[t.id%topicPalette.length]}"></i>主题 {{t.id+1}}</button></th></tr></thead><tbody><tr v-for="g in data.groups" :key="g.id"><th :title="g.members.join('、')"><i :style="{background:palette[g.id%palette.length]}"></i>社区 {{g.id+1}}</th><td v-for="(count,index) in g.counts" :key="index"><button data-testid="topic-cell" :data-count="count" :data-share="rowShare(g.counts,index)" :disabled="!count||busy" :aria-label="`社区 ${g.id+1} 主题 ${index+1}，${count} 条通信`" :style="{background:count?`color-mix(in srgb, ${chartColors.blue} ${8+42*intensity(g.counts,index)}%, ${chartColors.panel})`:chartColors.surface,color:chartColors.ink}" @click="selectTopic(index,g.id)">{{metric==='share'?(rowShare(g.counts,index)*100).toFixed(1)+'%':count||'·'}}</button></td></tr></tbody></table></div><h3>每日主题通信量</h3><svg class="topic-timeline" viewBox="0 0 728 127" aria-label="每日主题分布"><g v-for="(day,index) in data.daily" :key="day.date" role="button" tabindex="0" :aria-label="`${day.date} 主题分布`" @click="chooseDay(day.date)" @keydown.enter.prevent="chooseDay(day.date)" class="topic-day"><rect :x="index*51+12" y="10" width="33" height="90" :fill="chartColors.surface"/><rect v-for="(count,i) in day.counts" :key="i" :x="index*51+12" :y="barY(day.counts,i)" width="33" :height="count/maxDay*82" :fill="topicPalette[i%topicPalette.length]" :opacity="chosen===i?1:.68"/><text :x="index*51+28" y="119" text-anchor="middle" font-size="10" :fill="chartColors.muted">{{day.date.slice(5)}}</text><title>{{day.date}} · {{day.counts.reduce((a,b)=>a+b,0)}} 条；{{day.counts.map((n,i)=>`主题 ${i+1}：${n} 条`).join("；")}}</title></g></svg></div><aside class="topic-description" v-if="selected"><div class="topic-name"><i :style="{background:topicPalette[chosen%topicPalette.length]}"></i><h3 data-testid="topic-selection-scope">{{selectedGroup?`社区 ${selectedGroup.id+1} · `:''}}主题 {{chosen+1}}</h3><span>{{selectedIds.length}} 条</span></div><label class="sample-control">原文抽样<select aria-label="原文抽样方式" v-model="sampleMode" :disabled="busy"><option value="representative">代表样本：本主题权重最高</option><option value="boundary">边界样本：前两项权重最接近</option><option value="random">固定种子抽样（42）</option></select></label><div class="keywords"><button v-for="word in selected.keywords" :key="word" class="chip" @click="selection.q=word">{{word}}</button></div><div v-if="samplesBusy" class="topic-note" role="status">正在读取所选群体的原文样本…</div><button v-for="m in selectedSamples" :key="m.id" class="topic-sample" @click="emit('evidence',m.id)" data-testid="topic-sample"><span class="mono">{{m.id}} ↗</span><small>{{m.sender}} → {{m.receiver}} · {{m.timestamp}}</small><div class="sample-weights" data-testid="topic-weight-gap"><span v-for="factor in topWeights(m.id)" :key="factor.topic" :style="{borderColor:topicPalette[factor.topic]}">主题 {{factor.topic+1}} · {{(factor.weight*100).toFixed(1)}}%</span><b>权重差 {{(margin(m.id)*100).toFixed(1)}} 个百分点</b></div><p>{{m.content}}</p></button><div v-if="!selectedIds.length" class="empty">当前范围没有此主题的消息。</div></aside></div><details class="model-note"><summary>计算口径与模型参数</summary><p>每日图以日期为横轴、消息数为纵轴，当前纵轴范围为 0—{{maxDay}} 条，颜色对应矩阵中的主题。矩阵列标题可查看关键词，行标题可查看群体成员。</p><p>消息按最大相对主题权重归类。群体内占比以本行已归类的唯一关联消息为分母；跨群通信分别计入双方群体。样本展示当前选择范围内最多 3 条原文，权重差反映前两项主题的接近程度。</p><p data-testid="topic-reliability">模型对样本与初始化敏感；主题编号随模型变化。关键词用于检索原文，权重表示相对因子贡献。</p><p>模型 {{data.model.version}} · seed {{data.model.seed}} · 主题数 {{data.model.topic_count}}。从全部 584 条官方通信移除实体名称与英语缩写碎片后拟合 TF-IDF + NMF，日期与主体筛选不重训。重构误差 {{data.model.reconstruction_error}}。</p><p class="mono">原始 ZIP SHA-256：{{data.model.source_sha256}}</p></details></template></div></template>
<style scoped>
.sample-control{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:12px 0;font-size:12px;color:var(--ink)}.sample-control select{max-width:100%;font-size:12px;padding:5px}.sample-weights{display:flex;flex-wrap:wrap;gap:5px;margin:7px 0;font-size:12px;color:var(--ink)}.sample-weights span{border-left:4px solid;padding-left:5px}.sample-weights b{font-weight:500}.topic-table thead i,.topic-name i{border-radius:1px!important;width:9px!important;height:9px!important}

.topic-view{padding:12px 14px}.topic-toolbar{display:flex;align-items:center;gap:12px;font-size:12px;color:var(--muted);flex-wrap:wrap}.topic-toolbar label{display:flex;gap:6px;align-items:center}.topic-toolbar select{padding:4px 8px}.topic-toolbar>.chip{margin-left:auto}.topic-note{font-size:12px;color:var(--muted);line-height:1.8;margin:10px 0}.topic-layout{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(230px,1fr);gap:20px}.topic-table table{width:100%;border-spacing:4px;table-layout:fixed;font-size:12px}.topic-table th{font-weight:500;color:var(--muted);text-align:center}.topic-table th:first-child{width:100px;text-align:left}.topic-table th>button{background:none;border:0;padding:6px 0;font-size:12px;width:100%}.topic-table small{display:block;font-size:10px;line-height:1.5;color:var(--muted);margin-top:5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.topic-table td{padding:0}.topic-table td button{height:42px;width:100%;border:0;border-radius:2px;font-variant-numeric:tabular-nums;font-size:14px}.topic-table td button:disabled{opacity:1;cursor:default}.topic-table i,.topic-name i{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px}.topic-layout h3{font-size:13px;font-weight:600;color:var(--muted);margin:15px 0 8px}.topic-timeline{width:100%;display:block}.topic-day{cursor:pointer}.topic-day:hover>rect:first-child{fill:var(--surface)}.topic-name{display:flex;align-items:center;gap:4px}.topic-name h3{margin:0}.topic-name>span{margin-left:auto;font-size:12px;color:var(--muted)}.keywords{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px}.keywords .chip{font-size:12px}.topic-sample{display:block;width:100%;text-align:left;border:0;border-top:1px solid var(--selected);border-radius:0;padding:12px 0;background:transparent}.topic-sample>span{font-size:12px;color:var(--blue)}.topic-sample small{display:block;color:var(--muted);font-size:10px;margin:5px 0}.topic-sample p{font-size:14px;line-height:1.8;margin:0;color:var(--muted)}.model-note{font-size:12px;color:var(--muted);line-height:1.8;margin-top:15px}.model-note summary{cursor:pointer}.model-note p{overflow-wrap:anywhere}@media(max-width:1450px){.topic-layout{grid-template-columns:1fr}.topic-description{border-top:1px solid var(--selected);padding-top:14px}}
</style>
