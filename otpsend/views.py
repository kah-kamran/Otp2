from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import SignUpSerializer
from rest_framework.decorators import api_view, permission_classes
import pyotp
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

User = get_user_model()

class generateKey:
    @staticmethod
    def returnValue():
        secret = pyotp.random_base32()        
        totp = pyotp.TOTP(secret, interval=86400)
        OTP = totp.now()
        return {"totp":secret,"OTP":OTP}


@api_view(['POST'])
@permission_classes([AllowAny,])
def signup(request):
    serializer = SignUpSerializer(data=request.data)
    
    if serializer.is_valid():
        
        key = generateKey.returnValue()
        user = User(
            username = serializer.data['username'],
            email = serializer.data['email'],
            otp = key['OTP'],
            activation_key = key['totp'],
        )
        
        try:
            validate_password(serializer.data['password'], user)
        except ValidationError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.data['password'])
        user.is_active = False
        user.save()
        
        email_template = render_to_string('signup_otp.html',{"otp":key['OTP'],"username":serializer.data['username']})    
        sign_up = EmailMultiAlternatives(
                        "Otp Verification", 
                        "Otp Verification",
                        settings.EMAIL_HOST_USER, 
                        [serializer.data['email']],
                    )
        sign_up.attach_alternative(email_template, 'text/html')
        sign_up.send()
    
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([AllowAny,])
def signupVerify(request,otp):
    try:
        user = User.objects.get(otp = otp,is_active = False)
        _otp = user.otp
        if otp != _otp:
            return Response({"Otp" : "Invalid otp"},status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            activation_key = user.activation_key
            totp = pyotp.TOTP(activation_key, interval=86400)
            verify = totp.verify(otp)
            
            if verify:
                user.is_active = True
                user.save()
                
                email_template = render_to_string('signup_otp_success.html',{"username":user.username})    
                sign_up = EmailMultiAlternatives(
                        "Account successfully activated", 
                        "Account successfully activated",
                        settings.EMAIL_HOST_USER, 
                        [user.email],
                    )
                sign_up.attach_alternative(email_template, 'text/html')
                sign_up.send()
                
                return Response({"Varify success" : "Your account has been successfully activated!!"}, status=status.HTTP_202_ACCEPTED)
            else:
                return Response({"Time out" : "Given otp is expired!!"}, status=status.HTTP_408_REQUEST_TIMEOUT)
    
    except:
        return Response({"No User" : "Invalid otp OR No any inactive user found for given otp"}, status=status.HTTP_400_BAD_REQUEST)
