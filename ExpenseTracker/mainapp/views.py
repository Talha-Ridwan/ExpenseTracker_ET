from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect
from .models import User, EmailOTP, Feedback
from .serializers import UserRegisterSerializer, EmailOTPSerializer
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
import random
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication




def home_view(request):
    return render(request, 'Home/home.html')

def contactus_page(request):
    return render(request,'CONTACT/c_us.html')

@login_required
def update_profile_page(request):
    return render(request, 'UPDATE_PROFILE/update_profile.html', {
        'user': request.user
    })


@login_required
def setting_page(request):
    return render(request,'SETTING/setting.html')


@login_required
def delete_account_page(request):
    return render(request, 'DELETE_ACCOUNT/delete_account.html')

# Render registration form
def register_page(request):
    return render(request, 'REGISTER/register.html')

# Render login form
def login_page(request):
    return render(request, 'LOGIN/login.html')

# Render update profile form
def update_profile_page(request):
    return render(request, 'UPDATE_PROFILE/update_profile.html')

# Render delete account form
def delete_account_page(request):
    return render(request, 'delete_account.html')

@login_required
def dashboard_page(request):
    return render(request, 'DASHBOARD/dashboard.html')


@login_required
def contact_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        message = request.POST.get('message')
        is_user = request.POST.get('is_user') == 'on'  # 'on' means checked

        # Check if the user agreed to the privacy policy
        consent = request.POST.get('consent') == 'on'
        if not consent:
            messages.error(request, "You must agree to the privacy policy before submitting.")
            return redirect('contact')
        

        # Check if user is authenticated and email matches
        if request.user.is_authenticated:
            if email != request.user.email:
                messages.error(request, "Email doesn't match your account email.")
                return redirect('contact')

        # Save the feedback to the database
        Feedback.objects.create(email=email, message=message, is_user=is_user)
        # Show a success message
        messages.success(request, "Your feedback has been submitted successfully!")
        return redirect('contact')
    initial_email = request.user.email if request.user.is_authenticated else ''
    return render(request, 'CONTACT/contact.html', {'initial_email': initial_email})




class SendOTP(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        otp = str(random.randint(100000, 999999))

        # Save or update OTP
        EmailOTP.objects.update_or_create(email=email, defaults={'otp': otp})

        # Send email
        try:
            send_mail(
                subject='Your OTP Code',
                message=f'Your OTP is: {otp}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({'msg': 'OTP sent to your email'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to send OTP: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class RegisterView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp_input = request.data.get('otp')

        try:
            otp_record = EmailOTP.objects.get(email=email)
        except EmailOTP.DoesNotExist:
            return Response({'errors': {'otp': 'OTP not requested'}}, status=status.HTTP_400_BAD_REQUEST)

        if otp_record.otp != otp_input:
            return Response({'errors': {'otp': 'Invalid OTP'}}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            otp_record.delete()
            send_mail(
                subject='Account created at Expense Tracker',
                message='Your have successfully created an account at Expense Tracker and you can now login.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            return redirect('/login/') 
        return render(request, 'register.html', {'errors': serializer.errors})






class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        return render(request, "Login/login.html", {"error": "Invalid email or password."})





class DeleteAccountView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp_input = request.data.get('otp')

        try:
            otp_record = EmailOTP.objects.get(email=email)
        except EmailOTP.DoesNotExist:
            return Response({'error': 'OTP not requested'}, status=400)

        if otp_record.otp != otp_input:
            return Response({'error': 'Invalid OTP'}, status=400)

        try:
            user = User.objects.get(email=email)
            send_mail(
                subject='Expense Tracker account deleted',
                message=f'Your Expense Tracker account has been deleted. You  can Create  another account to login.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            user.delete()
            otp_record.delete()
            return redirect('/login/')
            #return Response({'message': 'Account deleted successfully'}, status=200)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

    

# Logout view
def logout_view(request):
    logout(request)  # Log the user out
    return redirect('login')  # Redirect to login page








#anika

@login_required
def update_profile_page(request):
    user = request.user
    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.username = request.POST.get('username')
        user.number = request.POST.get('number')
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('update_profile_page')
    return render(request, 'UPDATE_PROFILE/update_profile.html', {'user': user})


@login_required
def change_password(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('setting')

        try:
            otp_record = EmailOTP.objects.get(email=request.user.email)
            if otp_record.otp != otp_input:
                messages.error(request, "Invalid OTP.")
                return redirect('setting')
        except EmailOTP.DoesNotExist:
            messages.error(request, "OTP not requested.")
            return redirect('setting')

        request.user.set_password(new_password)
        request.user.save()
        otp_record.delete()
        messages.success(request, "Password changed successfully. Please log in again.")
        logout(request)
        return redirect('login')
    return redirect('setting')