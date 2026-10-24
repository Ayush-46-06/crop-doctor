import base64
import json
import os
from io import BytesIO

from dotenv import load_dotenv
from groq import Groq
from PIL import Image, UnidentifiedImageError
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

load_dotenv()
MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_CROPS = {"tomato", "potato", "maize", "rice", "wheat", "other"}

@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok", "service": "Crop Doctor AI API"})

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def analyze_crop(request):
    uploaded = request.FILES.get("image")
    crop = (request.data.get("crop") or "other").strip().lower()
    if not uploaded:
        return Response({"error": "Please upload a crop leaf image."}, status=status.HTTP_400_BAD_REQUEST)
    if uploaded.size > MAX_IMAGE_BYTES:
        return Response({"error": "Image too large. Upload an image smaller than 8 MB."}, status=status.HTTP_400_BAD_REQUEST)
    if crop not in ALLOWED_CROPS:
        crop = "other"
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    if not api_key:
        return Response({"error": "GROQ_API_KEY is missing. Add it to .env and restart Django."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        raw = uploaded.read()
        image = Image.open(BytesIO(raw))
        image.verify()
        image = Image.open(BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        return Response({"error": "Unreadable image. Please upload a JPG or PNG photo."}, status=status.HTTP_400_BAD_REQUEST)

    image.thumbnail((1400, 1400))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85, optimize=True)
    data_url = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    prompt = f'''
You are the visual assistant for a school-level educational project named Crop Doctor AI.
The user selected crop: {crop}.
Carefully inspect the attached image. If it is not a clear plant/crop leaf image, say so.
Describe visible evidence separately from guesses. Give only a POSSIBLE issue, never a guaranteed diagnosis.
Do not invent a disease when evidence is weak. Do not prescribe pesticides, chemical dosages, or treatments.
Return ONLY valid JSON with these keys:
{{
 "image_assessment": "one short sentence on whether image is suitable",
 "health_status": "Appears healthy" OR "Possible disease signs" OR "Unclear image",
 "possible_issue": "possible disease/symptom or Not determined",
 "observed_symptoms": ["visible observation"],
 "prevention_tips": ["general non-chemical prevention tip"],
 "next_steps": ["safe next step", "when to consult an agricultural expert"],
 "explanation": "simple explanation suitable for a Class 7 student"
}}
Keep concise. Do not provide a confidence percentage. If uncertain, clearly say the image is insufficient.
'''
    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_completion_tokens=900,
        )
        content = (completion.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3].strip()
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                raise
        for key in ["image_assessment", "health_status", "possible_issue", "explanation"]:
            result.setdefault(key, "Not available")
        for key in ["observed_symptoms", "prevention_tips", "next_steps"]:
            if not isinstance(result.get(key), list):
                result[key] = [str(result.get(key, "Not available"))]
        result["model_used"] = model
        result["disclaimer"] = "Preliminary educational observation only, not a confirmed diagnosis. Ask a local agricultural expert before taking treatment action."
        return Response(result)
    except json.JSONDecodeError:
        return Response({"error": "The AI returned an unreadable response. Try a clearer leaf photo."}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as exc:
        print(f"Groq analysis error: {type(exc).__name__}: {exc}")
        return Response({"error": "AI analysis failed. Check API key, model access, internet, and Groq usage limits."}, status=status.HTTP_502_BAD_GATEWAY)
