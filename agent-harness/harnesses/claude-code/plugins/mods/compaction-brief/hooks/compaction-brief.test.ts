import { test, expect } from 'claude-code/testing'
import type { On, SessionCompactInput } from 'claude-code'
import { COMPACTION_BRIEF } from './register'

const compactionOf = (overrides: Partial<SessionCompactInput> = {}): SessionCompactInput => ({
  trigger: 'auto',
  messages: [{ role: 'assistant' as const, text: 'earlier work', toolUses: [] }],
  ...overrides,
})

const recordInstructionsReachingTheSummarizer = (on: On) => {
  const received: { instructions?: string } = {}
  on('session.compact', (_engine, compaction) => {
    received.instructions = compaction.instructions
    return { messages: [{ role: 'assistant' as const, text: 'summary', toolUses: [] }] }
  })
  return received
}

for (const trigger of ['auto', 'manual', 'plugin', 'precompute'] as const) {
  test(`a ${trigger} compaction without instructions receives exactly the brief`, async ($, on) => {
    const received = recordInstructionsReachingTheSummarizer(on)

    await $.session.compact(compactionOf({ trigger }))

    expect(received.instructions).toBe(COMPACTION_BRIEF)
  })
}

test('the text typed after /compact leads and the brief follows it', async ($, on) => {
  const received = recordInstructionsReachingTheSummarizer(on)

  await $.session.compact(
    compactionOf({ trigger: 'manual', instructions: 'focus on the parser rewrite' }),
  )

  expect(received.instructions).toBe(`focus on the parser rewrite\n\n${COMPACTION_BRIEF}`)
})

test('a compaction another hook skips stays skipped', async ($, on) => {
  on('session.compact', () => ({ skip: 'nothing to compact' }))

  const result = await $.session.compact(compactionOf())

  expect(result).toEqual({ skip: 'nothing to compact' })
})
