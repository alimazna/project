// Brand configuration — rebrand the product without touching components.
// Override with VITE_APP_NAME in the build environment (see web/.env.example).
const APP_NAME = import.meta.env.VITE_APP_NAME || 'TrendCipher'

// Split the name so the logo can highlight a part, e.g. "Trend<em>Cipher</em>".
export function brandParts(): [string, string] {
  const parts = APP_NAME.split(/(?<=[a-z])(?=[A-Z])/)
  if (parts.length >= 2) return [parts[0], parts.slice(1).join('')]
  return [APP_NAME, '']
}

export function appName(): string {
  return APP_NAME
}

export function setDocumentTitle() {
  document.title = `${APP_NAME} — explainable crypto market intelligence`
}