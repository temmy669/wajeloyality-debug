from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path
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
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = {
    url(r'^merchant/$', merchantView.as_view()),
    url(r'^editmerchant/$', editMerchantRecord.as_view()),
    url(r'^merchantcustomer/$', MerchantCustomerView.as_view()),
    url(r'^merchantmanager/$', merchantManagerView.as_view()),
    path('merchant-manager/<int:pk>/', merchantDeleteManagerView.as_view()),
    url(r'^merchantbranch/$', merchantBranchView.as_view()),
    url(r'^merchantloyaltyrule/$', merchantLoyaltyRuleView.as_view()),
    # url(r'^merchantcrosspromotionrule/$',merchantCrossPromotionRuleView.as_view()),
    url(r'^merchantloyaltytransaction/$',merchantLoyaltyTransactionView.as_view()),
    url(r'^merchantauthentication/$', merchantLoginView.as_view()),
    url(r'^managerauthentication/$', branchManagerLoginView.as_view()),
    url(r'^merchantcustomerredemption/$',
        merchantCustomerRedemptionView.as_view()),
    url(r'^listsalesummary/$', listSaleSummaryView.as_view()),
    url(r'^listloyaltysummary/$', listLoyaltySummaryView.as_view()),
    url(r'^listcustomerspoint/$', listCustomersPoint.as_view()),
    url(r'^giftcardstat/$', listGiftCardSummaryView.as_view()),
    url(r'^merchantsetting/$', createMerchantSettings.as_view()),
    url(r'^themecolors/(?P<pk>\d+)/$', themeColorsDetails.as_view()),
    url(r'^merchantpasswordrecovery/$', recoverMerchantPassword.as_view()),
    url(r'^campaigntemplate/$', CampaignTemplate.as_view()),
    url(r'^campaign/$', Campaign.as_view()),
    url(r'^merchantchangepassword/$', merchantChangePassword.as_view()),
    url(r'attachment/$', documentattachment.as_view()),
    # url(r'plansubscription/$',planSubscription.as_view()),
    # url(r'upgradesubscription/$',upgradeSubscription.as_view()),
    url(r'merchantgiftcard/$', MerchantGiftCardView.as_view()),
    url(r'deactivategift/$', deactivateGiftCard.as_view()),
    url(r'purchasegiftcard/$', purchaseMerchantGiftCardView.as_view()),
    url(r'redeemgiftcard/$', redeemMerchantGiftCardView.as_view()),
    url(r'campaignhistory/$', campaignHistoryView.as_view()),
    url(r'redeemloyaltypoint/$', redeemCustomerPoint.as_view()),
    url(r'customeregisterationapi/$', MerchantCustomerRegistrationView.as_view()),
    url(r'customerloginapi/$', MerchantCustomerLoginView.as_view()),
    url(r'customerearnpointapi/$', MerchantCustomerEarnPointsView.as_view()),
    url(r'customerredeempointapi/$', MerchantCustomerRedeemPointsView.as_view()),
    url(r'getcustomerpointapi/$', MerchantCustomerPointsView.as_view()),
    url(r'merchantgiftcardapi/$', MerchantGiftcard.as_view()),
    url(r'redeemgiftcardapi/$', MerchantCustomerGiftcardView.as_view()),
    url(r'verifygiftcard/$', MerchantCustomerGiftcardVerificationView.as_view()),
    url(r'bulkpurchase/$', bulkPurchaseMerchantGiftCardView.as_view()),
    url(r'^processcampaign/$', crossCampaign),
    url(r'^startmetropos/$', saveGiftVoucherRecord),
    url(r'^scheduler/$', processtestCampaign),
    url(r'^integrationmidas/$', processTwentyhoursCampaign),
    url(r'^notification/$', testNotification),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/$',
        activate_user_account, name='activate_user_account'),
    url(r'^passwordrecovery/$', passwordRecovery.as_view()),
    url(r'^api/token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    url(r'^api/token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    url(r'^api/token/verify/$', TokenVerifyView.as_view(), name='token_verify'),
    path('roles', ListCreateRoleView.as_view(), name='role'),
    path('role/<pk>', UpdateRoleView.as_view(), name='edit-role'),
    path('giftcard_list/<int:merchant_service_id>', GiftCardView.as_view(), name='giftcard'),
    path('giftcard_update/<pk>', UpdateGiftCardView.as_view(), name='update-giftcard'),
    path('verify-transaction/', VerifyTransactionAPIView.as_view(), name='verify-transaction'),
    #path('admin/', admin.site.urls),
}
urlpatterns = format_suffix_patterns(urlpatterns)
