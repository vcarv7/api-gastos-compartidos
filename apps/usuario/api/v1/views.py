"""Views for version 1 of the usuario API."""

from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """Create an account. Open to anonymous requests by design.

    One class per endpoint on purpose: a ``delete()`` here would expose
    ``DELETE /register/``, a URL with nothing to identify what to delete.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        tags=["Cuentas"],
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
            400: OpenApiResponse(
                description="Validation error. One entry per invalid field."
            ),
            429: OpenApiResponse(description="Rate limit exceeded."),
        },
        summary="Create an account",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        # raise_exception=True is what turns validation failures into a 400.
        # Without it the view would fall through and answer 201 with no account.
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(post=extend_schema(tags=["Sesiones"]))
class LoginView(TokenObtainPairView):
    """Issue an access/refresh pair. Brute force lives here, not in register."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class MeView(APIView):
    """Return the authenticated user.

    The identity comes from the token, not from the URL, so there is no way to
    read somebody else's profile through this endpoint.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Cuentas"],
        responses={200: UserSerializer},
        summary="Return the authenticated user",
    )
    def get(self, request):
        # context={"request": request} lets ImageField build an absolute URL
        # for photo; without it the client receives a relative path.
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)
