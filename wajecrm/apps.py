from django.apps import AppConfig


class WajecrmConfig(AppConfig):
    name = 'wajecrm'
    def ready(self): 
        from wajecrm import scheduler      
        scheduler.start()
 