from django.urls import resolve

def current_app(request):
    try:
        return {"current_app": resolve(request.path_info).app_name}
    except:
        return {"current_app": None}