// 开发期走 vite proxy(/api -> 8000),生产期由 FastAPI 同源直发
const BASE = import.meta.env.DEV ? '/api' : ''

async function request(method, path, body) {
  const opts = { method, headers: {} }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const r = await fetch(BASE + path, opts)
  if (!r.ok) {
    let detail = r.statusText
    const raw = await r.text().catch(() => '')
    if (raw) {
      try {
        const j = JSON.parse(raw)
        detail = j.detail || j.message || raw
      } catch {
        detail = raw
      }
    }
    throw new Error(`${r.status} ${detail}`)
  }
  return r.json()
}

export const api = {
  health: () => request('GET', '/health'),
  createProfile: (data) => request('POST', '/profile', data),
  listConcepts: (subject = '管综数学') =>
    request('GET', `/concepts?subject=${encodeURIComponent(subject)}`),
  sampleQuestions: (n = 5) => request('GET', `/questions/sample?n=${n}`),
  diagnose: (data) => request('POST', '/diagnose', data),
  getPath: (sid) => request('GET', `/path/${sid}`),
  postInteraction: (data) => request('POST', '/interaction', data),
}
