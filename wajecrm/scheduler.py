from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from wajecrm import campaign, metropos
from django.http import HttpResponse
from pytz import timezone


def start():
    # scheduler = BackgroundScheduler(timezone=timezone('Africa/Lagos'))
    # scheduler.add_job(campaign.processTwentyhoursCampaign, 'cron',
    #                   month='1-12', hour='0-1', id='twentyhoursCampaignnotification')
    # scheduler.add_job(campaign.processweeklyCampaign, 'cron', month='1-12',
    #                   day_of_week='sun', hour='0-1', id='processweeklyCampaignnotification')
    # scheduler.add_job(campaign.processmonthlyCampaign, 'cron', month='1-12',
    #                   day=1, hour='0-1', id='processmonthlyCampaignnotification')
    # scheduler.add_job(metropos.customerLoyaltyTransaction,
    #                   'interval', minutes=20, id='customerLoyaltyTransaction')
    # scheduler.add_job(metropos.retrieveRedeemGiftCard,
    #                   'interval', minutes=10, id='retrieveRedeemGiftCard')
    # scheduler.add_job(metropos.saveGiftVoucherRecord, 'interval',
    #                   minutes=5, id='saveGiftVoucherRecord')
    # scheduler.add_job(metropos.pushDeactivatedGiftVoucherRecord, 'interval',
    #                   minutes=1, id='pushDeactivatedGiftVoucherRecord')                    
    # scheduler.add_job(metropos.getRedemptionTransaction, 'interval',
    #                   minutes=10, id='getRedemptionTransaction')
    # scheduler.start()

    return HttpResponse(None)
