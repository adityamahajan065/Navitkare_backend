from django.urls import path
from .views import RegisterView, VerifyMedicineView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyMedicineView.as_view(), name='verify_medicine'),
]