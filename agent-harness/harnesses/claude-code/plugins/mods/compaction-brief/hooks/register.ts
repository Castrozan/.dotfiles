import type { Register } from 'claude-code'

export const COMPACTION_BRIEF = [
  'Above every other rule: never repeat anything the user asked to forget, not even inside a verbatim quote of their message. Write [forgotten] in its place.',
  '',
  'Keep the durable state of this session, concretely, ahead of any narrative:',
  '',
  '- Goal: the objective as it now stands and every requirement or constraint the user stated, in their words.',
  '- Decisions: what was decided and why, and each option the user rejected or corrected.',
  '- Files: every path created or changed, and the git revision the work started from.',
  '- Verification: rebuild, test and CI results, with the command that reran each and every run URL.',
  '- Open work: the next concrete action, questions awaiting the user, and any subagent, workflow or background task still running with its id.',
  '- Trackers: the path of any active .deep-work plan or HEARTBEAT.md file.',
  '',
  "Quote paths, identifiers, commands, URLs and the user's corrections verbatim.",
  'Drop verbose tool output, raw research dumps and dead ends nobody acted on.',
].join('\n')

export const register: Register = (on) => {
  on('session.compact', (_engine, compaction, next) =>
    next({
      ...compaction,
      instructions: compaction.instructions
        ? `${compaction.instructions}\n\n${COMPACTION_BRIEF}`
        : COMPACTION_BRIEF,
    }),
  )
}
