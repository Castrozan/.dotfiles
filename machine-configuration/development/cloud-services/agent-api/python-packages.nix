pythonPackages: with pythonPackages; [
  fastapi
  httpx
  jsonschema
  (scrapy.overridePythonAttrs (previousAttributes: {
    disabledTests = (previousAttributes.disabledTests or [ ]) ++ [
      "test_download_with_proxy_https_timeout"
    ];
  }))
  trafilatura
  uvicorn
  yt-dlp
]
