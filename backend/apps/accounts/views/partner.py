from rest_framework.generics import RetrieveAPIView

from apps.accounts.models.user import Partner

# from apps.accounts.serializers.partner import PartnerGeneralStatisticsSerializer


# class PartnerGeneralStatisticsRetrieveView(RetrieveAPIView):
#     serializer_class = PartnerGeneralStatisticsSerializer
#
#     def get_object(self):
#         user = self.request.user
#         return user.partner_profile
#
#     def retrieve(self, request, *args, **kwargs):
#         partner_profile = self.get_object()
