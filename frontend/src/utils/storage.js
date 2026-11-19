const PREFIX = 'libreserve:draft'
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000

function store(kind) {
  try {
    return kind === 'session' ? window.sessionStorage : window.localStorage
  } catch {
    return null
  }
}

export function draftKey(owner, form) {
  return `${PREFIX}:${owner ?? 'guest'}:${form}`
}

export function readDraft(key, kind = 'local') {
  const storage = store(kind)
  if (!storage) return null
  try {
    const saved = JSON.parse(storage.getItem(key))
    if (!saved || typeof saved.values !== 'object') return null
    if (Date.now() - saved.savedAt > MAX_AGE_MS) {
      storage.removeItem(key)
      return null
    }
    return saved.values
  } catch {
    return null
  }
}

export function writeDraft(key, values, kind = 'local') {
  const storage = store(kind)
  if (!storage) return
  try {
    storage.setItem(key, JSON.stringify({ savedAt: Date.now(), values }))
  } catch {
  }
}

export function removeDraft(key, kind = 'local') {
  store(kind)?.removeItem(key)
}

export function clearDraftsFor(owner) {
  const prefix = `${PREFIX}:${owner}:`
  ;['local', 'session'].forEach((kind) => {
    const storage = store(kind)
    if (!storage) return
    Object.keys(storage)
      .filter((key) => key.startsWith(prefix))
      .forEach((key) => storage.removeItem(key))
  })
}
