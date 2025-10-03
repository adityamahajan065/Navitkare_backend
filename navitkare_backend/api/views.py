from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
import cv2, pytesseract, numpy as np, re, tensorflow as tf
from .models import Medicine
from .serializers import RegisterSerializer, MedicineSerializer

try:
    COUNTERFEIT_MODEL = tf.keras.models.load_model('path/to/your/model.h5')
except (ImportError, IOError):
    print("Warning: TensorFlow model not found or failed to load. AI check will be skipped.")
    COUNTERFEIT_MODEL = None
    
def check_blockchain_provenance(uid):
    print(f"Checking blockchain for UID: {uid}")
    return True

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class VerifyMedicineView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _extract_text_from_image(self, image_file):
        try:
            image_bytes = image_file.read()
            np_arr = np.frombuffer(image_bytes, np.uint8)
            img_cv = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            gray_img = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            denoised_img = cv2.medianBlur(gray_img, 3)
            extracted_text = pytesseract.image_to_string(denoised_img)
            return extracted_text, img_cv
        except Exception as e:
            print(f"Error during OCR processing: {e}")
            return None, None

    def _parse_uid_from_text(self, text):
        match = re.search(r'\b[A-Z0-9]{10,20}\b', text, re.IGNORECASE)
        return match.group(0) if match else None

    def post(self, request, *args, **kwargs):
        image_file = request.data.get('medicine_image')
        uid_from_scanner = request.data.get('uid')
        if not image_file and not uid_from_scanner:
            return Response({"error": "Please provide an image or a UID."}, status=400)
        
        extracted_text, img_cv, uid_from_ocr = "", None, None
        if image_file:
            extracted_text, img_cv = self._extract_text_from_image(image_file)
            if extracted_text is None:
                return Response({"error": "Could not process the uploaded image."}, status=500)
            uid_from_ocr = self._parse_uid_from_text(extracted_text)

        final_uid = uid_from_scanner or uid_from_ocr
        if not final_uid:
            return Response({"status": "Error", "reason": "Could not find a valid UID.", "details": {"extracted_text": extracted_text}}, status=400)

        try:
            medicine_record = Medicine.objects.get(uid__iexact=final_uid)
        except Medicine.DoesNotExist:
            return Response({"status": "Counterfeit", "reason": "UID not found in the official database."})

        if not check_blockchain_provenance(final_uid):
            return Response({"status": "Counterfeit", "reason": "Blockchain provenance check failed."})

        ai_warning = None
        if COUNTERFEIT_MODEL and img_cv is not None:
            try:
                img_resized = cv2.resize(img_cv, (224, 224))
                img_normalized = img_resized / 255.0
                img_batch = np.expand_dims(img_normalized, axis=0)
                prediction = COUNTERFEIT_MODEL.predict(img_batch)
                confidence_score = prediction[0][0]
                if confidence_score < 0.8:
                    ai_warning = f"AI model detected potential visual anomalies with a confidence of {confidence_score:.2f}."
            except Exception as e:
                print(f"AI model prediction failed: {e}")
                ai_warning = "AI visual check could not be performed."
        
        serializer = MedicineSerializer(medicine_record)
        response_data = {"status": "Verified" if not ai_warning else "Warning", "details": serializer.data}
        if ai_warning:
            response_data["ai_warning"] = ai_warning
        return Response(response_data)