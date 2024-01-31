from rest_framework.serializers import ModelSerializer

from apps.information.models import Program, UserProgram


class ProgramListSerializer(ModelSerializer):
    class Meta:
        model = Program
        fields = [
            "name",
            "duration",
            "exp_profit",
            "max_risk",
            "min_deposit"
            "accrual_type"
            "withdrawal_type"
            "max_risk"
            "success_fee"
            "management_fee"
            "withdrawal_term",
        ]


class UserProgramListSerializer(ModelSerializer):
    class Meta:
        model = UserProgram
        fields = [
            "name",
            "start_date",
            "end_date",
            "funds",
        ]
