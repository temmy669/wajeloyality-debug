#from django.conf.urls import url, include
from django.urls import include, re_path
from django.contrib import admin
from django.urls import path
from .accountant import *
from .auditor import *
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
from .accountant import *
from .utils.export import ExportGiftCardReportExcelView
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from .managerCheckout import CheckoutVoucherBalanceView, CheckoutVoucherRedeemView
# from .import giftcard

from rest_framework import permissions



urlpatterns = [
    re_path(r'^merchant/$', merchantView.as_view()),
    re_path(r'^editmerchant/$', editMerchantRecord.as_view()),
    re_path(r'^merchantcustomer/$', MerchantCustomerView.as_view()),
    re_path(r'^merchant/staffs', ListCreateMerchantStaffView.as_view()), # new - list merchant users/staff
    re_path(r'^merchant/staffs/<pk>', UpdateMerchantStaffView.as_view()), # new - edit merchant users/staff
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
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/$', activate_user_account, name='activate_user_account'),
    re_path(r'^passwordrecovery/$', passwordRecovery.as_view()),
    re_path(r'^api/token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r'^api/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^api/token/verify/$', TokenVerifyView.as_view(), name='token_verify'),
    path('roles', ListCreateRoleView.as_view(), name='role'),
    path('role/<pk>', UpdateRoleView.as_view(), name='edit-role'),
    path('giftcard/<str:merchant_service_id>', GiftCardView.as_view(), name='giftcard'),
    path('giftcard/<pk>', UpdateGiftCardView.as_view(), name='update-giftcard'),
    path('admin/', admin.site.urls),
    path('verify-transaction/', VerifyTransactionAPIView.as_view(), name='verify-transaction'),
    path('auditor/', AuditorAPIView.as_view(), name='auditor'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('accountant/giftcards', AccountDataView.as_view(), name='giftcard-accountantview'),
    path('list-roles/', roleListView.as_view(), name='list-roles'),
    path('manager-verification/', merchantGiftcardVerificationView.as_view(), name='manager-verification'),
    path('export/giftcard/', ExportGiftCardReportExcelView.as_view(), name='export-giftcard-excel'),
    path('checkout/voucher-balance/', CheckoutVoucherBalanceView.as_view(), name='checkout-voucher-balance'),
    path('checkout/voucher-redeem/',  CheckoutVoucherRedeemView.as_view(),  name='checkout-voucher-redeem'),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns = format_suffix_patterns(urlpatterns)
