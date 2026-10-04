export function formatVnd(value: number) { return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(Math.round(value))} ₫` }
