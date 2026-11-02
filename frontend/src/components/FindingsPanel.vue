<script setup lang="ts">
import { onMounted,ref } from 'vue'
import { get } from '../api'
import type { Finding,FindingContext } from '../report'
defineProps<{open:boolean}>()
const emit=defineEmits<{close:[];select:[context:FindingContext];evidence:[id:string]}>()
const data=ref<{source_sha256:string;analysis_version:string;scope:string;items:Finding[]}>(),error=ref(''),chosen=ref('rhythm')
async function load(){error.value='';try{data.value=await get('findings')}catch(e){error.value=(e as Error).message}}
function restore(finding:Finding){if(data.value)emit('select',{finding,source_sha256:data.value.source_sha256,analysis_version:data.value.analysis_version,scope:data.value.scope})}
onMounted(load)
</script>
<template>
  <section v-if="open" class="findings-drawer" aria-label="分析发现与依据" data-testid="findings-panel">
    <header><h2>分析发现与依据</h2><button aria-label="关闭分析发现" @click="emit('close')">关闭 ×</button></header>
    <p v-if="error" class="error">{{error}} <button @click="load">重试</button></p>
    <nav v-if="data" aria-label="分析发现选择"><button v-for="item in data.items" :key="item.id" :class="{active:chosen===item.id}" @click="chosen=item.id" :data-testid="`finding-${item.id}`">{{item.title}}</button></nav>
    <article v-for="item in data?.items.filter(item=>item.id===chosen)" :key="item.id">
      <h3>{{item.title}}</h3><p>{{item.claim}}</p>
      <details v-if="item.reasoning_steps?.length"><summary>展开分析过程 · 从观察到判断</summary><ol><li v-for="step in item.reasoning_steps" :key="step.observation"><strong>{{step.observation}}</strong><p>{{step.interpretation}}</p><div><button v-for="id in step.message_ids" :key="id" class="link mono" style="margin-right:10px" @click="emit('evidence',id)">{{id}}</button></div></li></ol></details>
      <dl v-if="item.id==='rhythm'"><dt>第一周 / 第二周的通信时间中位数</dt><dd>{{item.statistics.first_week_median}} / {{item.statistics.second_week_median}}（各 7 天）</dd></dl>
      <div class="counter"><strong>关联记录</strong><p>{{item.competing_explanation}}</p></div>
      <div class="limits"><strong>分析口径</strong><p>{{item.limitation}}</p></div>
      <ol v-if="item.stages.length" class="claim-timeline" aria-label="Nadia 行动与通信依据">
        <li v-for="stage in item.stages" :key="stage.date"><time>{{stage.date}}</time><strong>{{stage.claim}}</strong><div><span>支持：</span><button v-for="id in stage.support_ids" :key="id" class="link mono" @click="emit('evidence',id)">{{id}}</button></div><div v-if="stage.counter_ids.length"><span>竞争解释：</span><button v-for="id in stage.counter_ids" :key="id" class="link mono" @click="emit('evidence',id)">{{id}}</button></div></li>
      </ol>
      <button class="restore" data-testid="restore-finding" @click="restore(item)">恢复分析状态并检查 {{item.evidence.length}} 条原文 ↗</button>
      <details><summary>查看全部引用原文与出处</summary><p class="source-note">分析版本 {{data?.analysis_version}} · 原始来源 SHA-256：{{data?.source_sha256}}</p><article v-for="message in item.evidence" :key="message.id" class="source-record"><button class="link mono" @click="emit('evidence',message.id)">{{message.id}}</button><small>{{message.timestamp}} · {{message.sender}} → {{message.receiver}}</small><p>{{message.content}}</p></article></details>
      
    </article>
  </section>
</template>
<style scoped>
.findings-drawer{position:absolute;z-index:20;top:64px;right:20px;width:min(710px,calc(100% - 40px));max-height:calc(100vh - 90px);overflow:auto;background:var(--panel);border:1px solid var(--border);border-radius:6px;box-shadow:0 12px 36px #26334230;padding:18px 22px;color:var(--ink);font-size:14px;line-height:1.75}.findings-drawer header{display:flex;justify-content:space-between;align-items:center;gap:12px}.findings-drawer h2{font-size:18px;margin:0}.findings-drawer h3{font-size:17px}.source-note{font-size:14px;color:var(--muted)}.source-note{overflow-wrap:anywhere}.findings-drawer nav{display:grid;grid-template-columns:1fr 1fr;gap:8px}.findings-drawer nav button{text-align:left;font-size:13px}.findings-drawer nav .active{border-color:var(--blue);background:var(--surface)}.counter,.limits{padding:10px 13px;margin:12px 0;background:var(--surface);border-left:3px solid #8b7a4e}.counter p,.limits p{margin:4px 0}.limits{border-color:var(--muted)}.claim-timeline{list-style:none;padding:0 0 0 12px}.claim-timeline li{padding:0 0 16px 16px;border-left:2px solid var(--border)}.claim-timeline time{font-size:12px;display:block;color:var(--muted)}.claim-timeline strong{display:block}.claim-timeline li>div{display:flex;flex-wrap:wrap;gap:4px 8px;font-size:12px}.claim-timeline li>p{margin:5px 0;font-size:13px}.restore{background:var(--surface);margin:4px 0 15px;color:var(--blue)}.source-record{border-top:1px solid var(--selected);padding:12px 0}.source-record small{display:block;font-size:12px}.source-record p{margin:5px 0}.findings-drawer summary{cursor:pointer}.findings-drawer dd{margin-left:0;font-weight:600}@media(max-width:700px){.findings-drawer nav{grid-template-columns:1fr}}
</style>
