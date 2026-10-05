export interface MobileUpdateInfo { currentVersion: string; latestVersion: string; apkUrl: string; releaseUrl: string }

const owner = 'nova-io-vn'
const repository = 'personal-manager'

function versionParts(value: string) { return value.replace(/^v/, '').split('.').map((part) => Number.parseInt(part, 10) || 0) }
function isNewer(latest: string, current: string) {
  const a = versionParts(latest); const b = versionParts(current)
  for (let index = 0; index < 3; index += 1) if ((a[index] ?? 0) !== (b[index] ?? 0)) return (a[index] ?? 0) > (b[index] ?? 0)
  return false
}

export async function checkMobileUpdate(): Promise<MobileUpdateInfo | null> {
  const currentVersion = import.meta.env.VITE_APP_VERSION || '0.1.0'
  const response = await fetch(`https://api.github.com/repos/${owner}/${repository}/releases/latest`, { headers: { Accept: 'application/vnd.github+json' } })
  if (!response.ok) throw new Error('Release check failed')
  const release = await response.json() as { tag_name?: string; html_url?: string; assets?: Array<{ name?: string; browser_download_url?: string }> }
  const latestVersion = String(release.tag_name ?? '').replace(/^v/, '')
  const apk = release.assets?.find((asset) => asset.name?.toLowerCase().endsWith('.apk'))
  if (!latestVersion || !apk?.browser_download_url || !isNewer(latestVersion, currentVersion)) return null
  return { currentVersion, latestVersion, apkUrl: apk.browser_download_url, releaseUrl: String(release.html_url ?? apk.browser_download_url) }
}
