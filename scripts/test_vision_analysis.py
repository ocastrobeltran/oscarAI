import os
import json
import base64
import urllib.request

BASE_URL = "http://127.0.0.1:8080"

def main():
    print("=== TESTING GEMINI VISION MULTIMODAL ENDPOINT (/api/v1/documents/analyze-image) ===")

    # 1. Create a minimal 1x1 PNG pixel for multimodal testing
    tiny_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    png_bytes = base64.b64decode(tiny_png_base64)
    test_img_path = "test_architecture_diagram.png"
    with open(test_img_path, "wb") as f:
        f.write(png_bytes)

    # 2. Upload and analyze image via multipart/form-data POST
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    body = []
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"project_id\"\r\n\r\n1\r\n".encode("utf-8"))
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\nDiagrama de Arquitectura BioD Assistant\r\n".encode("utf-8"))
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\nDescribe la arquitectura general de los asistentes virtuales de BioD.\r\n".encode("utf-8"))
    body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{test_img_path}\"\r\nContent-Type: image/png\r\n\r\n".encode("utf-8"))
    body.append(png_bytes)
    body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    payload_bytes = b"".join(body)

    url = f"{BASE_URL}/api/v1/documents/analyze-image"
    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Agent-ID": "test-vision-analyzer"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("[OK] Vision Analysis Response:", res["status"])
        print("[OK] Document ID:", res["document"]["id"], "| Title:", res["document"]["title"])
        print("[OK] Chunks Vectorized in Qdrant:", res["total_chunks"])
        print("\n--- Gemini Vision Analysis Output Sample ---\n", res["analysis"][:300], "...")

    # Clean up test file
    if os.path.exists(test_img_path):
        os.remove(test_img_path)

    print("\n=== GEMINI VISION MULTIMODAL TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
