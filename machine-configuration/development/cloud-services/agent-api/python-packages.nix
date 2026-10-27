pythonPackages: with pythonPackages; [
  fastapi
  httpx
  jsonschema
  (scrapy.overridePythonAttrs { doCheck = false; })
  trafilatura
  uvicorn
  yt-dlp
]
