from . import userdb


def get_user(request):
    userid = request.unauthenticated_userid
    if userid is not None:
        user = userdb.from_id(request.db, userid)
        return user


def groupfinder(userid, request):
    user = request.user
    if user is not None:
        return ['g:' + group for group in request.user.groups]
    return None
