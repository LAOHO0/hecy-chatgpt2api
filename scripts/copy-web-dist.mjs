import { cpSync, existsSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const source = join(process.cwd(), 'web', 'out')
const target = join(process.cwd(), 'web_dist')

if (!existsSync(source)) {
  throw new Error(`Next export output not found: ${source}`)
}

rmSync(target, { force: true, recursive: true })
cpSync(source, target, { recursive: true })

