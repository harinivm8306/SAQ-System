from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
import random
from django.core.mail import send_mail
from django.contrib.auth.models import User


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            if request.POST.get("remember_me"):
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # expires on browser close

            return redirect("dashboard")

        else:
            return render(request, "users/login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "users/login.html")




def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not username:
            return render(request, "users/register.html", {
                "error": "Username is required"
            })

        if not email:
            return render(request, "users/register.html", {
                "error": "Email is required"
            })

        if password != confirm_password:
            return render(request, "users/register.html", {
                "error": "Passwords do not match"
            })

        if User.objects.filter(username=username).exists():
            return render(request, "users/register.html", {
                "error": "Username already exists"
            })

        if User.objects.filter(email=email).exists():
            return render(request, "users/register.html", {
                "error": "Email already registered. Please login."
            })

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return redirect("login")

    return render(request, "users/register.html")



def logout_view(request):
    logout(request)
    return redirect('login')

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not registered")
            return redirect("forgot_password")

        otp = random.randint(100000, 999999)
        request.session['reset_otp'] = otp
        request.session['reset_email'] = email

        send_mail(
            "Password Reset OTP",
            f"Your OTP is {otp}",
            "harinivm8306@gmail.com",
            [email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent to your email")
        return redirect("verify_otp")

    return render(request, "users/forgot_password.html")

def reset_password(request):
    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password != confirm:
            messages.error(request, "Passwords do not match")
            return redirect("reset_password")

        email = request.session.get('reset_email')
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successful. Login now.")
        return redirect("login")

    return render(request, "users/reset_password.html")

def verify_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")

        if int(otp) == request.session.get('reset_otp'):
            return redirect("reset_password")
        else:
            messages.error(request, "Invalid OTP")

    return render(request, "users/verify_otp.html")
