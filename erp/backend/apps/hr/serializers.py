"""Serializers for HR master data (shape only)."""

from __future__ import annotations

from rest_framework import serializers

from apps.hr.models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "id",
            "company",
            "site",
            "department",
            "user",
            "employee_code",
            "first_name_fa",
            "last_name_fa",
            "first_name_en",
            "last_name_en",
            "job_title",
            "is_active",
            "created_at",
            "updated_at",
        ]
