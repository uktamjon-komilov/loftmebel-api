from datetime import datetime, timedelta
from api.models import WrongRty
from api.utils import get_client_ip


def create_wrong_try(request, data):
    username = data["username"].strip()
    password = data["password"].strip()
    
    wrong_try = WrongRty(
        username=username,
        password=password,
        user_agent=request.user_agent,
        ip=get_client_ip(request)
    )
    wrong_try.save()


def check_black_list(request):
    wrong_tries = WrongRty.objects.filter(
        user_agent=request.user_agent,
        ip=get_client_ip(request),
        created_at__gte=(datetime.now() - timedelta(minutes=5))
    )

    if wrong_tries.count() >= 3:
        return True
    return False