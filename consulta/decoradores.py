from django.shortcuts import redirect

def rol_requerido(roles):
    def decorador(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.rol not in roles:
                return redirect("login")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorador
