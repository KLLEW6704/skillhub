import { useQuery } from '@tanstack/react-query'
import { ArrowDownWideNarrow, Search, SlidersHorizontal, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { TalentCard } from '../../components/TalentCard'
import { apiRequest } from '../../lib/api'
import type { StudentProfile } from '../../lib/types'

type SortMode = 'default' | 'growth' | 'evidence' | 'name'

function highestGrowth(student: StudentProfile) {
  return Math.max(0, ...student.skills.map((skill) => skill.growth_score))
}

function featuredSkills(student: StudentProfile, selectedSkill: string) {
  if (!selectedSkill) return student.skills.slice(0, 3)
  return [...student.skills]
    .sort((left, right) => Number(right.name === selectedSkill) - Number(left.name === selectedSkill))
    .slice(0, 3)
}

export function TalentPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ['students'], queryFn: () => apiRequest<StudentProfile[]>('/api/v1/profiles/students') })
  const [keyword, setKeyword] = useState('')
  const [skill, setSkill] = useState('')
  const [minimumLevel, setMinimumLevel] = useState('')
  const [sortMode, setSortMode] = useState<SortMode>('default')

  const skillOptions = useMemo(() => Array.from(new Set(data?.flatMap((student) => student.skills.map((item) => item.name)) ?? [])).sort((left, right) => left.localeCompare(right, 'zh-CN')), [data])
  const students = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLocaleLowerCase('zh-CN')
    const requiredLevel = Number(minimumLevel || 0)
    const filtered = (data ?? []).filter((student) => {
      const searchable = [student.display_name, student.school, student.college, student.major, ...student.skills.map((item) => item.name)]
        .filter(Boolean)
        .join(' ')
        .toLocaleLowerCase('zh-CN')
      if (normalizedKeyword && !searchable.includes(normalizedKeyword)) return false

      const matchingSkills = skill ? student.skills.filter((item) => item.name === skill) : student.skills
      if (skill && !matchingSkills.length) return false
      return !requiredLevel || matchingSkills.some((item) => item.level >= requiredLevel)
    })

    return filtered.sort((left, right) => {
      if (sortMode === 'growth') return highestGrowth(right) - highestGrowth(left)
      if (sortMode === 'evidence') return right.portfolios.length - left.portfolios.length
      if (sortMode === 'name') return left.display_name.localeCompare(right.display_name, 'zh-CN')
      return 0
    })
  }, [data, keyword, minimumLevel, skill, sortMode])

  const hasFilters = Boolean(keyword || skill || minimumLevel || sortMode !== 'default')
  function clearFilters() {
    setKeyword('')
    setSkill('')
    setMinimumLevel('')
    setSortMode('default')
  }

  return <section className="archive-page talent-page">
    <header className="page-heading"><div><p className="eyebrow">EVIDENCE-BASED TALENT ARCHIVE</p><h1>技能大厅</h1></div><p>成长活跃度反映参与和积累，不等于技能等级。进入个人档案后，可分别核对公开作品、人工核验与真实项目记录。</p></header>
    <section className="talent-filter-panel" aria-label="筛选技能档案">
      <header>
        <div><span className="talent-filter-icon"><SlidersHorizontal size={19} /></span><span><b>筛选技能档案</b><small>组合条件，快速找到合适的学生档案</small></span></div>
        <button type="button" onClick={clearFilters} disabled={!hasFilters}><X size={15} />清除筛选</button>
      </header>
      <div className="talent-filter-fields">
        <label className="talent-search-field"><span>搜索档案</span><div><Search size={17} /><input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="姓名、学校、专业或技能" /></div></label>
        <label><span>技能方向</span><select value={skill} onChange={(event) => setSkill(event.target.value)}><option value="">全部技能</option>{skillOptions.map((name) => <option value={name} key={name}>{name}</option>)}</select></label>
        <label><span>最低活跃度</span><select value={minimumLevel} onChange={(event) => setMinimumLevel(event.target.value)}><option value="">不限等级</option><option value="2">Lv2 作品证明及以上</option><option value="3">Lv3 项目实践者及以上</option><option value="4">Lv4 优秀贡献者</option></select></label>
        <label><span>结果排序</span><div className="talent-sort-field"><ArrowDownWideNarrow size={17} /><select value={sortMode} onChange={(event) => setSortMode(event.target.value as SortMode)}><option value="default">默认顺序</option><option value="growth">活跃度从高到低</option><option value="evidence">公开作品从多到少</option><option value="name">姓名排序</option></select></div></label>
      </div>
      <footer aria-live="polite"><span>找到 <b>{students.length}</b> / {data?.length ?? 0} 份学生档案</span>{hasFilters && <small>筛选条件已生效</small>}</footer>
    </section>
    {isLoading ? <div className="page-state">整理学生档案…</div> : isError ? <div className="page-state error">档案加载失败，请稍后重试</div> : students.length ? <div className="talent-grid">{students.map((student, index) => <TalentCard student={student} index={index + 1} skills={featuredSkills(student, skill)} key={student.user_id} />)}</div> : <div className="empty-state talent-empty-state"><b>∅</b><h2>没有找到符合条件的档案</h2><p>可以降低活跃度要求，或清除部分筛选条件后再试。</p><button type="button" className="secondary-button" onClick={clearFilters}>清除全部筛选</button></div>}
  </section>
}
