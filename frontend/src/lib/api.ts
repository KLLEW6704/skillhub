const TOKEN_KEY = 'skillhub_token'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !(init.body instanceof FormData) && !(init.body instanceof URLSearchParams)) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    let message = '请求失败，请稍后重试'
    try {
      const payload = await response.json() as { detail?: string | Array<{ msg: string }> }
      if (typeof payload.detail === 'string') message = payload.detail
      else if (Array.isArray(payload.detail)) message = payload.detail.map((item) => item.msg).join('；')
    } catch { /* response is not JSON */ }
    if (response.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.dispatchEvent(new Event('skillhub:unauthorized'))
    }
    throw new ApiError(response.status, message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function apiBlob(path: string): Promise<Blob> {
  const headers = new Headers()
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(path, { headers })
  if (!response.ok) throw new ApiError(response.status, '无法读取作品文件')
  return response.blob()
}

export { TOKEN_KEY }
