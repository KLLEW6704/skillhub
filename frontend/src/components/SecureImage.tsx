import { useEffect, useState } from 'react'
import { apiBlob } from '../lib/api'

export function SecureImage({ src, alt }: { src: string; alt: string }) {
  const [result, setResult] = useState<{ src: string; url: string | null; failed: boolean }>({
    src: '', url: null, failed: false,
  })
  useEffect(() => {
    let active = true
    let objectUrl = ''
    apiBlob(src).then((blob) => {
      if (!active) return
      objectUrl = URL.createObjectURL(blob)
      setResult({ src, url: objectUrl, failed: false })
    }).catch(() => active && setResult({ src, url: null, failed: true }))
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [src])
  if (result.src === src && result.failed) return <div className="evidence-preview is-unavailable">作品预览暂不可用</div>
  if (result.src !== src || !result.url) return <div className="evidence-preview is-loading">读取作品预览…</div>
  return <img className="evidence-preview" src={result.url} alt={alt} />
}
