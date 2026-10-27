pythonPackages: with pythonPackages; [
  fastapi
  httpx
  jsonschema
  (scrapy.overridePythonAttrs {
    doCheck = false;
    pythonImportsCheck = [ ];
  })
  (trafilatura.overridePythonAttrs {
    doCheck = false;
    pythonImportsCheck = [ ];
  })
  uvicorn
  yt-dlp
]
