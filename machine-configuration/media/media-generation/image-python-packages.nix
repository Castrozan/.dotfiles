pythonPackages: [
  (pythonPackages.openai.override {
    withAiohttp = false;
    withRealtime = false;
    withVoiceHelpers = false;
  })
  pythonPackages.replicate
  pythonPackages.pillow
]
