from functools import wraps
from rest_framework.response import Response
from rest_framework import status

def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user = request.user

        # Check if the user belongs to the 'Administrator' group
        if user.groups.filter(name='Administrator').exists():
            # User is in the 'Administrator' group, allow access to the view
            return view_func(request, *args, **kwargs)
        else:
            # User doesn't have the required permission, return permission denied
            return Response({'message': 'Permission denied, You need to be an administrator'}, status=status.HTTP_403_FORBIDDEN)

    return wrapped_view