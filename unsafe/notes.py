from pyramid.httpexceptions import HTTPFound, HTTPNoContent
from pyramid.request import Request
from pyramid.security import Allow
from pyramid.view import view_config

from . import db
from .app import RootContextFactory
from .embed import embeddable


class NotesFactory(RootContextFactory):

    def __getitem__(self, note_id):
        note = db.note.find_note(self.request.db, note_id)
        if note:
            return NoteResource(note)

        raise KeyError(note_id)


class NoteResource:
    def __init__(self, note: db.note.Note):
        self.note = note

    @property
    def __acl__(self):
        return [
            (Allow, self.note.user_id, ('view', 'edit'))
        ]


###############################################################################
# Notes
###############################################################################

@view_config(route_name='note-action',
             request_method=('GET', 'POST'),
             request_param='action=delete')
def delete_note_action(request):
    """Unsafe delete of note.

    - Deletes as a side effect of GET request
    - Does not validate arguments (SQL injection due to unsafe implementation
      of delete_note)
    - Does not check permissions
    - Vulnerable to CSRF
    """

    db.note.delete_note(request.db, request.params['id'])
    return HTTPNoContent()


@view_config(route_name='notes', permission='view',
             renderer='notes/list-notes.jinja2')
def notes_listing(request):
    search = request.params.get('search', '')
    from_date = request.params.get('from', '')
    to_date = request.params.get('to', '')
    notes = db.note.find_notes(request.db,
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


@view_config(route_name='note', permission='edit', request_method='GET',
             renderer='notes/edit-note.jinja2', decorator=embeddable)
def edit_note(context: NoteResource, request: Request):
    return dict(title='Redigera anteckning',
                note=context.note)


@view_config(route_name='note', permission='edit', request_method='POST',
             renderer='notes/edit-note.jinja2', decorator=embeddable)
def save_note(context: NoteResource, request: Request):
    _save_or_create_note(context.note, request)
    return HTTPFound(location=request.route_url('notes'))


@view_config(route_name='new-note', permission='edit',
             renderer='notes/edit-note.jinja2', require_csrf=True,
             decorator=embeddable)
def create_note(request: Request):
    note = db.note.Note(None,
                        user_id=request.user.user_id,
                        content=request.params.get('note', ''))
    if request.method == 'POST':
        _save_or_create_note(note, request)
        return HTTPFound(location=request.route_url('notes'))

    return dict(title='Ny anteckning',
                note=note)


def _save_or_create_note(note: db.note.Note, request: Request):
    content: str = request.params['note']
    note.content = content.replace('\r', '')
    return db.note.save_note(request.db, note)


def includeme(config):
    config.add_route('notes', '/notes', factory=NotesFactory)
    config.add_route('new-note', '/notes/new')
    config.add_route('note',
                     pattern='/notes/{note}',
                     traverse='/{note}',
                     factory=NotesFactory)

    config.add_route('note-action', '/api/notes')
