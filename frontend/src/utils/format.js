export function formatMoney(amount) {
  if (amount === null || amount === undefined) {
    return '-'
  }
  return '₹' + Number(amount).toLocaleString('en-IN')
}

export function formatDate(value) {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatPercent(probability) {
  if (probability === null || probability === undefined) {
    return '-'
  }
  return Math.round(probability * 100) + '%'
}
