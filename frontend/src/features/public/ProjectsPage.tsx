import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { apiRequest } from '../../lib/api'
import type { ProjectPage } from '../../lib/types'
import { ProjectCard } from '../../components/ProjectCard'

export function ProjectsPage() {
  const [draft,setDraft]=useState({keyword:'',category:'',skill:''}); const [filters,setFilters]=useState(draft)
  const query = new URLSearchParams(Object.entries(filters).filter(([,v])=>v))
  const {data,isLoading,isError}=useQuery({queryKey:['projects',filters],queryFn:()=>apiRequest<ProjectPage>(`/api/v1/projects?${query}`)})
  function submit(e:FormEvent){e.preventDefault();setFilters({...draft})}
  return <section className="archive-page"><header className="page-heading"><div><p className="eyebrow">OPEN PROJECT INDEX</p><h1>项目大厅</h1></div><p>找到一件真实发生的事，把技能放进去，经受协作与交付的检验。</p></header><form className="filter-bar" onSubmit={submit}><label>关键词<input aria-label="关键词" value={draft.keyword} onChange={e=>setDraft({...draft,keyword:e.target.value})} placeholder="项目名称或说明"/></label><label>项目分类<input aria-label="项目分类" value={draft.category} onChange={e=>setDraft({...draft,category:e.target.value})} placeholder="如：校园文化"/></label><label>所需技能<input aria-label="所需技能" value={draft.skill} onChange={e=>setDraft({...draft,skill:e.target.value})} placeholder="如：摄影"/></label><button className="primary-button">筛选项目</button></form>{isLoading?<div className="page-state">正在翻阅项目档案…</div>:isError?<div className="page-state error">项目加载失败，请稍后重试</div>:data?.items.length?<div className="project-grid">{data.items.map((p,i)=><ProjectCard key={p.id} project={p} index={i+1}/>)}</div>:<div className="empty-state"><b>∅</b><h2>没有找到符合条件的项目</h2><p>换一个关键词或清空筛选条件再试。</p></div>}</section>
}
