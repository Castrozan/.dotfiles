"workflow budget guard start";
const workflowBudgetGuardOriginalAgent = globalThis.agent;
const workflowBudgetGuardAgentCeiling = __AGENT_CEILING__;
const workflowBudgetGuardWeightedOutputTokenCeiling = __OUTPUT_TOKEN_CEILING__;
const workflowBudgetGuardOutputPriceWeightByModelFamily = {
  haiku: 0.025,
  sonnet: 0.5,
  opus: 1,
};
const workflowBudgetGuardInFlightWeights = [];
let workflowBudgetGuardLastSpent = budget.spent();
let workflowBudgetGuardWeightedOutputTokensSpent = 0;
let workflowBudgetGuardAgentCount = 0;
const workflowBudgetGuardOutputPriceWeight = (agentOptions) => {
  const modelName = String(agentOptions?.model ?? "").toLowerCase();
  const modelFamily = Object.keys(
    workflowBudgetGuardOutputPriceWeightByModelFamily,
  ).find((family) => modelName.includes(family));
  return modelFamily
    ? workflowBudgetGuardOutputPriceWeightByModelFamily[modelFamily]
    : 1;
};
const workflowBudgetGuardSettleSpending = () => {
  const currentSpent = budget.spent();
  const outputTokensSinceLastSettle =
    currentSpent - workflowBudgetGuardLastSpent;
  workflowBudgetGuardLastSpent = currentSpent;
  const inFlightCount = workflowBudgetGuardInFlightWeights.length;
  const averageInFlightWeight = inFlightCount
    ? workflowBudgetGuardInFlightWeights.reduce(
        (total, weight) => total + weight,
        0,
      ) / inFlightCount
    : 1;
  workflowBudgetGuardWeightedOutputTokensSpent +=
    outputTokensSinceLastSettle * averageInFlightWeight;
};
const workflowBudgetGuardStop = (ceilingDescription) => {
  const stopMessage = `workflow budget guard refused agent ${workflowBudgetGuardAgentCount + 1}: ${ceilingDescription}`;
  log(stopMessage);
  throw new Error(stopMessage);
};
// biome-ignore lint/correctness/noUnusedVariables: this binding shadows the runtime agent for the workflow script appended after the prelude
const agent = (...agentArguments) => {
  workflowBudgetGuardSettleSpending();
  if (workflowBudgetGuardAgentCount >= workflowBudgetGuardAgentCeiling) {
    workflowBudgetGuardStop(
      `the ${workflowBudgetGuardAgentCeiling}-agent ceiling is reached`,
    );
  }
  if (
    workflowBudgetGuardWeightedOutputTokensSpent >=
    workflowBudgetGuardWeightedOutputTokenCeiling
  ) {
    workflowBudgetGuardStop(
      `${Math.round(workflowBudgetGuardWeightedOutputTokensSpent)} of ${workflowBudgetGuardWeightedOutputTokenCeiling} Opus-equivalent output tokens are spent`,
    );
  }
  workflowBudgetGuardAgentCount += 1;
  const agentWeight = workflowBudgetGuardOutputPriceWeight(agentArguments[1]);
  workflowBudgetGuardInFlightWeights.push(agentWeight);
  const releaseAgent = () => {
    workflowBudgetGuardSettleSpending();
    workflowBudgetGuardInFlightWeights.splice(
      workflowBudgetGuardInFlightWeights.indexOf(agentWeight),
      1,
    );
  };
  return workflowBudgetGuardOriginalAgent(...agentArguments).then(
    (agentResult) => {
      releaseAgent();
      return agentResult;
    },
    (agentFailure) => {
      releaseAgent();
      throw agentFailure;
    },
  );
};
("workflow budget guard end");
