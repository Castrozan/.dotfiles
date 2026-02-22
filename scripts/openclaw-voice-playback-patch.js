// Patch OpenClaw's reply-B2UJINPw.js to pipe TTS audio into Discord voice sessions.
// Applied as a post-install step; idempotent (checks for sentinel comment).

const fs = require('fs');
const path = require('path');

const replyFilePath = path.join(
  process.env.HOME,
  '.local/share/openclaw-npm/lib/node_modules/openclaw/dist/reply-B2UJINPw.js'
);

const patchSentinel = '/* VOICE_PLAYBACK_PATCH_APPLIED */';

let sourceContent = fs.readFileSync(replyFilePath, 'utf8');

if (sourceContent.includes(patchSentinel)) {
  console.log('voice-playback patch: already applied');
  process.exit(0);
}

// PATCH 1: Expose voiceManagerRef globally when created
const voiceManagerRefCreationPattern = 'const voiceManagerRef = { current: null };';
const voiceManagerRefReplacement = `const voiceManagerRef = { current: null };
  ${patchSentinel}
  if (!globalThis.__openclawVoiceManagers) globalThis.__openclawVoiceManagers = {};
  const __patchAccountId = account.accountId;`;

if (!sourceContent.includes(voiceManagerRefCreationPattern)) {
  console.error('voice-playback patch: cannot find voiceManagerRef pattern');
  process.exit(1);
}
sourceContent = sourceContent.replace(voiceManagerRefCreationPattern, voiceManagerRefReplacement);

// PATCH 2: Register voice manager globally when assigned
const voiceManagerAssignPattern = 'voiceManagerRef.current = voiceManager;';
const voiceManagerAssignReplacement = `voiceManagerRef.current = voiceManager;
			globalThis.__openclawVoiceManagers[__patchAccountId] = voiceManager;`;

sourceContent = sourceContent.replace(voiceManagerAssignPattern, voiceManagerAssignReplacement);

// PATCH 3: Hook into sendVoiceMessageDiscord to also play through voice session
// Find the point after sendVoiceMessageDiscord is called in deliverDiscordReply
const voiceMessageSendPattern = `await sendVoiceMessageDiscord(params.target, firstMedia, {
				token: params.token,
				rest: params.rest,
				accountId: params.accountId,
				replyTo
			});`;

const voiceMessageSendReplacement = `await sendVoiceMessageDiscord(params.target, firstMedia, {
				token: params.token,
				rest: params.rest,
				accountId: params.accountId,
				replyTo
			});
			try {
				const __vm = globalThis.__openclawVoiceManagers?.[params.accountId];
				if (__vm && firstMedia) {
					for (const [, __entry] of __vm.sessions) {
						__vm.enqueuePlayback(__entry, async () => {
							const __res = createAudioResource(firstMedia);
							__entry.player.play(__res);
							await entersState(__entry.player, AudioPlayerStatus.Playing, 5000).catch(() => {});
							await entersState(__entry.player, AudioPlayerStatus.Idle, 120000).catch(() => {});
						});
					}
				}
			} catch {}`;

if (!sourceContent.includes('await sendVoiceMessageDiscord(params.target, firstMedia,')) {
  console.error('voice-playback patch: cannot find sendVoiceMessageDiscord pattern');
  process.exit(1);
}
sourceContent = sourceContent.replace(voiceMessageSendPattern, voiceMessageSendReplacement);

fs.writeFileSync(replyFilePath, sourceContent, 'utf8');
console.log('voice-playback patch: applied successfully');
