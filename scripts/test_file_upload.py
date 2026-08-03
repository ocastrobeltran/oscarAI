import os
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8080"

def main():
    print("=== TESTING DIRECT FILE UPLOAD ENDPOINT (/api/v1/documents/upload) ===")
    
    # 1. Create a temporary test Markdown file
    test_md_path = "test_upload_doc.md"
    with open(test_md_path, "w", encoding="utf-8") as f:
        f.write("# Manual de Pruebas de Subida Directa\n\nEste es un documento de prueba subido mediante la API de Oscar AI.\nContiene especificaciones sobre el sistema de ingesta y fragmentacion automatica.")

    # 2. Upload file via multipart/form-data POST
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(test_md_path, "rb") as f:
        file_bytes = f.read()

    body = []
    # project_id form field
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"project_id\"\r\n\r\n1\r\n".encode("utf-8"))
    # chunk_size form field
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chunk_size\"\r\n\r\n250\r\n".encode("utf-8"))
    # file form field
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{test_md_path}\"\r\nContent-Type: text/markdown\r\n\r\n".encode("utf-8"))
    body.append(file_bytes)
    body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    payload_bytes = b"".join(body)

    url = f"{BASE_URL}/api/v1/documents/upload"
    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Agent-ID": "test-file-uploader"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("[OK] Upload Response:", res["status"])
        print("[OK] Document ID:", res["document"]["id"], "| Title:", res["document"]["title"])
        print("[OK] Chunks Generated & Vectorized in Qdrant:", res["total_chunks"])

    # Clean up test file
    if os.path.exists(test_md_path):
        os.remove(test_md_path)

    print("=== DIRECT FILE UPLOAD TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
