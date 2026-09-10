import { NavLink, Outlet } from 'react-router-dom'

export function ReviewerLayout() {
  return <div className="workspace"><aside><p className="eyebrow">HUMAN REVIEW DESK</p><h2>评审工作台</h2><NavLink end to="/reviewer">待复核证据</NavLink><p className="aside-note">AI 只提供辅助初评。人工决定必须基于作品、答辩与量表证据。</p></aside><div className="workspace-main"><Outlet /></div></div>
}
