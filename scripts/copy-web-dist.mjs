import { cpSync, existsSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const source = join(process.cwd(), 'web', 'out')
const target = join(process.cwd(), 'web_dist')
const cleanupTargets = [
  join(process.cwd(), 'web', 'node_modules'),
  join(process.cwd(), 'web', '.next'),
  join(process.cwd(), 'web', 'out'),
  join(process.cwd(), '.npm-cache'),
]

if (!existsSync(source)) {
  throw new Error(`Next export output not found: ${source}`)
}

rmSync(target, { force: true, recursive: true })
cpSync(source, target, { recursive: true })

if (process.env.VERCEL) {
  for (const item of cleanupTargets) {
    rmSync(item, { force: true, recursive: true })
  }
}
