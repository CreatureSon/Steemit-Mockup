from django.shortcuts import redirect
from .utils import is_time_expired

def study_time_required(view_func):
    def wrapper(request, *args, **kwargs):
        if is_time_expired(request):
            return redirect("participants:end")
        return view_func(request, *args, **kwargs)
    return wrapper
