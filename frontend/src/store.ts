import { computed, reactive, ref, watch, watchSyncEffect, onBeforeUnmount } from 'vue'
import type { Params } from './api'

export const selection = reactive({ start:'2040-10-01', end:'2040-10-14', entity:'', hour:null as number|null, q:'', messageIds:[] as string[] })
export const filters = computed<Params>(() => ({start:selection.start,end:selection.end,entity_id:selection.entity || undefined,hour:selection.hour,q:selection.q}))
export { communityPalette as palette, topicPalette } from './theme'
export const viewReadiness = reactive<Record<string,boolean>>({})
export function useViewReadiness(name:string,ready:()=>boolean){
  watchSyncEffect(()=>{viewReadiness[name]=ready()})
  onBeforeUnmount(()=>{delete viewReadiness[name]})
}
export function reset() { Object.assign(selection,{start:'2040-10-01',end:'2040-10-14',entity:'',hour:null,q:'',messageIds:[]}) }
export function selectEntity(id:string) { selection.entity=id; selection.messageIds=[] }
export function selectCell(day:string,hour:number) { selection.start=day; selection.end=day; selection.hour=hour; selection.messageIds=[] }
export function exportJson(name:string,value:unknown) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}))
  const link=document.createElement('a'); link.href=url;link.download=name;link.click();URL.revokeObjectURL(url)
}

type Scope = {start:string;end:string;entity:string;hour:number|null;q:string}
const scopeSnapshot=():Scope=>({start:selection.start,end:selection.end,entity:selection.entity,hour:selection.hour,q:selection.q})
const history=ref<Scope[]>([])
let restoring=false
watch(scopeSnapshot,(_,previous)=>{if(!restoring){history.value.push(previous);if(history.value.length>30)history.value.shift()}})
export const canUndo=computed(()=>history.value.length>0)
export async function undoFilters(){const previous=history.value.pop();if(!previous)return;restoring=true;Object.assign(selection,previous,{messageIds:[]});await Promise.resolve();restoring=false}
