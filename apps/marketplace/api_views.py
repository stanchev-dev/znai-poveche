from decimal import Decimal, InvalidOperation

from django.db.models import Case, DateTimeField, F, IntegerField, Value, When
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Listing
from .serializers import (
    ListingContactSerializer,
    ListingCreateSerializer,
    ListingDetailSerializer,
    ListingListSerializer,
    ListingVipUpgradeSerializer,
)


class ListingPagination(PageNumberPagination):
    page_size = 20


class ListingListCreateAPIView(generics.GenericAPIView):
    queryset = Listing.objects.select_related(
        "subject",
        "owner",
        "owner__profile",
    )
    pagination_class = ListingPagination
    serializer_class = ListingListSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ListingCreateSerializer
        return ListingListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        queryset = self.get_queryset()

        subject = request.query_params.get("subject")
        if subject and subject != "all":
            queryset = queryset.filter(subject__slug=subject)

        online_only = request.query_params.get("online_only")
        if online_only is not None:
            if online_only not in {"0", "1"}:
                return Response(
                    {"online_only": ["Must be either 0 or 1."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if online_only == "1":
                queryset = queryset.filter(online_only=True)

        price_min = request.query_params.get("price_min")
        if price_min not in (None, ""):
            min_value = self._parse_decimal("price_min", price_min)
            if isinstance(min_value, Response):
                return min_value
            queryset = queryset.filter(price_per_hour__gte=min_value)

        price_max = request.query_params.get("price_max")
        if price_max not in (None, ""):
            max_value = self._parse_decimal("price_max", price_max)
            if isinstance(max_value, Response):
                return max_value
            queryset = queryset.filter(price_per_hour__lte=max_value)

        queryset = queryset.annotate(
            is_vip_int=Case(
                When(vip_until__gt=now, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            vip_until_sort=Case(
                When(vip_until__gt=now, then=F("vip_until")),
                default=Value(None),
                output_field=DateTimeField(),
            ),
        ).order_by(
            "-is_vip_int",
            F("vip_until_sort").desc(nulls_last=True),
            "-created_at",
            "-id",
        )

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        create_serializer.is_valid(raise_exception=True)
        listing = create_serializer.save()
        listing = Listing.objects.select_related(
            "subject",
            "owner",
            "owner__profile",
        ).get(pk=listing.pk)
        output_serializer = ListingDetailSerializer(listing)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def _parse_decimal(self, field_name: str, value: str):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError):
            return Response(
                {field_name: ["Must be a valid decimal number."]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ListingVipUpgradeAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListingVipUpgradeSerializer
    queryset = Listing.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class ListingDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ListingDetailSerializer
    queryset = Listing.objects.select_related(
        "subject",
        "owner",
        "owner__profile",
    )


class ListingContactAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ListingContactSerializer
    queryset = Listing.objects.all()
