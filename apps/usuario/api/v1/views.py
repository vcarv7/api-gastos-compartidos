"""Views for version 1 of the usuario API."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .serializers import RegisterSerializer


class RegisterView(APIView):
    """Create an account. Open to anonymous requests by design.

    One class per endpoint on purpose: a ``delete()`` here would expose
    ``DELETE /register/``, a URL with nothing to identify what to delete.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        # raise_exception=True is what turns validation failures into a 400.
        # Without it the view would fall through and answer 201 with no account.
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
