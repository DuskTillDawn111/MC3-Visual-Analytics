<script setup lang="ts">
import { onBeforeUnmount,onMounted,ref,watch } from 'vue'
import * as d3 from 'd3'
import type { GraphData,GraphEdge,GraphNode } from '../api'
import { palette } from '../store'
import { chartColors } from '../theme'
const props=defineProps<{data:GraphData;selected:string;selectedMessageIds?:string[]}>()
const emit=defineEmits<{entity:[id:string];evidence:[id:string];edge:[edge:GraphEdge]}>()
const el=ref<SVGSVGElement>(),host=ref<HTMLElement>()
const hovered=ref(''),bridges=ref(false),representation=ref('network'),allLabels=ref(false)
const positions=new Map<string,{x:number;y:number}>()
let maximumNodes=0,previousMode='' 
type N = GraphNode & d3.SimulationNodeDatum
type L = d3.SimulationLinkDatum<N> & {record:GraphEdge}
let observer:ResizeObserver|undefined
function edgePath(l:L){
  const s=l.source as N,t=l.target as N
  if(s.id===t.id)return `M${s.x!-6},${s.y!-5} C${s.x!-40},${s.y!-43} ${s.x!+40},${s.y!-43} ${s.x!+6},${s.y!-5}`
  return `M${s.x},${s.y} Q${(s.x!+t.x!)/2+(t.y!-s.y!)*.07},${(s.y!+t.y!)/2-(t.x!-s.x!)*.07} ${t.x},${t.y}`
}
function nodeSummary(n:N){return `${n.label} · ${n.communications} 条唯一消息（发出 ${n.sent} / 接收 ${n.received} / 自环 ${n.self_loops}）· 加权度 ${n.weighted_degree} · 中介中心性 ${n.centrality}`}
function render(){
  if(!el.value||!host.value)return
  const width=host.value.clientWidth,height=host.value.clientHeight
  if(!width||!height)return
  const svg=d3.select(el.value);svg.selectAll('*').remove();svg.on('.zoom',null);svg.attr('viewBox',`0 0 ${width} ${height}`).style('min-width',null).style('height','100%')
  svg.append('rect').attr('width','100%').attr('height','100%').attr('fill',representation.value==='matrix'?chartColors.panel:chartColors.canvas)
  const defs=svg.append('defs');defs.append('marker').attr('id','network-arrow').attr('viewBox','0 -3 6 6').attr('refX',16).attr('refY',0).attr('markerWidth',4).attr('markerHeight',4).attr('orient','auto').append('path').attr('d','M0,-3L6,0L0,3').attr('fill',chartColors.muted)
  const nodes:N[]=props.data.nodes.map(n=>({...n})), links:L[]=props.data.edges.filter(e=>!bridges.value||e.bridge).map(record=>({source:record.source,target:record.target,record}))
  if(!nodes.length)return
  const selectedMessages=new Set(props.selectedMessageIds||[])
  const selectedLink=(l:L)=>l.record.message_ids.some(id=>selectedMessages.has(id))
  const linkOpacity=(l:L)=>selectedMessages.size?(selectedLink(l)?.95:.05):(l.record.source===l.record.target?.8:l.record.bridge?.28:.5)
  nodes.sort((a,b)=>a.community-b.community||a.id.localeCompare(b.id))
  if(representation.value==='matrix'){
    const margin=132,cell=Math.max(14,Math.min(22,(width-margin-16)/nodes.length)),size=Math.max(width,margin+nodes.length*cell+16)
    svg.attr('viewBox',`0 0 ${size} ${size}`).style('min-width',`${size}px`).style('height',`${size}px`)
    const indexes=new Map(nodes.map((n,i)=>[n.id,i])),matrix=svg.append('g').attr('transform',`translate(${margin},${margin})`)
    nodes.forEach((n,i)=>{
      matrix.append('rect').attr('x',0).attr('y',i*cell).attr('width',nodes.length*cell).attr('height',cell).attr('fill',i%2?chartColors.surface:chartColors.panel)
      for(const column of [false,true])matrix.append('text').attr('transform',column?`translate(${i*cell+14},-8) rotate(-60)`:`translate(-8,${i*cell+15})`).attr('text-anchor',column?'start':'end').attr('font-size',12).attr('fill',palette[Math.max(0,n.community)%palette.length]!).attr('role','button').attr('tabindex',0).style('cursor','pointer').text(n.label).on('click',()=>{if(n.type==='Entity')emit('entity',n.id);else emit('evidence',n.id)}).on('keydown',(e:KeyboardEvent)=>{if(e.key==='Enter'){if(n.type==='Entity')emit('entity',n.id);else emit('evidence',n.id)}})
    })
    const max=d3.max(links,l=>l.record.weight)||1
    const cells=matrix.selectAll('g.matrix-cell').data(links).join('g').attr('class','matrix-cell').attr('data-testid','matrix-cell').attr('tabindex',0).attr('role','button').attr('aria-label',l=>`${l.record.source} 到 ${l.record.target}，${l.record.weight} 条记录`).style('cursor','pointer').on('click',(_,l)=>emit('edge',l.record)).on('keydown',(e:KeyboardEvent,l)=>{if(e.key==='Enter')emit('edge',l.record)})
    cells.append('rect').attr('x',l=>indexes.get(l.record.target)!*cell+1).attr('y',l=>indexes.get(l.record.source)!*cell+1).attr('width',cell-2).attr('height',cell-2).attr('rx',2).attr('fill',l=>d3.interpolateRgb(chartColors.heat[0]!,chartColors.blue)(.15+.85*Math.sqrt(l.record.weight/max))).attr('stroke',l=>l.record.is_inferred?chartColors.purple:'none').attr('stroke-dasharray',l=>l.record.is_inferred?'3 2':null)
    cells.append('text').attr('x',l=>indexes.get(l.record.target)!*cell+cell/2).attr('y',l=>indexes.get(l.record.source)!*cell+15).attr('text-anchor','middle').attr('font-size',11).attr('fill',l=>l.record.weight/max>.35?chartColors.panel:chartColors.ink).attr('pointer-events','none').text(l=>l.record.weight)
    cells.append('title').text(l=>`${l.record.source} → ${l.record.target} · ${l.record.weight} 条\n${l.record.message_ids.join(', ')}`)
    svg.append('text').attr('x',12).attr('y',22).attr('font-size',12).attr('fill',chartColors.muted).text('行：发送方 → 列：接收方')
    return
  }
  if(previousMode!==props.data.mode){positions.clear();maximumNodes=0;previousMode=props.data.mode}
  if(nodes.length>maximumNodes){
    maximumNodes=nodes.length
    if(props.data.mode==='communication'){
      const groups=[...new Set(nodes.map(n=>n.community))].sort((a,b)=>a-b)
      const centers=new Map(groups.map((id,i)=>{const angle=i/groups.length*Math.PI*2-Math.PI/2;return [id,{x:width*(.5+Math.cos(angle)*.27),y:height*(.5+Math.sin(angle)*.27)}]}))
      nodes.forEach((n,i)=>{const c=centers.get(n.community)!;n.x=c.x+Math.cos(i*2.4)*35;n.y=c.y+Math.sin(i*2.4)*35})
      const simulation=d3.forceSimulation(nodes).randomSource(d3.randomLcg(42))
        .force('link',d3.forceLink<N,L>(links).id(n=>n.id).distance(l=>l.record.bridge?120:44).strength(.12))
        .force('x',d3.forceX<N>(n=>centers.get(n.community)!.x).strength(.3))
        .force('y',d3.forceY<N>(n=>centers.get(n.community)!.y).strength(.3))
        .force('charge',d3.forceManyBody().strength(-75)).force('collision',d3.forceCollide<N>(17)).stop()
      simulation.tick(200)
      const xs=d3.extent(nodes,n=>n.x!) as [number,number],ys=d3.extent(nodes,n=>n.y!) as [number,number]
      const sx=d3.scaleLinear().domain(xs).range([.18,.82]),sy=d3.scaleLinear().domain(ys).range([.12,.88])
      nodes.forEach(n=>positions.set(n.id,{x:sx(n.x!),y:sy(n.y!)}))
    }
    else {
      const simulation=d3.forceSimulation(nodes).randomSource(d3.randomLcg(42)).force('link',d3.forceLink<N,L>(links).id(n=>n.id).distance(55)).force('charge',d3.forceManyBody().strength(-150)).force('center',d3.forceCenter(width/2,height/2)).stop();simulation.tick(140)
      const xs=d3.extent(nodes,n=>n.x!) as [number,number],ys=d3.extent(nodes,n=>n.y!) as [number,number]
      const sx=d3.scaleLinear().domain(xs[0]===xs[1]?[xs[0]-1,xs[1]+1]:xs).range([.12,.88]),sy=d3.scaleLinear().domain(ys[0]===ys[1]?[ys[0]-1,ys[1]+1]:ys).range([.12,.88])
      nodes.forEach(n=>positions.set(n.id,{x:sx(n.x!),y:sy(n.y!)}))
    }
  }
  nodes.forEach((n,i)=>{const p=positions.get(n.id)||{x:.5+Math.cos(i)*.25,y:.5+Math.sin(i)*.25};n.x=p.x*width;n.y=p.y*height})
  const byId=new Map(nodes.map(n=>[n.id,n]));links.forEach(l=>{l.source=byId.get(l.record.source)!;l.target=byId.get(l.record.target)!})
  const top=new Set([...nodes].sort((a,b)=>b.communications-a.communications).slice(0,8).map(n=>n.id))
  const group=svg.append('g')
  const edge=group.append('g').selectAll('path').data(links).join('path').attr('class','graph-edge').attr('data-testid','graph-edge').attr('role','button').attr('tabindex',0).attr('aria-label',l=>`${l.record.source} 到 ${l.record.target}，${l.record.weight} 条记录`).attr('d',edgePath).attr('fill','none').attr('stroke',l=>selectedMessages.size&&selectedLink(l)?chartColors.blue:l.record.bridge?chartColors.muted:chartColors.edge).attr('stroke-width',l=>Math.min(4,.8+Math.sqrt(l.record.weight)*.35)).attr('stroke-dasharray',l=>l.record.is_inferred?'4 4':'none').attr('opacity',linkOpacity).attr('marker-end','url(#network-arrow)').style('cursor','pointer').on('click',(_,l)=>emit('edge',l.record)).on('keydown',(e:KeyboardEvent,l)=>{if(e.key==='Enter')emit('edge',l.record)})
  edge.append('title').text(l=>`${l.record.source} → ${l.record.target}\n${l.record.type} · ${l.record.weight} 条\n${l.record.is_inferred?'文本推断':'直接通信记录'}`)
  const node=group.append('g').selectAll<SVGGElement,N>('g').data(nodes).join('g').attr('class','graph-node').attr('data-testid','graph-node').attr('data-id',n=>n.id).attr('role','button').attr('tabindex',0).attr('aria-label',n=>`${n.id}，${n.sub_type}`).attr('transform',n=>`translate(${n.x},${n.y})`).style('cursor','pointer')
  node.append('path').attr('d',n=>d3.symbol().type(n.type==='Event'?d3.symbolTriangle:n.type==='Relationship'?d3.symbolSquare:n.sub_type==='Vessel'?d3.symbolDiamond:n.sub_type==='Location'?d3.symbolSquare:n.sub_type==='Organization'?d3.symbolCross:n.sub_type==='Group'?d3.symbolTriangle:d3.symbolCircle).size((n.type==='Entity'?90+Math.sqrt(n.communications)*23:36)*(width>=900?1.25:1))()!).attr('fill',n=>n.community>=0?palette[n.community%palette.length]!:(n.type==='Event'?chartColors.muted:n.type==='Relationship'?chartColors.purple:chartColors.blue)).attr('stroke',n=>n.id===props.selected?chartColors.gold:chartColors.panel).attr('stroke-width',n=>n.id===props.selected?3:1.5).attr('opacity',.94)
  const labels=node.append('text').text(n=>n.type==='Entity'?n.label:'').attr('pointer-events','none').attr('text-anchor',n=>n.x!<width/2?'end':'start').attr('x',n=>n.x!<width/2?-13:13).attr('dy',4).attr('fill',chartColors.ink).attr('font-size',width>=900?14:12).attr('paint-order','stroke').attr('stroke',chartColors.canvas).attr('stroke-width',3).attr('font-weight',500).attr('opacity',n=>allLabels.value||top.has(n.id)||n.id===props.selected?1:0)
  node.append('title').text(nodeSummary)
  function activate(n:N){if(n.type==='Entity')emit('entity',n.id);else emit('evidence',n.id)}
  node.on('click',(_,n)=>activate(n)).on('keydown',(e:KeyboardEvent,n)=>{if(e.key==='Enter')activate(n)}).on('mouseenter',(_,n)=>{hovered.value=nodeSummary(n);const adjacent=new Set([n.id,...links.filter(l=>(l.source as N).id===n.id||(l.target as N).id===n.id).flatMap(l=>[(l.source as N).id,(l.target as N).id])]);node.attr('opacity',o=>adjacent.has(o.id)?1:.2);labels.attr('opacity',o=>adjacent.has(o.id)?1:0);edge.attr('opacity',l=>(l.source as N).id===n.id||(l.target as N).id===n.id?1:.08)}).on('mouseleave',()=>{hovered.value='';node.attr('opacity',1);labels.attr('opacity',n=>allLabels.value||top.has(n.id)||n.id===props.selected?1:0);edge.attr('opacity',linkOpacity)})
  node.call(d3.drag<SVGGElement,N>().on('drag',function(event,n){n.x=event.x;n.y=event.y;positions.set(n.id,{x:n.x!/width,y:n.y!/height});d3.select(this).attr('transform',`translate(${n.x},${n.y})`);edge.attr('d',edgePath)}))
  const zoom=d3.zoom<SVGSVGElement,unknown>().scaleExtent([.35,5]).on('zoom',event=>group.attr('transform',event.transform))
  svg.call(zoom)
  const bounds=group.node()!.getBBox()
  const scale=Math.max(.35,Math.min(2.5,(width-80)/Math.max(1,bounds.width),(height-64)/Math.max(1,bounds.height)))
  svg.call(zoom.transform,d3.zoomIdentity.translate(width/2,height/2).scale(scale).translate(-bounds.x-bounds.width/2,-bounds.y-bounds.height/2))
}
onMounted(()=>{observer=new ResizeObserver(render);observer.observe(host.value!);render()})
watch([()=>props.data,()=>props.selected,()=>props.selectedMessageIds,bridges,representation,allLabels],render)
onBeforeUnmount(()=>observer?.disconnect())
</script>
<template><div class="network-view"><div class="network-legend"><div class="representation"><button :class="{active:representation==='network'}" @click="representation='network'">关系图</button><button :class="{active:representation==='matrix'}" @click="representation='matrix'" data-testid="matrix-mode">邻接矩阵</button></div><label v-if="representation==='network'"><input type="checkbox" v-model="allLabels">全部标签</label><label v-if="data.mode==='communication'"><input type="checkbox" v-model="bridges">跨群联系</label></div><div class="network-stage scroll" ref="host"><svg ref="el" aria-label="交互关系网络"></svg><div v-if="!data.nodes.length" class="network-empty">当前筛选下没有连接，试试重置筛选。</div></div><div v-if="hovered||representation==='matrix'" class="hover-info" aria-live="polite">{{hovered||'行：发送方 → 列：接收方；点击色块查原文。'}}</div><div class="community-legend"><span v-for="c in data.communities" :key="c.id" :title="c.members.join('、')"><i :style="{background:palette[c.id%palette.length]}"></i>社区 {{c.id+1}} · {{c.size}}</span><span v-if="data.mode==='original'">▲ 事件 / ■ 关系 · 虚线为推断</span></div><p v-if="data.truncated" class="panel-note">当前显示最多 180 个节点，选择主体可查看其邻域。</p><details class="communities"><summary>图例与群体明细</summary><div class="shape-legend"><span>● 人物</span><span>◆ 船舶</span><span>■ 地点</span><span>✚ 组织</span><span>▲ 群体</span></div><p class="panel-note">滚轮缩放视图，拖动节点或画布调整位置。</p><p class="panel-note">{{data.mode==='communication'?'节点大小＝当前日期/小时/检索范围内的唯一消息数；环形边＝自环（计一次），发出/接收不含自环，加权度另列。箭头＝发送方向；颜色＝当前窗口社区，筛选后可能重算。中心性表示桥接作用；位置仅为图布局。社区与边类型控件筛选本图。':'原始异构图：实线为直接记录，虚线为文本推断。'}}</p><div v-for="c in data.communities" :key="c.id">社区 {{c.id+1}} · 内部 {{c.internal_communications}} / 跨群发出 {{c.sent_external}} / 接入 {{c.received_external}}<br>关联总量 {{c.communications}} · 代表成员 {{c.representatives.join('、')}}<br>高频词（非主题标签）：{{c.topics.join(' / ')}}<br><span>{{c.members.join('、')}}</span></div></details></div></template>
<style scoped>
.network-view{position:relative}.network-legend{display:flex;gap:18px;align-items:center;padding:0 18px 10px;font-size:12px;color:var(--muted);flex-wrap:wrap}.network-legend label{display:flex;align-items:center;gap:6px;min-height:40px;cursor:pointer}.network-legend input{margin:0;min-height:0}.representation{display:flex;gap:2px;margin-right:auto;padding:3px;background:var(--surface);border:1px solid var(--border);border-radius:8px}.representation button{font-size:12px;padding:4px 12px;border:0;border-radius:5px;background:transparent;color:var(--muted);min-height:32px}.representation button.active{background:var(--panel);color:var(--ink);box-shadow:0 1px 3px #00000012}
.network-stage{height:clamp(400px,calc(100dvh - 490px),760px);position:relative;background:var(--canvas);border-block:1px solid var(--canvas-line)}svg{display:block;width:100%;height:100%;touch-action:none}.network-empty{position:absolute;inset:0;display:grid;place-content:center;color:var(--muted);font-size:13px;pointer-events:none}.hover-info{position:absolute;left:16px;right:16px;bottom:85px;padding:10px 14px;font-size:12px;color:var(--ink);background:var(--panel);box-shadow:0 2px 12px #0000000d;border:1px solid var(--border);border-radius:6px;line-height:1.6;pointer-events:none}
.community-legend{display:flex;gap:16px;padding:14px 18px 8px;font-size:12px;color:var(--muted);flex-wrap:wrap}.community-legend span{display:flex;gap:6px;align-items:center}.community-legend i{width:8px;height:8px;border-radius:50%;display:inline-block}.communities{padding:0 18px 12px;font-size:12px;color:var(--muted)}.communities summary{cursor:pointer;min-height:32px;display:list-item;align-content:center}.communities div{padding:12px 0;line-height:1.8;border-bottom:1px solid var(--border)}.communities .shape-legend{display:flex;gap:16px;flex-wrap:wrap}.communities span{color:var(--muted)}
@media(max-width:900px){.network-legend{padding:0 14px 10px;gap:8px 14px}.network-legend label{min-height:44px}.representation button{min-height:38px}.network-stage{height:440px}.hover-info{bottom:110px}.community-legend{padding-inline:14px;gap:10px}.communities{padding-inline:14px}}
</style>
