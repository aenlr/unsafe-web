from pyramid.httpexceptions import HTTPFound, HTTPNoContent
from pyramid.request import Request
from pyramid.security import Allow
from pyramid.view import view_config

from .app import RootContextFactory
from . import postdb


class NotesFactory(RootContextFactory):

    def __getitem__(self, post_id):
        note = postdb.find_post(self.request.db, post_id)
        if note:
            return NoteResource(note)

        raise KeyError(post_id)


class NoteResource:
    def __init__(self, note: postdb.Post):
        self.note = note

    @property
    def __acl__(self):
        return [
            (Allow, self.note.user_id, ('view', 'edit'))
        ]


###############################################################################
## Notes
###############################################################################

@view_config(route_name='note-action', request_method=('GET', 'POST'), request_param='action=delete')
def delete_note_unsafe(request):
    """Unsafe delete of note.

    - Deletes as a side effect of GET request
    - Does not validate arguments (SQL injection due to unsafe implementation of delete_note)
    - Does not check permissions
    """

    postdb.delete_post(request.db, request.params['id'])
    return HTTPNoContent()


@view_config(route_name='notes', permission='view', renderer='templates/list-notes.jinja2')
def notes_view(request):
    search = request.params.get('search', '')
    from_date = request.params.get('from', '')
    to_date = request.params.get('to', '')
    notes = postdb.find_posts(request.db,
                              public=False,
                              user_id=request.user.user_id,
                              from_date=from_date,
                              to_date=to_date,
                              search=search)

    return {
        'notes': notes,
        'from': from_date,
        'to': to_date,
        'search': search
    }


@view_config(route_name='edit-note', permission='edit', renderer='templates/edit-note.jinja2')
def edit_note(context: NoteResource, request: Request):
    if request.method == 'POST':
        content: str = request.params['note']
        context.note.content = content.replace('\r', '')
        postdb.save_post(request.db, context.note)
        return HTTPFound(location=request.route_url('notes'))

    return dict(title='Redigera anteckning',
                note=context.note)


@view_config(route_name='new-note', permission='edit', renderer='templates/edit-note.jinja2')
def create_note(request: Request):
    if request.method == 'POST':
        note = postdb.Post(None,
                           user_id=request.user.user_id,
                           content=request.params['note'])
        postdb.save_post(request.db, note)
        return HTTPFound(location=request.route_url('notes'))

    return dict(title='Ny anteckning',
                note=postdb.Post(None, user_id=request.user.user_id, content=''))


def includeme(config):
    config.add_route('notes', '/notes', factory=NotesFactory)
    config.add_route('new-note', '/notes/new')
    config.add_route('edit-note', '/notes/{note}/edit', factory=NotesFactory,
                     traverse='/{note}')

    config.add_route('note-action', '/api/notes')
