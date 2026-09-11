import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Eye, GraduationCap, Image, Save, ShieldCheck, UserRound } from 'lucide-react'
import { type FormEvent, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../../lib/api'
import type { EditableStudentProfile } from '../../lib/types'

function clean(value: FormDataEntryValue | null) {
  const text = String(value ?? '').trim()
  return text || null
}

function ProfileEditor({ initialProfile }: { initialProfile: EditableStudentProfile }) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState(initialProfile)
  const [saved, setSaved] = useState(false)
  const update = useMutation({
    mutationFn: (payload: unknown) => apiRequest<EditableStudentProfile>('/api/v1/profiles/me', { method: 'PATCH', body: JSON.stringify(payload) }),
    onSuccess: (profile) => {
      setDraft(profile)
      setSaved(true)
      queryClient.setQueryData(['my-profile'], profile)
      queryClient.invalidateQueries({ queryKey: ['home-students'] })
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['student'] })
    },
  })
  const fields = [draft.display_name, draft.avatar_url, draft.school, draft.college, draft.major, draft.grade, draft.bio]
  const completeness = Math.round(fields.filter((value) => value?.trim()).length / fields.length * 100)
  const affiliation = useMemo(() => [draft.school, draft.college, draft.major, draft.grade].filter(Boolean).join(' · '), [draft.school, draft.college, draft.major, draft.grade])

  function change(field: keyof EditableStudentProfile, value: string) {
    setSaved(false)
    setDraft((current) => ({ ...current, [field]: value }))
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    update.mutate({
      display_name: clean(data.get('display_name')),
      avatar_url: clean(data.get('avatar_url')),
      school: clean(data.get('school')),
      college: clean(data.get('college')),
      major: clean(data.get('major')),
      grade: clean(data.get('grade')),
      bio: clean(data.get('bio')),
    })
  }

  return <section className="workspace-page profile-editor-page">
    <div className="profile-editor-heading"><div><p className="eyebrow">PERSONAL ARCHIVE</p><h1>个人资料</h1><p>完善公开身份与学业背景，让项目方更容易理解你的方向。作品、技能和核验结果仍在各自页面单独管理。</p></div><div className="profile-completeness"><span>资料完整度</span><strong>{completeness}%</strong><div aria-label={`资料完整度 ${completeness}%`}><i style={{ width: `${completeness}%` }} /></div></div></div>
    <div className="profile-editor-layout">
      <form className="profile-editor-form" onSubmit={submit}>
        <section className="profile-form-section">
          <header><span><UserRound size={20} /></span><div><b>公开身份</b><small>这些信息会出现在技能大厅与个人公开档案。</small></div></header>
          <div className="profile-form-grid">
            <label>展示姓名<input name="display_name" value={draft.display_name} maxLength={80} required onChange={(event) => change('display_name', event.target.value)} placeholder="例如：林同学" /></label>
            <label>头像图片地址（选填）<input name="avatar_url" type="url" value={draft.avatar_url ?? ''} maxLength={500} onChange={(event) => change('avatar_url', event.target.value)} placeholder="https://example.com/avatar.jpg" /><small>当前版本支持填写公开图片地址。</small></label>
          </div>
        </section>
        <section className="profile-form-section">
          <header><span><GraduationCap size={20} /></span><div><b>学业信息</b><small>帮助项目方了解你所在的学习环境与专业方向。</small></div></header>
          <div className="profile-form-grid">
            <label>学校<input name="school" value={draft.school ?? ''} maxLength={120} onChange={(event) => change('school', event.target.value)} placeholder="例如：南方大学" /></label>
            <label>学院<input name="college" value={draft.college ?? ''} maxLength={120} onChange={(event) => change('college', event.target.value)} placeholder="例如：设计学院" /></label>
            <label>专业<input name="major" value={draft.major ?? ''} maxLength={120} onChange={(event) => change('major', event.target.value)} placeholder="例如：视觉传达设计" /></label>
            <label>年级<input name="grade" value={draft.grade ?? ''} maxLength={30} onChange={(event) => change('grade', event.target.value)} placeholder="例如：大三" /></label>
          </div>
        </section>
        <section className="profile-form-section">
          <header><span><Image size={20} /></span><div><b>个人介绍</b><small>可以说明你的兴趣方向、常用工具、合作方式或期待参与的项目。</small></div></header>
          <label className="profile-bio-field">个人介绍<textarea name="bio" value={draft.bio ?? ''} maxLength={2000} onChange={(event) => change('bio', event.target.value)} placeholder="例如：关注校园视觉与信息设计，熟悉 Figma、Illustrator，期待参与品牌与活动传播项目。" /><small>{draft.bio?.length ?? 0} / 2000</small></label>
        </section>
        <footer className="profile-form-actions"><p><ShieldCheck size={16} />邮箱与登录账号不会显示在公开档案中。</p><button className="primary-button" disabled={update.isPending}><Save size={17} />{update.isPending ? '保存中…' : '保存个人资料'}</button></footer>
        {update.isError && <p className="form-error" role="alert">{update.error instanceof Error ? update.error.message : '资料保存失败，请稍后重试'}</p>}
        {saved && <p className="profile-save-success" role="status">个人资料已保存，公开档案将使用最新信息。</p>}
      </form>
      <aside className="profile-live-preview" aria-label="公开档案预览">
        <header><span>PUBLIC PROFILE PREVIEW</span><b>公开档案预览</b></header>
        <div className="profile-avatar-preview"><strong>{draft.display_name.trim().slice(0, 1) || '档'}</strong>{draft.avatar_url && <img key={draft.avatar_url} src={draft.avatar_url} alt="头像预览" onError={(event) => { event.currentTarget.hidden = true }} />}</div>
        <p className="eyebrow">STUDENT ARCHIVE</p>
        <h2>{draft.display_name || '你的展示姓名'}</h2>
        <p className="profile-preview-affiliation">{affiliation || '学校 · 学院 · 专业 · 年级'}</p>
        <blockquote>{draft.bio || '个人介绍会显示在这里。可以简单说明你的方向、工具与期待参与的项目。'}</blockquote>
        <small>这里只预览个人资料；公开作品与核验记录会在档案下方继续展示。</small>
        <Link className="profile-full-preview-link" to={`/talent/${draft.user_id}`}><Eye size={16} />查看完整公开档案</Link>
      </aside>
    </div>
  </section>
}

export function ProfileEditPage() {
  const profile = useQuery({ queryKey: ['my-profile'], queryFn: () => apiRequest<EditableStudentProfile>('/api/v1/profiles/me') })
  if (profile.isLoading) return <div className="page-state">正在读取个人资料…</div>
  if (profile.isError || !profile.data) return <div className="page-state error">个人资料暂时无法读取，请稍后重试。</div>
  return <ProfileEditor initialProfile={profile.data} />
}
