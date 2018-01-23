from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def login_required(view_func):
    def wrapper(request, *view_args, **view_kwargs):
        if request.session.has_key('is_login'):
            return view_func(request, *view_args, **view_kwargs)
        else:
            print(reverse('users:login'))
            return redirect(reverse('users:login'))
    return wrapper
