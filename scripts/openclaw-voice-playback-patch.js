// Patch OpenClaw's reply-B2UJINPw.js to pipe TTS audio into Discord voice sessions.
// Applied as a post-install step; idempotent (checks for sentinel comment).

const fs = require('fs');
const path = require('path');

const replyFilePath = path.join(
  process.env.HOME,
  '.local/share/openclaw-npm/lib/node_modules/openclaw/dist/reply-B2UJINPw.js'
);

const patchSentinel = '/* VOICE_PLAYBACK_PATCH_V2 */';

let sourceContent = fs.readFileSync(replyFilePath, 'utf8');

if (sourceContent.includes(patchSentinel)) {
  console.log('voice-playback patch v2: already applied');
  process.exit(0);
}

// Remove v1 sentinel if present
sourceContent = sourceContent.replace(/\/\* VOICE_PLAYBACK_PATCH_APPLIED \*\/\n/g, '');

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
if (sourceContent.includes('globalThis.__openclawVoiceManagers[__patchAccountId] = voiceManager;')) {
  // Already patched from v1
} else {
  const voiceManagerAssignReplacement = `voiceManagerRef.current = voiceManager;
			globalThis.__openclawVoiceManagers[__patchAccountId] = voiceManager;`;
  sourceContent = sourceContent.replace(voiceManagerAssignPattern, voiceManagerAssignReplacement);
}

// PATCH 3: Hook into deliverDiscordReply — after ALL media sends, pipe audio to VC
// The key insight: TTS audio on Discord goes through the regular media path (not audioAsVoice)
// We hook the end of the for-of loop in deliverDiscordReply

// Helper function to inject — plays media through active voice sessions
const voicePlaybackHelper = `
function __playMediaInVoiceSessions(accountId, mediaPath) {
	try {
		const __vm = globalThis.__openclawVoiceManagers?.[accountId];
		if (!__vm || !mediaPath || !__vm.sessions?.size) return;
		for (const [, __entry] of __vm.sessions) {
			__vm.enqueuePlayback(__entry, async () => {
				const __res = createAudioResource(mediaPath);
				__entry.player.play(__res);
				await entersState(__entry.player, AudioPlayerStatus.Playing, 5000).catch(() => {});
				await entersState(__entry.player, AudioPlayerStatus.Idle, 120000).catch(() => {});
			});
		}
	} catch {}
}`;

// Inject helper after the createAudioPlayer import line
const importMarker = 'import { AudioPlayerStatus, EndBehaviorType, VoiceConnectionStatus, createAudioPlayer, createAudioResource, entersState, joinVoiceChannel } from "@discordjs/voice";';
if (!sourceContent.includes(importMarker)) {
  console.error('voice-playback patch: cannot find @discordjs/voice import');
  process.exit(1);
}
if (!sourceContent.includes('__playMediaInVoiceSessions')) {
  sourceContent = sourceContent.replace(importMarker, importMarker + '\n' + voicePlaybackHelper);
}

// PATCH 4: Hook sendVoiceMessageDiscord path (audioAsVoice=true, e.g. Telegram-style)
const voiceMessagePattern = `await sendVoiceMessageDiscord(params.target, firstMedia, {
				token: params.token,
				rest: params.rest,
				accountId: params.accountId,
				replyTo
			});`;

if (sourceContent.includes(voiceMessagePattern) && !sourceContent.includes('__playMediaInVoiceSessions(params.accountId, firstMedia);')) {
  sourceContent = sourceContent.replace(voiceMessagePattern,
    voiceMessagePattern + '\n\t\t\t__playMediaInVoiceSessions(params.accountId, firstMedia);');
}

// PATCH 5: Hook regular media send path (the one Discord actually uses for TTS)
// This is the path: sendMessageDiscord(params.target, text, { mediaUrl: firstMedia, ... })
const regularMediaPattern = `await sendMessageDiscord(params.target, text, {
			token: params.token,
			rest: params.rest,
			mediaUrl: firstMedia,
			accountId: params.accountId,
			replyTo
		});`;

if (sourceContent.includes(regularMediaPattern) && !sourceContent.includes('/* VOICE_MEDIA_HOOK */')) {
  sourceContent = sourceContent.replace(regularMediaPattern,
    regularMediaPattern + '\n\t\t/* VOICE_MEDIA_HOOK */\n\t\tif (firstMedia) __playMediaInVoiceSessions(params.accountId, firstMedia);');
}

// PATCH 6: Also hook the text-only chunk sends (for TTS text without separate audio)
// When TTS is on but sends text+audio as mediaUrl, it goes through the media path above.
// But also hook sendDiscordChunkWithFallback for text-only TTS piping
// Actually, text chunks don't have audio — skip this.

fs.writeFileSync(replyFilePath, sourceContent, 'utf8');
console.log('voice-playback patch v2: applied successfully');
