import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);

const HINDSIGHT_DAEMON_BASE_URL = 'http://127.0.0.1:9077';

export function escapeShellArg(arg) {
    return arg.replace(/'/g, "'\\''");
}
export class HindsightClient {
    bankId = 'default';
    llmProvider;
    llmApiKey;
    llmModel;
    embedVersion;
    embedPackagePath;
    constructor(llmProvider, llmApiKey, llmModel, embedVersion = 'latest', embedPackagePath) {
        this.llmProvider = llmProvider;
        this.llmApiKey = llmApiKey;
        this.llmModel = llmModel;
        this.embedVersion = embedVersion || 'latest';
        this.embedPackagePath = embedPackagePath;
    }
    getEmbedCommandPrefix() {
        if (this.embedPackagePath) {
            return `uv run --directory ${this.embedPackagePath} hindsight-embed`;
        }
        else {
            const embedPackage = this.embedVersion ? `hindsight-embed@${this.embedVersion}` : 'hindsight-embed@latest';
            return `uvx ${embedPackage}`;
        }
    }
    setBankId(bankId) {
        this.bankId = bankId;
    }
    async setBankMission(mission) {
        if (!mission || mission.trim().length === 0) {
            return;
        }
        const escapedMission = escapeShellArg(mission);
        const embedCmd = this.getEmbedCommandPrefix();
        const cmd = `${embedCmd} --profile openclaw bank mission ${this.bankId} '${escapedMission}'`;
        try {
            const { stdout } = await execAsync(cmd);
            console.log(`[Hindsight] Bank mission set: ${stdout.trim()}`);
        }
        catch (error) {
            console.warn(`[Hindsight] Could not set bank mission (bank may not exist yet): ${error}`);
        }
    }
    async retain(request) {
        const docId = request.document_id || 'conversation';
        const retainUrl = `${HINDSIGHT_DAEMON_BASE_URL}/v1/default/banks/${encodeURIComponent(this.bankId)}/memories`;
        const retainPayload = {
            items: [{ content: request.content, document_id: docId }],
            async: true,
        };
        try {
            const response = await fetch(retainUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(retainPayload),
            });
            if (!response.ok) {
                const errorBody = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorBody}`);
            }
            const result = await response.json();
            console.log(`[Hindsight] Retained via HTTP API (async): ${JSON.stringify(result).substring(0, 200)}`);
            return {
                message: 'Memory queued for background processing',
                document_id: docId,
                memory_unit_ids: [],
            };
        }
        catch (error) {
            throw new Error(`Failed to retain memory: ${error}`);
        }
    }
    async recall(request) {
        const query = escapeShellArg(request.query);
        const maxTokens = request.max_tokens || 1024;
        const embedCmd = this.getEmbedCommandPrefix();
        const cmd = `${embedCmd} --profile openclaw memory recall ${this.bankId} '${query}' --output json --max-tokens ${maxTokens}`;
        try {
            const { stdout } = await execAsync(cmd);
            const response = JSON.parse(stdout);
            const results = response.results || [];
            return {
                results: results.map((r) => ({
                    content: r.text || r.content || '',
                    score: 1.0,
                    metadata: {
                        document_id: r.document_id,
                        chunk_id: r.chunk_id,
                        ...r.metadata,
                    },
                })),
            };
        }
        catch (error) {
            throw new Error(`Failed to recall memories: ${error}`);
        }
    }
}
