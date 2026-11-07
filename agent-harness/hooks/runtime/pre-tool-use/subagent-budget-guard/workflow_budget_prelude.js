"workflow budget guard start";
const workflowBudgetGuardOriginalAgent = globalThis.agent;
const workflowBudgetGuardAgentCeiling = __AGENT_CEILING__;
const workflowBudgetGuardOutputTokenCeiling = __OUTPUT_TOKEN_CEILING__;
const workflowBudgetGuardOutputTokenBaseline = budget.spent();
let workflowBudgetGuardAgentCount = 0;
const workflowBudgetGuardStop = (ceilingDescription) => {
  const stopMessage = `workflow budget guard refused agent ${workflowBudgetGuardAgentCount + 1}: ${ceilingDescription}`;
  log(stopMessage);
  throw new Error(stopMessage);
};
const agent = (...agentArguments) => {
  if (workflowBudgetGuardAgentCount >= workflowBudgetGuardAgentCeiling) {
    workflowBudgetGuardStop(
      `the ${workflowBudgetGuardAgentCeiling}-agent ceiling is reached`,
    );
  }
  const outputTokensSpent =
    budget.spent() - workflowBudgetGuardOutputTokenBaseline;
  if (outputTokensSpent >= workflowBudgetGuardOutputTokenCeiling) {
    workflowBudgetGuardStop(
      `${outputTokensSpent} of ${workflowBudgetGuardOutputTokenCeiling} output tokens are spent`,
    );
  }
  workflowBudgetGuardAgentCount += 1;
  return workflowBudgetGuardOriginalAgent(...agentArguments);
};
("workflow budget guard end");
