#from django.conf.urls import url, include
from django.urls import include, re_path
from django.contrib import admin
from django.urls import path
from .accountant import *
from .merchant import *
from .customer import *
from .api import *
from .loyalty import *
from .dashboard import *
from .campaign import *
from .scheduler import *
from .plan import *
from .giftcard import *
from .vendors import *
from .metropos import *
from .notification import *
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .import giftcard




from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="API DOCUMENTATION FOR WAJE LOYALTY BACKEND",
        default_version='v1',
        description="Waje Loyalty appliation for gift cards",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="fadabose@wajesmart.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)






urlpatterns = {
    re_path(r'^merchant/$', merchantView.as_view()),
    re_path(r'^editmerchant/$', editMerchantRecord.as_view()),
    re_path(r'^merchantcustomer/$', MerchantCustomerView.as_view()),
    re_path(r'^merchantmanager/$', merchantManagerView.as_view()),
    path('merchant-manager/<int:pk>/', merchantDeleteManagerView.as_view()),
    re_path(r'^merchantbranch/$', merchantBranchView.as_view()),
    re_path(r'^merchantloyaltyrule/$', merchantLoyaltyRuleView.as_view()),
    # re_path(r'^merchantcrosspromotionrule/$',merchantCrossPromotionRuleView.as_view()),
    re_path(r'^merchantloyaltytransaction/$',merchantLoyaltyTransactionView.as_view()),
    re_path(r'^merchantauthentication/$', merchantLoginView.as_view()),
    re_path(r'^managerauthentication/$', branchManagerLoginView.as_view()),
    re_path(r'^merchantcustomerredemption/$',
        merchantCustomerRedemptionView.as_view()),
    re_path(r'^listsalesummary/$', listSaleSummaryView.as_view()),
    re_path(r'^listloyaltysummary/$', listLoyaltySummaryView.as_view()),
    re_path(r'^listcustomerspoint/$', listCustomersPoint.as_view()),
    re_path(r'^giftcardstat/$', listGiftCardSummaryView.as_view()),
    re_path(r'^merchantsetting/$', createMerchantSettings.as_view()),
    re_path(r'^themecolors/(?P<pk>\d+)/$', themeColorsDetails.as_view()),
    re_path(r'^merchantpasswordrecovery/$', recoverMerchantPassword.as_view()),
    re_path(r'^campaigntemplate/$', CampaignTemplate.as_view()),
    re_path(r'^campaign/$', Campaign.as_view()),
    re_path(r'^merchantchangepassword/$', merchantChangePassword.as_view()),
    re_path(r'attachment/$', documentattachment.as_view()),
    # re_path(r'plansubscription/$',planSubscription.as_view()),
    # re_path(r'upgradesubscription/$',upgradeSubscription.as_view()),
    re_path(r'merchantgiftcard/$', MerchantGiftCardView.as_view()),
    re_path(r'deactivategift/$', deactivateGiftCard.as_view()),
    re_path(r'purchasegiftcard/$', purchaseMerchantGiftCardView.as_view()),
    re_path(r'redeemgiftcard/$', redeemMerchantGiftCardView.as_view()),
    re_path(r'campaignhistory/$', campaignHistoryView.as_view()),
    re_path(r'redeemloyaltypoint/$', redeemCustomerPoint.as_view()),
    re_path(r'customeregisterationapi/$', MerchantCustomerRegistrationView.as_view()),
    re_path(r'customerloginapi/$', MerchantCustomerLoginView.as_view()),
    re_path(r'customerearnpointapi/$', MerchantCustomerEarnPointsView.as_view()),
    re_path(r'customerredeempointapi/$', MerchantCustomerRedeemPointsView.as_view()),
    re_path(r'getcustomerpointapi/$', MerchantCustomerPointsView.as_view()),
    re_path(r'merchantgiftcardapi/$', MerchantGiftcard.as_view()),
    re_path(r'redeemgiftcardapi/$', MerchantCustomerGiftcardView.as_view()),
    re_path(r'verifygiftcard/$', MerchantCustomerGiftcardVerificationView.as_view()),
    re_path(r'bulkpurchase/$', bulkPurchaseMerchantGiftCardView.as_view(), name="test"),
    re_path(r'^processcampaign/$', crossCampaign),
    re_path(r'^startmetropos/$', saveGiftVoucherRecord),
    re_path(r'^scheduler/$', processtestCampaign),
    re_path(r'^integrationmidas/$', processTwentyhoursCampaign),
    re_path(r'^notification/$', testNotification),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/$',
        activate_user_account, name='activate_user_account'),
    re_path(r'^passwordrecovery/$', passwordRecovery.as_view()),
    re_path(r'^api/token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r'^api/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^api/token/verify/$', TokenVerifyView.as_view(), name='token_verify'),
    path('roles', ListCreateRoleView.as_view(), name='role'),
    path('role/<pk>', UpdateRoleView.as_view(), name='edit-role'),
    path('admin/', admin.site.urls),
    path("test/", giftcard.test, name="test"),
    path('verify-transaction/', VerifyTransactionAPIView.as_view(), name='verify-transaction'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'), #API DOCUMENTATION URL
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc')

}
urlpatterns = format_suffix_patterns(urlpatterns)
