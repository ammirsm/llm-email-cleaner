# tasks.py
from celery import shared_task
from django.apps import apps


@shared_task(rate_limit="100/s")
def fill_full_data(obj_id, model_name):
    model = apps.get_model("retriever", model_name)
    obj = model.objects.get(id=obj_id)
    obj.load_full_data()
