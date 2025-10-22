export function extractErrorMessage(
  error: any,
  fallback: string
): string {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item?.msg) return item.msg
        return JSON.stringify(item)
      })
      .filter(Boolean)
    if (messages.length > 0) {
      return messages.join(' • ')
    }
  } else if (typeof detail === 'string') {
    return detail
  } else if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string') {
      return detail.message
    }
    return JSON.stringify(detail)
  }

  if (error?.message && typeof error.message === 'string') {
    return error.message
  }

  return fallback
}
