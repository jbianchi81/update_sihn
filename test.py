from update_sihn.update_sihn import downloadParseAndUploadAll
import json

result = downloadParseAndUploadAll()

f = open("/tmp/sihn_upload_response.json","w")
json.dump(result, f)
f.close()