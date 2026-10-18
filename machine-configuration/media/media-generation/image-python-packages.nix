pythonPackages: [
  (pythonPackages.openai.override {
    withAiohttp = false;
    withRealtime = false;
    withVoiceHelpers = false;
  })
  pythonPackages.pillow
]
