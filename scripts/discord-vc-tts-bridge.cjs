#!/usr/bin/env node
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');
const homeDirectory = os.homedir();

const { Client, GatewayIntentBits } = require('discord.js');
const { joinVoiceChannel, entersState, VoiceConnectionStatus, createAudioPlayer, createAudioResource, AudioPlayerStatus } = require('@discordjs/voice');

const discordBotToken = fs.readFileSync(path.join(homeDirectory, '.openclaw/secrets/discord-bot-token-robson'), 'utf8').trim();
const guildId = process.env.DISCORD_VC_GUILD_ID || '998625197802410094';
const textChannelId = process.env.DISCORD_VC_TEXT_CHANNEL_ID || '998625197802410097';
const voiceChannelId = process.env.DISCORD_VC_CHANNEL_ID || '998625197802410098';
const ttsVoiceName = process.env.DISCORD_VC_TTS_VOICE || 'pt-BR-AntonioNeural';

const discordClient = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent] });
const audioPlayer = createAudioPlayer();
let voiceConnection = null;
let playbackQueuePromise = Promise.resolve();

function appendPlaybackTask(task) {
  playbackQueuePromise = playbackQueuePromise.then(task).catch(() => {});
}

function synthesizeSpeechToFile(textToSpeak, outputFilePath) {
  return new Promise((resolve, reject) => {
    const edgeTtsProcess = spawn('edge-tts', ['--voice', ttsVoiceName, '--text', textToSpeak, '--write-media', outputFilePath], { stdio: 'ignore' });
    edgeTtsProcess.on('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`edge-tts failed with code ${code}`));
    });
    edgeTtsProcess.on('error', reject);
  });
}

async function playTextInVoiceChannel(textToSpeak) {
  if (!voiceConnection || !textToSpeak.trim()) return;
  const tempAudioPath = path.join('/tmp', `discord-vc-bridge-${Date.now()}-${Math.random().toString(36).slice(2)}.mp3`);
  await synthesizeSpeechToFile(textToSpeak.slice(0, 1200), tempAudioPath);
  const audioResource = createAudioResource(tempAudioPath);
  audioPlayer.play(audioResource);
  await entersState(audioPlayer, AudioPlayerStatus.Playing, 5000).catch(() => {});
  await entersState(audioPlayer, AudioPlayerStatus.Idle, 120000).catch(() => {});
  fs.unlink(tempAudioPath, () => {});
}

async function connectBotToVoiceChannel() {
  const guild = await discordClient.guilds.fetch(guildId);
  const voiceAdapterCreator = guild.voiceAdapterCreator;
  voiceConnection = joinVoiceChannel({
    guildId,
    channelId: voiceChannelId,
    adapterCreator: voiceAdapterCreator,
    selfMute: false,
    selfDeaf: true
  });
  await entersState(voiceConnection, VoiceConnectionStatus.Ready, 20000);
  voiceConnection.subscribe(audioPlayer);
  voiceConnection.on(VoiceConnectionStatus.Disconnected, async () => {
    try {
      await Promise.race([
        entersState(voiceConnection, VoiceConnectionStatus.Signalling, 5000),
        entersState(voiceConnection, VoiceConnectionStatus.Connecting, 5000)
      ]);
    } catch {
      try {
        voiceConnection.destroy();
      } catch {}
      setTimeout(() => {
        connectBotToVoiceChannel().catch(() => {});
      }, 3000);
    }
  });
}

discordClient.once('ready', async () => {
  await connectBotToVoiceChannel();
});

discordClient.on('messageCreate', (discordMessage) => {
  if (!discordClient.user) return;
  if (discordMessage.author.id !== discordClient.user.id) return;
  if (discordMessage.guildId !== guildId) return;
  if (discordMessage.channelId !== textChannelId) return;
  const textContent = (discordMessage.content || '').trim();
  if (!textContent) return;
  appendPlaybackTask(async () => {
    await playTextInVoiceChannel(textContent);
  });
});

discordClient.login(discordBotToken).catch(() => process.exit(1));
